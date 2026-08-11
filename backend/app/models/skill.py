from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import MasteryLevel


class SkillInDB(BaseModel):
    id: str = Field(alias="_id")
    skill_id: str
    name: str
    category: str
    parent_skill_id: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    description: str = ""
    verification_sources: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"populate_by_name": True}


class SkillCreate(BaseModel):
    skill_id: str
    name: str
    category: str
    parent_skill_id: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    description: str = ""
    verification_sources: list[str] = Field(default_factory=list)


class SkillSignal(BaseModel):
    score: float = 0.0
    last_updated: datetime | None = None
    evidence_count: int = 0


class SkillSignals(BaseModel):
    knowledge: SkillSignal = Field(default_factory=SkillSignal)
    performance: SkillSignal = Field(default_factory=SkillSignal)
    consistency: SkillSignal = Field(default_factory=SkillSignal)
    independence: SkillSignal = Field(default_factory=SkillSignal)
    confidence: SkillSignal = Field(default_factory=SkillSignal)


class EvidenceRecord(BaseModel):
    signal_type: str
    assessment_id: str | None = None
    score: float
    confidence: str
    hints_used: int = 0
    timestamp: datetime


class UserSkillProgressInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    skill_id: str
    mastery_level: MasteryLevel = MasteryLevel.UNKNOWN
    signals: SkillSignals = Field(default_factory=SkillSignals)
    weaknesses: list[str] = Field(default_factory=list)
    evidence_records: list[EvidenceRecord] = Field(default_factory=list)
    next_retest_at: datetime | None = None
    updated_at: datetime

    model_config = {"populate_by_name": True}
