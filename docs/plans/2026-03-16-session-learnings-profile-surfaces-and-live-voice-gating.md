# Session Learnings — 2026-03-16

## Scope
- Coachi profile/manage-subscription surface redesign on the existing SwiftUI path.
- Live voice summary CTA visibility, quota accounting, and backend/iOS policy sync.
- Launch-surface cleanup and verification before one combined push.

## What Changed
1. `Administrer abonnement`, `Personlig profil`, and `Helseprofil` were upgraded on the existing [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) path instead of creating parallel settings screens.
2. `Talk to Coach Live` stays visible in workout summary whenever live voice is enabled, while actual session access still gates through auth, free-tier daily limits, and paywall flow on the same runtime path.
3. Free live-voice sessions are now counted only after the realtime session reaches `.connected`, not when the summary CTA is tapped.
4. Free/premium live-voice defaults were re-synced across iOS config, Flask config, `.env.example`, and ops docs so launch policy stays consistent.

## Key Lessons
1. Summary CTA visibility and quota consumption must be treated separately. Discovery belongs on the surface; billing/usage should only trigger after the feature successfully starts.
2. If a free-tier live voice feature is enforced on both iOS and backend, keep `sessions/day` and `max_duration_seconds` aligned in code and operational docs in the same batch.
3. Inspiration-driven profile redesigns should reuse the real app state already stored in auth/profile settings rather than introducing temporary models just to match screenshots.

## Verification
- `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_live_voice_rollout_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_config_env_overrides.py`
- `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_launch_page_copy_contract.py tests_phaseb/test_web_blueprint_contract.py tests_phaseb/test_onboarding_theme_contract.py tests_phaseb/test_canonical_event_contract.py`
- `python3 -m py_compile config.py main.py xai_voice.py`
- `python3 scripts/generate_codebase_guide.py`
- `python3 scripts/generate_codebase_guide.py --check`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
