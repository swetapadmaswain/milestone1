from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
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
    rule_score: float
    llm_score: float
    final_score: float
    explanation: str
    confidence: str


class RecommendationResponse(BaseModel):
    total_candidates: int
    returned_count: int
    fallback_used: bool
    fallback_reason: Optional[str] = None
    relaxation_steps: List[str] = Field(default_factory=list)
    prompt_version: str
    recommendations: List[RestaurantRecommendation]


class IngestionResponse(BaseModel):
    message: str
    raw_records: int
    prepared_records: int
