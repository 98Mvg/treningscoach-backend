# Fix Grok Routing & Post-Welcome Silence — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Grok the active coaching brain (currently $0.00 usage) and eliminate the 50-second silence gap after welcome message.

**Architecture:** Two backend-only fixes. (1) Separate init-failure cooldown from runtime-failure cooldown in brain_router so Grok retries faster after cold-start failures; add skip-reason logging. (2) Add early-workout grace period in coaching_intelligence Gate 2 so the first 30 seconds always produce coaching output.

**Tech Stack:** Python/Flask backend, pytest for tests. No iOS changes.

**Design doc:** `docs/plans/2026-02-15-grok-routing-and-silence-design.md`

**Guardrails (from session takeaways — DO NOT break):**
1. Language consistency: ingress normalization, locale-aware fallbacks, final output guard before TTS
2. Intensity normalization: canonical `calm|moderate|intense|critical` everywhere
3. Silence policy: session-scoped counters only (no global)
4. Wake-word restart: bounded backoff + retry cap + degraded mode
5. Per-tick latency logging: analyze_ms, decision_ms, brain_ms, tts_ms, total_ms

---

### Task 1: Test early-workout grace period in coaching_intelligence

**Files:**
- Create: `tests_phaseb/test_early_workout_grace.py`

**Step 1: Write the failing tests**

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching_intelligence import should_coach_speak


def test_early_workout_forces_speak():
    """Coach MUST speak in first 30 seconds even with no intensity change."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=10,
    )
    assert should_speak is True
    assert reason == "early_workout_engagement"


def test_early_workout_grace_expires():
    """After grace period, normal rules apply (no change = no speak)."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=45,
    )
    # After grace, with no change, should not speak
    assert should_speak is False


