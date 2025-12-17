"""
Validation script for Phase 2: Core Data Models & Skill/Gaps Schema.
Tests that all schemas, models, and utilities are properly set up.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def test_imports():
    """Test that all critical imports work."""
    print("Testing imports...")
    
    try:
        # Test schema imports
        from app.schemas import (
            UserCreate, UserResponse,
            SkillCreate, SkillResponse,
            GapCreate, GapResponse,
            StudyPlanCreate, StudyPlanResponse,
            TaskCreate, TaskResponse,
            PracticeItemCreate, PracticeItemResponse,
            EvaluationCreate, EvaluationResponse,
            MasteryResponse,
            CalendarEventCreate, CalendarEventResponse,
            DocumentCreate, DocumentResponse
        )
        print("  [OK] All schemas import successfully")
        
        # Test model imports
        from app.db.models import (
            User, Document, Skill, SkillEvidence, Gap,
            StudyPlan, Week, Day, DailyTask,
            PracticeItem, PracticeAttempt, Evaluation, Rubric,
            SkillMastery, CalendarEvent
        )
        print("  [OK] All models import successfully")
        
        # Test utility imports
        from app.core.serializers import (
            serialize_user, serialize_skill, serialize_gap,
            serialize_study_plan, serialize_task
        )
        print("  [OK] Serializers import successfully")
        
        from app.core.validators import (
            validate_skill_data, validate_gap_data,
            validate_mastery_score
        )
        print("  [OK] Validators import successfully")
        
        from app.fixtures.sample_data import (
            get_sample_user, get_sample_skill, get_sample_gap
        )
        print("  [OK] Sample data fixtures import successfully")
        
        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False


def test_schema_validation():
    """Test that schemas validate correctly."""
    print("\nTesting schema validation...")
    
    try:
        from app.schemas import UserCreate, SkillCreate, GapCreate
        from app.fixtures.sample_data import get_sample_user, get_sample_skill, get_sample_gap
        
        # Test User schema
        user_data = get_sample_user()
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        print("  [OK] User schema validation works")
        
        # Test Skill schema
        skill_data = get_sample_skill()
        skill = SkillCreate(**skill_data)
        assert skill.name == "Python"
        print("  [OK] Skill schema validation works")
        
        # Test Gap schema
        gap_data = get_sample_gap()
        gap = GapCreate(**gap_data)
        assert gap.priority.value == "high"
        print("  [OK] Gap schema validation works")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Schema validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validators():
    """Test validation functions."""
    print("\nTesting validators...")
    
    try:
        from app.core.validators import validate_mastery_score
        
        # Test valid scores
        validate_mastery_score(0.0)
        validate_mastery_score(0.5)
        validate_mastery_score(1.0)
        print("  [OK] Valid mastery scores accepted")
        
        # Test invalid score
        try:
            validate_mastery_score(1.5)
            print("  [FAIL] Should have rejected score > 1.0")
            return False
        except ValueError:
            print("  [OK] Invalid mastery scores rejected")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Validator error: {e}")
        return False


def test_database_models():
    """Test that database models are properly defined."""
    print("\nTesting database models...")
    
    try:
        from app.db.database import Base
        from app.db.models import (
            User, Document, Skill, SkillEvidence, Gap,
            StudyPlan, Week, Day, DailyTask,
            PracticeItem, PracticeAttempt, Evaluation, Rubric,
            SkillMastery, CalendarEvent
        )
        
        # Check that all models are registered with Base
        tables = list(Base.metadata.tables.keys())
        expected_tables = [
            "users", "documents", "skills", "skill_evidence", "gaps",
            "study_plans", "weeks", "days", "daily_tasks",
            "practice_items", "practice_attempts", "evaluations", "rubrics",
            "skill_mastery", "calendar_events"
        ]
        
        for table in expected_tables:
            if table not in tables:
                print(f"  [FAIL] Missing table: {table}")
                return False
        
        print(f"  [OK] All {len(expected_tables)} tables are defined")
        return True
    except Exception as e:
        print(f"  [FAIL] Database model error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 validation tests."""
    print("=" * 60)
    print("Phase 2 Validation: Core Data Models & Skill/Gaps Schema")
    print("=" * 60)
    print()
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Schema Validation", test_schema_validation()))
    results.append(("Validators", test_validators()))
    results.append(("Database Models", test_database_models()))
    
    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n[SUCCESS] Phase 2 validation complete! All checks passed.")
        print("\nNext steps:")
        print("  1. Install missing dependencies: pip install email-validator")
        print("  2. Run database initialization: python scripts/init_db.py")
        print("  3. Run serialization tests: python scripts/test_serialization.py")
        return 0
    else:
        print("\n[FAIL] Some validation checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

