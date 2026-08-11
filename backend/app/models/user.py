from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.common import UserPhase, UserRole


class UserPreferences(BaseModel):
    learning_style: str | None = None
    location: str | None = None
    salary_expectation: str | None = None
    preferred_environment: str | None = None


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
