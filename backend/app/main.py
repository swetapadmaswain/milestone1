from datetime import datetime, timezone
from time import perf_counter
from typing import Dict, List

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import ensure_directories, settings
from app.models.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    IngestionResponse,
    MetricsResponse,
    RecommendationRequest,
    RecommendationResponse,
    UserProfileResponse,
)
from app.services.cache_service import CacheService
from app.services.data_pipeline import DataPipeline
from app.services.experimentation_service import ExperimentationService
from app.services.llm_service import LLMService
from app.services.metrics_service import MetricsService
from app.services.personalization_service import PersonalizationService
from app.services.rate_limiter import RateLimiter
from app.services.recommendation_engine import RecommendationEngine
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered restaurant recommendation system with LLM integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Ensure directories exist
ensure_directories()

# Initialize services
metrics_service = MetricsService()
cache_service = CacheService()
data_pipeline = DataPipeline(metrics_service)
personalization_service = PersonalizationService(metrics_service)
experimentation_service = ExperimentationService()
llm_service = LLMService(metrics_service)
recommendation_engine = RecommendationEngine(
    personalization_service=personalization_service,
    experimentation_service=experimentation_service,
    llm_service=llm_service,
    metrics_service=metrics_service,
)
rate_limiter = RateLimiter()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
app.add_middleware(AuthMiddleware)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Middleware to track request timing."""
    start_time = perf_counter()
    response = await call_next(request)
    elapsed_ms = (perf_counter() - start_time) * 1000
    
    # Record timing metrics
    endpoint = f"http.{request.url.path}"
    metrics_service.observe_latency(endpoint, elapsed_ms)
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    metrics_service.increment_counter(f"errors.http.{exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    metrics_service.increment_counter("errors.unexpected")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Health and Monitoring Endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    uptime = perf_counter()  # This would be calculated from app start time
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=uptime,
        database_status="connected",  # Would check actual DB connection
        llm_status="available" if settings.GROQ_API_KEY else "unavailable",
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """Get system metrics."""
    return metrics_service.get_metrics()


# Data Management Endpoints
@app.post("/ingest", response_model=IngestionResponse, tags=["Data"])
async def ingest_data():
    """Ingest and prepare restaurant data."""
    try:
        start_time = perf_counter()
        result = await data_pipeline.ingest_and_prepare()
        processing_time = perf_counter() - start_time
        
        metrics_service.increment_counter("data.ingestion.success")
        
        return IngestionResponse(
            message="Data ingestion completed successfully",
            raw_records=result.raw_records,
            prepared_records=result.prepared_records,
            processing_time_seconds=processing_time,
        )
    except Exception as exc:
        metrics_service.increment_counter("data.ingestion.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data ingestion failed: {str(exc)}",
        ) from exc


# Recommendation Endpoints
@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(
    request: RecommendationRequest,
    http_request: Request,
):
    """Get personalized restaurant recommendations."""
    try:
        # Apply rate limiting
        client_key = getattr(http_request.state, "client_key", "unknown")
        if not rate_limiter.allow(client_key):
            metrics_service.increment_counter("rate_limited")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        
        # Check cache first
        cache_key = cache_service.make_key(request.model_dump())
        cached_result = cache_service.get(cache_key)
        if cached_result:
            metrics_service.increment_counter("cache.hit")
            return RecommendationResponse(**cached_result, cache_hit=True)
        
        metrics_service.increment_counter("cache.miss")
        
        # Get recommendations
        catalog = await data_pipeline.load_catalog()
        result = await recommendation_engine.recommend(catalog, request)
        
        response = RecommendationResponse(
            total_candidates=result.total_candidates,
            returned_count=result.returned_count,
            fallback_used=result.fallback_used,
            fallback_reason=result.fallback_reason,
            relaxation_steps=result.relaxation_steps,
            experiment_variant=result.experiment_variant,
            prompt_version=result.prompt_version,
            cache_hit=False,
            recommendations=result.recommendations,
        )
        
        # Cache the result
        cache_service.set(cache_key, response.model_dump(exclude={"cache_hit"}))
        
        metrics_service.increment_counter("recommendations.success")
        return response
        
    except ValueError as exc:
        metrics_service.increment_counter("recommendations.validation_error")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        metrics_service.increment_counter("recommendations.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(exc)}",
        ) from exc


# Feedback and Personalization Endpoints
@app.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def capture_feedback(request: FeedbackRequest):
    """Capture user feedback for personalization."""
    try:
        delta = await personalization_service.capture_feedback(request)
        
        metrics_service.increment_counter("feedback.captured")
        
        return FeedbackResponse(
            message="Feedback recorded successfully",
            personalization_delta=round(delta, 4),
        )
    except Exception as exc:
        metrics_service.increment_counter("feedback.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback capture failed: {str(exc)}",
        ) from exc


@app.get("/profile/{session_id}", response_model=UserProfileResponse, tags=["Personalization"])
async def get_user_profile(
    session_id: str,
    user_id: str | None = None,
):
    """Get user profile summary."""
    try:
        profile = await personalization_service.get_profile_summary(user_id, session_id)
        
        metrics_service.increment_counter("profile.accessed")
        
        return UserProfileResponse(**profile)
    except Exception as exc:
        metrics_service.increment_counter("profile.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile retrieval failed: {str(exc)}",
        ) from exc


# Experimentation Endpoints
@app.get("/experiments/assignments/{user_key}", tags=["Experiments"])
async def get_experiment_assignments(user_key: str):
    """Get experiment assignments for a user."""
    try:
        assignments = await experimentation_service.get_user_assignments(user_key)
        
        metrics_service.increment_counter("experiments.assignments_accessed")
        
        return {"user_key": user_key, "assignments": assignments}
    except Exception as exc:
        metrics_service.increment_counter("experiments.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment assignment failed: {str(exc)}",
        ) from exc


@app.post("/experiments/track", tags=["Experiments"])
async def track_experiment_event(
    user_key: str,
    experiment_id: str,
    variant: str,
    event_data: Dict,
):
    """Track experiment event."""
    try:
        await experimentation_service.track_event(user_key, experiment_id, variant, event_data)
        
        metrics_service.increment_counter("experiments.event_tracked")
        
        return {"message": "Event tracked successfully"}
    except Exception as exc:
        metrics_service.increment_counter("experiments.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event tracking failed: {str(exc)}",
        ) from exc


# Admin Endpoints
@app.delete("/cache", tags=["Admin"])
async def clear_cache():
    """Clear all cache entries (admin only)."""
    try:
        cache_service.clear()
        metrics_service.increment_counter("cache.cleared")
        
        return {"message": "Cache cleared successfully"}
    except Exception as exc:
        metrics_service.increment_counter("cache.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache clear failed: {str(exc)}",
        ) from exc


@app.get("/admin/stats", tags=["Admin"])
async def get_admin_stats():
    """Get administrative statistics."""
    try:
        stats = {
            "metrics": metrics_service.get_metrics(),
            "cache_stats": cache_service.get_stats(),
            "rate_limiter_stats": rate_limiter.get_stats(),
            "catalog_info": await data_pipeline.get_catalog_info(),
        }
        
        metrics_service.increment_counter("admin.stats_accessed")
        
        return stats
    except Exception as exc:
        metrics_service.increment_counter("admin.error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(exc)}",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
