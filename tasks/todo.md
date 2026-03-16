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

- 2026-03-16: Kept the single existing Flask API path and added Supabase-ready backend infrastructure under it instead of introducing direct Supabase calls from SwiftUI.
- 2026-03-16: Added `CoachingScore` persistence on the existing workout save path plus an Alembic migration and Supabase RLS bootstrap SQL for `users`, `workout_history`, `coaching_scores`, and `user_subscriptions`.
- 2026-03-16: Migrated the existing email OTP routes to optional Supabase Auth behind `SUPABASE_AUTH_ENABLED`, while preserving current `/auth/email/request-code` and `/auth/email/verify` contract shapes.
- 2026-03-16: Added a dedicated `email_service` boundary for login, password reset, and subscription receipt sending, reusing the existing Resend-capable email sender.
- 2026-03-16: Hardened error monitoring by routing auth, subscription, webhook, and workout-save failures through the existing Sentry integration path with structured context.
- 2026-03-16: Fixed onboarding so the endurance-training "No" path skips frequency/duration cleanly, returns from summary to the correct prior step, and preserves one deterministic onboarding session.
- 2026-03-16: Reworked the Coachi paywall/manage-subscription/profile/settings/legal surfaces to Coachi-only copy and Coachi URLs, while keeping the same SwiftUI navigation/runtime path.
- 2026-03-16: Fixed website mobile navigation visibility and interaction on the existing `index_launch.html` path and added a `/terms` alias without breaking `/termsofuse`.
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
