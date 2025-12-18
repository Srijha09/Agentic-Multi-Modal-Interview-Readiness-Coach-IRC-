"""
Validation script for Phase 5: Planner Agent.

This script validates:
1. Planner service imports correctly
2. API endpoints are registered
3. Schemas are properly defined
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_imports():
    """Test that all Phase 5 modules import correctly."""
    print("Testing Phase 5 imports...")
    
    try:
        from app.services.planner import StudyPlanner
        print("✓ Planner service imported")
    except Exception as e:
        print(f"✗ Failed to import planner service: {e}")
        return False
    
    try:
        from app.api.v1.endpoints.plans import router
        print("✓ Plan API endpoints imported")
    except Exception as e:
        print(f"✗ Failed to import plan endpoints: {e}")
        return False
    
    try:
        from app.schemas.plan import (
            StudyPlanCreate,
            StudyPlanResponse,
            WeekResponse,
            DayResponse,
            TaskResponse,
        )
        print("✓ Plan schemas imported")
    except Exception as e:
        print(f"✗ Failed to import plan schemas: {e}")
        return False
    
    return True


def test_router_registration():
    """Test that plan endpoints are registered in the main router."""
    print("\nTesting router registration...")
    
    try:
        from app.api.v1.router import api_router
        
        # Check if plans router is included
        routes = [route.path for route in api_router.routes]
        plan_routes = [r for r in routes if "/plans" in r]
        
        if plan_routes:
            print(f"✓ Plan endpoints registered: {plan_routes}")
            return True
        else:
            print("✗ Plan endpoints not found in router")
            return False
    except Exception as e:
        print(f"✗ Failed to check router: {e}")
        return False


def test_schemas():
    """Test that schemas are properly defined."""
    print("\nTesting schemas...")
    
    try:
        from app.schemas.plan import TaskType, TaskStatus
        
        # Test enum values
        assert TaskType.LEARN.value == "learn"
        assert TaskType.PRACTICE.value == "practice"
        assert TaskType.REVIEW.value == "review"
        print("✓ TaskType enum valid")
        
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        print("✓ TaskStatus enum valid")
        
        return True
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 5 Validation: Planner Agent")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Router Registration", test_router_registration()))
    results.append(("Schemas", test_schemas()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ Phase 5 validation PASSED")
        return 0
    else:
        print("\n✗ Phase 5 validation FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

