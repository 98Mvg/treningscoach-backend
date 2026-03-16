## Session Learnings — 2026-03-16

- `Administrer abonnement` in the profile tab should visually align with the existing Coachi paywall direction; subscription status cards alone read as unfinished compared with pricing-card layouts.
- For `Talk to Coach Live`, the summary CTA should rely on session validity, not only hydrated profile state. Free signed-in users can otherwise be blocked by `currentUser == nil` even when the auth token is valid.
- `Kontakt support` works better as a short decision surface with one clear CTA. The longer instructional content belongs on a separate FAQ/help page.
- FAQ content in profile should be grouped by the user’s real tasks: watch/sync, user profile, subscription, and heart-rate usage. This is easier to scan than long mixed Q&A blocks.
- The home screen centers more reliably when the content column is centered first and each section opts into leading alignment only where needed.
