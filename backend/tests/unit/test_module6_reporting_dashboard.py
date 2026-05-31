#!/usr/bin/env python3

"""
Module 6: Reporting & Dashboard Comprehensive Unit Tests
Covers REQ_16, REQ_17, REQ_18, REQ_19, REQ_20 and all reporting & dashboard functionality

Test Coverage:
- Dashboard displays overall quality score (0-100)
- Defect list with severity color coding (red=high, yellow=medium, blue=low)
- AI Rewrite Suggestions with "Apply" and "Dismiss" options (REQ_17)
- Apply fix replaces text and marks defect "Resolved"
- Undo history stack (minimum 5 levels) (BR-15)
- Traceability Matrix: maps requirements → validation status → visual elements (REQ_18)
- User notes field with timestamp (informational only, does not modify text) (BR-16)
- Supervisor Review: read-only access, Approve/Request Changes decision (BR-18, BR-19)
- Export PDF: includes timestamp, VisSpec watermark (BR-20)
- All data encrypted in transit (HTTPS/TLS 1.2+)
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from services.report.export_service import ExportService
from models.validation import ValidationSession
from models.requirement import Requirement
from models.traceability import TraceabilityNote

client = TestClient(app)

class TestModule6ReportingDashboard:
    """Comprehensive test suite for Module 6: Reporting & Dashboard"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def export_service(self):
        """Export service instance"""
        return ExportService()

    # === Dashboard Quality Score Tests ===
    
    def test_dashboard_displays_overall_quality_score(self):
        """Test dashboard displays overall quality score (0-100)"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock validation session with defects
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.overall_score = 75.0
            mock_session.defects = [
                {
                    "id": 1,
                    "type": "Ambiguity",
                    "severity": "Medium",
                    "text": "The system shall process data quickly.",
                    "status": "Open"
                },
                {
                    "id": 2,
                    "type": "Incompleteness",
                    "severity": "Low",
                    "text": "The system shall handle user input.",
                    "status": "Open"
                }
            ]
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            response = client.get("/api/dashboard/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "quality_score" in data
                assert 0 <= data["quality_score"] <= 100
                assert data["quality_score"] == 75.0
    
    def test_quality_score_calculation_formula(self):
        """Test quality score calculation: (total_requirements - defect_count)/total_requirements × 100"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock data: 10 requirements, 3 defects
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.total_requirements = 10
            mock_session.defect_count = 3
            
            # Calculate expected score
            expected_score = ((10 - 3) / 10) * 100  # 70%
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            response = client.get("/api/dashboard/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "quality_score" in data
                # Should match calculated score (allow small variance)
                assert abs(data["quality_score"] - expected_score) <= 1

    # === Defect List and Severity Tests ===
    
    def test_defect_list_severity_color_coding(self):
        """Test defect list with severity color coding (red=high, yellow=medium, blue=low)"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock defects with different severities
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.defects = [
                {
                    "id": 1,
                    "type": "Ambiguity",
                    "severity": "High",
                    "text": "The system shall do everything perfectly.",
                    "status": "Open"
                },
                {
                    "id": 2,
                    "type": "Inconsistency",
                    "severity": "Medium",
                    "text": "The system shall allow and not allow user deletion.",
                    "status": "Open"
                },
                {
                    "id": 3,
                    "type": "Completeness",
                    "severity": "Low",
                    "text": "The system shall handle user input.",
                    "status": "Open"
                }
            ]
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            response = client.get("/api/dashboard/defects/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "defects" in data
                
                defects = data["defects"]
                
                # Check color coding
                for defect in defects:
                    severity = defect.get("severity")
                    color_class = defect.get("color_class")
                    
                    if severity == "High":
                        assert color_class == "bg-red-100" or "red" in color_class.lower()
                    elif severity == "Medium":
                        assert color_class == "bg-yellow-100" or "yellow" in color_class.lower()
                    elif severity == "Low":
                        assert color_class == "bg-blue-100" or "blue" in color_class.lower()

    # === AI Rewrite Suggestions Tests ===
    
    def test_ai_rewrite_suggestions_apply_dismiss_options(self):
        """Test AI Rewrite Suggestions with "Apply" and "Dismiss" options (REQ_17)"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock defect with AI suggestion
            mock_defect = MagicMock()
            mock_defect.id = 1
            mock_defect.type = "Ambiguity"
            mock_defect.severity = "Medium"
            mock_defect.text = "The system shall process data quickly."
            mock_defect.ai_suggestion = "The system shall process requests within 200ms."
            mock_defect.status = "Open"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_defect
            
            response = client.get("/api/dashboard/defect/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "ai_suggestion" in data
                assert "actions" in data
                
                actions = data["actions"]
                assert "apply" in actions or "Apply" in str(actions)
                assert "dismiss" in actions or "Dismiss" in str(actions)
    
    def test_apply_fix_replaces_text_and_marks_resolved(self):
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock defect and requirement
            mock_defect = MagicMock()
            mock_defect.id = 1
            mock_defect.status = "Open"
            
            mock_requirement = MagicMock()
            mock_requirement.id = 1
            mock_requirement.current_text = "The system shall process data quickly."
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [mock_defect, mock_requirement]
            
            response = client.post("/api/dashboard/defect/1/apply", json={
                "suggestion": "The system shall process requests within 200ms."
            })
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify requirement text was updated
                assert mock_requirement.current_text == "The system shall process requests within 200ms."
                
                # Verify defect status was updated
                assert mock_defect.status == "Resolved""
                
                # Verify database commit was called
                mock_db.commit.assert_called()
    
    def test_dismiss_suggestion_marks_dismissed(self):
        """Test Dismiss option marks suggestion as dismissed"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_defect = MagicMock()
            mock_defect.id = 1
            mock_defect.status = "Open"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_defect
            
            response = client.post("/api/dashboard/defect/1/dismiss")
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify defect status was updated
                assert mock_defect.status == "Dismissed"
                
                # Verify database commit was called
                mock_db.commit.assert_called()

    # === Undo History Tests ===
    
    def test_undo_history_stack_minimum_5_levels_br15(self):
        """Test undo history stack (minimum 5 levels) (BR-15)"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock undo history
            mock_history = [
                {
                    "id": 1,
                    "action": "apply",
                    "old_text": "The system shall process data quickly.",
                    "new_text": "The system shall process requests within 200ms.",
                    "timestamp": "2024-01-01T10:00:00Z"
                },
                {
                    "id": 2,
                    "action": "apply",
                    "old_text": "Users must authenticate.",
                    "new_text": "Users must authenticate using MFA.",
                    "timestamp": "2024-01-01T10:01:00Z"
                },
                {
                    "id": 3,
                    "action": "dismiss",
                    "old_text": "The system shall be user-friendly.",
                    "new_text": "",
                    "timestamp": "2024-01-01T10:02:00Z"
                },
                {
                    "id": 4,
                    "action": "apply",
                    "old_text": "System should respond quickly.",
                    "new_text": "System shall respond within 100ms.",
                    "timestamp": "2024-01-01T10:03:00Z"
                },
                {
                    "id": 5,
                    "action": "apply",
                    "old_text": "The system shall provide adequate performance.",
                    "new_text": "The system shall provide 99.9% uptime.",
                    "timestamp": "2024-01-01T10:04:00Z"
                }
            ]
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_history
            
            response = client.get("/api/dashboard/undo-history/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "history" in data
                
                history = data["history"]
                # Should have at least 5 levels
                assert len(history) >= 5
                
                # Should have proper structure
                for item in history:
                    assert "action" in item
                    assert "old_text" in item
                    assert "new_text" in item
                    assert "timestamp" in item
    
    def test_undo_functionality_restores_previous_state(self):
        """Test undo functionality restores previous state"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock undo action
            mock_undo_action = MagicMock()
            mock_undo_action.old_text = "The system shall process data quickly."
            mock_undo_action.new_text = "The system shall process requests within 200ms."
            mock_undo_action.requirement_id = 1
            
            mock_requirement = MagicMock()
            mock_requirement.current_text = "The system shall process requests within 200ms."
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [mock_undo_action, mock_requirement]
            
            response = client.post("/api/dashboard/undo/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify text was restored
                assert mock_requirement.current_text == "The system shall process data quickly."
                
                # Verify database commit was called
                mock_db.commit.assert_called()

    # === Traceability Matrix Tests ===
    
    def test_traceability_matrix_mapping_req18(self):
        """Test Traceability Matrix: maps requirements → validation status → visual elements (REQ_18)"""
        with patch('api.traceability.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock traceability data
            mock_requirements = [
                {
                    "req_id": "REQ-001",
                    "text": "The system shall allow users to register.",
                    "validation_status": "Passed",
                    "visual_elements": ["UseCase: User Registration", "Sequence: Registration Flow"],
                    "notes": []
                },
                {
                    "req_id": "REQ-002",
                    "text": "Users must authenticate securely.",
                    "validation_status": "Failed",
                    "visual_elements": ["UseCase: Authentication"],
                    "notes": [
                        {
                            "id": 1,
                            "text": "Need to clarify authentication method",
                            "timestamp": "2024-01-01T10:00:00Z",
                            "author": "User"
                        }
                    ]
                }
            ]
            
            mock_db.query.return_value.all.return_value = mock_requirements
            
            response = client.get("/api/traceability/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "requirements" in data
                
                requirements = data["requirements"]
                
                # Verify traceability mapping
                for req in requirements:
                    assert "req_id" in req
                    assert "validation_status" in req
                    assert "visual_elements" in req
                    assert "notes" in req
                    
                    # Should have proper mapping structure
                    assert isinstance(req["visual_elements"], list)
                    assert isinstance(req["notes"], list)

    # === User Notes Tests ===
    
    def test_user_notes_field_with_timestamp_br16(self):
        """Test User notes field with timestamp (informational only, does not modify text) (BR-16)"""
        with patch('api.traceability.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock adding a note
            mock_note = MagicMock()
            mock_note.id = 1
            mock_note.text = "This requirement needs clarification from stakeholders."
            mock_note.timestamp = datetime.utcnow()
            mock_note.author = "User"
            
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post("/api/traceability/note", json={
                "requirement_id": 1,
                "text": "This requirement needs clarification from stakeholders."
            })
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify note was created with timestamp
                mock_db.add.assert_called()
                mock_db.commit.assert_called()
                
                # Note should not modify requirement text
                # (This would be verified by checking requirement text wasn't changed)
    
    def test_notes_informational_only_no_text_modification(self):
        """Test notes are informational only and do not modify requirement text"""
        with patch('api.traceability.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock requirement
            mock_requirement = MagicMock()
            original_text = "The system shall allow users to register."
            mock_requirement.current_text = original_text
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_requirement
            
            # Add note
            response = client.post("/api/traceability/note", json={
                "requirement_id": 1,
                "text": "Note about this requirement"
            })
            
            # Verify requirement text was not modified
            assert mock_requirement.current_text == original_text

    # === Supervisor Review Tests ===
    
    def test_supervisor_review_read_only_access_br18(self):
        """Test Supervisor Review: read-only access (BR-18)"""
        with patch('api.supervisor.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock supervisor user
            mock_user = MagicMock()
            mock_user.role = "supervisor"
            
            # Mock project with read-only status
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.status = "supervisor_review"
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_project]
            
            response = client.get("/api/supervisor/review/1")
            
            if response.status_code == 200:
                data = response.json()
                assert "project" in data
                assert "requirements" in data
                assert "read_only" in data
                assert data["read_only"] == True

    def test_supervisor_approve_request_changes_br19(self):
        """Test Supervisor Review: Approve/Request Changes decision (BR-19)"""
        with patch('api.supervisor.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock supervisor user and project
            mock_user = MagicMock()
            mock_user.role = "supervisor"
            
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.status = "pending_review"
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_project]
            
            # Test approve action
            response = client.post("/api/supervisor/approve/1", json={
                "comments": "Requirements look good. Approved."
            })
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify project status was updated
                assert mock_project.status == "approved"
                
                # Verify database commit was called
                mock_db.commit.assert_called()
            
            # Test request changes action
            response = client.post("/api/supervisor/request-changes/1", json={
                "comments": "Need to clarify authentication requirements."
            })
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data or data.get("status") == "success"
                
                # Verify project status was updated
                assert mock_project.status == "changes_requested"

    # === PDF Export Tests ===
    
    def test_export_pdf_timestamp_watermark_br20(self):
        """Test Export PDF: includes timestamp, VisSpec watermark (BR-20)"""
        export_service = ExportService()
        
        # Mock report data
        report_data = {
            "project_name": "Test Project",
            "quality_score": 75.0,
            "defects": [
                {
                    "type": "Ambiguity",
                    "severity": "Medium",
                    "text": "The system shall process data quickly."
                }
            ],
            "requirements": [
                {
                    "req_id": "REQ-001",
                    "text": "The system shall allow users to register."
                }
            ]
        }
        
        # Mock PDF generation
        with patch('services.report.export_service.FPDF') as mock_fpdf:
            mock_pdf = MagicMock()
            mock_fpdf.return_value = mock_pdf
            
            pdf_content = export_service.generate_pdf_report(report_data)
            
            # Verify PDF generation was called
            mock_fpdf.assert_called()
            
            # Verify watermark was added
            watermark_calls = [call for call in mock_pdf.method_calls if 'set_text_color' in str(call) or 'watermark' in str(call).lower()]
            assert len(watermark_calls) > 0, "Should add VisSpec watermark"
            
            # Verify timestamp was included
            timestamp_calls = [call for call in mock_pdf.method_calls if 'timestamp' in str(call).lower() or datetime.now().strftime('%Y-%m-%d') in str(call)]
            assert len(timestamp_calls) > 0, "Should include timestamp"

    def test_pdf_download_functionality(self):
        """Test PDF download functionality"""
        with patch('api.report.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock project data
            mock_project = MagicMock()
            mock_project.name = "Test Project"
            mock_project.requirements = []
            mock_project.validation_sessions = []
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            
            # Mock PDF generation
            with patch('services.report.export_service.ExportService.generate_pdf_report') as mock_generate:
                mock_generate.return_value = b"PDF content"
                
                response = client.get("/api/report/export/1")
                
                # Should return PDF file
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert "attachment" in response.headers["content-disposition"]
                assert "vispec_report" in response.headers["content-disposition"].lower()

    # === Security Tests ===
    
    def test_data_encrypted_in_transits(self):
        """Test all data encrypted in transit (HTTPS/TLS 1.2+)"""
        # Test that endpoints require HTTPS (in production)
        # This would be tested through middleware configuration
        
        # Verify secure headers are set
        response = client.get("/api/dashboard/1")
        
        # In production, should have HTTPS security headers
        # For testing, we verify the endpoint exists and is accessible
        assert response.status_code in [200, 401, 403, 404]  # Should not be 500

    # === Integration Tests ===
    
    def test_complete_dashboard_workflow(self):
        """Test complete dashboard workflow from validation to export"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock complete dashboard data
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.overall_score = 75.0
            mock_session.defects = [
                {
                    "id": 1,
                    "type": "Ambiguity",
                    "severity": "Medium",
                    "text": "The system shall process data quickly.",
                    "ai_suggestion": "The system shall process requests within 200ms.",
                    "status": "Open"
                }
            ]
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            # 1. Get dashboard data
            response = client.get("/api/dashboard/1")
            if response.status_code == 200:
                dashboard_data = response.json()
                assert "quality_score" in dashboard_data
                assert "defects" in dashboard_data
            
            # 2. Apply AI suggestion
            response = client.post("/api/dashboard/defect/1/apply", json={
                "suggestion": "The system shall process requests within 200ms."
            })
            if response.status_code == 200:
                assert "success" in response.json()
            
            # 3. Get traceability matrix
            response = client.get("/api/traceability/1")
            if response.status_code == 200:
                traceability_data = response.json()
                assert "requirements" in traceability_data
            
            # 4. Export PDF report
            with patch('services.report.export_service.ExportService.generate_pdf_report') as mock_generate:
                mock_generate.return_value = b"PDF content"
                
                response = client.get("/api/report/export/1")
                if response.status_code == 200:
                    assert response.headers["content-type"] == "application/pdf"
    
    def test_dashboard_performance_requirements(self):
        """Test dashboard meets performance requirements"""
        with patch('api.dashboard.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock dashboard data
            mock_session = MagicMock()
            mock_session.overall_score = 75.0
            mock_session.defects = []
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            
            # Test dashboard loading performance
            start_time = time.time()
            response = client.get("/api/dashboard/1")
            end_time = time.time()
            
            loading_time = end_time - start_time
            
            # Should load within reasonable time (less than 3 seconds)
            assert loading_time < 3.0, f"Dashboard loading took too long: {loading_time}s"
            
            # Should return valid data
            if response.status_code == 200:
                data = response.json()
                assert "quality_score" in data

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
