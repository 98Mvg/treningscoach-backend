# 2026-03-05 Session Learnings — Watch Capability Hardening + Short-Line Audit

## Scope completed
1. Hardened WatchConnectivity behavior on iPhone using a single deterministic watch-capability model.
2. Removed watch transport attempts when watch integration is unavailable (unsupported/not paired/not installed).
3. Audited current coaching phrase length limits and actual catalog max word counts (excluding Talk to Coach content behavior changes).

## What was implemented
1. Watch capability state model in iOS transport layer
   - Added `WatchCapabilityState` in `PhoneWCManager`:
     - `noWatchSupport`
     - `watchNotInstalled`
     - `watchInstalledNotReachable`
     - `watchReady`
   - Added `canUseWatchTransport` guard (`isPaired && isWatchAppInstalled`).
   - Added `onSessionStateChanged` callback and structured capability logging.

2. Hard WC transport gating
   - `sendStartRequest` now branches by capability:
     - `watchReady` -> `sendMessage`
     - `watchInstalledNotReachable` -> `updateApplicationContext` + local fallback
     - `noWatchSupport` / `watchNotInstalled` -> local-only (`watch_unavailable`), no WC sync API call
   - `sendWorkoutStopped` now exits early when transport is unavailable and logs `WATCH_NOTIFY_SKIPPED`.

3. WorkoutViewModel made capability-driven
   - Added published `watchCapabilityState` and bound launch/start/stop behavior to it.
   - Start flow now only enters watch request path for:
     - `watchReady`
     - `watchInstalledNotReachable`
   - No-watch states now start locally directly and skip watch notify on stop.

4. Launch UX alignment to real capability
   - Start CTA uses “Start på Watch / Start on Watch” only when `watchReady`.
   - Reachability helper text appears only for `watchInstalledNotReachable`:
     - `Åpne TreningsCoach på Apple Watch for live puls.`
   - No helper text for no-watch states.
   - No “No live HR” pre-start subtext when neither watch-ready nor BLE-connected.

## Phrase-length and runtime limit findings (today)
1. Runtime/generation limits currently in code:
   - Realtime coaching validation: `1-15` words.
   - Strategic validation: `2-30` words.
   - Zone LLM rewrite cap: `ZONE_EVENT_LLM_REWRITE_MAX_WORDS=16`.
2. Current max actual phrase lengths in `PHRASE_CATALOG` (non-talk lines):
   - EN max: `20` words (`zone.hr_poor_enter.1`)
   - NO max: `19` words (`zone.hr_poor_enter.1`)
3. Non-talk lines over 4 words today: `136` entries.
4. No short-line enforcement migration was applied in this pass; this is queued for the next session.

## Test/build verification in this session
1. Targeted contracts:
```bash
pytest -q tests_phaseb/test_canonical_event_contract.py tests_phaseb/test_watch_connectivity_contract.py tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_watch_capability_gating_contract.py
```
Result: `58 passed`

2. iOS generic build (no signing):
```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build
```
Result: `BUILD SUCCEEDED`

## Next session start point (tomorrow)
1. Implement the short-line policy for all non-talk coaching lines with chosen cap.
2. Keep Talk to Coach behavior separate from workout cue word limits.
3. Regenerate phrase assets and manifest after catalog edits.
