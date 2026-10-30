"""
FretIQ App - User Models
Pydantic models for user-related data.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field


# Request models
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class FavoriteCreate(BaseModel):
    song_name: str = Field(..., min_length=1, max_length=200)
    artist: Optional[str] = Field(None, max_length=200)
    result_data: Any  # JSON-serializable song result


class FeedbackCreate(BaseModel):
    result_id: str
    song_name: str = Field(..., min_length=1, max_length=200)
    artist: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    corrections: Optional[Any] = None


# Response models
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class SearchHistoryItem(BaseModel):
    id: int
    song_name: str
    artist: Optional[str]
    instruments: List[str]
    result_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteResponse(BaseModel):
    id: int
    song_name: str
    artist: Optional[str]
    result_data: Any
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    id: int
    result_id: str
    song_name: str
    artist: Optional[str]
    rating: int
    comment: Optional[str]
    corrections: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    user: UserResponse
    stats: dict  # search_count, favorites_count, feedback_count