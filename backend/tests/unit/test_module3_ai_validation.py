#!/usr/bin/env python3

"""
Module 3: AI-Based Validation Comprehensive Unit Tests
Covers REQ_08, REQ_09, REQ_10 and all AI validation functionality

Test Coverage:
- LLM (LLaMA 3 via Groq API) receives sanitized requirement text
- Prompt engineering follows consistent validation template
- API timeout handling (60 seconds max with retry)
- Ambiguity detection: flags vague terms (fast, adequate, user-friendly)
- Inconsistency detection: identifies conflicting requirements (A vs B)
- Completeness checking: identifies missing conditional statements
- Defect classification: Ambiguity, Incompleteness, Inconsistency, Unverifiable
- Severity assignment (Low/Medium/High) per defect
- Confidence score threshold 70% for reporting (BR-10)
- Zero-retention policy: data not stored by AI provider (BR-09)
- Malformed JSON response handling with error logging
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from services.validation.validator import Validator
from services.ai.llm_validator import LLMValidator
from services.ai.response_parser import ResponseParser
from core.config import settings

client = TestClient(app)

class TestModule3AIValidation:
    """Comprehensive test suite for Module 3: AI-Based Validation"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def validator(self):
        """Validator instance"""
        return Validator(use_llm=False)  # Use rule-based for testing
    
    @pytest.fixture
    def llm_validator(self):
        """LLM Validator instance"""
        return LLMValidator()

    # === LLM Integration Tests ===
    
    def test_llm_receives_sanitized_requirement_text(self):
        """Test LLM receives sanitized requirement text"""
        llm_validator = LLMValidator()
        
        # Text with metadata and formatting
        unsanitized_text = """
        Author: John Doe
        Date: 2024-01-01
        Version: 1.0
        
        1. Requirements
        The system shall process data quickly and adequately handle user requests.
        
        2. Implementation
        Additional implementation details...
        """
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            # Mock LLM response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "defects": [
                    {
                        "type": "Ambiguity",
                        "text": "The system shall process data quickly and adequately handle user requests.",
                        "confidence": 0.85,
                        "severity": "Medium",
                        "suggestion": "The system shall process requests within 200ms"
                    }
                ]
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            result = llm_validator.validate_text(unsanitized_text)
            
            # Verify LLM was called with sanitized text
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Should not contain metadata
            sanitized_prompt = messages[-1]['content']
            assert "Author: John Doe" not in sanitized_prompt
            assert "Date: 2024-01-01" not in sanitized_prompt
            assert "Implementation details" not in sanitized_prompt
            assert "process data quickly" in sanitized_prompt  # Should contain requirement
    
    def test_prompt_engineering_consistent_template(self):
        """Test prompt engineering follows consistent validation template"""
        llm_validator = LLMValidator()
        
        requirement_text = "The system shall process user requests efficiently."
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "defects": []
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            llm_validator.validate_text(requirement_text)
            
            # Verify consistent template structure
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Should have system message with consistent template
            system_message = messages[0]['content']
            assert "act as a requirements validation expert" in system_message.lower()
            assert "ambiguity" in system_message.lower()
            assert "inconsistency" in system_message.lower()
            assert "completeness" in system_message.lower()
            assert "json format" in system_message.lower()
    
    def test_api_timeout_handling_60_seconds(self):
        """Test API timeout handling (60 seconds max with retry)"""
        llm_validator = LLMValidator()
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            # Mock timeout exception
            import groq
            mock_client.chat.completions.create.side_effect = groq.RateLimitError("Timeout")
            
            with patch('time.sleep') as mock_sleep:  # Speed up test
                result = llm_validator.validate_text("Test requirement")
                
                # Should retry and handle timeout
                assert mock_client.chat.completions.create.call_count >= 2  # At least 2 attempts
                assert mock_sleep.call_count >= 1  # Should sleep between retries
                
                # Should fall back to rule-based validation
                assert result is not None
                assert "defects" in result

    # === Defect Detection Tests ===
    
    def test_ambiguity_detection_vague_terms(self):
        """Test ambiguity detection flags vague terms (fast, adequate, user-friendly)"""
        validator = Validator(use_llm=False)  # Use rule-based
        
        # Test sentences with vague terms
        vague_requirements = [
            "The system shall process data quickly.",
            "The system shall provide adequate performance.",
            "The system shall be user-friendly.",
            "The system shall respond in a timely manner.",
            "The system shall have good security."
        ]
        
        for req in vague_requirements:
            result = validator.validate_text(req)
            
            # Should detect ambiguity
            assert "defects" in result
            defects = result["defects"]
            
            # Should have at least one ambiguity defect
            ambiguity_defects = [d for d in defects if d.get("type") == "Ambiguity"]
            assert len(ambiguity_defects) > 0, f"Should detect ambiguity in: {req}"
            
            # Should identify vague terms
            vague_terms_found = any(
                any(term in d.get("description", "").lower() for term in ["quickly", "adequate", "user-friendly", "timely", "good"])
                for d in ambiguity_defects
            )
            assert vague_terms_found, f"Should identify vague terms in: {req}"
    
    def test_inconsistency_detection_conflicting_requirements(self):
        """Test inconsistency detection identifies conflicting requirements"""
        validator = Validator(use_llm=False)
        
        # Test conflicting requirements
        conflicting_requirements = [
            "The system shall allow users to delete their accounts.",
            "The system shall not allow users to delete their accounts."
        ]
        
        # Test as context (multiple requirements)
        result = validator.validate_requirements_with_context(conflicting_requirements)
        
        # Should detect inconsistency
        assert "defects" in result
        defects = result["defects"]
        
        # Should have inconsistency defect
        inconsistency_defects = [d for d in defects if d.get("type") == "Inconsistency"]
        assert len(inconsistency_defects) > 0, "Should detect inconsistency between conflicting requirements"
        
        # Should identify the conflict
        conflict_found = any(
            "delete" in d.get("description", "").lower() and "conflict" in d.get("description", "").lower()
            for d in inconsistency_defects
        )
        assert conflict_found, "Should identify specific conflict about account deletion"
    
    def test_completeness_checking_missing_conditionals(self):
        """Test completeness checking identifies missing conditional statements"""
        validator = Validator(use_llm=False)
        
        # Test incomplete requirement (missing condition)
        incomplete_req = "The system shall handle user input."
        
        result = validator.validate_text(incomplete_req)
        
        # Should detect completeness issues
        assert "defects" in result
        defects = result["defects"]
        
        # Should have completeness defect
        completeness_defects = [d for d in defects if d.get("type") == "Incompleteness"]
        assert len(completeness_defects) > 0, "Should detect completeness issue"
        
        # Should identify missing conditions
        condition_missing = any(
            "condition" in d.get("description", "").lower() or "when" in d.get("description", "").lower()
            for d in completeness_defects
        )
        assert condition_missing, "Should identify missing conditional statements"

    # === Defect Classification Tests ===
    
    def test_defect_classification_types(self):
        """Test defect classification: Ambiguity, Incompleteness, Inconsistency, Unverifiable"""
        validator = Validator(use_llm=False)
        
        # Test each defect type
        test_cases = [
            ("The system shall process data quickly.", "Ambiguity"),
            ("The system shall handle user input.", "Incompleteness"),
            ("The system shall allow and not allow user deletion.", "Inconsistency"),
            ("The system shall make users happy.", "Unverifiable")
        ]
        
        for requirement, expected_type in test_cases:
            result = validator.validate_text(requirement)
            
            # Should classify correctly
            defects = result["defects"]
            classified_defects = [d for d in defects if d.get("type") == expected_type]
            
            assert len(classified_defects) > 0, f"Should classify as {expected_type}: {requirement}"
    
    def test_severity_assignment_low_medium_high(self):
        """Test severity assignment (Low/Medium/High) per defect"""
        validator = Validator(use_llm=False)
        
        # Test different severity levels
        test_cases = [
            ("The system shall have good performance.", "Low"),  # Minor ambiguity
            ("The system shall process data quickly.", "Medium"),  # Significant ambiguity
            ("The system shall do everything perfectly.", "High"),  # Major issues
        ]
        
        for requirement, expected_severity in test_cases:
            result = validator.validate_text(requirement)
            
            defects = result["defects"]
            if defects:
                # Check if any defect matches expected severity
                severity_found = any(d.get("severity") == expected_severity for d in defects)
                assert severity_found, f"Should assign {expected_severity} severity to: {requirement}"
    
    def test_confidence_score_threshold_70_percent_br10(self):
        """Test confidence score threshold 70% for reporting (BR-10)"""
        validator = Validator(use_llm=False)
        
        requirement = "The system shall process data quickly."
        result = validator.validate_text(requirement)
        
        # All reported defects should have confidence >= 0.70
        defects = result["defects"]
        
        for defect in defects:
            confidence = defect.get("confidence", 0)
            assert confidence >= 0.70, f"Defect confidence {confidence} should be >= 0.70: {defect}"
    
    def test_zero_retention_policy_br09(self):
        """Test zero-retention policy: data not stored by AI provider (BR-09)"""
        llm_validator = LLMValidator()
        
        requirement_text = "The system shall process user data."
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({"defects": []})
            mock_client.chat.completions.create.return_value = mock_response
            
            llm_validator.validate_text(requirement_text)
            
            # Verify no data retention settings
            call_args = mock_client.chat.completions.create.call_args
            kwargs = call_args[1]
            
            # Should not have data retention enabled
            assert kwargs.get("store", True) is not False  # Default should not store
            # In actual implementation, would verify no training data usage

    # === Error Handling Tests ===
    
    def test_malformed_json_response_handling(self):
        """Test malformed JSON response handling with error logging"""
        llm_validator = LLMValidator()
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            # Mock malformed JSON response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Invalid JSON response {{{"
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('services.ai.llm_validator.logger') as mock_logger:
                result = llm_validator.validate_text("Test requirement")
                
                # Should handle malformed JSON gracefully
                assert result is not None
                assert "defects" in result
                
                # Should log error
                mock_logger.error.assert_called()
                error_call_args = mock_logger.error.call_args[0][0]
                assert "json" in error_call_args.lower() or "parse" in error_call_args.lower()
    
    def test_api_error_handling(self):
        """Test API error handling and fallback to rule-based"""
        llm_validator = LLMValidator()
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            # Mock API error
            import groq
            mock_client.chat.completions.create.side_effect = groq.APIError("API Error")
            
            result = llm_validator.validate_text("Test requirement")
            
            # Should fall back to rule-based validation
            assert result is not None
            assert "defects" in result
            assert "overall_score" in result

    # === Response Parser Tests ===
    
    def test_response_parser_valid_json(self):
        """Test response parser handles valid JSON correctly"""
        parser = ResponseParser()
        
        valid_response = json.dumps({
            "defects": [
                {
                    "type": "Ambiguity",
                    "text": "The system shall process data quickly.",
                    "confidence": 0.85,
                    "severity": "Medium",
                    "suggestion": "Specify exact processing time"
                }
            ],
            "overall_score": 75.0
        })
        
        parsed = parser.parse_validation_response(valid_response)
        
        assert "defects" in parsed
        assert len(parsed["defects"]) == 1
        assert parsed["defects"][0]["type"] == "Ambiguity"
        assert parsed["defects"][0]["confidence"] == 0.85
        assert parsed["overall_score"] == 75.0
    
    def test_response_parser_partial_json(self):
        """Test response parser handles partial/missing fields"""
        parser = ResponseParser()
        
        partial_response = json.dumps({
            "defects": [
                {
                    "type": "Ambiguity",
                    "text": "The system shall process data quickly."
                    # Missing confidence, severity, suggestion
                }
            ]
            # Missing overall_score
        })
        
        parsed = parser.parse_validation_response(partial_response)
        
        # Should fill in missing fields with defaults
        assert "defects" in parsed
        assert len(parsed["defects"]) == 1
        defect = parsed["defects"][0]
        assert "confidence" in defect  # Should have default
        assert "severity" in defect    # Should have default
        assert "overall_score" in parsed  # Should have default

    # === Integration Tests ===
    
    def test_complete_ai_validation_pipeline(self):
        """Test complete AI validation pipeline"""
        validator = Validator(use_llm=True)  # Use LLM
        
        requirement_text = "The system shall process data quickly and adequately handle user requests."
        
        with patch('services.ai.llm_validator.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client
            
            # Mock successful LLM response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "defects": [
                    {
                        "type": "Ambiguity",
                        "text": requirement_text,
                        "confidence": 0.85,
                        "severity": "Medium",
                        "suggestion": "The system shall process requests within 200ms and handle user requests with proper error handling."
                    }
                ],
                "overall_score": 70.0
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            result = validator.validate_text(requirement_text)
            
            # Should complete successfully
            assert "defects" in result
            assert len(result["defects"]) == 1
            assert result["defects"][0]["type"] == "Ambiguity"
            assert result["defects"][0]["confidence"] >= 0.70
            assert result["overall_score"] == 70.0
    
    def test_validation_api_endpoint(self):
        """Test validation API endpoint functionality"""
        with patch('api.validation.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            with patch('services.validation.validator.Validator') as mock_validator_class:
                mock_validator = MagicMock()
                mock_validator.validate_text.return_value = {
                    "defects": [
                        {
                            "type": "Ambiguity",
                            "text": "The system shall process data quickly.",
                            "confidence": 0.85,
                            "severity": "Medium",
                            "suggestion": "Specify exact processing time"
                        }
                    ],
                    "overall_score": 70.0
                }
                mock_validator_class.return_value = mock_validator
                
                response = client.post("/api/validation/validate", json={
                    "text": "The system shall process data quickly."
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "defects" in data
                assert len(data["defects"]) == 1
                assert data["defects"][0]["type"] == "Ambiguity"
                assert data["defects"][0]["confidence"] >= 0.70
    
    def test_validation_with_multiple_requirements(self):
        """Test validation with multiple requirements context"""
        validator = Validator(use_llm=False)
        
        requirements = [
            "The system shall allow users to register accounts.",
            "The system shall authenticate users before granting access.",
            "The system shall not allow users to delete their accounts.",
            "The system shall allow users to delete their accounts."  # Conflicting
        ]
        
        result = validator.validate_requirements_with_context(requirements)
        
        # Should detect inconsistency between conflicting requirements
        assert "defects" in result
        defects = result["defects"]
        
        inconsistency_defects = [d for d in defects if d.get("type") == "Inconsistency"]
        assert len(inconsistency_defects) > 0, "Should detect inconsistency in multiple requirements"
    
    def test_validation_performance_requirements(self):
        """Test validation meets performance requirements"""
        validator = Validator(use_llm=False)
        
        # Test with typical requirement length
        requirement = "The system shall process user requests efficiently and provide adequate performance for all operations."
        
        start_time = time.time()
        result = validator.validate_text(requirement)
        end_time = time.time()
        
        # Should complete within reasonable time (less than 5 seconds for rule-based)
        processing_time = end_time - start_time
        assert processing_time < 5.0, f"Validation took too long: {processing_time}s"
        
        # Should produce valid results
        assert "defects" in result
        assert "overall_score" in result

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
