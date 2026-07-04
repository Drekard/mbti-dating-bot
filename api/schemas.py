from pydantic import BaseModel
from typing import Optional, List


class ProfileCreate(BaseModel):
    name: Optional[str] = ""
    gender: Optional[str] = ""
    age: Optional[int] = None
    mbti_type: Optional[str] = ""
    visibility_mode: Optional[str] = "public"
    communication_form: Optional[str] = ""
    description: Optional[str] = ""
    looking_for: Optional[str] = ""


class ProfileUpdate(BaseModel):
    field: str
    value: str


class ProfileResponse(BaseModel):
    user_id: int
    name: str
    gender: str
    age: Optional[int]
    mbti_type: str
    visibility_mode: str
    communication_form: str
    description: str
    looking_for: str
    is_visible: bool
    is_approved: bool
    photo_count: int


class BrowseProfileResponse(BaseModel):
    user_id: int
    name: str
    gender: str
    age: Optional[int]
    mbti_type: str
    communication_form: str
    description: str
    looking_for: str
    photo_urls: List[str]


class LikeRequest(BaseModel):
    target_user_id: int
    like_type: str  # "like" or "dislike"


class StatsResponse(BaseModel):
    likes_received: int
    matches: int
    avg_rating: Optional[float]
    total_reviews: int


class AdminProfileResponse(BaseModel):
    user_id: int
    username: Optional[str]
    name: str
    gender: str
    age: Optional[int]
    mbti_type: str
    communication_form: str
    description: str
    looking_for: str
    visibility_mode: str
    is_visible: bool
    is_approved: bool
    is_rejected: bool
    photo_count: int
