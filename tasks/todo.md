# Task Plan (Active)

Updated: 2026-03-17

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

- 2026-03-19: Kept the single existing `NO_HR` hierarchy in `zone_event_motor.py` and refined breath into a high-confidence modifier only: it now tightens anti-silence timing only when confidence is genuinely high, and after the first structure cue it refines runtime phrase selection on the same path instead of introducing a parallel motivation path.
- 2026-03-19: Kept the single existing `zone_event_motor.py` runtime path and made staged motivation truly `BOTH` for intervals and easy/free run by letting the same motivation engine unlock in structure-driven mode after the first structure cue in the current segment, instead of keeping sustained motivation `FULL_HR`-only.
- 2026-03-19: Added focused runtime coverage proving free run stays on the easy-run path with `plan_free_run` as the only no-warmup exception, and proving no-HR interval/easy-run workouts can now escalate from structure cues into the staged motivation families on the same path.
- 2026-03-19: Kept the existing easy-run/free-run runtime path and refined it so `plan_free_run` still skips warmup and auto-finish, but can now emit halfway progress when a real free-run target duration exists. The same `zone_event_motor.py` path also now picks structure-driven motivation phrases from small internal tone buckets for `interval` and `easy_run`, while fallback/max-silence reuses only existing `zone.silence.*` IDs.
- 2026-03-19: Kept the existing V2 workout-cue path and updated the active warmup/pause/resume/no-HR copy only in `phrase_review_v2.py`, `tts_phrase_catalog.py`, and the deterministic fallback text in `zone_event_motor.py`, without changing any event ids or introducing a parallel cue system.
- 2026-03-19: Kept `WatchConnectedPremiumOfferStepView` as the single shared Free/Premium/14-day-trial deck source of truth, changed auto-rotation to 12 seconds, updated the shared comparison rows (`Coaching by analysing puls`, `5 days workout history`, `Full workout history`, `Single session feedback`, `Remembers past workouts`, `Choose coach voice (coming soon)`), and left purchase/current-plan logic untouched.
- 2026-03-19: Hid the floating bottom tab bar on the existing `Manage Subscription` push path by wiring a single host-level suppression flag from `MainTabView` through `ProfileView` into `ManageSubscriptionView`, instead of trying to disable tab chrome inside the shared deck.
- 2026-03-18: Kept the single shared Free/Premium/14-day trial deck as the purchase entry point and aligned its contract/tests to the current direct `SubscriptionManager` purchase path instead of an extra `Choose subscription` sheet.
- 2026-03-18: Locked the shared plan deck copy so `Talk to Coach Live · 1/day` / `3/day` is presented as cleaner coach-conversation value copy on the cards (`Limited conversations with coach` / `Full conversations with coach`).
- 2026-03-18: Moved the authenticated delete-account entry into `Personlig profil` directly under the email row with the clearer `Slett brukerkontoen din` copy, and removed the duplicate bottom placement on the same existing `DeleteAccountInfoView` path.
- 2026-03-18: Reused the existing onboarding `Free -> Premium -> 14 dagers gratis prøveperiode` swiper from `Administrer abonnement` via a full-screen offers surface instead of sending `Se alle tilbudene` straight to the generic paywall or duplicating plan-card logic.
- 2026-03-17: Moved the responsive overflow/hamburger navigation to the actual `coachi.no` runtime path in `templates/index_launch.html`/`backend/templates/index_launch.html`, and changed `main.py` default web variant fallback from `codex` to `launch` so preview/default truth matches the live site.
- 2026-03-17: Fixed iOS/backend timeout noise on the single existing runtime path by adding a short backend-unavailable cooldown in `BackendAPIService`, routing `/auth/me` through the same guarded service instead of `URLSession.shared`, and fast-failing best-effort + primary calls (`/health`, `/analytics/mobile`, `/subscription/validate`, `/voice/session`, `/coach/continuous`, `/coach/talk`) when Render is already known unavailable.
- 2026-03-17: Updated stale source contracts around workout-summary live-voice UI to match the current `WorkoutSummarySheet` implementation instead of removed internal properties/CTA event names.
- 2026-03-17: Promoted new V2 runtime phrases for `zone.above.default.2`, `zone.in_zone.default.2`, `zone.in_zone.default.3`, and `zone.main_started.2`, synced the changed `countdown/work/cooldown` copy across `phrase_review_v2.py`, `tts_phrase_catalog.py`, and `zone_event_motor.py`, and kept the single existing V2->R2/app path intact.
- 2026-03-17: Ran `python3 tools/generate_audio_pack.py --version v2 --changed-only --sync-r2` with local `.env` sourcing; the tool regenerated only changed/new phrases (`16 changed`, `12 new`, `88 unchanged skipped`), wrote `v2/manifest.json` + `latest.json`, uploaded the updated V2 pack to R2, and pruned `0` stale MP3 objects.
- 2026-03-17: Ran `python3 tools/select_core_bundle.py --version v2` so the app’s bundled offline `CoreAudioPack` now mirrors the current V2 manifest (`58` IDs / `116` MP3s), including the newly added V2 phrases like `zone.main_started.2`, `zone.above.default.2`, `zone.in_zone.default.2`, `zone.in_zone.default.3`, and `zone.countdown.session_halfway.dynamic`.
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
- `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py`
  - result: `21 passed`
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

## Review — 2026-03-17 returning-user name persistence fix

- Fixed the returning-user auth/onboarding path so existing users keep the real onboarding name instead of falling back to a random auth-provider `display_name`.
- Backend `/auth/me` now includes `profile_name` from `user_profiles.name` in [database.py](/Users/mariusgaarder/Documents/treningscoach/database.py), and the Swift auth model in [UserProfile.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/UserProfile.swift) now exposes `resolvedDisplayName` that prefers `profile_name` over `display_name`.
- Centralized authenticated profile hydration in [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift) so successful login/profile refresh persists `user_first_name`, `user_last_name`, and `user_display_name` from the backend profile when available, while refusing to overwrite a good stored onboarding name with a weaker fallback.
- Updated the existing runtime callsites in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift), [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift), and [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) to read `resolvedDisplayName` on the same path instead of introducing a second name source.
- Verification:
  - `pytest -q tests_phaseb/test_ios_auth_refresh_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_voice_session_contract.py` -> `46 passed`
  - `python3 scripts/generate_codebase_guide.py` -> `[OK] Wrote CODEBASE_GUIDE.md`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-17 watch app list branding correction

- Kept the watch target display name as `Coachi` in [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Info.plist), which is the field that controls the iPhone Watch app list label.
- Reverted the watch target icon catalog in [AppIcon.appiconset](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Assets.xcassets/AppIcon.appiconset) back to the older per-size watch assets after the user clarified the icon on Apple Watch was already visually correct and only the `Coachi Watch` label needed fixing.
- Verification:
  - `plutil -p TreningsCoach/TreningsCoachWatchApp/Info.plist` -> `CFBundleDisplayName = Coachi`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 onboarding Premium bridge

- Added a new onboarding Premium bridge in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) so non-premium users now see a Coachi-specific Premium explainer before notification permissions.
- Kept the existing monetization runtime path by opening [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) from the new onboarding step instead of creating a second purchase flow.
- Kept non-watch or already-premium users on the simpler existing `sensorConnect -> notificationPermission` path, so the upsell is contextual rather than generic.
- Updated onboarding contracts in [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py) to lock the new branch and the `Continue with Free` fallback.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py` -> `8 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 onboarding `premiumOffer` naming cleanup

- Renamed the internal onboarding Premium bridge step from `watchConnectedOffer` to `premiumOffer` in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) so the enum and routing name match the current product behavior.
- Synced [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py) to the new internal step name.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py` -> `8 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 Claude sync handoff

- Added a dedicated Claude handoff in [2026-03-16-claude-sync-handoff.md](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-16-claude-sync-handoff.md) with current pushed commit, runtime map, request/event path, latest landed changes, and guardrails for continuing work.
- Explicitly documented which local artifacts are references only and must stay out of product commits.
- Added explicit remaining-work sections for the fix phase, polish phase, and today's launch goal so the next agent has a concrete continuation list instead of just a generic "next work" hint.
- Reconfirmed that [CODEBASE_GUIDE.md](/Users/mariusgaarder/Documents/treningscoach/CODEBASE_GUIDE.md) is in sync after the handoff doc was added.

## Review — 2026-03-16 Live voice tracker SwiftUI publish warning

- Fixed the `Publishing changes from within view updates is not allowed` warning in [LiveVoiceSessionTracker.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/LiveVoiceSessionTracker.swift) by removing the eager `synchronize()` publish from `init()` and deferring later `@Published` updates to the next main-loop turn.
- Kept the existing runtime path intact: [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) and [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift) still use the same shared tracker, but tracker writes no longer fire synchronously during SwiftUI update passes.
- Updated [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py) to lock the deferred publish helper so the tracker does not drift back to direct synchronous assignment in `synchronize()` or `recordSession()`.
- Verification:
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py` -> `11 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 onboarding premium bridge and profile subscription polish

- Synced [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py) to the intended onboarding behavior: all non-premium users now see the Premium bridge in onboarding, not only users with a confirmed watch-connected flag.
- Refined [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) so the screen shows a clearer `My plan / Min plan` summary using the existing subscription-manager state, while keeping the included-items Free vs Premium comparison on the same page.
- Moved the primary CTA stack in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) into a bottom safe-area section so `Continue / Start free trial` stays anchored at the bottom of the screen instead of living inside the scroll content.
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_monitor_management_contract.py` -> `20 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-16 XP summary + launch legal/support pass

- Locked the summary XP/runtime path to the existing workout-complete flow by verifying the local snapshot-based fix in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift), [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift), [Config.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Config.swift), and [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift). XP now keys off qualified workout duration, and the summary reads a frozen completion snapshot instead of live values that may already have reset.
- Verified that profile/settings section headers remain left-aligned on the existing path in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift); no parallel settings surface was introduced.
- Replaced the public [support.html](/Users/mariusgaarder/Documents/treningscoach/templates/support.html), [privacy.html](/Users/mariusgaarder/Documents/treningscoach/templates/privacy.html), and [termsofuse.html](/Users/mariusgaarder/Documents/treningscoach/templates/termsofuse.html) stubs with launch-grade Coachi pages, and upgraded the source legal drafts in [coachi-personvernerklaering-utkast-no.md](/Users/mariusgaarder/Documents/treningscoach/docs/legal/coachi-personvernerklaering-utkast-no.md) and [coachi-vilkar-for-bruk-utkast-no.md](/Users/mariusgaarder/Documents/treningscoach/docs/legal/coachi-vilkar-for-bruk-utkast-no.md) so site/runtime text and source-of-truth docs match.
- Added and synced focused contracts in [test_support_and_legal_web_content_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_support_and_legal_web_content_contract.py), [test_settings_docs_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_settings_docs_contract.py), [test_coachi_progress_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coachi_progress_contract.py), and [test_coach_score_visual_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coach_score_visual_contract.py) to match the current single runtime path.
- Checked local email activation status and confirmed Resend is still not active on this machine because `.env` is missing `RESEND_API_KEY`, `EMAIL_PROVIDER`, `EMAIL_SENDING_ENABLED`, and `EMAIL_FROM`.
- Verification:
  - `pytest -q tests_phaseb/test_coachi_progress_contract.py tests_phaseb/test_coach_score_visual_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_web_blueprint_contract.py tests_phaseb/test_support_and_legal_web_content_contract.py tests_phaseb/test_settings_docs_contract.py` -> `27 passed`
  - `python3 scripts/generate_codebase_guide.py` -> `CODEBASE_GUIDE.md` regenerated
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-16 legal entity insertion for launch docs

