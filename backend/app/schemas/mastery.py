"""Mastery tracking schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MasteryBase(BaseModel):
    """Base mastery schema."""
    skill_name: str = Field(..., min_length=1, max_length=200)
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    last_practiced: Optional[datetime] = None


class MasteryUpdate(BaseModel):
    """Schema for updating mastery."""
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    last_practiced: Optional[datetime] = None


class MasteryResponse(MasteryBase):
    """Schema for mastery response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    practice_count: int = 0
    improvement_trend: Optional[str] = None  # "improving", "stable", "declining"

    model_config = {"from_attributes": True}

