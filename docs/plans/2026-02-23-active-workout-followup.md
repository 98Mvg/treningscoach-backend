# 2026-02-23 - Active Workout Follow-Up (Phase 3 Continuation)

## Goal

Continue yesterday's iOS runtime stabilization and Phase 3 sensor handling work.

## Changes shipped

### 1) Active workout UI simplification

- Removed coach guidance text line from the main active-workout surface.
- Kept the workout screen focused on:
  - orb/timer control
  - elapsed time
  - HR pill (when watch is connected)
  - mic + Spotify controls

File:
- `TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift`

### 2) More reliable diagnostics panel opening

- Replaced in-canvas diagnostics overlay rendering with sheet presentation bound to `showDiagnostics`.
- Mic long-press still routes to Pulse tab and opens diagnostics, but visibility is now more robust.

File:
- `TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift`

### 3) Phase 3 HR quality request fix

- Fixed outbound tick quality selection:
  - before: `hrQuality=good` whenever watch connected + HR present
  - now: `hrQuality` respects current signal quality state (`good`/`poor`) and source availability
- Added helper `resolvedHRQualityForRequest(...)`.

File:
- `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift`

## Tests

- Added/updated:
  - `tests_phaseb/test_workout_ui_gesture_contract.py`
  - `tests_phaseb/test_phase3_hr_quality_contract.py` (new)

Run:
- `pytest -q tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_phase3_hr_quality_contract.py`
  - Result: `5 passed`

## Build verification

- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - Result: `BUILD SUCCEEDED`

## Remaining step

- Device validation still needed on physical iPhone:
  - confirm mic long-press opens panel every time
  - confirm no accidental stop when using mic control
  - confirm no NaN/CoreGraphics warnings reappear in active workout flow
