# Unified Event Router Phase 1 Learnings (2026-02-26)

## Single source of truth
- Workout speech authority for `easy_run` and `interval` must come from backend `events[]`.
- iOS should only use legacy `should_speak/audio_url` when `events[]` is empty.
- Keep `standard` mode on legacy path until phased migration is complete.

## Compatibility lessons
- Preserve legacy `event_type` for existing tests/analytics, even when canonical event routing is enabled.
- Canonical `events[]` can coexist with legacy fields during rollout without creating parallel runtime logic.

## Sensor fallback behavior (Phase 1)
- `FULL_HR` => zone cues allowed.
- `BREATH_FALLBACK` / `NO_SENSORS` => notices + phase/countdown only (no fallback coaching cues).
- Notices must be once-per-session to avoid repetition fatigue.

## Stability guards
- HR loss/restored must use streak thresholds (`>=4s` lost, `>=5s` restored).
- Countdowns must be once per `(phase_id, threshold)` and pause-safe.
- Contract rule: `hr_bpm` is always `0` when HR is unavailable.

## Rollout
- Use flags: `UNIFIED_EVENT_ROUTER_ENABLED`, `UNIFIED_EVENT_ROUTER_SHADOW`, `IOS_EVENT_SPEECH_ENABLED`.
- Keep logs aligned with spoken output to avoid debugging mismatches.
