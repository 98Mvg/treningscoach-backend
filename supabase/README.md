# Supabase migration shell for Coachi

Supabase is the long-term data home for Coachi business data.

Current migration direction:
- keep Flask + SQLAlchemy + existing workout runtime alive
- mirror product data into Supabase
- cut over only after parity is verified

Initial canonical tables:
- profiles
- workout_sessions
- workout_metrics
- entitlements
- identity_links
- email_events

Current export shell writes:
- `profiles.json`
- `workout_sessions.json`
- `workout_metrics.json`
- `email_events.json`
- `entitlements.json` (empty until premium is live)
- `identity_links.json` (empty until Clerk linking is active)

Additive write paths in this scaffold:
- Clerk webhook sync updates `profiles` and `identity_links`
- Resend email shell writes `email_events`
- future StoreKit entitlement sync updates `entitlements`
- legacy export remains offline-only bootstrap material

Additive read paths in this scaffold:
- web account shell reads `profiles`, `workout_sessions`, `workout_metrics`, and `entitlements`

Do not move deterministic workout execution into Supabase during this phase.
