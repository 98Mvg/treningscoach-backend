# Session Learnings — 2026-03-16 Onboarding Summary Edit and Live Voice Stability

## What changed

- Updated the onboarding HR explainer copy in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) to the requested wording for max HR and resting HR.
- Changed the endurance examples to explicit `✅` and `❌` rows so the classification is obvious without extra explanation.
- Made the onboarding summary screen editable by routing each displayed field back to its owning onboarding step.
- Reworked `Administrer abonnement` in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) into an included-items comparison between Free and Premium and added an app update prompt driven by runtime version checks.
- Fixed live-voice silence and SwiftUI update warnings by making [LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift) read methods side-effect free, synchronizing tracker state outside `body`, and adding an explicit first-response kickoff in [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift).

## Why this path

- The product already had the right onboarding and settings surfaces. The missing piece was clarity and editability, not another navigation path.
- Summary editing is higher leverage than forcing users to backtrack because it preserves the current onboarding flow while removing friction.
- The live voice bug was a runtime state-management issue, so the right fix was to remove side effects from availability reads and make session startup more deterministic.

## Verification

- `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `30 passed`
- `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Follow-up note

- If live voice still feels too passive after the kickoff, tune the opening prompt and server-side VAD thresholds on the same existing realtime path rather than adding a parallel “auto-talk” mode.
