#!/usr/bin/env python3
"""
Module 3: AI Validation - Professional Unit Tests

Scope:
- Rule-based ambiguity, completeness, and consistency validation
- Validator orchestration and result shape
- LLM validator safety behavior without live API dependency
- LLM response parsing utilities

Note:
- Live LLM network paths and authenticated API endpoint flows are integration tests
  and are intentionally skipped in this unit suite.
"""

import json

import pytest

import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from backend.core.config import settings
from backend.services.ai.llm_validator import LLMValidator
from backend.services.ai.response_parser import ResponseParser
from backend.services.validation.validator import Validator


class TestModule3AIValidation:
    """Professional unit tests for Module 3 AI validation pipeline."""

    # =====================================================================
    # Rule-Based Validation Tests
    # =====================================================================

    def test_validator_returns_expected_result_shape(self):
        """Validator returns full result payload with required keys."""
        validator = Validator(use_llm=False)
        result = validator.validate_text("The system shall process requests quickly.")

        assert isinstance(result, dict)
        for key in [
            "overall_score",
            "total_defects",
            "defects_by_type",
            "defects_by_severity",
            "defects",
            "llm_used",
            "processing_time_ms",
        ]:
            assert key in result

        assert result["llm_used"] is False
        assert isinstance(result["defects"], list)

    def test_ambiguity_detection_flags_vague_terms(self):
        """Rule-based validator flags common vague terms as ambiguity defects."""
        validator = Validator(use_llm=False)
        text = "The system shall provide fast and user-friendly responses."
        result = validator.validate_text(text)

        ambiguity_defects = [d for d in result["defects"] if d.get("type") == "ambiguity"]
        assert len(ambiguity_defects) > 0
        assert any("vague" in d.get("description", "").lower() for d in ambiguity_defects)

    def test_completeness_detection_missing_modal(self):
        """Requirement without modal verb is flagged as incompleteness."""
        validator = Validator(use_llm=False)
        text = "System handles user input and stores data."
        result = validator.validate_text(text)

        incompleteness_defects = [d for d in result["defects"] if d.get("type") == "incompleteness"]
        assert len(incompleteness_defects) > 0
        assert any("modal verb" in d.get("description", "").lower() for d in incompleteness_defects)

    def test_consistency_detection_internal_contradiction(self):
        """Single requirement with contradictory terms is flagged as inconsistency."""
        validator = Validator(use_llm=False)
        text = "The system shall always accept input and never accept input."
        result = validator.validate_text(text)

        inconsistency_defects = [d for d in result["defects"] if d.get("type") == "inconsistency"]
        assert len(inconsistency_defects) > 0
        assert any("contradict" in d.get("description", "").lower() for d in inconsistency_defects)

    def test_context_validation_maps_defects_to_requirement_ids(self):
        """Context-aware validation should attach req_id for detected defects."""
        validator = Validator(use_llm=False)
        requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall be user-friendly and fast.",
                "category": "functional",
                "vague_terms": ["user-friendly", "fast"],
                "modal_verbs": ["shall"],
            },
            {
                "req_id": "REQ-002",
                "original_text": "System handles errors.",
                "category": "functional",
                "vague_terms": [],
                "modal_verbs": [],
            },
        ]

        result = validator.validate_requirements_with_context(requirements)
        assert "defects" in result
        assert len(result["defects"]) > 0
        assert any(d.get("req_id") in {"REQ-001", "REQ-002"} for d in result["defects"])

    def test_validate_multiple_returns_cross_requirement_summary(self):
        """validate_multiple returns per-requirement summary and cross-requirement analysis."""
        validator = Validator(use_llm=False)
        inputs = [
            "The system shall allow account deletion.",
            "The system shall prevent account deletion.",
        ]

        result = validator.validate_multiple(inputs)
        assert "overall_score" in result
        assert "total_defects" in result
        assert "requirement_count" in result
        assert "cross_requirement_defects" in result
        assert result["requirement_count"] == 2

    # =====================================================================
    # LLM Validator Unit Tests (No Live Network)
    # =====================================================================

    def test_llm_validator_unavailable_without_api_key(self, monkeypatch):
        """When API key is missing, LLM validator must fail safe without network calls."""
        monkeypatch.setattr(settings, "GROQ_API_KEY", "")
        llm_validator = LLMValidator()

        assert llm_validator.is_available is False
        result = llm_validator.validate_requirement("The system shall process requests quickly.")
        assert result["llm_used"] is False
        assert "error" in result

    def test_llm_confidence_filtering_enforces_threshold(self):
        """Confidence filter keeps only defects above configured threshold."""
        llm_validator = LLMValidator()
        defects = [
            {"type": "ambiguity", "confidence": 0.92},
            {"type": "incompleteness", "confidence": 0.69},
            {"type": "inconsistency", "confidence": 0.70},
        ]

        filtered = llm_validator._filter_by_confidence(defects)
        assert all(d["confidence"] >= settings.MIN_CONFIDENCE_THRESHOLD for d in filtered)

    def test_llm_response_parser_handles_malformed_json(self):
        """Malformed LLM JSON should return None rather than throwing."""
        llm_validator = LLMValidator()
        parsed = llm_validator._parse_llm_response("{ bad json")
        assert parsed is None

    # =====================================================================
    # Response Parser Utility Tests
    # =====================================================================

    def test_response_parser_extracts_json_from_code_block(self):
        """ResponseParser should extract JSON payload wrapped in markdown fences."""
        text = """
        Here is the result:
        ```json
        {"defects": [{"type": "ambiguity"}]}
        ```
        """
        json_str = ResponseParser.extract_json(text)
        assert json_str is not None
        assert "defects" in json_str

    def test_response_parser_parses_valid_json_object(self):
        """ResponseParser.parse_json should parse valid JSON object content."""
        text = json.dumps({"defects": [{"type": "ambiguity", "severity": "high", "confidence": 0.9, "text": "x", "description": "y"}]})
        parsed = ResponseParser.parse_json(text)
        assert isinstance(parsed, dict)
        assert "defects" in parsed

    # =====================================================================
    # Integration/Live Tests (Skipped in Unit Suite)
    # =====================================================================

    @pytest.mark.skip(reason="Requires live Groq API and network connectivity - integration test")
    def test_live_llm_validation_path(self):
        """Live LLM validation should be covered in integration environment."""
        llm_validator = LLMValidator()
        result = llm_validator.validate_requirement("The system shall respond quickly.")
        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Requires authenticated async API context and DB fixtures - integration test")
    def test_validation_endpoint_integration(self):
        """Validation endpoint flow should be tested with auth + DB fixtures."""
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
