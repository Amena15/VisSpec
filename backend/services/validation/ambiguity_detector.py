"""
Ambiguity detector for requirements text.
Uses spaCy NLP + rule-based heuristics to find vague terms, pronouns, and subjective language.
"""
import re
from typing import List, Dict, Any

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Vague terms commonly found in defective requirements
VAGUE_TERMS = [
    "user-friendly", "intuitive", "efficient", "fast", "quick", "easy",
    "appropriate", "adequate", "sufficient", "reasonable", "normal",
    "regular", "timely", "seamless", "robust", "flexible", "scalable",
    "as needed", "etc", "and/or", "if necessary", "if applicable", "enough",
    "should", "may", "might", "could",
]

# Pronouns that often lack clear antecedents
AMBIGUOUS_PRONOUNS = ["it", "they", "them", "this", "these", "those", "he", "she"]

# Subjective adjectives
SUBJECTIVE_TERMS = [
    "good", "bad", "better", "best", "high", "low", "large", "small",
    "many", "few", "several", "some", "most", "all", "any",
]


class AmbiguityDetector:
    """Detects ambiguous, vague, or subjective language in requirements."""

    def __init__(self):
        self.vague_pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")\b",
            re.IGNORECASE,
        )
        self.pronoun_pattern = re.compile(
            r"\b(" + "|".join(re.escape(p) for p in AMBIGUOUS_PRONOUNS) + r")\b",
            re.IGNORECASE,
        )
        self.subjective_pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in SUBJECTIVE_TERMS) + r")\b",
            re.IGNORECASE,
        )
        self.compliance_pattern = re.compile(
            r"\brelevant\s+\w+\s+regulations?\b",
            re.IGNORECASE,
        )

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze text for ambiguities.
        Returns list of defect findings with confidence scores.
        Per-defect confidence (as per FYP Report):
        - vague_term: 0.85
        - ambiguous_pronoun: 0.60
        - subjective_term: 0.55
        """
        defects = []
        sentences = re.split(r"[.!?]+", text)

        # Check for vague terms (confidence: 0.85 per FYP Report)
        for match in self.vague_pattern.finditer(text):
            severity, confidence = self._vague_confidence(match.group(0), sentences)
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": severity,
                "confidence": round(confidence, 2),
                "description": f"Vague term '{match.group(0)}' makes the requirement unverifiable.",
                "suggestion": f"Replace '{match.group(0)}' with a measurable, specific criterion.",
            })

        # Check for ambiguous pronouns (confidence: 0.60)
        for match in self.pronoun_pattern.finditer(text):
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": "low",
                "confidence": 0.60,
                "description": f"Pronoun '{match.group(0)}' may lack a clear antecedent.",
                "suggestion": f"Replace '{match.group(0)}' with the specific noun it refers to.",
            })

        # Check for subjective terms (confidence: 0.55)
        for match in self.subjective_pattern.finditer(text):
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": "low",
                "confidence": 0.55,
                "description": f"Subjective term '{match.group(0)}' is open to interpretation.",
                "suggestion": f"Replace '{match.group(0)}' with objective, measurable language.",
            })

        # Check for vague compliance references (confidence: 0.85)
        for match in self.compliance_pattern.finditer(text):
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": "high",
                "confidence": 0.85,
                "description": f"Compliance reference '{match.group(0)}' is underspecified.",
                "suggestion": "Specify the exact regulation, standard, or policy to comply with.",
            })

        return defects

    def _vague_confidence(self, term: str, sentences: list) -> tuple[str, float]:
        """
        Compute confidence for a vague term.
        Per FYP Report: vague_term confidence = 0.85
        """
        term_lower = term.lower()
        critical_markers = ["shall", "must", "should", "will", "required", "need"]

        # Per FYP Report specification: vague_term confidence = 0.85
        base_confidence = 0.85
        
        # Keep severity logic but use fixed confidence
        for sent in sentences:
            if term_lower in sent.lower():
                if any(m in sent.lower() for m in critical_markers):
                    return "high", base_confidence
                clauses = len(re.split(r"\band\b|\bor\b|\b;\b", sent))
                if clauses >= 3:
                    return "medium", base_confidence

        return "low", base_confidence
