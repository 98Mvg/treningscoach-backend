# Coachi Web

This is the isolated Next.js/Vercel shell for `Coachi.no`.

Scope for this migration phase:
- marketing and support entry points
- legal pages
- Clerk-backed account shell
- Supabase-backed history and entitlement pages
- protected account routes via Clerk middleware
- Clerk webhook shell that syncs identity into Supabase
- health endpoint for basic Vercel-side readiness checks
- Resend email shell for welcome / waitlist / account-created flows

Non-goals for this phase:
- replacing the existing Flask workout runtime
- moving deterministic coaching to serverless routes
- implementing Stripe as the first iOS unlock path

The existing Flask backend remains the source of truth for the workout runtime.
The web account pages read only mirrored business data from Supabase. They do not create a second workout runtime.

Key additive routes in this scaffold:
- `/api/health`
- `/api/webhooks/clerk`

Operational docs:
- `docs/business-platform/coachi-env-runbook.md`
- `docs/business-platform/coachi-migration-checklist.md`
