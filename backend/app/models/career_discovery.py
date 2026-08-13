from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import ConfidenceLevel


class QuestionOption(BaseModel):
    id: str
    text: str
    scores: dict[str, int] = Field(default_factory=dict, exclude=True)

    def __init__(self, id: str | None = None, text: str | None = None, scores: dict[str, int] | None = None, **data):
        if id is not None:
            data["id"] = id
        if text is not None:
            data["text"] = text
        if scores is not None:
            data["scores"] = scores
        super().__init__(**data)


class DiscoveryQuestion(BaseModel):
    id: str
    category: str
    text: str
    options: list[QuestionOption]
    version: str = "1.0"
    active: bool = True

    def __init__(self, id: str | None = None, category: str | None = None, text: str | None = None, options: list[QuestionOption] | None = None, **data):
        for key, value in (("id", id), ("category", category), ("text", text), ("options", options)):
            if value is not None:
                data[key] = value
        super().__init__(**data)


class PublicDiscoveryQuestion(BaseModel):
    id: str
    category: str
    text: str
    options: list[tuple[str, str]]
    version: str
    active: bool


class AssessmentAnswer(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    option_id: str = Field(min_length=1, max_length=100)


class AssessmentAnswerSubmission(BaseModel):
    answers: list[AssessmentAnswer] = Field(min_length=1, max_length=20)


class CareerRole(BaseModel):
    role_id: str
    name: str
    description: str
    core_skills: list[str]
    supporting_skills: list[str]
    relevant_interests: list[str]
    relevant_work_preferences: list[str]
    prerequisites: list[str]
    skill_requirements: dict[str, int] = Field(default_factory=dict)
    optional_skills: list[str] = Field(default_factory=list)
    expected_proficiency: dict[str, int] = Field(default_factory=dict)

    def __init__(
        self,
        role_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        core_skills: list[str] | None = None,
        supporting_skills: list[str] | None = None,
        relevant_interests: list[str] | None = None,
        relevant_work_preferences: list[str] | None = None,
        prerequisites: list[str] | None = None,
        **data,
    ):
        values = {
            "role_id": role_id,
            "name": name,
            "description": description,
            "core_skills": core_skills,
            "supporting_skills": supporting_skills,
            "relevant_interests": relevant_interests,
            "relevant_work_preferences": relevant_work_preferences,
            "prerequisites": prerequisites,
        }
        data.update({key: value for key, value in values.items() if value is not None})
        super().__init__(**data)


class AssessmentResult(BaseModel):
    assessment_id: str
    status: str
    dimension_scores: dict[str, float]
    completed_at: datetime | None


class CareerRecommendation(BaseModel):
    role: CareerRole
    score: float = Field(ge=0, le=100)
    supporting_evidence: list[str]
    missing_evidence: list[str]
    confidence: ConfidenceLevel
    recommended_next_experiment: str
    explanation: str


class TargetRoleSelectionRequest(BaseModel):
    role_id: str = Field(min_length=1, max_length=100)
    assessment_id: str = Field(min_length=1, max_length=100)


class TargetRoleSelection(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    role: CareerRole
    assessment_id: str
    recommendation_evidence: list[str]
    selected_at: datetime

    model_config = {"populate_by_name": True}