- Inserted the real legal entity details you provided into the active legal/support surfaces:
  - [privacy.html](/Users/mariusgaarder/Documents/treningscoach/templates/privacy.html)
  - [termsofuse.html](/Users/mariusgaarder/Documents/treningscoach/templates/termsofuse.html)
  - [support.html](/Users/mariusgaarder/Documents/treningscoach/templates/support.html)
- Synced the same entity details into the source legal drafts:
  - [coachi-personvernerklaering-utkast-no.md](/Users/mariusgaarder/Documents/treningscoach/docs/legal/coachi-personvernerklaering-utkast-no.md)
  - [coachi-vilkar-for-bruk-utkast-no.md](/Users/mariusgaarder/Documents/treningscoach/docs/legal/coachi-vilkar-for-bruk-utkast-no.md)
- Legal identity now reads `GAARDER (enkeltpersonforetak)` with org.nr. `937 327 412`.
- Remaining launch-grade legal gap after this pass: postal/business address is still not present because it has not been provided yet.
- Verification:
  - `pytest -q tests_phaseb/test_support_and_legal_web_content_contract.py tests_phaseb/test_settings_docs_contract.py` -> `6 passed`
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-16 support form picker selection fix

- Fixed the SwiftUI runtime warning `Picker: the selection "" is invalid and does not have an associated tag` on the existing profile/support path in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift).
- Root cause was that `SupportRequestFormView` rendered with `accountStatus` and `category` set to `""` before `.onAppear` could replace them with the first valid picker options. The support form now seeds those `@State` values in `init()` with valid localized defaults and revalidates them in `prefillFromCurrentUser()`.
- Updated [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py) to lock the new non-empty picker initialization and invalid-selection fallback.
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py` -> `9 passed`

## Review — 2026-03-16 Claude XP summary handoff

- Added a focused Claude handoff for the XP summary path in [2026-03-16-session-learnings-claude-xp-summary-handoff.md](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-16-session-learnings-claude-xp-summary-handoff.md).
- The note documents:
  - the user-visible XP summary bug
  - the real root cause
  - the correct runtime path from `stopContinuousWorkout()` to `WorkoutCompleteView`
  - the files that define the contract
  - the duration-only XP product rule
  - guardrails for future edits
- This is intentionally separate from the mixed legal/support note so Claude can find the summary logic quickly without reconstructing it from chat history.

## Review — 2026-03-17 Apple Watch HR stabilization

- Stabilized the single existing watch HR runtime path instead of introducing a parallel transport architecture:
  - [PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift) now accepts queued HR fallback payloads through `didReceiveUserInfo`, routes them through the same ingress path as `sendMessage`, and retries one deferred start request when reachability recovers.
  - [WatchWorkoutManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift) now uses `transferUserInfo` as the unreachable HR fallback transport with a 2-second throttle and BPM-delta gating instead of abusing `updateApplicationContext` for live HR.
  - [HeartRateArbiter.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/HeartRate/HeartRateArbiter.swift) now treats watch `.degraded` / `.connecting` as watch-attached while keeping live-HR truth tied to fresh samples.
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) now filters stale HK startup snapshots, starts a 45-second `watch_starting` grace window for watch-backed workouts, clears that grace on first fresh watch HR sample, and sends `watch_starting` to backend ticks until live watch HR arrives or the grace expires.
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) now suppresses `hr_structure_mode_notice`, `watch_disconnected_notice`, and `no_sensors_notice` during the explicit watch startup grace period, while leaving normal deterministic notice behavior unchanged after grace expiry.
- Added troubleshooting-grade telemetry for transport path, startup grace lifecycle, HK snapshot acceptance/ignore decisions, and deferred watch-start retry.
- Synced/expanded the watch HR contracts in:
  - [test_watch_connectivity_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_connectivity_contract.py)
  - [test_watch_request_id_correlation_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_request_id_correlation_contract.py)
  - [test_hr_arbiter_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_hr_arbiter_contract.py)
  - [test_hr_provider_resilience_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_hr_provider_resilience_contract.py)
  - [test_watch_hr_source_arbitration_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_hr_source_arbitration_contract.py)
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
- Verification:
  - `pytest -q tests_phaseb/test_watch_connectivity_contract.py tests_phaseb/test_watch_request_id_correlation_contract.py tests_phaseb/test_hr_arbiter_contract.py tests_phaseb/test_hr_provider_resilience_contract.py tests_phaseb/test_watch_hr_source_arbitration_contract.py tests_phaseb/test_zone_event_motor.py` -> `56 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
  - `python3 -m py_compile zone_event_motor.py` -> passed
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 Apple Watch branding in iPhone Watch app

- Updated the watch target display name in [TreningsCoachWatchApp/Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Info.plist) from `Coachi Watch` to `Coachi`, so the iPhone Watch app shows the same product name as the main app.
- Reused the existing centered Coachi iPhone app icon for the watch target by replacing [TreningsCoachWatchApp/Assets.xcassets/AppIcon.appiconset/AppIcon.png](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Assets.xcassets/AppIcon.appiconset/AppIcon.png) with the current Coachi-branded logo treatment from the iPhone asset catalog, instead of keeping the cropped watch-only variant.
- Kept the current single watch target/runtime path intact: no bundle identifiers, target names, asset-catalog structure, or watch connectivity behavior were changed.
- Verification:
  - `plutil -p TreningsCoach/TreningsCoachWatchApp/Info.plist` -> `CFBundleDisplayName => Coachi`
  - `shasum TreningsCoach/TreningsCoach/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png TreningsCoach/TreningsCoachWatchApp/Assets.xcassets/AppIcon.appiconset/AppIcon.png` -> hashes match, so the watch icon now reuses the same Coachi logo asset as iPhone
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -showBuildSettings -target TreningsCoachWatchApp | rg "ASSETCATALOG_COMPILER_APPICON_NAME|INFOPLIST_FILE|PRODUCT_BUNDLE_IDENTIFIER"` -> watch target still resolves `AppIcon`, `TreningsCoachWatchApp/Info.plist`, and `com.coachi.app.watchapp`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> blocked by an existing unrelated compile error in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift), after the watch asset/plist steps already resolved correctly

## Review — 2026-03-17 Guest auth guard before watch-HR troubleshooting

- Fixed the highest-impact auth/runtime issue on the single existing guest-capable workout path instead of changing the product model:
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) now pre-arms guest backend suppression at workout start when `requireSignInForWorkoutStart == false` and no usable session exists, so `/coach/continuous` no longer needs to fail once with `Missing or invalid Authorization header` before the app realizes it should stay local.
  - [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift) now skips `/subscription/validate` entirely when neither an access token nor a refresh token exists, instead of generating predictable 401/retry noise from guest mode.
- This keeps the supported guest-mode runtime intact:
  - workouts still start locally without sign-in
  - protected backend calls are simply short-circuited earlier when there is no auth material
  - watch-HR startup behavior can now be evaluated without auth noise masking the logs
- Added/updated source-contract tests in:
  - [test_ios_continuous_auth_guard_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_continuous_auth_guard_contract.py)
  - [test_ios_auth_refresh_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_auth_refresh_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_ios_continuous_auth_guard_contract.py tests_phaseb/test_ios_auth_refresh_contract.py` -> `13 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 V2 phrase curation workflow

- Added category-first phrase-curation support on the existing V2 review path instead of creating a third workflow:
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) now exposes explicit curation categories for `instruction` and `context_progress`, filtered down to current active rows only.
  - [tools/phrase_catalog_editor.py](/Users/mariusgaarder/Documents/treningscoach/tools/phrase_catalog_editor.py) now exports category-first curation artifacts under `output/phrase_curation/` as:
    - human-readable Markdown with current active phrases only
    - structured JSON working files with `keep` / `edit` / `add_variant`
  - The same editor now imports those JSON files back into [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py), where:
    - `edit` updates the existing `ReviewSeed`
    - `add_variant` appends a new `future` seed with the next family/event-specific variant id
- Kept pack/runtime behavior unchanged:
  - [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) still keys off approved active review rows only
  - candidate queue remains a side tool and was not merged into the runtime V2 curation path
- Added/updated tests in:
  - [tests_phaseb/test_phrase_catalog_editor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_editor.py)
  - [tests_phaseb/test_phrase_catalog_v2_review.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_v2_review.py)
  - [tests_phaseb/test_generate_audio_pack_sample_and_latest.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_generate_audio_pack_sample_and_latest.py)
- Verification:
  - `pytest -q tests_phaseb/test_phrase_catalog_editor.py tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_generate_audio_pack_sample_and_latest.py` -> `52 passed`
  - `python3 -m py_compile phrase_review_v2.py tools/phrase_catalog_editor.py` -> passed
  - `python3 tools/phrase_catalog_editor.py export-v2-curation --category instruction --output-dir /tmp/phrase_curation_smoke` -> wrote markdown + JSON
  - `python3 tools/phrase_catalog_editor.py import-v2-curation --json /private/tmp/phrase_curation_smoke/instruction_working_edited.json` -> dry-run showed `1` edit + `1` addition with no repo write

## Review — 2026-03-17 Halfway countdown integration

- Added halfway countdown support on the existing deterministic zone-event path instead of creating a second timing/coaching path:
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) now emits:
    - `interval_countdown_halfway` for timed warmup, interval work, and timed easy-run main segments
    - `interval_countdown_session_halfway` once per interval main block
  - `30 seconds left` still wins when it collides with halfway, so 60-second warmups keep the existing `interval_countdown_30` behavior and suppress a duplicate halfway cue.
- Kept the runtime split explicit:
  - segment halfway uses the same deterministic countdown family and progress catalog
  - interval-session halfway uses dynamic text on the same path so the coach can say progress like `2 of 4 done`
- Updated iOS routing in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift):
  - new priorities for halfway events
  - `.dynamic` countdown phrase IDs now bypass local pack resolution and intentionally use backend TTS, so dynamic interval progress is spoken correctly instead of falling back to static pack audio
- Updated/added source-contract tests in:
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)
  - [test_workout_cue_catalog_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_workout_cue_catalog_contract.py)
  - [test_r2_audio_pack_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_r2_audio_pack_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_zone_event_motor.py tests_phaseb/test_canonical_event_contract.py tests_phaseb/test_workout_cue_catalog_contract.py tests_phaseb/test_r2_audio_pack_contract.py` -> `81 passed`
  - `python3 -m py_compile zone_event_motor.py workout_cue_catalog.py` -> passed
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 Halfway countdown copy simplification

- Kept the new halfway event ids and `.dynamic` routing, but simplified both spoken variants to the same temporary copy approved by the user:
  - EN: `You are halfway through`
  - NO: `Du er halvveis nå.`
- Deferred richer session-progress wording like `2/4 done` without undoing the session-halfway event itself, so future copy iteration can stay on the same deterministic countdown path.
- Re-locked the wording in [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py) and [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py).

