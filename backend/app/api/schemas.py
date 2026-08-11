from pydantic import BaseModel

from app.config import Settings
from app.models.common import ReviewStatus
from app.models.user import UserPublic
from app.verification.policy import get_verification_policy


class HealthResponse(BaseModel):
    status: str
    app_name: str
    database: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class ReviewActionRequest(BaseModel):
    status: ReviewStatus
    reviewed_by: str | None = None