def test_early_workout_none_elapsed_no_crash():
    """If elapsed_seconds is None (legacy call), don't crash — skip grace."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=None,
    )
    # Should not crash; result depends on other rules
    assert isinstance(should_speak, bool)
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/mariusgaarder/Documents/treningscoach && python3 -m pytest tests_phaseb/test_early_workout_grace.py -v`
Expected: FAIL — `should_coach_speak() got an unexpected keyword argument 'elapsed_seconds'`

**Step 3: Commit failing tests**

```bash
git add tests_phaseb/test_early_workout_grace.py
git commit -m "test: add early-workout grace period tests (failing)"
```

---

### Task 2: Implement early-workout grace period

**Files:**
- Modify: `backend/coaching_intelligence.py:152-158` (function signature)
- Modify: `backend/coaching_intelligence.py:189` (insert grace rule after critical_breathing)
- Modify: `backend/config.py:54` (add EARLY_WORKOUT_GRACE_SECONDS)
- Modify: `backend/main.py:825-831` (pass elapsed_seconds to should_coach_speak)

**Step 1: Add config value**

In `backend/config.py`, after line 54 (`MAX_SILENCE_SECONDS = 30`), add:
```python
EARLY_WORKOUT_GRACE_SECONDS = 30  # Force coaching output during early workout
```

**Step 2: Add elapsed_seconds parameter to should_coach_speak**

In `backend/coaching_intelligence.py`, change function signature at line 152:
```python
def should_coach_speak(
    current_analysis: Dict,
    last_analysis: Optional[Dict],
    coaching_history: List[Dict],
    phase: str,
    training_level: str = "intermediate",
    elapsed_seconds: Optional[int] = None
) -> Tuple[bool, str]:
```

**Step 3: Add grace period rule**

In `backend/coaching_intelligence.py`, after the critical_breathing rule (line 189), insert:
```python
    # Rule 1a: Early workout grace period — always speak to keep user engaged
    grace = getattr(config, "EARLY_WORKOUT_GRACE_SECONDS", 30)
    if elapsed_seconds is not None and elapsed_seconds < grace:
        logger.info("Coach speaking: early_workout_engagement (elapsed=%ds < %ds grace)", elapsed_seconds, grace)
        return (True, "early_workout_engagement")
```

**Step 4: Pass elapsed_seconds in main.py**

In `backend/main.py` at line 825-831, add `elapsed_seconds=elapsed_seconds`:
```python
                speak_decision, reason = should_coach_speak(
                    current_analysis=breath_data,
                    last_analysis=last_breath,
                    coaching_history=coaching_context["coaching_history"],
                    phase=phase,
                    training_level=training_level,
                    elapsed_seconds=elapsed_seconds
                )
```

**Step 5: Run tests**

Run: `cd /Users/mariusgaarder/Documents/treningscoach && python3 -m pytest tests_phaseb/ -q`
Expected: ALL PASS (12 existing + 3 new = 15)

**Step 6: Sync and compile-check**

```bash
cp backend/coaching_intelligence.py . && cp backend/config.py . && cp backend/main.py .
python3 -m py_compile main.py coaching_intelligence.py config.py
```

**Step 7: Commit**

```bash
git add backend/coaching_intelligence.py backend/config.py backend/main.py coaching_intelligence.py config.py main.py tests_phaseb/test_early_workout_grace.py
git commit -m "fix: add early-workout grace period to prevent post-welcome silence"
```

---

### Task 3: Test Grok init-retry with short cooldown

**Files:**
- Create: `tests_phaseb/test_brain_init_retry.py`

**Step 1: Write the failing tests**

```python
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_router import BrainRouter


def test_init_failure_uses_short_cooldown():
    """Init failures should use BRAIN_INIT_RETRY_SECONDS, not the long runtime cooldown."""
    router = BrainRouter()
    # Force an init failure for a fake brain
    router.brain_pool["test_brain"] = None
    router._set_init_cooldown("test_brain")

    cooldown_until = router.brain_init_cooldowns.get("test_brain", 0)
    remaining = cooldown_until - time.time()
    # Init cooldown should be ~5s, not 30s or 60s
    assert remaining <= 6.0, f"Init cooldown too long: {remaining:.1f}s"
    assert remaining > 0, "Init cooldown should be in the future"


def test_init_cooldown_separate_from_runtime_cooldown():
    """Init cooldown dict should be independent from runtime cooldown dict."""
    router = BrainRouter()
    router._set_init_cooldown("grok")
    router._set_cooldown("grok", seconds=30)

    # Both should exist independently
    assert "grok" in router.brain_init_cooldowns
    assert "grok" in router.brain_cooldowns
    # Init cooldown should be shorter
    init_remaining = router.brain_init_cooldowns["grok"] - time.time()
    runtime_remaining = router.brain_cooldowns["grok"] - time.time()
    assert init_remaining < runtime_remaining


def test_skip_logging_in_priority_response(capsys):
    """When a brain is skipped, a log line should explain why."""
    router = BrainRouter()
    # Put grok in cooldown
    router.brain_cooldowns["grok"] = time.time() + 9999
    # Try priority response — grok should be skipped with a log
    router._get_priority_response(
        breath_data={"intensity": "moderate", "language": "en"},
        phase="warmup",
        mode="realtime_coach",
        language="en",
        persona=None,
    )
    captured = capsys.readouterr()
    assert "SKIPPED" in captured.out or "skipped" in captured.out.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/mariusgaarder/Documents/treningscoach && python3 -m pytest tests_phaseb/test_brain_init_retry.py -v`
Expected: FAIL — `AttributeError: 'BrainRouter' object has no attribute 'brain_init_cooldowns'` or `'_set_init_cooldown'`

**Step 3: Commit failing tests**

```bash
git add tests_phaseb/test_brain_init_retry.py
git commit -m "test: add brain init-retry and skip-logging tests (failing)"
```

---

### Task 4: Implement Grok init-retry with short cooldown + skip logging

**Files:**
- Modify: `backend/brain_router.py:45` (add brain_init_cooldowns dict)
- Modify: `backend/brain_router.py:142-164` (_get_brain_instance — use init cooldown)
- Modify: `backend/brain_router.py:166-168` (add _set_init_cooldown)
- Modify: `backend/brain_router.py:170-186` (_is_brain_available — return reason)
- Modify: `backend/brain_router.py:237-246` (_get_priority_response — log skips)
- Modify: `backend/brain_router.py:438-462` (health_check — add pool_status)
- Modify: `backend/config.py` (add BRAIN_INIT_RETRY_SECONDS)

**Step 1: Add config value**

In `backend/config.py`, after line 254 (`BRAIN_TIMEOUT_COOLDOWN_SECONDS = 30`), add:
```python
BRAIN_INIT_RETRY_SECONDS = 5  # Short retry for init failures (cold starts)
```

**Step 2: Add brain_init_cooldowns dict in __init__**

In `backend/brain_router.py` line 47, after `self.brain_cooldowns = {}`, add:
```python
        self.brain_init_cooldowns = {}  # Separate short cooldown for init failures
```

**Step 3: Add _set_init_cooldown method**

In `backend/brain_router.py`, after `_set_cooldown` (line 168), add:
```python
    def _set_init_cooldown(self, brain_name: str):
        """Set a short cooldown for init failures (faster retry for cold starts)."""
        seconds = getattr(config, "BRAIN_INIT_RETRY_SECONDS", 5)
        self.brain_init_cooldowns[brain_name] = time.time() + seconds
```

**Step 4: Update _get_brain_instance to use init cooldown**

Replace `backend/brain_router.py` lines 142-164 with:
```python
    def _get_brain_instance(self, brain_name: str):
        """Get or lazily initialize a brain instance."""
        if brain_name in self.brain_pool:
            cached = self.brain_pool[brain_name]
            if cached is not None:
                return cached
            # Cached init failure — retry if init cooldown expired
            init_cooldown_until = self.brain_init_cooldowns.get(brain_name, 0)
            if time.time() < init_cooldown_until:
                return None  # Still in init cooldown
            # Init cooldown expired — clear cache and retry below
            print(f"[BRAIN] {brain_name} | RETRYING init after cooldown")
            del self.brain_pool[brain_name]
        try:
            brain = self._create_brain(brain_name)
            self.brain_pool[brain_name] = brain
            if brain is not None:
                print(f"✅ Brain Router: Loaded {brain_name} (model: {brain.model})")
                # Clear any init cooldown on success
                self.brain_init_cooldowns.pop(brain_name, None)
            return brain
        except Exception as e:
            print(f"⚠️ Brain Router: Failed to initialize {brain_name}: {e}")
            self._set_init_cooldown(brain_name)
            self.brain_pool[brain_name] = None
            return None
```

**Step 5: Add skip logging in _get_priority_response**

Replace `backend/brain_router.py` lines 237-246 with:
```python
        for brain_name in self.priority_brains:
            if not self._is_brain_available(brain_name):
                # Log why this brain was skipped
                skip_reason = self._get_skip_reason(brain_name)
                print(f"[BRAIN] {brain_name} | SKIPPED | {skip_reason}")
                continue

            if brain_name == "config":
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

            brain = self._get_brain_instance(brain_name)
            if brain is None:
                print(f"[BRAIN] {brain_name} | SKIPPED | init_failed")
                continue
```

**Step 6: Add _get_skip_reason helper**

After `_is_brain_available` method, add:
```python
    def _get_skip_reason(self, brain_name: str) -> str:
        """Get human-readable reason why a brain is unavailable."""
        cooldown_until = self.brain_cooldowns.get(brain_name)
        if cooldown_until and time.time() < cooldown_until:
            remaining = int(cooldown_until - time.time())
            return f"runtime_cooldown ({remaining}s remaining)"

        usage = getattr(config, "BRAIN_USAGE", {}).get(brain_name, 0.0)
        usage_limit = getattr(config, "USAGE_LIMIT", 0.9)
        if usage >= usage_limit:
            return f"usage_limit ({usage:.0%} >= {usage_limit:.0%})"

        stats = self.brain_stats.get(brain_name, {})
        avg_latency = stats.get("avg_latency")
        slow_threshold = getattr(config, "BRAIN_SLOW_THRESHOLD", None)
        if slow_threshold and avg_latency and avg_latency > slow_threshold:
            return f"too_slow (avg={avg_latency:.2f}s > threshold={slow_threshold}s)"

        return "unknown"
```

**Step 7: Add pool_status to health_check**

In `backend/brain_router.py` `health_check()` at line 449, add to the status dict:
```python
            "pool_status": {
                name: {
                    "initialized": name in self.brain_pool and self.brain_pool[name] is not None,
                    "init_cooldown_remaining": max(0, int(self.brain_init_cooldowns.get(name, 0) - time.time())),
                    "runtime_cooldown_remaining": max(0, int(self.brain_cooldowns.get(name, 0) - time.time())),
                }
                for name in self.priority_brains
            } if self.use_priority_routing else {}
```

**Step 8: Run all tests**

Run: `cd /Users/mariusgaarder/Documents/treningscoach && python3 -m pytest tests_phaseb/ -q`
Expected: ALL PASS (15 + 3 = 18)

**Step 9: Compile check**

```bash
python3 -m py_compile brain_router.py config.py
```

**Step 10: Sync and commit**

```bash
cp backend/brain_router.py . && cp backend/config.py .
diff backend/brain_router.py brain_router.py && diff backend/config.py config.py
git add backend/brain_router.py backend/config.py brain_router.py config.py tests_phaseb/test_brain_init_retry.py
git commit -m "fix: separate init cooldown for Grok, add skip-reason logging and pool_status"
```

---

### Task 5: Final validation and push

**Step 1: Run full test suite**

```bash
cd /Users/mariusgaarder/Documents/treningscoach && python3 -m pytest tests_phaseb/ -v
```
Expected: 18 passed

**Step 2: Compile all changed files**

```bash
python3 -m py_compile main.py brain_router.py coaching_intelligence.py config.py
```

**Step 3: Verify all synced**

```bash
diff backend/main.py main.py
diff backend/brain_router.py brain_router.py
diff backend/config.py config.py
diff backend/coaching_intelligence.py coaching_intelligence.py
```
Expected: No differences for all 4

**Step 4: Push to main**

```bash
git push origin main
```

**Step 5: Post-deploy verification**

```bash
# After Render deploys (~2 min):
curl -s https://treningscoach-backend.onrender.com/brain/health | python3 -m json.tool
# Check: pool_status.grok.initialized = true
# Check: active_brain = "priority"
```

Then start a workout in the app. Expected:
- Welcome message plays
- Coach speaks again within 8-16 seconds (early_workout_engagement)
- Render logs show `[BRAIN] grok | latency=...` (not claude)
- xAI billing shows non-zero usage
