"""Domain model definitions for future milestones."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import ConfidenceLevel, MasteryLevel


class QuestionVerification(BaseModel):
    verified: bool = False
    method: str | None = None
    computed_answer: str | None = None
    declared_answer: str | None = None
    verified_at: datetime | None = None
    verifier_version: str = "1.0"


class QuestionInDB(BaseModel):
    id: str = Field(alias="_id")
    type: str
    skill_ids: list[str] = Field(default_factory=list)
    difficulty: int = 1
    content: dict = Field(default_factory=dict)
    expected_answer: str | None = None
    verification: QuestionVerification = Field(default_factory=QuestionVerification)
    source: str = "generated"
    usage_count: int = 0
    created_at: datetime

    model_config = {"populate_by_name": True}


class AssessmentInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: str
    skill_ids: list[str] = Field(default_factory=list)
    questions: list[dict] = Field(default_factory=list)
    overall_score: float | None = None
    weaknesses_identified: list[str] = Field(default_factory=list)
    timed: bool = False
    duration_seconds: int | None = None
    status: str = "in_progress"
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"populate_by_name": True}


class LearningSessionInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    skill_id: str
    phase: str = "explain"
    topic: str = ""
    messages_summary: str = ""
    misconceptions_detected: list[str] = Field(default_factory=list)
    hints_given: int = 0
    practice_items: list[dict] = Field(default_factory=list)
    status: str = "active"
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ProjectInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    title: str
    problem_statement: str = ""
    requirements: list[str] = Field(default_factory=list)
    user_stories: list[str] = Field(default_factory=list)
    architecture_decisions: list[dict] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    status: str = "planning"
    student_notes: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class ProjectReviewInDB(BaseModel):
    id: str = Field(alias="_id")
    project_id: str
    user_id: str
    review_type: str
    feedback: str = ""
    score: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    created_at: datetime

    model_config = {"populate_by_name": True}


class InterviewInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: str
    target_role_id: str | None = None
    questions: list[dict] = Field(default_factory=list)
    overall_score: float | None = None
    overall_confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    weaknesses_identified: list[str] = Field(default_factory=list)
    rubric_version: str = "1.0"
    evaluated_at: datetime | None = None
    created_at: datetime

    model_config = {"populate_by_name": True}


class ReadinessDimension(BaseModel):
    score: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    recommended_action: str = ""


class ReadinessProfileInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    target_role_id: str | None = None
    overall_readiness: float = 0.0
    overall_confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    dimensions: dict[str, ReadinessDimension] = Field(default_factory=dict)
    formula_version: str = "1.0"
    disclaimer: str = (
        "Current evidence indicates your readiness for this target role. "
        "This does not guarantee employment."
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class EvaluationEvidenceInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    evidence_type: str
    reference_collection: str
    reference_id: str
    score: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    metadata: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"populate_by_name": True}
