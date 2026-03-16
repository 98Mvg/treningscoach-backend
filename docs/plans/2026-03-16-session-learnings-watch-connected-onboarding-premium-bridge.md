# Session Learnings — 2026-03-16 — Watch-Connected Onboarding Premium Bridge

## What changed
- Added a new onboarding step that appears after Apple Watch is successfully connected.
- Kept the real purchase path in the existing `PaywallView`, and used the new onboarding step only as a contextual bridge with Premium value framing.
- Preserved the simpler flow for users who continue without a connected watch.

## Why it matters
- The upsell is more relevant immediately after the user has completed the watch-connect milestone.
- Users can understand why Premium matters in Coachi before they hit a generic paywall.
- Reusing the existing paywall keeps StoreKit handling, restore flow, and legal/footer behavior in one place.

## Guardrails
- Do not add a second purchase implementation inside onboarding.
- Keep the onboarding bridge informational, with a clear free-path escape hatch.
- Only show the watch-connected Premium bridge when the watch is actually ready and the user does not already have Premium access.
