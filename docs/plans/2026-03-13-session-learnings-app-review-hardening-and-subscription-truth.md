# 2026-03-13 - App Review Hardening And Subscription Truth

- Coachi is now modeled as a free app with a real free core path: onboarding can continue without an account, while sign-in remains the upgrade path for history, durable account features, and Premium-linked surfaces.
- `DELETE /auth/me` was already implemented on the backend; the launch-safe fix was to wire it into the existing settings screen instead of inventing a support-only deletion flow.
- Signing out now transitions the app to guest mode instead of forcing users back through onboarding, which better matches the free-core product shape and reduces App Review risk.
- Settings, FAQ, and terms copy must describe Premium as optional monthly/yearly Apple subscriptions when the repo already contains live StoreKit/paywall code; stale "free mode at launch" copy is product-truth drift.
