from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import httpx
import pandas as pd

from .config import GROQ_API_KEY, GROQ_MODEL, LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS, PROMPT_VERSION
from .data_pipeline import budget_to_cost_range
from .models import RecommendationRequest, RestaurantRecommendation


@dataclass
class RecommendationRunResult:
    recommendations: List[RestaurantRecommendation]
    fallback_used: bool
    fallback_reason: str | None
    relaxation_steps: List[str]


class Recommender:
    def recommend(self, catalog: pd.DataFrame, request: RecommendationRequest) -> RecommendationRunResult:
        city = request.location.strip().lower()
        cuisine_pref = request.preferred_cuisine.strip().lower()
        min_cost, max_cost = budget_to_cost_range(request.budget)
        steps: List[str] = []

        filtered = self._apply_filters(catalog, city, request.min_rating, min_cost, max_cost, cuisine_pref, True)
        if filtered.empty:
            relaxed = max(request.min_rating - 0.5, 0.0)
            filtered = self._apply_filters(catalog, city, relaxed, min_cost, max_cost, cuisine_pref, True)
            if not filtered.empty:
                steps.append(f"Relaxed minimum rating from {request.min_rating:.1f} to {relaxed:.1f}.")
        if filtered.empty:
            filtered = self._apply_filters(
                catalog, city, max(request.min_rating - 0.5, 0.0), min_cost, max_cost, cuisine_pref, False
            )
            if not filtered.empty:
                steps.append("Relaxed cuisine match from strict to any cuisine in location.")
        if filtered.empty:
            return RecommendationRunResult([], bool(steps), None, steps)

        filtered = filtered.copy()
        filtered["rule_score"] = filtered.apply(lambda row: self._rule_score(row, request.min_rating), axis=1)
        candidates = filtered.sort_values(
            by=["rule_score", "rating", "estimated_cost", "restaurant_name"],
            ascending=[False, False, True, True],
        ).head(max(request.top_n * 2, 8))

        llm_map, fallback_used, fallback_reason = self._llm_rank_and_explain(request, candidates)
        if fallback_used:
            candidates["llm_score"] = candidates["rule_score"]
            candidates["explanation"] = candidates.apply(
                lambda r: self._deterministic_explanation(r, request), axis=1
            )
            candidates["confidence"] = "medium"
        else:
            candidates["llm_score"] = candidates.apply(
                lambda r: llm_map.get(str(r["restaurant_name"]).strip().lower(), {}).get("llm_score", r["rule_score"]),
                axis=1,
            )
            candidates["explanation"] = candidates.apply(
                lambda r: llm_map.get(str(r["restaurant_name"]).strip().lower(), {}).get(
                    "explanation", self._deterministic_explanation(r, request)
                ),
                axis=1,
            )
            candidates["confidence"] = candidates.apply(
                lambda r: llm_map.get(str(r["restaurant_name"]).strip().lower(), {}).get("confidence", "medium"),
                axis=1,
            )

        candidates["final_score"] = 0.5 * candidates["rule_score"] + 0.5 * candidates["llm_score"]
        top_n = candidates.sort_values(
            by=["final_score", "rating", "estimated_cost", "restaurant_name"],
            ascending=[False, False, True, True],
        ).head(request.top_n)

        recs = [
            RestaurantRecommendation(
                restaurant_name=row["restaurant_name"],
                location=row["location"],
                cuisine=row["cuisine"],
                estimated_cost=float(row["estimated_cost"]),
                rating=float(row["rating"]),
                rule_score=round(float(row["rule_score"]), 4),
                llm_score=round(float(row["llm_score"]), 4),
                final_score=round(float(row["final_score"]), 4),
                explanation=str(row["explanation"]),
                confidence=str(row["confidence"]),
            )
            for _, row in top_n.iterrows()
        ]
        return RecommendationRunResult(recs, fallback_used, fallback_reason, steps)

    def _llm_rank_and_explain(
        self, request: RecommendationRequest, candidates: pd.DataFrame
    ) -> Tuple[Dict[str, Dict], bool, str | None]:
        if not GROQ_API_KEY:
            return {}, True, "Groq API key missing"
        payload = [
            {
                "restaurant_name": row["restaurant_name"],
                "location": row["location"],
                "cuisine": row["cuisine"],
                "estimated_cost": float(row["estimated_cost"]),
                "rating": float(row["rating"]),
                "rule_score": round(float(row["rule_score"]), 4),
            }
            for _, row in candidates.iterrows()
        ]
        prompt = self._build_prompt(request, payload)
        attempt = 0
        while attempt <= LLM_MAX_RETRIES:
            try:
                with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                    resp = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                        json={
                            "model": GROQ_MODEL,
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                            "messages": [
                                {"role": "system", "content": "Return strict JSON only."},
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
                valid = self._validate_llm_output(payload, parsed)
                if valid:
                    return valid, False, None
                raise RuntimeError("Invalid schema or unknown candidates")
            except Exception:
                attempt += 1
                time.sleep(0.4 * attempt)
        return {}, True, "Groq ranking/explanation failed"

    def _validate_llm_output(self, candidates: List[Dict], parsed: Dict) -> Dict[str, Dict]:
        raw_items = parsed.get("recommendations", [])
        if not isinstance(raw_items, list):
            return {}
        candidate_names = {str(c["restaurant_name"]).strip().lower() for c in candidates}
        validated = {}
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("restaurant_name", "")).strip().lower()
            if name not in candidate_names:
                continue
            llm_score = item.get("llm_score", 0.0)
            if not isinstance(llm_score, (int, float)):
                continue
            validated[name] = {
                "llm_score": max(min(float(llm_score), 1.0), 0.0),
                "explanation": str(item.get("explanation", "")).strip()[:280],
                "confidence": str(item.get("confidence", "medium")).strip().lower(),
            }
        return validated

    @staticmethod
    def _build_prompt(request: RecommendationRequest, candidates: List[Dict]) -> str:
        return (
            f"Prompt version: {PROMPT_VERSION}\n"
            "Given user preferences and candidates, output JSON:\n"
            '{"recommendations":[{"restaurant_name":"...","llm_score":0.0,"explanation":"...","confidence":"low|medium|high"}]}\n'
            "Use ONLY provided restaurant_name entries.\n"
            f"User prefs: location={request.location}, budget={request.budget}, cuisine={request.preferred_cuisine}, min_rating={request.min_rating}, extras={request.additional_preferences}\n"
            f"Candidates: {json.dumps(candidates, ensure_ascii=True)}"
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
        filtered = filtered[(filtered["estimated_cost"] >= min_cost) & (filtered["estimated_cost"] < max_cost)]
        if apply_cuisine and cuisine_pref:
            filtered = filtered[filtered["cuisine"].str.contains(cuisine_pref, case=False, na=False)]
        return filtered

    @staticmethod
    def _rule_score(row: pd.Series, min_rating: float) -> float:
        rating_component = row["rating"] / 5.0
        rating_headroom = max(row["rating"] - min_rating, 0) / 5.0
        affordability = 1 / (1 + row["estimated_cost"] / 1500.0)
        return (0.6 * rating_component) + (0.2 * rating_headroom) + (0.2 * affordability)

    @staticmethod
    def _deterministic_explanation(row: pd.Series, request: RecommendationRequest) -> str:
        return (
            f"Matches {request.preferred_cuisine} in {request.location}, rating {row['rating']:.1f} "
            f"meets minimum {request.min_rating:.1f}, and estimated cost {row['estimated_cost']:.0f} "
            f"fits {request.budget} budget."
        )
