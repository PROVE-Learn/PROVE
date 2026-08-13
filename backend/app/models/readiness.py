from pydantic import BaseModel, Field

from app.models.learning import SkillGap


class TargetCompanyReadiness(BaseModel):
    company_id: str
    name: str
    role_evidence_count: int = Field(ge=0)


class ReadinessAction(BaseModel):
    action: str
    detail: str


class ReadinessProvenance(BaseModel):
    component: str
    source: str
    record_count: int = Field(ge=0)


class CareerReadiness(BaseModel):
    target_role_id: str | None = None
    target_role_name: str | None = None
    readiness_score: int = Field(ge=0, le=100)
    skill_gaps: list[SkillGap] = Field(default_factory=list)
    completed_activity_count: int = Field(default=0, ge=0)
    target_companies: list[TargetCompanyReadiness] = Field(default_factory=list)
    next_actions: list[ReadinessAction] = Field(default_factory=list)
    provenance: list[ReadinessProvenance] = Field(default_factory=list)


class LearningEvidenceReview(BaseModel):
    skill_id: str
    skill_name: str
    current_level: int = Field(ge=0, le=5)
    required_level: int = Field(ge=0, le=5)
    evidence_status: str
    evidence_count: int = Field(ge=0)


class CompanyEvidenceReview(BaseModel):
    company_id: str
    company_name: str
    trusted_evidence_count: int = Field(ge=0)
    unverified_evidence_count: int = Field(ge=0)
    conflicting_evidence_count: int = Field(ge=0)


class ReadinessReview(BaseModel):
    review_status: str
    target_role_id: str | None = None
    demonstrated_learning: list[LearningEvidenceReview] = Field(default_factory=list)
    missing_learning: list[LearningEvidenceReview] = Field(default_factory=list)
    company_evidence: list[CompanyEvidenceReview] = Field(default_factory=list)
    completed_activity_count: int = Field(default=0, ge=0)
    provenance: list[ReadinessProvenance] = Field(default_factory=list)
