# Session Learnings — 2026-03-16 Render Profile Persistence Crash

## What changed

- Fixed the `/coach/continuous` runtime profile path in [main.py](/Users/mariusgaarder/Documents/treningscoach/main.py) so local iOS personalization identifiers like `profile_<uuid>` are treated as runtime-only keys and never persisted into `user_profiles.user_id`.
- Added a DB-safe persisted profile user-ID helper that only accepts real database users when reading or writing [UserProfile](/Users/mariusgaarder/Documents/treningscoach/database.py).
- Changed runtime profile resolution to skip empty profile snapshots instead of creating blank `user_profiles` rows with no meaningful values.
- Made `/coach/continuous` prefer the authenticated user ID when resolving a persisted runtime profile, so signed-in sessions use the real saved profile even if the request also carries a local personalization key.
- Added regression coverage in [test_profile_runtime_resolution.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_profile_runtime_resolution.py) and synced current route expectations in [test_rate_limit_verification.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_rate_limit_verification.py).

## Why this path

- The crash came from mixing two different identifier domains: local personalization IDs and persisted `users.id` foreign keys.
- The correct fix was to tighten the existing normalization path, not to add another profile store or another request field.
- Empty profile snapshots are not useful data. Persisting them only creates noisy rows and makes startup/runtime failures more likely to surface later.

## Verification

- `pytest -q tests_phaseb/test_profile_runtime_resolution.py tests_phaseb/test_profile_upsert_contract.py tests_phaseb/test_rate_limit_verification.py -k "profile or continuous"` -> `10 passed, 7 deselected`
- `python3 -m py_compile main.py` -> passed

## Follow-up note

- If more runtime-only identifiers are introduced later, keep them explicitly separate from database foreign keys and make the normalization helper the single boundary between “session/personalization ID” and “persisted user ID”.
