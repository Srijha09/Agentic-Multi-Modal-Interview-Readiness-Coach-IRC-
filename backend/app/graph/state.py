"""
Shared state schema for LangGraph agent workflows.
"""
from typing import Any, Dict, List, Optional, TypedDict
from datetime import date, datetime


class CoachState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    # Identity & context
    user_id: int
    db_session: Any  # SQLAlchemy Session (set in runner, not serialized)

    # Document intake
    resume_document_id: Optional[int]
    jd_document_id: Optional[int]

    # Plan generation
    study_plan_id: Optional[int]
    weeks: int
    hours_per_week: float
    interview_date: Optional[datetime]

    # Daily coach
    target_date: Optional[date]

    # Practice
    task_id: Optional[int]
    practice_type: Optional[str]
    practice_count: int
    practice_item_id: Optional[int]
    attempt_id: Optional[int]
    attempt_answer: Optional[str]
    attempt_time_spent_seconds: Optional[int]
    attempt_task_id: Optional[int]

    # Adaptive
    apply_adaptations: bool

    # Workflow control
    run_plan_after_gap: bool
    run_adapt_after_eval: bool
    error: Optional[str]

    # Results (populated by nodes)
    gaps: List[Any]
    study_plan: Any
    practice_items: List[Any]
    attempt: Any
    evaluation: Any
    briefing: Any
    adaptation_result: Optional[Dict[str, Any]]
    messages: List[str]
