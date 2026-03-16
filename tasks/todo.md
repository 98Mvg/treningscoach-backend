# Task Plan (Active)

Updated: 2026-03-16

## Working Rules (from workflow image)

- For non-trivial work, write a short checkable plan before implementation.
- Stop and re-plan if execution goes sideways.
- Verify behavior before marking anything done.
- Keep changes minimal and focused on root cause.
- Update this file with progress and review notes.

## Next Session Plan

- [ ] Verify first-launch carousel on physical iPhone 15 after commit `0b849ca` (no left-edge text clipping, CTAs fully visible).
- [ ] Capture one screenshot per intro page on iPhone 15 to confirm safe-area and content-fit quality.
- [ ] Device-check launch page in Safari (NO/EN + light/dark toggle + image loading on production URL).
- [ ] Device-smoke first-launch onboarding carousel (4 pages auto-advance + dot navigation + both bottom CTAs on every page).
- [ ] Validate iPhone runtime after full onboarding expansion (all new profile/HR/habits pages on real device).
- [ ] Validate tap-to-talk flow on device (press Talk button, capture speech, coach reply audio, state reset).
- [ ] Collect user feedback on onboarding copy clarity (NO + EN) and tighten wording.
- [x] Confirm mic long-press behavior and workout stop behavior do not conflict.
- [x] Keep workout UI minimal text and backend diagnostics separated from user-facing UI.
- [x] Continue Phase 3 sensor work (HR/watch quality handling + fallback clarity).
- [x] Re-run focused checks and capture results below.
- [x] Add fast Grok-first Q&A path for "Ask Coach" with max 3-sentence output.
- [x] Expand Ask Coach policy: ~5s think-time, allow >3 sentences when needed, and hard domain/safety guardrails.
- [x] Make iOS talk requests explicitly send `response_mode=qa` (including missing-session fallback) to avoid heuristic routing.

## Progress Log

