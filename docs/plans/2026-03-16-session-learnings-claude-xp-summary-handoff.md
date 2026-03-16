# Session Learnings — Claude XP Summary Handoff

Date: 2026-03-16

## Why this note exists

- Claude should treat the XP summary fix as an existing runtime contract, not as an open redesign problem.
- The bug was not just "XP text missing". The real failure was that the summary screen was reading live workout state after the workout flow had already started resetting that state.

## User-visible bug

- After a workout finished, the summary screen could show missing or unstable XP, duration, and final BPM.
- The UI sometimes fell back to partially reset live values instead of the final completed workout values.

## Root cause

- [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) originally depended too directly on live state from [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift).
- During `stopContinuousWorkout()`, the workout lifecycle could clear or mutate live values before the summary UI finished reading them.
- That meant the summary screen was racing the reset path.

## Correct runtime path now

1. Workout ends in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift).
2. `applyCoachiProgression(durationSeconds:)` computes XP using qualified workout duration.
3. `captureWorkoutCompletionSnapshot(...)` freezes the final summary state into `completedWorkoutSnapshot`.
4. [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) prefers that snapshot for:
   - XP award / ring animation
   - final duration text
   - final BPM text
   - summary telemetry context
5. Only if the snapshot is absent should the UI fall back to the older live values.

## Files that define the contract

- [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
  - owns `completedWorkoutSnapshot`
  - owns `postWorkoutSummaryContext`
  - owns `applyCoachiProgression(durationSeconds:)`
  - owns `captureWorkoutCompletionSnapshot(...)`
- [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift)
  - defines `WorkoutCompletionSnapshot`
- [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)
  - renders the summary from the frozen snapshot
- [Config.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Config.swift)
  - no longer carries the old `minCoachScoreForXPAward` threshold
- [test_coachi_progress_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coachi_progress_contract.py)
  - locks the snapshot path and duration-only XP logic
- [test_coach_score_visual_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coach_score_visual_contract.py)
  - locks the summary ring / XP rendering path

## Important product rule

- XP is now duration-driven on the current Coachi path.
- Do not reintroduce a summary-time coach-score gate for XP unless product explicitly changes that rule again.

## Guardrails for Claude

- Do not create a second summary model or a second XP architecture.
- Keep the single existing runtime path: workout end -> snapshot -> summary screen.
- If summary UI needs more fields, extend `WorkoutCompletionSnapshot` instead of re-reading mutable live workout state.
- If the workout stop flow is refactored, preserve this order:
  1. compute progression
  2. freeze snapshot
  3. allow reset/cleanup paths
- If a UI tweak changes XP presentation, keep the snapshot-backed data source intact.

## Verification already done

- `pytest -q tests_phaseb/test_coachi_progress_contract.py tests_phaseb/test_coach_score_visual_contract.py`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`

## What Claude should assume going forward

- If XP is "missing" again, first inspect whether the summary is reading from `completedWorkoutSnapshot`.
- If duration/BPM/XP look inconsistent, first inspect the ordering inside `stopContinuousWorkout()`.
- If a test fails around summary XP, treat that as a regression in the snapshot contract before changing product rules.
