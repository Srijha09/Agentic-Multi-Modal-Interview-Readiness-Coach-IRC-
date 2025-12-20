"""
Migration script to add hours_per_week column to study_plans table.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.db.database import engine

def migrate():
    """Add hours_per_week column if it doesn't exist."""
    print("Migrating database: Adding hours_per_week column to study_plans...")
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(study_plans)"))
            columns = [row[1] for row in result]
            
            if 'hours_per_week' in columns:
                print("✓ Column 'hours_per_week' already exists. No migration needed.")
                return
            
            # Add the column
            print("  Adding hours_per_week column...")
            conn.execute(text("ALTER TABLE study_plans ADD COLUMN hours_per_week REAL DEFAULT 10.0"))
            conn.commit()
            print("✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()


