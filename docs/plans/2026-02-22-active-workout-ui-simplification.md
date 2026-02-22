# 2026-02-22 - Active Workout UI Simplification

## What changed

- Removed user-facing `HR NOT CONNECTED` text from workout screens.
- HR status chip now renders only when `watchConnected == true`.
- In active workout, start/stop controls were consolidated into the orb:
  - tap orb: pause/resume
  - long-press orb: stop workout
- Removed extra in-workout control text (phase pills and coaching toggle text) for a cleaner visual surface.
- Mic CTA made more visible with larger button + pulse ring.
- Workout launch input card no longer shows "Apple Watch not connected" when no watch is present.

## Product intent preserved

- Coaching/event motor logic unchanged.
- Backend signal handling and HR quality behavior unchanged.
- UI simplification only.

## Files

- `TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift`
- `TreningsCoach/TreningsCoach/Views/Tabs/WorkoutLaunchView.swift`

## Verification

- iOS compile:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - Result: `BUILD SUCCEEDED`
