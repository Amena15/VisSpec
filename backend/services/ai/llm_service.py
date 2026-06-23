"""
Groq API / LLaMA 3 integration service.
Handles LLM calls with retry logic, response parsing, and error handling.
"""
import json
import re
import asyncio
from typing import Any, Dict, Optional, List
import requests

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.services.ai.prompts import (
    AMBIGUITY_DETECTION_PROMPT,
    CLASSIFICATION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    COMPLEXITY_ESTIMATION_PROMPT,
    DIAGRAM_GENERATION_PROMPT,
    REQUIREMENT_EXTRACTION_PROMPT,
    VALIDATION_PROMPT,
)
from backend.services.ai.response_parser import ResponseParser
from backend.services.ai.retry_handler import retry_handler


logger = get_logger(__name__)


class GroqLLMService:
    """Service for interacting with Groq API (LLaMA 3)."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE
        self._available = bool(self.api_key)

        if not self._available:
            logger.warning(
                "GROQ_API_KEY not set. LLM features will fall back to rule-based analysis."
            )

    def _make_request(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """Make a single API call to Groq."""
        if not self._available:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        system_instruction = (
            "You are a strict data extraction API. You MUST output ONLY valid JSON. "
            "Do not include conversational filler (e.g., 'I am ready', 'Here is the JSON'). "
            "Do not include markdown blocks (e.g., ```json)."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def call_with_retry(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """Call the API with retry logic."""
        return retry_handler.execute_with_retry(
            self._make_request,
            prompt,
            max_tokens,
            retryable_exceptions=(requests.RequestException, ConnectionError, TimeoutError),
        )

    def analyze_ambiguity(self, text: str) -> Dict[str, Any]:
        """Detect ambiguities and defects in requirements text."""
        prompt = AMBIGUITY_DETECTION_PROMPT.format(text=text)
        response = self.call_with_retry(prompt)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed and ResponseParser.validate_defects(parsed):
                return parsed

        return {"defects": []}

    def classify_requirements(self, text: str) -> Dict[str, Any]:
        """Classify requirements by type."""
        prompt = CLASSIFICATION_PROMPT.format(text=text)
        response = self.call_with_retry(prompt)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed and ResponseParser.validate_classification(parsed):
                return parsed

        return {"classifications": []}

    def extract_requirements(self, text: str) -> Dict[str, Any]:
        """Extract clean, atomic requirements using professional prompt."""
        if len(text) > 8000:
            text = text[:8000]

        prompt = REQUIREMENT_EXTRACTION_PROMPT.format(text=text)
        response = self.call_with_retry(prompt, max_tokens=2048)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed and "requirements" in parsed:
                return parsed

        return {"requirements": []}

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities, actors, and relationships."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
        response = self.call_with_retry(prompt)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed:
                return parsed

        return {"entities": [], "relationships": [], "modal_verbs": [], "vague_terms": []}

    def estimate_complexity(self, text: str) -> Dict[str, Any]:
        """Estimate implementation complexity."""
        prompt = COMPLEXITY_ESTIMATION_PROMPT.format(text=text)
        response = self.call_with_retry(prompt)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed:
                return parsed

        return {
            "complexity_score": 0,
            "estimated_effort_hours": 0,
            "risk_level": "unknown",
            "factors": [],
            "recommendations": [],
        }

    def generate_diagram(self, text: str, diagram_type: str) -> Optional[str]:
        """Generate Mermaid diagram syntax from requirements."""
        prompt = DIAGRAM_GENERATION_PROMPT.format(text=text, diagram_type=diagram_type)
        response = self.call_with_retry(prompt, max_tokens=4096)

        if response:
            match = re.search(r"```mermaid\s*\n(.*?)\n```", response, re.DOTALL)
            if match:
                return match.group(1).strip()
            return response.strip()

        return None

    def validate_requirement(self, text: str) -> Dict[str, Any]:
        """
        Validate a single requirement using IEEE 830 standards.
        Returns defects with type, severity, confidence, and suggestion.
        Filters by confidence >= 0.70 (BR-10 threshold).
        """
        prompt = VALIDATION_PROMPT.format(requirement_text=text)
        response = self.call_with_retry(prompt, max_tokens=2048)

        if response:
            parsed = ResponseParser.parse_json(response)
            if parsed and "defects" in parsed:
                filtered_defects = [
                    d for d in parsed["defects"]
                    if d.get("confidence", 0) >= 0.70
                ]
                return {"defects": filtered_defects}

        return {"defects": []}

    async def chat_completion(self, prompt: str, temperature: float = 0.1, **kwargs) -> str:
        """
        Async wrapper for chat completion using the existing sync call_with_retry.
        This is used by the diagram semantic extractor.
        """
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.call_with_retry(prompt)
        )
        return response or ""

    @property
    def is_available(self) -> bool:
        return self._available


# Global LLM service instance
llm_service = GroqLLMService()