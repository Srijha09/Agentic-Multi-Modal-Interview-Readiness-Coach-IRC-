"""
Validation script for Phase 6: Daily Coach Agent
"""
import sys
from pathlib import Path
import asyncio
import httpx
from datetime import date, datetime, timedelta

# Add the backend directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import SessionLocal
from app.db.models import User, StudyPlan, DailyTask, TaskStatusEnum
from app.services.daily_coach import DailyCoach

# Fix Windows encoding for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_ID = 1


def setup_test_data(db_session: SessionLocal):
    """Ensure test user and study plan exist."""
    print("Setting up test data...")
    user = db_session.query(User).filter(User.id == TEST_USER_ID).first()
    if not user:
        user = User(id=TEST_USER_ID, email="test@example.com", name="Test User")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        print(f"✓ Created test user {user.id}")
    else:
        print(f"✓ Test user {user.id} already exists.")

    # Check for study plan
    study_plan = db_session.query(StudyPlan).filter(
        StudyPlan.user_id == TEST_USER_ID
    ).order_by(StudyPlan.created_at.desc()).first()
    
    if not study_plan:
        print("⚠ No study plan found. Please generate one first using /api/v1/plans/generate")
        return False
    
    print(f"✓ Found study plan {study_plan.id}")
    return True


async def validate_daily_briefing():
    """Test daily briefing endpoint."""
    print("\n=== Testing Daily Briefing ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{API_BASE_URL}/coach/briefing",
            params={"user_id": TEST_USER_ID}
        )
        
        if response.status_code == 200:
            briefing = response.json()
            print(f"✓ Daily briefing retrieved successfully")
            print(f"  Date: {briefing['date']}")
            print(f"  Total tasks: {briefing['total_tasks']}")
            print(f"  Completed: {briefing['completed_tasks']}")
            print(f"  Pending: {briefing['pending_tasks']}")
            print(f"  Overdue: {briefing['overdue_tasks']}")
            print(f"  Completion: {briefing['completion_percentage']:.1f}%")
            if briefing.get('motivational_message'):
                print(f"  Message: {briefing['motivational_message']}")
            return True
        else:
            print(f"✗ Failed to get briefing: {response.status_code}")
            print(f"  Error: {response.text}")
            return False


async def validate_task_completion():
    """Test task completion endpoint."""
    print("\n=== Testing Task Completion ===")
    
    # First, get a task to complete
    db = SessionLocal()
    try:
        task = db.query(DailyTask).filter(
            DailyTask.study_plan_id.in_(
                db.query(StudyPlan.id).filter(StudyPlan.user_id == TEST_USER_ID)
            ),
            DailyTask.status == TaskStatusEnum.PENDING
        ).first()
        
        if not task:
            print("⚠ No pending tasks found to complete")
            return False
        
        print(f"  Found task {task.id}: {task.title}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/coach/tasks/{task.id}/complete",
                params={"actual_minutes": 45}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Task marked as completed")
                print(f"  Status: {result['status']}")
                print(f"  Completed at: {result.get('completed_at', 'N/A')}")
                return True
            else:
                print(f"✗ Failed to complete task: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
    finally:
        db.close()


async def validate_task_reschedule():
    """Test task rescheduling."""
    print("\n=== Testing Task Rescheduling ===")
    
    db = SessionLocal()
    try:
        # Get a task to reschedule
        task = db.query(DailyTask).filter(
            DailyTask.study_plan_id.in_(
                db.query(StudyPlan.id).filter(StudyPlan.user_id == TEST_USER_ID)
            )
        ).first()
        
        if not task:
            print("⚠ No tasks found to reschedule")
            return False
        
        new_date = (date.today() + timedelta(days=2)).isoformat()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/coach/tasks/{task.id}/reschedule",
                json={
                    "new_date": new_date,
                    "reason": "Test rescheduling"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Task rescheduled successfully")
                print(f"  Old date: {result['old_date']}")
                print(f"  New date: {result['new_date']}")
                print(f"  Message: {result['message']}")
                return True
            else:
                print(f"✗ Failed to reschedule task: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
    finally:
        db.close()


async def validate_carry_over():
    """Test carry-over functionality."""
    print("\n=== Testing Carry-Over ===")
    
    from_date = (date.today() - timedelta(days=1)).isoformat()
    to_date = date.today().isoformat()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/coach/carry-over",
            params={
                "user_id": TEST_USER_ID,
                "from_date": from_date,
                "to_date": to_date
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Carry-over processed")
            print(f"  Total carried over: {result['total_carried_over']}")
            print(f"  Rescheduled tasks: {len(result['rescheduled_tasks'])}")
            return True
        else:
            print(f"✗ Failed to carry over tasks: {response.status_code}")
            print(f"  Error: {response.text}")
            return False


async def validate_auto_reschedule():
    """Test auto-reschedule functionality."""
    print("\n=== Testing Auto-Reschedule ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/coach/auto-reschedule",
            params={"user_id": TEST_USER_ID}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Auto-reschedule completed")
            print(f"  Rescheduled count: {result['rescheduled_count']}")
            print(f"  Message: {result['message']}")
            return True
        else:
            print(f"✗ Failed to auto-reschedule: {response.status_code}")
            print(f"  Error: {response.text}")
            return False


async def validate_phase6():
    """Main validation function."""
    print("\n" + "="*60)
    print("Phase 6: Daily Coach Agent - Validation")
    print("="*60)
    
    db = SessionLocal()
    try:
        if not setup_test_data(db):
            print("\n⚠ Please generate a study plan first:")
            print(f"  POST {API_BASE_URL}/plans/generate?user_id={TEST_USER_ID}&weeks=4&hours_per_week=10")
            return False
    finally:
        db.close()
    
    results = []
    
    # Test daily briefing
    results.append(await validate_daily_briefing())
    
    # Test task completion
    results.append(await validate_task_completion())
    
    # Test task rescheduling
    results.append(await validate_task_reschedule())
    
    # Test carry-over
    results.append(await validate_carry_over())
    
    # Test auto-reschedule
    results.append(await validate_auto_reschedule())
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Phase 6 is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(validate_phase6())
    sys.exit(0 if success else 1)

