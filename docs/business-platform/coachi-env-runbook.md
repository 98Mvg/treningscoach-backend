# Coachi business stack environment runbook

This runbook defines where configuration belongs for the additive `Coachi.no` business stack.

Scope:
- `web/` Next.js shell on Vercel
- Clerk for web identity
- Supabase for mirrored business data
- Resend for transactional email
- PostHog and Sentry for observability

Non-goals:
- replacing the Flask workout runtime
- moving `zone_event_motor.py` to serverless
- storing live secrets in committed `.env.example` files

## Rules

1. `.env.example` files stay placeholders-only.
2. Real secrets never go in git.
3. Public browser variables must be prefixed with `NEXT_PUBLIC_`.
4. Server-only variables must only exist in:
   - Vercel project env vars
   - Clerk app/webhook settings
   - Supabase project secrets
   - local `web/.env.local` for development only

## Default website reference

Use `https://coachi.no` as the default site URL for the web shell and related docs.

## Environment placement matrix

| Variable | Scope | Where it belongs | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | Public | Vercel env / `web/.env.local` | Default web reference for `Coachi.no` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public | Vercel env / `web/.env.local` | Safe for browser use |
| `CLERK_SECRET_KEY` | Server-only | Vercel env | Never expose client-side |
| `CLERK_WEBHOOK_SECRET` | Server-only | Vercel env + Clerk webhook config | Used by `/api/webhooks/clerk` |
| `SUPABASE_URL` | Server + build-time config | Vercel env / `web/.env.local` | Public project URL, but still keep in env |
| `SUPABASE_ANON_KEY` | Public client key | Vercel env / `web/.env.local` | Browser-safe |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only | Vercel env / Supabase secrets | Never expose client-side |
| `RESEND_API_KEY` | Server-only | Vercel env | For transactional email |
| `EMAIL_FROM` | Server-only | Vercel env | Defaults may exist locally, but production should set explicitly |
| `EMAIL_REPLY_TO` | Server-only | Vercel env | Support/reply address |
| `SUPPORT_EMAIL` | Public/support metadata | Vercel env | Can also be duplicated in app/backend envs |
| `PRIVACY_EMAIL` | Public/legal metadata | Vercel env | Legal/support page content |
| `NEXT_PUBLIC_POSTHOG_KEY` | Public | Vercel env / `web/.env.local` | Browser-safe analytics key |
| `NEXT_PUBLIC_POSTHOG_HOST` | Public | Vercel env / `web/.env.local` | Usually `https://eu.i.posthog.com` |
| `NEXT_PUBLIC_SENTRY_DSN` | Public | Vercel env / `web/.env.local` | Browser-safe DSN |
| `SENTRY_AUTH_TOKEN` | Server-only / CI | Vercel env / CI secret store | Never expose client-side |

## Local development

Use:
- `web/.env.local` for the Next.js shell
- root `.env` for the existing Flask backend if needed

Do not copy secrets into:
- `web/.env.example`
- root `.env.example`

## Clerk setup

Clerk is the long-term identity provider for `Coachi.no`.

Current migration rule:
- existing mobile auth stays alive temporarily
- Clerk is additive for web
- user linkage happens through `identity_links`

Required Clerk setup:
1. Create the Clerk application for `Coachi.no`
2. Configure sign-in and sign-up URLs for the Next.js shell
3. Point the Clerk webhook to:
   - `/api/webhooks/clerk`
4. Store:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `CLERK_WEBHOOK_SECRET`

## Supabase setup

Supabase is the target source of truth for business/product data, not the workout runtime.

Current migration rule:
- export and mirror first
- do not cut over Flask workout runtime yet
- verify data parity before any source-of-truth switch

Required setup:
1. Create Supabase project
2. Apply `supabase/migrations/20260309_000001_business_platform.sql`
3. Set:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
4. Run the offline export and verification scripts before import/cutover

## Resend setup

Only these flows are in scope now:
- welcome
- waitlist confirmation
- account-created confirmation

Required setup:
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `EMAIL_REPLY_TO`

Email failure must never block signup or account creation.

## PostHog setup

Only these events are in scope now:
- `signup_completed`
- `app_opened`
- `workout_started`
- `workout_completed`
- `coach_score_viewed`
- `talk_to_coach_used`
- `upgrade_viewed`
- `subscription_started`
- `trial_started`
- `subscription_active`

Required setup:
- `NEXT_PUBLIC_POSTHOG_KEY`
- `NEXT_PUBLIC_POSTHOG_HOST`

## Sentry setup

Required setup:
- `NEXT_PUBLIC_SENTRY_DSN`
- `SENTRY_AUTH_TOKEN`

Sentry should be active for the web shell and available for build/release tasks without leaking server-only values to the browser.

## Verification checklist

Before using the business stack in a real environment:
1. `web/.env.example` contains placeholders only
2. No server-only secrets are referenced from client-side files
3. Clerk sign-in, sign-up, middleware, and webhook route all resolve
4. Supabase schema exists and covers the required business tables
5. Offline export artifacts can be generated and validated
6. Resend helper is limited to the initial three flows
7. PostHog and Sentry helpers can initialize from env without touching the Flask runtime
