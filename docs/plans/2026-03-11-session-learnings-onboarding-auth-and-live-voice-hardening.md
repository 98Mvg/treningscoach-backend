# Session Learnings — 2026-03-11

## Scope
- Mandatory account onboarding on the single existing auth path
- Passwordless email sign-in alongside Apple Sign-In
- Post-workout live voice stability hardening
- Welcome log cleanup

## What Landed
- Onboarding now requires either Apple Sign-In or passwordless email verification; there is no longer a "continue without account" path in the active onboarding flow.
- Backend auth now supports `POST /auth/email/request-code` and `POST /auth/email/verify` on the existing `/auth/*` path.
- The iOS app now signs out stale sessions automatically when `/auth/me` returns `404`, instead of staying in a half-authenticated state.
- `Talk to Coach Live` now uses the current workout summary plus a sanitized structured workout-history overview, not prior chat memory.
- Live voice now avoids a mixer-format crash by converting incoming provider PCM16 audio into a mixer-friendly float playback format.
- Live voice now times out during startup and fails into an explicit retry/text-fallback state instead of getting stuck indefinitely in preparing/connecting.
- Dismiss/close on the live voice screen now returns control to the user immediately instead of waiting on telemetry/network cleanup.
- Welcome runtime logs on iOS no longer expose `welcome.standard.*` utterance IDs in app logs.

## Remaining
- Validate the identity-step keyboard/CTA behavior on physical devices and reduce any remaining typing lag in the name step.
- Re-verify the live voice screen on real devices after the startup-timeout and audio playback fixes.
- Complete deployed launch smoke for auth, live voice, phrase rotation, and score credibility.
