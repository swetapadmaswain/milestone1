from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from .data_pipeline import budget_to_cost_range
from .models import RecommendationRequest, RestaurantRecommendation


@dataclass
class RecommendationRunResult:
    recommendations: List[RestaurantRecommendation]
    fallback_used: bool
    relaxation_steps: List[str]


class Recommender:
    def recommend(
        self, catalog: pd.DataFrame, request: RecommendationRequest
    ) -> RecommendationRunResult:
        city = request.location.strip().lower()
        cuisine_pref = request.preferred_cuisine.strip().lower()
        min_cost, max_cost = budget_to_cost_range(request.budget)

        steps: List[str] = []
        filtered = self._apply_filters(
            catalog=catalog,
            city=city,
            min_rating=request.min_rating,
            min_cost=min_cost,
            max_cost=max_cost,
            cuisine_pref=cuisine_pref,
            apply_cuisine=True,
        )

        if filtered.empty:
            relaxed_rating = max(request.min_rating - 0.5, 0.0)
            filtered = self._apply_filters(
                catalog=catalog,
                city=city,
                min_rating=relaxed_rating,
                min_cost=min_cost,
                max_cost=max_cost,
                cuisine_pref=cuisine_pref,
                apply_cuisine=True,
            )
            if not filtered.empty:
                steps.append(
                    f"Relaxed minimum rating from {request.min_rating:.1f} to {relaxed_rating:.1f}."
                )

        if filtered.empty:
            filtered = self._apply_filters(
                catalog=catalog,
                city=city,
                min_rating=max(request.min_rating - 0.5, 0.0),
                min_cost=min_cost,
                max_cost=max_cost,
                cuisine_pref=cuisine_pref,
                apply_cuisine=False,
            )
            if not filtered.empty:
                steps.append("Relaxed cuisine match from strict to any cuisine in location.")

        if filtered.empty:
            widened_min = max(min_cost - 250, 0)
            widened_max = max_cost + 500 if max_cost != float("inf") else float("inf")
            filtered = self._apply_filters(
                catalog=catalog,
                city=city,
                min_rating=max(request.min_rating - 0.5, 0.0),
                min_cost=widened_min,
                max_cost=widened_max,
                cuisine_pref=cuisine_pref,
                apply_cuisine=False,
            )
            if not filtered.empty:
                steps.append(
                    f"Widened cost band from [{min_cost:.0f}, {max_cost if max_cost == float('inf') else f'{max_cost:.0f}'}) "
                    f"to [{widened_min:.0f}, {widened_max if widened_max == float('inf') else f'{widened_max:.0f}'}) "
                    "with location retained."
                )

        if filtered.empty:
            return RecommendationRunResult(
                recommendations=[],
                fallback_used=bool(steps),
                relaxation_steps=steps,
            )

        filtered["match_score"] = filtered.apply(
            lambda row: self._score_row(row, request.min_rating), axis=1
        )
        filtered = filtered.sort_values(
            by=["match_score", "rating", "estimated_cost", "restaurant_name"],
            ascending=[False, False, True, True],
        )
        top_n = filtered.head(request.top_n)

        recommendations = [
            RestaurantRecommendation(
                restaurant_name=row["restaurant_name"],
                location=row["location"],
                cuisine=row["cuisine"],
                estimated_cost=float(row["estimated_cost"]),
                rating=float(row["rating"]),
                match_score=round(float(row["match_score"]), 4),
                reason=self._build_reason(row, request),
            )
            for _, row in top_n.iterrows()
        ]
        return RecommendationRunResult(
            recommendations=recommendations,
            fallback_used=bool(steps),
            relaxation_steps=steps,
        )

    @staticmethod
    def _apply_filters(
        catalog: pd.DataFrame,
        city: str,
        min_rating: float,
        min_cost: float,
        max_cost: float,
        cuisine_pref: str,
        apply_cuisine: bool,
    ) -> pd.DataFrame:
        filtered = catalog.copy()
        filtered = filtered[filtered["location"] == city]
        filtered = filtered[filtered["rating"] >= min_rating]
        filtered = filtered[
            (filtered["estimated_cost"] >= min_cost) & (filtered["estimated_cost"] < max_cost)
        ]
        if apply_cuisine and cuisine_pref:
            contains_pref = filtered["cuisine"].str.contains(cuisine_pref, case=False, na=False)
            filtered = filtered[contains_pref]
        return filtered

    @staticmethod
    def _score_row(row: pd.Series, min_rating: float) -> float:
        # Deterministic weighted score for Phase 1 baseline ranking.
        rating_component = row["rating"] / 5.0
        rating_headroom = max(row["rating"] - min_rating, 0) / 5.0
        affordability = 1 / (1 + row["estimated_cost"] / 1500.0)
        return (0.6 * rating_component) + (0.2 * rating_headroom) + (0.2 * affordability)

    @staticmethod
    def _build_reason(row: pd.Series, request: RecommendationRequest) -> str:
        return (
            f"Matches {request.preferred_cuisine} cuisine preference in {request.location}, "
            f"rating {row['rating']:.1f} meets minimum {request.min_rating:.1f}, "
            f"and estimated cost {row['estimated_cost']:.0f} fits {request.budget} budget."
        )
