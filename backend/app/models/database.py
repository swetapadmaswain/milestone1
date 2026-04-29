from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class RestaurantDB(Base):
    """Database model for restaurant data."""
    
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    cuisine = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    rating = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UserProfileDB(Base):
    """Database model for user profiles."""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    profile_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeedbackDB(Base):
    """Database model for user feedback."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    restaurant_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    cuisine = Column(String(255), nullable=False)
    signal_type = Column(String(50), nullable=False)  # explicit/implicit
    signal_name = Column(String(50), nullable=False)  # like/dislike/click/etc
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Pydantic Models for API
class RestaurantBase(BaseModel):
    """Base restaurant model."""
    restaurant_name: str
    location: str
    cuisine: str
    estimated_cost: float
    rating: float


class RestaurantCreate(RestaurantBase):
    """Restaurant creation model."""
    pass


class RestaurantResponse(RestaurantBase):
    """Restaurant response model."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Base user profile model."""
    user_id: Optional[str] = None
    session_id: str
    profile_data: dict


class UserProfileCreate(UserProfileBase):
    """User profile creation model."""
    pass


class UserProfileResponse(UserProfileBase):
    """User profile response model."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackBase(BaseModel):
    """Base feedback model."""
    user_id: Optional[str] = None
    session_id: str
    restaurant_name: str
    location: str
    cuisine: str
    signal_type: str  # explicit/implicit
    signal_name: str  # like/dislike/click/etc
    value: float = Field(ge=0.0, le=1.0)


class FeedbackCreate(FeedbackBase):
    """Feedback creation model."""
    pass


class FeedbackResponse(FeedbackBase):
    """Feedback response model."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
