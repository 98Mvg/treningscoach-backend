# 2026-03-16 - Supabase Auth And Launch Surface Cleanup

- Coachi can adopt Supabase for Postgres and email-auth without rewriting the public Flask API or adding direct Supabase SDK calls to the SwiftUI app.
- The safe launch path is to keep the richer existing schema (`users`, `workout_history`, `user_subscriptions`) and add `coaching_scores`, rather than creating parallel simplified tables that drift from runtime truth.
- Optional external-provider adoption should stay behind explicit feature flags like `SUPABASE_AUTH_ENABLED`, so launch-safe fallback behavior still works without credentials.
- Subscription/legal/settings polish is not just design work; stale non-Coachi copy and wrong legal/support URLs create real launch and review risk.
- Website and app legal surfaces should move together: adding `/terms` on the backend and pointing in-app links at `coachi.no/terms`, `coachi.no/privacy`, and `coachi.no/support` keeps the product coherent at launch.