- 2026-03-16: Kept `Talk to Coach Live` visible on workout summary for all users when live voice is enabled, but moved actual free-session counting from summary tap to the first successful realtime connection so failed starts/timeouts do not burn daily quota.
- 2026-03-16: Synced free live-voice policy to `3/day` across iOS config, backend defaults, `.env.example`, and launch ops docs, while preserving max-duration caps for both free and premium sessions.
- 2026-03-16: Cleaned the live website launch surfaces so `/` and `/download` now use `coachi.no` metadata/canonical URLs, real `/privacy` and `/terms` footer links, and free-download + optional Premium copy instead of old beta/onrender wording.
- 2026-03-16: Fixed iOS compile regression where `WorkoutCompleteView` could not resolve `LiveVoiceSessionTracker` because the new Swift file existed on disk but was missing from the Xcode project file reference + app target sources list.
- 2026-03-16: Fixed Supabase pooler startup crash by stopping automatic `db.create_all()` on external Postgres in `database.py`; local SQLite still auto-creates schema while production/external databases are now migration-owned.
- 2026-03-16: Kept the single existing Flask API path and added Supabase-ready backend infrastructure under it instead of introducing direct Supabase calls from SwiftUI.
- 2026-03-16: Added `CoachingScore` persistence on the existing workout save path plus an Alembic migration and Supabase RLS bootstrap SQL for `users`, `workout_history`, `coaching_scores`, and `user_subscriptions`.
- 2026-03-16: Migrated the existing email OTP routes to optional Supabase Auth behind `SUPABASE_AUTH_ENABLED`, while preserving current `/auth/email/request-code` and `/auth/email/verify` contract shapes.
- 2026-03-16: Added a dedicated `email_service` boundary for login, password reset, and subscription receipt sending, reusing the existing Resend-capable email sender.
- 2026-03-16: Hardened error monitoring by routing auth, subscription, webhook, and workout-save failures through the existing Sentry integration path with structured context.
- 2026-03-16: Fixed onboarding so the endurance-training "No" path skips frequency/duration cleanly, returns from summary to the correct prior step, and preserves one deterministic onboarding session.
- 2026-03-16: Reworked the Coachi paywall/manage-subscription/profile/settings/legal surfaces to Coachi-only copy and Coachi URLs, while keeping the same SwiftUI navigation/runtime path.
- 2026-03-16: Fixed website mobile navigation visibility and interaction on the existing `index_launch.html` path and added a `/terms` alias without breaking `/termsofuse`.
- 2026-03-16: Removed dead onboarding preview code that still carried stale `AQ` copy, and added a concrete Coachi App Store metadata/review-note draft for submission prep.
- 2026-02-23: Fixed iPhone 15 intro clipping in `FeaturesPageView` by constraining content-card width to device width and tightening responsive paddings/wrapping; pushed in commit `0b849ca`.
- 2026-02-23: Validation run after clipping fix: onboarding/speech contract tests passed (`19 passed`) and iOS build succeeded.
- 2026-02-23: Resumed with workflow-orchestration rules from user-provided image.
- 2026-02-23: Root-cause signal for UI lag identified in simulator logs: repeated `RBLayer: full image queue` from continuous hidden-tab rendering load.
- 2026-02-23: Reduced hidden-tab render load by disabling animated workout background when workout tab is not selected.
- 2026-02-23: Made `WaveformView` static when inactive (no Timeline/continuous frame churn outside active talk visuals).
- 2026-02-23: Replaced `WorkoutBgTrail` image content to ensure no "Perfect pulse" text appears in app background assets.
- 2026-02-23: Active workout screen updated to sheet-based diagnostics panel for more reliable mic long-press open behavior.
- 2026-02-23: Removed coach guidance text line from active workout surface (minimal text UI).
- 2026-02-23: Phase 3 bug fixed: outbound `hrQuality` now respects current signal quality, not just watch-connected status.
- 2026-02-23: Hardened multiple SwiftUI/CoreGraphics paths against non-finite numeric values (`NaN`/`Inf`) to address typing lag + console spam during onboarding.
- 2026-02-23: Added name-field input hints (`givenName`/`familyName`) and disabled autocorrect for lighter text-entry behavior.
- 2026-02-23: Reworked active workout controls to primary tap-to-talk CTA in center + smaller Spotify corner control.
- 2026-02-23: Hardened talk-to-coach runtime path with unpaused gating, missing-session fallback endpoint, and deterministic state reset.
- 2026-02-23: Added question-aware `/coach/talk` routing to fast Grok-first Q&A path with deterministic 3-sentence cap + fallback.
- 2026-02-23: Updated Ask Coach behavior to short-by-default answers with optional up to 5 sentences, 5s Q&A timeout budget, and strict refusal for sexual/harassing/off-topic questions.
- 2026-02-23: iOS now sends explicit Q&A intent (`response_mode=qa`) in workout talk payloads and generic fallback talk payloads.
- 2026-02-23: Implemented full onboarding parity sequence (identity, birth/gender, body metrics, HR max/resting HR, endurance habits, frequency/duration, summary, result, sensor/no-sensor, notifications).
- 2026-02-23: Wired onboarding completion to typed profile persistence in `AppViewModel.completeOnboarding(profile:)`, including backend-critical keys (`hr_max`, `resting_hr`, `user_age`, `training_level`, `app_language`).
- 2026-02-23: Added guided onboarding progress indicator (`Step X of Y`) for the long profile flow.
- 2026-02-23: Hardened `resetOnboarding()` to clear profile/HR defaults so QA can reproduce true first-launch behavior.
- 2026-02-23: Refreshed launch visuals using clean NanoBanana assets (no baked text overlays), including new hero background, watch image, and action imagery.
- 2026-02-23: Added light/dark mode toggle on `index_launch.html` with persisted preference (`coachi_site_theme`) and dynamic `<meta name=\"theme-color\">`.
- 2026-02-23: Re-synced root/backend launch templates and static site images to keep runtime/tests aligned.
- 2026-02-23: iOS onboarding now follows system light/dark mode (removed root-level dark lock) and uses adaptive palette in `AppTheme`.
- 2026-02-23: Added step-based onboarding atmosphere backgrounds (outdoor/run/calm) with blur + readability overlays.
- 2026-02-23: Updated onboarding card/input/border styling for light-mode readability while preserving dark-mode contrast.
- 2026-02-23: Updated first-launch onboarding to fixed 4-page value carousel (business promise, CoachScore, Spotify, Watch connect) with auto-advance + tappable dots + persistent register/existing-user CTAs.
- 2026-02-23: Replaced intro/onboarding background assets with brighter NanoBanana images (including water-break visual) for more positive first-launch tone.
- 2026-02-23: Tuned onboarding overlays to lighter gradients while preserving text readability in both dark and light mode.

## Review Results

- `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_live_voice_rollout_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_config_env_overrides.py`
  - result: `47 passed`
- `python3 -m py_compile config.py main.py xai_voice.py`
  - result: passed
