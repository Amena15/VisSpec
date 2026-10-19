"""
Privacy redaction tests (reviewer checklist E).

Verifies that privacy.redact()/restore() mask PII before any text leaves the
machine and restore it locally afterwards, including through the LLMValidator
pipeline (with the network call stubbed out).

Run: python3 -m pytest backend/tests/unit/test_privacy_redaction.py -q
 (or) python3 backend/tests/unit/test_privacy_redaction.py
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.ai import privacy


EMAIL = "john.doe@example.com"
PHONE = "+1 (555) 123-4567"
SSN = "123-45-6789"


class TestRedactRestore(unittest.TestCase):
    def test_email_masked_and_restored(self):
        text = f"Contact {EMAIL} for details."
        redacted, mapping = privacy.redact(text)
        self.assertNotIn(EMAIL, redacted)
        self.assertIn(EMAIL, mapping.values())
        self.assertEqual(privacy.restore(redacted, mapping), text)

    def test_phone_masked_and_restored(self):
        text = f"Call {PHONE} today."
        redacted, mapping = privacy.redact(text)
        self.assertNotIn(PHONE, redacted)
        self.assertEqual(privacy.restore(redacted, mapping), text)

    def test_ssn_masked_and_restored(self):
        text = f"SSN on file: {SSN}."
        redacted, mapping = privacy.redact(text)
        self.assertNotIn(SSN, redacted)
        self.assertEqual(privacy.restore(redacted, mapping), text)

    def test_no_pii_is_identity(self):
        text = "The system shall validate the login form."
        redacted, mapping = privacy.redact(text)
        self.assertEqual(redacted, text)
        self.assertEqual(mapping, {})
        self.assertEqual(privacy.restore(redacted, mapping), text)

    def test_restore_is_safe_on_clean_text(self):
        """restore() on text without placeholders must not alter it."""
        self.assertEqual(privacy.restore("clean text", {}), "clean text")

    def test_redact_is_idempotent(self):
        """Redacting already-redacted text must not corrupt placeholders."""
        text = f"Email {EMAIL} or {EMAIL} again."
        once, mapping = privacy.redact(text)
        twice, _ = privacy.redact(once)
        self.assertEqual(privacy.restore(twice, mapping), text)


class TestValidatorRedactsBeforeSend(unittest.TestCase):
    """The prompt actually sent over the network must contain no PII."""

    def test_prompt_sent_to_llm_has_no_pii(self):
        from backend.services.ai.llm_validator import LLMValidator

        validator = LLMValidator()
        captured = {}

        def fake_call(prompt):
            captured["prompt"] = prompt
            # Echo any redaction placeholder back in evidence/description, as a
            # real model does, so the restore step is exercised end-to-end.
            import json as _json
            import re as _re
            ph = _re.findall(r"\[(?:EMAIL|PHONE|ID|IP|URL)_\d+\]", prompt)
            echo = ph[0] if ph else "the login form"
            body = {"defects": [{
                "type": "ambiguity", "severity": "High", "confidence": 0.9,
                "description": f"Recipient {echo} unclear",
                "evidence": echo, "suggestion": "define it",
            }]}
            return _json.dumps(body), validator.model, True

        requirement = (
            "The system shall email reports to admin@example.com within 24 hours."
        )
        with patch.object(validator, "_call_llm_with_retry", side_effect=fake_call):
            result = validator.validate_requirement(requirement)

        # PII never left the machine...
        self.assertNotIn("admin@example.com", captured["prompt"])
        # ...but the local result restores it for the user.
        joined = str(result)
        self.assertIn("admin@example.com", joined)
        self.assertTrue(result["llm_used"])

    def test_failed_call_reports_llm_used_false(self):
        """A failed LLM call must never be reported as an LLM verdict."""
        from backend.services.ai.llm_validator import LLMValidator

        validator = LLMValidator()
        with patch.object(
            validator, "_call_llm_with_retry",
            side_effect=Exception("provider down"),
        ):
            result = validator.validate_requirement("The system shall be fast.")
        self.assertFalse(result["llm_used"])
        self.assertFalse(result["json_parse_ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
