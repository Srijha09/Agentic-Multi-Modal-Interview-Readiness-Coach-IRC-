"""
Serialization and deserialization utilities for models and schemas.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.db.models import (
    User, Document, Skill, SkillEvidence, Gap, StudyPlan, Week, Day,
    DailyTask, PracticeItem, PracticeAttempt, Evaluation, Rubric,
    SkillMastery, CalendarEvent
)
from app.schemas import (
    UserResponse, DocumentResponse, SkillResponse, SkillEvidenceResponse,
    GapResponse, StudyPlanResponse, WeekResponse, DayResponse, TaskResponse,
    PracticeItemResponse, PracticeAttemptResponse, EvaluationResponse,
    RubricResponse, MasteryResponse, CalendarEventResponse
)


def serialize_user(user: User) -> Dict[str, Any]:
    """Serialize User model to dict."""
    return UserResponse.model_validate(user).model_dump()


def serialize_document(doc: Document) -> Dict[str, Any]:
    """Serialize Document model to dict."""
    return DocumentResponse.model_validate(doc).model_dump()


def serialize_skill(skill: Skill) -> Dict[str, Any]:
    """Serialize Skill model to dict."""
    return SkillResponse.model_validate(skill).model_dump()


def serialize_skill_evidence(evidence: SkillEvidence) -> Dict[str, Any]:
    """Serialize SkillEvidence model to dict."""
    return SkillEvidenceResponse.model_validate(evidence).model_dump()


def skill_evidence_to_response(evidence: SkillEvidence) -> SkillEvidenceResponse:
    """Convert SkillEvidence model to SkillEvidenceResponse schema."""
    return SkillEvidenceResponse.model_validate(evidence)


def serialize_gap(gap: Gap, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize Gap model to dict."""
    gap_dict = {
        "id": gap.id,
        "skill_id": gap.skill_id,
        "user_id": gap.user_id,
        "required_skill_name": gap.required_skill_name,
        "coverage_status": gap.coverage_status.value,
        "priority": gap.priority.value,
        "gap_reason": gap.gap_reason,
        "evidence_summary": gap.evidence_summary,
        "estimated_learning_hours": gap.estimated_learning_hours,
        "created_at": gap.created_at.isoformat() if gap.created_at else None,
    }
    
    if include_relations:
        if gap.skill:
            gap_dict["skill"] = serialize_skill(gap.skill)
        if gap.skill_evidence:
            gap_dict["evidence"] = [serialize_skill_evidence(e) for e in gap.skill_evidence]
    
    return gap_dict


