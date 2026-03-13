# Phase 1 Launch Ops Checklist

Purpose: keep launch-critical environment setup and current product audit truth in one place while the app is still iPhone-first.

Companion checklist:

- `docs/checklists/phase1-security-review.md` for the 30-rule launch security review.
- `docs/checklists/app-store-submission-checklist.md` for the App Store Connect and subscription submission checklist.
- `docs/checklists/app-review-notes-template.md` for the reviewer instructions text.

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
   - `OPENAI_API_KEY` only if `TALK_STT_ENABLED=true`
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
8. For a free-core + optional Premium launch:
   - set `APP_FREE_MODE=false`
   - set `BILLING_ENABLED=true`
   - set `PREMIUM_SURFACES_ENABLED=true`
   - keep the free workout path reachable without purchase

## Live Voice Rollout Checklist

Use this when enabling the post-workout xAI live voice mode for real users.

Required backend env:

1. Set `XAI_API_KEY`.
2. Confirm `XAI_VOICE_AGENT_ENABLED=true`.
3. Confirm `XAI_VOICE_AGENT_MODEL=grok-3-mini` unless intentionally overridden.
4. Confirm `XAI_VOICE_AGENT_REGION=us-east-1`.
5. Confirm `XAI_VOICE_AGENT_VOICE=Rex`.
6. Confirm `XAI_VOICE_AGENT_CLIENT_SECRET_URL=https://api.x.ai/v1/realtime/client_secrets`.
7. Confirm `XAI_VOICE_AGENT_WEBSOCKET_URL=wss://api.x.ai/v1/realtime`.
8. Confirm `XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT=12` unless intentionally overridden.
9. Confirm session policy:
   - `XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS=120`
   - `XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS=300`
   - `XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY=2`
   - `XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY=10`

Expected current product behavior:

1. Live voice is enabled by default in the iPhone app build via `LIVE_COACH_VOICE_ENABLED=true`.
2. The post-workout summary CTA is visible for authenticated users.
3. Free users get shorter/fewer live sessions.
4. Premium users get longer/more live sessions.
5. Live voice uses the current workout summary plus a sanitized structured workout-history overview on the existing backend route.
6. Fallback text still uses the existing `/coach/talk` path.

Fastest manual smoke test:

```bash
chmod +x ./scripts/smoke_live_voice.sh
FREE_USER_BEARER_TOKEN="..." \
PREMIUM_USER_BEARER_TOKEN="..." \
BASE_URL="https://treningscoach-backend.onrender.com" \
./scripts/smoke_live_voice.sh
```

Optional quota-burn verification:

```bash
CHECK_DAILY_LIMITS=true \
FREE_USER_BEARER_TOKEN="..." \
PREMIUM_USER_BEARER_TOKEN="..." \
BASE_URL="https://treningscoach-backend.onrender.com" \
./scripts/smoke_live_voice.sh
```

Important:

- `CHECK_DAILY_LIMITS=true` consumes real daily live-voice quota for both tokens.
- Use separate test accounts for free and premium smoke checks.

## App Store + Premium Submission Checklist

Use this when Coachi is submitted as a free app with optional monthly/yearly Premium.

1. In App Store Connect, complete:
   - Paid Apps Agreement
   - tax information
   - banking information
2. Create one subscription group for Coachi Premium with:
   - monthly plan
   - yearly plan
3. Confirm the app remains free to download and that the free core workout path is still usable without payment.
4. Confirm premium surfaces are reviewer-visible in the app:
   - `Upgrade to Premium`
   - `Restore Purchases`
   - `Manage Subscription`
5. Confirm in-app account deletion works from settings on the existing `DELETE /auth/me` backend path.
6. Test monthly and yearly purchases in Sandbox and TestFlight before submission.
7. Submit the first subscriptions together with the app version.
8. Paste the current reviewer instructions from `docs/checklists/app-review-notes-template.md` into the App Review notes field.

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
