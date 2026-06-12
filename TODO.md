# TODO - System bug fixing checklist

## Step 1: Fix failing pytest collection
- [ ] Patch `backend/scripts/simple_db_test.py` so it doesn't run at import time (only under `__main__`).
- [ ] Ensure `database`/`models` import paths work during tests (likely switch to absolute imports or guard execution).

## Step 2: Fix traceability note update logic + syntax
- [ ] Ensure `backend/api/traceability.py` indentation and control flow are correct.
- [ ] Fix note update behavior to not incorrectly overwrite `created_at` if a separate `updated_at` is intended.

## Step 3: Fix DB session type consistency
- [ ] Identify all API routers that use `Depends(get_db)` but treat it as sync Session.
- [ ] Either convert those routes to async/`AsyncSession` or provide a sync `get_db`.

## Step 4: Fix validation defect confidence key mismatch
- [ ] Verify validator returns `confidence` (or `confidence_score`) and align filtering in `backend/api/validation.py`.

## Step 5: Run tests
- [ ] Re-run `python -m pytest -q` after each major fix.

