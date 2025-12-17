"""
Validation utilities for models and schemas.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import ValidationError
from app.schemas import (
    SkillCreate, SkillEvidenceCreate, GapCreate, StudyPlanCreate,
    TaskCreate, PracticeItemCreate, PracticeAttemptCreate
)


def validate_skill_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate skill creation data."""
    try:
        skill = SkillCreate(**data)
        return skill.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid skill data: {e}")


def validate_gap_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate gap creation data."""
    try:
        gap = GapCreate(**data)
        return gap.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid gap data: {e}")


def validate_study_plan_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate study plan creation data."""
    try:
        plan = StudyPlanCreate(**data)
        return plan.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid study plan data: {e}")


def validate_task_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate task creation data."""
    try:
        task = TaskCreate(**data)
        return task.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid task data: {e}")


def validate_practice_item_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate practice item creation data."""
    try:
        item = PracticeItemCreate(**data)
        return item.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid practice item data: {e}")


def validate_mastery_score(score: float) -> float:
    """Validate mastery score is between 0.0 and 1.0."""
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Mastery score must be between 0.0 and 1.0, got {score}")
    return score


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate that start_date is before end_date."""
    if start_date > end_date:
        raise ValueError(f"Start date {start_date} must be before end date {end_date}")
    return True


def validate_skill_names(skill_names: List[str]) -> List[str]:
    """Validate and normalize skill names."""
    if not isinstance(skill_names, list):
        raise ValueError("skill_names must be a list")
    
    normalized = []
    for skill_name in skill_names:
        if not isinstance(skill_name, str):
            raise ValueError(f"Skill name must be a string, got {type(skill_name)}")
        normalized_name = skill_name.strip()
        if normalized_name:
            normalized.append(normalized_name)
    
    return normalized


def validate_json_structure(data: Any, expected_type: type) -> Any:
    """Validate JSON structure matches expected type."""
    if not isinstance(data, expected_type):
        raise ValueError(f"Expected {expected_type.__name__}, got {type(data).__name__}")
    return data

