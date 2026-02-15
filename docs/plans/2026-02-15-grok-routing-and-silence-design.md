# Design: Fix Grok Routing & Post-Welcome Coach Silence

Date: 2026-02-15
Status: Approved
Bugs: Grok $0.00 usage (never called), coach silent after welcome message

## Problem 1: Grok Never Called

**Evidence:** xAI billing dashboard shows $0.00 usage with $20.00 prepaid credits untouched across February 2026.

**Root cause:** `_get_priority_response()` calls `_is_brain_available()` before `_get_brain_instance()`. When Grok init fails (missing key, Render cold-start timeout), `_get_brain_instance` caches `None` and sets a 30-second cooldown. During that cooldown, `_is_brain_available()` returns `False` — the loop skips Grok without logging why. After cooldown expires, next init attempt may also timeout, restarting the cycle. Priority chain silently falls through to Claude.

**Two sub-problems:**
1. Init failures use the same 30s cooldown as runtime timeouts — too long for transient cold-start failures
2. No logging when `_is_brain_available()` skips a brain — invisible in Render logs

## Problem 2: Coach Silent After Welcome

**Evidence:** Welcome message plays, then no coaching audio for ~50 seconds.

**Root cause — two-gate gap:**
- Gate 1 (`voice_intelligence.should_stay_silent`): Returns `(False, "early_workout")` for first 30 seconds — correctly says "don't force silence"
- Gate 2 (`coaching_intelligence.should_coach_speak`): Returns `(False, "no_change")` when early audio chunks produce similar analyses with no intensity/tempo change detected
- Gate 1 saying "don't silence" ≠ Gate 2 saying "actively speak"
- `apply_max_silence_override` only fires at 60 seconds — too late

The first few audio chunks are noisy (contain welcome playback audio), produce similar low-quality analyses, and Gate 2 sees "no change" → stays silent.

## Design

### Fix 1: Grok Init Retry + Skip Logging

**File: `backend/brain_router.py`**

A. Separate init cooldown from runtime cooldown:
- Init failures: 5-second retry (`BRAIN_INIT_RETRY_SECONDS`)
- Runtime timeouts: keep existing 30s cooldown (`BRAIN_TIMEOUT_COOLDOWN_SECONDS`)
- Distinguish via a `_brain_init_failures` dict (separate from `brain_cooldowns`)

B. Add skip-reason logging in `_get_priority_response()`:
- When `_is_brain_available()` returns False, log which check failed (cooldown, latency, usage)
- Format: `[BRAIN] grok | SKIPPED | reason=cooldown_until=1708012345`

C. Add pool status to `/brain/health` response:
- New `pool_status` field showing init state per brain

**File: `backend/config.py`**
- Add `BRAIN_INIT_RETRY_SECONDS = 5`

### Fix 2: Early-Workout Grace Period in Gate 2

**File: `backend/coaching_intelligence.py`**

Add early-workout engagement rule at the TOP of `should_coach_speak()`, right after critical-breathing check:
```python
if elapsed_seconds is not None and elapsed_seconds < EARLY_WORKOUT_GRACE_SECONDS:
    return (True, "early_workout_engagement")
```

This makes Gate 2 match Gate 1's behavior — first 30 seconds are always chatty. By tick 4 (~32s), recording buffer has clean audio and normal decision logic takes over.

**File: `backend/config.py`**
- Add `EARLY_WORKOUT_GRACE_SECONDS = 30`

**File: `backend/main.py`**
- Pass `elapsed_seconds` to `should_coach_speak()` (verify it's already passed; add if not)

### Files Touched

| File | Change |
|------|--------|
| `backend/brain_router.py` | Init-retry cooldown, skip logging, pool status |
| `backend/coaching_intelligence.py` | Early workout grace period |
| `backend/config.py` | `BRAIN_INIT_RETRY_SECONDS`, `EARLY_WORKOUT_GRACE_SECONDS` |
| `backend/main.py` | Pass elapsed_seconds to should_coach_speak (if needed) |

### Files NOT Touched

- iOS code (no changes needed)
- `voice_intelligence.py` (session-scoped silence from Codex session preserved)
- `elevenlabs_tts.py`, `persona_manager.py`, `locale_config.py`
- All brain adapters (language normalization from Codex session preserved)

### Guardrails Preserved

- ✅ Language consistency (3-layer: ingress, brain adapter, output guard)
- ✅ Intensity normalization (canonical keys everywhere)
- ✅ Session-scoped silence (no global counters)
- ✅ Bounded wake-word restarts (backoff + cap + degraded mode)
- ✅ Per-tick latency logging (analyze_ms, decision_ms, brain_ms, tts_ms, total_ms)
- ✅ Single runtime path (no parallel architecture)

### Validation

```bash
pytest -q tests_phaseb
python3 -m py_compile main.py brain_router.py coaching_intelligence.py config.py
```

Post-deploy verification:
```bash
curl https://treningscoach-backend.onrender.com/brain/health  # Check pool_status shows grok initialized
curl "https://treningscoach-backend.onrender.com/welcome?language=no"  # Check TTS works
```

Then start a workout — coach should speak within first 30 seconds, and Render logs should show `[BRAIN] grok | latency=...` instead of Claude.
