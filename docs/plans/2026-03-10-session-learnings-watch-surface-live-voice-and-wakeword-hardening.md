# 2026-03-10 Session Learnings — Watch Surface, Live Voice Scope, And Wake-Word Handoff

## Scope completed
1. Polished the launch-critical watch surface on the single existing watch runtime path.
2. Kept post-workout live voice isolated from the workout runtime while aligning the summary CTA with the in-workout coach button.
3. Hardened the wake-word -> workout-talk handoff to reduce local speech-recognition churn on device.
4. Clarified the product truth for `Talk to Coach Live` context and updated repo guidance accordingly.

## What shipped
1. Watch launch surface polish
   - Added watch-specific app-icon entries and padded watch icon assets inside the shared `AppIcon.appiconset`.
   - Turned `WatchStartWorkoutView` into a real running dashboard with:
     - large BPM as the primary metric
     - `Live Heart Rate` sublabel
     - secondary remaining/elapsed time
     - direct stop action
   - Extended the existing phone/watch WC payload with a session-plan snapshot so the watch can compute remaining time locally without a new architecture path.

2. Watch transport and device realism
   - Kept the single `PhoneWCManager <-> WatchWCManager` transport path.
   - Preserved request correlation / watch-owned-stop semantics from the previous hardening pass.
   - Confirmed the product truth on device: watch install, watch launch, and HR backfeed can now work on a paired device when the companion app is installed correctly.

3. Live voice UI alignment
   - Restyled the summary-screen `Talk to Coach Live` CTA to match the established workout mic CTA visual language instead of creating a second button style.
   - Kept the same gating, modal presentation, and backend bootstrap behavior.

4. Wake-word handoff hardening
   - `WakeWordManager` now suspends recognition more gracefully for workout-talk capture instead of tearing speech recognition down abruptly.
   - Apple local speech-service interruptions during the handoff are treated separately from true degraded-mode failures.
   - The change is designed to reduce `kAFAssistantErrorDomain Code=1101` log spam during wake-word talk capture on real devices.

5. Truth clarified: `Talk to Coach Live` context
   - Live voice does **not** inject full account history or prior workout history.
   - The current xAI live voice session uses only a sanitized post-workout summary snapshot plus the current realtime session turns.
   - Any broader memory/history behavior must be treated as a future product change, not something that already exists implicitly.

## Verification run in this session
1. Watch/icon/live-voice contracts
```bash
pytest -q tests_phaseb/test_watch_target_contract.py tests_phaseb/test_watch_connectivity_contract.py tests_phaseb/test_watch_request_id_correlation_contract.py tests_phaseb/test_watch_hr_source_arbitration_contract.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_ios_entitlements_signing_guard.py
```
Result: `38 passed`

2. Wake-word capture and live-voice scope contracts
```bash
pytest -q tests_phaseb/test_wakeword_capture_error_contract.py tests_phaseb/test_talk_to_coach_contract.py tests_phaseb/test_live_voice_mode_contract.py
```
Result: `22 passed`

3. iPhone and watch generic builds
```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoachWatchApp -configuration Debug -destination 'generic/platform=watchOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build
```
Result: `BUILD SUCCEEDED` for both targets

## Phase 1-4 snapshot after this session
1. Phase 1 (Voice + NO/EN experience): mostly done for launch
   - Done: V2 voice pipeline, launch-safe settings/legal/support, Apple Sign-In enablement, watch icon/dashboard polish, summary live-voice CTA alignment.
   - Missing: final deployed/no-HR phrase-rotation and coach-score audit on real devices and live backend.

2. Phase 2 (Deterministic event motor): guarded and stable
   - Done: deterministic ownership remains in `zone_event_motor`, talk safety/security/rate limiting are on the single runtime path, and live voice stays isolated from continuous coaching.
   - Missing: targeted dead-code cleanup and final production smoke after Render/live env is stable.

3. Phase 3 (Sensor layer: Watch HR/cadence + fallback): launch-usable but still needs soak time
   - Done: watch capability gating, companion install/signing fixes, request correlation, HR backfeed, fallback semantics, and watch dashboard.
   - Missing: longer paired-device soak for watch reachability transitions and any cadence/live-pulse follow-up.

4. Phase 4 (LLM as language layer only): controlled, not fully rolled out operationally
   - Done: Grok-first workout talk, xAI live voice on a separate post-workout path, summary-only live-voice context.
   - Missing: deployed xAI rollout validation, free/premium limit smoke, and continued device verification of local speech-service stability during workout talk.

## Rules reinforced for future sessions
1. Keep watch improvements on the existing WC + watch workout path; do not split the watch runtime.
2. Keep live voice as an isolated summary-mode experience until a deliberate product decision changes that boundary.
3. Treat `Talk to Coach Live` memory/history scope as explicit product policy, not accidental provider behavior.
4. Device-log issues around speech handoff should be fixed by changing the current path, not by adding a second wake-word/talk stack.
