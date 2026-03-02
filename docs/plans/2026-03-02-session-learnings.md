# Session Learnings - 2026-03-02

## Core architecture decisions
- Keep a single runtime authority for workout speech decisions: `zone_event_motor` via canonical `events[]`.
- In iOS, prefer backend-provided event metadata:
  - `event.priority` is primary for selection order.
  - `event.phraseId` is primary for utterance/audio lookup.
  - Local mappings are fallback-only and must be logged when used.
- Avoid reintroducing parallel legacy ownership in `/coach/continuous`.

## Contract hardening completed
- Speakable backend events must carry both `priority` and `phrase_id`.
- If a speakable primary event violates contract, downgrade deterministically to safe fallback (`max_silence_override`) instead of silent failure.
- If safe fallback cannot be resolved, drop speech safely with explicit reason.

## Max-silence ownership and behavior
- Max silence for workout modes is zone-event owned and context-aware (workout type, phase, elapsed time, HR/breath availability).
- Missing `zone_tick` in `/coach/continuous` now uses strict silent-safe guard:
  - no legacy fallback speech path
  - `decision_owner` remains `zone_event`
  - explicit guard reason/log emitted.

## CI and quality gates
- Added manifest coverage test to fail when any phrase IDs emitted by `zone_event_motor` are missing from active audio pack manifest.
- Added/extended regression tests for:
  - canonical contract fields
  - zone-event max-silence ownership in `events[]`
  - no-legacy-fallback behavior when zone tick is missing.

## Audio pack operations learned
- Keep `latest.json` and active manifest in sync before runtime verification.
- Regenerate and upload audio pack whenever new event phrase IDs are introduced (especially motivation/breath/feel families).
- Verify remote manifest presence before assuming iOS sync issues are app-side.

## Working rules for future edits
- Modify existing runtime path first; do not create parallel architecture.
- Add tests in the same change-set for contract/ownership changes.
- Prefer deterministic event behavior over implicit fallback logic.
