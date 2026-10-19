"""
PII redaction for text sent to the external LLM provider (R2-9).

Pattern-based masking applied BEFORE any text leaves the local machine, and
restored AFTER the response returns, so the application can continue to work
with the original text locally.

IMPORTANT (honesty note): this is a local, pattern-based control. It reduces
but does NOT guarantee anonymisation, and it is NOT the same as the provider's
zero-retention policy — that is a provider policy guarantee, not a feature
enforced by this code.
"""
import re
from typing import Dict, List, Tuple

PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("URL", re.compile(r"https?://\S+")),
    ("IP", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("PHONE", re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d")),
    ("ID", re.compile(r"\b[A-Z]{2,}-\d{3,}\b")),  # contract / ticket style ids (adapt to your org)
]


def redact(text: str, extra_terms: Tuple[str, ...] = ()) -> Tuple[str, Dict[str, str]]:
    """Return (masked_text, mapping). extra_terms: client/project names to mask."""
    if not isinstance(text, str) or not text:
        return text, {}
    mapping: Dict[str, str] = {}
    counters: Dict[str, int] = {}

    def sub(label: str, m: re.Match) -> str:
        counters[label] = counters.get(label, 0) + 1
        tok = f"[{label}_{counters[label]}]"
        mapping[tok] = m.group(0)
        return tok

    for label, pat in PATTERNS:
        text = pat.sub(lambda m, l=label: sub(l, m), text)
    for t in extra_terms:
        if t:
            text = re.sub(re.escape(t), lambda m: sub("ORG", m), text, flags=re.I)
    return text, mapping


def restore(text: str, mapping: Dict[str, str]) -> str:
    """Replace redaction placeholders with their original values (local only)."""
    if not text or not mapping:
        return text
    for tok, orig in mapping.items():
        text = text.replace(tok, orig)
    return text
