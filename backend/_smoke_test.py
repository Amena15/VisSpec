"""Protocol step 4 smoke test: send one requirement through LLMValidator and
print HTTP/API success, the actual model id returned by the API, parsed defects
with raw confidence + evidence, and llm_used. Stop if llm_used is false.
Run from repo root: python3 backend/_smoke_test.py
Exit codes: 0 = pass, 2 = LLM did not genuinely answer.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Only import config-derived values; never print the key.
from backend.core.config import settings
from backend.services.ai.llm_validator import LLMValidator, PROMPT_SHA256

REQ = "The system shall be fast and user-friendly."

print("=" * 70)
print("SMOKE TEST (protocol step 4)")
print("=" * 70)
print(f"Profile (LLM_PROFILE) : {settings.LLM_PROFILE}")
print(f"Endpoint host         : {settings.llm_host}")
print(f"Configured model      : {settings.llm_model_id}")
print(f"Prompt SHA-256        : {PROMPT_SHA256[:16]}...")
print(f"Key present           : {bool(settings.LLM_API_KEY)} (length only, never printed)")
print(f"Confidence threshold  : {settings.MIN_CONFIDENCE_THRESHOLD} (BR-10, applied in code)")
print(f"Requirement           : {REQ!r}")
print("-" * 70)

v = LLMValidator()
result = v.validate_requirement(REQ)

llm_used = result.get("llm_used")
model_returned = result.get("model_returned")
print(f"llm_used              : {llm_used}")
print(f"json_parse_ok         : {result.get('json_parse_ok')}")
print(f"model_returned        : {model_returned}")
print(f"model_used            : {result.get('model_used')}")
if result.get("error"):
    # Errors are already PII-redacted by LLMValidator; print as-is.
    print(f"error (redacted)      : {result['error']}")

raw_defects = result.get("defects", [])
filtered = result.get("filtered_defects", [])
print(f"defects parsed (raw)  : {len(raw_defects)}")
print(f"passing BR-10 (>=0.70): {len(filtered)}")
for d in raw_defects:
    print(f"   - type={d.get('type')} severity={d.get('severity')} "
          f"raw_confidence={d.get('confidence')} evidence={str(d.get('evidence',''))[:50]!r} "
          f"desc={str(d.get('description',''))[:50]!r}")

print("-" * 70)
# Three gates, all mandatory before any evaluation run:
if not llm_used:
    print("SMOKE TEST FAILED: llm_used is false -> STOP (protocol step 4).")
    print("The LLM path did not produce a verdict; do NOT run the evaluation")
    print("as if the LLM/Hybrid numbers were LLM-produced.")
    sys.exit(2)
if model_returned != settings.llm_model_id:
    print(f"SMOKE TEST FAILED: model returned '{model_returned}' != configured "
          f"'{settings.llm_model_id}' -> STOP. The evaluation would not be of "
          "the model we claim.")
    sys.exit(2)
if not raw_defects:
    print("SMOKE TEST FAILED: JSON parsed but zero defects returned for an")
    print("obviously defective requirement -> likely empty/truncated answer. STOP.")
    sys.exit(2)
print(f"SMOKE TEST PASSED: llm_used=true, model_returned='{model_returned}' "
      f"matches configured, JSON parsed, {len(raw_defects)} defects.")
sys.exit(0)
