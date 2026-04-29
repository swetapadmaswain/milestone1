from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Persistent user id")
    session_id: str = Field(..., description="Current browsing session id")
    location: str = Field(..., description="City/locality name")
    budget: str = Field(..., description="low | medium | high")
    preferred_cuisine: str = Field(..., description="Preferred cuisine")
    min_rating: float = Field(0.0, ge=0.0, le=5.0)
    additional_preferences: Optional[List[str]] = Field(default_factory=list)
    top_n: int = Field(5, ge=1, le=20)


class RestaurantRecommendation(BaseModel):
    restaurant_name: str
    location: str
    cuisine: str
    estimated_cost: float
    rating: float
    final_score: float
    score_breakdown: Dict[str, float]
    reason: str
    explanation: str
    confidence: str


class RecommendationResponse(BaseModel):
    total_candidates: int
    returned_count: int
    fallback_used: bool
    fallback_reason: Optional[str] = None
    relaxation_steps: List[str] = Field(default_factory=list)
    experiment_variant: str
    prompt_version: str
    cache_hit: bool
    recommendations: List[RestaurantRecommendation]


class IngestionResponse(BaseModel):
    message: str
    raw_records: int
    prepared_records: int


class FeedbackRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: str
    restaurant_name: str
    location: str
    cuisine: str
    signal_type: Literal["explicit", "implicit"]
    signal_name: Literal["like", "dislike", "click", "dwell", "conversion", "skip"]
    value: float = Field(..., ge=0.0, le=1.0)


class FeedbackResponse(BaseModel):
    message: str
    personalization_delta: float


class UserProfileResponse(BaseModel):
    user_key: str
    total_events: int
    top_cuisines: Dict[str, float]
    favored_budget_bands: Dict[str, float]