def serialize_study_plan(plan: StudyPlan, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize StudyPlan model to dict."""
    from datetime import datetime
    
    plan_dict = {
        "id": plan.id,
        "user_id": plan.user_id,
        "interview_date": plan.interview_date if plan.interview_date else None,
        "weeks": plan.weeks,
        "hours_per_week": plan.hours_per_week,
        "focus_areas": plan.focus_areas or [],
        "created_at": plan.created_at if plan.created_at else None,
        "updated_at": plan.updated_at if plan.updated_at else None,
    }
    
    if include_relations:
        # Calculate totals
        total_hours = sum(week.estimated_hours for week in plan.weeks_data) if plan.weeks_data else 0.0
        completed_tasks = sum(1 for task in plan.daily_tasks if task.status.value == "completed") if plan.daily_tasks else 0
        total_tasks = len(plan.daily_tasks) if plan.daily_tasks else 0
        completion_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        plan_dict["total_estimated_hours"] = total_hours
        plan_dict["completion_percentage"] = completion_pct
        plan_dict["weeks_data"] = [serialize_week(week) for week in plan.weeks_data] if plan.weeks_data else []
    
    return plan_dict


def serialize_week(week: Week, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize Week model to dict."""
    week_dict = {
        "id": week.id,
        "week_number": week.week_number,
        "theme": week.theme,
        "focus_skills": week.focus_skills or [],
        "estimated_hours": week.estimated_hours,
        "created_at": week.created_at.isoformat() if week.created_at else None,
    }
    
    if include_relations and week.days:
        week_dict["days"] = [serialize_day(day) for day in week.days]
    
    return week_dict


def serialize_day(day: Day, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize Day model to dict."""
    from datetime import date as date_type
    
    # Handle date conversion - Day.date is DateTime, but schema expects date
    day_date = day.date
    if isinstance(day_date, datetime):
        day_date = day_date.date()
    elif day_date is None:
        day_date = None
    
    day_dict = {
        "id": day.id,
        "day_number": day.day_number,
        "date": day_date if isinstance(day_date, date_type) else None,
        "theme": day.theme,
        "estimated_hours": day.estimated_hours,
        "created_at": day.created_at if day.created_at else None,
    }
    
    if include_relations and day.tasks:
        day_dict["tasks"] = [serialize_task(task) for task in day.tasks]
    
    return day_dict


def serialize_task(task: DailyTask) -> Dict[str, Any]:
    """Serialize DailyTask model to dict."""
    # Handle None values before validation
    task_data = {
        "id": task.id,
        "task_type": task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
        "title": task.title,
        "description": task.description,
        "skill_names": task.skill_names if task.skill_names is not None else [],
        "estimated_minutes": task.estimated_minutes,
        "dependencies": task.dependencies if task.dependencies is not None else [],
        "content": task.content if task.content is not None else {},
        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
        "completed_at": task.completed_at,
        "actual_minutes": task.actual_minutes,
        "created_at": task.created_at,
    }
    
    return TaskResponse.model_validate(task_data).model_dump()


def serialize_practice_item(item: PracticeItem) -> Dict[str, Any]:
    """Serialize PracticeItem model to dict."""
    return PracticeItemResponse.model_validate(item).model_dump()


def serialize_practice_attempt(attempt: PracticeAttempt, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize PracticeAttempt model to dict."""
    attempt_dict = PracticeAttemptResponse.model_validate(attempt).model_dump()
    
    if include_relations and attempt.practice_item:
        attempt_dict["practice_item"] = serialize_practice_item(attempt.practice_item)
    
    return attempt_dict


def serialize_evaluation(eval_obj: Evaluation, include_relations: bool = True) -> Dict[str, Any]:
    """Serialize Evaluation model to dict."""
    eval_dict = EvaluationResponse.model_validate(eval_obj).model_dump()
    
    if include_relations and eval_obj.rubric:
        eval_dict["rubric"] = RubricResponse.model_validate(eval_obj.rubric).model_dump()
    
    return eval_dict


def serialize_rubric(rubric: Rubric) -> Dict[str, Any]:
    """Serialize Rubric model to dict."""
    return RubricResponse.model_validate(rubric).model_dump()


def serialize_mastery(mastery: SkillMastery) -> Dict[str, Any]:
    """Serialize SkillMastery model to dict."""
    return MasteryResponse.model_validate(mastery).model_dump()


def serialize_calendar_event(event: CalendarEvent) -> Dict[str, Any]:
    """Serialize CalendarEvent model to dict."""
    return CalendarEventResponse.model_validate(event).model_dump()


def deserialize_study_plan_data(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize study plan JSON data structure."""
    # Validate and normalize plan data structure
    if not isinstance(plan_data, dict):
        raise ValueError("Plan data must be a dictionary")
    
    required_keys = ["weeks"]
    for key in required_keys:
        if key not in plan_data:
            raise ValueError(f"Plan data missing required key: {key}")
    
    # Normalize weeks structure
    if isinstance(plan_data["weeks"], list):
        normalized_weeks = []
        for week_idx, week_data in enumerate(plan_data["weeks"], start=1):
            if isinstance(week_data, dict):
                week_data.setdefault("week_number", week_idx)
                week_data.setdefault("theme", f"Week {week_idx}")
                week_data.setdefault("days", [])
                normalized_weeks.append(week_data)
        plan_data["weeks"] = normalized_weeks
    
    return plan_data

