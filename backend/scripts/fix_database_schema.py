"""
Fix database schema by adding missing columns or recreating tables.
Run this if you get "no such column" errors.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from app.db.database import engine, Base
from app.db.models import StudyPlan, Week, Day, DailyTask

def fix_schema():
    """Add missing columns or recreate tables."""
    print("Fixing database schema...")
    
    with engine.connect() as conn:
        # Check study_plans table
        inspector = inspect(engine)
        if 'study_plans' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('study_plans')]
            print(f"Current study_plans columns: {columns}")
            
            if 'hours_per_week' not in columns:
                print("  Adding hours_per_week column...")
                try:
                    conn.execute(text("ALTER TABLE study_plans ADD COLUMN hours_per_week REAL DEFAULT 10.0"))
                    conn.commit()
                    print("  ✓ Added hours_per_week column")
                except Exception as e:
                    print(f"  ✗ Failed to add column: {e}")
                    print("  Attempting to recreate table...")
                    # Drop and recreate
                    conn.execute(text("DROP TABLE IF EXISTS study_plans"))
                    conn.commit()
                    Base.metadata.create_all(bind=engine, tables=[StudyPlan.__table__])
                    print("  ✓ Recreated study_plans table")
        else:
            print("  Creating study_plans table...")
            Base.metadata.create_all(bind=engine, tables=[StudyPlan.__table__])
            print("  ✓ Created study_plans table")
        
        # Ensure all tables exist
        print("\nEnsuring all tables exist...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database schema fixed!")

if __name__ == "__main__":
    fix_schema()


