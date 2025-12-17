"""Calendar event schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CalendarEventBase(BaseModel):
    """Base calendar event schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    recurrence_rule: Optional[str] = None  # RRULE format


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a calendar event."""
    study_plan_id: int
    task_id: Optional[int] = None


class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event response."""
    id: int
    study_plan_id: int
    task_id: Optional[int] = None
    ics_uid: Optional[str] = None  # Unique identifier for ICS
    synced: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

