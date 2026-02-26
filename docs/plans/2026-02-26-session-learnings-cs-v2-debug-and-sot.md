# 2026-02-26 Session Learnings — CS v2, Debug Logging, and Single Source of Truth

## What changed in this session
- Implemented CS v2 scoring adjustments so score ceilings are earned by available pillars:
  - HR + Duration can reach 100.
  - Breath + Duration can reach 100.
  - HR + Breath + Duration can reach 100.
  - Duration-only cannot reach 100 (duration-only guardrail cap).
- Kept hard rule: workouts under 20 minutes are capped proportionally to 0-20.
- Added deterministic one-line CS summary debug log on each workout tick (`CS_DEBUG_SUMMARY`).
- Added deterministic one-line coach transcript debug log (`COACH_TRANSCRIPT`) for NO/EN tuning.
- Added user-facing improvement hints when sensor coverage is limited.

## Single source of truth (SOT)
- Runtime backend SOT for scoring and debug output is:
  - `main.py` (CS computation + API response + logs)
  - `zone_event_motor.py` (target generation + zone metrics)
  - `config.py` (flags/thresholds)
- iOS display contract consumes backend fields via:
  - `Models.swift`
  - `BackendAPIService.swift`
  - `WorkoutViewModel.swift`
  - `WorkoutCompleteView.swift`
- Avoid adding parallel scoring engines or alternate response schemas.

## No double-work checklist for future tasks
- Before changing scoring, inspect existing `_compute_layered_coach_score_*` paths first.
- Extend existing payload fields before introducing new top-level contracts.
- Add tests to existing `tests_phaseb` scoring/zone contract files; do not duplicate test suites.
- Reuse existing config flags (`COACH_SCORE_VERSION`, debug flags) before adding new toggles.

## Debug tuning outputs now available
- `COACH_TRANSCRIPT`: session, lang, phase, speak decision, reason, source, final text.
- `CS_DEBUG_SUMMARY`: duration, HR valid seconds, zone valid seconds, zone compliance, zone score, breath flags/scores/confidence, raw score, cap applied, winning reason, all reasons, final CS.

## Product guardrails retained
- Warmup targets remain Easy regardless of selected workout intensity.
- Missing HR displays as `0 BPM` (never blank/em-dash).
- Duration is always included in scoring.

## Validation status
- Python scoring/contract tests passed.
- UI contract tests passed.
- iOS debug build passed.
