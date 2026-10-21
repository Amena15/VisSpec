"""
main()-level abort-path test for scripts/run_frozen_eval.py.

Exercises the REAL main() code path with a mocked provider so that we can
assert the fatal-auth-abort contract end to end:

  * three consecutive HTTP 403 responses stop the run,
  * main() exits with a NON-ZERO code,
  * the run is marked INCOMPLETE (never COMPLETE),
  * the status/body of the failed response is printed,
  * secret-looking material in the response body is REDACTED before printing,
  * a run with fewer than 3 consecutive auth failures is NOT aborted early.

Only non-frozen driver code is exercised here; no frozen artifact is touched
and no network call is made.
"""
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
    "run_frozen_eval", os.path.join(REPO, "scripts", "run_frozen_eval.py")
)
rfe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rfe)

FORBIDDEN_BODY = (
    '{"error":{"message":"Invalid API key: gsk_LiveSecretKey1234567890ABC",'
    '"type":"invalid_request_error"}}'
)


def _make_settings():
    s = MagicMock()
    s.LLM_PROFILE = "groq-gpt-oss-120b"
    s.llm_model_id = "openai/gpt-oss-120b"
    s.llm_host = "api.groq.com"
    s.LLM_MAX_TOKENS = 4096
    s.LLM_REASONING_EFFORT = "low"
    return s


def _make_llm_validator(side_effect, available=True):
    v = MagicMock()
    v.is_available = available
    v.validate_requirement.side_effect = side_effect
    return v


def _make_rules_validator(defects=None):
    v = MagicMock()
    v.validate_text.return_value = {
        "raw_defects": defects or [], "defects": defects or []}
    return v


def _dataset(n):
    return [{"id": f"TC-{i:03d}", "text": f"Requirement {i} shall do X.",
             "expert_verdict": "NO_DEFECT", "defect_type": None}
            for i in range(1, n + 1)]


def _run_main(side_effect, n_cases=6, rules_defects=None, run_no=99):
    """Invoke rfe.main() against mocks; return (exit_code, stdout, result_file)."""
    tmpdir = tempfile.mkdtemp(prefix="visspec_authabort_")
    dataset = Path(tmpdir) / "ds.json"
    dataset.write_text(json.dumps(_dataset(n_cases)), encoding="utf-8")

    buf = io.StringIO()
    argv = ["run_frozen_eval.py", "--profile", "groq-gpt-oss-120b",
            "--run", str(run_no), "--dataset", str(dataset),
            "--delay", "0", "--out-dir", tmpdir]
    with patch.object(sys, "argv", argv), \
         patch.dict(os.environ, {"LLM_PROFILE": "groq-gpt-oss-120b"}), \
         patch("backend.core.config.settings", _make_settings()), \
         patch("backend.services.ai.llm_validator.LLMValidator",
               return_value=_make_llm_validator(side_effect)), \
         patch("backend.services.validation.validator.Validator",
               return_value=_make_rules_validator(rules_defects)), \
         redirect_stdout(buf):
        rc = rfe.main()

    out = buf.getvalue()
    res = Path(tmpdir) / f"evaluation_results_groq-gpt-oss-120b_run{run_no}.json"
    return rc, out, (res if res.exists() else None), tmpdir



