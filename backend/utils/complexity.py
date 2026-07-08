"""Shared requirement complexity utilities.

Centralizes requirement complexity heuristics so API surfaces stay consistent.
"""

from __future__ import annotations


def determine_requirement_complexity(requirement_text: str) -> str:
    """Return normalized complexity level: high, medium, or low."""
    text = (requirement_text or "").lower()
    word_count = len(text.split())

    # Keep this aligned with analyst traceability semantics.
    complexity_indicators = {
        "high": ["multiple", "various", "complex", "integrate", "system", "database", "security"],
        "medium": ["shall", "must", "should", "will", "interface", "validate", "process"],
        "low": ["simple", "basic", "single", "display", "show", "list"],
    }

    score = 0
    for level, indicators in complexity_indicators.items():
        for indicator in indicators:
            if indicator in text:
                if level == "high":
                    score += 3
                elif level == "medium":
                    score += 2
                else:
                    score += 1

    if word_count > 20:
        score += 2
    elif word_count > 10:
        score += 1

    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"
