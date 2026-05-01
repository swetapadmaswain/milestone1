import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
import threading

from app.core.config import settings
from app.models.schemas import FeedbackRequest, UserProfileResponse
from app.services.metrics_service import MetricsService


class PersonalizationService:
    """Service for user personalization and profile management."""
    
    DECAY_HALFLIFE_DAYS = 30.0
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
        self._lock = threading.Lock()
        
        # Ensure directories exist
        settings.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        settings.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    async def capture_feedback(self, feedback: FeedbackRequest) -> float:
        """Capture user feedback and update personalization model."""
        try:
            # Generate user key
            user_key = self._get_user_key(feedback.user_id, feedback.session_id)
            
            # Load or create user profile
            profile = await self._load_profile(user_key)
            
            # Calculate signal weight
            weight = self._calculate_signal_weight(feedback.signal_name, feedback.signal_type)
            signed_value = weight * feedback.value
            
            # Create feedback event
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "restaurant_name": feedback.restaurant_name.strip().lower(),
                "location": feedback.location.strip().lower(),
                "cuisine": feedback.cuisine.strip().lower(),
                "signal_name": feedback.signal_name,
                "signal_type": feedback.signal_type,
                "signed_value": signed_value,
            }
            
            # Add to profile
            profile["events"].append(event)
            profile["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Update preferences
            await self._update_preferences(profile, event)
            
            # Save profile
            await self._save_profile(user_key, profile)
            
            # Log feedback event
            await self._log_feedback_event(user_key, event)
            
            # Calculate personalization delta
            delta = self._calculate_personalization_delta(profile)
            
            self.metrics_service.increment_counter("personalization.feedback_captured")
            self.metrics_service.set_gauge("personalization.total_profiles", await self._get_total_profiles())
            
            return delta
            
        except Exception as exc:
            self.metrics_service.increment_counter("personalization.feedback_error")
            raise RuntimeError(f"Failed to capture feedback: {exc}") from exc
    
    async def get_profile_summary(self, user_id: Optional[str], session_id: str) -> UserProfileResponse:
        """Get user profile summary for recommendations."""
        try:
            user_key = self._get_user_key(user_id, session_id)
            profile = await self._load_profile(user_key)
            
            # Calculate summary statistics
            total_events = len(profile["events"])
            top_cuisines = self._get_top_cuisines(profile)
            favored_budget_bands = self._get_favored_budget_bands(profile)
            last_activity = self._get_last_activity(profile)
            
            self.metrics_service.increment_counter("personalization.profile_accessed")
            
            return UserProfileResponse(
                user_key=user_key,
                total_events=total_events,
                top_cuisines=top_cuisines,
                favored_budget_bands=favored_budget_bands,
                last_activity=last_activity,
            )
            
        except Exception as exc:
            self.metrics_service.increment_counter("personalization.profile_error")
            raise RuntimeError(f"Failed to get profile summary: {exc}") from exc
    
    async def personalization_score(self, restaurant: Dict[str, Any], user_id: Optional[str], session_id: str) -> float:
        """Calculate personalization score for a restaurant."""
        try:
            user_key = self._get_user_key(user_id, session_id)
            profile = await self._load_profile(user_key)
            
            if not profile["events"]:
                return 0.5  # Neutral score for new users
            
            # Calculate cuisine preference score
            cuisine_score = self._calculate_cuisine_score(restaurant, profile)
            
            # Calculate location preference score
            location_score = self._calculate_location_score(restaurant, profile)
            
            # Calculate cost preference score
            cost_score = self._calculate_cost_score(restaurant, profile)
            
            # Combine scores with weights
            personalization_score = (
                0.5 * cuisine_score +
                0.3 * location_score +
                0.2 * cost_score
            )
            
            return max(0.0, min(1.0, personalization_score))
            
        except Exception as exc:
            self.metrics_service.increment_counter("personalization.score_error")
            return 0.5  # Return neutral score on error
    
    def _load_profile_sync(self, user_key: str) -> Dict[str, Any]:
        """Load user profile from storage (synchronous)."""
        profile_file = settings.PROFILES_DIR / f"{user_key}.json"
        
        if profile_file.exists():
            with profile_file.open("r", encoding="utf-8") as f:
                profile = json.load(f)
        else:
            profile = {
                "user_key": user_key,
                "events": [],
                "preferences": {
                    "cuisines": {},
                    "locations": {},
                    "cost_bands": {},
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        
        return profile
    
    async def _load_profile(self, user_key: str) -> Dict[str, Any]:
        """Load user profile from storage (async wrapper)."""
        return await asyncio.to_thread(self._load_profile_sync, user_key)
    
    def _save_profile_sync(self, user_key: str, profile: Dict[str, Any]) -> None:
        """Save user profile to storage (synchronous)."""
        profile_file = settings.PROFILES_DIR / f"{user_key}.json"
        
        with self._lock:
            with profile_file.open("w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
    
    async def _save_profile(self, user_key: str, profile: Dict[str, Any]) -> None:
        """Save user profile to storage (async wrapper)."""
        await asyncio.to_thread(self._save_profile_sync, user_key, profile)
    
    def _log_feedback_event_sync(self, user_key: str, event: Dict[str, Any]) -> None:
        """Log feedback event to append-only log (synchronous)."""
        log_entry = {
            "user_key": user_key,
            **event
        }
        
        with settings.FEEDBACK_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    async def _log_feedback_event(self, user_key: str, event: Dict[str, Any]) -> None:
        """Log feedback event to append-only log (async wrapper)."""
        await asyncio.to_thread(self._log_feedback_event_sync, user_key, event)
    
    async def _update_preferences(self, profile: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Update user preferences based on feedback event."""
        cuisine = event["cuisine"]
        location = event["location"]
        cost_band = self._estimate_cost_band(event.get("estimated_cost", 0))
        value = event["signed_value"]
        
        # Update cuisine preferences
        if cuisine not in profile["preferences"]["cuisines"]:
            profile["preferences"]["cuisines"][cuisine] = 0.0
        profile["preferences"]["cuisines"][cuisine] += value
        
        # Update location preferences
        if location not in profile["preferences"]["locations"]:
            profile["preferences"]["locations"][location] = 0.0
        profile["preferences"]["locations"][location] += value
        
        # Update cost band preferences
        if cost_band not in profile["preferences"]["cost_bands"]:
            profile["preferences"]["cost_bands"][cost_band] = 0.0
        profile["preferences"]["cost_bands"][cost_band] += value
    
    def _get_user_key(self, user_id: Optional[str], session_id: str) -> str:
        """Generate user key for profile storage."""
        if user_id:
            return f"user:{user_id}"
        else:
            return f"session:{session_id}"
    
    def _calculate_signal_weight(self, signal_name: str, signal_type: str) -> float:
        """Calculate weight for different signal types."""
        weights = {
            ("like", "explicit"): 1.0,
            ("dislike", "explicit"): -1.0,
            ("click", "implicit"): 0.3,
            ("dwell", "implicit"): 0.2,
            ("conversion", "implicit"): 0.8,
            ("skip", "implicit"): -0.2,
        }
        
        return weights.get((signal_name, signal_type), 0.1)
    
    def _calculate_personalization_delta(self, profile: Dict[str, Any]) -> float:
        """Calculate how much the profile has changed."""
        if len(profile["events"]) <= 1:
            return 0.0
        
        # Simple heuristic: delta based on number of recent events
        recent_events = [
            event for event in profile["events"]
            if datetime.fromisoformat(event["timestamp"]) > 
            datetime.now(timezone.utc) - timedelta(days=7)
        ]
        
        return min(len(recent_events) / 10.0, 1.0)
    
    def _get_top_cuisines(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """Get top cuisine preferences."""
        cuisines = profile["preferences"]["cuisines"]
        
        if not cuisines:
            return {}
        
        # Apply time decay
        decayed_cuisines = {}
        current_time = datetime.now(timezone.utc)
        
        for cuisine, score in cuisines.items():
            # Simple decay based on last interaction
            decayed_score = score * 0.9  # Apply some decay
            decayed_cuisines[cuisine] = decayed_score
        
        # Sort and return top 5
        sorted_cuisines = sorted(decayed_cuisines.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_cuisines[:5])
    
    def _get_favored_budget_bands(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """Get favored budget bands."""
        cost_bands = profile["preferences"]["cost_bands"]
        
        if not cost_bands:
            return {}
        
        # Normalize and sort
        total = sum(abs(v) for v in cost_bands.values())
        if total == 0:
            return {}
        
        normalized = {k: v/total for k, v in cost_bands.items()}
        sorted_bands = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_bands[:3])
    
    def _get_last_activity(self, profile: Dict[str, Any]) -> Optional[datetime]:
        """Get last activity timestamp."""
        if not profile["events"]:
            return None
        
        last_event = max(profile["events"], key=lambda x: x["timestamp"])
        return datetime.fromisoformat(last_event["timestamp"])
    
    def _calculate_cuisine_score(self, restaurant: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate cuisine preference score."""
        restaurant_cuisines = [c.strip().lower() for c in restaurant["cuisine"].split(",")]
        cuisine_prefs = profile["preferences"]["cuisines"]
        
        if not cuisine_prefs:
            return 0.5
        
        scores = []
        for cuisine in restaurant_cuisines:
            if cuisine in cuisine_prefs:
                # Normalize preference score to 0-1 range
                pref_score = (cuisine_prefs[cuisine] + 1.0) / 2.0  # Assuming -1 to 1 range
                scores.append(max(0.0, min(1.0, pref_score)))
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_location_score(self, restaurant: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate location preference score."""
        location = restaurant["location"].strip().lower()
        location_prefs = profile["preferences"]["locations"]
        
        if not location_prefs or location not in location_prefs:
            return 0.5
        
        # Normalize preference score
        pref_score = (location_prefs[location] + 1.0) / 2.0
        return max(0.0, min(1.0, pref_score))
    
    def _calculate_cost_score(self, restaurant: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate cost preference score."""
        cost = restaurant["estimated_cost"]
        cost_band = self._estimate_cost_band(cost)
        cost_prefs = profile["preferences"]["cost_bands"]
        
        if not cost_prefs or cost_band not in cost_prefs:
            return 0.5
        
        # Normalize preference score
        pref_score = (cost_prefs[cost_band] + 1.0) / 2.0
        return max(0.0, min(1.0, pref_score))
    
    def _estimate_cost_band(self, cost: float) -> str:
        """Estimate cost band from cost value."""
        if cost <= 500:
            return "low"
        elif cost <= 1500:
            return "medium"
        else:
            return "high"
    
    async def _get_total_profiles(self) -> int:
        """Get total number of user profiles."""
        try:
            profile_files = list(settings.PROFILES_DIR.glob("*.json"))
            return len(profile_files)
        except Exception:
            return 0
    
    async def cleanup_old_profiles(self, days_threshold: int = 90) -> int:
        """Clean up old inactive profiles."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
            cleaned_count = 0
            
            for profile_file in settings.PROFILES_DIR.glob("*.json"):
                try:
                    with profile_file.open("r", encoding="utf-8") as f:
                        profile = json.load(f)
                    
                    last_updated = datetime.fromisoformat(profile["last_updated"])
                    if last_updated < cutoff_date:
                        profile_file.unlink()
                        cleaned_count += 1
                        
                except Exception:
                    # Skip corrupted files
                    continue
            
            self.metrics_service.increment_counter("personalization.profiles_cleaned", cleaned_count)
            return cleaned_count
            
        except Exception as exc:
            self.metrics_service.increment_counter("personalization.cleanup_error")
            raise RuntimeError(f"Profile cleanup failed: {exc}") from exc
