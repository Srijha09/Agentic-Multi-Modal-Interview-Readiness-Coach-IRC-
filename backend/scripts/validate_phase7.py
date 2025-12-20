"""
Validation script for Phase 7: Practice Generator
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import (
    User, DailyTask, PracticeItem, PracticeTypeEnum, DifficultyLevelEnum
)
from app.services.practice_generator import PracticeGenerator


def test_imports():
    """Test that all Phase 7 modules import correctly."""
    print("Testing Phase 7 imports...")
    try:
        from app.services.practice_generator import PracticeGenerator
        from app.api.v1.endpoints.practice import router
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_practice_generator_initialization():
    """Test that PracticeGenerator can be initialized."""
    print("\nTesting PracticeGenerator initialization...")
    try:
        generator = PracticeGenerator()
        assert generator.llm is not None
        assert generator.quiz_prompt is not None
        assert generator.flashcard_prompt is not None
        assert generator.behavioral_prompt is not None
        assert generator.system_design_prompt is not None
        print("✓ PracticeGenerator initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return False


def test_quiz_generation():
    """Test quiz generation."""
    print("\nTesting quiz generation...")
    try:
        generator = PracticeGenerator()
        db = SessionLocal()
        
        # Test MCQ quiz
        quiz_data = generator.generate_quiz(
            skill_names=["Python", "Data Structures"],
            quiz_type="mcq",
            difficulty=DifficultyLevelEnum.INTERMEDIATE,
            context="Interview preparation"
        )
        
        assert quiz_data["practice_type"] == PracticeTypeEnum.QUIZ
        assert "question" in quiz_data
        assert "options" in quiz_data["content"]
        assert len(quiz_data["content"]["options"]) == 4
        assert "expected_answer" in quiz_data
        print("✓ MCQ quiz generation successful")
        
        # Test short-answer quiz
        quiz_data = generator.generate_quiz(
            skill_names=["Machine Learning"],
            quiz_type="short_answer",
            difficulty=DifficultyLevelEnum.ADVANCED,
            context="Interview preparation"
        )
        
        assert quiz_data["practice_type"] == PracticeTypeEnum.QUIZ
        assert "question" in quiz_data
        assert "key_points" in quiz_data["content"]
        print("✓ Short-answer quiz generation successful")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Quiz generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flashcard_generation():
    """Test flashcard generation."""
    print("\nTesting flashcard generation...")
    try:
        generator = PracticeGenerator()
        
        flashcard_data = generator.generate_flashcard(
            skill_names=["React", "JavaScript"],
            difficulty=DifficultyLevelEnum.BEGINNER,
            context="Frontend development"
        )
        
        assert flashcard_data["practice_type"] == PracticeTypeEnum.FLASHCARD
        assert "question" in flashcard_data  # Front side
        assert "back" in flashcard_data["content"]  # Back side
        assert flashcard_data["expected_answer"] is not None
        print("✓ Flashcard generation successful")
        return True
    except Exception as e:
        print(f"✗ Flashcard generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_behavioral_prompt_generation():
    """Test behavioral prompt generation."""
    print("\nTesting behavioral prompt generation...")
    try:
        generator = PracticeGenerator()
        
        behavioral_data = generator.generate_behavioral_prompt(
            skill_names=["Leadership", "Teamwork"],
            difficulty=DifficultyLevelEnum.INTERMEDIATE,
            context="Software engineering role"
        )
        
        assert behavioral_data["practice_type"] == PracticeTypeEnum.BEHAVIORAL
        assert "question" in behavioral_data
        assert "competency" in behavioral_data["content"]
        assert "star_guidance" in behavioral_data["content"]
        assert "rubric" in behavioral_data
        print("✓ Behavioral prompt generation successful")
        return True
    except Exception as e:
        print(f"✗ Behavioral prompt generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_design_generation():
    """Test system design prompt generation."""
    print("\nTesting system design prompt generation...")
    try:
        generator = PracticeGenerator()
        
        design_data = generator.generate_system_design_prompt(
            skill_names=["System Design", "Scalability"],
            difficulty=DifficultyLevelEnum.ADVANCED,
            context="Backend engineering role"
        )
        
        assert design_data["practice_type"] == PracticeTypeEnum.SYSTEM_DESIGN
        assert "question" in design_data
        assert "requirements" in design_data["content"]
        assert "constraints" in design_data["content"]
        assert "evaluation_framework" in design_data["content"]
        assert "rubric" in design_data
        print("✓ System design prompt generation successful")
        return True
    except Exception as e:
        print(f"✗ System design prompt generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_based_generation():
    """Test generating practice items for a task."""
    print("\nTesting task-based practice generation...")
    try:
        db = SessionLocal()
        generator = PracticeGenerator()
        
        # Find a task
        task = db.query(DailyTask).first()
        if not task:
            print("⚠ No tasks found in database. Skipping task-based test.")
            db.close()
            return True
        
        user_id = task.study_plan.user_id
        
        # Generate flashcards for task
        practice_items = generator.generate_for_task(
            task=task,
            practice_type=PracticeTypeEnum.FLASHCARD,
            user_id=user_id,
            db=db,
            count=1
        )
        
        assert len(practice_items) > 0
        assert all(isinstance(item, PracticeItem) for item in practice_items)
        assert all(item.task_id == task.id for item in practice_items)
        
        db.rollback()  # Don't commit test data
        db.close()
        print("✓ Task-based practice generation successful")
        return True
    except Exception as e:
        print(f"✗ Task-based generation error: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
            db.close()
        return False


def test_difficulty_determination():
    """Test difficulty determination based on mastery."""
    print("\nTesting difficulty determination...")
    try:
        db = SessionLocal()
        generator = PracticeGenerator()
        
        # Find a user
        user = db.query(User).first()
        if not user:
            print("⚠ No users found. Skipping difficulty test.")
            db.close()
            return True
        
        # Test with no mastery (should default to BEGINNER)
        difficulty = generator._determine_difficulty(
            skill_names=["Python"],
            user_id=user.id,
            db=db
        )
        
        assert difficulty in DifficultyLevelEnum
        print(f"✓ Difficulty determination successful: {difficulty.value}")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Difficulty determination error: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.close()
        return False


def main():
    """Run all Phase 7 validation tests."""
    print("=" * 60)
    print("Phase 7 Validation: Practice Generator")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("PracticeGenerator Initialization", test_practice_generator_initialization),
        ("Quiz Generation", test_quiz_generation),
        ("Flashcard Generation", test_flashcard_generation),
        ("Behavioral Prompt Generation", test_behavioral_prompt_generation),
        ("System Design Generation", test_system_design_generation),
        ("Difficulty Determination", test_difficulty_determination),
        ("Task-Based Generation", test_task_based_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Phase 7 is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


