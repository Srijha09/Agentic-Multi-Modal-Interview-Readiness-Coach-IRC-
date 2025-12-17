"""
Database initialization script.
Creates all tables if they don't exist.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from app.db.database import engine, Base
from app.db.models import (
    User,
    Document,
    Skill,
    SkillEvidence,
    Gap,
    StudyPlan,
    Week,
    Day,
    DailyTask,
    PracticeItem,
    PracticeAttempt,
    Evaluation,
    Rubric,
    SkillMastery,
    CalendarEvent
)

def init_db():
    """Initialize database by creating all tables."""
    print("Creating database tables...")
    print("  - Users")
    print("  - Documents")
    print("  - Skills")
    print("  - Skill Evidence")
    print("  - Gaps")
    print("  - Study Plans")
    print("  - Weeks")
    print("  - Days")
    print("  - Daily Tasks")
    print("  - Practice Items")
    print("  - Practice Attempts")
    print("  - Evaluations")
    print("  - Rubrics")
    print("  - Skill Mastery")
    print("  - Calendar Events")
    
    Base.metadata.create_all(bind=engine)
    print("\n✓ Database tables created successfully!")
    print(f"✓ Total tables: {len(Base.metadata.tables)}")


if __name__ == "__main__":
    init_db()




