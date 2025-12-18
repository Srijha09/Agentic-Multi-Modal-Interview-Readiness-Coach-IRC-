import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import SessionLocal
from app.db.models import User

def create_test_user():
    db = SessionLocal()
    try:
        user = User(
            email="test@example.com",
            name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user with ID: {user.id}")
        print(f"Email: {user.email}")
        return user.id
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()