import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from .config import API_KEY, PROMPT_VERSION
from .data_pipeline import DataPipeline
from .models import (
    FeedbackRequest,
    FeedbackResponse,
    IngestionResponse,
    RecommendationRequest,
    RecommendationResponse,
    UserProfileResponse,
)
from .services import (
    CacheService,
    ExperimentationService,
    GuardrailService,
    LLMService,
    MetricsService,
    PersonalizationService,
    RateLimiter,
    Recommender,
)

app = FastAPI(title="Phase 4 Production Recommender", version="4.0.0")

pipeline = DataPipeline()
metrics = MetricsService()
guardrails = GuardrailService()
cache = CacheService()
rate_limiter = RateLimiter()
personalization_service = PersonalizationService()
experiment_service = ExperimentationService()
llm_service = LLMService(metrics, guardrails)
recommender = Recommender(personalization_service, experiment_service, llm_service)
UI_FILE = Path(__file__).resolve().parent / "ui" / "index.html"


def _check_auth(x_api_key: str | None) -> None:
    if API_KEY and x_api_key != API_KEY:
        metrics.inc("auth.rejected")
        raise HTTPException(status_code=401, detail="Invalid API key.")


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    metrics.observe_ms(f"http.{request.url.path}", elapsed_ms)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "phase": "4", "prompt_version": PROMPT_VERSION}


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


@app.get("/", response_class=HTMLResponse)
def ui_home():
    if not UI_FILE.exists():
        raise HTTPException(status_code=500, detail="UI file missing.")
    return UI_FILE.read_text(encoding="utf-8")


@app.post("/ingest", response_model=IngestionResponse)
def ingest_data(x_api_key: str | None = Header(default=None)):
    _check_auth(x_api_key)
    try:
        result = pipeline.ingest_and_prepare()
        return IngestionResponse(
            message="Ingestion and preprocessing completed.",
            raw_records=result.raw_records,
            prepared_records=result.prepared_records,
        )
    except Exception as exc:
        metrics.inc("errors.ingest")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    req: Request,
    x_api_key: str | None = Header(default=None),
):
    _check_auth(x_api_key)
    client_key = req.client.host if req.client else "unknown"
    if not rate_limiter.allow(client_key):
        metrics.inc("rate_limited")
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    try:
        cleaned_request = guardrails.sanitize_request(request)
        cache_payload = cleaned_request.model_dump()
        cache_key = cache.make_key(cache_payload)
        cached = cache.get(cache_key)
        if cached:
            metrics.inc("cache.hit")
            return RecommendationResponse(**cached, cache_hit=True)

        metrics.inc("cache.miss")
        catalog = pipeline.load_catalog()
        run_result = recommender.recommend(catalog, cleaned_request)
        response_data = RecommendationResponse(
            total_candidates=len(catalog),
            returned_count=len(run_result.recommendations),
            fallback_used=run_result.fallback_used,
            fallback_reason=run_result.fallback_reason,
            relaxation_steps=run_result.relaxation_steps,
            experiment_variant=run_result.experiment_variant,
            prompt_version=PROMPT_VERSION,
            recommendations=run_result.recommendations,
            cache_hit=False,
        )
        cache.set(cache_key, response_data.model_dump(exclude={"cache_hit"}))
        return response_data
    except ValueError as exc:
        metrics.inc("errors.validation")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        metrics.inc("errors.recommend")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/feedback", response_model=FeedbackResponse)
def capture_feedback(payload: FeedbackRequest, x_api_key: str | None = Header(default=None)):
    _check_auth(x_api_key)
    try:
        delta = personalization_service.capture_feedback(payload)
    except Exception as exc:
        metrics.inc("errors.feedback")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return FeedbackResponse(message="Feedback recorded.", personalization_delta=round(delta, 4))


@app.get("/profile/{session_id}", response_model=UserProfileResponse)
def get_profile(session_id: str, user_id: str | None = None, x_api_key: str | None = Header(default=None)):
    _check_auth(x_api_key)
    try:
        summary = personalization_service.profile_summary(user_id, session_id)
    except Exception as exc:
        metrics.inc("errors.profile")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return UserProfileResponse(**summary)
