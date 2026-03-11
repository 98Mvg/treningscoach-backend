# 2026-03-11 Session Learnings — Onboarding Refresh And Welcome Retirement

## Scope
- Tightened the first onboarding carousel and CTA copy on the single existing iPhone onboarding path.
- Reworked the required-account auth surface without introducing a second auth architecture.
- Retired dedicated workout welcome audio end-to-end so workouts now begin directly on the normal coaching/event path.

## What changed
- The intro carousel footer no longer carries stale helper text or trust badges; the primary CTA is now `Registrer deg`, the dots are larger, and the final intro page now explains supported watch/sensor options plus the no-watch breath-analysis fallback.
- The auth step now shows active Apple sign-in, visible but disabled Google sign-in, and passwordless email registration with a required terms/privacy checkbox. The flow remains on the existing `/auth/*` backend path.
- The onboarding sequence after auth is now `identity -> personalized hello -> 4-page explainer -> existing profile steps`, with the old data-purpose page replaced by a personalized hello step.
- The shared onboarding scaffold now uses a keyboard-safe bottom inset instead of a fixed footer, which removes the overlap/lag feel around first-name and last-name entry.
- `welcome.standard.*` is gone from the phrase catalog, generated manifests, bundle-selection rules, iOS workout start flow, web/demo references, and release smoke checks. `GET /welcome` now returns `410 Gone` as an explicit deprecation path.

## Why it matters
- Onboarding copy and behavior now match product truth: account required, Apple/email only, and no misleading `Start free` messaging.
- The name/auth steps are less fragile on device because the action area no longer competes with keyboard layout.
- Dedicated welcome audio was a parallel startup path with extra artifacts, stale MP3 storage, and extra latency before normal coaching. Removing it reduces drift and keeps workout startup on the same deterministic event path as the rest of the runtime.

## Guardrails
- Do not reintroduce guest onboarding or fake password fields unless the real auth model changes.
- Do not reintroduce `welcome.standard.*` phrases or MP3s into manifests, CoreAudioPack, or app startup. If a future intro/audio path is needed, it must be justified as part of the single active workout runtime path rather than a parallel welcome subsystem.
