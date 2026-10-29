#!/usr/bin/env python3
"""
06_redact_before_llm.py -- Addresses R2-Major-9 (privacy/governance of text sent to the external API).

Drop-in pre-processing step: call redact(text) BEFORE the text is sent to Groq, and
restore(text, mapping) on the response. Place in backend/services/ai/privacy.py and call it
inside LLMValidator.validate_requirement() / GroqLLMService._make_request().

Pattern-based masking is a minimum baseline, NOT a guarantee of anonymisation; say so in the paper.
"""
import re

PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("URL", re.compile(r"https?://\S+")),
    ("IP", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("PHONE", re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d")),
    ("ID", re.compile(r"\b[A-Z]{2,}-\d{3,}\b")),   # contract / ticket style ids (adapt to your org)
]


def redact(text: str, extra_terms=()):
    """Return (masked_text, mapping). extra_terms: client/project names to be masked too."""
    mapping, counters = {}, {}

    def sub(label, m):
        counters[label] = counters.get(label, 0) + 1
        tok = f"[{label}_{counters[label]}]"
        mapping[tok] = m.group(0)
        return tok

    for label, pat in PATTERNS:
        text = pat.sub(lambda m, l=label: sub(l, m), text)
    for t in extra_terms:
        text = re.sub(re.escape(t), lambda m: sub("ORG", m), text, flags=re.I)
    return text, mapping


def restore(text: str, mapping: dict) -> str:
    for tok, orig in mapping.items():
        text = text.replace(tok, orig)
    return text


if __name__ == "__main__":
    s = ("Contact ali@acme.com or +60 12-345 6789; the ACME-1234 portal at "
         "https://acme.internal should log users from 10.0.0.1.")
    masked, mp = redact(s, extra_terms=["ACME"])
    print("masked:", masked)
    print("round-trip ok:", restore(masked, mp) == s)
