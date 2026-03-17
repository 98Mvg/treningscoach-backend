## Session Learnings — 2026-03-16 Live Voice Tracker Warning

### Symptom
- Xcode logged:
  - `Publishing changes from within view updates is not allowed, this will cause undefined behavior.`
- The warning pointed at [LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift), around the date/count lookup path.

### Root cause
- [LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift) is a shared `ObservableObject` singleton used by [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) and [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift).
- It previously called `synchronize()` from `init()`, and later wrote `sessionsUsedToday` synchronously from `synchronize()` and `recordSession(isPremium:)`.
- When SwiftUI first created or refreshed views around the shared tracker, those synchronous `@Published` writes could happen during an active render/update pass, which triggered the runtime warning.

### Fix
- Seed `sessionsUsedToday` directly in `init()` instead of calling a publish-capable sync method there.
- Keep query methods side-effect free.
- Route later tracker publishes through a small helper that defers the `@Published` assignment with `DispatchQueue.main.async`, so the value change lands after the current view-update cycle.

### Verification
- `pytest -q tests_phaseb/test_live_voice_mode_contract.py` -> `11 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

### Guardrail
- Any shared SwiftUI-facing singleton that uses `@Published` should avoid synchronous publish in `init()` and avoid writing state from helpers that can be called during view evaluation.
