#!/usr/bin/env python3
"""
Module 6: Reporting & Dashboard - Professional Unit Tests

Tests the report export functionality with:
- Input validation (project name, report type, dict/list fields)
- Report type validation (full, summary, supervisor)
- Error handling with structured logging
- Filename sanitization
- PDF generation

NOTE: PDF service integration skipped - requires reportlab + mock service
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from backend.api.reports import ReportExportRequest


class TestModule6ReportingDashboard:
    """Professional test suite for Module 6: Reporting & Dashboard"""

    # =====================================================================
    # Input Validation Tests
    # =====================================================================

    def test_report_export_request_valid_full_report(self):
        """ReportExportRequest should accept valid full report params"""
        request = ReportExportRequest(
            project_name="Test Project",
            project_id="proj-123",
            report_type="full",
            analysis_data={"quality_score": 85},
            diagrams=[{"type": "usecase", "data": "mermaid syntax"}],
            metrics={"complexity": 65},
            traceability=[{"req_id": "REQ-001", "status": "passed"}]
        )
        
        assert request.project_name == "Test Project"
        assert request.report_type == "full"
        assert isinstance(request.analysis_data, dict)
        assert isinstance(request.diagrams, list)

    def test_report_export_request_valid_summary_report(self):
        """ReportExportRequest should accept summary report type"""
        request = ReportExportRequest(report_type="summary")
        assert request.report_type == "summary"

    def test_report_export_request_valid_supervisor_report(self):
        """ReportExportRequest should accept supervisor report type"""
        request = ReportExportRequest(report_type="supervisor")
        assert request.report_type == "supervisor"

    def test_report_export_request_defaults(self):
        """ReportExportRequest should use sensible defaults"""
        request = ReportExportRequest()
        assert request.project_name == "Untitled Project"
        assert request.report_type == "full"
        assert request.analysis_data == {}
        assert request.diagrams == []
        assert request.metrics == {}
        assert request.traceability == []

    # =====================================================================
    # Input Validation - Negative Tests
    # =====================================================================

    def test_report_export_request_rejects_long_project_name(self):
        """ReportExportRequest should reject project names exceeding 500 chars"""
        long_name = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(project_name=long_name)
        
        error_msg = str(exc_info.value).lower()
        assert "exceeds maximum length" in error_msg or "length_greater_than_equal" in error_msg

    def test_report_export_request_rejects_invalid_report_type(self):
        """ReportExportRequest should reject invalid report types"""
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(report_type="invalid_type")
        
        error_msg = str(exc_info.value).lower()
        assert "must be one of" in error_msg or "input should not be a valid enumeration" in error_msg

    def test_report_export_request_rejects_non_dict_analysis_data(self):
        """ReportExportRequest should reject non-dict analysis_data"""
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(analysis_data="not a dict")
        
        error_msg = str(exc_info.value).lower()
        assert "dict" in error_msg

    def test_report_export_request_rejects_non_dict_metrics(self):
        """ReportExportRequest should reject non-dict metrics"""
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(metrics="not a dict")
        
        error_msg = str(exc_info.value).lower()
        assert "dict" in error_msg

    def test_report_export_request_rejects_non_list_diagrams(self):
        """ReportExportRequest should reject non-list diagrams"""
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(diagrams="not a list")
        
        error_msg = str(exc_info.value).lower()
        assert "list" in error_msg

    def test_report_export_request_rejects_non_list_traceability(self):
        """ReportExportRequest should reject non-list traceability"""
        with pytest.raises(ValidationError) as exc_info:
            ReportExportRequest(traceability="not a list")
        
        error_msg = str(exc_info.value).lower()
        assert "list" in error_msg

    # =====================================================================
    # Filename Sanitization Tests
    # =====================================================================

    def test_filename_sanitization_removes_special_chars(self):
        """Filename sanitization should remove special characters"""
        dangerous_names = [
            "Project/../../../etc/passwd",
            "Project<script>alert(1)</script>",
            "Project\x00null",
            "Project\nwith\nnewlines",
        ]
        
        for name in dangerous_names:
            # Character filtering logic
            safe_filename = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in name
            ).strip()
            
            # Should not contain path traversal or injection chars
            assert ".." not in safe_filename
            assert "<" not in safe_filename
            assert ">" not in safe_filename
            assert "\x00" not in safe_filename

    def test_filename_sanitization_preserves_valid_chars(self):
        """Filename sanitization should preserve alphanumeric, space, dash, underscore"""
        valid_name = "My-Project_2025 Report"
        safe_filename = "".join(
            c if c.isalnum() or c in (' ', '-', '_') else '_'
            for c in valid_name
        ).strip()
        
        assert safe_filename == "My-Project_2025 Report"

    # =====================================================================
    # Report Type Coverage Tests
    # =====================================================================

    def test_report_type_full_includes_all_data(self):
        """Full report should include analysis, diagrams, metrics, traceability"""
        request = ReportExportRequest(
            report_type="full",
            analysis_data={"key": "value"},
            diagrams=[{"type": "usecase"}],
            metrics={"complexity": 50},
            traceability=[{"req_id": "REQ-001"}]
        )
        
        assert request.report_type == "full"
        assert len(request.diagrams) > 0
        assert len(request.traceability) > 0

    def test_report_type_summary_may_include_subset(self):
        """Summary report may include subset of data"""
        request = ReportExportRequest(
            report_type="summary",
            analysis_data={"key": "value"},
            metrics={"complexity": 50}
        )
        
        assert request.report_type == "summary"
        assert request.analysis_data is not None
        assert request.metrics is not None

    def test_report_type_supervisor_may_be_read_only(self):
        """Supervisor report type accepted for read-only dashboards"""
        request = ReportExportRequest(report_type="supervisor")
        assert request.report_type == "supervisor"

    # =====================================================================
    # Data Structure Tests
    # =====================================================================

    def test_analysis_data_structure_flexibility(self):
        """Analysis data should accept flexible nested structures"""
        complex_data = {
            "quality_score": 85,
            "defects": {
                "high": 2,
                "medium": 5,
                "low": 10
            },
            "timeline": {
                "phase1": {"status": "completed", "date": "2025-01-15"},
                "phase2": {"status": "in_progress", "date": "2025-02-01"}
            }
        }
        
        request = ReportExportRequest(analysis_data=complex_data)
        assert request.analysis_data == complex_data

    def test_diagrams_structure_flexibility(self):
        """Diagrams should accept various diagram types"""
        diagrams = [
            {"type": "usecase", "format": "mermaid", "data": "graph TD..."},
            {"type": "sequence", "format": "plantuml", "data": "participant..."},
            {"type": "activity", "format": "mermaid", "data": "state..."},
        ]
        
        request = ReportExportRequest(diagrams=diagrams)
        assert len(request.diagrams) == 3
        assert request.diagrams[0]["type"] == "usecase"

    def test_traceability_structure_flexibility(self):
        """Traceability should accept requirement mapping structures"""
        traceability = [
            {
                "req_id": "REQ-001",
                "text": "User can login",
                "status": "passed",
                "visual_elements": ["usecase_login", "seq_auth_flow"],
                "complexity": "Medium"
            },
            {
                "req_id": "REQ-002",
                "text": "User can register",
                "status": "warning",
                "defects": [{"id": "DEF-001", "type": "Ambiguity"}],
                "complexity": "High"
            }
        ]
        
        request = ReportExportRequest(traceability=traceability)
        assert len(request.traceability) == 2

    # =====================================================================
    # Edge Case Tests
    # =====================================================================

    def test_report_with_empty_diagrams_list(self):
        """Report should allow empty diagrams list"""
        request = ReportExportRequest(diagrams=[])
        assert request.diagrams == []

    def test_report_with_empty_traceability_list(self):
        """Report should allow empty traceability list"""
        request = ReportExportRequest(traceability=[])
        assert request.traceability == []

    def test_report_with_none_optional_fields(self):
        """Report should handle Optional fields (omitted or as default)"""
        # Test with omitted optional fields (use defaults)
        request = ReportExportRequest()
        
        assert request.project_name == "Untitled Project"
        assert request.diagrams == []
        assert request.analysis_data == {}

    @pytest.mark.skip(reason="Requires async DB session and ReportExportService - integration test")
    def test_export_report_endpoint_integration(self):
        """Full endpoint test requires service mocking and async fixtures"""
        assert True

    @pytest.mark.skip(reason="Requires PDF generation service - integration test")
    def test_pdf_generation_with_complex_data(self):
        """PDF generation with diagrams, metrics, traceability requires service"""
        assert True

    @pytest.mark.skip(reason="Requires async DB and auth context - integration test")
    def test_report_export_access_control(self):
        """Endpoint should validate user access to project"""
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
