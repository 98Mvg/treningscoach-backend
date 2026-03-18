# Session Learnings — 2026-03-18 Post-Workout Share, Live Voice, and Watch Runtime

## Scope

Tighten the existing Coachi runtime instead of creating any parallel paths:

- stabilize the current watch-backed workout startup and live-HR path
- keep free/premium live voice on the existing `/voice/session` bootstrap and existing audio-pack lock flow
- polish the post-workout `Get Feedback` -> `WorkoutSummarySheet` -> `Talk to Coach` and share surfaces without replacing the summary system

Primary files touched on this runtime path:

- [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
- [PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift)
- [WatchWorkoutManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift)
- [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
- [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)
- [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
- [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift)
- [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift)
- [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py)

## What changed

### 1. Watch-backed workouts now recover on the current request-id path

- iPhone start no longer treats a temporary `sendMessage` failure as a hard watch-start failure if the existing app-context backup path is still alive.
- The watch-start ACK window is longer, and a late matching watch ACK can upgrade the already-active workout instead of being discarded.
- Watch HR still uses `sendMessage` as the fast path, but failures now queue the same payload through the existing `transferUserInfo` fallback.
- Backend disconnect-style notices are no longer emitted just because HR freshness dipped briefly while the watch was still attached.

### 2. Free live voice and premium limits stay on one existing path

- Free live voice preview is time-based on the existing summary-sheet live voice flow, not a second “trial conversation” system.
- Timeout handoff stays on the current audio-pack route: play the existing local lock clip first, then enter the existing `.liveVoice` paywall.
- Premium remains capped by session length and daily count through the same `/voice/session` policy/bootstrap path.

### 3. Post-workout summary, talk, and share surfaces should converge stylistically, not fork

- `WorkoutSummarySheet`, the inline `Talk to Coach` surface, and the share sheet now work best when they reuse the same floating-card language and button family.
- The best fix for “Type instead” from voice is not a second text-coach feature. It is a compact composer mode on `PostWorkoutTextCoachView`, launched only from live-voice entry points.
- The inline coach controls should live directly under the waveform, and the sheet should not auto-expand when voice starts.

### 4. Prompt correctness matters as much as UI polish

- Generic post-workout labels such as `Workout` / `Økt` must be treated as a general running workout, not a generic exercise session.
- The strength/gym hallucination guard has to exist in both places:
  - realtime voice bootstrap in [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py)
  - typed fallback prompt in [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift)
- If the backend sanitizer drops summary fields like average HR or distance, the prompt loses specificity even when the UI had the right context available.

### 5. Voice tone should be tuned on the current runtime before changing provider or identity

- The first lever for “phone-call / rusty / low-quality” tone on iOS is `AVAudioSession` mode.
- Using `.default` on the current `.playAndRecord` path gives a cleaner post-workout voice presentation than `.voiceChat`, while keeping the same provider, auth flow, quotas, and `Rex` identity.

## Guardrails

- Do not build a second post-workout summary screen, a second share flow, or a second text-coach system for small UX polish.
- Do not split watch startup into a new connectivity architecture; keep the single request-id flow and let late ACKs reconcile into the existing workout.
- Do not let voice and typed fallback drift on workout semantics. If running-only language changes, update both prompt surfaces in the same pass.
- Do not jump to a new TTS/provider/voice identity when the problem is still explainable by iOS session mode or prompt correctness on the existing path.

## Tomorrow-ready follow-up

If work continues tomorrow, the highest-value follow-ups are:

1. Run real-device validation for:
   - start on iPhone, then start/confirm on watch
   - short reachability dips during active watch-backed workouts
   - free live voice timeout -> local clip -> paywall handoff
2. Visual QA on device for:
   - compact `Type instead` sheet height and keyboard interaction
   - `Conversation ended` readability in light and dark mode
   - summary-sheet vs share-sheet surface parity
3. Prompt/output QA for:
   - generic `Workout` sessions no longer producing squat/gym language
   - `Rex` opening lines using available workout numbers naturally