- `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_launch_page_copy_contract.py tests_phaseb/test_web_blueprint_contract.py tests_phaseb/test_onboarding_theme_contract.py tests_phaseb/test_canonical_event_contract.py`
  - result: `70 passed`
- `python3 scripts/generate_codebase_guide.py`
  - result: `CODEBASE_GUIDE.md` regenerated
- `python3 scripts/generate_codebase_guide.py --check`
  - result: `CODEBASE_GUIDE.md is in sync`
- `pytest -q tests_phaseb/test_live_voice_mode_contract.py`
  - result: `10 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py`
  - result: `12 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_launch_page_copy_contract.py tests_phaseb/test_web_blueprint_contract.py`
  - result: `4 passed`
- `python3 scripts/generate_codebase_guide.py --check`
  - result: `CODEBASE_GUIDE.md is in sync`
- `pytest -q tests_phaseb/test_live_voice_mode_contract.py`
  - result: `9 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `python3 scripts/generate_codebase_guide.py --check`
  - result: `CODEBASE_GUIDE.md is in sync`
- `pytest -q tests_phaseb/test_config_env_overrides.py -k \"database_url or init_db\"`
  - result: `3 passed, 21 deselected`
- `python3 -m py_compile database.py`
  - result: passed
- `python3 scripts/generate_codebase_guide.py --check`
  - result: `CODEBASE_GUIDE.md is in sync`
- `python3 -m py_compile main.py auth_routes.py database.py config.py launch_integrations.py email_service.py supabase_auth_service.py web_routes.py app_store_runtime.py`
  - result: passed
- `pytest -q tests_phaseb/test_supabase_auth_contract.py tests_phaseb/test_launch_integrations_contract.py tests_phaseb/test_app_store_runtime_contract.py tests_phaseb/test_app_store_webhook_contract.py tests_phaseb/test_auth_and_workout_security.py tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_web_blueprint_contract.py`
  - result: `43 passed`
- `pytest -q tests_phaseb/test_ios_auth_refresh_contract.py tests_phaseb/test_onboarding_theme_contract.py tests_phaseb/test_coach_score_visual_contract.py tests_phaseb/test_coachi_progress_contract.py tests_phaseb/test_workout_ui_gesture_contract.py`
  - result: `66 passed`
- `python3 scripts/generate_codebase_guide.py`
  - result: `CODEBASE_GUIDE.md` regenerated
- `python3 scripts/generate_codebase_guide.py --check`
  - result: `CODEBASE_GUIDE.md is in sync`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_onboarding_theme_contract.py tests_phaseb/test_web_blueprint_contract.py`
  - result: `28 passed`
- `pytest -q tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_phase3_hr_quality_contract.py`
  - result: `5 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_talk_to_coach_contract.py`
  - result: `19 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_talk_to_coach_contract.py`
  - result: `18 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_talk_to_coach_contract.py`
  - result: `9 passed`
- `pytest -q tests_phaseb/test_brain_router_timeout_policy.py tests_phaseb/test_api_contracts.py`
  - result: `22 passed`
- `pytest -q tests_phaseb/test_brain_router_timeout_policy.py tests_phaseb/test_api_contracts.py`
  - result: `24 passed`
- `pytest -q tests_phaseb/test_talk_to_coach_contract.py tests_phaseb/test_api_contracts.py`
  - result: `15 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_workout_ui_gesture_contract.py tests_phaseb/test_talk_to_coach_contract.py`
  - result: `14 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`
- `pytest -q tests_phaseb/test_launch_page_assets.py tests_phaseb/test_launch_page_copy_contract.py tests_phaseb/test_web_blueprint_contract.py`
  - result: `7 passed`
- `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_onboarding_theme_contract.py`
  - result: `9 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED` (existing warnings unchanged)
- `pytest -q tests_phaseb/test_onboarding_theme_contract.py tests_phaseb/test_onboarding_inspo_contract.py`
  - result: `10 passed`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build`
  - result: `BUILD SUCCEEDED`

## Review — 2026-03-16 profile/support/home/live batch

- Reworked `Administrer abonnement` in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) to a pricing-card layout that matches the existing paywall direction more closely, while keeping restore/legal/App Store management on the same runtime path.
- Split support into a short `Kontakt support` surface plus a dedicated `SupportRequestFormView` mailto draft flow, and moved FAQ into a separate `FAQGuideView` with four Coachi-specific help categories.
- Relaxed summary live-voice account gating in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) from `currentUser != nil` to `hasUsableSession()` so free signed-in users are not blocked when profile hydration lags.
- Centered the home content column in [HomeView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/HomeView.swift) without introducing a parallel layout path.
- Verification:
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `22 passed`
  - `python3 scripts/generate_codebase_guide.py` -> `CODEBASE_GUIDE.md` regenerated
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 onboarding explanation pass

