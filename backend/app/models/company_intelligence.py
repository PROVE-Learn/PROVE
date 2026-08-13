from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, model_validator


class SourceType(StrEnum):
    OFFICIAL_COMPANY = "OFFICIAL_COMPANY"
    OFFICIAL_JOB_POSTING = "OFFICIAL_JOB_POSTING"
    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"
    REPUTABLE_SOURCE = "REPUTABLE_SOURCE"
    COMMUNITY_REPORT = "COMMUNITY_REPORT"
    USER_PROVIDED = "USER_PROVIDED"
    OTHER = "OTHER"


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTING = "CONFLICTING"


class Company(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    company_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    aliases: list[str] = Field(default_factory=list)
    official_website: HttpUrl | None = None
    careers_url: HttpUrl | None = None
    industry: str | None = Field(default=None, max_length=100)
    locations: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=1000)
    active: bool = True

    model_config = {"populate_by_name": True}


class JobPosting(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    company_id: str
    role_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    location: str | None = None
    employment_type: str | None = None
    url: HttpUrl
    description: str | None = None
    qualifications: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_type: SourceType
    active: bool = True

    model_config = {"populate_by_name": True}

    def is_stale(self, ttl_days: int) -> bool:
        return self.collected_at + timedelta(days=ttl_days) < datetime.now(UTC)


class EvidenceClaim(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    company_id: str
    role_id: str | None = None
    claim_key: str = Field(min_length=1, max_length=100)
    claim_text: str = Field(min_length=1, max_length=2000)
    source_url: HttpUrl
    source_type: SourceType
    source_title: str | None = Field(default=None, max_length=300)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = Field(default=0.0, ge=0, le=1)
    evidence_text: str = Field(min_length=1, max_length=4000)
    last_verified_at: datetime | None = None
    next_review_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def verified_requires_explicit_verification(self):
        if self.verification_status == VerificationStatus.VERIFIED and self.last_verified_at is None:
            raise ValueError("Verified claims require last_verified_at")
        return self
