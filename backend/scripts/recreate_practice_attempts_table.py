"""
Recreate practice_attempts table with correct schema.
This will drop the existing table and create a new one with the correct columns.
WARNING: This will delete all existing practice attempts!
"""
import sys
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Get database path
DB_PATH = PROJECT_ROOT / "irc_coach.db"

def recreate_practice_attempts_table():
    """Recreate practice_attempts table with correct schema."""
    if not DB_PATH.exists():
        print(f"Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check current structure
    cursor.execute("PRAGMA table_info(practice_attempts)")
    current_columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {current_columns}")
    
    # Expected columns for PracticeAttempt
    expected_columns = {
        'id', 'user_id', 'practice_item_id', 'task_id', 
        'answer', 'time_spent_seconds', 'score', 'feedback', 'created_at'
    }
    
    if set(current_columns) == expected_columns:
        print("\nTable structure is already correct!")
        conn.close()
        return
    
    print("\nWARNING: Table structure is incorrect!")
    print("Current columns don't match expected schema.")
    print("\nDropping and recreating practice_attempts table...")
    
    # Drop the table
    cursor.execute("DROP TABLE IF EXISTS practice_attempts")
    
    # Create the table with correct schema
    cursor.execute("""
        CREATE TABLE practice_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            practice_item_id INTEGER NOT NULL,
            task_id INTEGER,
            answer TEXT NOT NULL,
            time_spent_seconds INTEGER,
            score REAL,
            feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (practice_item_id) REFERENCES practice_items(id),
            FOREIGN KEY (task_id) REFERENCES daily_tasks(id)
        )
    """)
    
    # Create index
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_practice_attempts_id ON practice_attempts(id)")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(practice_attempts)")
    new_columns = [row[1] for row in cursor.fetchall()]
    print(f"\nNew columns: {new_columns}")
    print("\nTable recreated successfully!")
    
    conn.close()

if __name__ == "__main__":
    recreate_practice_attempts_table()

