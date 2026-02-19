# 2026-02-19 - Phase Status and Spotify Decision

## Product phase status (locked)

1. Voice + language quality (NO/EN): **DONE**
2. Event motor (deterministic coaching): **DONE**
3. Sensor layer (HR/cadence + fallback): **DONE**

Remaining:

4. Intelligence layer (LLM for phrasing only, never decisions): **DONE**
5. Personalization (recovery baseline, thresholds, habits): **DONE**
6. Modes/programs + late UX integrations: **DONE**

## Phase 3 completion notes

- Pause detection is robust and deterministic:
  - movement low + HR falling (when HR quality is good)
  - safe fallback on rapid HR drop when movement signal is missing
- Sustained corrective logic is active:
  - `below_zone_push` for sustained under-target while moving
  - `above_zone_ease` for sustained over-target with rising HR/breath stress
- Added telemetry fields:
  - `hr_delta_bpm`
  - `zone_duration_seconds`

## New product decision: Spotify integration timing

- Spotify integration is explicitly deferred to a **late phase** (after Phase 3).
- It belongs under **Phase 6** scope (mode polish + ecosystem UX), not in core event logic.
- UI requirement captured:
  - Add a small **Spotify** icon/button in active workout UI to control background music flow.

## Guardrail

- Spotify must not modify coaching decisions, cooldowns, or scoring.
- It is a UX/media integration only.

## 2026-02-19 completion update

- Phase 4 shipped as an optional phrasing layer:
  - deterministic zone event text is the source of truth
  - optional LLM rewrite is wording-only and timeout-protected
  - fallback is always deterministic template text
- Phase 5 shipped as an insight layer:
  - recovery baseline tracking is stored per profile id
  - next-time tips and recovery line are generated from zone metrics
  - no personalization data changes event decisions/cooldowns/scoring
- Phase 6 shipped with product polish:
  - launch flow includes Easy Run + Intervals + Strength (coming soon)
  - post-workout summary includes CoachScore vibe, why bullets, and next-time advice
  - active workout has Spotify quick-access button (background music UX)
