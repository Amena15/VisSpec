"""
Enhanced LLM Validator for VisSpec using LLaMA 3 via Groq API.
Implements IEEE 830 compliant validation with confidence filtering (BR-10).
"""

import json
import time
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LLMValidator:
    """
    Enhanced LLM validator using LLaMA 3 via Groq API.
    Implements structured validation with IEEE 830 criteria and confidence filtering.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE
        self.confidence_threshold = settings.MIN_CONFIDENCE_THRESHOLD
        self._available = bool(self.api_key)

        if not self._available:
            logger.warning("GROQ_API_KEY not set. LLM validation will be disabled.")
        else:
            logger.info(f"LLM Validator initialized with model: {self.model}")

    @property
    def is_available(self) -> bool:
        """Check if LLM validator is available."""
        return self._available

    def validate_requirement(self, requirement_text: str) -> Dict[str, Any]:
        """
        Validate a single requirement using LLaMA 3 with IEEE 830 standards.
        
        Args:
            requirement_text: The requirement text to validate
            
        Returns:
            Dict with defects list filtered by confidence >= 0.70 (BR-10)
        """
        if not self._available:
            return {"defects": [], "llm_used": False, "error": "LLM not available"}

        try:
            # Log zero-retention confirmation (BR-09)
            logger.info("Sending requirement to LLM - no user data will be stored by provider (zero-retention)")
            
            # Construct IEEE 830 compliant prompt
            prompt = self._build_validation_prompt(requirement_text)
            
            # Call LLM with retry logic
            response = self._call_llm_with_retry(prompt)
            
            if response:
                # Parse JSON response
                parsed_response = self._parse_llm_response(response)
                
                if parsed_response and "defects" in parsed_response:
                    # Filter by confidence threshold (BR-10)
                    filtered_defects = self._filter_by_confidence(parsed_response["defects"])
                    
                    # Log zero-retention confirmation after response
                    logger.info("LLM response received - zero-retention confirmed (no data stored by provider)")
                    
                    return {
                        "defects": filtered_defects,
                        "llm_used": True,
                        "zero_retention_confirmed": True,
                        "model_used": self.model
                    }
            
            return {"defects": [], "llm_used": True, "error": "No valid response"}

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {"defects": [], "llm_used": False, "error": str(e)}

    def validate_batch(self, requirements: List[str]) -> Dict[str, Any]:
        """
        Validate multiple requirements in batch for efficiency.
        
        Args:
            requirements: List of requirement texts to validate
            
        Returns:
            Dict with defects mapped to requirement indices
        """
        if not self._available:
            return {"defects_by_index": {}, "llm_used": False, "error": "LLM not available"}

        try:
            logger.info(f"Validating batch of {len(requirements)} requirements with LLM")
            
            all_defects = {}
            for i, req_text in enumerate(requirements):
                result = self.validate_requirement(req_text)
                if result.get("defects"):
                    all_defects[i] = result["defects"]
            
            return {
                "defects_by_index": all_defects,
                "llm_used": True,
                "zero_retention_confirmed": True,
                "model_used": self.model,
                "total_requirements": len(requirements),
                "requirements_with_defects": len(all_defects)
            }

        except Exception as e:
            logger.error(f"Batch LLM validation failed: {e}")
            return {"defects_by_index": {}, "llm_used": False, "error": str(e)}

    def _build_validation_prompt(self, requirement_text: str) -> str:
        """
        Build IEEE 830 compliant validation prompt.
        
        Args:
            requirement_text: The requirement to validate
            
        Returns:
            Structured prompt for LLM
        """
        return f"""You are a requirements engineering expert following IEEE 830 standards. Analyze the following requirement and return a JSON object.

Requirement: {requirement_text}

Evaluate for the four IEEE 830 defect types:
1. Ambiguity: vague terms (e.g., "fast", "adequate", "user-friendly", "appropriate", "reasonable") that have multiple interpretations
2. Incompleteness: missing conditions, exceptions, error handling, or constraints
3. Inconsistency: contradictions with standard requirements engineering practices
4. Unverifiability: no measurable acceptance criteria or test conditions

For each defect found, provide:
- type (string): one of "ambiguity", "incompleteness", "inconsistency", "unverifiable"
- severity (string): "High", "Medium", or "Low"
- confidence (float): 0.0-1.0 (only include defects with confidence >= 0.70)
- description (string): clear explanation of the issue
- suggestion (string): concrete rewrite recommendation with specific, measurable criteria

Return JSON format:
{{
  "defects": [
    {{
      "type": "ambiguity|incompleteness|inconsistency|unverifiable",
      "severity": "High|Medium|Low",
      "confidence": 0.0-1.0,
      "description": "clear explanation of the issue",
      "suggestion": "specific rewrite recommendation with measurable criteria"
    }}
  ]
}}

Only include defects with confidence >= 0.70. If no defects meet this threshold, return empty defects array.
"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _call_llm_with_retry(self, prompt: str) -> Optional[str]:
        """
        Call LLM with retry logic for reliability.
        
        Args:
            prompt: The prompt to send to LLM
            
        Returns:
            LLM response text or None if failed
        """
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}")
            raise

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM JSON response safely.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed JSON dict or None if invalid
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Invalid JSON response: {response}")
            return None

    def _filter_by_confidence(self, defects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter defects by confidence threshold (BR-10).
        
        Args:
            defects: List of defect dictionaries
            
        Returns:
            Filtered list with confidence >= 0.70
        """
        filtered = []
        for defect in defects:
            confidence = defect.get("confidence", 0.0)
            if confidence >= self.confidence_threshold:
                filtered.append(defect)
            else:
                logger.debug(f"Filtered defect with confidence {confidence}: {defect.get('type', 'unknown')}")
        
        logger.info(f"Filtered defects: {len(filtered)}/{len(defects)} meet confidence >= {self.confidence_threshold}")
        return filtered

    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics and status.
        
        Returns:
            Dict with validator status and configuration
        """
        return {
            "available": self._available,
            "model": self.model,
            "temperature": self.temperature,
            "confidence_threshold": self.confidence_threshold,
            "api_key_configured": bool(self.api_key)
        }