- Kept onboarding on the single existing SwiftUI path in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) and added Coachi-specific explanations directly to the max pulse, resting HR, endurance, and intensity steps instead of introducing a new onboarding engine or copying Mia layouts.
- Expanded the max pulse step with a clearer definition of what max pulse means and a small explanation card about when to trust a measured value versus the age-based estimate.
- Expanded the resting HR step with a stronger definition for when resting HR should be measured and an extra explanation card about why calm conditions matter.
- Added a dedicated endurance explainer block with examples that count (`løping`, `gåturer`, `sykling`, `svømming`, `dansing`, `aerobic`) and examples that usually do not count on their own (`yoga`, `styrketrening`, `pilates`).
- Strengthened the low/moderate/high intensity descriptions so users can map the hardest weekly endurance session to breathing and effort, and added a short explanation of moderate intensity on the frequency/duration step.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_onboarding_theme_contract.py` -> `33 passed`
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 onboarding/profile/live-voice stability batch

- Updated the onboarding HR explainer copy in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) to the requested English wording for max HR and resting HR, and changed endurance examples to use explicit `✅`/`❌` markers.
- Made the onboarding summary editable from the existing summary screen by wiring each row back to its source step, so users can fix a wrong value without backing through the whole flow.
- Reworked `Administrer abonnement` in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) to an included-items comparison between Free and Premium, and added an in-app update prompt tied to runtime version checks.
- Fixed a SwiftUI state regression in [LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift) and [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) by making tracker read methods side-effect free and synchronizing state outside `body` evaluation.
- Added an explicit initial assistant kickoff in [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift) so live voice sessions do not sit silent after connect.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `30 passed`
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 Render profile persistence crash fix

- Traced the Render `StringDataRightTruncation` crash to [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py), where `/coach/continuous` could treat the iOS-local `profile_<uuid>` personalization key as a database `user_profiles.user_id`.
- Added a DB-safe persisted user-id guard so local personalization identifiers are never written into the `user_profiles` foreign key column.
- Changed runtime profile resolution to skip empty profile snapshots, which prevents writing empty `user_profiles` rows that only carry timestamps and no useful HR/profile data.
- Made `/coach/continuous` prefer the authenticated user ID when resolving a persisted runtime profile, so signed-in users still get their saved DB profile even if the client also sends a local personalization key.
- Updated regression coverage in [test_profile_runtime_resolution.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_profile_runtime_resolution.py) and synced continuous/rate-limit media tests in [test_rate_limit_verification.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_rate_limit_verification.py) with current auth and upload-signature requirements.
- Verification:
  - `pytest -q tests_phaseb/test_profile_runtime_resolution.py tests_phaseb/test_profile_upsert_contract.py tests_phaseb/test_rate_limit_verification.py -k "profile or continuous"` -> `10 passed, 7 deselected`
  - `python3 -m py_compile main.py` -> passed

## Review — 2026-03-16 profile cleanup for root vs personal settings

- Removed the duplicated premium/offers card from the root [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) so subscription discovery happens through `Administrer abonnement` on the same settings path instead of a second promo surface.
- Removed the visible root-level `Delete account` entry and the `About Coachi · v...` row from the `Din profil / Your profile` list to keep the top-level settings surface lighter and less destructive.
- Kept `Delete account` only inside [PersonalProfileSettingsView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift), moved to the bottom of that screen, and removed `Sign out` plus the `Account` section there so destructive actions are less prominent.
- Updated profile/settings contracts in [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py) to lock the new separation between root profile settings and nested personal profile.
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `12 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-16 watch-connected onboarding Premium bridge

- Added a new watch-connected onboarding branch in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) so users who successfully connect Apple Watch now see a Coachi-specific Premium explainer before notification permissions.
- Kept the existing monetization runtime path by opening [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) from the new onboarding step instead of creating a second purchase flow.
- Kept non-watch or already-premium users on the simpler existing `sensorConnect -> notificationPermission` path, so the upsell is contextual rather than generic.
- Updated onboarding contracts in [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py) to lock the new branch and the `Continue with Free` fallback.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py` -> `8 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
