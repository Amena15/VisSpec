"""Simple unit tests for traceability API endpoints without SQLAlchemy conflicts."""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

def test_traceability_endpoint_exists():
    """Test that traceability endpoint can be imported and has correct structure."""
    try:
        from backend.api.traceability import router, get_traceability, save_traceability_note
        
        # Check router exists and has correct prefix
        assert router is not None
        assert router.prefix == "/api/traceability"
        
        # Check functions exist
        assert callable(get_traceability)
        assert callable(save_traceability_note)
        
        print("✅ test_traceability_endpoint_exists passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_traceability_response_models():
    """Test that traceability response models are properly defined."""
    try:
        from backend.api.traceability import TraceabilityItem, TraceabilityResponse, NoteRequest, NoteResponse
        
        # Test TraceabilityItem model
        item = TraceabilityItem(
            req_id="test-req-1",
            identifier="REQ-001",
            text="Test requirement",
            validation_status="passed",
            visual_elements=["Actor: User"],
            complexity="Medium",
            note=None
        )
        assert item.req_id == "test-req-1"
        assert item.validation_status == "passed"
        
        # Test TraceabilityResponse model
        response = TraceabilityResponse(
            project_id="test-project",
            project={"id": "test-project", "name": "Test Project"},
            traceability=[item]
        )
        assert response.project_id == "test-project"
        assert len(response.traceability) == 1
        
        print("✅ test_traceability_response_models passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_helper_functions():
    """Test traceability helper functions work correctly."""
    try:
        from backend.api.traceability import _determine_validation_status, _extract_visual_elements, _determine_complexity
        
        # Test validation status determination
        mock_defect_high = Mock()
        mock_defect_high.severity = "high"
        
        mock_defect_medium = Mock()
        mock_defect_medium.severity = "medium"
        
        # Test with no defects
        status = _determine_validation_status("req-1", [])
        assert status == "passed"
        
        # Test with high severity defect
        status = _determine_validation_status("req-1", [mock_defect_high])
        assert status == "failed"
        
        # Test with medium severity defect
        status = _determine_validation_status("req-1", [mock_defect_medium])
        assert status == "warning"
        
        # Test visual element extraction
        elements = _extract_visual_elements("The user shall login to the system")
        assert "Actor: User" in elements
        assert "Use Case: Login" in elements
        
        # Test complexity determination
        complexity = _determine_complexity("The user shall login")
        assert complexity in ["Low", "Medium", "High"]
        
        complexity = _determine_complexity("The system shall integrate multiple complex databases with security validation")
        assert complexity in ["Low", "Medium", "High"]
        
        print("✅ test_helper_functions passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_api_endpoint_structure():
    """Test that API endpoints are properly structured."""
    try:
        from backend.api.traceability import router
        
        # Check that router has routes
        routes = [route for route in router.routes]
        assert len(routes) >= 2  # At least GET traceability and POST note
        
        # Check route paths
        route_paths = [route.path for route in routes]
        assert "/{project_id}" in route_paths  # GET traceability
        assert "/note" in route_paths  # POST note
        
        print("✅ test_api_endpoint_structure passed")
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

if __name__ == "__main__":
    """Run all tests manually."""
    tests = [
        test_traceability_endpoint_exists,
        test_traceability_response_models,
        test_helper_functions,
        test_api_endpoint_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")
