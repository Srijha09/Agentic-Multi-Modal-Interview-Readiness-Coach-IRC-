"""
Validation script for Phase 4: Skill Extraction & Gap Analysis.

This script validates:
1. Skill extraction service imports correctly
2. Gap analysis service imports correctly
3. API endpoints are registered
4. Schemas are properly defined
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
    """Test that all Phase 4 modules import correctly."""
    print("Testing Phase 4 imports...")
    
    try:
        from app.core.llm import get_llm, get_llm_with_temperature
        print("✓ LLM utilities imported")
    except Exception as e:
        print(f"✗ Failed to import LLM utilities: {e}")
        return False
    
    try:
        from app.services.skill_extraction import SkillExtractor, ExtractedSkill, SkillExtractionResult
        print("✓ Skill extraction service imported")
    except Exception as e:
        print(f"✗ Failed to import skill extraction: {e}")
        return False
    
    try:
        from app.services.gap_analysis import GapAnalyzer
        print("✓ Gap analysis service imported")
    except Exception as e:
        print(f"✗ Failed to import gap analysis: {e}")
        return False
    
    try:
        from app.api.v1.endpoints.gaps import router
        print("✓ Gap analysis API endpoints imported")
    except Exception as e:
        print(f"✗ Failed to import gap endpoints: {e}")
        return False
    
    try:
        from app.schemas.skill import (
            CoverageStatus,
            GapPriority,
            GapResponse,
            GapReportResponse,
            SkillEvidenceResponse,
        )
        print("✓ Gap analysis schemas imported")
    except Exception as e:
        print(f"✗ Failed to import gap schemas: {e}")
        return False
    
    return True


def test_router_registration():
    """Test that gap endpoints are registered in the main router."""
    print("\nTesting router registration...")
    
    try:
        from app.api.v1.router import api_router
        
        # Check if gaps router is included
        routes = [route.path for route in api_router.routes]
        gap_routes = [r for r in routes if "/gaps" in r]
        
        if gap_routes:
            print(f"✓ Gap endpoints registered: {gap_routes}")
            return True
        else:
            print("✗ Gap endpoints not found in router")
            return False
    except Exception as e:
        print(f"✗ Failed to check router: {e}")
        return False


def test_schemas():
    """Test that schemas are properly defined."""
    print("\nTesting schemas...")
    
    try:
        from app.schemas.skill import CoverageStatus, GapPriority
        
        # Test enum values
        assert CoverageStatus.COVERED.value == "covered"
        assert CoverageStatus.PARTIAL.value == "partial"
        assert CoverageStatus.MISSING.value == "missing"
        print("✓ CoverageStatus enum valid")
        
        assert GapPriority.CRITICAL.value == "critical"
        assert GapPriority.HIGH.value == "high"
        assert GapPriority.MEDIUM.value == "medium"
        assert GapPriority.LOW.value == "low"
        print("✓ GapPriority enum valid")
        
        return True
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 4 Validation: Skill Extraction & Gap Analysis")
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
        print("\n✓ Phase 4 validation PASSED")
        return 0
    else:
        print("\n✗ Phase 4 validation FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())


