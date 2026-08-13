from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import ConfidenceLevel, InferenceType, ReviewStatus


class DimensionResult(BaseModel):
    score: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    responses: list[dict] = Field(default_factory=list)


class CareerAssessmentInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    status: str = "in_progress"
    dimensions: dict[str, DimensionResult] = Field(default_factory=dict)
    raw_responses: list[dict] = Field(default_factory=list)
    completed_at: datetime | None = None
    question_version: str = "1.0"
    created_at: datetime

    model_config = {"populate_by_name": True}


class CareerRecommendationItem(BaseModel):
    career_id: str
    career_title: str
    compatibility_score: float
    compatibility_breakdown: dict[str, float] = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    recommended_experiment: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    reasoning: str = ""


class CareerRecommendationInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    assessment_id: str
    recommendations: list[CareerRecommendationItem] = Field(default_factory=list)
    selected_career_index: int | None = None
    scoring_engine_version: str = "1.0"
    assessment_completeness: float = 0.0
    created_at: datetime

    model_config = {"populate_by_name": True}


class SourceClaim(BaseModel):
    claim: str
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    conflicts_with: list[str] = Field(default_factory=list)


class ResearchSource(BaseModel):
    source_id: str
    url: str
    source_type: str
    fetched_at: datetime | None = None
    content_hash: str | None = None
    freshness: str = "fresh"
    claims: list[SourceClaim] = Field(default_factory=list)


class RoleRequirement(BaseModel):
    requirement: str
    category: str
    inference_type: InferenceType = InferenceType.UNVERIFIED
    source_id: str | None = None
    source_quote: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED


class TargetRoleInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    title: str
    level: str = "intern"
    technical_skills: list[RoleRequirement] = Field(default_factory=list)
    programming_languages: list[RoleRequirement] = Field(default_factory=list)
    frameworks: list[RoleRequirement] = Field(default_factory=list)
    dsa_topics: list[RoleRequirement] = Field(default_factory=list)
    cs_fundamentals: list[RoleRequirement] = Field(default_factory=list)
    aptitude_requirements: list[RoleRequirement] = Field(default_factory=list)
    soft_skills: list[RoleRequirement] = Field(default_factory=list)
    project_expectations: list[RoleRequirement] = Field(default_factory=list)
    interview_competencies: list[RoleRequirement] = Field(default_factory=list)
    experience_requirements: list[RoleRequirement] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    conflicts: list[dict] = Field(default_factory=list)
    research_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class CompanyProfileInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    company_name: str
    role_title: str
    requirements: list[RoleRequirement] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    conflicts: list[dict] = Field(default_factory=list)
    research_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