## Review — 2026-03-17 Shared context phrase refresh

- Refreshed the active shared context cues on the single existing phrase path:
  - [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py)
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py)
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
- Updated runtime `.1` copy for:
  - `zone.phase.warmup.1` -> `Warmup started` / `Oppvarming startet`
  - `zone.pause.detected.1` -> `Workout paused` / `Du har pauset økten`
  - `zone.pause.resumed.1` -> `Workout has resumed` / `Økten fortsetter.`
- Added/updated the non-active variant `zone.main_started.2` in the phrase sources as:
  - `Workout starting now` / `Treningsøkten begynner nå`
- Kept runtime routing unchanged for `main_started`; the app still maps `main_started` to `.1`, while `.2` is now available as the next curated variant instead of a second routing path.
- Verified the shared-context contract with:
  - `pytest -q tests_phaseb/test_canonical_event_contract.py tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_generate_audio_pack_sample_and_latest.py tests_phaseb/test_r2_audio_pack_contract.py tests_phaseb/test_workout_cue_catalog_contract.py` -> `85 passed`
  - `python3 -m py_compile tts_phrase_catalog.py phrase_review_v2.py zone_event_motor.py` -> passed
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 V2 phrase sync for new shared cues

- Added the two new halfway countdown cues to [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) as active `progress` rows with `mode="BOTH"`:
  - `zone.countdown.halfway.dynamic`
  - `zone.countdown.session_halfway.dynamic`
- Kept them on the existing V2 review/upload path without inventing a second phrase source. This makes all newly added shared workout cues visible in phrase curation/export even though runtime still treats the `.dynamic` ids specially on playback.
- Updated review-count and curation tests in [test_phrase_catalog_v2_review.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_v2_review.py) so the `context_progress` curation view now includes the halfway cues alongside the rest of the active countdown family.
- Verification:
  - `PYTHONPATH=. pytest -q tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_phrase_catalog_editor.py tests_phaseb/test_generate_audio_pack_sample_and_latest.py tests_phaseb/test_r2_audio_pack_contract.py tests_phaseb/test_workout_cue_catalog_contract.py tests_phaseb/test_canonical_event_contract.py` -> `101 passed`
  - `python3 -m py_compile phrase_review_v2.py` -> passed
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 V2 runtime pack sync to R2/app path

- Closed the real single-source-of-truth gap on the existing audio-pack path:
  - app runtime was already manifest-driven from R2 via [AudioPackSyncManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AudioPackSyncManager.swift)
  - but V2 generation still built text from [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py) and used review only as an ID filter
- [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) now builds the V2 pack from active runtime rows in [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py), so:
  - local V2 review/source controls which runtime phrases are included
  - generated `manifest.json` / `latest.json` stay the pack truth
  - `--sync-r2` now provides a one-step generate + upload + stale-R2-prune workflow on the same existing pipeline
- [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) no longer hard-bypasses `.dynamic` IDs. It now:
  - tries local pack first
  - tries R2 pack fetch next
  - falls back to backend TTS only if the pack does not contain the file
- This keeps R2/app sync authoritative even for curated countdown IDs that previously always skipped the pack path.
- Updated source contracts in:
  - [test_generate_audio_pack_sample_and_latest.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_generate_audio_pack_sample_and_latest.py)
  - [test_phrase_catalog_v2_review.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_v2_review.py)
  - [test_r2_audio_pack_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_r2_audio_pack_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_generate_audio_pack_sample_and_latest.py tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_r2_audio_pack_contract.py` -> `52 passed`
  - `python3 -m py_compile phrase_review_v2.py tools/generate_audio_pack.py` -> passed
  - `python3 tools/generate_audio_pack.py --version v2 --dry-run` -> `Phrases: 108`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 Phrase rotation on existing runtime path

- Kept the current single cue runtime path and made backend phrase selection less repetitive without inventing a second selector in iOS.
- Added [build_runtime_event_phrase_map()](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) in [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) so the active V2 review rows remain the source of truth for which variants are eligible per event.
- Updated [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) so the selected primary event now uses backend-owned rotation for active V2 variants on shared context/instruction events such as:
  - `main_started`
  - `entered_target`
  - `exited_target_above`
  - and any future event that gains multiple active rows in the same review-event bucket
- Left iOS on the same event path in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift): the app still prefers backend-provided `phrase_id`, so no duplicate rotation logic was added client-side.
- Motivation was checked rather than redesigned:
  - interval motivation only fires in `work` when HR is valid, the user is in target long enough, and the first 10 seconds of the rep have passed
  - interval motivation uses slot/budget logic from work duration
  - easy-run motivation fires after sustain and respects the easy-run cooldown
  - higher-priority events suppress motivation in the same tick
- Added/updated source contracts in:
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_zone_motivation_stages.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_motivation_stages.py)
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)
  - [test_phrase_catalog_v2_review.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_v2_review.py)
- Verification:
  - `PYTHONPATH=. pytest -q tests_phaseb/test_zone_event_motor.py tests_phaseb/test_zone_motivation_stages.py tests_phaseb/test_canonical_event_contract.py tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_r2_audio_pack_contract.py` -> `133 passed`
  - `python3 -m py_compile zone_event_motor.py phrase_review_v2.py` -> passed
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 Render dependency cleanup

- Troubleshot the Render deploy path against the real production runtime:
  - Render deploys from root [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) via [Procfile](/Users/mariusgaarder/Documents/treningscoach/Procfile)
  - root [requirements.txt](/Users/mariusgaarder/Documents/treningscoach/requirements.txt) is therefore the production dependency truth
- Removed tool-only `boto3` from root [requirements.txt](/Users/mariusgaarder/Documents/treningscoach/requirements.txt) so Render no longer installs the R2 upload SDK as part of the Flask runtime.
- Added [requirements-tools.txt](/Users/mariusgaarder/Documents/treningscoach/requirements-tools.txt) for manual tooling and R2 upload flows. This keeps the existing [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) path working without bloating production deploys.
- Converted [backend/requirements.txt](/Users/mariusgaarder/Documents/treningscoach/backend/requirements.txt) into a simple compatibility shim (`-r ../requirements.txt`) so stale FastAPI/uvicorn/soundfile drift no longer misrepresents the real backend runtime.
- Kept `psycopg[binary]` in root [requirements.txt](/Users/mariusgaarder/Documents/treningscoach/requirements.txt). The production DB URL is normalized to `postgresql+psycopg://` in [database.py](/Users/mariusgaarder/Documents/treningscoach/database.py), so the driver is a real runtime dependency and must not be removed.
- Updated [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) error text so local R2 upload failures now point to `pip install -r requirements-tools.txt`.
- Updated dependency/source contracts in:
  - [test_r2_audio_pack_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_r2_audio_pack_contract.py)
  - [test_launch_integrations_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_launch_integrations_contract.py)
  - [test_config_env_overrides.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_config_env_overrides.py)
- Verification:
  - `PYTHONPATH=. pytest -q tests_phaseb/test_r2_audio_pack_contract.py tests_phaseb/test_launch_integrations_contract.py tests_phaseb/test_config_env_overrides.py` -> `45 passed`
  - `python3 -m py_compile tools/generate_audio_pack.py` -> passed
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-17 Phase 2 runtime polish on the existing app path

- Kept the single existing runtime path and closed three remaining Phase 2 gaps without introducing parallel systems:
  - push reminder flow now has a real post-workout reminder and deep link routing in [AppViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/AppViewModel.swift)
  - mobile analytics allowlist in [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) now accepts the push/returning-user events the iOS app actually emits
  - CoachScore polish now surfaces streak + XP context on the existing home and workout summary views in [HomeView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/HomeView.swift) and [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)
- Extended [PushNotificationManager](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/AppViewModel.swift) so it schedules:
  - the existing onboarding reminder
  - a new workout reminder after workout completion
  - deep-link payloads back into `coachi://tab/workout`
  - analytics for notification opens on the same existing push path
- Wired the workout runtime to schedule the workout reminder on completion in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift), while still clearing pending reminders when a new workout starts.
- Added a small maintainability/runtime win in [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift) with `currentWorkoutStreak()` so streak logic is shared instead of duplicated in the views.
- Fixed two existing SwiftUI compile issues on the same runtime path in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) while landing the summary polish:
  - invalid `@ViewBuilder` use on a `String` property
  - mismatched return branches in `summaryRow(...)`
