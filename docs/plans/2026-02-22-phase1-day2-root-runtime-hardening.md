# 2026-02-22 - Phase 1 (Day 2) Root Runtime Hardening

## Scope shipped

- Hardened root-only backend runtime policy with executable guard checks.
- Converted `backend/start.sh` from obsolete FastAPI launcher to legacy alias for `backend/start_backend.sh`.
- Added source-of-truth validation script and wired it into release checks.
- Added targeted tests to prevent regressions back to backend-runtime duplication.

## Files changed

- `backend/start.sh`
- `scripts/check_root_runtime.sh` (new)
- `scripts/release_check.sh`
- `tests_phaseb/test_root_runtime_source_of_truth.py` (new)
- `move_huggingface_to_ssd.sh`
- `CLAUDE.md`

## Behavior

### Root runtime guard

Run manually:

```bash
./scripts/check_root_runtime.sh
```

It verifies:

1. `Procfile` points to `gunicorn main:app`
2. `backend/main.py` is compatibility shim importing root app
3. `backend/start_backend.sh` launches root `main.py`

### Release checklist integration

`./scripts/release_check.sh` now runs root-runtime guard first before remote endpoint checks.

### Legacy launcher behavior

`backend/start.sh` now delegates to `backend/start_backend.sh` instead of trying to run stale FastAPI flow.

## Verification

- Shell syntax:
  - `bash -n backend/start.sh backend/start_backend.sh scripts/check_root_runtime.sh scripts/release_check.sh`
- Source-of-truth guard:
  - `./scripts/check_root_runtime.sh`
- Tests:
  - `pytest -q tests_phaseb/test_root_runtime_source_of_truth.py tests_phaseb/test_config_env_overrides.py tests_phaseb/test_api_contracts.py tests_phaseb/test_waitlist_persistence.py`

## Notes

- This is a hardening pass only; no coaching logic changed.
- Existing `datetime.utcnow()` deprecation warnings remain unchanged.
