# 2026-02-22 - Phase 1 (Day 2) Release Safety + Launch Locks

## Scope shipped

- Added a reusable release validation script for production smoke checks.
- Locked launch behavior via environment defaults in `.env.example` (root + backend mirror).
- Made `DEFAULT_LANGUAGE` and `MIN_SIGNAL_QUALITY_TO_FORCE` environment-driven in runtime config.
- Updated runtime endpoints to use `config.DEFAULT_LANGUAGE` as API default where language is omitted.
- Kept root/backend runtime files synchronized.

## Files changed

- `scripts/release_check.sh`
- `config.py`
- `backend/config.py`
- `main.py`
- `backend/main.py`
- `.env.example`
- `backend/.env.example`
- `tests_phaseb/test_config_env_overrides.py`

## Behavior

### Release check script

Run:

```bash
./scripts/release_check.sh
```

Optional overrides:

- `BASE_URL` (default: `https://treningscoach-backend.onrender.com`)
- `EXPECT_APP_STORE_URL`
- `EXPECT_GOOGLE_PLAY_URL`

Checks performed:

1. `/health` returns healthy status
2. `/coach/continuous` rejects empty payload with `400`
3. `/waitlist` accepts new signup
4. `/welcome` (NO) returns text + audio URL
5. `/` includes tracked download CTA events

### Launch lock defaults

`.env.example` now includes:

- `DEFAULT_LANGUAGE=no`
- `USE_HYBRID_BRAIN=false`
- `USE_STRATEGIC_BRAIN=false`
- `COACHING_VALIDATION_ENFORCE=true`
- `BREATHING_TIMELINE_ENFORCE=false`
- `MIN_SIGNAL_QUALITY_TO_FORCE=0.0`

### Runtime default-language behavior

When language is omitted in API payload/query, backend now uses `config.DEFAULT_LANGUAGE` for:

- `/welcome`
- `/coach`
- `/coach/continuous`
- `/coach/talk`
- `/waitlist`
- `/workouts` (save path language field default)

## Verification

- Compile:
  - `python3 -m py_compile config.py backend/config.py main.py backend/main.py`
- Tests:
  - `pytest -q tests_phaseb/test_config_env_overrides.py tests_phaseb/test_api_contracts.py tests_phaseb/test_waitlist_persistence.py`
  - Result: `15 passed`

## Notes

- Existing UTC-naive `datetime.utcnow()` deprecation warnings remain (pre-existing), unchanged in this slice.
- Root/backend mirror still exists; full mirror elimination is still pending as a separate migration step.
