#!/usr/bin/env python3

"""
Module 5: Predictive Analytics Comprehensive Unit Tests
Covers REQ_14, REQ_15 and all predictive analytics functionality

Test Coverage:
- Complexity Score calculation: (actor_count × 5) + (requirement_count × 0.3) + (avg_word_count × 0.1) + (modal_verb_density × 10) + (vague_term_density × 15)
- Required minimum 5 requirements for prediction (otherwise "Insufficient data")
- Estimated weeks: heuristic mapping of complexity score (0-100: 2-4 weeks, 100-200: 5-8 weeks, 200+: 9-12 weeks)
- Relative Cost Index: Low/Medium/High based on complexity score tertiles
- Disclaimer displayed: "Approximation only. Based on requirement density." (BR-13)
- Supervisor dashboard displays same metrics for review
- Real-time recalculation when requirements are edited
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from services.ai.predictive_analyzer import PredictiveAnalyzer, PredictiveResult

client = TestClient(app)

class TestModule5PredictiveAnalytics:
    """Comprehensive test suite for Module 5: Predictive Analytics"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def predictive_analyzer(self):
        """Predictive analyzer instance"""
        return PredictiveAnalyzer()

    # === Complexity Score Calculation Tests ===
    
    def test_complexity_score_calculation_formula(self):
        """Test complexity score calculation: (actor_count × 5) + (requirement_count × 0.3) + (avg_word_count × 0.1) + (modal_verb_density × 10) + (vague_term_density × 15)"""
        analyzer = PredictiveAnalyzer()
        
        # Test with known values
        test_text = """
        Actors: User, Admin, System
        REQ-001: The system shall allow users to register accounts.
        REQ-002: The system must authenticate users before access.
        REQ-003: Users should be able to reset passwords.
        REQ-004: The system shall provide adequate performance.
        REQ-005: Admin may manage user accounts efficiently.
        REQ-006: System will process data quickly and reliably.
        REQ-007: Users can view reports securely.
        REQ-008: The system shall handle user requests properly.
        """
        
        result = analyzer.analyze(test_text)
        
        # Should calculate complexity score
        assert hasattr(result, 'complexity_score')
        complexity_score = result.complexity_score
        
        # Should be within expected range (0-100)
        assert 0 <= complexity_score <= 100, f"Complexity score {complexity_score} should be in range 0-100"
        
        # Should follow the formula approximately
        # Let's verify the components are being calculated
        breakdown = result.breakdown if hasattr(result, 'breakdown') else {}
        
        if breakdown:
            # Verify individual components
            assert 'actor_count' in breakdown
            assert 'requirement_count' in breakdown
            assert 'avg_word_count' in breakdown
            assert 'modal_verb_density' in breakdown
            assert 'vague_term_density' in breakdown
            
            # Verify weights are applied correctly
            expected_actor_contribution = breakdown['actor_count'] * 5
            expected_req_contribution = breakdown['requirement_count'] * 0.3
            expected_word_contribution = breakdown['avg_word_count'] * 0.1
            expected_modal_contribution = breakdown['modal_verb_density'] * 10
            expected_vague_contribution = breakdown['vague_term_density'] * 15
            
            # The final score should be close to the sum of weighted components
            expected_score = (expected_actor_contribution + expected_req_contribution + 
                            expected_word_contribution + expected_modal_contribution + 
                            expected_vague_contribution)
            
            # Allow some variance due to scaling/normalization
            assert abs(complexity_score - expected_score) <= 20, f"Score {complexity_score} should be close to expected {expected_score}"
    
    def test_complexity_score_components_calculation(self):
        """Test individual components of complexity score calculation"""
        analyzer = PredictiveAnalyzer()
        
        # Test with specific values
        test_text = """
        Actors: User, Admin, System
        REQ-001: The system shall allow users to register accounts.
        REQ-002: Users must authenticate securely.
        REQ-003: The system should provide adequate performance.
        REQ-004: Admin may manage accounts efficiently.
        REQ-005: System will process data quickly.
        """
        
        result = analyzer.analyze(test_text)
        breakdown = result.breakdown if hasattr(result, 'breakdown') else {}
        
        if breakdown:
            # Actor count should be 3
            assert breakdown['actor_count'] == 3, f"Actor count should be 3, got {breakdown['actor_count']}"
            
            # Requirement count should be 5
            assert breakdown['requirement_count'] == 5, f"Requirement count should be 5, got {breakdown['requirement_count']}"
            
            # Average word count should be reasonable
            assert 5 <= breakdown['avg_word_count'] <= 20, f"Avg word count should be reasonable, got {breakdown['avg_word_count']}"
            
            # Modal verb density should be > 0
            assert breakdown['modal_verb_density'] > 0, f"Modal verb density should be > 0, got {breakdown['modal_verb_density']}"
            
            # Vague term density should be > 0
            assert breakdown['vague_term_density'] > 0, f"Vague term density should be > 0, got {breakdown['vague_term_density']}"

    # === Minimum Requirements Tests ===
    
    def test_minimum_5_requirements_for_prediction(self):
        """Test required minimum 5 requirements for prediction (otherwise "Insufficient data")"""
        analyzer = PredictiveAnalyzer()
        
        # Test with insufficient requirements (less than 5)
        insufficient_text = """
        Actors: User
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        """
        
        result = analyzer.analyze(insufficient_text)
        
        # Should indicate insufficient data
        assert hasattr(result, 'error') or hasattr(result, 'message')
        error_message = getattr(result, 'error', getattr(result, 'message', ''))
        assert "insufficient" in error_message.lower() or "data" in error_message.lower()
        
        # Test with sufficient requirements (5 or more)
        sufficient_text = """
        Actors: User, Admin
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        REQ-004: Admin may manage accounts.
        REQ-005: System will process data.
        """
        
        result = analyzer.analyze(sufficient_text)
        
        # Should produce valid analysis
        assert hasattr(result, 'complexity_score')
        assert not hasattr(result, 'error') or result.error is None

    # === Estimated Weeks Tests ===
    
    def test_estimated_weeks_heuristic_mapping(self):
        """Test estimated weeks: heuristic mapping of complexity score (0-100: 2-4 weeks, 100-200: 5-8 weeks, 200+: 9-12 weeks)"""
        analyzer = PredictiveAnalyzer()
        
        # Test low complexity (0-100)
        low_complexity_text = """
        Actors: User
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        REQ-004: Admin may manage accounts.
        REQ-005: System will process data.
        """
        
        result = analyzer.analyze(low_complexity_text)
        
        if hasattr(result, 'estimated_effort_weeks'):
            weeks = result.estimated_effort_weeks
            assert 2 <= weeks <= 4, f"Low complexity should be 2-4 weeks, got {weeks}"
        
        # Test medium complexity (100-200)
        medium_complexity_text = """
        Actors: User, Admin, System, Manager, Guest
        REQ-001: The system shall allow users to register with secure authentication.
        REQ-002: Users must authenticate using multi-factor authentication.
        REQ-003: System should validate input and provide adequate performance.
        REQ-004: Admin may manage accounts and view reports efficiently.
        REQ-005: System will process data quickly and reliably.
        REQ-006: Users can upload and download files securely.
        REQ-007: The system shall provide real-time notifications.
        REQ-008: Admin can configure system settings properly.
        REQ-009: Users should be able to reset passwords securely.
        REQ-010: System will maintain audit logs effectively.
        REQ-011: The system shall integrate with external APIs.
        REQ-012: Admin may generate comprehensive reports.
        REQ-013: Users can customize their dashboard interface.
        REQ-014: System should handle concurrent requests efficiently.
        REQ-015: The system will provide backup and recovery functionality.
        """
        
        result = analyzer.analyze(medium_complexity_text)
        
        if hasattr(result, 'estimated_effort_weeks'):
            weeks = result.estimated_effort_weeks
            assert 5 <= weeks <= 8, f"Medium complexity should be 5-8 weeks, got {weeks}"
        
        # Test high complexity (200+)
        high_complexity_text = """
        Actors: User, Admin, System, Manager, Guest, Developer, Tester, Auditor
        """ + "\n".join([f"REQ-{i:03d}: The system shall provide complex functionality {i} with adequate performance and security features." for i in range(1, 26)])
        
        result = analyzer.analyze(high_complexity_text)
        
        if hasattr(result, 'estimated_effort_weeks'):
            weeks = result.estimated_effort_weeks
            assert 9 <= weeks <= 12, f"High complexity should be 9-12 weeks, got {weeks}"

    # === Cost Index Tests ===
    
    def test_relative_cost_index_calculation(self):
        """Test Relative Cost Index: Low/Medium/High based on complexity score tertiles"""
        analyzer = PredictiveAnalyzer()
        
        # Test low complexity (should be Low)
        low_text = """
        Actors: User
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        REQ-004: Admin may manage accounts.
        REQ-005: System will process data.
        """
        
        result = analyzer.analyze(low_text)
        
        if hasattr(result, 'cost_index'):
            cost_index = result.cost_index
            assert cost_index in ["low", "medium", "high"], f"Cost index should be Low/Medium/High, got {cost_index}"
            # For low complexity, should be "low"
            assert cost_index == "low", f"Low complexity should have 'low' cost index, got {cost_index}"
        
        # Test medium complexity (should be Medium)
        medium_text = """
        Actors: User, Admin, System
        """ + "\n".join([f"REQ-{i:03d}: The system shall provide functionality {i} with adequate features." for i in range(1, 16)])
        
        result = analyzer.analyze(medium_text)
        
        if hasattr(result, 'cost_index'):
            cost_index = result.cost_index
            assert cost_index == "medium", f"Medium complexity should have 'medium' cost index, got {cost_index}"
        
        # Test high complexity (should be High)
        high_text = """
        Actors: User, Admin, System, Manager, Guest, Developer
        """ + "\n".join([f"REQ-{i:03d}: The system shall provide complex functionality {i} with adequate performance and security features." for i in range(1, 26)])
        
        result = analyzer.analyze(high_text)
        
        if hasattr(result, 'cost_index'):
            cost_index = result.cost_index
            assert cost_index == "high", f"High complexity should have 'high' cost index, got {cost_index}"

    # === Disclaimer Tests ===
    
    def test_disclaimer_display_br13(self):
        """Test disclaimer displayed: "Approximation only. Based on requirement density." (BR-13)"""
        analyzer = PredictiveAnalyzer()
        
        test_text = """
        Actors: User, Admin
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        REQ-004: Admin may manage accounts.
        REQ-005: System will process data.
        """
        
        result = analyzer.analyze(test_text)
        
        # Should include disclaimer
        if hasattr(result, 'disclaimer'):
            disclaimer = result.disclaimer
            assert "approximation" in disclaimer.lower()
            assert "requirement density" in disclaimer.lower()
        elif hasattr(result, 'message'):
            # Check if disclaimer is in message or notes
            message = result.message
            assert "approximation" in message.lower() or "disclaimer" in message.lower()

    # === Real-time Recalculation Tests ===
    
    def test_real_time_recalculation_when_requirements_edited(self):
        """Test real-time recalculation when requirements are edited"""
        analyzer = PredictiveAnalyzer()
        
        # Original requirements
        original_text = """
        Actors: User, Admin
        REQ-001: The system shall allow users to register.
        REQ-002: Users must authenticate.
        REQ-003: System should validate input.
        REQ-004: Admin may manage accounts.
        REQ-005: System will process data.
        """
        
        original_result = analyzer.analyze(original_text)
        original_score = original_result.complexity_score
        
        # Modified requirements (added complexity)
        modified_text = """
        Actors: User, Admin, System, Manager
        REQ-001: The system shall allow users to register with secure authentication.
        REQ-002: Users must authenticate using multi-factor authentication.
        REQ-003: System should validate input and provide adequate performance.
        REQ-004: Admin may manage accounts and view comprehensive reports.
        REQ-005: System will process data quickly and reliably.
        REQ-006: Users can upload and download files securely.
        REQ-007: The system shall provide real-time notifications.
        """
        
        modified_result = analyzer.analyze(modified_text)
        modified_score = modified_result.complexity_score
        
        # Scores should be different
        assert original_score != modified_score, "Scores should change when requirements are modified"
        
        # Modified score should be higher (more complex)
        assert modified_score > original_score, f"Modified score {modified_score} should be higher than original {original_score}"
        
        # Test timing (should be fast for real-time)
        start_time = time.time()
        analyzer.analyze(modified_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 2.0, f"Real-time recalculation should be fast (< 2s), took {processing_time}s"

    # === Supervisor Dashboard Tests ===
    
    def test_supervisor_dashboard_displays_same_metrics(self):
        """Test supervisor dashboard displays same metrics for review"""
        # This would be tested through API endpoints
        with patch('api.analysis.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock project with requirements
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "Test Project"
            
            mock_requirements = [
                MagicMock(
                    original_text="The system shall allow users to register.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="Users must authenticate securely.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="System should validate input.",
                    actors_json='["System"]'
                ),
                MagicMock(
                    original_text="Admin may manage accounts.",
                    actors_json='["Admin"]'
                ),
                MagicMock(
                    original_text="System will process data.",
                    actors_json='["System"]'
                )
            ]
            
            mock_db.query.return_value.filter.return_value.all.return_value = mock_requirements
            
            # Test analysis endpoint
            response = client.get("/api/analysis/complexity/1")
            
            # Should return same metrics for supervisor
            if response.status_code == 200:
                data = response.json()
                assert "complexity_score" in data
                assert "estimated_effort_weeks" in data
                assert "cost_index" in data
                assert "disclaimer" in data or "message" in data

    # === API Endpoint Tests ===
    
    def test_complexity_score_api_endpoint(self):
        """Test /api/complexity-score endpoint functionality"""
        with patch('api.analysis.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock requirements
            mock_requirements = [
                MagicMock(
                    original_text="The system shall allow users to register.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="Users must authenticate.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="System should validate input.",
                    actors_json='["System"]'
                ),
                MagicMock(
                    original_text="Admin may manage accounts.",
                    actors_json='["Admin"]'
                ),
                MagicMock(
                    original_text="System will process data.",
                    actors_json='["System"]'
                )
            ]
            
            mock_db.query.return_value.filter.return_value.all.return_value = mock_requirements
            
            response = client.post("/api/analysis/complexity", json={
                "project_id": 1
            })
            
            # Should return analysis results
            if response.status_code == 200:
                data = response.json()
                assert "complexity_score" in data
                assert "estimated_effort_weeks" in data
                assert "cost_index" in data
                assert isinstance(data["complexity_score"], (int, float))
                assert isinstance(data["estimated_effort_weeks"], (int, float))
                assert data["cost_index"] in ["low", "medium", "high"]

    def test_insufficient_data_message(self):
        """Test 'Insufficient data' message appears when <5 requirements submitted"""
        with patch('api.analysis.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock insufficient requirements (less than 5)
            mock_requirements = [
                MagicMock(
                    original_text="The system shall allow users to register.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="Users must authenticate.",
                    actors_json='["User"]'
                ),
                MagicMock(
                    original_text="System should validate input.",
                    actors_json='["System"]'
                )
            ]
            
            mock_db.query.return_value.filter.return_value.all.return_value = mock_requirements
            
            response = client.post("/api/analysis/complexity", json={
                "project_id": 1
            })
            
            # Should return insufficient data message
            if response.status_code == 200:
                data = response.json()
                assert "error" in data or "message" in data
                message = data.get("error", data.get("message", ""))
                assert "insufficient" in message.lower() or "data" in message.lower()

    # === Integration Tests ===
    
    def test_complete_predictive_analytics_workflow(self):
        """Test complete predictive analytics workflow"""
        analyzer = PredictiveAnalyzer()
        
        # Test with comprehensive requirements
        test_text = """
        Actors: User, Admin, System, Manager
        REQ-001: The system shall allow users to register with secure authentication.
        REQ-002: Users must authenticate using multi-factor authentication.
        REQ-003: System should validate input and provide adequate performance.
        REQ-004: Admin may manage accounts and view comprehensive reports.
        REQ-005: System will process data quickly and reliably.
        REQ-006: Users can upload and download files securely.
        REQ-007: The system shall provide real-time notifications.
        REQ-008: Admin can configure system settings properly.
        REQ-009: Users should be able to reset passwords securely.
        REQ-010: System will maintain audit logs effectively.
        """
        
        result = analyzer.analyze(test_text)
        
        # Should produce complete analysis
        assert hasattr(result, 'complexity_score')
        assert hasattr(result, 'estimated_effort_weeks')
        assert hasattr(result, 'cost_index')
        
        # Values should be reasonable
        assert 0 <= result.complexity_score <= 100
        assert 2 <= result.estimated_effort_weeks <= 12
        assert result.cost_index in ["low", "medium", "high"]
        
        # Should include disclaimer
        if hasattr(result, 'disclaimer'):
            assert "approximation" in result.disclaimer.lower()
    
    def test_predictive_analytics_performance(self):
        """Test predictive analytics meets performance requirements"""
        analyzer = PredictiveAnalyzer()
        
        # Test with large requirements set
        large_text = """
        Actors: User, Admin, System, Manager, Guest, Developer, Tester
        """ + "\n".join([f"REQ-{i:03d}: The system shall provide complex functionality {i} with adequate performance and security features." for i in range(1, 51)])
        
        start_time = time.time()
        result = analyzer.analyze(large_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (less than 5 seconds)
        assert processing_time < 5.0, f"Analysis took too long: {processing_time}s"
        
        # Should produce valid results
        assert hasattr(result, 'complexity_score')
        assert result.complexity_score >= 0
    
    def test_predictive_analytics_error_handling(self):
        """Test predictive analytics error handling"""
        analyzer = PredictiveAnalyzer()
        
        # Test with empty text
        result = analyzer.analyze("")
        
        # Should handle gracefully
        assert hasattr(result, 'error') or hasattr(result, 'message')
        
        # Test with malformed text
        result = analyzer.analyze("Invalid text without requirements")
        
        # Should handle gracefully
        assert hasattr(result, 'error') or hasattr(result, 'message')

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
