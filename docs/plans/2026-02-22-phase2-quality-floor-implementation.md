# 2026-02-22 - Phase 2: Coaching Quality Floor Implemented

## Scope shipped

- Enabled quality-floor enforcement defaults in runtime config.
- Added selective breathing timeline enforcement so deterministic zone-event text keeps priority.
- Added lightweight quality guard counters for validation/timeline/language guard behavior.
- Exposed quality counters in `/health` for fast production monitoring.
- Added tests for validation fallback and timeline-vs-zone priority contract.

## Files changed

- `config.py`
- `main.py`
- `.env.example`
- `backend/.env.example`
- `scripts/release_check.sh`
- `tests_phaseb/test_phase2_quality_floor.py` (new)
- `tests_phaseb/test_api_contracts.py`

## Runtime behavior changes

### 1) Enforcement defaults

- `COACHING_VALIDATION_ENFORCE` default changed to `True`.
- `BREATHING_TIMELINE_ENFORCE` default changed to `True`.

Both remain environment-overridable for emergency rollback.

### 2) Selective timeline enforcement

When timeline has a cue and enforce mode is on:
- Timeline cue will override only if no deterministic zone event text is active.
- If zone-event text is active, timeline override is skipped and zone text is preserved.

This protects event-motor determinism while keeping phase-appropriate breathing guidance.

### 3) Health observability

`/health` now includes `quality_guards` with counters/rates:

- `validation_checks`
- `validation_failures`
- `validation_template_fallbacks`
- `timeline_cue_candidates`
- `timeline_overrides`
- `timeline_zone_priority_skips`
- `language_guard_rewrites`
- `validation_failure_rate`
- `validation_template_fallback_rate`

## Verification

- Compile:
  - `python3 -m py_compile main.py config.py`
- Tests:
  - `pytest -q tests_phaseb/test_phase2_quality_floor.py tests_phaseb/test_api_contracts.py tests_phaseb/test_config_env_overrides.py tests_phaseb/test_waitlist_persistence.py`
  - Result: `17 passed`

## Rollback knobs

If needed, disable with env vars (no code rollback required):

- `COACHING_VALIDATION_ENFORCE=false`
- `BREATHING_TIMELINE_ENFORCE=false`

## Notes

- Existing `datetime.utcnow()` deprecation warnings are unchanged and pre-existing.
- No event-motor scoring/cooldown logic was changed in this phase.
