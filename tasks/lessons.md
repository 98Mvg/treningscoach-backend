# Lessons / Execution Guardrails

Updated: 2026-03-17

## Workflow Orchestration

1. Plan-first for non-trivial work.
- Use checkable steps.
- Re-plan immediately if the path is failing.

2. Keep main context clean.
- Do targeted exploration before edits.
- Parallelize independent reads/checks.

3. Self-improvement loop.
- After corrections, write the lesson here.
- Turn repeated mistakes into explicit guardrails.

4. Verification before done.
- Do not mark complete without proof.
- Validate with build/tests/logs relevant to touched code.

5. Elegance, balanced.
- Ask if there is a simpler and more robust fix.
- Avoid over-engineering small fixes.

6. Autonomous bug-fixing behavior.
- When a bug is reported, investigate logs/errors/tests first.
- Fix root cause with minimal impact.

## Core Principles

- Simplicity first.
- No temporary patching when a clean fix is possible.
- Minimal impact: touch only what is necessary.

## Session-Specific Lessons

- 2026-03-17: When Render/backend timeouts appear across many iOS endpoints at once, treat it as one shared availability problem. Fix it in `BackendAPIService` with a small cooldown/circuit-breaker on the existing runtime path instead of patching each endpoint separately.
- 2026-03-17: Do not let `/auth/me` bypass the shared backend service; if profile hydration uses `URLSession.shared` directly, it will miss the same timeout/backoff policy as analytics, subscription, coaching, and voice.
- 2026-03-17: Keep source-contract tests aligned to current SwiftUI structure, not removed internal computed properties or old CTA analytics names; otherwise verification fails on test drift instead of real regressions.
- 2026-03-17: When curating V2 phrases, update the review source (`phrase_review_v2.py`), the fallback catalog (`tts_phrase_catalog.py`), and the deterministic backend text path (`zone_event_motor.py`) on the same pass or the app, pack generation, and tests drift immediately.
- 2026-03-17: For R2 pack updates, prefer `tools/generate_audio_pack.py --changed-only --sync-r2` after small copy/variant edits so unchanged MP3s keep their existing audio identity while only genuinely changed/new phrases are regenerated and uploaded.
- 2026-03-17: After updating V2 and syncing R2, run `tools/select_core_bundle.py --version v2` to keep the app’s bundled offline `CoreAudioPack` aligned with the same V2 manifest; otherwise offline fallback will lag behind the live pack.
- 2026-03-16: When onboarding copy feels too thin, enrich the existing step views in `OnboardingContainerView.swift` with compact Coachi explanation cards instead of adding a second explainer flow or copying inspiration screens literally.
- 2026-03-16: For HR onboarding, define the metric first (`makspuls`, `hvilepuls`) and then give one concrete measurement rule; that is enough clarity without turning the page into a medical article.
- 2026-03-16: When asking about endurance habits, users need explicit examples of what counts and what does not. Keep those examples on the same page as the yes/no choice so they do not have to guess before answering.
- 2026-03-16: Intensity labels (`lav`, `moderat`, `høy`) are too abstract on their own; anchor them to breathing, control, and how long the effort can be sustained.
- 2026-03-16: Summary CTA gating and quota accounting are separate concerns; keep `Talk to Coach Live` visible as a discovery surface, but only consume a free daily session after the realtime voice connection actually reaches `.connected`.
- 2026-03-16: When a live-voice policy exists on both iOS and Flask, sync the numeric defaults (`sessions/day`, free/premium max duration) in code, `.env.example`, and ops docs on the same pass or launch truth drifts immediately.
- 2026-03-16: When redesigning existing settings/profile surfaces from inspiration screenshots, first map them onto the fields that already live in `UserDefaults`, auth state, and the current SwiftUI path; do not invent a second profile model just to match UI.
- 2026-03-16: If a free signed-in feature is gated in SwiftUI, prefer session validity (`hasUsableSession()`) over `currentUser != nil`; profile hydration can lag behind token availability and incorrectly lock users out.
- 2026-03-16: Keep support surfaces separated by intent: one short “Contact support” screen with a clear CTA, and a separate FAQ/instructions screen. Mixing long FAQ text into the support entry page makes the profile tab feel unfinished.
- 2026-03-16: When a home screen feels visually off-center, center the content column first and give individual sections explicit leading alignment as needed instead of forcing the whole root stack to `.leading`.
- 2026-03-16: If FAQ content is moved into support, remove the separate runtime entry point and lock the new consolidated support surface with contract tests so profile navigation does not drift back into duplicate help pages.
- 2026-03-16: Launch-surface cleanup must include metadata and legal anchors, not just visible hero/FAQ copy; stale canonical URLs and `#` footer links are launch bugs too.
- 2026-03-16: If Swift reports `Cannot find '<type>' in scope` right after a new file lands, check `project.pbxproj` target membership first; the file may exist on disk but still be absent from `PBXFileReference` and `PBXSourcesBuildPhase`.
- 2026-03-16: When Supabase/Postgres is reached through the pooler (`aws-...pooler.supabase.com`), do not rely on Flask `db.create_all()` at boot; let Alembic own schema changes to avoid PgBouncer/prepared-statement startup crashes.
- 2026-03-16: For ship-day infrastructure work, keep Flask as the single app-facing API and wrap Supabase/Auth providers behind the existing Coachi routes instead of introducing a parallel client/server auth path.
- 2026-03-16: When a launch plan requests a simpler schema than the live product already uses, map the plan onto the real runtime tables instead of duplicating `workouts`/`subscriptions` storage.
- 2026-03-16: Treat legal/support/paywall copy drift as a launch bug; fix the live SwiftUI/runtime surfaces and website routes together so Coachi branding and URLs stay consistent.
- 2026-03-16: If the user removes a scope item mid-plan, remove it from implementation and final reporting instead of quietly carrying the old task forward.
- 2026-03-16: Stale pre-launch copy often survives inside dead preview/demo components; remove the dead component path, not just the visible string, when cleaning launch surfaces.
- 2026-02-23: Guard all runtime UI numeric inputs (`NaN`/`Inf`) before CoreGraphics/SwiftUI drawing.
- 2026-02-23: When logs show `invalid numeric value (NaN) to CoreGraphics`, prioritize finite/clamp guards in `trim`, `Path.addArc`, animated scales, and Canvas rect/opacity math.
- 2026-02-23: If simulator logs show repeated `RBLayer: full image queue`, treat it as render-pressure/perf issue from continuous animations and reduce background Timeline activity first.
- 2026-02-23: Hidden tabs that stay mounted must not keep high-frequency animation loops running (Particle/Canvas/wave timelines should pause when tab is not visible).
- 2026-02-23: Keep coach persona contract strict: persona changes tone only, never event logic/cooldowns/scoring.
- 2026-02-23: For Phase 3 requests, derive `hrQuality` from current signal quality + watch/source state, not watch connection alone.
- 2026-02-23: For talk-to-coach UX, prioritize one clear tap action (no competing long-press gesture) on the primary mic CTA.
- 2026-02-23: Never send workout-talk request with empty `session_id` without fallback; use generic talk endpoint to preserve user response path.
- 2026-02-23: Route explicit user questions to a dedicated Grok-first Q&A path instead of generic coaching prompts, so answer quality matches "Ask Coach" intent.
- 2026-02-23: Enforce response shape after model output (max 3 sentences) to keep spoken Q&A concise even when provider responses are verbose.
- 2026-02-23: For Ask Coach, apply strict domain guardrails before any model call (training/health only) to avoid answering unrelated, sexual, or harassing prompts.
- 2026-02-23: Keep Q&A concise by default, but make sentence cap configurable (allow >3 when needed) instead of hard-coding a strict 3-sentence limit.
- 2026-02-23: Do not rely only on backend heuristics for question detection; include explicit `response_mode=qa` from iOS client payloads for deterministic behavior.
- 2026-02-23: Keep onboarding as a single runtime path (no parallel onboarding engines); add new data-capture steps directly inside `OnboardingContainerView` and persist through `AppViewModel`.
- 2026-02-23: For HR-zone products, onboarding must persist `user_age`, `hr_max`, and `resting_hr` before first workout so backend coaching can personalize immediately.
- 2026-02-23: Long onboarding flows need visible progress (`Step X/Y`) to reduce perceived friction and drop-off.
- 2026-02-23: `resetOnboarding()` should clear all onboarding-dependent defaults (profile + HR keys), not only the completion flag.
- 2026-02-23: When updating launch visuals, keep root and backend launch templates/static assets in sync to avoid drift and contract-test failures.
- 2026-02-23: If marketing images include baked text overlays (e.g., "Push it"/"Perfect pulse"), exclude them from production and keep tests aligned with clean assets.
- 2026-02-23: Theme work should update both CSS variables and runtime meta theme-color so iOS Safari/browser UI stays consistent in light/dark mode.
- 2026-02-23: iOS light/dark support can be silently broken by a global `.preferredColorScheme(.dark)`; remove root-level force before tuning component colors.
- 2026-02-23: For onboarding readability on photo backgrounds, pair blurred image layers with step-specific overlay gradients instead of increasing text shadow/noise.
- 2026-02-23: In SwiftUI onboarding forms, hard-coded `Color.white.opacity(...)` borders fail in light mode; route all borders through adaptive theme tokens.
- 2026-02-23: First-launch value onboarding should stay fixed at four short promise pages with persistent CTAs; avoid mixing these pages with profile-form onboarding steps.
- 2026-02-23: For conversion-oriented onboarding, keep auto-advance between 5-10 seconds and retain manual dot navigation so users control pacing.
- 2026-02-23: Square onboarding images on tall iPhones must use a dual-layer render (blurred fill + foreground `scaledToFit`) to avoid aggressive crop/zoom cutting key content.
- 2026-02-23: Keep a short "why we ask this data" step before DOB/HR fields to improve completion and trust in personalized zone coaching.
- 2026-02-23: For talk-to-coach speech UX, suppress cancellation/transitional speech-recognition errors (`kAFAssistantErrorDomain` 1101/1107/1110, canceled requests) to avoid false error logs after successful captures.
- 2026-02-23: iPhone 15 onboarding hero cards need explicit width constraints tied to screen width; relying on `maxWidth` alone can clip text off-screen.
- 2026-02-23: Keep iOS verification split: `xcodebuild` for compile confidence, real-device pass for layout confidence when CoreSimulatorService is unstable.
- 2026-02-25: Onboarding layout bugs can come from parent/window sizing (scene not expanding, split/mac destination) not just the card view; enforce full-window frames at root/container and use a finite centered content width (`layoutWidth`) instead of `UIScreen.main.bounds` clamps.
- 2026-02-25: If intro page is fixed but later onboarding pages still clip, root cause is usually outside the intro view; apply the same finite-width pattern to shared onboarding containers (`OnboardingScaffold`, `AuthView`) so every step follows one layout contract.
- 2026-02-25: Inside onboarding `ScrollView`, avoid unconstrained horizontal growth (`maxWidth: .infinity` chains without a bounded width). Use `layoutWidth` + `contentWidth`, frame content explicitly, and keep `.clipped()` at the container edge.
- 2026-02-25: Onboarding should allow vertical overflow only when needed. Standardize on `ScrollView(.vertical, ...)` with `.scrollBounceBehavior(.basedOnSize, axes: .vertical)` and no horizontal scroll path.
- 2026-02-25: Status bar behavior must be controlled from onboarding container level (`.statusBar(hidden:)`) so all steps stay consistent instead of per-page overrides.
- 2026-02-25: Keyboard can inflate `geo.safeAreaInsets.bottom` on onboarding forms; cap bottom CTA/spacer insets (do not directly use full keyboard-sized inset) or form content may appear to disappear while typing.
- 2026-02-25: Compact calendar `DatePicker` can clash with fixed bottom CTAs in onboarding flows; prefer wheel-style date pickers for birth date so selection is naturally scrollable and stays inside layout bounds.
- 2026-03-01: Audio pack must be manifest-driven. Keep `manifest.json` + `latest.json` as the only authority for local pack sync state.
- 2026-03-01: Enforce SHA256 verification both for manifest bytes and each downloaded MP3 before persisting files.
- 2026-03-01: Never purge stale audio files during active workouts; allow cleanup only in safe states (`idle`/`complete`) and manual reset paths.
- 2026-03-01: Keep version-isolated local pack directories and dynamic version lookup from sync manager to avoid stale-path drift.
- 2026-03-01: For voice safety, maintain persona-scoped audio lookup and prevent toxic/performance phrases from loading for personal-trainer persona.
- 2026-03-03: In zone-event runtime, do not emit `hr_signal_lost` on first bootstrap tick when HR starts missing; only emit after a stable connected->disconnected transition.
- 2026-03-03: Interval cue order must explicitly include warmup-end countdowns (`30/15/5/start`) before main-zone coaching.
- 2026-03-03: Countdown reliability depends on poll cadence; keep interval warmup/recovery on tighter `/coach/continuous` wait budgets to avoid skipping countdown windows.
- 2026-03-05: Real Apple Watch workout testing requires proper Apple Developer Program provisioning; Personal Team profiles cannot ship Watch HealthKit workout capabilities for production-style device validation.
- 2026-03-05: Keep watch-gated start non-blocking on iPhone: always preserve immediate local fallback and send deferred watch payload via `updateApplicationContext` when Watch is unreachable.
- 2026-03-05: Start/ACK correlation must use `request_id`; late watch ACKs should never restart an already-running iPhone workout.
- 2026-03-05: BLE live HR reliability improves with explicit scan timeout + reconnect backoff + cancellation of pending reconnect/scan work items during stop/power-state transitions.
- 2026-03-05: Arbiter edge-case tests should use an injected clock (`nowProvider`) and deterministic evaluate hook to validate freshness/promotion/demotion without timing flakes.
- 2026-03-05: For iOS 17+, use `AVAudioApplication.shared.recordPermission` instead of deprecated `AVAudioSession.recordPermission` in workout payload preflight checks.
- 2026-03-16: Treat iOS `profile_<uuid>` personalization IDs as runtime-only keys. Never persist them into DB tables that foreign-key to `users.id`.
- 2026-03-16: Runtime profile persistence should ignore empty snapshots; if all profile fields are `None`, return defaults instead of creating a blank `user_profiles` row.
- 2026-03-16: Focused backend route tests for `/coach/continuous` must account for current mobile auth and audio-signature validation, or they will fail for the wrong reason and hide the real regression.
- 2026-03-16: Do not duplicate subscription entry points between the root profile tab and `Administrer abonnement`; keep offers/discovery on the dedicated subscription screen and keep the root settings list task-focused.
- 2026-03-16: In nested settings screens, keep destructive actions at the very bottom and avoid colocating them with routine actions like sign-out or language/theme toggles.
- 2026-03-16: Never let SwiftUI `body` reads call helpers that mutate `@Published` state; live availability/count queries must be side-effect free or they will trigger `Publishing changes from within view updates is not allowed`.
- 2026-03-16: If users review onboarding data in a summary screen, make each summary row jump back to the owning step instead of forcing linear back-navigation through the whole flow.
- 2026-03-16: Realtime voice sessions should send an explicit first-response kickoff after connect; relying only on VAD/user speech can leave the coach silent even when the socket is healthy.
- 2026-03-16: If a monetization surface depends on a user milestone like successful watch connection, insert it on that exact onboarding branch instead of showing a generic upsell earlier or elsewhere in settings.
- 2026-03-16: New onboarding monetization steps should reuse the existing `PaywallView` purchase path; keep the bridge screen explanatory and let the actual StoreKit handling stay in one place.
- 2026-03-16: When handing work over between agents, create a repo-local sync note with pushed commit, runtime path, changed files, remaining local-only artifacts, and clear guardrails so the next agent does not need to reconstruct state from chat history.
- 2026-03-16: Agent handoff notes are more useful when they separate remaining fix work, remaining polish work, and remaining manual launch work; otherwise the next agent cannot tell what is code vs ops vs QA.
- 2026-03-16: Shared `ObservableObject` singletons used by SwiftUI screens must not publish synchronously from `init()` or other code paths that can run during first render; seed initial values without publish and defer later `@Published` updates to the next main-loop turn when needed.
- 2026-03-16: If onboarding monetization policy changes from "only after watch connected" to "all non-premium users", update the route contract test in the same pass so repo truth matches product intent immediately.
- 2026-03-16: Subscription screens feel more trustworthy when `Manage subscription` shows the user’s current plan explicitly (`Free`, `Free trial`, `Premium`) in the same screen as the included-items comparison instead of only showing plan badges.
- 2026-03-16: On paywall-like screens reached from profile/settings, keep the primary CTA anchored in a bottom safe-area action section so the action remains visible even when the plan cards scroll.
- 2026-03-16: Rename onboarding enum cases when product meaning changes; keeping `watchConnectedOffer` after it became a general Premium bridge created misleading chat answers and weaker code readability.
- 2026-03-16: When a summary screen depends on workout values after stop/reset, freeze a completion snapshot in the view model and render from that snapshot; otherwise duration, BPM, and XP state can silently disappear before the summary animates.
- 2026-03-16: Launch-grade legal/support work should update both the public HTML pages and the source markdown/legal drafts in the same pass, then sync the contract tests; otherwise the website and internal source-of-truth drift immediately.
- 2026-03-16: Checking whether Resend is "done" is not a code question alone; confirm both runtime wiring and env presence. If `RESEND_API_KEY`, `EMAIL_PROVIDER`, `EMAIL_SENDING_ENABLED`, and `EMAIL_FROM` are missing, treat the integration as not activated.
- 2026-03-16: When the user provides real legal-entity data mid-pass, patch the active website templates and the source legal drafts together. Do not update only the markdown or only the public HTML.
- 2026-03-16: For a Norwegian sole proprietorship, keep the legal identity explicit as `GAARDER (enkeltpersonforetak)` plus `org.nr.` on privacy, terms, and support surfaces. If address is still missing, call that out as the next remaining legal gap instead of inventing one.
- 2026-03-16: SwiftUI `Picker` views must never render with a selection value that has no matching `.tag`. Seed picker-backed `@State` with a valid default in `init()` instead of relying on `.onAppear`, or Xcode will emit undefined-behavior warnings before the first frame.
- 2026-03-16: When handing XP summary work to another agent, document the snapshot contract explicitly: the summary must read from `completedWorkoutSnapshot`, and regressions usually mean the stop/reset ordering drifted, not that the product rule changed.
- 2026-03-17: Keep WatchConnectivity control-plane and live HR data-plane separate. `updateApplicationContext` is acceptable for start/stop/session state, but queued live HR fallback should use `transferUserInfo`, with `sendMessage` kept as the fast path.
- 2026-03-17: Apple Watch HR startup needs an explicit `watch_starting` grace state on the iPhone->backend tick path; otherwise deterministic coaching logic will misclassify transport warmup as missing sensors and emit the wrong notices.
- 2026-03-17: For live workout arbitration, treat watch `.degraded` reachability as watch-attached, not watch-disconnected. Freshness of `wc`/`ble` samples should determine live-HR availability, not `WCSession.isReachable` alone.
- 2026-03-17: Do not inject old HK snapshots into active workout HR arbitration. Age-gate startup HK samples aggressively before they can become the selected source, or the arbiter will churn `hk -> none` during watch startup.
- 2026-03-17: If a watch-backed workout starts in deferred mode, retry exactly one live start message with the same `request_id` when reachability recovers; do not generate a second start request or a new correlation ID.
- 2026-03-17: The iPhone Watch app entry name comes from the watch target's `CFBundleDisplayName`, not the iPhone target. Brand/name fixes for that list should be made in `TreningsCoachWatchApp/Info.plist`.
- 2026-03-17: Keep Apple Watch branding on the existing watch target by reusing the main Coachi `AppIcon` asset when the watch icon has drifted into a cropped or generic-looking variant; do not create parallel icon catalogs or alternate target structures for a simple branding correction.
- 2026-03-17: For returning users, treat `user_profiles.name` as the authoritative onboarding name and expose it through `/auth/me`; provider `display_name` can be random or lossy and should only be a fallback when no stored onboarding name exists.
- 2026-03-17: The iPhone Watch app installed-list label and the icon as rendered on Apple Watch are related but not identical acceptance targets. If the user asks to fix `Coachi Watch` under `My Watches`, keep the display-name fix in the watch target plist but do not assume the watch icon itself should be rebranded.
- 2026-03-17: If guest mode is an intentional product path, do not detect it by sending the first protected backend request and waiting for a 401. Pre-arm guest suppression before the first coaching tick when no usable session exists.
- 2026-03-17: Best-effort protected calls like `/subscription/validate` should short-circuit when there is no access token and no refresh token at all; otherwise guest mode generates misleading auth noise that obscures unrelated debugging like watch-HR transport.
- 2026-03-17: For pack curation, do not invent a third phrase workflow. Keep V2 review as the single curation path, add category-first exports on top of it, and leave candidate queue as a side tool for idea generation only.
- 2026-03-17: Category-first phrase review works better when it shows only current active rows; future and compatibility rows should stay in the full V2 review flow so the “what we have now” curation view stays focused.
- 2026-03-17: When importing structured phrase-curation edits back into `phrase_review_v2.py`, anchor variant numbering by `family + event`, not family alone. Countdown and pause families contain multiple event-specific id stems, so naive family-wide numbering will generate the wrong phrase ids.
- 2026-03-17: Dynamic countdown copy like `2/4 done` should stay on the existing zone-event path but bypass local audio-pack playback. Use a `.dynamic` phrase-id suffix and let iOS fall through to backend TTS, otherwise local pack audio will silently override the dynamic progress text.
- 2026-03-17: Halfway countdowns should be modeled as deterministic progress events, not as a second progress engine. Reuse `countdown_fired_map`, keep `interval_countdown_30` higher priority, and suppress halfway when it collides with the existing 30-second cue.
- 2026-03-17: If the user wants simpler halfway wording for now, keep both halfway events alive but point them at the same copy temporarily. Do not remove the session-halfway event just because `2/4 done` is postponed.
- 2026-03-17: `warmup_started`, `main_started`, `pause_detected`, and `pause_resumed` are shared `BOTH` context cues. Treat them as phase/session narration that should stay coherent in both HR and no-HR runtime paths, not as HR-only correction phrases.
- 2026-03-17: New shared countdown/runtime cues should also be represented in `phrase_review_v2.py` as `BOTH` rows, even if the app currently bypasses local-pack playback for `.dynamic` ids. V2 curation must still show the real active phrase surface before upload/review.
- 2026-03-17: The app-side audio truth was already R2 `latest.json` + `manifest.json`; the missing source-of-truth fix was upstream. For V2 packs, generate from active runtime rows in `phrase_review_v2.py`, not by treating review as an ID-only filter over `tts_phrase_catalog.py`.
- 2026-03-17: `.dynamic` suffix should not mean "always bypass the pack." If a curated V2 phrase id can exist in the synced pack, iOS should try local/R2 audio first and only fall back to backend TTS if the file is actually missing.
- 2026-03-17: A one-step `--sync-r2` workflow on the existing generator is safer than inventing a parallel upload script. Keep generation, manifest write, `latest.json`, upload, and stale-R2 prune on the same tool path.
- 2026-03-17: For non-motivation workout cues that already have multiple active V2 variants, keep phrase rotation backend-owned. The app already honors backend `phrase_id`, so adding a second rotation layer in iOS would create drift between pack truth and runtime behavior.
- 2026-03-17: Motivation timing is already stricter than normal context cues: interval motivation waits for valid in-zone HR plus sustain and skips the first 10 seconds of a rep; easy-run motivation uses a separate sustain + cooldown path. Check those guards before assuming “the coach is repetitive” is a trigger problem.
- 2026-03-17: Render deploys from the root Flask runtime (`main.py` + `Procfile` + root `requirements.txt`). Do not fix deployment failures by editing stale `backend/requirements.txt` alone; either mirror root truth there or leave it as a compatibility shim.
- 2026-03-17: Tool-only dependencies like `boto3` should not live in production `requirements.txt` just because a local script uses them. Put them in a dedicated tool requirements file and let runtime stay focused on what Gunicorn/Flask actually imports.
- 2026-03-17: `SQLAlchemy` does not install the `psycopg` driver for you. If runtime normalizes `DATABASE_URL` to `postgresql+psycopg://`, keep `psycopg[binary]` explicit in root production requirements even if another package happened to pull it transitively before.
- 2026-03-17: Local reminders are more useful if they land back in a concrete app destination. Keep reminder scheduling and notification-open handling on the existing `PushNotificationManager` path, and always attach a stable deep link when the reminder is workout-specific.
- 2026-03-17: Best-effort mobile analytics endpoints should accept the events the shipped iOS runtime actually emits. If new push or returning-user events are added on device, update the backend allowlist in the same pass or production telemetry will drift silently.
- 2026-03-17: CoachScore polish should reuse persisted workout history instead of inventing a second progress model. Shared helpers like `currentWorkoutStreak()` belong in the model layer so Home and Workout Summary stay consistent.
- 2026-03-17: When a feature pass uncovers unrelated compile errors on the same runtime path, fix them in the same batch if they block verification and the correction is local and obvious. It is better to keep the build green than to preserve a broken intermediate state.
- 2026-03-17: The active marketing site currently serves the `codex` variant by default. If a web-nav request is about the live landing page, patch `templates/index_codex.html` first instead of assuming `index_launch.html` is the production truth just because it already has a hamburger.
- 2026-03-17: Responsive navigation overflow should not rely only on viewport breakpoints when the page supports multiple languages. Recalculate collapse state after language changes and on resize so longer English/Norwegian labels do not wrap or clip.
- 2026-03-17: When the user asks whether Resend/auth are “working,” verify both configuration and runtime contracts. Local env presence alone is not enough, but source tests plus keychain/refresh-token persistence checks give a launch-safe answer without inventing a second auth story.
