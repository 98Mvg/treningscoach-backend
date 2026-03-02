# 2026-02-22 - Phase 1 Completed

## Phase 1 goal

Ship launch-ready foundation:
- website funnel + lead capture reliability
- deployment safety
- single backend runtime source of truth (no root/backend drift)

## Completed scope

### Day 1: Funnel + lead protection

- Waitlist moved from in-memory to DB persistence with duplicate handling + per-IP rate limit.
- Landing CTA links made env-driven (`APP_STORE_URL`, `GOOGLE_PLAY_URL`, `ANDROID_EARLY_ACCESS_URL`).
- Landing analytics restricted to launch funnel events only.
- Launch page aligned to app-download funnel flow (no web demo dependency in launch route).

### Day 2: Deployment safety + source-of-truth cutover

- Added `scripts/release_check.sh` smoke checks.
- Added launch lock env defaults in `.env.example`.
- Config defaults made env-driven for launch-critical controls (`DEFAULT_LANGUAGE`, `MIN_SIGNAL_QUALITY_TO_FORCE`).
- Legacy `backend/main.py` converted to compatibility entrypoint importing root app.
- `backend/start_backend.sh` and `backend/start.sh` now launch root runtime path.
- All backend runtime mirror modules (`backend/*.py`, `backend/brains/*.py`) converted to compatibility wrappers importing root modules.
- Added source-of-truth guard script: `scripts/check_root_runtime.sh`.
- Wired root-runtime guard into release checks.
- Added regression tests to lock this behavior: `tests_phaseb/test_root_runtime_source_of_truth.py`.

## Verification snapshot

- Root runtime guard: pass
- Compile: pass (`python3 -m py_compile backend/*.py backend/brains/*.py`)
- Tests: pass (`20 passed` in focused Phase 1 suite)

## Outcome

Phase 1 is now complete: launch funnel is operationally safer, and backend runtime drift between root and backend mirrors is removed via compatibility wrappers and automated guardrails.
