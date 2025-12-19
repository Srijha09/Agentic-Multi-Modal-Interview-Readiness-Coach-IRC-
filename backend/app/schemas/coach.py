"""
Schemas for Daily Coach Agent (Phase 6).
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from app.schemas.plan import TaskResponse


class TaskUpdateRequest(BaseModel):
    """Request to update a task status."""
    task_id: int
    status: str = Field(..., pattern="^(pending|in_progress|completed|skipped)$")
    actual_minutes: Optional[int] = Field(None, ge=0)


class DailyBriefingTask(BaseModel):
    """Task information for daily briefing."""
    id: int
    title: str
    description: str
    task_type: str
    estimated_minutes: int
    skill_names: List[str]
    status: str
    dependencies: List[int]
    is_overdue: bool = False
    days_overdue: int = 0
    content: Dict[str, Any] = {}  # Study materials, links, resources
    task_date: Optional[date] = None  # Date when task is scheduled


class DailyBriefingResponse(BaseModel):
    """Daily briefing response."""
    date: date
    study_plan_id: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    estimated_minutes: int
    actual_minutes: Optional[int] = None
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    tasks: List[DailyBriefingTask]
    motivational_message: Optional[str] = None
    focus_skills: List[str] = []
    upcoming_tasks: List[DailyBriefingTask] = []  # Tasks from next few days
    current_week: Optional[int] = None
    total_weeks: Optional[int] = None
    week_progress: Optional[float] = None  # Progress for current week


class TaskRescheduleRequest(BaseModel):
    """Request to reschedule a task."""
    new_date: date
    reason: Optional[str] = None


class TaskRescheduleResponse(BaseModel):
    """Response after rescheduling a task."""
    task_id: int
    old_date: date
    new_date: date
    status: str
    message: str


class CarryOverSummary(BaseModel):
    """Summary of tasks carried over."""
    date: date
    carried_over_tasks: List[DailyBriefingTask]
    total_carried_over: int
    rescheduled_tasks: List[TaskRescheduleResponse] = []

