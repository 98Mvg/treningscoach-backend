# 2026-02-22 - Spotify Connect UI (iOS)

## What shipped

- Active workout now uses a branded Spotify quick-access button.
- Tapping Spotify when not connected opens a full-screen Spotify connect flow.
- Tapping Spotify when connected opens Spotify directly.
- Connection state is persisted locally with `UserDefaults` key `spotify_connected`.
- New users now get a one-time Spotify prompt after onboarding/account setup.
- Home tab now shows Spotify connection state and allows connect/open from home.
- Workout center status area is simplified to only HR status:
  - green dot + `HR <bpm>` when reliable
  - `HR NOT CONNECTED` when not reliable
- Removed on-screen coach text line from active workout view (voice-only coaching).
- UI label rename shipped: `Toxic Mode` -> `Performance Mode` (raw backend persona key unchanged).

## Guardrail preserved

- This is a media UX layer only.
- Coaching logic, event motor decisions, cooldowns, and scoring are unchanged.

## Files touched

- `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift`
- `TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift`
- `TreningsCoach/TreningsCoach/Views/ContentView.swift`
- `TreningsCoach/TreningsCoach/ViewModels/AppViewModel.swift`
- `TreningsCoach/TreningsCoach/Services/AuthManager.swift`

## Notes / limits (current MVP)

- Current connect flow is UX-first and does not yet perform Spotify OAuth token exchange.
- "Connected" state is local app state for now.
- Prompt keys used:
  - `spotify_prompt_pending`
  - `spotify_prompt_seen`

## Verification

- Built iOS target successfully:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build`
  - Result: `BUILD SUCCEEDED`

## Next optional increment

1. Implement Spotify OAuth Authorization Code with PKCE.
2. Store refresh token securely in Keychain.
3. Replace local `spotify_connected` flag with real token validity checks.
