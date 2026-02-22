# 2026-02-22 - Phase 1 (Day 1) Waitlist Persistence

## Scope shipped

- Replaced in-memory waitlist capture with persistent DB storage.
- Added DB-backed per-IP rate limiting window for `/waitlist`.
- Preserved idempotent behavior for duplicate emails (returns success with `duplicate=true`).
- Applied in both runtime paths (root and backend mirror).

## Files changed

- `database.py`
- `backend/database.py`
- `main.py`
- `backend/main.py`
- `tests_phaseb/test_waitlist_persistence.py`

## Behavior

- `/waitlist` now writes `email`, `language`, `source`, `ip_hash`, `created_at` to `waitlist_signups`.
- Rate limit: max 5 signups per `ip_hash` per rolling 1 hour window.
- Duplicate email:
  - Response `200` with `{ "success": true, "duplicate": true }`
  - No additional row written.

## Verification

- Compile check:
  - `python3 -m py_compile main.py backend/main.py database.py backend/database.py`
- Tests:
  - `pytest -q tests_phaseb/test_waitlist_persistence.py tests_phaseb/test_api_contracts.py`
  - Result: `8 passed`

## Note

- Pytest warnings include `datetime.utcnow()` deprecation from existing UTC-naive timestamp usage. This is non-blocking and can be cleaned in a dedicated UTC-hardening pass.
