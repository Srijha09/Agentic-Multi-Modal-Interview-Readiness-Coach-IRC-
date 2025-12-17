"""
Test script to validate serialization/deserialization of models.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fixtures.sample_data import (
    get_sample_user,
    get_sample_skill,
    get_sample_gap,
    get_sample_study_plan,
    get_sample_task,
    get_sample_practice_item,
    get_sample_practice_attempt,
    get_sample_evaluation,
    get_sample_mastery,
    get_sample_calendar_event
)
from app.schemas import (
    SkillCreate,
    GapCreate,
    StudyPlanCreate,
    TaskCreate,
    PracticeItemCreate,
    PracticeAttemptCreate,
    MasteryUpdate
)
from app.core.validators import (
    validate_skill_data,
    validate_gap_data,
    validate_study_plan_data,
    validate_task_data,
    validate_practice_item_data,
    validate_mastery_score
)


def test_skill_serialization():
    """Test skill schema serialization."""
    print("Testing Skill serialization...")
    skill_data = get_sample_skill()
    skill = SkillCreate(**skill_data)
    assert skill.name == "Python"
    assert skill.category.value == "programming"
    print("  ✓ Skill serialization works")


def test_gap_serialization():
    """Test gap schema serialization."""
    print("Testing Gap serialization...")
    gap_data = get_sample_gap()
    gap = GapCreate(**gap_data)
    assert gap.priority.value == "high"
    assert gap.coverage_status.value == "missing"
    print("  ✓ Gap serialization works")


def test_study_plan_serialization():
    """Test study plan schema serialization."""
    print("Testing Study Plan serialization...")
    plan_data = get_sample_study_plan()
    plan = StudyPlanCreate(**plan_data)
    assert plan.weeks == 4
    assert plan.hours_per_week == 10.0
    print("  ✓ Study Plan serialization works")


def test_task_serialization():
    """Test task schema serialization."""
    print("Testing Task serialization...")
    task_data = get_sample_task()
    task = TaskCreate(**task_data)
    assert task.task_type.value == "learn"
    assert task.estimated_minutes == 60
    print("  ✓ Task serialization works")


def test_practice_item_serialization():
    """Test practice item schema serialization."""
    print("Testing Practice Item serialization...")
    item_data = get_sample_practice_item()
    item = PracticeItemCreate(**item_data)
    assert item.practice_type.value == "quiz"
    assert item.difficulty.value == "intermediate"
    print("  ✓ Practice Item serialization works")


def test_validation():
    """Test validation functions."""
    print("Testing validation functions...")
    
    # Test mastery score validation
    try:
        validate_mastery_score(0.5)
        validate_mastery_score(1.0)
        validate_mastery_score(0.0)
        print("  ✓ Mastery score validation works")
    except ValueError:
        print("  ✗ Mastery score validation failed")
        raise
    
    # Test invalid mastery score
    try:
        validate_mastery_score(1.5)
        print("  ✗ Should have raised ValueError for score > 1.0")
        raise AssertionError("Validation should have failed")
    except ValueError:
        print("  ✓ Invalid mastery score correctly rejected")
    
    # Test skill data validation
    skill_data = get_sample_skill()
    validated = validate_skill_data(skill_data)
    assert validated["name"] == "Python"
    print("  ✓ Skill data validation works")


def main():
    """Run all serialization tests."""
    print("=" * 50)
    print("Phase 2: Serialization/Deserialization Tests")
    print("=" * 50)
    print()
    
    try:
        test_skill_serialization()
        test_gap_serialization()
        test_study_plan_serialization()
        test_task_serialization()
        test_practice_item_serialization()
        test_validation()
        
        print()
        print("=" * 50)
        print("✓ All serialization tests passed!")
        print("=" * 50)
        return 0
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

