# 2026-02-22 - Backend Monetization Policy (Free Now, Billing-Ready Later)

## Decision

- Product remains fully free in current phase.
- Backend is prepared for future billing activation via env flags.

## Runtime policy

- `APP_FREE_MODE=true` hard-locks paid behavior off.
- `BILLING_ENABLED` and `PREMIUM_SURFACES_ENABLED` can be configured now but are forced off while free mode is active.
- Later enablement path:
  - `APP_FREE_MODE=false`
  - `BILLING_ENABLED=true`
  - `PREMIUM_SURFACES_ENABLED=true`

## API support

- `/app/runtime` exposes `product_flags` for client-side gating.
- `/health` now also returns `product_flags` for ops visibility.

## Guardrail

- No paywall or premium gating should be shown while `APP_FREE_MODE=true`.
