# Session Learnings — 2026-03-16 — Profile Root Cleanup And Destructive Actions

## What changed
- Removed duplicate premium/offers promotion from the root profile tab and kept subscription comparison inside `Administrer abonnement`.
- Removed root-level visibility for account deletion and version/about rows from the main profile surface.
- Kept `Sign out` only on the root profile tab and moved `Delete account` to the bottom of `Personlig profil`.

## Why it matters
- The root profile tab should stay focused on navigation, not duplicate purchase funnels.
- Destructive account actions should be harder to trigger accidentally than routine settings.
- Version/about details belong inside nested settings, not as a primary profile action.

## Guardrails
- Avoid showing the same subscription CTA both on the profile root and inside the manage-subscription screen.
- Keep `Delete account` only in the deepest reasonable settings surface.
- Keep `Sign out` and `Delete account` separated so users do not confuse routine exit with destructive removal.
