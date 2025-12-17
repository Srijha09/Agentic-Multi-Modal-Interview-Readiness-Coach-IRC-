"""
Database initialization script.
Creates all tables if they don't exist.
"""
from app.db.database import engine, Base
from app.db.models import (
    User,
    Document,
    StudyPlan,
    DailyTask,
    PracticeAttempt,
    SkillMastery
)

def init_db():
    """Initialize database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()



