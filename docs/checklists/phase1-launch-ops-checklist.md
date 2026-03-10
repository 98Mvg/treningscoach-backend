# Phase 1 Launch Ops Checklist

Purpose: keep launch-critical environment setup and current product audit truth in one place while the app is still iPhone-first.

Companion checklist:

- `docs/checklists/phase1-security-review.md` for the 30-rule launch security review.

## Required Production Environment

Before deploying to Render or any production-like environment:

1. Set `JWT_SECRET`.
2. Set `CORS_ALLOWED_ORIGINS` to the real production domains.
3. Set `APPLE_CLIENT_ID` and `APPLE_CLIENT_IDS` if Apple Sign-In is enabled for that build.
4. Set the audio pack variables if remote pack sync is expected:
   - `R2_BUCKET_NAME`
   - `R2_ACCOUNT_ID`
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_PUBLIC_URL`
5. Set the active AI/TTS credentials used by the current production path:
   - `ELEVENLABS_API_KEY`
   - `XAI_API_KEY`
   - `OPENAI_API_KEY` if speech transcription is enabled
6. If launch analytics/error tracking are enabled, set:
   - `POSTHOG_ENABLED=true`
   - `POSTHOG_API_KEY`
   - `POSTHOG_HOST`
   - `SENTRY_ENABLED=true`
   - `SENTRY_DSN`
   - `SENTRY_ENVIRONMENT`
   - `SENTRY_RELEASE`
7. If welcome/account emails are enabled, set:
   - `EMAIL_SENDING_ENABLED=true`
   - `EMAIL_PROVIDER` (`auto`, `resend`, or `smtp`)
   - `EMAIL_FROM`
   - `RESEND_API_KEY` for Resend, or SMTP credentials for SMTP
8. Keep `APP_FREE_MODE=true` and `BILLING_ENABLED=false` until premium boundaries are explicitly launched.

## Phrase Rotation Audit Truth

Current deterministic runtime truth:

1. Structure-driven no-HR instruction rotation is implemented.
   - Per-event rotation state exists in `zone_event_motor.py`.
   - The runtime avoids immediate repetition when multiple structure phrase IDs exist.
2. Motivation rotation is implemented, but currently rotates across two stage variants only.
   - Current stage pool is `.1` and `.2`.
   - `.3` variants remain editorial/backlog until runtime/audio parity is explicitly promoted.
3. HR-driven correction cues remain canonical.
   - `entered_target -> zone.in_zone.default.1`
   - `exited_target_above -> zone.above.default.1`
   - `exited_target_below -> zone.below.default.1`

Implication: phrase rotation is partially done, not globally done across every family.

## Coach Score Audit Truth

Current product truth:

1. `COACH_SCORE_VERSION` defaults to `cs_v2`.
2. Coach score is already implemented and should not be treated as a placeholder feature.
3. Missing HR or missing enforced target data intentionally caps the score ceiling.
4. Breath data helps only when reliable; it must not become a required fallback before signal quality is proven good enough.

Operational implication:

- If no-HR sessions are common at launch, the capped score behavior is expected product behavior, not necessarily a bug.
- This should be explained clearly in the app copy later if users question low/no-HR score ceilings.
