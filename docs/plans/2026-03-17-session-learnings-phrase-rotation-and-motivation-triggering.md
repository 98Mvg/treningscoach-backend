## Session learnings — 2026-03-17 phrase rotation and motivation triggering

### What changed

- Kept the current single runtime path for workout cues:
  - active phrase truth stays in `phrase_review_v2.py`
  - backend deterministic selection stays in `zone_event_motor.py`
  - iOS keeps using backend-provided `phrase_id` in `WorkoutViewModel.swift`
- Added a lightweight runtime event->phrase map builder in `phrase_review_v2.py` so backend phrase selection can follow the active V2 review rows directly.
- Extended `zone_event_motor.py` so the selected primary event can rotate between multiple active variants for the same review-event bucket instead of hardcoding `.1` forever.

### Why this was needed

- Motivation already had anti-repeat and staged pools.
- Regular context/instruction cues like `main_started`, `entered_target`, and `exited_target_above` did not.
- Because iOS already prefers backend `phrase_id`, the cleanest fix was to make backend choose among the active V2 variants instead of adding client-side rotation.

### Motivation timing that already exists

- Interval motivation:
  - only in `work`
  - only when HR is valid and targets are enforced
  - only after the first 10 seconds of the rep
  - only after a sustained in-zone window
  - limited by rep-duration-based slot/budget logic
- Easy-run motivation:
  - only in main/easy-run path with valid in-zone HR
  - only after sustain threshold
  - respects easy-run cooldown between motivation cues
- Higher-priority cues suppress motivation in the same tick.

### Guardrail

- If a cue family already has multiple active variants in `phrase_review_v2.py`, treat backend phrase selection as the only rotation owner.
- Do not add a separate iOS-side phrase-rotation policy for the same cue family.
