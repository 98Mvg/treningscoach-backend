# Task Plan (Active)

Updated: 2026-02-23

## Working Rules (from workflow image)

- For non-trivial work, write a short checkable plan before implementation.
- Stop and re-plan if execution goes sideways.
- Verify behavior before marking anything done.
- Keep changes minimal and focused on root cause.
- Update this file with progress and review notes.

## Next Session Plan

- [ ] Validate iPhone runtime after NaN hardening.
- [x] Confirm mic long-press behavior and workout stop behavior do not conflict.
- [x] Keep workout UI minimal text and backend diagnostics separated from user-facing UI.
- [x] Continue Phase 3 sensor work (HR/watch quality handling + fallback clarity).
- [x] Re-run focused checks and capture results below.

## Progress Log

- 2026-02-23: Resumed with workflow-orchestration rules from user-provided image.
- 2026-02-23: Active workout screen updated to sheet-based diagnostics panel for more reliable mic long-press open behavior.
- 2026-02-23: Removed coach guidance text line from active workout surface (minimal text UI).
- 2026-02-23: Phase 3 bug fixed: outbound `hrQuality` now respects current signal quality, not just watch-connected status.

## Review Results

- `pytest -q tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_phase3_hr_quality_contract.py`
  - result: `5 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
