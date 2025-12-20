"""
Fix skill_mastery table by adding missing columns.
SQLite version - handles ALTER TABLE limitations.
"""
import sys
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Get database path
DB_PATH = PROJECT_ROOT / "irc_coach.db"

def fix_skill_mastery_table():
    """Add missing columns to skill_mastery table if they don't exist."""
    if not DB_PATH.exists():
        print(f"Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get current table structure
    cursor.execute("PRAGMA table_info(skill_mastery)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    print(f"Current columns in skill_mastery: {list(columns.keys())}")
    
    # Expected columns
    expected_columns = {
        'practice_count': 'INTEGER',
        'improvement_trend': 'VARCHAR',
        'updated_at': 'DATETIME'
    }
    
    missing_columns = []
    for col_name, col_type in expected_columns.items():
        if col_name not in columns:
            missing_columns.append((col_name, col_type))
    
    if not missing_columns:
        print("\nAll expected columns are present!")
        conn.close()
        return
    
    print(f"\nAdding {len(missing_columns)} missing column(s)...")
    
    for col_name, col_type in missing_columns:
        try:
            if col_name == 'practice_count':
                cursor.execute(f"""
                    ALTER TABLE skill_mastery 
                    ADD COLUMN {col_name} INTEGER DEFAULT 0
                """)
            elif col_name == 'improvement_trend':
                cursor.execute(f"""
                    ALTER TABLE skill_mastery 
                    ADD COLUMN {col_name} VARCHAR
                """)
            elif col_name == 'updated_at':
                cursor.execute(f"""
                    ALTER TABLE skill_mastery 
                    ADD COLUMN {col_name} DATETIME
                """)
            conn.commit()
            print(f"Column {col_name} added successfully!")
        except sqlite3.OperationalError as e:
            print(f"Error adding column {col_name}: {e}")
            conn.rollback()
    
    # Verify the columns exist now
    cursor.execute("PRAGMA table_info(skill_mastery)")
    new_columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"\nUpdated columns in skill_mastery: {list(new_columns.keys())}")
    
    # Check if all expected columns are present
    all_expected = {
        'id', 'user_id', 'skill_name', 'mastery_score', 
        'last_practiced', 'practice_count', 'improvement_trend',
        'created_at', 'updated_at'
    }
    
    if all_expected.issubset(set(new_columns.keys())):
        print("\nAll expected columns are present!")
    else:
        missing = all_expected - set(new_columns.keys())
        print(f"\nStill missing columns: {missing}")
    
    conn.close()

if __name__ == "__main__":
    fix_skill_mastery_table()

