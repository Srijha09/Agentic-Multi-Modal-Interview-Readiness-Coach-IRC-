"""
Validation script to verify Phase 1 setup is correct.
Run this after setting up the environment to ensure everything works.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_imports():
    """Check that all critical imports work."""
    print("Checking imports...")
    try:
        from app.core.config import settings
        print("✓ Config imported successfully")
        
        from app.db.database import engine, Base, get_db
        print("✓ Database modules imported successfully")
        
        from app.db.models import User, Document, StudyPlan, DailyTask, PracticeAttempt, SkillMastery
        print("✓ Database models imported successfully")
        
        from app.api.v1.router import api_router
        print("✓ API router imported successfully")
        
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def check_database():
    """Check database connection and tables."""
    print("\nChecking database...")
    try:
        from app.db.database import engine, Base
        from app.db.models import User, Document, StudyPlan
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database connection successful")
        print("✓ Tables can be created")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def check_config():
    """Check configuration."""
    print("\nChecking configuration...")
    try:
        from app.core.config import settings
        
        print(f"✓ Environment: {settings.ENVIRONMENT}")
        print(f"✓ Database URL: {settings.DATABASE_URL}")
        print(f"✓ API prefix: {settings.API_V1_PREFIX}")
        print(f"✓ LLM Provider: {settings.LLM_PROVIDER}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 50)
    print("Phase 1 Setup Validation")
    print("=" * 50)
    
    results = []
    results.append(("Imports", check_imports()))
    results.append(("Database", check_database()))
    results.append(("Configuration", check_config()))
    
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("✓ All checks passed! Phase 1 setup is complete.")
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())




