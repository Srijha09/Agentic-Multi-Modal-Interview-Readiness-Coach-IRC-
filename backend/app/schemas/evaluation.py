"""Evaluation and rubric schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class RubricCriterion(BaseModel):
    """Rubric criterion schema."""
    name: str
    description: str
    weight: float = Field(..., ge=0.0, le=1.0)
    max_score: float = Field(..., ge=0.0)


class RubricResponse(BaseModel):
    """Schema for rubric response."""
    id: int
    practice_type: str
    criteria: List[RubricCriterion]
    total_max_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationBase(BaseModel):
    """Base evaluation schema."""
    practice_attempt_id: int
    rubric_id: Optional[int] = None
    overall_score: float = Field(..., ge=0.0, le=1.0)
    criterion_scores: Dict[str, float] = {}  # criterion_name -> score
    strengths: List[str] = []
    weaknesses: List[str] = []
    feedback: str
    evaluator_notes: Optional[str] = None


class EvaluationCreate(EvaluationBase):
    """Schema for creating an evaluation."""
    pass


class EvaluationResponse(EvaluationBase):
    """Schema for evaluation response."""
    id: int
    created_at: datetime
    rubric: Optional[RubricResponse] = None

    model_config = {"from_attributes": True}

