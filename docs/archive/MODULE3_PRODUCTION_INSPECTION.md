# Module 3 Production Inspection (AI Validation)

## Result
- Inspection completed for validation API + validator pipeline.
- Production hardening fixes applied.
- Regression status:
  - Module 3 tests: 11 passed, 2 skipped
  - Module 2 tests: 4 passed, 17 skipped

## Issues Found And Fixed

1. Error masking in validation endpoints (HIGH)
- Problem:
  - Validation routes returned synthetic success-like payloads on internal errors, which could hide backend failures and show false perfect results.
- Fix:
  - Replaced fallback success payload behavior with explicit HTTP errors.
  - Added structured exception logging for diagnostics.
- File:
  - [backend/api/validation.py](backend/api/validation.py)

2. Confidence threshold mismatch (MEDIUM)
- Problem:
  - Defects were filtered using `>` while BR-10 and other code paths use `>=` threshold semantics.
- Fix:
  - Changed filtering to `>= settings.MIN_CONFIDENCE_THRESHOLD` for consistency.
- File:
  - [backend/api/validation.py](backend/api/validation.py)

3. Unsafe test endpoints exposed in production (HIGH)
- Problem:
  - `/api/validation/test-validation-no-auth/{doc_id}` and `/api/validation/test-validation/{doc_id}` were always available.
- Fix:
  - Added debug-only guard via `_ensure_test_routes_enabled()` and return 404 when `DEBUG=False`.
- File:
  - [backend/api/validation.py](backend/api/validation.py)

4. Potential DB integrity failure from unmapped defects (MEDIUM)
- Problem:
  - `Defect.req_id` is non-nullable. If mapping fails, DB write can fail.
- Fix:
  - Added explicit skip + warning log for defects that cannot be mapped to a requirement.
- File:
  - [backend/api/validation.py](backend/api/validation.py)

## Additional Improvements Included
- Added consistent exception logging (`logger.exception`) in key validation routes.
- Kept existing API contracts for successful flows while making failure states explicit.

## Verification Performed
- [backend/tests/unit/test_module3_ai_validation.py](backend/tests/unit/test_module3_ai_validation.py)
  - 11 passed, 2 skipped
- [backend/tests/unit/test_module2_document_processing.py](backend/tests/unit/test_module2_document_processing.py)
  - 4 passed, 17 skipped

## Residual Risks / Next Steps
1. Add integration tests for validation endpoints under authenticated async DB fixtures:
- Validate `/validate-document` error states (DB failure, ownership, missing doc).
- Validate test endpoints are inaccessible when `DEBUG=False`.

2. Normalize defect `severity` case across rule-based and LLM paths:
- Current code expects lowercase in counting logic.
- Ensure any external LLM response is normalized before persistence.

3. Add structured metrics for skipped unmapped defects:
- Track count and rate to detect parser/mapper quality regressions.
