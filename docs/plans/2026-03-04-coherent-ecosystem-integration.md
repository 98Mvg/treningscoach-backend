# Coherent Ecosystem Integration (2026-03-04)

## Scope
- Keep one runtime path: `/coach/continuous -> evaluate_zone_tick`.
- Keep `breath_analyzer.py` audio-only.
- Keep iOS event-first playback and talk arbitration.

## Enabled Rollout Flags
- `CONTINUOUS_CONTRACT_V2_ENABLED`
- `PROFILE_DB_ENABLED`
- `SERVER_CLOCK_ENABLED`
- `SENSOR_MODE_TABLE_V2_ENABLED`
- `COUNTDOWN_ENGINE_ONLY_ENABLED`
- `CONTINUOUS_FAILSAFE_ENABLED`
- `TALK_CONTEXT_SUMMARY_ENABLED`
- `AUDIO_PREFETCH_ENABLED`

## Runtime Policies
- Server-authoritative elapsed clock for continuous ticks, with client-ahead resync guard.
- Profile precedence:
  1. Newer valid snapshot
  2. Stored DB profile
  3. Valid snapshot
  4. Safe defaults
- Sensor modes:
  - `FULL_HR`
  - `BREATH_FALLBACK`
  - `NO_SENSORS`
- Countdown ownership:
  - warmup/recovery countdowns emitted only from `zone_event_motor.py`
  - keyed by `phase_id + countdown_kind`

## Talk Policy
- Unified `/coach/talk` for wake button/wake word with trigger-specific timeout budgets.
- Workout context summary is injected into prompt shaping.
- HR truth guardrail:
  - if HR invalid/missing, responses cannot claim BPM values.
- Deterministic progress hints include sets/time-left when present.

## Audio Pack Coverage + Prefetch
- Manifest coverage tests enforce wake/welcome/core zone phrase IDs.
- iOS prefetches core utterances at workout start:
  - wake acknowledgements
  - warmup/countdown core phrases
  - welcome standard variants

## SLO Log Events to Watch
- `CLOCK_CANONICAL`
- `COUNTDOWN_EMIT`
- `PROFILE_RUNTIME`
- `PROFILE_RUNTIME_TALK`
- `FAILSAFE_200`
- `COACH_TALK ... fallback_used=...`
- `Resolving audio source: cached_local_pack|bundled_core|r2_pack|backend_tts`
- `AUDIO_PREFETCH downloaded=... missing=...`
