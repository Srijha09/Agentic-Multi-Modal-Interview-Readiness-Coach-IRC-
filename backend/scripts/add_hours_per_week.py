"""
Quick fix: Add missing columns to database tables.
Fixes schema mismatches between models and database.
"""
import sqlite3
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path(__file__).resolve().parents[1] / "irc_coach.db"

def add_columns():
    """Add missing columns to database tables."""
    print(f"Connecting to database: {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Fix study_plans table
        print("\n=== Fixing study_plans table ===")
        cursor.execute("PRAGMA table_info(study_plans)")
        study_plans_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(study_plans_columns)}")
        
        if 'hours_per_week' not in study_plans_columns:
            print("Adding hours_per_week column...")
            cursor.execute("ALTER TABLE study_plans ADD COLUMN hours_per_week REAL DEFAULT 10.0")
            conn.commit()
            print("[OK] Added hours_per_week")
        else:
            print("[OK] hours_per_week exists")
        
        if 'focus_areas' not in study_plans_columns:
            print("Adding focus_areas column...")
            cursor.execute("ALTER TABLE study_plans ADD COLUMN focus_areas TEXT")
            conn.commit()
            print("[OK] Added focus_areas")
        else:
            print("[OK] focus_areas exists")
        
        # Fix daily_tasks table
        print("\n=== Fixing daily_tasks table ===")
        cursor.execute("PRAGMA table_info(daily_tasks)")
        daily_tasks_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(daily_tasks_columns)}")
        
        # Required columns for daily_tasks
        required_daily_tasks_columns = {
            'day_id': 'INTEGER',
            'status': 'TEXT',
            'title': 'TEXT',
            'description': 'TEXT',
            'skill_names': 'TEXT',
            'estimated_minutes': 'INTEGER',
            'actual_minutes': 'INTEGER',
            'dependencies': 'TEXT',
            'completed_at': 'TEXT'
        }
        
        for col_name, col_type in required_daily_tasks_columns.items():
            if col_name not in daily_tasks_columns:
                print(f"Adding {col_name} column...")
                cursor.execute(f"ALTER TABLE daily_tasks ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"[OK] Added {col_name}")
            else:
                print(f"[OK] {col_name} exists")
        
        # Check if weeks and days tables exist
        print("\n=== Checking weeks and days tables ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'weeks' not in tables:
            print("[WARNING] weeks table does not exist - will be created on next init_db")
        else:
            print("[OK] weeks table exists")
        
        if 'days' not in tables:
            print("[WARNING] days table does not exist - will be created on next init_db")
        else:
            print("[OK] days table exists")
        
        # Update existing NULL values to empty lists/objects
        print("\n=== Updating NULL values in daily_tasks ===")
        cursor.execute("UPDATE daily_tasks SET dependencies = '[]' WHERE dependencies IS NULL")
        cursor.execute("UPDATE daily_tasks SET skill_names = '[]' WHERE skill_names IS NULL")
        cursor.execute("UPDATE daily_tasks SET content = '{}' WHERE content IS NULL")
        conn.commit()
        print("[OK] Updated NULL values to defaults")
        
        print("\n[OK] Database schema fixes completed!")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()