class TestMainAuthAbort(unittest.TestCase):
    """The REAL main() must abort fatally on 3 consecutive 401/403."""

    def test_three_consecutive_403_exits_nonzero_and_marks_incomplete(self):
        rc, out, res, tmp = _run_main(Exception("403 Client Error: Forbidden"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        self.assertNotEqual(rc, 0, "main() must exit non-zero on fatal auth failure")
        self.assertEqual(rc, 2, "INCOMPLETE exit code is 2")
        self.assertIn("status: INCOMPLETE", out)
        self.assertIn("ABORT: 3 consecutive 401/403", out)

        # The run must be persisted as INCOMPLETE, never COMPLETE.
        self.assertIsNotNone(res, "result file should still be written")
        d = json.loads(res.read_text(encoding="utf-8"))
        self.assertEqual(d["status"], "INCOMPLETE")
        self.assertIn("NOT valid LLM results", d["status_note"])

    def test_abort_stops_before_processing_all_cases(self):
        rc, out, res, tmp = _run_main(Exception("403 Client Error: Forbidden"), n_cases=10)
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        progress = [ln for ln in out.splitlines()
                    if ln.startswith("[") and "LLM-FAILED" in ln]
        self.assertEqual(len(progress), 3,
                         f"expected exactly 3 attempted cases before abort, got {progress}")

    def test_status_is_printed(self):
        rc, out, res, tmp = _run_main(Exception("403 Client Error: Forbidden"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.assertIn("403", out, "the 403 status must be printed")
        self.assertIn("AUTH-FAILURE", out)

    def test_response_body_is_printed_and_redacted(self):
        """A requests-style exception carrying a response body prints the body
        with secret material redacted."""
        resp = MagicMock()
        resp.text = FORBIDDEN_BODY
        exc = Exception("403 Client Error: Forbidden for url: https://api.groq.com/v1")
        exc.response = resp

        rc, out, res, tmp = _run_main(exc)
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        self.assertNotEqual(rc, 0)
        self.assertIn("AUTH-FAILURE body", out)
        self.assertIn("Invalid API key", out, "body content should be shown")
        self.assertNotIn("gsk_LiveSecretKey1234567890ABC", out,
                         "raw key material must never be printed")
        self.assertIn("REDACTED", out)

    def test_401_also_aborts(self):
        rc, out, res, tmp = _run_main(Exception("401 Client Error: Unauthorized"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.assertEqual(rc, 2)
        self.assertIn("status: INCOMPLETE", out)
        self.assertIn("ABORT: 3 consecutive 401/403", out)

    def test_failed_llm_calls_are_not_successful_verdicts(self):
        rc, out, res, tmp = _run_main(Exception("403 Client Error: Forbidden"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        d = json.loads(res.read_text(encoding="utf-8"))
        for path in ("llm", "hybrid"):
            for r in d["detailed_results_by_path"][path]:
                self.assertTrue(r["llm_failed"], f"{path}/{r['id']} should be llm_failed")
                self.assertFalse(r["llm_used"])
                self.assertEqual(r["vis_prediction"], "NO_DEFECT")
                self.assertEqual(r["defects_raw"], [])

    def test_rules_results_do_not_fill_failed_llm_only_calls(self):
        """The LLM-only path must not inherit the rules verdict."""
        rc, out, res, tmp = _run_main(
            Exception("403 Forbidden"),
            rules_defects=[{"type": "ambiguity", "confidence": 0.95}], run_no=98)
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        self.assertNotEqual(rc, 0)
        d = json.loads(res.read_text(encoding="utf-8"))
        # The rules path DOES have the defect ...
        self.assertTrue(any(r["vis_prediction"] == "DEFECT"
                            for r in d["detailed_results_by_path"]["rules"]))
        # ... but the llm-only path must NOT.
        for r in d["detailed_results_by_path"]["llm"]:
            self.assertEqual(r["vis_prediction"], "NO_DEFECT")
            self.assertEqual(r["defects_raw"], [])

    def test_non_auth_failure_does_not_abort_early(self):
        """429 is transient: the run continues through all cases."""
        rc, out, res, tmp = _run_main(
            Exception("429 Client Error: Too Many Requests"), n_cases=5)
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.assertEqual(rc, 2, "still INCOMPLETE, but not aborted")
        self.assertNotIn("ABORT: 3 consecutive 401/403", out)
        progress = [ln for ln in out.splitlines() if ln.startswith("[")]
        self.assertEqual(len(progress), 5, "all cases should have been attempted")

    def test_two_consecutive_403_do_not_abort(self):
        """Only the THIRD consecutive auth failure is fatal."""
        calls = {"n": 0}

        def side_effect(_text):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise Exception("403 Client Error: Forbidden")
            return {"defects": [{"type": "ambiguity", "confidence": 0.95}],
                    "filtered_defects": [{"type": "ambiguity", "confidence": 0.95}],
                    "llm_used": True, "json_parse_ok": True,
                    "model_returned": "openai/gpt-oss-120b", "error": None}

        rc, out, res, tmp = _run_main(side_effect, n_cases=5)
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.assertNotIn("ABORT: 3 consecutive 401/403", out)
        self.assertEqual(calls["n"], 5, "the run should have continued past case 2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
