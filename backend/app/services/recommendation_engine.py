from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import pandas as pd
import asyncio

from app.models.schemas import RecommendationRequest, RestaurantRecommendation
from app.services.data_pipeline import DataPipeline, budget_to_cost_range
from app.services.personalization_service import PersonalizationService
from app.services.experimentation_service import ExperimentationService
from app.services.llm_service import LLMService, FallbackLLMService
from app.services.metrics_service import MetricsService


@dataclass
class RecommendationResult:
    """Result of recommendation generation."""
    total_candidates: int
    returned_count: int
    recommendations: List[RestaurantRecommendation]
    fallback_used: bool
    fallback_reason: Optional[str]
    relaxation_steps: List[str]
    experiment_variant: str
    prompt_version: str


class RecommendationEngine:
    """Main recommendation engine that orchestrates all services."""
    
    def __init__(
        self,
        personalization_service: PersonalizationService,
        experimentation_service: ExperimentationService,
        llm_service: LLMService,
        metrics_service: MetricsService,
    ):
        self.personalization_service = personalization_service
        self.experimentation_service = experimentation_service
        self.llm_service = llm_service
        self.metrics_service = metrics_service
        
        # Initialize fallback LLM service
        self.fallback_llm = FallbackLLMService()
    
    async def recommend(self, catalog: pd.DataFrame, request: RecommendationRequest) -> RecommendationResult:
        """Generate restaurant recommendations."""
        try:
            # Get user key for personalization and experimentation
            user_key = self._get_user_key(request.user_id, request.session_id)
            
            # Assign experiment variant
            experiment_variant = await self.experimentation_service.assign_variant(user_key, "recommendation_weights")
            
            # Get experiment weights
            weights = self.experimentation_service.get_weights_for_variant(experiment_variant)
            
            # Apply filters and get candidates
            filtered_df, relaxation_steps = await self._apply_filters(catalog, request)
            
            if filtered_df.empty:
                return RecommendationResult(
                    total_candidates=len(catalog),
                    returned_count=0,
                    recommendations=[],
                    fallback_used=False,
                    fallback_reason="No restaurants match the specified criteria",
                    relaxation_steps=relaxation_steps,
                    experiment_variant=experiment_variant,
                    prompt_version="v1-fallback",
                )
            
            # Calculate scores
            scored_df = await self._calculate_scores(filtered_df, request, weights)
            
            # Sort and get top recommendations
            top_df = scored_df.head(request.top_n)
            
            # Generate LLM explanations
            recommendations = await self._generate_recommendations(top_df, request, weights)
            
            # Track experiment event
            await self._track_recommendation_event(user_key, experiment_variant, request, recommendations)
            
            self.metrics_service.increment_counter("recommendations.success")
            
            return RecommendationResult(
                total_candidates=len(catalog),
                returned_count=len(recommendations),
                recommendations=recommendations,
                fallback_used=False,
                fallback_reason=None,
                relaxation_steps=relaxation_steps,
                experiment_variant=experiment_variant,
                prompt_version="v1-groq-backend",
            )
            
        except Exception as exc:
            self.metrics_service.increment_counter("recommendations.error")
            raise RuntimeError(f"Recommendation generation failed: {exc}") from exc
    
    async def _apply_filters(self, catalog: pd.DataFrame, request: RecommendationRequest) -> Tuple[pd.DataFrame, List[str]]:
        """Apply filters to the restaurant catalog."""
        relaxation_steps = []
        
        # Normalize inputs
        location = request.location.strip().lower()
        cuisine_pref = request.preferred_cuisine.strip().lower()
        min_cost, max_cost = budget_to_cost_range(request.budget)
        
        # Initial filtering
        filtered = catalog.copy()
        
        # Location filter
        filtered = filtered[filtered["location"] == location]
        if filtered.empty:
            relaxation_steps.append(f"No restaurants found in '{location}'. Consider nearby locations.")
            return filtered, relaxation_steps
        
        # Rating filter
        rating_filtered = filtered[filtered["rating"] >= request.min_rating]
        if rating_filtered.empty and request.min_rating > 0:
            # Relax rating constraint
            relaxed_rating = max(request.min_rating - 0.5, 0.0)
            rating_filtered = filtered[filtered["rating"] >= relaxed_rating]
            if not rating_filtered.empty:
                relaxation_steps.append(f"Relaxed minimum rating from {request.min_rating:.1f} to {relaxed_rating:.1f}")
        
        filtered = rating_filtered
        
        # Cost filter
        cost_filtered = filtered[
            (filtered["estimated_cost"] >= min_cost) & 
            (filtered["estimated_cost"] <= max_cost)
        ]
        if cost_filtered.empty:
            # Relax cost constraint
            cost_filtered = filtered[filtered["estimated_cost"] >= min_cost]
            if not cost_filtered.empty:
                relaxation_steps.append(f"Relaxed maximum cost constraint")
        
        filtered = cost_filtered
        
        # Cuisine filter (if specified)
        if cuisine_pref:
            cuisine_filtered = filtered[
                filtered["cuisine"].str.contains(cuisine_pref, case=False, na=False)
            ]
            if cuisine_filtered.empty:
                # Relax cuisine constraint
                relaxation_steps.append("Relaxed cuisine constraint to include all cuisines")
            else:
                filtered = cuisine_filtered
        
        return filtered, relaxation_steps
    
    async def _calculate_scores(self, df: pd.DataFrame, request: RecommendationRequest, weights: Dict[str, float]) -> pd.DataFrame:
        """Calculate scores for all restaurants."""
        df = df.copy()
        
        # Rule-based score
        df["rule_score"] = df.apply(lambda row: self._calculate_rule_score(row, request), axis=1)
        
        # LLM seed score (will be updated after LLM call)
        df["llm_seed"] = df.apply(lambda row: self._calculate_llm_seed_score(row, request), axis=1)
        
        # Personalization score - compute async scores in parallel
        personalization_scores = await asyncio.gather(*[
            self.personalization_service.personalization_score(
                row.to_dict(), request.user_id, request.session_id
            )
            for _, row in df.iterrows()
        ])
        df["personalization_score"] = personalization_scores
        
        # Calculate final score
        df["final_score"] = (
            weights["rule"] * df["rule_score"] +
            weights["llm"] * df["llm_seed"] +
            weights["personal"] * df["personalization_score"]
        )
        
        return df
    
    def _calculate_rule_score(self, row: pd.Series, request: RecommendationRequest) -> float:
        """Calculate rule-based score for a restaurant."""
        score = 0.0
        
        # Rating component (40% of rule score)
        rating_score = min(row["rating"] / 5.0, 1.0)
        score += 0.4 * rating_score
        
        # Cost component (30% of rule score)
        min_cost, max_cost = budget_to_cost_range(request.budget)
        if row["estimated_cost"] <= max_cost:
            cost_score = 1.0 - (row["estimated_cost"] - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 1.0
            cost_score = max(0.0, min(1.0, cost_score))
            score += 0.3 * cost_score
        
        # Cuisine match component (30% of rule score)
        if request.preferred_cuisine:
            cuisines = [c.strip().lower() for c in row["cuisine"].split(",")]
            if request.preferred_cuisine.lower() in cuisines:
                score += 0.3
            else:
                score += 0.1  # Partial credit for not matching
        else:
            score += 0.3  # Full credit if no preference
        
        return score
    
    def _calculate_llm_seed_score(self, row: pd.Series, request: RecommendationRequest) -> float:
        """Calculate initial LLM seed score (will be updated by actual LLM)."""
        # Simple heuristic based on rating and cost
        rating_score = min(row["rating"] / 5.0, 1.0)
        cost_score = 0.5  # Neutral cost score until LLM evaluates
        
        return (rating_score + cost_score) / 2.0
    
    async def _generate_recommendations(
        self, 
        df: pd.DataFrame, 
        request: RecommendationRequest, 
        weights: Dict[str, float]
    ) -> List[RestaurantRecommendation]:
        """Generate final recommendations with LLM explanations."""
        # Prepare candidates for LLM
        candidates = df.to_dict("records")
        
        # Get LLM explanations
        request_data = request.model_dump()
        llm_results, fallback_used, fallback_reason = await self.llm_service.explain_recommendations(
            request_data, candidates
        )
        
        # If LLM failed, use fallback
        if fallback_used:
            self.metrics_service.increment_counter("recommendations.llm_fallback")
            llm_results, _, _ = await self.fallback_llm.explain_recommendations(request_data, candidates)
        
        # Update LLM scores in dataframe
        df["llm_score"] = df.apply(
            lambda row: llm_results.get(
                str(row["restaurant_name"]).strip().lower(), 
                {}
            ).get("llm_score", row["llm_seed"]),
            axis=1
        )
        
        # Recalculate final scores with actual LLM scores
        df["final_score"] = (
            weights["rule"] * df["rule_score"] +
            weights["llm"] * df["llm_score"] +
            weights["personal"] * df["personalization_score"]
        )
        
        # Sort by final score
        df = df.sort_values("final_score", ascending=False)
        
        # Generate recommendation objects
        recommendations = []
        for _, row in df.iterrows():
            restaurant_name = str(row["restaurant_name"]).strip().lower()
            llm_data = llm_results.get(restaurant_name, {})
            
            score_breakdown = {
                "rule_score": round(float(row["rule_score"]), 4),
                "llm_score": round(float(row["llm_score"]), 4),
                "personalization_score": round(float(row["personalization_score"]), 4),
                "weight_rule": weights["rule"],
                "weight_llm": weights["llm"],
                "weight_personal": weights["personal"],
            }
            
            reason = self._build_reason(row, request, score_breakdown)
            explanation = llm_data.get("explanation", "AI explanation not available")
            confidence = llm_data.get("confidence", "medium")
            
            recommendation = RestaurantRecommendation(
                restaurant_name=row["restaurant_name"],
                location=row["location"],
                cuisine=row["cuisine"],
                estimated_cost=float(row["estimated_cost"]),
                rating=float(row["rating"]),
                final_score=round(float(row["final_score"]), 4),
                score_breakdown=score_breakdown,
                reason=reason,
                explanation=explanation,
                confidence=confidence,
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _build_reason(self, row: pd.Series, request: RecommendationRequest, score_breakdown: Dict[str, float]) -> str:
        """Build a reason for the recommendation."""
        reasons = []
        
        # Location match
        if row["location"].lower() == request.location.lower():
            reasons.append(f"Located in {request.location}")
        
        # Rating
        if row["rating"] >= request.min_rating:
            reasons.append(f"High rating ({row['rating']}/5)")
        
        # Cost
        min_cost, max_cost = budget_to_cost_range(request.budget)
        if row["estimated_cost"] <= max_cost:
            reasons.append(f"Within budget (â¹{row['estimated_cost']:.0f})")
        
        # Cuisine
        if request.preferred_cuisine and request.preferred_cuisine.lower() in row["cuisine"].lower():
            reasons.append(f"Matches {request.preferred_cuisine} preference")
        
        # Score breakdown
        reasons.append(f"Score: {score_breakdown['rule_score']:.2f} (rules) + {score_breakdown['llm_score']:.2f} (AI) + {score_breakdown['personalization_score']:.2f} (personal)")
        
        return "; ".join(reasons)
    
    def _get_user_key(self, user_id: Optional[str], session_id: str) -> str:
        """Generate user key for tracking."""
        if user_id:
            return f"user:{user_id}"
        else:
            return f"session:{session_id}"
    
    async def _track_recommendation_event(
        self, 
        user_key: str, 
        variant: str, 
        request: RecommendationRequest, 
        recommendations: List[RestaurantRecommendation]
    ) -> None:
        """Track recommendation generation for experiment analytics."""
        try:
            event_data = {
                "event_type": "recommendation_generated",
                "request": request.model_dump(),
                "num_recommendations": len(recommendations),
                "avg_score": sum(rec.final_score for rec in recommendations) / len(recommendations) if recommendations else 0,
                "top_restaurant": recommendations[0].restaurant_name if recommendations else None,
            }
            
            await self.experimentation_service.track_event(user_key, "recommendation_weights", variant, event_data)
            
        except Exception as exc:
            # Don't fail the recommendation if tracking fails
            self.metrics_service.increment_counter("recommendations.tracking_error")
            print(f"Failed to track recommendation event: {exc}")
