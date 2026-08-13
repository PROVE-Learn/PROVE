from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import MemoryCategory, MemorySource


class MemoryCreate(BaseModel):
    category: MemoryCategory
    key: str = Field(min_length=1, max_length=100)
    value: Any
    source: MemorySource = MemorySource.USER_REPORTED
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class MemoryUpdate(BaseModel):
    key: str | None = Field(default=None, min_length=1, max_length=100)
    value: Any | None = None
    source: MemorySource | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class UserMemoryInDB(MemoryCreate):
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
