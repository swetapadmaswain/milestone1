from __future__ import annotations

import hashlib
import json
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Tuple

import httpx
import pandas as pd

from .config import (
    CACHE_TTL_SECONDS,
    EXPERIMENT_ASSIGNMENTS,
    FEEDBACK_LOG,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_TIMEOUT_SECONDS,
    PROFILE_DIR,
    PROMPT_VERSION,
    RATE_LIMIT_PER_MIN,
    ensure_dirs,
)
from .data_pipeline import budget_to_cost_range
from .models import FeedbackRequest, RecommendationRequest, RestaurantRecommendation


@dataclass
class RecommendationRunResult:
    recommendations: List[RestaurantRecommendation]
    fallback_used: bool
    fallback_reason: str | None
    relaxation_steps: List[str]
    experiment_variant: str


class MetricsService:
    def __init__(self) -> None:
        self.counters = defaultdict(int)
        self.timings = defaultdict(list)
        self.lock = Lock()

    def inc(self, key: str, value: int = 1) -> None:
        with self.lock:
            self.counters[key] += value

    def observe_ms(self, key: str, elapsed_ms: float) -> None:
        with self.lock:
            self.timings[key].append(elapsed_ms)

    def snapshot(self) -> Dict:
        with self.lock:
            latency = {}
            for key, values in self.timings.items():
                if not values:
                    continue
                latency[key] = {
                    "count": len(values),
                    "avg_ms": round(sum(values) / len(values), 2),
                    "p95_ms": round(sorted(values)[max(int(len(values) * 0.95) - 1, 0)], 2),
                }
            return {"counters": dict(self.counters), "latency": latency}


class GuardrailService:
    INPUT_PATTERN = re.compile(r"(ignore previous|system prompt|developer instructions)", re.I)

    def sanitize_text(self, value: str) -> str:
        cleaned = " ".join(value.split())
        return cleaned[:200]

    def sanitize_request(self, request: RecommendationRequest) -> RecommendationRequest:
        prefs = []
        for pref in request.additional_preferences or []:
            if not self.INPUT_PATTERN.search(pref):
                prefs.append(self.sanitize_text(pref))
        request.additional_preferences = prefs
        request.location = self.sanitize_text(request.location)
        request.preferred_cuisine = self.sanitize_text(request.preferred_cuisine)
        return request

    def validate_llm_output(self, candidate_names: set[str], items: List[Dict]) -> List[Dict]:
        safe = []
        for item in items:
            name = str(item.get("restaurant_name", "")).strip().lower()
            if name in candidate_names:
                safe.append(item)
        return safe


class CacheService:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self.ttl = ttl_seconds
        self.data: Dict[str, Tuple[float, Dict]] = {}
        self.lock = Lock()

    def make_key(self, payload: Dict) -> str:
        canonical = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Dict | None:
        now = time.time()
        with self.lock:
            item = self.data.get(key)
            if not item:
                return None
            expires_at, value = item
            if now > expires_at:
                del self.data[key]
                return None
            return value

    def set(self, key: str, value: Dict) -> None:
        with self.lock:
            self.data[key] = (time.time() + self.ttl, value)


