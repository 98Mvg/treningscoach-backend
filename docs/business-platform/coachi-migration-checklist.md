# Coachi business-platform migration checklist

## Batch 1 — Web foundation
- [x] Add `web/` Next.js shell for `Coachi.no`
- [x] Add legal and support entry pages
- [x] Add Clerk sign-in / sign-up shell
- [x] Add Sentry and PostHog client/server scaffolding

## Batch 2 — Supabase data layer
- [x] Add initial Supabase schema
- [x] Add one-way export shell from current SQLAlchemy data
- [x] Add placeholder export artifacts for entitlements and identity links
- [x] Add offline verification for mirrored export artifacts
- [ ] Verify mirrored data against production exports

## Batch 3 — Identity migration shell
- [x] Add `identity_links` schema
- [x] Add Clerk as target identity provider in web shell
- [x] Add Clerk webhook shell that syncs profiles and identity links into Supabase
- [ ] Add backend trust for Clerk tokens when web routes need it

## Batch 4 — Premium architecture
- [x] Document StoreKit-first entitlement rule
- [x] Add entitlement schema
- [ ] Implement StoreKit in iOS when premium scope is approved

## Batch 5 — Web account surfaces
- [x] Add account shell
- [x] Add history / premium / preferences shells
- [x] Add web health endpoint for scaffold verification
- [x] Back with real Supabase reads

## Batch 6 — Email provider migration
- [x] Add Resend-ready provider shell
- [x] Add Resend email helpers and `email_events` logging shell
- [x] Keep the initial email scope to welcome / waitlist / account-created confirmation
- [ ] Configure `RESEND_API_KEY`
- [ ] Verify production transactional emails through Resend

## Batch 7 — Analytics / observability
- [x] Add PostHog event list
- [x] Add Sentry scaffolding
- [ ] Verify production ingestion on `Coachi.no`

## Operations
- [x] Add environment and secret placement runbook
