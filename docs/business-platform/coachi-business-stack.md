# Coachi business stack migration

This document defines the additive migration around the current Flask workout runtime.

## Keep
- Flask backend for workout runtime and phrase/audio systems
- iOS/watch apps as the main product surfaces
- deterministic ownership in `zone_event_motor.py`

## Add now
- `web/` Next.js shell for `Coachi.no`
- Supabase schema for product data
- Clerk as target identity provider for web and later shared identity
- Sentry + PostHog from day 1 of the new stack
- Resend as the future transactional email provider

## Add later
- StoreKit-backed premium unlock in iOS
- Stripe for web billing
- Upstash for rate limits/cache if needed
- Pinecone only if a real retrieval/search use case is proven

## Current scaffold added in this branch
- `web/` Next.js shell for `Coachi.no`
- Clerk sign-in / sign-up and protected account shell
- Clerk webhook shell for profile / identity-link sync into Supabase
- Supabase-backed account, history, premium, and preferences shells
- Supabase schema and export shell
- PostHog and Sentry setup stubs
- Resend email helpers with `email_events` logging shell
- environment/secret placement runbook for `Coachi.no`
- offline Supabase export verification script
- StoreKit-first premium policy docs
- migration checklist for safe incremental rollout

## Migration rule
Do not create a second workout runtime. The business stack grows around the current runtime instead of replacing it.
