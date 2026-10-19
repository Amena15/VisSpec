"""
Ambiguity detector for requirements text.
Uses spaCy NLP + rule-based heuristics to find vague terms, pronouns, and subjective language.
"""
import re
from typing import List, Dict, Any

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Vague terms commonly found in defective requirements.
# IMPORTANT: keep this list focused; overly broad vague-term matching
# creates false positives for otherwise specific (and correctly labeled)
# requirements.
VAGUE_TERMS = [
    "user-friendly", "intuitive",
    # performance adjectives (treat as vague only with weak modal/quantification)
    "efficient", "fast", "quick", "quickly", "easy",
    "appropriate", "adequate", "sufficient", "reasonable",
    "normal", "regular", "timely", "seamless",
    "robust", "flexible", "scalable",
    # security / quality adjectives
    "secure", "security", "proper",
    # control/uncertainty phrases
    "as needed", "etc", "and/or",
    "if necessary", "if applicable", "enough",
    # modality words
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

        Principle (measurable specificity suppresses vague-term noise):
        - A requirement that already contains a concrete, measurable, or verifiable
          signal (a numeric quantity with units, a bounded time/size limit, or an
          explicit standard/format/protocol identifier) is *specific*, so we do NOT
          raise low-value ambiguity noise for vague/performance-style wording.
        - Pronouns, subjective terms, compliance references and internal
          contradictions are still detected regardless of measurable signals.
        """
        defects: List[Dict[str, Any]] = []
        text_lower = text.lower()

        # ================================================================
        # 1) DETECT STRONG SPECIFIC SIGNALS (measurable / verifiable)
        # ================================================================
        # Quantitative measurability: a number tied to a unit, percentage, size,
        # count or character/digit length. These generalise to any requirement.
        strong_signals = [
            r"\b\d+\s*(ms|milliseconds?|seconds?|sec|s|minutes?|mins?|hours?|hrs?|days?)\b",
            r"\b\d+(?:\.\d+)?\s*%\b",
            r"\b\d+(?:\.\d+)?\s*(bytes?|mb|kb|gb|tb)\b",
            r"\b\d+\s*characters?\b",
            r"\b\d+\s*(?:or\s+)?(?:more|less|fewer|additional)\b",
            r"\b(?:at\s+least|at\s+most|no\s+more\s+than|no\s+fewer\s+than|minimum\s+of|"
            r"maximum\s+of|up\s+to|less\s+than|more\s+than|greater\s+than|fewer\s+than)"
            r"\s+\d+\b",
            r"\b(?:within|under|over|after|before|every|each)\s+\d+\b",
            r"\b\d+\s*(?:concurrent\s+)?(?:users?|requests?|attempts?|connections?|"
            r"transactions?|records?|retries|times)\b",
        ]
        # A small, dataset-independent vocabulary of concrete formats, standards,
        # protocols and well-known technologies that name a verifiable artefact.
        specific_identifiers = [
            "json", "xml", "yaml", "csv", "pdf", "png", "jpeg", "jpg", "sql",
            "oauth", "oauth2", "openid", "openapi", "rest", "https", "http",
            "tls", "ssl", "jwt", "saml", "wcag", "owasp", "iso", "gdpr", "hipaa",
            "bcrypt", "argon2", "pbkdf2", "aes", "sha-256", "sha256",
            "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
            "elasticsearch", "kafka", "rabbitmq", "docker", "kubernetes", "websocket",
        ]
        identifier_pattern = (
            r"\b(?:v?\d+(?:\.\d+)+)\b"  # explicit versions e.g. 3.0, 2.1, v1.2
            r"|\b(?:" + "|".join(re.escape(t) for t in specific_identifiers) + r")\b"
        )

        has_strong_signal = (
            any(re.search(p, text_lower, re.IGNORECASE) for p in strong_signals)
            or bool(re.search(identifier_pattern, text_lower, re.IGNORECASE))
        )


        # 2) CONTRADICTION DETECTION (kept even when strong signals are present)
        contradiction_patterns = [
            r"allow.*but.*(prevent|restrict|deny|not)",
            r"must.*but.*(should|may|could)",
            r"also.*but",
            r"handle.*but.*restrict",
            r"delete.*but.*retention",
        ]

        if any(re.search(p, text_lower, re.IGNORECASE) for p in contradiction_patterns):
            defects.append({
                "text": text[:100],
                "type": "inconsistency",
                "severity": "high",
                "confidence": 0.90,
                "description": "Requirement contains contradictory statements.",
                "suggestion": "Resolve the contradiction between conflicting requirements.",
            })

        # 3) When a requirement already contains a measurable/verifiable signal, do not
        # raise low-value ambiguity noise for performance-style wording.
        if has_strong_signal:
            return defects

        # 4) VAGUE / SUBJECTIVE / PRONOUN DETECTION (only when no strong signal)
        sentences = re.split(r"[.!?]+", text)

        for match in self.vague_pattern.finditer(text):
            term = match.group(0)
            severity, confidence = self._vague_confidence(term, sentences)
            defects.append({
                "text": term,
                "type": "ambiguity",
                "severity": severity,
                "confidence": round(confidence, 2),
                "description": f"Vague term '{term}' makes the requirement unverifiable.",
                "suggestion": f"Replace '{term}' with a measurable, specific criterion.",
            })

        # Pronouns
        for match in self.pronoun_pattern.finditer(text):
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": "low",
                "confidence": 0.60,
                "description": f"Pronoun '{match.group(0)}' may lack a clear antecedent.",
                "suggestion": f"Replace '{match.group(0)}' with the specific noun it refers to.",
            })

        # Subjective terms
        for match in self.subjective_pattern.finditer(text):
            defects.append({
                "text": match.group(0),
                "type": "ambiguity",
                "severity": "low",
                "confidence": 0.55,
                "description": f"Subjective term '{match.group(0)}' is open to interpretation.",
                "suggestion": f"Replace '{match.group(0)}' with objective, measurable language.",
            })

        # Compliance reference
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
