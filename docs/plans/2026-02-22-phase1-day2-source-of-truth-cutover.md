# 2026-02-22 - Phase 1 (Day 2) Source-of-Truth Cutover

## Scope shipped

- Cut backend launch path over to root runtime as the only backend source of truth.
- Converted `backend/main.py` from mirrored runtime code to a compatibility shim that imports root `main.py`.
- Updated backend start script to launch root runtime directly.
- Updated primary architecture/process docs to remove mirror-sync workflow and enforce root-only backend edits.

## Files changed

- `backend/main.py`
- `backend/start_backend.sh`
- `README.md`
- `CLAUDE.md`
- `docs/ARCHITECTURE_SOURCE_OF_TRUTH.md`

## Behavior

### Runtime behavior

- Production remains unchanged (`Procfile` still runs `gunicorn main:app`).
- Legacy local launcher (`backend/start_backend.sh`) now starts:
  - `python3 /Users/mariusgaarder/Documents/treningscoach/main.py`
- `backend/main.py` now acts as compatibility entrypoint and no longer contains independent runtime logic.

### Process behavior

- Backend runtime edits should happen only in root files (`main.py`, `config.py`, `brain_router.py`, `brains/*.py`).
- Mirror-sync commands (`cp backend/*.py .`) are removed from primary operating doc.

## Verification

- Compile:
  - `python3 -m py_compile main.py config.py backend/main.py`
- Tests:
  - `pytest -q tests_phaseb/test_config_env_overrides.py tests_phaseb/test_api_contracts.py tests_phaseb/test_waitlist_persistence.py`
  - Result: `15 passed`

## Notes

- Existing `datetime.utcnow()` deprecation warnings are unchanged and still present.
- This cutover removes the highest-risk drift path (`backend/main.py` runtime duplication) while preserving legacy script compatibility.
