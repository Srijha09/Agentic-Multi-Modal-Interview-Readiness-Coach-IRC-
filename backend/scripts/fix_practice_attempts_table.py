"""
Fix practice_attempts table by adding missing practice_item_id column.
SQLite version - handles ALTER TABLE limitations.
"""
import sys
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Get database path from config or use default
DB_PATH = PROJECT_ROOT / "irc_coach.db"

def fix_practice_attempts_table():
    """Add practice_item_id column if it doesn't exist."""
    if not DB_PATH.exists():
        print(f"Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get current table structure
    cursor.execute("PRAGMA table_info(practice_attempts)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns in practice_attempts: {columns}")
    
    if 'practice_item_id' not in columns:
        print("\nAdding practice_item_id column...")
        try:
            # SQLite supports ADD COLUMN but not with REFERENCES in ALTER TABLE
            # We'll add the column first, then the foreign key constraint separately if needed
            cursor.execute("""
                ALTER TABLE practice_attempts 
                ADD COLUMN practice_item_id INTEGER
            """)
            conn.commit()
            print("Column practice_item_id added successfully!")
        except sqlite3.OperationalError as e:
            print(f"Error adding column: {e}")
            conn.rollback()
            return
    else:
        print("\nColumn practice_item_id already exists.")
    
    # Verify the column exists now
    cursor.execute("PRAGMA table_info(practice_attempts)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nUpdated columns in practice_attempts: {columns}")
    
    # Check if we need to add any other missing columns from the model
    expected_columns = {
        'id', 'user_id', 'practice_item_id', 'task_id', 
        'answer', 'time_spent_seconds', 'score', 'feedback', 'created_at'
    }
    missing_columns = expected_columns - set(columns)
    
    if missing_columns:
        print(f"\nMissing columns: {missing_columns}")
        print("You may need to recreate the table or add these columns manually.")
    else:
        print("\nAll expected columns are present!")
    
    conn.close()

if __name__ == "__main__":
    fix_practice_attempts_table()

