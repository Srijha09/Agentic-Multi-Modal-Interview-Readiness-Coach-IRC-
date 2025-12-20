"""
Verify database schema matches models.
"""
import sqlite3
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = Path(__file__).resolve().parents[1] / "irc_coach.db"

def verify_schema():
    """Check study_plans table structure."""
    print(f"Checking database schema: {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info(study_plans)")
        columns = cursor.fetchall()
        
        print("\nstudy_plans table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check for required columns
        column_names = [col[1] for col in columns]
        required = ['id', 'user_id', 'interview_date', 'weeks', 'hours_per_week', 'focus_areas', 'plan_data', 'created_at', 'updated_at']
        
        print("\nChecking required columns:")
        missing = []
        for req in required:
            if req in column_names:
                print(f"  [OK] {req}")
            else:
                print(f"  [MISSING] {req}")
                missing.append(req)
        
        if missing:
            print(f"\n[ERROR] Missing columns: {missing}")
            return False
        else:
            print("\n[OK] All required columns present!")
            return True
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    verify_schema()


