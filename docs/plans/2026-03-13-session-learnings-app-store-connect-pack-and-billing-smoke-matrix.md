# 2026-03-13 — App Store Connect Pack And Billing Smoke Matrix

- The subscription code path was already in place; the missing launch work was operational packaging, not more StoreKit architecture.
- App Store submission readiness needs three separate artifacts, not one generic checklist: a fill-in worksheet for App Store Connect, a Sandbox/TestFlight matrix, and a paste-ready App Review notes template.
- Product IDs should be copied directly from `TreningsCoach/TreningsCoach/Config.swift` into launch docs so App Store Connect setup cannot drift from runtime truth.
- The remaining launch blockers after this pass are external: filling in App Store Connect values, running real purchase/restore tests on device, and submitting the first subscriptions together with the app version.