- Updated source contracts in:
  - [test_ios_push_notification_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_push_notification_contract.py)
  - [test_app_store_webhook_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_app_store_webhook_contract.py)
  - [test_coach_score_visual_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coach_score_visual_contract.py)
  - [test_ios_app_router_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_app_router_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_ios_push_notification_contract.py tests_phaseb/test_app_store_webhook_contract.py tests_phaseb/test_coach_score_visual_contract.py tests_phaseb/test_ios_app_router_contract.py` -> `21 passed`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-17 Landing navigation overflow + email/auth verification

- Kept the active website path on the default `codex` variant in [templates/index_codex.html](/Users/mariusgaarder/Documents/treningscoach/templates/index_codex.html) and added a responsive hamburger flow instead of introducing a second navigation system.
- Navigation behavior now matches the requested priority:
  - primary CTA stays visible as long as possible
  - regular site navigation links collapse into a hamburger menu when width is tight
  - mobile forces the collapsed navigation state
  - language switch and non-navigation actions stay outside the hamburger path
- Implemented runtime overflow detection in the existing page script by measuring the nav width after language changes and window resizes, rather than using only a hard screen-width breakpoint.
- Verified the current email/auth status instead of guessing:
  - local `.env` has `EMAIL_PROVIDER=resend`, `EMAIL_SENDING_ENABLED=true`, `RESEND_API_KEY` present, and `EMAIL_FROM` configured
  - backend auth/email routes already use the existing [email_sender.py](/Users/mariusgaarder/Documents/treningscoach/email_sender.py) path for passwordless email auth and welcome emails
  - iOS auth persistence still uses keychain-backed access + refresh tokens on the existing [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift) path
- The reported Xcode error in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) is not reproducing on the current runtime path; the app builds successfully with the current file state.
- Added a source contract in [test_landing_navigation_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_landing_navigation_contract.py) so the codex landing page keeps:
  - the primary CTA outside the hamburger
  - a nav toggle + overflow menu
  - resize/language-triggered overflow recalculation
- Verification:
  - `PYTHONPATH=. pytest -q tests_phaseb/test_landing_navigation_contract.py tests_phaseb/test_web_blueprint_contract.py tests_phaseb/test_auth_email_contract.py tests_phaseb/test_waitlist_persistence.py tests_phaseb/test_auth_and_workout_security.py tests_phaseb/test_ios_auth_refresh_contract.py tests_phaseb/test_launch_integrations_contract.py` -> `30 passed`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-17 Claude worktree harvest + sensor tab-bar clearance

- Reviewed the Claude worktrees against current `main` and kept the pass selective on the single runtime path instead of merging stale branches.
- Ported the one remaining high-signal worktree improvement into [SettingsView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Settings/SettingsView.swift):
  - the voice-pack status row stays visible
  - destructive maintenance actions now sit behind an expandable advanced toggle
  - existing `AudioPackSyncManager` actions and behavior stay unchanged
- Reconciled the old `determined-sinoussi` monetization work and confirmed the valuable parts were already in `main`:
  - post-workout text coach remaining-free hint already exists
  - profile subscription comparison surface already exists
  - onboarding premium offer already uses the newer trial-oriented copy and current paywall path
- Fixed the runtime layout issue shown in the screenshots by adding explicit tab-bar clearance to the sensor management screens in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift):
  - [HeartRateMonitorsView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) now reserves space for the floating tab bar
  - [WatchConnectFromProfileView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) now reserves the same bottom clearance so the Apple Watch CTA stack no longer sits behind the tab bar
- Updated the source contract in [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py) to lock:
  - the expandable advanced voice-pack controls
  - the shared floating tab-bar clearance on the two sensor/watch surfaces

## Review — 2026-03-17 Profile Apple Watch flow polish

- Fixed the Apple Watch detail path opened from Profile so it behaves like the onboarding version without creating a second sensor UI.
- In [SensorConnectOnboardingView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift), added opt-in layout overrides for:
  - a more compact top inset
  - extra bottom action clearance above the floating tab bar
- [WatchConnectFromProfileView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) now uses those overrides, so:
  - the `Apple Watch` title sits higher on screen
  - `Continue without watch` and `Check again` stay visible and tappable above the floating tab bar
  - the view still reuses the same existing `PhoneWCManager` and onboarding button logic
- Simplified [HeartRateMonitorsView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) by removing the redundant top instruction card, `Sounds good!` button, and helper line from the screenshots. The screen now goes straight into the Live / History monitor list.
- Updated [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py) to lock the new profile-watch layout contract and the removal of the extra top copy.

## Review — 2026-03-17 Apple Watch stability + WorkoutSummarySheet polish

- Kept the single existing runtime path and improved the current watch/sheet flow only. No parallel watch-connect system, no duplicate summary flow, and no second button architecture were introduced.
- Apple Watch startup stability on the existing path:
  - [PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift) now keeps `updateApplicationContext` as the required backup path and treats `sendMessage` failure as transport degradation instead of an immediate workout-start failure.
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) now uses a `12.0s` watch ACK window, stops forcing a stop message on timeout fallback, and accepts a matching late `workout_started` ACK on the same request id so a phone-started workout can be upgraded into the watch-backed session without restarting the workout.
  - [WatchWorkoutManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift) still sends live HR over `sendMessage`, but now reuses the existing throttled `transferUserInfo` fallback when `sendMessage` errors mid-workout.
- Watch disconnect notice stability on the existing backend path:
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) now gates `watch_disconnected_notice` and `watch_restored_notice` on real watch availability transitions, instead of treating any temporary `FULL_HR -> fallback` downgrade as a watch disconnect.
- WorkoutSummarySheet polish on the existing post-workout surface:
  - [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) now uses one shared `SummarySurfaceButtonStyle` for `Get Feedback`, `Talk to Coach`, `End Conversation`, `HOME`, and `SHARE`.
  - The summary sheet uses adaptive `CoachiTheme` colors for the live coach state, fixes the washed-out light/dark mode issue, constrains the content into a lifted Coachi insight card, and keeps the current sheet/detent flow intact.
  - XP is now a temporary celebration only: the XP badge, outer XP ring, and XP pill last about `1.5s`, then the persistent result settles on Coachi Score. Persistent XP rows were removed from the summary sheet.
- Updated source contracts in:
  - [test_watch_connectivity_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_connectivity_contract.py)
  - [test_watch_request_id_correlation_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_request_id_correlation_contract.py)
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_coach_score_visual_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_coach_score_visual_contract.py)
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_watch_connectivity_contract.py tests_phaseb/test_watch_request_id_correlation_contract.py tests_phaseb/test_zone_event_motor.py tests_phaseb/test_coach_score_visual_contract.py tests_phaseb/test_live_voice_mode_contract.py` -> `67 passed`
  - `python3 -m py_compile zone_event_motor.py` -> `passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-17 Live voice free preview + premium caps

- Kept the existing post-workout voice path intact:
  - [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) still owns the summary-sheet entry and paywall handoff
  - [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift) still owns start tracking
  - [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift) still owns live-session timing and disconnect behavior
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) remains the backend policy source of truth for session caps
- Free live voice is now a true preview instead of a turn-limited conversation:
  - free tier is capped to `30` seconds per session and `2` sessions per day
  - the turn-count cutoff was removed, so the existing realtime session now ends only on the configured timer
  - summary sheet copy now shows free quota clearly with `Free today: N remaining` and `30 seconds max per session`
- Premium live voice is now explicitly capped on the existing policy path:
  - premium remains longer-form live voice, capped to `3` minutes per session and `3` sessions per day through the existing backend `/voice/session` policy
  - paywall copy now reflects capped premium value instead of claiming unlimited daily sessions
- The timeout handoff now uses the existing audio-pack system instead of jumping straight to the paywall:
  - added [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/en/voice.preview.free_limit.1.mp3) and [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/no/voice.preview.free_limit.1.mp3) to the active `v2` pack
  - bundled the same clip in [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack/en/voice.preview.free_limit.1.mp3) and [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack/no/voice.preview.free_limit.1.mp3)
  - [AudioPackSyncManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AudioPackSyncManager.swift) now exposes a local cached-or-bundled resolver for these playback-only clips
  - on free-tier `timeLimit`, the summary sheet now plays the local preview-end clip first, then presents the existing `.liveVoice` paywall
- Updated contracts in:
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - active audio-pack manifest at [manifest.json](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/manifest.json)
- Verification:
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_audio_pack_manifest_coverage.py tests_phaseb/test_select_core_bundle.py tests_phaseb/test_r2_audio_pack_contract.py` -> `52 passed`
  - `python3 -m py_compile main.py config.py` -> `passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Norwegian preview-limit clip refresh

- Updated only the existing Norwegian live-voice preview-limit audio on the current pack path:
  - [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/no/voice.preview.free_limit.1.mp3)
  - bundled fallback at [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack/no/voice.preview.free_limit.1.mp3)
- Refreshed the active `v2` manifest entry in [manifest.json](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/manifest.json) with the new size/hash and re-uploaded the current pack to the existing R2 bucket.
- Verification:
  - `python3 tools/generate_audio_pack.py --version v2 --upload-only` -> `Uploaded 118 MP3 files + v2/manifest.json + latest.json to R2 bucket 'coachi'`
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_audio_pack_manifest_coverage.py tests_phaseb/test_select_core_bundle.py tests_phaseb/test_r2_audio_pack_contract.py` -> `52 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Norwegian preview-limit clip wording refresh

- Replaced only the existing Norwegian preview-limit clip on the current live-voice pack path with `Fortsett samtalen med Premium.`:
  - [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/no/voice.preview.free_limit.1.mp3)
  - bundled fallback at [voice.preview.free_limit.1.mp3](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack/no/voice.preview.free_limit.1.mp3)
- Refreshed the active `v2` manifest entry in [manifest.json](/Users/mariusgaarder/Documents/treningscoach/output/audio_pack/v2/manifest.json) with the new size/hash before re-uploading the same pack to R2.
- Verification:
  - `python3 tools/generate_audio_pack.py --version v2 --upload-only` -> `Uploaded 118 MP3 files + v2/manifest.json + latest.json to R2 bucket 'coachi'`
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_audio_pack_manifest_coverage.py tests_phaseb/test_select_core_bundle.py tests_phaseb/test_r2_audio_pack_contract.py` -> `52 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Workout complete Get Feedback CTA refresh

- Kept the existing post-workout flow in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) and restyled only the current `Get Feedback` CTA that opens `WorkoutSummarySheet`.
- Added a `hero` variant to the existing `SummarySurfaceButtonStyle` so the button uses a darker rectangular fill, brighter cyan border glow, and centered label/icon composition closer to the provided reference, without introducing a second button component.
- Verification:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 WorkoutSummarySheet template refresh

- Used [Workoutsummarysheet.png](/Users/mariusgaarder/Documents/treningscoach/Workoutsummarysheet.png) as the visual template for the existing `WorkoutSummarySheet` in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift).
- Kept the current summary/coaching flow, but changed the sheet presentation to a clear-backed floating card and retuned the existing sheet surface to match the template more closely:
  - warm translucent glass card instead of a full sheet background
  - pill label + serif-style summary title/subtitle
  - darker embedded coach panel
  - premium-style `Talk to Coach` CTA and glass `HOME` / `SHARE` buttons
- Extended the existing `SummarySurfaceButtonStyle` with additional summary-card variants instead of creating a second button system.
- Verification:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Get Feedback width tweak

- Kept the same `Get Feedback` CTA in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift), but capped its width to avoid running edge-to-edge across the bottom action area.
- Verification:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Keep summary sheet detent on Talk to Coach

- Removed the automatic `summaryDetent = .large` jump in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) when `Talk to Coach` starts from `WorkoutSummarySheet`.
- The existing summary sheet now stays at its current size instead of expanding just because live coach starts.
- Verification:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Share workout sheet matched to Talk to Coach surface

- Kept the existing share-workout flow in [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift), but restyled `WorkoutShareDestinationsSheet` to use the same clear-backed floating-card treatment as the Talk to Coach sheet.
- Extracted a shared `WorkoutModalCardBackground` so the summary sheet and share sheet now use the same warm glass card background instead of separate surface treatments.
- Updated the share sheet to use the same header language, card layout, and summary-card button styling family rather than the old plain white sheet.
- Verification:
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Post-workout share + live coach polish

- Kept the single existing post-workout flow and tightened only the current runtime surfaces:
  - [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift)
  - [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
  - [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift)
  - [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift)
  - [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py)
- Share-workout surface:
  - removed the yellow `Share with Coachi` / `Del med Coachi` badge and the extra subtitle, leaving only the localized white `Share workout` / `Del økten` title on the existing floating share card
- `Talk to Coach` sheet:
  - moved the existing coach toggle directly under `WaveformBarsView`
  - changed the toggle labels to localized `Start` / `Stop`
  - kept `HOME` / `SHARE` on the bottom row
  - increased waveform status contrast so ended/failed/connecting states remain readable on the glass card
- `Type instead`:
  - added an internal `PostWorkoutTextCoachPresentationMode` with default full-screen behavior plus a compact composer mode
  - both live-voice entry points now open the compact composer sheet at a fixed one-third-height detent instead of the full transcript screen
  - compact mode keeps the existing text-coach path and paywall handling, but trims the UI down to the short context line, input, send, and close controls
- Coach correctness + tone:
  - changed the live voice `AVAudioSession` mode from `.voiceChat` to `.default` while keeping the same `.playAndRecord` route options and the same `Rex` voice/provider path
  - hardened the backend voice bootstrap and typed fallback prompt so the post-workout coach is explicitly running-only, treats generic `Workout` labels as a general running workout, and forbids gym/strength/bodyweight references
  - preserved existing summary metrics in `xai_voice.py` sanitization for average heart rate, distance, and coaching style so the current summary context can actually reach the voice instructions
- Test coverage:
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py) now covers the badge removal, compact text fallback mode, `Start` / `Stop` labels, `.default` audio-session mode, and running-only prompt guards
- Verification:
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_voice_session_contract.py` -> `24 passed`
  - `python3 -m py_compile xai_voice.py` -> passed
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Session learnings + codebase sync

- Added a focused handoff/learning document at [2026-03-18-session-learnings-post-workout-share-live-voice-and-watch-runtime.md](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-18-session-learnings-post-workout-share-live-voice-and-watch-runtime.md) covering:
  - watch-backed workout startup and HR recovery rules on the existing request-id/WC path
  - post-workout summary/share/live-coach UI convergence on one sheet system
  - compact text fallback expectations for voice entry points
  - running-only prompt guardrails and current `Rex` audio-session guidance
  - explicit tomorrow follow-up checks
- Added distilled recurring rules to [lessons.md](/Users/mariusgaarder/Documents/treningscoach/tasks/lessons.md) so the same mistakes are less likely to repeat in later passes.
- Updated [generate_codebase_guide.py](/Users/mariusgaarder/Documents/treningscoach/scripts/generate_codebase_guide.py) so the new learning doc is part of the generated “Recent Session Learnings” section and the current operational status reflects:
  - stabilized watch-backed workout recovery semantics
  - free 30-second live voice preview on the existing summary path
  - shared post-workout floating-card surfaces plus compact voice-entry text fallback
- Regenerated [CODEBASE_GUIDE.md](/Users/mariusgaarder/Documents/treningscoach/CODEBASE_GUIDE.md) so tomorrow’s session can start from the updated generated source-of-truth instead of chat history.
- Verification:
  - `python3 -m py_compile scripts/generate_codebase_guide.py` -> passed
  - `python3 scripts/generate_codebase_guide.py` -> `[OK] Wrote CODEBASE_GUIDE.md`
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`

## Review — 2026-03-18 Risk list fixes: session persistence, trusted identity, iOS path mapping

- Kept the single existing runtime path and reduced the top Phase-1 risks without introducing parallel session or API flows.
- Backend runtime hardening:
  - [session_manager.py](/Users/mariusgaarder/Documents/treningscoach/session_manager.py) now supports database-backed session persistence with safe in-memory fallback when no Flask DB bind is available, so worker-local cache misses can recover session state instead of dropping talk/workout context.
  - [database.py](/Users/mariusgaarder/Documents/treningscoach/database.py) and [20260318_0004_add_runtime_session_states.py](/Users/mariusgaarder/Documents/treningscoach/alembic/versions/20260318_0004_add_runtime_session_states.py) add the `runtime_session_states` table for persisted runtime session payloads.
  - [breathing_timeline.py](/Users/mariusgaarder/Documents/treningscoach/breathing_timeline.py) now serializes/deserializes timeline state so persisted sessions keep deterministic breathing-timeline context across workers.
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) now instantiates the global `SessionManager` with DB storage, reloads session metadata through the manager instead of raw in-memory dict access, persists recent zone events/timeline updates, and bootstraps missing `/coach/continuous` sessions from authenticated user identity instead of parsing `user_id` out of client-supplied `session_id`.
- iOS client correctness:
  - [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift) now tags `/analyze` and `/coach/continuous` with their correct backend-availability paths, so request suppression/failure tracking is applied to the right endpoint.
- Test coverage:
  - [test_latency_strategy_state.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_latency_strategy_state.py) adds a DB-backed session-manager round-trip test across instances.
  - [test_profile_runtime_resolution.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_profile_runtime_resolution.py) now verifies that missing-session bootstrap uses authenticated user identity, not a forged `session_id`.
  - [test_talk_to_coach_runtime_context.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_talk_to_coach_runtime_context.py) now exercises authenticated `/coach/talk` requests and verifies recent zone-event/session-history recovery after local cache loss.
  - [test_ios_auth_refresh_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_auth_refresh_contract.py) now locks the corrected analyze/continuous path mapping.
  - [conftest.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/conftest.py) adds shared authenticated-route test support for `/coach/continuous` and `/coach/talk`, plus synthetic-audio signature bypass for tests that intentionally use dummy bytes.
- Verification:
  - `pytest -q tests_phaseb/test_latency_strategy_state.py tests_phaseb/test_profile_runtime_resolution.py tests_phaseb/test_talk_to_coach_runtime_context.py tests_phaseb/test_ios_auth_refresh_contract.py tests_phaseb/test_rate_limit_verification.py` -> `37 passed`
  - `pytest -q tests_phaseb/test_zone_continuous_contract.py tests_phaseb/test_workout_context_summary_contract.py tests_phaseb/test_server_authoritative_clock.py tests_phaseb/test_contract_version_schema.py tests_phaseb/test_zone_llm_phrase_layer.py tests_phaseb/test_phase2_quality_floor.py tests_phaseb/test_persona_event_motor_contract.py` -> `26 passed, 5 failed`
  - Residual wider-suite failures are stale expectations outside this risk-fix scope:
    - [test_zone_continuous_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_continuous_contract.py) still expects older `decision_reason` / `breath_quality_state` / max-silence behavior than the current zone-event motor returns
    - [test_phase2_quality_floor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phase2_quality_floor.py) uses a timeline stub that no longer matches the runtime `BreathingTimeline` interface
    - [test_persona_event_motor_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_persona_event_motor_contract.py) assumes persona text variance on a path now owned by deterministic zone-event templates
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Onboarding swipeable Free/Premium plan step

- Kept the single existing onboarding route in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift):
  - non-premium users still go from `sensorConnect` to `.premiumOffer`
  - premium users still skip to notification permission
- Replaced the old static watch-ready premium bridge with a swipeable two-page `Free` / `Premium` selector on the existing `WatchConnectedPremiumOfferStepView`.
- Made the step watch-aware without making it watch-dependent:
  - it now observes [PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift) state for copy/badge only
  - watch-ready users get positive Apple Watch copy
  - other non-premium users get generic choose-plan copy
- Kept purchase ownership on the existing [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) `.general` sheet:
  - `Free` card continues onboarding
  - `Premium` card opens the existing paywall
  - when premium access becomes active, the onboarding card snaps to Premium and the CTA becomes `Continue`
- Added a small shared subscription comparison source in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) so the onboarding step and Manage Subscription screen use the same feature truth instead of maintaining duplicate plan rows.
- Extended `OnboardingScaffold` just enough to support card-driven steps by hiding the bottom action area for this one onboarding screen instead of creating a second onboarding scaffold.
- Updated contract coverage:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `11 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Onboarding 14-day free-trial swipe

- Extended the same onboarding swiper in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) from two cards to three:
  - `Free`
  - `Premium`
  - `14-day free trial`
