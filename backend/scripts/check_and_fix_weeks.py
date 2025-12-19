"""
Script to check study plan weeks and add missing weeks if needed.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import StudyPlan, Week, Day, DailyTask
from app.services.planner import StudyPlanner
from datetime import datetime, timedelta
from sqlalchemy import func

def check_and_fix_weeks():
    """Check study plans and add missing weeks."""
    db = SessionLocal()
    
    try:
        # Get all study plans
        plans = db.query(StudyPlan).all()
        
        for plan in plans:
            print(f"\n=== Study Plan ID: {plan.id} ===")
            print(f"User ID: {plan.user_id}")
            print(f"Requested weeks: {plan.weeks}")
            
            # Count actual weeks in database
            week_count = db.query(Week).filter(Week.study_plan_id == plan.id).count()
            print(f"Weeks in database: {week_count}")
            
            # Get existing week numbers
            existing_weeks = db.query(Week.week_number).filter(
                Week.study_plan_id == plan.id
            ).order_by(Week.week_number).all()
            existing_week_nums = [w[0] for w in existing_weeks]
            print(f"Existing week numbers: {existing_week_nums}")
            
            if week_count < plan.weeks:
                print(f"⚠️  Missing {plan.weeks - week_count} weeks!")
                print(f"   Plan expects {plan.weeks} weeks but only {week_count} exist.")
                print(f"   Missing weeks: {[i for i in range(1, plan.weeks + 1) if i not in existing_week_nums]}")
                
                # Option to add missing weeks
                response = input(f"\nAdd missing weeks for plan {plan.id}? (y/n): ")
                if response.lower() == 'y':
                    add_missing_weeks(db, plan, existing_week_nums)
            else:
                print("✅ All weeks present")
    
    finally:
        db.close()

def add_missing_weeks(db, plan, existing_week_nums):
    """Add missing weeks to a study plan."""
    from app.db.models import TaskTypeEnum, TaskStatusEnum
    
    print(f"\nAdding missing weeks to plan {plan.id}...")
    
    # Get the last week's date to continue from
    last_week = db.query(Week).filter(
        Week.study_plan_id == plan.id
    ).order_by(Week.week_number.desc()).first()
    
    # Calculate start date for new weeks
    if last_week:
        # Get the last day of the last week
        last_day = db.query(Day).filter(
            Day.week_id == last_week.id
        ).order_by(Day.day_number.desc()).first()
        
        if last_day and last_day.date:
            start_date = last_day.date.date() + timedelta(days=1)
        else:
            start_date = datetime.now().date()
    else:
        start_date = datetime.now().date()
    
    # Create missing weeks
    for week_num in range(1, plan.weeks + 1):
        if week_num not in existing_week_nums:
            print(f"  Creating Week {week_num}...")
            
            # Create week
            week = Week(
                study_plan_id=plan.id,
                week_number=week_num,
                theme=f"Week {week_num}: Additional Study Week",
                focus_skills=[],
                estimated_hours=plan.hours_per_week,
            )
            db.add(week)
            db.flush()
            
            # Create days for this week (5 days)
            for day_num in range(1, 6):
                day_date = start_date + timedelta(days=(week_num - len(existing_week_nums) - 1) * 7 + day_num - 1)
                
                day = Day(
                    week_id=week.id,
                    day_number=day_num,
                    date=datetime.combine(day_date, datetime.min.time()),
                    theme=f"Day {day_num}",
                    estimated_hours=plan.hours_per_week / 5,
                )
                db.add(day)
                db.flush()
                
                # Create a placeholder task
                task = DailyTask(
                    study_plan_id=plan.id,
                    day_id=day.id,
                    task_date=datetime.combine(day_date, datetime.min.time()),
                    task_type=TaskTypeEnum.LEARN,
                    title=f"Week {week_num} - Day {day_num} Study Task",
                    description="Complete your study tasks for this day",
                    skill_names=[],
                    estimated_minutes=int((plan.hours_per_week / 5) * 60),
                    status=TaskStatusEnum.PENDING,
                    dependencies=[],
                    content={
                        "study_materials": ["Review study materials"],
                        "resources": [],
                        "key_concepts": [],
                        "practice_exercises": []
                    },
                )
                db.add(task)
            
            print(f"  ✅ Created Week {week_num}")
    
    db.commit()
    print(f"\n✅ Successfully added missing weeks to plan {plan.id}")

if __name__ == "__main__":
    check_and_fix_weeks()

