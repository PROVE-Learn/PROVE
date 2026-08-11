from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import ConfidenceLevel, ReviewStatus


class VerificationRecordCreate(BaseModel):
    entity_type: str
    entity_id: str | None = None
    verification_type: str
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    computed_result: str | None = None
    declared_result: str | None = None
    passed: bool
    failure_reason: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    verifier_version: str = "1.0"


class VerificationRecordInDB(BaseModel):
    id: str = Field(alias="_id")
    entity_type: str
    entity_id: str | None = None
    verification_type: str
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    computed_result: str | None = None
    declared_result: str | None = None
    passed: bool
    failure_reason: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    verifier_version: str = "1.0"
    created_at: datetime

    model_config = {"populate_by_name": True}


class HumanReviewItemCreate(BaseModel):
    item_type: str
    reference_collection: str
    reference_id: str | None = None
    content_snapshot: dict[str, Any] = Field(default_factory=dict)
    reason: str


class HumanReviewItemInDB(BaseModel):
    id: str = Field(alias="_id")
    item_type: str
    reference_collection: str
    reference_id: str | None = None
    content_snapshot: dict[str, Any] = Field(default_factory=dict)
    reason: str
    status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"populate_by_name": True}
