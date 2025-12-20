"""Practice item and attempt schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PracticeType(str, Enum):
    """Practice types."""
    QUIZ = "quiz"
    FLASHCARD = "flashcard"
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"


class DifficultyLevel(str, Enum):
    """Difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PracticeItemBase(BaseModel):
    """Base practice item schema."""
    practice_type: PracticeType
    title: str = Field(..., min_length=1, max_length=200)
    question: str = Field(..., min_length=10)
    skill_names: List[str] = []
    difficulty: DifficultyLevel
    content: Dict[str, Any] = {}  # Flexible content (options, hints, etc.)
    expected_answer: Optional[str] = None
    rubric: Optional[Dict[str, Any]] = None


class PracticeItemCreate(PracticeItemBase):
    """Schema for creating a practice item."""
    task_id: Optional[int] = None


class PracticeItemResponse(PracticeItemBase):
    """Schema for practice item response."""
    id: int
    task_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PracticeAttemptBase(BaseModel):
    """Base practice attempt schema."""
    practice_item_id: int
    answer: str = Field(..., min_length=1)
    time_spent_seconds: Optional[int] = None


class PracticeAttemptCreate(PracticeAttemptBase):
    """Schema for creating a practice attempt."""
    user_id: int
    task_id: Optional[int] = None


class PracticeAttemptResponse(PracticeAttemptBase):
    """Schema for practice attempt response."""
    id: int
    user_id: int
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    feedback: Optional[str] = None
    evaluation_id: Optional[int] = None
    created_at: datetime
    practice_item: Optional[PracticeItemResponse] = None
    evaluation: Optional["EvaluationResponse"] = None  # Phase 8

    model_config = {"from_attributes": True}


# Update forward references after all classes are defined
# This is needed for Pydantic to resolve the forward reference
try:
    from app.schemas.evaluation import EvaluationResponse
    PracticeAttemptResponse.model_rebuild()
except ImportError:
    # If evaluation schema not available yet, that's okay
    pass

