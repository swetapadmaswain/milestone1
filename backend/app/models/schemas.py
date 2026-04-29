from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# Recommendation Request/Response Models
class RecommendationRequest(BaseModel):
    """Request model for restaurant recommendations."""
    user_id: Optional[str] = Field(None, description="Persistent user id")
    session_id: str = Field(..., description="Current browsing session id")
    location: str = Field(..., description="City/locality name")
    budget: Literal["low", "medium", "high"] = Field(..., description="Budget category")
    preferred_cuisine: str = Field(default="", description="Preferred cuisine")
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Minimum rating")
    additional_preferences: List[str] = Field(default_factory=list, description="Additional preferences")
    top_n: int = Field(default=5, ge=1, le=20, description="Number of recommendations")


class RestaurantRecommendation(BaseModel):
    """Individual restaurant recommendation."""
    restaurant_name: str
    location: str
    cuisine: str
    estimated_cost: float
    rating: float
    final_score: float
    score_breakdown: Dict[str, float]
    reason: str
    explanation: str
    confidence: Literal["low", "medium", "high"]


class RecommendationResponse(BaseModel):
    """Response model for restaurant recommendations."""
    total_candidates: int
    returned_count: int
    fallback_used: bool
    fallback_reason: Optional[str] = None
    relaxation_steps: List[str] = Field(default_factory=list)
    experiment_variant: str
    prompt_version: str
    cache_hit: bool
    recommendations: List[RestaurantRecommendation]


# Feedback Models
class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    user_id: Optional[str] = None
    session_id: str
    restaurant_name: str
    location: str
    cuisine: str
    signal_type: Literal["explicit", "implicit"]
    signal_name: Literal["like", "dislike", "click", "dwell", "conversion", "skip"]
    value: float = Field(..., ge=0.0, le=1.0)


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    message: str
    personalization_delta: float


# User Profile Models
class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_key: str
    total_events: int
    top_cuisines: Dict[str, float]
    favored_budget_bands: Dict[str, float]
    last_activity: Optional[datetime] = None


# Data Ingestion Models
class IngestionResponse(BaseModel):
    """Response model for data ingestion."""
    message: str
    raw_records: int
    prepared_records: int
    processing_time_seconds: float


# Health and Metrics Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    database_status: str
    llm_status: str


class MetricValue(BaseModel):
    """Individual metric value."""
    name: str
    value: float
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Response model for system metrics."""
    counters: Dict[str, int]
    gauges: Dict[str, float]
    timers: Dict[str, List[float]]
    timestamp: datetime


# Authentication Models
class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    field: str
    message: str
    value: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    message: str = "Request validation failed"
    details: List[ValidationErrorDetail]
    timestamp: datetime


# Experiment Models
class ExperimentVariant(BaseModel):
    """Experiment variant configuration."""
    name: str
    weight: float = Field(ge=0.0, le=1.0)
    config: Dict[str, any]


class ExperimentConfig(BaseModel):
    """Experiment configuration."""
    experiment_id: str
    name: str
    variants: List[ExperimentVariant]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExperimentAssignment(BaseModel):
    """Experiment assignment for a user."""
    user_key: str
    experiment_id: str
    variant: str
    assigned_at: datetime
