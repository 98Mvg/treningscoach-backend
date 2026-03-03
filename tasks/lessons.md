# Lessons / Execution Guardrails

Updated: 2026-03-03

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