class RateLimiter:
    def __init__(self, limit_per_minute: int = RATE_LIMIT_PER_MIN) -> None:
        self.limit = limit_per_minute
        self.events = defaultdict(deque)
        self.lock = Lock()

    def allow(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - 60
        with self.lock:
            q = self.events[client_key]
            while q and q[0] < window_start:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


class LLMService:
    def __init__(self, metrics: MetricsService, guardrails: GuardrailService) -> None:
        self.metrics = metrics
        self.guardrails = guardrails

    def explain_with_groq(
        self, request: RecommendationRequest, ranked_rows: List[Dict]
    ) -> Tuple[Dict[str, Dict], bool, str | None]:
        if not GROQ_API_KEY:
            self.metrics.inc("fallback.groq_key_missing")
            return {}, True, "Groq API key missing"

        prompt = self._build_prompt(request, ranked_rows)
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": GROQ_MODEL,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a strict recommendation explainer. Output JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                    },
                )
            elapsed_ms = (time.perf_counter() - started) * 1000
            self.metrics.observe_ms("llm.groq_call", elapsed_ms)
            if response.status_code != 200:
                self.metrics.inc("fallback.groq_http_error")
                return {}, True, f"Groq HTTP error: {response.status_code}"

            body = response.json()
            self.metrics.inc("llm.calls")
            self.metrics.inc("llm.tokens_prompt", int(body.get("usage", {}).get("prompt_tokens", 0)))
            self.metrics.inc("llm.tokens_completion", int(body.get("usage", {}).get("completion_tokens", 0)))

            text = body["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            raw_items = parsed.get("recommendations", [])
            valid_items = self.guardrails.validate_llm_output(
                {r["restaurant_name"].strip().lower() for r in ranked_rows}, raw_items
            )
            mapped = {
                item["restaurant_name"].strip().lower(): {
                    "llm_score": max(min(float(item.get("llm_score", 0.5)), 1.0), 0.0),
                    "explanation": str(item.get("explanation", "")).strip()[:280],
                    "confidence": str(item.get("confidence", "medium")).lower(),
                }
                for item in valid_items
            }
            if not mapped:
                self.metrics.inc("fallback.groq_invalid_payload")
                return {}, True, "Groq output invalid after guardrails"
            return mapped, False, None
        except Exception:
            self.metrics.inc("fallback.groq_exception")
            return {}, True, "Groq timeout/error"

    @staticmethod
    def _build_prompt(request: RecommendationRequest, ranked_rows: List[Dict]) -> str:
        return (
            f"Prompt version: {PROMPT_VERSION}\n"
            "Given user preferences and candidate restaurants, return valid JSON:\n"
            '{"recommendations":[{"restaurant_name":"...","llm_score":0.0,"explanation":"...","confidence":"low|medium|high"}]}\n'
            "Use only provided restaurant_name values.\n"
            f"User: location={request.location}, budget={request.budget}, cuisine={request.preferred_cuisine}, min_rating={request.min_rating}\n"
            f"Candidates: {json.dumps(ranked_rows, ensure_ascii=True)}"
        )


class PersonalizationService:
    DECAY_HALFLIFE_DAYS = 30.0

    def __init__(self) -> None:
        ensure_dirs()

    def capture_feedback(self, feedback: FeedbackRequest) -> float:
        profile = self._load_profile(self._user_key(feedback.user_id, feedback.session_id))
        weight = self._signal_weight(feedback.signal_name, feedback.signal_type)
        signed_value = weight * feedback.value
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "restaurant_name": feedback.restaurant_name.strip().lower(),
            "location": feedback.location.strip().lower(),
            "cuisine": feedback.cuisine.strip().lower(),
            "signal_name": feedback.signal_name,
            "signal_type": feedback.signal_type,
            "signed_value": signed_value,
        }
        profile["events"].append(event)
        self._save_profile(self._user_key(feedback.user_id, feedback.session_id), profile)
        with FEEDBACK_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"user_key": self._user_key(feedback.user_id, feedback.session_id), **event}))
            handle.write("\n")
        return signed_value

    def profile_summary(self, user_id: str | None, session_id: str) -> Dict:
        user_key = self._user_key(user_id, session_id)
        profile = self._load_profile(user_key)
        cuisine_scores, budget_scores = self._aggregate(profile["events"])
        return {
            "user_key": user_key,
            "total_events": len(profile["events"]),
            "top_cuisines": cuisine_scores,
            "favored_budget_bands": budget_scores,
        }

    def personalization_score(self, row: pd.Series, user_id: str | None, session_id: str) -> float:
        user_key = self._user_key(user_id, session_id)
        profile = self._load_profile(user_key)
        if not profile["events"]:
            return 0.0
        cuisine_scores, budget_scores = self._aggregate(profile["events"])
        cuisine_score = cuisine_scores.get(str(row["cuisine"]).lower(), 0.0)
        budget_band = self._cost_to_band(float(row["estimated_cost"]))
        budget_score = budget_scores.get(budget_band, 0.0)
        return max(min((0.7 * cuisine_score) + (0.3 * budget_score), 1.0), -1.0)

    def _aggregate(self, events: List[Dict]) -> Tuple[Dict[str, float], Dict[str, float]]:
        now = datetime.now(timezone.utc)
        cuisine_raw: Dict[str, float] = {}
        budget_raw: Dict[str, float] = {}
        for event in events:
            timestamp = datetime.fromisoformat(event["timestamp"])
            age_days = max((now - timestamp).total_seconds() / 86400.0, 0.0)
            decay = 0.5 ** (age_days / self.DECAY_HALFLIFE_DAYS)
            score = event["signed_value"] * decay
            cuisine = event["cuisine"]
            budget_band = self._cost_to_band_from_event(event)
            cuisine_raw[cuisine] = cuisine_raw.get(cuisine, 0.0) + score
            budget_raw[budget_band] = budget_raw.get(budget_band, 0.0) + score
        return self._normalize_scores(cuisine_raw), self._normalize_scores(budget_raw)

    @staticmethod
    def _normalize_scores(raw: Dict[str, float]) -> Dict[str, float]:
        if not raw:
            return {}
        max_abs = max(abs(v) for v in raw.values()) or 1.0
        return {k: round(v / max_abs, 4) for k, v in raw.items()}

    @staticmethod
    def _signal_weight(signal_name: str, signal_type: str) -> float:
        explicit = {"like": 1.0, "dislike": -1.0}
        implicit = {"click": 0.3, "dwell": 0.5, "conversion": 1.0, "skip": -0.2}
        table = explicit if signal_type == "explicit" else implicit
        return table.get(signal_name, 0.0)

    @staticmethod
    def _cost_to_band(value: float) -> str:
        if value < 500:
            return "low"
        if value < 1500:
            return "medium"
        return "high"

    @staticmethod
    def _cost_to_band_from_event(event: Dict) -> str:
        return "medium" if event.get("signal_name") in {"conversion", "like"} else "low"

    @staticmethod
    def _user_key(user_id: str | None, session_id: str) -> str:
        return (user_id or "").strip().lower() or f"session:{session_id.strip().lower()}"

    def _load_profile(self, user_key: str) -> Dict:
        path = PROFILE_DIR / f"{self._safe_filename(user_key)}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"user_key": user_key, "events": []}

    def _save_profile(self, user_key: str, payload: Dict) -> None:
        path = PROFILE_DIR / f"{self._safe_filename(user_key)}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_filename(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


