import json
import time
from typing import Any, Dict, List, Tuple, Optional
import httpx

from app.core.config import settings
from app.services.metrics_service import MetricsService


class LLMService:
    """Service for LLM integration with Groq API."""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
    
    async def explain_recommendations(
        self, 
        request_data: Dict, 
        candidates: List[Dict]
    ) -> Tuple[Dict[str, Dict], bool, Optional[str]]:
        """Generate LLM explanations for restaurant recommendations."""
        if not settings.GROQ_API_KEY:
            self.metrics_service.increment_counter("llm.api_key_missing")
            return {}, True, "Groq API key not configured"
        
        prompt = self._build_prompt(request_data, candidates)
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a strict recommendation explainer. Output valid JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": settings.GROQ_MAX_TOKENS,
                    },
                )
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics_service.observe_latency("llm.groq_call", elapsed_ms)
            
            if response.status_code != 200:
                self.metrics_service.increment_counter("llm.http_error")
                return {}, True, f"Groq HTTP error: {response.status_code}"
            
            body = response.json()
            self._record_token_usage(body)
            
            text = body["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            
            # Validate and process response
            raw_items = parsed.get("recommendations", [])
            valid_items = self._validate_llm_output(candidates, raw_items)
            
            mapped = {
                item["restaurant_name"].strip().lower(): {
                    "llm_score": max(min(float(item.get("llm_score", 0.5)), 1.0), 0.0),
                    "explanation": str(item.get("explanation", "")).strip()[:280],
                    "confidence": str(item.get("confidence", "medium")).lower(),
                }
                for item in valid_items
            }
            
            if not mapped:
                self.metrics_service.increment_counter("llm.invalid_output")
                return {}, True, "No valid recommendations in LLM output"
            
            self.metrics_service.increment_counter("llm.success")
            return mapped, False, None
            
        except json.JSONDecodeError as exc:
            self.metrics_service.increment_counter("llm.json_error")
            return {}, True, f"Invalid JSON response: {exc}"
        except httpx.TimeoutException:
            self.metrics_service.increment_counter("llm.timeout")
            return {}, True, "LLM request timeout"
        except Exception as exc:
            self.metrics_service.increment_counter("llm.exception")
            return {}, True, f"LLM service error: {exc}"
    
    def _build_prompt(self, request_data: Dict, candidates: List[Dict]) -> str:
        """Build prompt for LLM recommendation explanation."""
        return (
            f"Prompt version: {settings.PROMPT_VERSION}\n"
            "Given user preferences and candidate restaurants, return valid JSON:\n"
            '{"recommendations":[{"restaurant_name":"...","llm_score":0.0,"explanation":"...","confidence":"low|medium|high"}]}\n'
            "Use only provided restaurant_name values.\n"
            f"User: location={request_data.get('location')}, budget={request_data.get('budget')}, "
            f"cuisine={request_data.get('preferred_cuisine')}, min_rating={request_data.get('min_rating')}\n"
            f"Candidates: {json.dumps(candidates, ensure_ascii=True)}"
        )
    
    def _validate_llm_output(self, candidates: List[Dict], llm_items: List[Dict]) -> List[Dict]:
        """Validate LLM output against known candidates."""
        valid_names = {candidate["restaurant_name"].strip().lower() for candidate in candidates}
        valid_items = []
        
        for item in llm_items:
            restaurant_name = str(item.get("restaurant_name", "")).strip().lower()
            if restaurant_name in valid_names:
                valid_items.append(item)
        
        return valid_items
    
    def _record_token_usage(self, response_body: Dict) -> None:
        """Record token usage metrics."""
        usage = response_body.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        self.metrics_service.increment_counter("llm.tokens_prompt", prompt_tokens)
        self.metrics_service.increment_counter("llm.tokens_completion", completion_tokens)
        self.metrics_service.increment_counter("llm.tokens_total", total_tokens)
        self.metrics_service.set_gauge("llm.last_call_prompt_tokens", prompt_tokens)
        self.metrics_service.set_gauge("llm.last_call_completion_tokens", completion_tokens)
    
    async def health_check(self) -> bool:
        """Check LLM service health."""
        if not settings.GROQ_API_KEY:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 10,
                    },
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get LLM model information."""
        return {
            "model": settings.GROQ_MODEL,
            "timeout_seconds": settings.GROQ_TIMEOUT_SECONDS,
            "max_tokens": settings.GROQ_MAX_TOKENS,
            "prompt_version": settings.PROMPT_VERSION,
            "api_configured": bool(settings.GROQ_API_KEY),
        }


class FallbackLLMService:
    """Fallback service when LLM is unavailable."""
    
    def __init__(self):
        self.explanations = {
            "high": "Highly recommended based on your preferences and ratings.",
            "medium": "Good match for your criteria with solid ratings.",
            "low": "Basic match for your requirements.",
        }
    
    async def explain_recommendations(
        self, 
        request_data: Dict, 
        candidates: List[Dict]
    ) -> Tuple[Dict[str, Dict], bool, Optional[str]]:
        """Generate fallback explanations."""
        mapped = {}
        
        for candidate in candidates:
            name = candidate["restaurant_name"].strip().lower()
            rating = candidate.get("rating", 0)
            
            # Determine confidence based on rating
            if rating >= 4.0:
                confidence = "high"
                explanation = f"Excellent choice with high rating ({rating}/5). Matches your preferences well."
            elif rating >= 3.5:
                confidence = "medium"
                explanation = f"Good option with solid rating ({rating}/5). Fits your criteria."
            else:
                confidence = "low"
                explanation = f"Basic match with rating ({rating}/5). Consider other options first."
            
            mapped[name] = {
                "llm_score": min(rating / 5.0, 1.0),  # Normalize rating to 0-1
                "explanation": explanation[:280],
                "confidence": confidence,
            }
        
        return mapped, True, "Using deterministic fallback explanations"
    
    async def health_check(self) -> bool:
        """Fallback service is always healthy."""
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get fallback model information."""
        return {
            "model": "deterministic_fallback",
            "type": "rule_based",
            "description": "Fallback service when LLM is unavailable",
        }
