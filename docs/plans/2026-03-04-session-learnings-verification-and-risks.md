# 2026-03-04 Session Learnings — Verification, Risks, and Improvements

## What was verified this session
1. Repo state is clean and synced to `origin/main` before verification.
2. Recent ecosystem integration changes are active in the single runtime path (`/coach/continuous` + `zone_event_motor`).
3. No parallel coaching architecture was introduced.
4. Test-generated artifacts were cleaned and `instance/treningscoach.db` was restored after each run.

## Test runs and outcomes
### Run 1
```bash
pytest -q \
  tests_phaseb/test_server_authoritative_clock.py \
  tests_phaseb/test_workout_context_summary_contract.py \
  tests_phaseb/test_profile_runtime_resolution.py \
  tests_phaseb/test_talk_to_coach_runtime_context.py \
  tests_phaseb/test_brain_router_workout_talk_prompt.py \
  tests_phaseb/test_zone_event_motor.py \
  tests_phaseb/test_zone_continuous_contract.py \
  tests_phaseb/test_talk_to_coach_contract.py \
  tests_phaseb/test_audio_pack_manifest_coverage.py \
  tests_phaseb/test_breath_reliability_single_source.py
```
Result: `59 passed` (warnings only).

### Run 2
```bash
pytest -q \
  tests_phaseb/test_contract_version_schema.py \
  tests_phaseb/test_profile_upsert_contract.py \
  tests_phaseb/test_profile_db_persistence.py \
  tests_phaseb/test_ios_profile_sync_contract.py \
  tests_phaseb/test_canonical_event_contract.py
```
Result: `35 passed` (warnings only).

### Combined verification
- Total tests executed this session: `94 passed`.
- No failures.
- Warnings are known deprecation warnings around `datetime.utcnow()` usage (SQLAlchemy/auth paths).

## Confirmed architecture ownership (re-locked)
1. `zone_event_motor.py` owns event decisions, countdown emission, and SensorMode transitions.
2. `main.py` owns request parsing, compatibility filtering, orchestration, and failsafe response behavior.
3. `breath_analyzer.py` remains audio metrics only; no countdown scheduling ownership.
4. iOS remains event-first for workout speech; talk arbitration suppresses zone playback while talking/listening.

## Top risks (current)
1. **Time API deprecations**: `datetime.utcnow()` warnings in auth/DB paths may become hard failures in future runtime versions.
2. **Contract drift risk**: any future request/response field drift between backend and iOS can silently degrade context quality if tests are not updated together.
3. **Countdown reliability under extreme latency**: coarse network/tick delays can still threaten countdown timing quality unless phase-aware tick budgets stay enforced.
4. **Profile freshness conflicts**: stale or invalid snapshots from client could regress personalization if trust/freshness checks are weakened.
5. **Audio source fallback surprises**: if prefetch coverage slips, runtime can hit R2/backend_tts unexpectedly and increase perceived latency.

## Top improvements (next)
1. Replace remaining `datetime.utcnow()` with timezone-aware UTC in auth/DB code paths.
2. Add a CI “contract gate” bundle that always runs iOS source-contract + backend contract tests together on relevant changes.
3. Add explicit countdown latency telemetry (`countdown_due_ts` vs `emitted_ts`) for production observability.
4. Add profile conflict audit counters (`snapshot_newer`, `db_newer`, `snapshot_rejected`) to logs/metrics.
5. Expand audio prefetch priority list from static core to top-N phrase IDs observed in the last 7 days.

## Operational notes
1. After running tests locally, always restore `instance/treningscoach.db` before commit.
2. Keep session learnings in `docs/plans` and avoid ad-hoc notes outside repo.
