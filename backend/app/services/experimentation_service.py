import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import random

from app.core.config import settings
from app.models.schemas import ExperimentConfig, ExperimentAssignment, ExperimentVariant
from app.services.metrics_service import MetricsService


class ExperimentationService:
    """Service for A/B testing and experimentation."""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
        self._lock = threading.Lock()
        self._experiments = {}
        self._assignments = {}
        
        # Ensure directories exist
        settings.EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing experiments and assignments
        self._load_experiments()
        self._load_assignments()
    
    def assign_variant(self, user_key: str, experiment_id: str) -> str:
        """Assign a user to an experiment variant."""
        with self._lock:
            # Check if already assigned
            assignment_key = f"{user_key}:{experiment_id}"
            if assignment_key in self._assignments:
                return self._assignments[assignment_key]["variant"]
            
            # Get experiment configuration
            if experiment_id not in self._experiments:
                # Default experiment if not configured
                return "control"
            
            experiment = self._experiments[experiment_id]
            
            # Check if experiment is active
            if not self._is_experiment_active(experiment):
                return "control"
            
            # Assign variant based on weights
            variant = self._weighted_choice(experiment["variants"])
            
            # Record assignment
            assignment = {
                "user_key": user_key,
                "experiment_id": experiment_id,
                "variant": variant,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
            }
            
            self._assignments[assignment_key] = assignment
            self._save_assignments()
            
            # Record metrics
            self.metrics_service.increment_counter(f"experiments.{experiment_id}.assigned")
            self.metrics_service.increment_counter(f"experiments.{experiment_id}.{variant}.assigned")
            
            return variant
    
    def get_user_assignments(self, user_key: str) -> Dict[str, str]:
        """Get all experiment assignments for a user."""
        with self._lock:
            assignments = {}
            prefix = f"{user_key}:"
            
            for key, assignment in self._assignments.items():
                if key.startswith(prefix):
                    experiment_id = assignment["experiment_id"]
                    assignments[experiment_id] = assignment["variant"]
            
            return assignments
    
    def get_experiment_config(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment configuration."""
        return self._experiments.get(experiment_id)
    
    async def track_event(self, user_key: str, experiment_id: str, variant: str, event_data: Dict[str, Any]) -> None:
        """Track an experiment event."""
        try:
            # Validate assignment
            assignment_key = f"{user_key}:{experiment_id}"
            if assignment_key not in self._assignments:
                raise ValueError(f"No assignment found for user {user_key} in experiment {experiment_id}")
            
            assignment = self._assignments[assignment_key]
            if assignment["variant"] != variant:
                raise ValueError(f"Variant mismatch: expected {assignment['variant']}, got {variant}")
            
            # Create event
            event = {
                "user_key": user_key,
                "experiment_id": experiment_id,
                "variant": variant,
                "event_data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Log event
            await self._log_experiment_event(event)
            
            # Record metrics
            event_type = event_data.get("event_type", "unknown")
            self.metrics_service.increment_counter(f"experiments.{experiment_id}.{variant}.{event_type}")
            
        except Exception as exc:
            self.metrics_service.increment_counter("experiments.tracking_error")
            raise RuntimeError(f"Failed to track experiment event: {exc}") from exc
    
    def create_experiment(self, experiment_config: ExperimentConfig) -> None:
        """Create a new experiment."""
        with self._lock:
            # Validate experiment
            if experiment_config.experiment_id in self._experiments:
                raise ValueError(f"Experiment {experiment_config.experiment_id} already exists")
            
            if not experiment_config.variants:
                raise ValueError("Experiment must have at least one variant")
            
            # Validate weights sum to 1.0
            total_weight = sum(variant.weight for variant in experiment_config.variants)
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")
            
            # Store experiment
            self._experiments[experiment_config.experiment_id] = {
                "experiment_id": experiment_config.experiment_id,
                "name": experiment_config.name,
                "variants": [
                    {
                        "name": variant.name,
                        "weight": variant.weight,
                        "config": variant.config,
                    }
                    for variant in experiment_config.variants
                ],
                "start_date": experiment_config.start_date.isoformat() if experiment_config.start_date else None,
                "end_date": experiment_config.end_date.isoformat() if experiment_config.end_date else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            self._save_experiments()
            self.metrics_service.increment_counter("experiments.created")
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment results and statistics."""
        try:
            if experiment_id not in self._experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self._experiments[experiment_id]
            
            # Get assignment counts
            assignment_counts = {}
            for variant in experiment["variants"]:
                variant_name = variant["name"]
                count = sum(1 for assignment in self._assignments.values() 
                           if assignment["experiment_id"] == experiment_id and assignment["variant"] == variant_name)
                assignment_counts[variant_name] = count
            
            # Get event statistics (simplified - in production would aggregate from event logs)
            event_stats = {}
            for variant in experiment["variants"]:
                variant_name = variant["name"]
                event_stats[variant_name] = {
                    "clicks": self.metrics_service.counters.get(f"experiments.{experiment_id}.{variant_name}.click", 0),
                    "conversions": self.metrics_service.counters.get(f"experiments.{experiment_id}.{variant_name}.conversion", 0),
                    "views": self.metrics_service.counters.get(f"experiments.{experiment_id}.{variant_name}.view", 0),
                }
            
            return {
                "experiment_id": experiment_id,
                "name": experiment["name"],
                "variants": experiment["variants"],
                "assignment_counts": assignment_counts,
                "event_statistics": event_stats,
                "is_active": self._is_experiment_active(experiment),
            }
            
        except Exception as exc:
            self.metrics_service.increment_counter("experiments.results_error")
            raise RuntimeError(f"Failed to get experiment results: {exc}") from exc
    
    def get_weights_for_variant(self, variant: str) -> Dict[str, float]:
        """Get recommendation weights for an experiment variant."""
        # Default weights if no experiment is configured
        default_weights = {
            "rule": 0.3,
            "llm": 0.2,
            "personal": 0.5,
        }
        
        # Check if variant has custom weights
        experiment_configs = [
            exp for exp in self._experiments.values()
            if any(v["name"] == variant for v in exp["variants"])
        ]
        
        for experiment in experiment_configs:
            for variant_config in experiment["variants"]:
                if variant_config["name"] == variant:
                    config = variant_config.get("config", {})
                    if "recommendation_weights" in config:
                        return config["recommendation_weights"]
        
        return default_weights
    
    def _load_experiments(self) -> None:
        """Load experiments from file."""
        experiments_file = settings.EXPERIMENTS_DIR / "experiments.json"
        
        if experiments_file.exists():
            try:
                with experiments_file.open("r", encoding="utf-8") as f:
                    self._experiments = json.load(f)
            except Exception as exc:
                print(f"Failed to load experiments: {exc}")
                self._experiments = {}
        else:
            # Create default experiment
            self._create_default_experiment()
    
    def _load_assignments(self) -> None:
        """Load assignments from file."""
        if settings.EXPERIMENT_ASSIGNMENTS_FILE.exists():
            try:
                with settings.EXPERIMENT_ASSIGNMENTS_FILE.open("r", encoding="utf-8") as f:
                    self._assignments = json.load(f)
            except Exception as exc:
                print(f"Failed to load assignments: {exc}")
                self._assignments = {}
        else:
            self._assignments = {}
    
    def _save_experiments(self) -> None:
        """Save experiments to file."""
        experiments_file = settings.EXPERIMENTS_DIR / "experiments.json"
        
        with self._lock:
            with experiments_file.open("w", encoding="utf-8") as f:
                json.dump(self._experiments, f, indent=2, ensure_ascii=False)
    
    def _save_assignments(self) -> None:
        """Save assignments to file."""
        with self._lock:
            with settings.EXPERIMENT_ASSIGNMENTS_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._assignments, f, indent=2, ensure_ascii=False)
    
    async def _log_experiment_event(self, event: Dict[str, Any]) -> None:
        """Log experiment event to file."""
        events_file = settings.EXPERIMENTS_DIR / "events.jsonl"
        
        with events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    def _create_default_experiment(self) -> None:
        """Create default recommendation experiment."""
        default_experiment = {
            "experiment_id": "recommendation_weights",
            "name": "Recommendation Weight Optimization",
            "variants": [
                {
                    "name": "control",
                    "weight": 0.5,
                    "config": {
                        "recommendation_weights": {
                            "rule": 0.3,
                            "llm": 0.2,
                            "personal": 0.5,
                        }
                    }
                },
                {
                    "name": "llm_heavy",
                    "weight": 0.25,
                    "config": {
                        "recommendation_weights": {
                            "rule": 0.2,
                            "llm": 0.4,
                            "personal": 0.4,
                        }
                    }
                },
                {
                    "name": "personal_heavy",
                    "weight": 0.25,
                    "config": {
                        "recommendation_weights": {
                            "rule": 0.2,
                            "llm": 0.2,
                            "personal": 0.6,
                        }
                    }
                }
            ],
            "start_date": None,
            "end_date": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self._experiments["recommendation_weights"] = default_experiment
        self._save_experiments()
    
    def _is_experiment_active(self, experiment: Dict[str, Any]) -> bool:
        """Check if an experiment is currently active."""
        now = datetime.now(timezone.utc)
        
        # Check start date
        if experiment.get("start_date"):
            start_date = datetime.fromisoformat(experiment["start_date"])
            if now < start_date:
                return False
        
        # Check end date
        if experiment.get("end_date"):
            end_date = datetime.fromisoformat(experiment["end_date"])
            if now > end_date:
                return False
        
        return True
    
    def _weighted_choice(self, variants: List[Dict[str, Any]]) -> str:
        """Choose a variant based on weights."""
        total_weight = sum(variant["weight"] for variant in variants)
        r = random.uniform(0, total_weight)
        
        upto = 0
        for variant in variants:
            weight = variant["weight"]
            if upto + weight >= r:
                return variant["name"]
            upto += weight
        
        # Fallback to first variant
        return variants[0]["name"]
    
    async def cleanup_old_assignments(self, days_threshold: int = 90) -> int:
        """Clean up old experiment assignments."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
            cleaned_count = 0
            
            with self._lock:
                keys_to_remove = []
                
                for key, assignment in self._assignments.items():
                    assigned_at = datetime.fromisoformat(assignment["assigned_at"])
                    if assigned_at < cutoff_date:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self._assignments[key]
                    cleaned_count += 1
                
                if cleaned_count > 0:
                    self._save_assignments()
            
            self.metrics_service.increment_counter("experiments.assignments_cleaned", cleaned_count)
            return cleaned_count
            
        except Exception as exc:
            self.metrics_service.increment_counter("experiments.cleanup_error")
            raise RuntimeError(f"Assignment cleanup failed: {exc}") from exc
