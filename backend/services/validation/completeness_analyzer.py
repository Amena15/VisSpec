"""
Completeness analyzer for requirements.
Checks whether requirements contain all necessary components for a well-formed specification.
"""
import re
from typing import List, Dict, Any

from core.logging import get_logger

logger = get_logger(__name__)

# Patterns that indicate well-formed requirements
SHALL_PATTERN = re.compile(r"\b(shall|must|will|should)\b", re.IGNORECASE)
ACTOR_PATTERN = re.compile(r"\b(the\s+\w+|system|user|admin|actor)\b", re.IGNORECASE)
ACTION_PATTERN = re.compile(r"\b(shall|must|will|should)\s+(\w+)", re.IGNORECASE)
CONDITION_PATTERN = re.compile(r"\b(if|when|unless|while|after|before)\b", re.IGNORECASE)


class CompletenessAnalyzer:
    """Analyzes requirements for completeness."""

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """
        Check if a requirement has all necessary components.
        A well-formed requirement should have: actor, action, and optionally conditions.
        """
        defects = []
        word_count = len(text.split())

        # Check for modal verb
        if not SHALL_PATTERN.search(text):
            # Per FYP Report: missing modal confidence = 0.80
            confidence = 0.80
            defects.append({
                "text": text,
                "type": "incompleteness",
                "severity": "high",
                "confidence": confidence,
                "description": "Requirement lacks a modal verb (shall, must, will, should). It may not be a proper requirement.",
                "suggestion": "Add 'shall' for mandatory requirements or 'should' for recommended ones.",
            })

        # Check for actor/subject
        if not ACTOR_PATTERN.search(text):
            # Per FYP Report specification: missing_actor confidence = 0.75
            confidence = 0.75
            defects.append({
                "text": text,
                "type": "incompleteness",
                "severity": "medium",
                "confidence": confidence,
                "description": "No clear actor or subject identified in the requirement.",
                "suggestion": "Specify who or what performs the action (e.g., 'The system shall...').",
            })

        # Check for action verb after modal
        action_match = ACTION_PATTERN.search(text)
        if action_match:
            action_verb = action_match.group(2)
            weak_verbs = {"be", "have", "do", "provide", "support", "handle", "manage"}
            if action_verb.lower() in weak_verbs:
                defects.append({
                    "text": text,
                    "type": "incompleteness",
                    "severity": "low",
                    "confidence": 0.60,
                    "description": f"Weak action verb '{action_verb}' may not describe a specific behavior.",
                    "suggestion": f"Replace '{action_verb}' with a more specific action verb.",
                })

        # Check for missing acceptance criteria
        if word_count < 10:
            # Shortness is more concerning for requirements that should be detailed
            confidence = round(min(0.50 + (10 - word_count) * 0.05, 0.90), 2)
            defects.append({
                "text": text,
                "type": "incompleteness",
                "severity": "medium",
                "confidence": confidence,
                "description": "Requirement is very short and may lack sufficient detail.",
                "suggestion": "Add acceptance criteria, preconditions, or expected outcomes.",
            })

        return defects
