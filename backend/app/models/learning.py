from datetime import UTC, datetime
from enum import StrEnum
from pydantic import BaseModel, Field
from app.models.common import MasteryState

class ActivityType(StrEnum):
    LESSON = "lesson"; DOCUMENTATION = "documentation"; EXERCISE = "exercise"; CODING_TASK = "coding_task"; PROJECT = "project"; QUIZ = "quiz"; ASSESSMENT = "assessment"
class ActivityState(StrEnum):
    NOT_STARTED = "NOT_STARTED"; STARTED = "STARTED"; COMPLETED = "COMPLETED"

class SkillGap(BaseModel):
    skill_id: str; skill_name: str; current_level: int = Field(ge=0, le=5); required_level: int = Field(ge=0, le=5); gap_size: int = Field(ge=0); priority: int = Field(ge=0); prerequisites: list[str] = Field(default_factory=list); reason: str

class LearningStage(BaseModel):
    skill_id: str; title: str; prerequisites: list[str] = Field(default_factory=list); estimated_effort_hours: int = Field(ge=1); status: ActivityState = ActivityState.NOT_STARTED

class LearningPlan(BaseModel):
    id: str | None = Field(default=None, alias="_id"); user_id: str; target_role: str; gaps: list[SkillGap]; stages: list[LearningStage]; estimated_effort_hours: int; status: str = "ACTIVE"; created_at: datetime = Field(default_factory=lambda: datetime.now(UTC)); updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = {"populate_by_name": True}

class LearningActivity(BaseModel):
    id: str | None = Field(default=None, alias="_id"); activity_id: str; title: str; description: str; skill_id: str; activity_type: ActivityType; difficulty: int = Field(ge=1, le=5); estimated_effort_hours: int = Field(ge=1); prerequisites: list[str] = Field(default_factory=list); source: str | None = None; state: ActivityState = ActivityState.NOT_STARTED; evidence_required: bool = False
    model_config = {"populate_by_name": True}

class ProgressItem(BaseModel):
    skill_id: str; current_level: int; target_level: int; progress: float; status: MasteryState; evidence: list[str] = Field(default_factory=list)

class MentorSummary(BaseModel):
    user_id: str
    target_role: str
    weekly_focus: str
    top_gaps: list[str] = Field(default_factory=list)
    recommended_projects: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = {"populate_by_name": True}

class WeeklyMilestone(BaseModel):
    day: str
    objective: str
    task: str
    outcome: str

class WeeklyMentorPlan(BaseModel):
    user_id: str
    target_role: str
    weekly_focus: str
    milestones: list[WeeklyMilestone] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = {"populate_by_name": True}

class AdaptiveRoadmap(BaseModel):
    user_id: str
    target_role: str
    focus: str
    adjustments: list[str] = Field(default_factory=list)
    next_milestone: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_config = {"populate_by_name": True}
