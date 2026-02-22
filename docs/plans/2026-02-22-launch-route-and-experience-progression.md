# 2026-02-22 - Launch Route + Experience Progression

## What shipped

- Backend homepage now always renders `index_launch.html` for launch funnel focus.
- Applied in both runtime paths:
  - `main.py`
  - `backend/main.py`
- Synced template so backend copy can render launch page too:
  - `backend/templates/index_launch.html` (copied from root template)

## Experience leveling (gamification)

- New users now start at `beginner` by default.
- Onboarding setup now communicates auto-leveling instead of manual level selection.
- Home screen now shows experience progression:
  - current level badge (`Beginner`/`Intermediate`/`Advanced`)
  - progress bar toward next level
  - "good workouts to next level" line
- Level progression is based on "good-quality workouts":
  - workout duration >= 12 min
  - CoachScore >= 80
- Good workout thresholds for level-up:
  - `intermediate` at 4 good workouts
  - `advanced` at 12 good workouts

## Keys used

- `training_level`
- `good_coach_workout_count`

## Guardrails preserved

- Coach decisions / event-motor logic unchanged.
- Persona behavior contract unchanged (only UI name `Performance Mode` for `toxic_mode` label).

## Verification

- Backend syntax check:
  - `python3 -m py_compile main.py backend/main.py`
  - Result: passed
- iOS compile:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - Result: `BUILD SUCCEEDED`
