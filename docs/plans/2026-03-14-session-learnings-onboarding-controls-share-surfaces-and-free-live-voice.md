# 2026-03-14 - Onboarding Controls, Share Surfaces, And Free Live Voice

- Full-screen onboarding hero pages need their own visible in-view navigation controls; relying on `safeAreaInset` or broad drag gestures is too easy to regress and can hide `Next` completely on device.
- Post-workout sharing feels much clearer when users pick from visible destination buttons instead of a generic confirmation dialog. The summary and live-coach insight paths should use the same destination-driven UI.
- `Talk to Coach Live` can be free for signed-in users without changing the backend architecture, but anonymous guests still cannot use it because `/voice/session` remains auth-protected.
- Settings actions that matter for trust, like logout, restore purchases, and manage subscription, should be visible in one press and use adaptive colors so they stay legible in both light and dark mode.
- Workout setup should surface intensity as a primary decision, while watch connectivity should be shown as a compact status signal rather than verbose setup text.
