# 2026-03-14 - App Store State Resolution And Runtime Hardening

- Server-side premium resolution must look at whether a user has any active App Store subscription chain, not just the most recently updated transaction row. Out-of-order webhooks or a second expired chain can otherwise downgrade an actually active premium user.
- Persisting a `UserSubscription.tier` mirror is fine for fast reads, but it has to be recomputed from the full App Store state set when webhook or validation events arrive.
- StoreKit 2 signed transaction sync on iOS should use `VerificationResult<Transaction>.jwsRepresentation`, not `Transaction.jwsRepresentation`. The contract tests need to follow the API that actually compiles.
- App Store Server Notification JWS verification should validate the full `x5c` certificate chain and support a pinned root fingerprint allowlist. Leaf-only verification is too weak for a production monetization path.
- The existing `/subscription/validate`, `/webhooks/app-store`, and `/analytics/mobile` paths are enough to harden monetization without introducing a second runtime architecture. The missing work after that is mostly external: App Store Connect setup and device-side sandbox validation.
