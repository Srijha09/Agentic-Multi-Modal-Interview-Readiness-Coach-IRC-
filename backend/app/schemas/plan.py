"""Study plan, week, day, and task schemas."""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskType(str, Enum):
    """Task types."""
    LEARN = "learn"
    PRACTICE = "practice"
    REVIEW = "review"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class DayBase(BaseModel):
    """Base day schema."""
    day_number: int = Field(..., ge=1, le=365)
    date: date
    theme: Optional[str] = None
    estimated_hours: float = Field(..., ge=0.0)


class WeekBase(BaseModel):
    """Base week schema."""
    week_number: int = Field(..., ge=1, le=52)
    theme: str
    focus_skills: List[str] = []  # List of skill names
    estimated_hours: float = Field(..., ge=0.0)


class TaskBase(BaseModel):
    """Base task schema."""
    task_type: TaskType
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    skill_names: List[str] = []  # Associated skills
    estimated_minutes: int = Field(..., ge=1)
    dependencies: List[int] = []  # Task IDs this depends on
    content: Dict[str, Any] = {}  # Flexible content structure


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    day_id: Optional[int] = None
    study_plan_id: int


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: int
    status: TaskStatus
    completed_at: Optional[datetime] = None
    actual_minutes: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DayResponse(DayBase):
    """Schema for day response."""
    id: int
    tasks: List[TaskResponse] = []

    model_config = {"from_attributes": True}


class WeekResponse(WeekBase):
    """Schema for week response."""
    id: int
    days: List[DayResponse] = []

    model_config = {"from_attributes": True}


class StudyPlanBase(BaseModel):
    """Base study plan schema."""
    interview_date: Optional[datetime] = None
    weeks: int = Field(..., ge=1, le=52)
    hours_per_week: float = Field(..., ge=1.0, le=168.0)
    focus_areas: List[str] = []  # Priority skill areas


class StudyPlanCreate(StudyPlanBase):
    """Schema for creating a study plan."""
    user_id: int


class StudyPlanResponse(StudyPlanBase):
    """Schema for study plan response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    weeks_data: List[WeekResponse] = []
    total_estimated_hours: float
    completion_percentage: float = Field(..., ge=0.0, le=100.0)

    model_config = {"from_attributes": True}

