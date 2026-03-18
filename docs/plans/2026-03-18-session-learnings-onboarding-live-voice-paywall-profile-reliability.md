# Session Learnings — 2026-03-18 Onboarding, Live Voice, Paywall, and Profile Reliability

## Scope

Improve the current Coachi runtime without introducing parallel flows:

- keep onboarding on the single `OnboardingContainerView` path and tighten route order, keyboard behavior, and the existing plan swiper
- keep post-workout live voice on the current `WorkoutCompleteView -> LiveCoachConversationView -> XAIRealtimeVoiceService -> /voice/session` path
- keep the paywall on the existing `PaywallView` purchase surface
- keep profile photo and account deletion on the existing authenticated `/auth/me` account route

Primary files touched on this runtime path:

- [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
- [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
- [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift)
- [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift)
- [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
- [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift)
- [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift)
- [auth_routes.py](/Users/mariusgaarder/Documents/treningscoach/auth_routes.py)
- [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist)

## What changed

### 1. Onboarding plan selection should reuse the existing step, but behave like a real full-screen onboarding page

- If plan selection comes after the watch/sensor step, keep it on the existing `.premiumOffer` route instead of adding a second upsell flow somewhere else.
- The plan swiper works better when it behaves like the existing onboarding carousel: full-screen, edge-to-edge, manually swipeable, and auto-rotating on a short timer.
- If language selection is inserted before auth, preserve the prior register vs login intent instead of resetting the user back to register by default.

### 2. Keyboard handoff is part of onboarding reliability

- A step transition can look “laggy” even when navigation is correct if the keyboard is still active during the animation.
- For `IdentityStepView`, dismiss first responder before advancing into the post-auth explainer so the “Hi … let me first explain…” page does not inherit the previous keyboard state.

### 3. Cold-start live voice needs backend warmup before declaring failure

- `Could not connect` on post-workout voice was largely a startup-timing issue on the existing runtime path, not a reason to replace the provider or build a second live-voice system.
- The first fix is to warm the backend before calling `/voice/session`, keep the current retry path, and allow a longer startup window before surfacing failure.
- User-facing status is more trustworthy when the real localized failure message remains visible instead of collapsing everything to a generic connect label.

### 4. Paywall readability fixes belong on the current paywall, not on a new design surface

- Light/dark paywall bugs were caused by fixed pale fills and bottom bars on the existing `PaywallView`.
- Fix contrast by routing the active surface through adaptive Coachi theme colors end-to-end rather than creating a new “dark paywall” version.

### 5. Profile photos should stay on the current account route

- `Add profile photo` was only a placeholder until this pass; the clean fix is to extend the existing authenticated `/auth/me` route, not introduce a separate avatar API family or local-only photo cache.
- Managed avatar files need cleanup on both replacement and account deletion, or the account path will accumulate orphaned uploads.
- If profile photos are added in iOS, `Info.plist` must be updated in the same pass or the runtime path remains incomplete.

## Guardrails

- Do not create a second onboarding monetization path just to change timing or layout; keep the plan selector on `.premiumOffer`.
- Do not add a second voice bootstrap or fallback transport when cold starts are the issue; warm and retry the current path first.
- Do not add a second paywall or a profile-photo-only backend surface; keep purchases on `PaywallView` and account updates on `/auth/me`.
- Do not let account deletion and avatar cleanup drift apart; if Coachi manages the avatar file, delete it from the same account-delete flow.

## Tomorrow-ready follow-up

If work continues tomorrow, the highest-value follow-ups are:

1. Real-device QA for:
   - onboarding language -> auth -> identity -> explainer transitions
   - plan swiper auto-rotation and swipe behavior on smaller iPhones
   - live voice startup from a cold backend
2. Visual QA in both appearances for:
   - paywall text contrast
   - full-screen onboarding plan pages
   - profile photo rendering in profile entry row and personal profile screen
3. Backend/runtime QA for:
   - avatar replacement cleanup
   - account deletion after avatar upload
   - auth refresh behavior around the avatar upload path
