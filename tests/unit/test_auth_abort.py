"""
Unit test for the auth-abort rule in scripts/run_frozen_eval.py.

Verifies:
  - _is_auth_failure() returns True for HTTP 401/403 error strings
  - _is_auth_failure() returns False for non-auth errors (429, network, etc.)
  - _case() returns is_auth_failure=True when validate_requirement raises 403
  - After 3 consecutive 403s, the main loop aborts (simulated)
"""
import sys, os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add repo root to path so we can import run_frozen_eval
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

import importlib.util
spec = importlib.util.spec_from_file_location(
    "run_frozen_eval", os.path.join(REPO, "scripts", "run_frozen_eval.py")
)
rfe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rfe)


class TestIsAuthFailure(unittest.TestCase):
    """Test the _is_auth_failure string matcher."""

    def test_403_detected(self):
        self.assertTrue(rfe._is_auth_failure("403 Client Error: Forbidden"))

    def test_401_detected(self):
        self.assertTrue(rfe._is_auth_failure("401 Client Error: Unauthorized"))

    def test_429_not_auth(self):
        self.assertFalse(rfe._is_auth_failure("429 Client Error: Too Many Requests"))

    def test_network_error_not_auth(self):
        self.assertFalse(rfe._is_auth_failure(
            "Max retries exceeded with url: /openai/v1/chat/completions "
            "(Caused by NameResolutionError(...))"))

    def test_empty_error_not_auth(self):
        self.assertFalse(rfe._is_auth_failure(""))
        self.assertFalse(rfe._is_auth_failure(None))


class TestCaseAuthAbort(unittest.TestCase):
    """Test _case() returns is_auth_failure=True on 403."""

    def setUp(self):
        self.text = "The system shall authenticate users within 200ms."
        self.rules_v = Mock()
        self.rules_v.validate_text.return_value = {
            "raw_defects": [], "defects": [],
        }

    def _make_llm_mock(self, side_effect):
        llm = Mock()
        llm.validate_requirement.side_effect = side_effect
        return llm

    def test_403_returns_auth_failure(self):
        llm = self._make_llm_mock(Exception("403 Client Error: Forbidden"))
        out, is_auth = rfe._case(self.text, llm, self.rules_v)
        self.assertTrue(is_auth, "expected is_auth_failure=True for 403")
        self.assertFalse(out["llm"]["llm_used"])
        self.assertTrue(out["llm"]["llm_failed"])
        self.assertFalse(out["hybrid"]["llm_used"])
        self.assertTrue(out["hybrid"]["llm_failed"])

    def test_401_returns_auth_failure(self):
        llm = self._make_llm_mock(Exception("401 Client Error: Unauthorized"))
        out, is_auth = rfe._case(self.text, llm, self.rules_v)
        self.assertTrue(is_auth, "expected is_auth_failure=True for 401")

    def test_429_not_auth_failure(self):
        llm = self._make_llm_mock(Exception("429 Client Error: Too Many Requests"))
        out, is_auth = rfe._case(self.text, llm, self.rules_v)
        self.assertFalse(is_auth, "429 is rate-limit, not auth failure")

    def test_network_error_not_auth_failure(self):
        llm = self._make_llm_mock(Exception(
            "Max retries exceeded ... NameResolutionError(...)"
        ))
        out, is_auth = rfe._case(self.text, llm, self.rules_v)
        self.assertFalse(is_auth)


class TestConsecutiveAuthAbort(unittest.TestCase):
    """Simulate the main loop: abort after 3 consecutive 403s."""

    def test_aborts_after_three_consecutive_403(self):
        """After 3 consecutive 403s, consecutive_auth_failures >= 3."""
        consecutive = 0
        errors = [
            "403 Client Error: Forbidden",
            "403 Client Error: Forbidden",
            "403 Client Error: Forbidden",
        ]
        for err in errors:
            if rfe._is_auth_failure(err):
                consecutive += 1
            else:
                consecutive = 0
            if consecutive >= 3:
                break
        self.assertEqual(consecutive, 3)

    def test_no_abort_with_intervening_success(self):
        """A non-auth error between 403s resets the counter."""
        consecutive = 0
        errors = [
            "403 Client Error: Forbidden",
            "403 Client Error: Forbidden",
            "429 Client Error: Too Many Requests",  # resets counter
            "403 Client Error: Forbidden",
        ]
        for err in errors:
            if rfe._is_auth_failure(err):
                consecutive += 1
            else:
                consecutive = 0
        self.assertEqual(consecutive, 1, "counter should reset after non-auth failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
