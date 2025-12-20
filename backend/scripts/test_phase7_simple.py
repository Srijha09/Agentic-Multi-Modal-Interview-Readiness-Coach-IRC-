"""
Simple test script to verify Phase 7 Practice Generator is working.
Run this to test practice generation without needing the full validation suite.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User, DailyTask, PracticeItem, PracticeTypeEnum
from app.services.practice_generator import PracticeGenerator


def main():
    print("=" * 60)
    print("Phase 7: Practice Generator - Simple Verification")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Step 1: Check if PracticeGenerator can be imported and initialized
        print("\n1. Testing PracticeGenerator import and initialization...")
        generator = PracticeGenerator()
        print("   ✓ PracticeGenerator initialized successfully")
        
        # Step 2: Find a task to generate practice for
        print("\n2. Looking for a task to generate practice items...")
        task = db.query(DailyTask).first()
        
        if not task:
            print("   ⚠ No tasks found in database.")
            print("   → You need to:")
            print("     1. Upload a resume and job description")
            print("     2. Generate a study plan")
            print("     3. Then come back to test Phase 7")
            return
        
        print(f"   ✓ Found task: {task.title}")
        print(f"   → Task ID: {task.id}")
        print(f"   → Skills: {', '.join(task.skill_names) if task.skill_names else 'None'}")
        
        user_id = task.study_plan.user_id
        print(f"   → User ID: {user_id}")
        
        # Step 3: Test generating a flashcard
        print("\n3. Testing flashcard generation...")
        try:
            practice_items = generator.generate_for_task(
                task=task,
                practice_type=PracticeTypeEnum.FLASHCARD,
                user_id=user_id,
                db=db,
                count=1
            )
            
            if practice_items:
                item = practice_items[0]
                print(f"   ✓ Generated flashcard:")
                print(f"      - ID: {item.id}")
                print(f"      - Title: {item.title}")
                print(f"      - Question: {item.question[:80]}...")
                print(f"      - Difficulty: {item.difficulty.value}")
                db.commit()
                print("   ✓ Flashcard saved to database")
            else:
                print("   ✗ No practice items generated")
        except Exception as e:
            print(f"   ✗ Error generating flashcard: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        
        # Step 4: Test generating a quiz
        print("\n4. Testing quiz generation...")
        try:
            practice_items = generator.generate_for_task(
                task=task,
                practice_type=PracticeTypeEnum.QUIZ,
                user_id=user_id,
                db=db,
                count=1
            )
            
            if practice_items:
                print(f"   ✓ Generated {len(practice_items)} quiz item(s)")
                for item in practice_items:
                    print(f"      - {item.title}")
                    if item.content and "options" in item.content:
                        print(f"      - Has {len(item.content['options'])} options")
                db.commit()
                print("   ✓ Quiz saved to database")
            else:
                print("   ✗ No quiz items generated")
        except Exception as e:
            print(f"   ✗ Error generating quiz: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        
        # Step 5: Check what practice items exist
        print("\n5. Checking existing practice items in database...")
        all_items = db.query(PracticeItem).filter(PracticeItem.task_id == task.id).all()
        print(f"   ✓ Found {len(all_items)} practice item(s) for this task")
        
        if all_items:
            print("\n   Practice Items Summary:")
            for item in all_items[:5]:  # Show first 5
                print(f"      - [{item.practice_type.value}] {item.title}")
                print(f"        Difficulty: {item.difficulty.value}")
                print(f"        Skills: {', '.join(item.skill_names) if item.skill_names else 'None'}")
        
        # Step 6: Test API endpoint availability
        print("\n6. Testing API endpoint structure...")
        try:
            from app.api.v1.endpoints.practice import router
            routes = [route.path for route in router.routes]
            print(f"   ✓ Practice API routes available:")
            for route in routes:
                print(f"      - {route}")
        except Exception as e:
            print(f"   ✗ Error checking API routes: {e}")
        
        print("\n" + "=" * 60)
        print("✓ Phase 7 Verification Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start your backend server: python backend/main.py")
        print("2. Test API endpoints:")
        print("   - POST /api/v1/practice/items/generate?task_id={task_id}&practice_type=quiz&count=1")
        print("   - GET /api/v1/practice/items/task/{task_id}")
        print("3. Check the frontend to see practice items in the Daily Coach page")
        
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()


