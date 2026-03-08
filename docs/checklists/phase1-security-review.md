# Phase 1 Security Review Checklist

Purpose: keep a concrete, launch-grade security checklist for the current iPhone-first product while premium, subscriptions, and broader platform support are still deferred.

## Authentication And Session

1. Require an explicit `JWT_SECRET` in production-like environments.
2. Keep Apple Sign-In as the only exposed third-party provider until other providers are real.
3. Do not expose placeholder Google, Facebook, or Vipps flows in user-facing UI.
4. Revoke refresh-token families on sign-out.
5. Clear local auth state when refresh token rotation fails.
6. Avoid treating a non-empty token string as sufficient proof of a valid session.

## API And Backend

7. Keep `/coach/continuous` and `/coach/talk` behind explicit auth/guest-mode rules.
8. Fail fast on guest-mode auth errors instead of retrying protected endpoints for the whole workout.
9. Rate-limit public-facing routes that can be abused.
10. Keep upload validation strict for all audio/file endpoints.
11. Reject oversized or malformed payloads before expensive processing.
12. Keep CORS restricted to real app and site origins in production.

## Secrets And Environment

13. Do not commit secrets to the repo.
14. Keep `.env.example` truthful and production-safe.
15. Use real production env vars on Render, not generated fallback values.
16. Keep `OPENAI_API_KEY`, `XAI_API_KEY`, `ELEVENLABS_API_KEY`, and R2 credentials out of logs.
17. Treat missing billing and email env vars as disabled features, not silent partial runtime.
18. Keep separate dev and production values for auth, CORS, and storage endpoints.

## Workout Runtime Safety

19. Keep deterministic event ownership in `zone_event_motor.py`.
20. Do not let AI decide workout events or overwrite deterministic timing.
21. Drop stale workout responses that arrive too late to be useful.
22. Bound expensive analysis work so a single request cannot kill a worker.
23. Keep no-HR coaching on a deterministic structure path when HR is unavailable.
24. Never interrupt workouts with paywalls or growth prompts.

## Talk-To-Coach Safety

25. Keep workout talk on the same runtime path, but gate expensive compute by feature flags later.
26. Preserve real safety rules while removing obviously over-restrictive user-facing refusals.
27. Fail fast on STT quota or rate-limit errors and use short workout-specific fallback answers.
28. Prevent repeated talk triggers while the coach is already listening or responding.
29. Keep wake-word and talk-button handling bounded so they cannot stall the workout loop.
30. Log enough structured reason/state data to debug talk failures without logging sensitive user content beyond the minimum operational need.

## Current Phase 1 Status

- Completed:
  - production `JWT_SECRET` enforcement
  - placeholder auth-provider hardening on iOS
  - guest auth retry suppression
  - stale workout response guards
  - bounded talk and continuous-runtime fallback paths
- Still requires human launch review:
  - Render env vars are present and correct
  - Apple Sign-In is valid for the production bundle identifiers
  - CORS origins match the real production domains
  - logs and dashboards are reviewed before launch
