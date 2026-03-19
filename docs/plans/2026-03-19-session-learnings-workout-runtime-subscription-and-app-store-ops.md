# Session Learnings — 2026-03-19 Workout Runtime, Subscription Truth, and App Store Ops

## Scope

Tighten the existing Coachi runtime and monetization paths without introducing parallel systems:

- keep the workout coach on the single `WorkoutViewModel -> /coach/continuous -> zone_event_motor.py` path
- keep post-workout live voice on the existing `WorkoutCompleteView -> LiveCoachConversationView -> XAIRealtimeVoiceService -> /voice/session` path
- keep `Manage Subscription` and onboarding on the single shared subscription deck
- keep App Store subscription sync on the current StoreKit 2 + signed transaction + App Store webhook path

Primary files touched or validated on this path:

- [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
- [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py)
- [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
- [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py)
- [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
- [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
- [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift)
- [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist)
- [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Info.plist)
- [app_store_runtime.py](/Users/mariusgaarder/Documents/treningscoach/app_store_runtime.py)

## What changed

### 1. The best fixes stayed on the existing runtime path

- Post-workout live voice quality and latency were improved by warming the existing backend path earlier, tightening the first-turn prompt on the current `xai_voice.py` path, and adding bounded realtime mic backpressure on the current websocket service.
- The right fix for free-run first-tick silence was not a second coaching path. It was to harden [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) so a resolved `zone_tick` survives downstream TTS/output failures and the app can fall back to the existing phrase-pack audio path.
- `NO_HR` motivation became truly `BOTH` by extending the existing staged motivation engine on [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py), not by inventing a second motivation controller.

### 2. `NO_HR` policy is now clearer and more product-stable

- The right mental model is not “HR missing = broken.” It is “HR missing = switch to structure-driven coaching.”
- The correct `NO_HR` hierarchy is:
  1. countdowns / phase changes
  2. first structure cue for the segment
  3. staged motivation
  4. anti-silence fallback
  5. breath only as a high-confidence modifier
- Breath should never decide intent. Phase decides intent; breath only refines tone within that phase.
- Free run should behave like easy run coaching without structure: no warmup, no warmup countdowns, no automatic finish, and no halfway unless a target duration exists.

### 3. Workout cues need one authoring truth, but migration has to be incremental

- The safe path is to keep [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) as the authoring source while [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py) remains a compatibility/runtime surface until the legacy dependency path is reduced.
- V2 phrase changes must stay aligned across:
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py)
  - [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py)
  - deterministic fallback text on [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
- Prep countdowns for warmup/recovery are a phase-specific specialization of the existing countdown path, not a second countdown system.

### 4. Subscription content should have one owner

- The Free / Premium / 14-day trial cards should stay on one shared deck and be reused by both onboarding and `Manage Subscription`.
- `Manage Subscription` works best as the canonical host, while the actual single source of truth remains the shared deck implementation.
- Pricing, feature copy, CTA routing, and current-plan logic must all be updated in the same shared path, or the UI and purchase behavior drift apart.
- App-owned subscription prices should follow app language and shared fallback config so Norwegian and English surfaces stay consistent before and after StoreKit loads.

### 5. App Store operational truth matters as much as UI truth

- Coachi already has a real App Store Server Notifications V2 endpoint on [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py): `/webhooks/app-store`.
- Production and sandbox notifications can use the same HTTPS endpoint because the notification payload carries the environment.
- The route still depends on backend environment flags such as `APP_STORE_SERVER_NOTIFICATIONS_ENABLED`; App Store Connect setup alone is not enough.
- For the current StoreKit 2 + signed transaction path, the app-specific shared secret is not required unless Coachi intentionally adds legacy `verifyReceipt` receipt validation.
- Export compliance should stay explicit on every shipped bundle target. `ITSAppUsesNonExemptEncryption = NO` belongs in both the iPhone and watch app plists when the app only relies on standard Apple-managed HTTPS/TLS.

## Guardrails

- Do not build a second coach path to fix free-run or `NO_HR` behavior; keep the fix in [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) and the existing `/coach/continuous` response path.
- Do not create a second subscription deck, success popup, or onboarding-only monetization system; keep one shared deck and one purchase path.
- Do not let App Store operations drift into chat-only knowledge. Keep webhook state, export-compliance settings, and subscription verification behavior discoverable in the repo.
- Do not treat fallback audio/TTS issues as a reason to discard resolved deterministic events. Preserve the event contract and let the client use the current phrase-pack path.

## Tomorrow-ready follow-up

If work continues tomorrow, the highest-value follow-ups are:

1. Real-device QA for free run:
   - confirm first tick speaks on-device even when backend TTS is degraded
   - verify `main_started` and later easy-run motivation timing with and without HR
2. App Store operations QA:
   - enable and smoke-test `/webhooks/app-store`
   - verify sandbox and production notification delivery
3. Runtime/source-of-truth cleanup:
   - continue reducing direct runtime dependence on [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py)
   - keep V2 phrase authoring aligned with pack generation and runtime fallback text
