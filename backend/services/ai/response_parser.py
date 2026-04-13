"""
Response parser for LLaMA 3 / Groq API responses.
Validates and parses JSON responses from the LLM.
"""
import json
import re
from typing import Any, Dict, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class ResponseParser:
    """Parses and validates LLM responses."""

    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        """
        Extract JSON from LLM response text.
        Handles cases where the model wraps JSON in markdown code blocks.
        """
        # Try to find JSON in code blocks
        code_block_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try to find JSON object directly
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return None

    @staticmethod
    def parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON string into a dictionary."""
        json_str = ResponseParser.extract_json(text)
        if not json_str:
            logger.error(f"No JSON found in response: {text[:200]}")
            return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}. Raw: {json_str[:200]}")
            return None

    @staticmethod
    def validate_schema(data: Dict[str, Any], required_keys: list) -> bool:
        """Validate that response contains required top-level keys."""
        missing = [k for k in required_keys if k not in data]
        if missing:
            logger.warning(f"Missing required keys in response: {missing}")
            return False
        return True

    @staticmethod
    def validate_defects(data: Dict[str, Any]) -> bool:
        """Validate defect response schema."""
        if "defects" not in data:
            return False
        for defect in data["defects"]:
            required = ["text", "type", "severity", "confidence", "description"]
            if not all(k in defect for k in required):
                logger.warning(f"Defect missing required fields: {defect}")
                return False
            if defect["type"] not in ("ambiguity", "incompleteness", "inconsistency", "unverifiable"):
                logger.warning(f"Invalid defect type: {defect['type']}")
                return False
            if defect["severity"] not in ("high", "medium", "low"):
                logger.warning(f"Invalid severity: {defect['severity']}")
                return False
            if not (0.0 <= defect.get("confidence", 0) <= 1.0):
                logger.warning(f"Confidence out of range: {defect.get('confidence')}")
                return False
        return True

    @staticmethod
    def validate_classification(data: Dict[str, Any]) -> bool:
        """Validate classification response schema."""
        if "classifications" not in data:
            return False
        valid_categories = {"functional", "non_functional", "interface", "constraint", "data"}
        for item in data["classifications"]:
            if "category" not in item or "text" not in item:
                return False
            if item["category"] not in valid_categories:
                logger.warning(f"Invalid category: {item['category']}")
                return False
        return True
