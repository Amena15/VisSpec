"""
Consistency checker for requirements.
Detects contradictions, conflicting terms, and inconsistent terminology.
"""
import re
from typing import List, Dict, Any, Set
from collections import defaultdict

from core.logging import get_logger

logger = get_logger(__name__)

# Contradictory term pairs
CONTRADICTIONS = [
    ("always", "never"),
    ("must", "must not"),
    ("shall", "shall not"),
    ("required", "optional"),
    ("mandatory", "optional"),
    ("enabled", "disabled"),
    ("allow", "prevent"),
    ("permit", "forbid"),
    ("include", "exclude"),
    ("accept", "reject"),
]


class ConsistencyChecker:
    """Checks for contradictions and inconsistencies across requirements."""

    def check_single(self, text: str) -> List[Dict[str, Any]]:
        """Check a single requirement text for internal contradictions."""
        defects = []
        lower_text = text.lower()

        for term_a, term_b in CONTRADICTIONS:
            if term_a in lower_text and term_b in lower_text:
                # Confidence based on how many times the contradictory pair appears
                count_a = len(re.findall(re.escape(term_a), lower_text))
                count_b = len(re.findall(re.escape(term_b), lower_text))
                confidence = round(min(0.80 + (count_a + count_b) * 0.05, 1.0), 2)
                defects.append({
                    "text": text,
                    "type": "inconsistency",
                    "severity": "high",
                    "confidence": confidence,
                    "description": f"Contradictory terms '{term_a}' and '{term_b}' found in the same requirement.",
                    "suggestion": f"Resolve the contradiction between '{term_a}' and '{term_b}'.",
                })

        return defects

    def check_multiple(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """
        Check multiple requirements for cross-requirement inconsistencies.
        """
        defects = []

        # Extract key entities and their stated behaviors
        entity_behaviors: Dict[str, Set[str]] = defaultdict(set)

        for req_text in requirements:
            # Simple extraction: look for "system shall" patterns
            match = re.search(r"(?:the\s+)?(?:system|user|application)\s+(?:shall|should|must)\s+(.+?)(?:\.|$)", req_text, re.IGNORECASE)
            if match:
                behavior = match.group(1).strip().lower()
                # Use first noun phrase as entity key (simplified)
                entity_match = re.search(r"(?:the\s+)?(\w+)", req_text, re.IGNORECASE)
                if entity_match:
                    entity = entity_match.group(1).lower()
                    entity_behaviors[entity].add(behavior)

        # Check for contradictory behaviors
        for entity, behaviors in entity_behaviors.items():
            behavior_list = list(behaviors)
            for i, b1 in enumerate(behavior_list):
                for b2 in behavior_list[i + 1:]:
                    for term_a, term_b in CONTRADICTIONS:
                        if term_a in b1 and term_b in b2:
                            confidence = round(min(0.75 + len(behaviors) * 0.03, 1.0), 2)
                            defects.append({
                                "text": f"Requirements about '{entity}'",
                                "type": "inconsistency",
                                "severity": "high",
                                "confidence": confidence,
                                "description": f"Contradictory behaviors for '{entity}': '{b1}' vs '{b2}'.",
                                "suggestion": f"Reconcile the conflicting requirements for '{entity}'.",
                            })

        return defects
