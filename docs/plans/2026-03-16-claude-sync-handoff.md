# Claude Sync Handoff — 2026-03-16

## Pull first
- Latest pushed commit on `main`: `de5c057` — `Polish onboarding, profile flows, and backend stability`
- Claude should pull `main` before starting new work.

## Product and user goal
- Coachi is a SwiftUI iPhone + Apple Watch running coach app with a Flask backend.
- Core user flow: onboarding -> connect watch/HR source -> start guided workout -> get summary/score/xp -> optionally talk to coach -> manage profile/subscription/support.
- Current product focus is launch polish on the single existing runtime path, not new architecture.

## Runtime map
- iOS app entry: [TreningsCoachApp.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/TreningsCoachApp.swift)
- Root app routing: [RootView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/RootView.swift)
- Main tab shell: [ContentView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/ContentView.swift)
- Onboarding flow: [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
- Summary/live voice UI: [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift), [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
- Profile/settings/subscription/support: [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
- Paywall/purchase path: [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift), [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift)
- Backend entry: [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py)
- Deploy start: [Procfile](/Users/mariusgaarder/Documents/treningscoach/Procfile)

## Request path and event path
- Request path:
  - app launch -> `RootView`
  - onboarding path -> `OnboardingContainerView`
  - workout path -> `WorkoutLaunchView` / `WorkoutCompleteView`
  - profile path -> `ProfileView`
  - paywall path -> `PaywallView`
- Event path:
  - watch/sensor capability updates -> `PhoneWCManager` / workout view model -> onboarding + workout UI
  - live voice session -> summary CTA -> `LiveCoachConversationView` -> `XAIRealtimeVoiceService`
  - subscription actions -> `SubscriptionManager` -> StoreKit/App Store
  - backend workout/profile persistence -> `BackendAPIService` -> Flask routes in `main.py`

## What landed in `de5c057`
- Profile root cleanup:
  - removed duplicate premium/offers surface from root profile
  - hid root-level delete-account and version/about rows
  - moved delete-account to bottom of `Personlig profil`
  - kept sign-out only on root profile
- Support/settings polish:
  - simplified support flow
  - FAQ/support structure cleaned up
  - manage-subscription page refined around included items
- Onboarding:
  - stronger explanations for max HR, resting HR, endurance training, intensity
  - summary values are editable by jumping back to the owning step
  - new post-watch-connected Premium bridge step that reuses existing `PaywallView`
- Live voice stability:
  - first-response kickoff after connect so the coach does not stay silent
  - side-effect-free availability/count reads to avoid SwiftUI publish-during-view-update issues
- Backend stability:
  - runtime-only `profile_<uuid>` identifiers are not persisted into `user_profiles.user_id`
  - empty profile snapshots are skipped instead of writing blank DB rows

## Files touched in the last pushed batch
- [TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift)
- [TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift)
- [TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
- [TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
- [TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
- [TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)
- [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py)
- plus tests/docs in `tests_phaseb/`, `tasks/`, and `docs/plans/`

## Verification already done
- `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_profile_runtime_resolution.py tests_phaseb/test_rate_limit_verification.py tests_phaseb/test_subscription_paywall_contract.py` -> `45 passed`
- `python3 -m py_compile main.py` -> passed
- `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Current repo state
- No tracked code changes are left uncommitted after `de5c057`.
- Current local-only leftovers are reference artifacts and should not be mixed into product commits:
  - `.claude/worktrees/...`
  - `Pictures "your profile inspiration"/`
  - `onboarding_images/`
  - deleted local reference image `App inspo/IMG_5568.PNG`

## Likely next work for Claude
- Continue UI-only polish from the current runtime path.
- Highest-signal surfaces to iterate on:
  - onboarding screens in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
  - profile/settings/support/subscription surfaces in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
  - paywall styling/content in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift)
  - workout summary/live voice surfaces in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)

## Remaining work — Fix phase
- Re-verify on device that `Talk to Coach Live` actually starts speaking on first connect and does not silently stall even when the realtime socket connects.
- Re-verify on device that the summary CTA is available to the intended free-session path and that free quota is only consumed after a successful live connection.
- Re-check the `Administrer abonnement` comparison layout against the latest user preference and keep the included-items comparison on that single screen.
- Re-check profile/settings destructive actions and account flows on device to ensure `Delete account` only appears in the intended nested place and `Sign out` only on root profile.
- Re-check onboarding summary editing to confirm each row returns to the right step and preserves entered values when the user comes back.

## Remaining work — Polish/optimize phase
- Continue tightening onboarding copy in the existing step views so each health/training term is self-explanatory without adding a second explainer flow.
- Continue polishing `ProfileView` so support, FAQ, subscription, update prompts, and account management feel like one Coachi settings system rather than separate cards.
- Continue improving `PaywallView` and the post-watch-connected premium bridge so upsell timing and visual hierarchy feel intentional but still reuse the same purchase path.
- Watch for any remaining SwiftUI state-update warnings around live voice/workout summary and keep side-effect-causing reads out of `body`.

## Remaining work — Today's goal
- Automated/code work is functionally in good shape; the highest-value remaining work today is manual validation and launch ops.
- Device-test the latest onboarding, profile, manage-subscription, support, and live-voice flows on a real iPhone.
- Run the subscription sandbox matrix in [subscription-sandbox-test-matrix.md](/Users/mariusgaarder/Documents/treningscoach/docs/checklists/subscription-sandbox-test-matrix.md).
- Verify Render is serving the expected production commit and that no new backend errors appear in logs during live-voice and workout-save paths.
- Finish App Store Connect / submission checklist in [app-store-submission-checklist.md](/Users/mariusgaarder/Documents/treningscoach/docs/checklists/app-store-submission-checklist.md).

## Guardrails for Claude
- Keep one existing runtime path. Do not create a second onboarding or paywall architecture.
- Reuse `PaywallView` for purchases and `SubscriptionManager` for StoreKit behavior.
- Avoid touching backend unless the user explicitly asks for infra/backend work.
- Keep local inspiration folders and `.claude/worktrees/` out of commits.
- Sync [CODEBASE_GUIDE.md](/Users/mariusgaarder/Documents/treningscoach/CODEBASE_GUIDE.md) before ending the session.