class ExperimentationService:
    VARIANTS = {
        "control": {"rule": 0.6, "llm": 0.4, "personal": 0.0},
        "balanced": {"rule": 0.45, "llm": 0.3, "personal": 0.25},
        "personal_heavy": {"rule": 0.3, "llm": 0.2, "personal": 0.5},
    }

    def __init__(self) -> None:
        ensure_dirs()

    def assign_variant(self, key: str) -> str:
        assignments = self._load_assignments()
        if key not in assignments:
            bucket = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % len(self.VARIANTS)
            assignments[key] = list(self.VARIANTS.keys())[bucket]
            EXPERIMENT_ASSIGNMENTS.write_text(json.dumps(assignments, indent=2), encoding="utf-8")
        return assignments[key]

    def weights_for(self, variant: str) -> Dict[str, float]:
        return self.VARIANTS.get(variant, self.VARIANTS["control"])

    @staticmethod
    def _load_assignments() -> Dict[str, str]:
        if not EXPERIMENT_ASSIGNMENTS.exists():
            return {}
        return json.loads(EXPERIMENT_ASSIGNMENTS.read_text(encoding="utf-8"))


class Recommender:
    def __init__(
        self,
        personalization: PersonalizationService,
        experiments: ExperimentationService,
        llm_service: LLMService,
    ):
        self.personalization = personalization
        self.experiments = experiments
        self.llm = llm_service

    def recommend(self, catalog: pd.DataFrame, request: RecommendationRequest) -> RecommendationRunResult:
        city = request.location.strip().lower()
        cuisine_pref = request.preferred_cuisine.strip().lower()
        min_cost, max_cost = budget_to_cost_range(request.budget)
        user_key = (request.user_id or "").strip().lower() or f"session:{request.session_id.strip().lower()}"
        variant = self.experiments.assign_variant(user_key)
        weights = self.experiments.weights_for(variant)

        steps: List[str] = []
        filtered = self._apply_filters(catalog, city, request.min_rating, min_cost, max_cost, cuisine_pref, True)
        if filtered.empty:
            relaxed_rating = max(request.min_rating - 0.5, 0.0)
            filtered = self._apply_filters(catalog, city, relaxed_rating, min_cost, max_cost, cuisine_pref, True)
            if not filtered.empty:
                steps.append(
                    f"Relaxed minimum rating from {request.min_rating:.1f} to {relaxed_rating:.1f}."
                )
        if filtered.empty:
            filtered = self._apply_filters(
                catalog, city, max(request.min_rating - 0.5, 0.0), min_cost, max_cost, cuisine_pref, False
            )
            if not filtered.empty:
                steps.append("Relaxed cuisine match from strict to any cuisine in location.")
        if filtered.empty:
            return RecommendationRunResult([], bool(steps), None, steps, variant)

        filtered = filtered.copy()
        filtered["rule_score"] = filtered.apply(lambda row: self._rule_score(row, request.min_rating), axis=1)
        filtered["llm_seed"] = filtered.apply(lambda row: self._llm_style_score(row, cuisine_pref), axis=1)
        filtered["personalization_score"] = filtered.apply(
            lambda row: self.personalization.personalization_score(row, request.user_id, request.session_id), axis=1
        )
        filtered["final_score"] = (
            weights["rule"] * filtered["rule_score"]
            + weights["llm"] * filtered["llm_score"]
            + weights["personal"] * filtered["personalization_score"]
        )
        filtered = filtered.sort_values(
            by=["final_score", "rating", "estimated_cost", "restaurant_name"],
            ascending=[False, False, True, True],
        )
        top_n = filtered.head(request.top_n)
        ranked_payload = [
            {
                "restaurant_name": row["restaurant_name"],
                "cuisine": row["cuisine"],
                "rating": float(row["rating"]),
                "estimated_cost": float(row["estimated_cost"]),
                "final_score": round(float(row["final_score"]), 4),
            }
            for _, row in top_n.iterrows()
        ]
        llm_map, fallback_used, fallback_reason = self.llm.explain_with_groq(request, ranked_payload)
        filtered["llm_score"] = filtered.apply(
            lambda row: llm_map.get(str(row["restaurant_name"]).strip().lower(), {}).get("llm_score", row["llm_seed"]),
            axis=1,
        )
        recs = []
        for _, row in top_n.iterrows():
            key = str(row["restaurant_name"]).strip().lower()
            llm_data = llm_map.get(key, {})
            breakdown = {
                "rule_score": round(float(row["rule_score"]), 4),
                "llm_score": round(float(row["llm_score"]), 4),
                "personalization_score": round(float(row["personalization_score"]), 4),
                "weight_rule": weights["rule"],
                "weight_llm": weights["llm"],
                "weight_personal": weights["personal"],
            }
            recs.append(
                RestaurantRecommendation(
                    restaurant_name=row["restaurant_name"],
                    location=row["location"],
                    cuisine=row["cuisine"],
                    estimated_cost=float(row["estimated_cost"]),
                    rating=float(row["rating"]),
                    final_score=round(float(row["final_score"]), 4),
                    score_breakdown=breakdown,
                    reason=self._build_reason(row, request, breakdown),
                    explanation=llm_data.get(
                        "explanation",
                        "Deterministic explanation mode due to LLM fallback.",
                    ),
                    confidence=llm_data.get("confidence", "medium"),
                )
            )
        return RecommendationRunResult(recs, fallback_used, fallback_reason, steps, variant)

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
            filtered = filtered[filtered["cuisine"].str.contains(cuisine_pref, case=False, na=False)]
        return filtered

    @staticmethod
    def _rule_score(row: pd.Series, min_rating: float) -> float:
        rating_component = row["rating"] / 5.0
        rating_headroom = max(row["rating"] - min_rating, 0) / 5.0
        affordability = 1 / (1 + row["estimated_cost"] / 1500.0)
        return (0.6 * rating_component) + (0.2 * rating_headroom) + (0.2 * affordability)

    @staticmethod
    def _llm_style_score(row: pd.Series, cuisine_pref: str) -> float:
        cuisine_match = 1.0 if cuisine_pref and cuisine_pref in str(row["cuisine"]).lower() else 0.5
        quality = row["rating"] / 5.0
        price_penalty = min(row["estimated_cost"] / 3000.0, 0.35)
        return max((0.55 * cuisine_match) + (0.45 * quality) - price_penalty, 0.0)

    @staticmethod
    def _build_reason(
        row: pd.Series, request: RecommendationRequest, score_breakdown: Dict[str, float]
    ) -> str:
        return (
            f"Fits {request.preferred_cuisine} in {request.location}, rating {row['rating']:.1f} "
            f"clears minimum {request.min_rating:.1f}, blended with "
            f"rule={score_breakdown['weight_rule']:.2f}, llm={score_breakdown['weight_llm']:.2f}, "
            f"personalization={score_breakdown['weight_personal']:.2f}."
        )
