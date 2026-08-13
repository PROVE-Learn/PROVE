from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.common import ExperienceLevel, SelfReportedSkillLevel, UserPhase, UserRole


class UserPreferences(BaseModel):
    learning_style: str | None = None
    available_study_time: str | None = Field(default=None, max_length=100)
    preferred_difficulty: str | None = Field(default=None, max_length=50)
    learning_goals: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("learning_goals")
    @classmethod
    def reject_blank_learning_goals(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("List values must not be blank")
        return values


class ProfileSkill(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    level: SelfReportedSkillLevel
    evidence: str | None = Field(default=None, max_length=500)
    recorded_at: date = Field(default_factory=date.today)


class UserProfile(BaseModel):
    education: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=200)
    specialization: str | None = Field(default=None, max_length=200)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    experience_level: ExperienceLevel | None = None
    interests: list[str] = Field(default_factory=list, max_length=30)
    career_goals: list[str] = Field(default_factory=list, max_length=20)
    preferred_domains: list[str] = Field(default_factory=list, max_length=20)
    target_role: str | None = Field(default=None, max_length=150)
    target_companies: list[str] = Field(default_factory=list, max_length=30)
    known_skills: list[ProfileSkill] = Field(default_factory=list, max_length=100)
    completed_learning_item_ids: list[str] = Field(default_factory=list, max_length=500)
    assessment_history_ids: list[str] = Field(default_factory=list, max_length=500)
    project_ids: list[str] = Field(default_factory=list, max_length=500)
    interview_ids: list[str] = Field(default_factory=list, max_length=500)

    @field_validator(
        "interests",
        "career_goals",
        "preferred_domains",
        "target_companies",
        "completed_learning_item_ids",
        "assessment_history_ids",
        "project_ids",
        "interview_ids",
    )
    @classmethod
    def reject_blank_items(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("List values must not be blank")
        return values


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    education: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=200)
    specialization: str | None = Field(default=None, max_length=200)
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    experience_level: ExperienceLevel | None = None
    interests: list[str] | None = Field(default=None, max_length=30)
    career_goals: list[str] | None = Field(default=None, max_length=20)
    preferred_domains: list[str] | None = Field(default=None, max_length=20)
    target_role: str | None = Field(default=None, max_length=150)
    target_companies: list[str] | None = Field(default=None, max_length=30)
    known_skills: list[ProfileSkill] | None = Field(default=None, max_length=100)
    learning_preferences: UserPreferences | None = None
    completed_learning_item_ids: list[str] | None = Field(default=None, max_length=500)
    assessment_history_ids: list[str] | None = Field(default=None, max_length=500)
    project_ids: list[str] | None = Field(default=None, max_length=500)
    interview_ids: list[str] | None = Field(default=None, max_length=500)

    @field_validator(
        "interests",
        "career_goals",
        "preferred_domains",
        "target_companies",
        "completed_learning_item_ids",
        "assessment_history_ids",
        "project_ids",
        "interview_ids",
    )
    @classmethod
    def reject_blank_items(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("List values must not be blank")
        return values


class UserProfileResponse(UserProfile):
    id: str
    display_name: str
    email: EmailStr
    learning_preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    password_hash: str
    display_name: str
    role: UserRole = UserRole.STUDENT
    beta_slot: int | None = None
    current_phase: UserPhase = UserPhase.ONBOARDING
    phase_metadata: dict = Field(default_factory=dict)
    target_role_id: str | None = None
    target_company_id: str | None = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    profile: UserProfile = Field(default_factory=UserProfile)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    model_config = {"populate_by_name": True}


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    role: UserRole
    beta_slot: int | None
    current_phase: UserPhase
    created_at: datetime