- Kept this on the existing `.premiumOffer` step and existing paywall path. No new onboarding checkout or duplicate trial flow was introduced.
- The new trial card now:
  - sits after the Premium card in the existing swipe order
  - reuses the same premium feature list
  - previews pricing after trial with local monthly/yearly selection
  - shows a dynamic yearly-savings badge when StoreKit pricing is available
  - opens the existing [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) `.general` sheet with the selected monthly/yearly option preselected
- Added a small paywall-selection hook in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) so onboarding can pass the initial monthly/yearly selection without changing purchase ownership or creating a second paywall.
- Updated contract coverage to lock the third swipe and the paywall preselection hook:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `11 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Onboarding, live voice, paywall, and profile reliability pass

- Kept the single existing runtime paths in place and tightened them instead of introducing parallel onboarding, paywall, live-voice, or account systems.
- Onboarding reliability and polish in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift):
  - welcome now routes to language selection first, then auth, while preserving register vs login intent
  - identity now dismisses keyboard before advancing into the post-auth explainer to avoid the hanging keyboard transition
  - the existing `WatchConnectedPremiumOfferStepView` now auto-rotates every 5 seconds, stays manually swipeable, and renders as a full-screen adaptive offers surface instead of the old inset card step
- Live voice startup resilience on the existing path:
  - [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift) now warms the backend before initial connect and retry, and shows the actual failure message in the orb/status area instead of collapsing everything to a generic connect error
  - [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift) now wakes the backend before bootstrap, uses a longer startup window, and stages connection state as `.connecting` after session bootstrap so cold starts have room to recover
- Paywall readability fixes in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift):
  - removed the fixed pale `F7F7FB` surfaces
  - switched the background and sticky bottom action area to adaptive Coachi theme surfaces so text and controls remain visible in both light and dark mode
- Profile/account reliability on the existing `/auth/me` path:
  - [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) now supports synced profile-photo selection with `PhotosPicker`, renders the avatar in both the profile entry row and `Personlig profil`, and still keeps `Slett brukerkontoen din` directly under email
  - [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift) and [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift) now upload the avatar through the existing authenticated profile route
  - [auth_routes.py](/Users/mariusgaarder/Documents/treningscoach/auth_routes.py) now accepts optional avatar upload on `PUT /auth/me`, serves managed avatar files from the auth blueprint, and removes managed avatar files when the account is deleted
  - [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist) now declares photo-library usage for the existing iOS target
- Updated focused coverage:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_ios_profile_sync_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_profile_sync_contract.py)
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
  - [test_auth_and_workout_security.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_auth_and_workout_security.py)
- Verification:
  - `python3 -m py_compile auth_routes.py` -> passed
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_ios_profile_sync_contract.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_auth_and_workout_security.py` -> `47 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Onboarding language/auth regression pass

- Kept the same onboarding runtime path in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift); the fixes stayed local to the existing language step, auth step, and subscription bootstrap path.
- Fixed narrow-device clipping in [LanguageSelectionView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/LanguageSelectionView.swift) by moving it onto the same width-clamped full-screen layout model already used by the stronger onboarding screens:
  - clamps against render width and device width
  - constrains text to a centered content width
  - keeps the surface clipped to the screen bounds
  - uses adaptive Coachi borders instead of the old white-only outline
- Reduced onboarding hangs by tightening [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift):
  - `initialize()` is now idempotent so the app-level `.task` does not repeatedly re-run subscription boot work while onboarding rerenders
  - server-side entitlement sync now bails out before calling backend validation when there is no auth material, which removes the repeated unauthenticated `SUB_VALIDATE skipped reason=missing_auth_material` churn during onboarding
- Hardened onboarding auth error handling on the existing path:
  - [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift) now normalizes generic backend `Auth failed` responses into a localized sign-in failure instead of leaking the raw server fallback
  - [AuthView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/AuthView.swift) now clears stale auth errors when the step appears and when the user edits the email, so an old failure does not linger across retries
- Updated focused contract coverage:
  - [test_onboarding_theme_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_theme_contract.py)
  - [test_ios_auth_refresh_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_auth_refresh_contract.py)
  - [test_ios_app_router_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_app_router_contract.py)

## Review — 2026-03-18 Norwegian auth copy and post-watch plan pager fit pass

- Kept the single existing onboarding/auth/premium-offer runtime path and tightened the same files instead of creating a second plan selector or a separate auth recovery path.
- Fixed Norwegian alphabet output in the existing localized onboarding/auth strings:
  - [L10n.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Localization/L10n.swift) now uses proper `æ/ø/å` wording for the relevant Coachi surfaces instead of `aa`-style ASCII fallbacks
  - [AuthView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/AuthView.swift) now uses proper Norwegian characters in the hard-coded terms and validation copy
- Improved onboarding auth reliability on the current path in [AuthManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift):
  - auth/email requests now warm the existing backend path before sending
  - the same request path now retries once on transient backend/network failures instead of failing immediately
  - generic backend `Authentication failed` responses now normalize to the localized sign-in failure state
  - no provider flow was duplicated and the same `/auth/apple`, `/auth/google`, and `/auth/email/*` routes are still used
- Fixed the post-watch onboarding plan swiper overflow in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift):
  - the `Free / Premium / 14 dagers gratis prøveperiode` step now clamps to the same device/layout-width pattern used elsewhere in onboarding
  - removed the old fixed `630`-height pager behavior that was causing clipping on phone-sized screens
  - each slide now uses the available screen height, narrower adaptive type/padding, and a vertical card scroll path when content runs long
- Updated focused contract coverage:
  - [test_onboarding_theme_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_theme_contract.py)
  - [test_ios_auth_refresh_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_auth_refresh_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_ios_auth_provider_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_auth_provider_contract.py)
  - [test_ios_apple_signin_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_ios_apple_signin_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)

## Review — 2026-03-18 Render startup memory pressure pass

- Kept the single existing Flask runtime in [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) and reduced eager startup work instead of adding a second boot path or splitting services.
- Reduced eager memory pressure from breath-analysis startup:
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) now uses a lazy breath-analyzer proxy instead of constructing `BreathAnalyzer()` during process boot
  - default breath payloads are now available from a local helper, so safe fallback responses no longer need to import `librosa` just to build the default dict
  - [breath_analyzer.py](/Users/mariusgaarder/Documents/treningscoach/breath_analyzer.py) now exposes a small `prewarm()` hook, but startup prewarm is deferred by default
- Reduced eager memory pressure from TTS/provider startup:
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) now resolves ElevenLabs config at startup but defers actual `ElevenLabsTTS` client creation until first synthesis or cache-stats access
  - [elevenlabs_tts.py](/Users/mariusgaarder/Documents/treningscoach/elevenlabs_tts.py) now lazy-loads the ElevenLabs SDK classes instead of importing them at module import time
  - [strategic_brain.py](/Users/mariusgaarder/Documents/treningscoach/strategic_brain.py) now lazy-loads Anthropic, and the unused eager strategic-brain boot in `main.py` was removed
- Added lightweight startup memory observability:
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) now logs RSS / peak memory checkpoints around Flask app creation, DB init, auth/web/chat blueprint registration, lazy breath-analyzer import, and lazy ElevenLabs initialization
  - [config.py](/Users/mariusgaarder/Documents/treningscoach/config.py), [.env.example](/Users/mariusgaarder/Documents/treningscoach/.env.example), and [backend/.env.example](/Users/mariusgaarder/Documents/treningscoach/backend/.env.example) now expose `BACKEND_STARTUP_MEMORY_LOGGING_ENABLED` and `LIBROSA_STARTUP_PREWARM_ENABLED`
- Focused backend verification coverage:
  - [test_backend_startup_memory_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_backend_startup_memory_contract.py)
  - [test_api_contracts.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_api_contracts.py)
  - [test_backend_runtime_guards.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_backend_runtime_guards.py)
  - [test_tts_audio_cache.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_tts_audio_cache.py)
  - [test_web_blueprint_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_web_blueprint_contract.py)
  - [test_root_runtime_source_of_truth.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_root_runtime_source_of_truth.py)

## Review — 2026-03-18 Manage subscription offers swiper full-screen fit pass

- Kept the existing shared offers swiper in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) and reused it from [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) instead of creating a second offers surface.
- Split the shared view into presentation modes on the same runtime path:
  - `onboardingStep` preserves the existing onboarding title, subtitle, auto-advance, and helper copy
  - `fullScreenOffers` removes the `Choose plan` header/subtitle/footer helper so the slide deck is the screen
- Fixed the profile `See all offers` regression where `Free` was not reachable:
  - the profile path now opens the shared swiper in `.fullScreenOffers`
  - `.fullScreenOffers` always resets to `selectedPlan = .free`
  - premium-only auto-selection remains limited to the onboarding presentation mode
- Fixed the page-width/peek issue on the profile offers screen:
  - full-screen mode now uses the render width directly instead of the onboarding width clamp
  - page spacing is `0` in full-screen mode so only one plan page is visible at a time
  - the plan cards drop corner radius and card shadow in full-screen mode so the active page fills the available screen cleanly
- Removed duplicated background layering on the profile path by presenting the shared swiper directly instead of wrapping it in a second onboarding atmosphere background.
- Updated focused verification coverage:
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)

## Review — 2026-03-18 Manage subscription offers pager ordering and copy alignment pass

- Kept the single shared offers deck in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) and fixed the profile rendering issue on that same view instead of introducing another pager.
- Fixed the visual page-order bug in the profile `Se alle tilbudene` path:
  - the pager content is now explicitly left-anchored inside its viewport instead of being centered as a three-card `HStack`
  - this removes the old `Premium -> Trial -> blank` rendering and restores the intended `Free -> Premium -> 14 dagers gratis prøveperiode` order
  - the last page no longer drifts into empty space because the deck width is clipped from a leading-aligned frame
- Tightened content consistency across the three plan pages:
  - each plan now has one short summary paragraph under the title/price block so the decks read like the same system with different plan information
  - the trial page now starts with the same top-down information rhythm as the Free and Premium cards instead of feeling structurally different
- Kept the existing full-screen profile mode with no onboarding `Choose plan` header/subtitle/helper text, and kept one page visible at a time.
- Updated focused verification coverage:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)

## Review — 2026-03-18 Post-workout live voice duration and opening-line prompt pass

- Kept the existing post-workout voice path on [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) -> [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift) `/voice/session` -> [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) -> [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py). No new voice architecture or alternate prompt path was introduced.
- Fixed the `00:07` interpretation issue on the existing prompt/context path:
  - [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py) now resolves `elapsed_s` / `duration_text` into a spoken-safe duration string before it reaches the voice prompt
  - timer strings are now explicitly guarded in the system instructions, so `00:07` is treated as `7 seconds`, not `7 minutes`
  - very short workouts now add a specific instruction to treat the session as a brief or early-stopped running attempt instead of a hold or non-running exercise
- Tightened the first-sentence prompt guard against bad exercise guesses:
  - [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py) now explicitly blocks reinterpretation of short durations as holds, planks, sets, or other non-running exercises
  - [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift) mirrors the same timer and short-duration rules in `PostWorkoutSummaryContext.fallbackPrompt(...)` so typed follow-ups stay aligned with live voice
- Updated focused verification coverage:
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
  - [test_voice_session_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_voice_session_contract.py)
  - [test_xai_voice_post_workout_prompt.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_xai_voice_post_workout_prompt.py)

## Review — 2026-03-18 Compact text-coach header cleanup pass

- Kept the existing `WorkoutSummarySheet -> Type instead -> PostWorkoutTextCoachView` path in [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift).
- Removed the compact header subtitle so the sheet opens blank under `Skriv i stedet` / `Type instead` instead of surfacing `coachScoreSummaryLine` such as `Coach score 0 · Keep building.`.
- Left the rest of the compact composer unchanged: same close button, same input, same send path, same paywall/lock handling, and same transcript reply card behavior when a response arrives.
- Updated focused verification coverage:
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)

## Review — 2026-03-18 Render 512MB OOM worker reduction pass

- Investigated the existing Render deployment path and confirmed the single highest-impact remaining memory multiplier was still [Procfile](/Users/mariusgaarder/Documents/treningscoach/Procfile): `gunicorn main:app --timeout 120 --workers 2`.
- Kept the same Flask/Gunicorn architecture and the same runtime entrypoint. The fix is purely on the existing deploy command:
  - reduced Gunicorn from `--workers 2` to `--workers 1`
  - this removes the duplicate loaded Python process on a `512MB` Render instance, which is the cleanest way to stop startup/import memory from being doubled again after the earlier lazy-loading pass
- Added focused deploy/runtime guard coverage so the Procfile does not drift back to two workers:
  - [test_backend_startup_memory_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_backend_startup_memory_contract.py)
  - [test_root_runtime_source_of_truth.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_root_runtime_source_of_truth.py)
- Verification:
  - `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
  - `pytest -q tests_phaseb/test_backend_startup_memory_contract.py tests_phaseb/test_root_runtime_source_of_truth.py` -> `12 passed`
  - `python3 -m py_compile main.py config.py breath_analyzer.py elevenlabs_tts.py strategic_brain.py` -> passed

## Review — 2026-03-18 Shared offers swiper static-layout pass

- Kept the existing shared offers path on [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift), reused by onboarding and [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) `Se alle tilbudene`. No new paywall, no second offers screen, and no parallel subscription flow were introduced.
- Removed inner vertical scrolling from `planCard(...)` so the deck is swipe-only horizontally. Each plan card now uses a fixed-height layout with a bottom-anchored CTA instead of a nested vertical `ScrollView`.
- Tightened the trial page so the CTA stays visible on screen:
  - removed the `Pricing after trial` / `Pris etter prøvetid` heading
  - kept the existing monthly/yearly selectors on the same paywall path
  - updated the trial CTA copy to `Start 14 dagers gratis prøveperiode nå` / `Start 14-day free trial now`
- Kept the `Free -> Premium -> Trial` action behavior intact:
  - `Free` continues on the existing flow
  - `Premium` and `Trial` still open the existing [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) `.general` route
- Updated focused verification coverage:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py` -> `22 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Render pipeline-minute learning note

- Added the deploy-scope learning to the durable notes in [tasks/lessons.md](/Users/mariusgaarder/Documents/treningscoach/tasks/lessons.md): when pipeline minutes are the issue, the highest-ROI fix in this repo is preventing backend autodeploys on iOS-only commits with Render root-directory and build-filter settings.
- Added the same guardrail to [2026-03-17-session-learnings-render-runtime-vs-tool-dependencies.md](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-17-session-learnings-render-runtime-vs-tool-dependencies.md) so Render troubleshooting handoff now covers both runtime dependency truth and deploy-scope control.
- Kept runtime code unchanged. This pass is documentation only.

## Review — 2026-03-18 Paywall trial CTA copy pass

- Kept the existing onboarding/offers -> [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift) purchase path.
- Updated the trial CTA on the existing paywall bottom action from the generic free-trial label to explicit duration copy:
  - Norwegian: `Start 14 dagers gratis prøveperiode nå`
  - English: `Start 14-day free trial now`
- Left non-trial paywall CTAs unchanged.
- Updated focused contract coverage:
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)

## Review — 2026-03-18 Post-workout voice workout-reference hardening pass

- Traced the existing live voice request path end to end:
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) builds [PostWorkoutSummaryContext](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift)
  - [BackendAPIService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/BackendAPIService.swift) sends it to `/voice/session`
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) bootstraps the xAI session
  - [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py) builds the Rex instruction payload
- Root causes for bad first-sentence context like `plank` / `squat`:
  - generic labels like `Workout` / `Økt` were being repeated into the opening prompt instead of being normalized to a running-specific reference
  - the opening-message rules still allowed too much freedom on generic modes
  - workout history was available during bootstrap without an explicit guard that the opening must use only the just-finished workout summary
- Kept the single existing Rex/xAI live voice path and hardened it in place:
  - [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py) now canonicalizes generic labels like `Workout` / `Standard` into `general running workout` / `generell løpeøkt`
  - the opening message now gets an explicit workout-reference rule instead of using the raw generic label
  - the summary block now says `Workout: general running workout` instead of `Workout: Workout`
  - the bootstrap prompt now explicitly forbids using workout history in the opening message
  - [Models.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift) mirrors the same normalization and first-reply guard for the typed fallback path
- Updated focused verification coverage:
  - [test_xai_voice_post_workout_prompt.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_xai_voice_post_workout_prompt.py)
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
  - [test_voice_session_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_voice_session_contract.py)
- Verification:
  - `python3 -m py_compile xai_voice.py` -> passed
  - `pytest -q tests_phaseb/test_xai_voice_post_workout_prompt.py tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_voice_session_contract.py` -> `26 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`
- 2026-03-18: Hardened the Rex post-workout first-turn path again after a remaining bad opener leak. The primary policy still lives in xai_voice.py, but XAIRealtimeVoiceService.sendInitialAssistantKickoff() was sending a softer generic prompt that gave the model room to improvise exercise context. Tightened both ends of the same runtime path so the opening must stay generic/running-specific when the summary is sparse, and never claim a plank/squat unless the summary explicitly names it.
- 2026-03-18: Inlined the shared Free/Premium/14-day-trial deck directly into Manage Subscription instead of routing through a separate full-screen offers step. Kept the single existing WatchConnectedPremiumOfferStepView, added a manage-subscription presentation mode, bound the initial card to SubscriptionManager.status, disabled the active-plan CTA, and replaced the old offset/drag pager with a native selection-driven pager plus clean auto-rotation timers.

## Review — 2026-03-18 Manage Subscription deck cleanup and current-plan fix

- Kept the single existing subscription flow on the current runtime path:
  - [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift)
  - shared deck in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
  - existing purchase path in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift)
- Made the deck the primary content inside `Manage Subscription`:
  - removed the extra top summary card
  - removed the lower included-items comparison block
  - kept only the shared Free/Premium/14-day-trial deck, `Administrer i App Store`, `Gjenopprett kjøp`, and legal links
- Fixed current-plan resolution on the shared deck:
  - prefer `SubscriptionManager.status`
  - fall back to `SubscriptionManager.resolvedPlanLabel`
  - only then fall back to coarse premium access
  - reused that same resolved plan for the selected page, badge, disabled CTA, and visual emphasis
- Restored CTA hierarchy on the shared cards:
  - only the actual active plan shows the disabled `Current plan` / `Din plan` CTA
  - premium/trial cards keep `Get Premium` / `Start 14-day free trial now`
  - removed the card-level `Manage in App Store` takeover from the shared deck
  - kept `Manage in App Store` only as the smaller secondary action below the deck
- Fixed the trial-card title visibility by moving the top accent strip into real layout space instead of overlaying it over the title area
- Kept the current `TabView(selection:)` pager and the 7-second manage-subscription auto-rotation intact
- Updated focused verification coverage:
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py` -> `22 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Manage Subscription deck-only surface pass

- Simplified [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) again so the body now shows only:
  - the existing shared Free / Premium / 14-day trial deck
  - terms and privacy links
- Removed the remaining screen-level secondary subscription actions from `Manage Subscription`:
  - `Administrer i App Store`
  - `Gjenopprett kjøp`
- Kept purchase and current-plan behavior on the existing shared deck itself:
  - premium and trial cards still use their existing buy/trial CTAs
  - the active plan still shows the existing disabled `Current plan` / `Din plan` state
- Kept the single existing shared pager and purchase flow intact; no new subscription screen or duplicate logic was introduced
- Updated focused verification coverage:
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py` -> `22 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Manage Subscription bottom-actions and trial-CTA visibility pass

- Kept the same single `Manage Subscription -> shared offer deck -> Paywall` runtime path
- Added the screen-level bottom actions back in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift), but only as centered footer actions below the deck:
  - green `Manage in App Store` / `Administrer i App Store` capsule button
  - centered `Restore purchases` / `Gjenopprett kjøp` text action
  - centered terms/privacy links
- Preserved the deck-first layout: no top summary card and no comparison table were reintroduced
- Increased the inline deck height and tightened the inline trial-card spacing in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) so the 14-day trial CTA remains visible
- In inline manage-subscription mode, the trial savings badge is now suppressed to reduce vertical pressure and keep the primary trial button on-screen
- Updated focused verification coverage:
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py` -> `22 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Manage Subscription trial CTA visibility follow-up

- Kept the same single shared subscription deck and purchase flow; no new screen or pager logic was introduced
- Increased the inline deck height again in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) so the trial card has more vertical room inside `Manage Subscription`
- Tightened the inline shared trial card in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift):
  - reduced the dense-layout spacer before the footer CTA
  - shortened the inline trial detail text
  - kept compact inline trial pricing spacing
- Updated the shared trial card CTA copy on the deck to:
  - `Start 14 days free trail now`
- Updated focused verification coverage:
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
- Verification:
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py` -> `22 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Shared subscription deck source of truth, pricing rule, and onboarding name-step lag

- Kept one existing subscription deck only on the current runtime path:
  - [WatchConnectedPremiumOfferStepView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) remains the single card/layout implementation
  - [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) stays a host-only surface
  - onboarding after watch connect reuses the same deck instead of maintaining a second copy
- Moved the shared plan catalog/content ownership out of [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) and into [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) so `Manage Subscription` and onboarding cannot drift
- Unified deck behavior across both contexts:
  - `TabView(selection:)` remains the only pager implementation
  - auto-rotation now runs at `8s` in both onboarding and `Manage Subscription`
  - current-plan resolution stays shared and still prefers `SubscriptionManager.status`, then resolved label, then coarse fallback
- Hardened trial handling on the existing StoreKit path in [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift) and the shared deck:
  - monthly and yearly trial eligibility now comes from actual introductory offers
  - the trial card only shows eligible options
  - the trial CTA disables cleanly when no intro offer is available instead of promising a false 14-day trial
- Added one shared app-owned subscription pricing rule in [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift):
  - Norwegian app language -> `kr`
  - English app language -> `$`
  - trailing `.00` / `,00` is removed when not needed
  - free price uses `0 kr` / `$0`
- Reused that formatter on the existing subscription UI path:
  - shared deck in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
  - existing paywall in [PaywallView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/PaywallView.swift)
- Fixed onboarding name-entry lag on the current identity step in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift):
  - removed name-specific `textContentType` hints from the onboarding name fields
  - delayed autofocus by one main-actor tick
  - delayed continue until after focus/keyboard dismissal
- Updated focused verification coverage:
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_onboarding_theme_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_theme_contract.py)
- Verification:
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_onboarding_theme_contract.py` -> `49 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project /Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-19 V2 cue wording refresh

- Kept the single existing V2 workout cue path:
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) remains the phrase source of truth
  - [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py) mirrors the same ids and text
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) fallback text was updated in the same pass so runtime copy stays aligned if catalog lookup is bypassed
- Strengthened the requested active phrases without changing any ids:
  - `zone.phase.warmup.1` -> `Warmup starts now.` / `Oppvarming starter nå.`
  - `zone.main_started.1` -> `Main set starts now.` / `Hoveddelen starter nå.`
  - `zone.phase.work.default.1` -> `Interval starts now. Bring up the pace.` / `Drag starter nå. Øk farten.`
  - `zone.phase.rest.1` -> `Recovery starts now.` / `Pause starter nå.`
  - `zone.phase.cooldown.1` -> `Cooldown starts now.` / `Nedtrapping starter nå.`
  - `zone.pause.detected.1` -> `Workout paused.` / `Du har pauset økten.`
  - `zone.pause.resumed.1` -> `Workout resumed.` / `Økten er i gang igjen.`
  - `zone.hr_poor_timing.1` -> `No heart rate signal. I'll coach you by time and effort.` / `Mangler pulssignal. Jeg guider deg på tid og innsats.`
  - `zone.structure.work.1` -> `Interval starts now. Bring up the pace.` / `Drag starter nå. Øk farten.`
  - `zone.structure.recovery.1` -> `Recovery now. Ease off and reset.` / `Pause nå. Ro ned og hent deg inn.`
  - `zone.structure.steady.1` -> `Easy pace now. Keep it steady.` / `Rolig tempo nå. Hold det jevnt.`
- Updated the focused canonical cue contract in [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py) so the approved Norwegian fallback and catalog copy match the new active wording

## Review — 2026-03-19 Post-workout live coach startup, first turn, and streaming

- Kept the single existing post-workout live coach runtime path:
  - [WorkoutCompleteView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift) still owns the summary-sheet entrypoint
  - [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift) and its shared view model still drive the transcript/live UI
  - [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift) still owns the websocket/audio lifecycle
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) and [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py) remain the only backend voice bootstrap path
- Reduced startup latency on the current path by warming the backend when the workout summary sheet opens instead of waiting for `startIfNeeded()` alone
- Fixed session-counting semantics on the current quota path:
  - free-tier local usage is no longer counted on optimistic `.connected`
  - `voice_session_started` now fires only after the first real assistant response begins
  - added `voice_cta_tapped`, `voice_first_assistant_response`, and `voice_first_assistant_audio` telemetry on the current `/voice/telemetry` route
- Improved first-turn quality in [xai_voice.py](/Users/mariusgaarder/Documents/treningscoach/xai_voice.py):
  - added a deterministic opening recap brief built only from `PostWorkoutSummaryContext`
  - opening now explicitly requires workout reference, duration, one or two real stats, one short insight, and one question
  - kept the existing running-only / no-invented-exercises guardrails
  - tightened the iOS kickoff in [XAIRealtimeVoiceService.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/XAIRealtimeVoiceService.swift) so it no longer sends a second looser first-turn instruction
- Improved streaming stability and perceived live quality without changing transport architecture:
  - replaced unbounded per-tap audio send tasks with a bounded serial sender that caps queued mic payloads and drops the oldest unsent chunk under pressure
  - kept the same websocket message shape and same existing service
  - added listening / thinking / speaking UI states and transcript auto-scroll in [LiveCoachConversationView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/LiveCoachConversationView.swift)
- Updated focused verification:
  - [test_live_voice_mode_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_live_voice_mode_contract.py)
  - [test_voice_session_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_voice_session_contract.py)
  - [test_xai_voice_post_workout_prompt.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_xai_voice_post_workout_prompt.py)
- Verification:
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `python3 -m py_compile main.py xai_voice.py` -> passed
  - `pytest -q tests_phaseb/test_live_voice_mode_contract.py tests_phaseb/test_voice_session_contract.py tests_phaseb/test_xai_voice_post_workout_prompt.py` -> `26 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project /Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-18 Shared 14-day promo trial card refresh

- Kept the existing shared subscription deck as the single runtime path:
  - [WatchConnectedPremiumOfferStepView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) remains the only Free/Premium/Trial card implementation
  - [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) still hosts that same shared deck inline
  - onboarding after `watchConnected` still reuses the same deck instead of creating a promo-only variant
- Updated the existing trial card to match the reference in [14 days promo.png](/Users/mariusgaarder/Documents/treningscoach/Choose%20plan/14%20days%20promo.png):
  - switched the trial accent from green to a promo blue treatment
  - turned the top trial header into a taller integrated promo band
  - removed the old trial pill/badge so the card headline carries the emphasis
  - restyled the monthly/yearly selectors with darker filled tiles, blue selected border, and glow
  - changed the shared trial CTA to use a blue promo gradient while keeping the same purchase logic
- Increased the inline manage-subscription deck height in [ProfileView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) so the refreshed promo-style trial card keeps its CTA visible without adding vertical scrolling
- Preserved the existing StoreKit-driven behavior:
  - monthly/yearly intro-offer eligibility still controls which trial selectors are shown
  - the existing direct `SubscriptionManager.purchase(...)` path is unchanged
  - the existing `TabView(selection:)` pager and 8-second auto-rotation are unchanged
- Updated focused verification coverage:
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
- Verification:
  - `python3 scripts/generate_codebase_guide.py --check` -> `[OK] CODEBASE_GUIDE.md is in sync`
  - `pytest -q tests_phaseb/test_monitor_management_contract.py tests_phaseb/test_subscription_paywall_contract.py tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_onboarding_theme_contract.py` -> `49 passed`
  - `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project /Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Review — 2026-03-19 Warmup/recovery countdown split on existing V2 runtime path

- Kept the single existing workout-cue runtime path and added phase-specific prep countdown ids only where the user asked:
  - warmup/recovery now use `zone.countdown.warmup_recovery.{30,10,5,start}.1`
  - work/main phases still use the generic countdown family
  - no second countdown engine or parallel cue path was introduced
- Updated the single source-of-truth cue surfaces together:
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py)
  - [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py)
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
- Changed runtime behavior on the existing event path:
  - warmup and recovery countdowns now emit `30 / 10 / 5 / start`
  - the special warmup/recovery countdown family is chosen only for `phase == warmup` or recovery/rest
  - generic countdown mapping remains in place for work/main segments
  - warmup-end `start` keeps the warmup/recovery phrase id even when the canonical phase has already transitioned
- Regenerated and resynced the V2 audio assets on the same pack path:
  - `python3 tools/generate_audio_pack.py --version v2 --changed-only --sync-r2` -> generated `34` files (`27 changed`, `7 new`) and uploaded the refreshed V2 pack to R2
  - `python3 tools/select_core_bundle.py --version v2` -> copied `124` bundle MP3s into [CoreAudioPack](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack)
- Updated focused verification:
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_workout_cue_catalog_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_workout_cue_catalog_contract.py)
  - [test_r2_audio_pack_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_r2_audio_pack_contract.py)
  - [test_audio_pack_manifest_coverage.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_audio_pack_manifest_coverage.py)
  - [test_select_core_bundle.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_select_core_bundle.py)

## Review — 2026-03-19 Shared Premium success popup on existing subscription path

- Kept the single existing purchase/runtime path for Premium and trial entry:
  - the shared [WatchConnectedPremiumOfferStepView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) still owns Premium and trial CTAs
  - both onboarding and [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) still reuse that same shared deck
  - no second subscription success flow or duplicate paywall route was introduced
- Added one shared success presentation on the same deck path:
  - [SubscriptionManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/SubscriptionManager.swift) now returns a verified purchase outcome after entitlement refresh
  - [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) now shows a single Premium success popup for both Premium purchase and 14-day trial activation
  - onboarding and `Manage Subscription` stay synced because the popup lives on the shared deck, not in the hosts
- Preserved current behavior:
  - the popup shows only after StoreKit reports a successful purchase and `refreshStatus()` completes
  - onboarding continues through the existing `onContinue` path after the popup button
  - `Manage Subscription` dismisses the popup and stays on the existing screen
- Updated focused verification:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_monitor_management_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_monitor_management_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)

## Review — 2026-03-19 Workout cue single source of truth + BOTH motivation

- Kept the single existing workout cue runtime path:
  - [phrase_review_v2.py](/Users/mariusgaarder/Documents/treningscoach/phrase_review_v2.py) is now the authoring source for active workout cue text and metadata
  - [tts_phrase_catalog.py](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py) remains a compatibility shell and now derives workout cue entries from that authoring source instead of owning separate workout wording
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) now reads workout phrase text from the review source on the live runtime path
  - [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) now uses the review source for V2 workout cue metadata
- Extended the existing motivation path instead of creating a second one:
  - interval and easy-run stage motivation rows are marked `BOTH`
  - the no-HR structure-driven path can now reuse staged motivation after the first structure cue in the same segment, while preserving the initial structure guidance
  - no parallel motivation runtime or duplicate phrase family was introduced
- Updated validation/tests to match the approved stronger cue wording:
  - raised workout cue word caps just enough for the approved longer structure/no-HR lines
  - updated phrase review summary expectations to the current reviewed set
- Updated focused verification:
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)
  - [test_context_aware_max_silence.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_context_aware_max_silence.py)
  - [test_zone_motivation_stages.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_motivation_stages.py)
  - [test_phrase_catalog_v2_review.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_phrase_catalog_v2_review.py)
  - [test_workout_cue_catalog_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_workout_cue_catalog_contract.py)

## Review — 2026-03-19 Premium monthly deck price + purchase routing

- Kept the single existing subscription deck/runtime path:
  - [ManageSubscriptionView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift) still hosts the shared [WatchConnectedPremiumOfferStepView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift)
  - onboarding still reuses that same shared deck
  - no new Premium card, no duplicate paywall flow, and no parallel purchase path were introduced
- Fixed the product mismatch at the shared CTA:
  - the Premium card in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) now purchases the monthly SKU instead of the yearly SKU in both onboarding and `Manage Subscription`
  - this keeps the Premium monthly card price and the purchased App Store product aligned
- Tightened the fallback monthly USD amount in [Config.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Config.swift):
  - USD fallback monthly price is now `9.9`
  - NOK fallback monthly price remains `129`
- Tightened the shared yearly trial pricing on the same path:
  - USD fallback yearly price is now `99`
  - the shared trial card savings math in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) now falls back to configured monthly/yearly prices when StoreKit products are not loaded yet
  - this keeps the yearly trial option and savings text aligned even during cold product loads
- Updated NOK card fallback pricing on the same shared path:
  - NOK fallback monthly price is now `99`
  - NOK fallback yearly price is now `799`
  - the same shared savings math now rounds that NOK fallback pair to a `33%` yearly discount
- Updated focused verification:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)

## Review — 2026-03-19 NOK pricing update + V2 pack verification path

- Kept the single existing shared subscription card/runtime path:
  - [Config.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Config.swift) still owns the fallback monthly/yearly subscription pair
  - [WatchConnectedPremiumOfferStepView](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift) still reuses that same pair for `Manage Subscription` and onboarding
  - no separate pricing table or deck variant was introduced
- Updated shared NOK fallback pricing:
  - monthly NOK fallback is now `99`
  - yearly NOK fallback is now `799`
  - shared yearly savings math now rounds that pair to a `33%` yearly discount before StoreKit loads
- Verified and refreshed the existing V2 audio-pack path:
  - refreshed [output/phrase_review](/Users/mariusgaarder/Documents/treningscoach/output/phrase_review) and [output/spreadsheet](/Users/mariusgaarder/Documents/treningscoach/output/spreadsheet) exports from the current phrase sources
  - fixed a missing `get_phrase_by_id` import in [tools/generate_audio_pack.py](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py) so the V2 generator works again on the current tool path
  - verified local V2 pack status against build cache: `124 phrases`, `0 missing`, `0 changed`
  - refreshed bundled [CoreAudioPack](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Resources/CoreAudioPack) from the current V2 manifest
- Updated focused verification:
  - [test_onboarding_inspo_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_onboarding_inspo_contract.py)
  - [test_subscription_paywall_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_subscription_paywall_contract.py)
  - [test_generate_audio_pack_sample_and_latest.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_generate_audio_pack_sample_and_latest.py)
  - [test_r2_audio_pack_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_r2_audio_pack_contract.py)
  - [test_select_core_bundle.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_select_core_bundle.py)

## Review — 2026-03-19 NO_HR breath tone refinement

- Kept the single existing workout coach runtime path:
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) still passes the same breath fields into [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) still owns the same NO_HR hierarchy and event families
  - no second motivation path, no new event family, and no breath-first controller were introduced
- Tightened the NO_HR fallback policy so phase stays in charge of intent:
  - low breath confidence now ignores breath and stays on deterministic phase-neutral fallback
  - medium confidence adds only a mild calming bias inside the same phase
  - high confidence can refine tone, but only within the current phase
  - heavy breathing in work can switch to control/breath guidance, while stable breathing keeps push tone in work and steady/calm tone in easy or recovery
- Tightened anti-silence timing so breath only shortens silence when confidence is genuinely high, not merely barely reliable
- Updated focused verification:
  - [test_context_aware_max_silence.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_context_aware_max_silence.py)
  - [test_zone_motivation_stages.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_motivation_stages.py)
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)

## Review — 2026-03-19 NO_HR tone buckets + free run parity

- Kept the single existing runtime path:
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) remains the only workout cue/motivation selector
  - no new phrase ids, no new MP3 files, and no parallel motivation system were introduced
- Added a small internal runtime mapping in [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py):
  - `phase_family -> tone_bucket -> candidate_phrase_ids`
  - `interval` and `easy_run` structure-driven motivation now select from existing `interval.motivate.*` / `easy_run.motivate.*` ids
  - fallback/max-silence now selects only from existing `zone.silence.work.1`, `zone.silence.rest.1`, and `zone.silence.default.1`
- Kept HR-driven motivation timing/logic unchanged and applied tone-bucket phrase selection only in `NO_HR` / `structure_driven`
- Tightened free-run parity on the existing easy-run path:
  - free run still skips warmup and never auto-emits `workout_finished`
  - free run can emit halfway only when a target duration exists
- Updated focused verification:
  - [test_context_aware_max_silence.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_context_aware_max_silence.py)
  - [test_zone_motivation_stages.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_motivation_stages.py)
  - [test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)
  - [test_canonical_event_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_canonical_event_contract.py)

## Review — 2026-03-19 Free run continuous failsafe hardening

- Kept the single existing free-run request path:
  - [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift) still posts the same `/coach/continuous` request
  - [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) still owns the response contract
  - [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py) still decides free-run `main_started`
- Hardened [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) so once a valid `zone_tick` exists, later downstream exceptions degrade to an event-preserving response instead of collapsing all the way to `continuous_failsafe`
- This specifically protects free-run first ticks when backend TTS/output work fails:
  - `main_started` is preserved
  - `events` and `zone_phrase_id` are preserved
  - `audio_url` can fall back to `null`, allowing the iOS runtime to keep using the existing phrase-pack path
- Added focused contract coverage in [test_zone_continuous_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_continuous_contract.py) for a forced-TTS-failure free-run first tick

## Review — 2026-03-19 Export compliance plist alignment

- Confirmed the main iPhone app target already sets `ITSAppUsesNonExemptEncryption = NO` in [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist)
- Added the same explicit key to the watch app target in [Info.plist](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/Info.plist) so export-compliance stays explicit across the shipped bundle
- Kept the existing target/plist setup; no new config path or build setting indirection was introduced
