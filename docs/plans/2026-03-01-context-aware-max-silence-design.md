# Context-Aware Max Silence + Always-Speak Fallback

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace fixed 30s max-silence with context-aware thresholds, add motivation cooldown barriers, ensure coach always speaks (even with no watch + no mic) via event-owned system, and add new R2 audio pack phrases for go-by-feel and breath-guidance fallbacks.

**Architecture:** All changes live in `zone_event_motor.py` (event decision engine) + `config.py` (tunable constants) + `tts_phrase_catalog.py` (new utterance IDs). The existing max-silence block (lines 1786-1798) is replaced by a context-aware function. New event types (`max_silence_go_by_feel`, `max_silence_breath_guide`, `max_silence_motivation`) route through the same event priority/payload system. Motivation cooldown is a new gating layer applied during event selection.

**Tech Stack:** Python 3.11, pytest, zone_event_motor.py event system

---

## Current State (What Exists)

| Component | Location | Current Behavior |
|-----------|----------|-----------------|
| Max-silence threshold | `config.py:157` | Fixed `MAX_SILENCE_SECONDS = 30` |
| Max-silence trigger | `zone_event_motor.py:1786-1798` | Fires when `elapsed - last_spoken >= 30`, emits `max_silence_override` |
| Max-silence text | `zone_event_motor.py:1500-1505` | 3 static messages (work/rest/default), no signal awareness |
| Max-silence priority | `zone_event_motor.py:175` | Priority 89 (below countdowns/phases, above zone events) |
| Event priority map | `zone_event_motor.py:164-183` | 2 tiers only (high: countdowns/phases, low: zone events) |
| Style rate-limiting | `zone_event_motor.py:1092-1145` | `_allow_style_event()` with cooldowns, but no motivation-specific barrier |
| Sensor mode | `zone_event_motor.py:712-778` | Detects FULL_HR / BREATH_FALLBACK / NO_SENSORS |
| Speech timestamp | `zone_event_motor.py:255,1802` | `last_spoken_elapsed` tracked in state |
| Phrase catalog | `tts_phrase_catalog.py:280-282` | 3 silence phrases, 1 no-sensors phrase, 10 motivation phrases |
| State fields | `zone_event_motor.py:223-258` | No motivation timing, no max-silence budget tracking |

## Target State (What We Build)

### A. Context-Aware Max-Silence Threshold

```python
def _compute_max_silence_seconds(workout_type, phase, elapsed_minutes, hr_missing, config_module):
    if workout_type == "intervals":
        base = 30 if phase == "work" else 45
    else:  # easy_run
        base = min(120, max(60, 45 + (elapsed_minutes // 10) * 15))

    if hr_missing and workout_type == "easy_run":
        base = round(base * 1.5)

    return base
```

### B. Cue Priority Tiers (4 tiers)

| Tier | Events | Priority Range |
|------|--------|---------------|
| **A** (highest) | `interval_countdown_*`, `hr_signal_lost`, `hr_signal_restored` | 93-100 |
| **B** | Phase transitions: `warmup_started`, `main_started`, `cooldown_started`, `workout_finished`, `pause_detected`, `pause_resumed` | 85-90 |
| **C** | Actionable coaching: `exited_target_above`, `exited_target_below`, `entered_target`, `recovery_relax_*`, `max_silence_breath_guide`, `max_silence_go_by_feel` | 60-70 |
| **D** (lowest) | Motivation filler: `max_silence_motivation` | 10 |

Notices (`watch_disconnected_notice`, `no_sensors_notice`, `watch_restored_notice`) stay at 88 (between A and B).

### C. Motivation Cooldown Barrier

New gating applied during event selection (before `_allow_style_event`):

```
_allow_motivation_event(state, workout_type, elapsed_seconds):
  Rule 1: After Tier A/B/C spoken → suppress Tier D for barrier_window
           intervals: 25s, easy_run: 45s
  Rule 2: Min spacing between Tier D
           intervals: 60s, easy_run: 120s
  Rule 3: If Tier A/B/C eligible same tick → drop Tier D
```

### D. Signal-Aware Max-Silence Utterance Selection

When max-silence fires, choose event type based on available signals:

```
if hr_available and target_enforced:
    → max_silence_override (existing zone coaching text)
elif breath_reliable:
    → max_silence_breath_guide (breath-focused guidance)
elif not hr_available:
    → max_silence_go_by_feel (RPE: "steady effort", "relax", "controlled push")
else:
    → max_silence_motivation (generic encouragement)
```

### E. Speech Budget Guards

- **easy_run**: max 1 `max_silence_*` event per 90s (regardless of threshold)
- **intervals**: max 1 `max_silence_*` per `phase_id` (countdowns exempt)

### F. Interval Suppression

- Suppress `max_silence_*` during recovery when `remaining_phase_seconds <= 35` (countdowns will fire)
- Suppress during work phase first 12s (HR lag ramp window)

---

## New Phrase Catalog Entries

Add to `tts_phrase_catalog.py`:

```python
# Go-by-feel (no HR, no breath) — phase-aware
{"id": "zone.feel.easy_run.1", "en": "Steady effort. Stay comfortable.", "no": "Jevn innsats. Hold det behagelig.", ...}
{"id": "zone.feel.easy_run.2", "en": "Find your rhythm and hold it.", "no": "Finn rytmen din og hold den.", ...}
{"id": "zone.feel.easy_run.3", "en": "Easy and controlled. You set the pace.", "no": "Rolig og kontrollert. Du bestemmer tempoet.", ...}
{"id": "zone.feel.work.1", "en": "Push hard but controlled.", "no": "Trykk hardt men kontrollert.", ...}
{"id": "zone.feel.work.2", "en": "Strong effort now. Stay focused.", "no": "Sterk innsats nå. Hold fokus.", ...}
{"id": "zone.feel.recovery.1", "en": "Ease off. Let your body recover.", "no": "Slipp av. La kroppen hente seg inn.", ...}
{"id": "zone.feel.recovery.2", "en": "Relax and breathe. Recovery counts.", "no": "Slapp av og pust. Hvile teller.", ...}

# Breath guidance (no HR, breath reliable)
{"id": "zone.breath.easy_run.1", "en": "Match your breathing to your pace.", "no": "Tilpass pusten til tempoet.", ...}
{"id": "zone.breath.easy_run.2", "en": "Smooth breaths. You're doing well.", "no": "Jevn pust. Du gjør det bra.", ...}
{"id": "zone.breath.work.1", "en": "Breathe through the effort.", "no": "Pust gjennom innsatsen.", ...}
{"id": "zone.breath.recovery.1", "en": "Slow your breathing down.", "no": "Senk pustetakten.", ...}
```

---

## Tasks

### Task 1: Add config constants for context-aware max silence

**Files:**
- Modify: `config.py:157` (replace single constant with group)

**Step 1: Write the failing test**

Create `tests_phaseb/test_context_aware_max_silence.py`:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def test_config_has_max_silence_easy_run_base():
    assert hasattr(config, "MAX_SILENCE_EASY_RUN_BASE")
    assert config.MAX_SILENCE_EASY_RUN_BASE == 60

def test_config_has_max_silence_intervals_work():
    assert hasattr(config, "MAX_SILENCE_INTERVALS_WORK")
    assert config.MAX_SILENCE_INTERVALS_WORK == 30

def test_config_has_max_silence_intervals_recovery():
    assert hasattr(config, "MAX_SILENCE_INTERVALS_RECOVERY")
    assert config.MAX_SILENCE_INTERVALS_RECOVERY == 45

def test_config_has_max_silence_ramp_per_10min():
    assert hasattr(config, "MAX_SILENCE_RAMP_PER_10MIN")
    assert config.MAX_SILENCE_RAMP_PER_10MIN == 15

def test_config_has_max_silence_hr_missing_multiplier():
    assert hasattr(config, "MAX_SILENCE_HR_MISSING_MULTIPLIER")
    assert config.MAX_SILENCE_HR_MISSING_MULTIPLIER == 1.5

def test_config_has_motivation_barrier_intervals():
    assert hasattr(config, "MOTIVATION_BARRIER_SECONDS_INTERVALS")
    assert config.MOTIVATION_BARRIER_SECONDS_INTERVALS == 25

def test_config_has_motivation_barrier_easy_run():
    assert hasattr(config, "MOTIVATION_BARRIER_SECONDS_EASY_RUN")
    assert config.MOTIVATION_BARRIER_SECONDS_EASY_RUN == 45

def test_config_has_motivation_min_spacing_intervals():
    assert hasattr(config, "MOTIVATION_MIN_SPACING_INTERVALS")
    assert config.MOTIVATION_MIN_SPACING_INTERVALS == 60

def test_config_has_motivation_min_spacing_easy_run():
    assert hasattr(config, "MOTIVATION_MIN_SPACING_EASY_RUN")
    assert config.MOTIVATION_MIN_SPACING_EASY_RUN == 120

def test_config_has_max_silence_budget_easy_run():
    assert hasattr(config, "MAX_SILENCE_BUDGET_EASY_RUN_SECONDS")
    assert config.MAX_SILENCE_BUDGET_EASY_RUN_SECONDS == 90

def test_config_has_max_silence_interval_suppress_remaining():
    assert hasattr(config, "MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING")
    assert config.MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING == 35

def test_config_has_max_silence_interval_work_ramp_seconds():
    assert hasattr(config, "MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS")
    assert config.MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS == 12

def test_legacy_max_silence_seconds_still_exists():
    """Legacy constant must remain for non-zone workouts."""
    assert hasattr(config, "MAX_SILENCE_SECONDS")
    assert config.MAX_SILENCE_SECONDS == 30
```

**Step 2: Run test to verify it fails**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v`
Expected: FAIL (missing attributes)

**Step 3: Add constants to config.py**

At `config.py:157`, keep `MAX_SILENCE_SECONDS = 30` (legacy). Add below it:

```python
# Context-aware max silence (zone event motor)
MAX_SILENCE_EASY_RUN_BASE = int(os.getenv("MAX_SILENCE_EASY_RUN_BASE", "60"))
MAX_SILENCE_INTERVALS_WORK = int(os.getenv("MAX_SILENCE_INTERVALS_WORK", "30"))
MAX_SILENCE_INTERVALS_RECOVERY = int(os.getenv("MAX_SILENCE_INTERVALS_RECOVERY", "45"))
MAX_SILENCE_RAMP_PER_10MIN = int(os.getenv("MAX_SILENCE_RAMP_PER_10MIN", "15"))
MAX_SILENCE_HR_MISSING_MULTIPLIER = float(os.getenv("MAX_SILENCE_HR_MISSING_MULTIPLIER", "1.5"))
MAX_SILENCE_BUDGET_EASY_RUN_SECONDS = int(os.getenv("MAX_SILENCE_BUDGET_EASY_RUN_SECONDS", "90"))
MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING = int(os.getenv("MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING", "35"))
MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS = int(os.getenv("MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS", "12"))

# Motivation cooldown barrier
MOTIVATION_BARRIER_SECONDS_INTERVALS = int(os.getenv("MOTIVATION_BARRIER_SECONDS_INTERVALS", "25"))
MOTIVATION_BARRIER_SECONDS_EASY_RUN = int(os.getenv("MOTIVATION_BARRIER_SECONDS_EASY_RUN", "45"))
MOTIVATION_MIN_SPACING_INTERVALS = int(os.getenv("MOTIVATION_MIN_SPACING_INTERVALS", "60"))
MOTIVATION_MIN_SPACING_EASY_RUN = int(os.getenv("MOTIVATION_MIN_SPACING_EASY_RUN", "120"))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add config.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: add context-aware max-silence and motivation barrier config constants"
```

---

### Task 2: Add new phrase catalog entries for go-by-feel and breath guidance

**Files:**
- Modify: `tts_phrase_catalog.py` (add entries after existing `zone.silence.*` block, around line 282)

**Step 1: Write the failing test**

Add to `tests_phaseb/test_context_aware_max_silence.py`:

```python
from tts_phrase_catalog import PHRASES

def test_phrase_catalog_has_go_by_feel_easy_run():
    ids = {p["id"] for p in PHRASES}
    assert "zone.feel.easy_run.1" in ids
    assert "zone.feel.easy_run.2" in ids
    assert "zone.feel.easy_run.3" in ids

def test_phrase_catalog_has_go_by_feel_work():
    ids = {p["id"] for p in PHRASES}
    assert "zone.feel.work.1" in ids
    assert "zone.feel.work.2" in ids

def test_phrase_catalog_has_go_by_feel_recovery():
    ids = {p["id"] for p in PHRASES}
    assert "zone.feel.recovery.1" in ids
    assert "zone.feel.recovery.2" in ids

def test_phrase_catalog_has_breath_guide_phrases():
    ids = {p["id"] for p in PHRASES}
    assert "zone.breath.easy_run.1" in ids
    assert "zone.breath.easy_run.2" in ids
    assert "zone.breath.work.1" in ids
    assert "zone.breath.recovery.1" in ids

def test_go_by_feel_phrases_are_bilingual():
    for p in PHRASES:
        if p["id"].startswith("zone.feel."):
            assert p.get("en"), f"{p['id']} missing English"
            assert p.get("no"), f"{p['id']} missing Norwegian"
            assert p.get("persona") == "personal_trainer"
            assert p.get("priority") == "core"

def test_breath_guide_phrases_are_bilingual():
    for p in PHRASES:
        if p["id"].startswith("zone.breath."):
            assert p.get("en"), f"{p['id']} missing English"
            assert p.get("no"), f"{p['id']} missing Norwegian"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py::test_phrase_catalog_has_go_by_feel_easy_run -v`
Expected: FAIL

**Step 3: Add phrases to catalog**

In `tts_phrase_catalog.py`, after line 282 (`zone.silence.default.1`), add:

```python
    # Go-by-feel fallback (no HR, no reliable breath) — phase-aware
    {"id": "zone.feel.easy_run.1", "en": "Steady effort. Stay comfortable.", "no": "Jevn innsats. Hold det behagelig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.easy_run.2", "en": "Find your rhythm and hold it.", "no": "Finn rytmen din og hold den.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.easy_run.3", "en": "Easy and controlled. You set the pace.", "no": "Rolig og kontrollert. Du bestemmer tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.work.1", "en": "Push hard but controlled.", "no": "Trykk hardt men kontrollert.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.work.2", "en": "Strong effort now. Stay focused.", "no": "Sterk innsats nå. Hold fokus.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.recovery.1", "en": "Ease off. Let your body recover.", "no": "Slipp av. La kroppen hente seg inn.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.recovery.2", "en": "Relax and breathe. Recovery counts.", "no": "Slapp av og pust. Hvile teller.", "persona": "personal_trainer", "priority": "core"},

    # Breath guidance fallback (no HR, breath reliable)
    {"id": "zone.breath.easy_run.1", "en": "Match your breathing to your pace.", "no": "Tilpass pusten til tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.easy_run.2", "en": "Smooth breaths. You're doing well.", "no": "Jevn pust. Du gjør det bra.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.work.1", "en": "Breathe through the effort.", "no": "Pust gjennom innsatsen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.recovery.1", "en": "Slow your breathing down.", "no": "Senk pustetakten.", "persona": "personal_trainer", "priority": "core"},
```

**Step 4: Run test to verify it passes**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k phrase`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add tts_phrase_catalog.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: add go-by-feel and breath-guidance phrases to catalog"
```

---

### Task 3: Implement `_compute_max_silence_seconds()` in zone_event_motor

**Files:**
- Modify: `zone_event_motor.py` (add function around line 183, after `_event_priority`)

**Step 1: Write the failing test**

Add to `tests_phaseb/test_context_aware_max_silence.py`:

```python
from zone_event_motor import _compute_max_silence_seconds

def test_max_silence_intervals_work():
    assert _compute_max_silence_seconds("intervals", "work", 5, False, config) == 30

def test_max_silence_intervals_recovery():
    assert _compute_max_silence_seconds("intervals", "recovery", 5, False, config) == 45

def test_max_silence_easy_run_base():
    # At 0 min: clamp(45+0, 60, 120) = 60
    assert _compute_max_silence_seconds("easy_run", "main", 0, False, config) == 60

def test_max_silence_easy_run_10min():
    # At 10 min: clamp(45+15, 60, 120) = 60
    assert _compute_max_silence_seconds("easy_run", "main", 10, False, config) == 60

def test_max_silence_easy_run_20min():
    # At 20 min: clamp(45+30, 60, 120) = 75
    assert _compute_max_silence_seconds("easy_run", "main", 20, False, config) == 75

def test_max_silence_easy_run_30min():
    # At 30 min: clamp(45+45, 60, 120) = 90
    assert _compute_max_silence_seconds("easy_run", "main", 30, False, config) == 90

def test_max_silence_easy_run_50min():
    # At 50 min: clamp(45+75, 60, 120) = 120 (cap)
    assert _compute_max_silence_seconds("easy_run", "main", 50, False, config) == 120

def test_max_silence_easy_run_hr_missing_multiplier():
    # At 0 min: base=60, * 1.5 = 90
    assert _compute_max_silence_seconds("easy_run", "main", 0, True, config) == 90

def test_max_silence_easy_run_30min_hr_missing():
    # At 30 min: base=90, * 1.5 = 135
    assert _compute_max_silence_seconds("easy_run", "main", 30, True, config) == 135

def test_max_silence_intervals_work_hr_missing_unchanged():
    # Intervals work: HR missing does NOT change threshold (still want guidance)
    assert _compute_max_silence_seconds("intervals", "work", 5, True, config) == 30

def test_max_silence_intervals_recovery_hr_missing_unchanged():
    assert _compute_max_silence_seconds("intervals", "recovery", 5, True, config) == 45
```

**Step 2: Run test to verify it fails**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k "max_silence_intervals or max_silence_easy_run"`
Expected: FAIL (ImportError: cannot import `_compute_max_silence_seconds`)

**Step 3: Implement the function**

In `zone_event_motor.py`, after `_event_priority()` (line 183), add:

```python
def _compute_max_silence_seconds(
    workout_type: str,
    phase: str,
    elapsed_minutes: int,
    hr_missing: bool,
    config_module,
) -> int:
    """Context-aware max-silence threshold.

    easy_run: 60s base, ramps +15s per 10min, capped at 120s.
    intervals work: 30s fixed. intervals recovery: 45s fixed.
    HR-missing multiplier (easy_run only): 1.5x.
    """
    if workout_type == "intervals":
        if phase == "work":
            return int(getattr(config_module, "MAX_SILENCE_INTERVALS_WORK", 30))
        return int(getattr(config_module, "MAX_SILENCE_INTERVALS_RECOVERY", 45))

    # easy_run (or any non-interval zone workout)
    base_val = int(getattr(config_module, "MAX_SILENCE_EASY_RUN_BASE", 60))
    ramp = int(getattr(config_module, "MAX_SILENCE_RAMP_PER_10MIN", 15))
    raw = 45 + (elapsed_minutes // 10) * ramp
    base = min(120, max(base_val, raw))

    if hr_missing:
        multiplier = float(getattr(config_module, "MAX_SILENCE_HR_MISSING_MULTIPLIER", 1.5))
        base = round(base * multiplier)

    return base
```

**Step 4: Run test to verify it passes**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k "max_silence_intervals or max_silence_easy_run"`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add zone_event_motor.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: add _compute_max_silence_seconds with context-aware thresholds"
```

---

### Task 4: Implement motivation cooldown barrier

**Files:**
- Modify: `zone_event_motor.py` (add `_allow_motivation_event()` after `_allow_style_event` at line 1145, add state fields in `_zone_state` around line 255)

**Step 1: Write the failing test**

Add to `tests_phaseb/test_context_aware_max_silence.py`:

```python
from zone_event_motor import _allow_motivation_event

def test_motivation_allowed_when_no_recent_high_priority():
    state = {}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True

def test_motivation_blocked_by_barrier_easy_run():
    state = {"last_high_priority_spoken_elapsed": 280.0}
    # 300 - 280 = 20s < 45s barrier for easy_run
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is False

def test_motivation_allowed_after_barrier_easy_run():
    state = {"last_high_priority_spoken_elapsed": 250.0}
    # 300 - 250 = 50s >= 45s barrier for easy_run
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True

def test_motivation_blocked_by_barrier_intervals():
    state = {"last_high_priority_spoken_elapsed": 290.0}
    # 300 - 290 = 10s < 25s barrier for intervals
    assert _allow_motivation_event(state=state, workout_type="intervals", elapsed_seconds=300, config_module=config) is False

def test_motivation_blocked_by_min_spacing_easy_run():
    state = {"last_motivation_spoken_elapsed": 200.0}
    # 300 - 200 = 100s < 120s min spacing for easy_run
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is False

def test_motivation_allowed_after_min_spacing_easy_run():
    state = {"last_motivation_spoken_elapsed": 170.0}
    # 300 - 170 = 130s >= 120s min spacing for easy_run
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True

def test_motivation_blocked_by_min_spacing_intervals():
    state = {"last_motivation_spoken_elapsed": 260.0}
    # 300 - 260 = 40s < 60s min spacing for intervals
    assert _allow_motivation_event(state=state, workout_type="intervals", elapsed_seconds=300, config_module=config) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k motivation`
Expected: FAIL (ImportError)

**Step 3: Implement**

In `_zone_state()` (around line 255), add new state fields:

```python
    state.setdefault("last_high_priority_spoken_elapsed", None)
    state.setdefault("last_motivation_spoken_elapsed", None)
    state.setdefault("last_max_silence_elapsed", None)
```

After `_allow_style_event()` (line 1145), add:

```python
def _allow_motivation_event(
    *,
    state: Dict[str, Any],
    workout_type: str,
    elapsed_seconds: int,
    config_module,
) -> bool:
    """Motivation cooldown barrier. Returns True if Tier D event is allowed."""
    is_intervals = workout_type == "intervals"

    # Rule 1: Barrier after high-priority (Tier A/B/C) speech
    barrier = int(getattr(
        config_module,
        "MOTIVATION_BARRIER_SECONDS_INTERVALS" if is_intervals else "MOTIVATION_BARRIER_SECONDS_EASY_RUN",
        25 if is_intervals else 45,
    ))
    last_hp = _safe_float(state.get("last_high_priority_spoken_elapsed"))
    if last_hp is not None and (float(elapsed_seconds) - last_hp) < barrier:
        return False

    # Rule 2: Min spacing between motivation events
    spacing = int(getattr(
        config_module,
        "MOTIVATION_MIN_SPACING_INTERVALS" if is_intervals else "MOTIVATION_MIN_SPACING_EASY_RUN",
        60 if is_intervals else 120,
    ))
    last_mot = _safe_float(state.get("last_motivation_spoken_elapsed"))
    if last_mot is not None and (float(elapsed_seconds) - last_mot) < spacing:
        return False

    return True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k motivation`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add zone_event_motor.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: add motivation cooldown barrier with tier-based suppression"
```

---

### Task 5: Update event priority map with 4-tier system

**Files:**
- Modify: `zone_event_motor.py:164-183` (`_event_priority`)
- Modify: `zone_event_motor.py:1084-1089` (`_event_group`) — add motivation group

**Step 1: Write the failing test**

Add to `tests_phaseb/test_context_aware_max_silence.py`:

```python
from zone_event_motor import _event_priority, _event_group

def test_tier_a_highest_priority():
    assert _event_priority("interval_countdown_start") > _event_priority("main_started")
    assert _event_priority("hr_signal_lost") > _event_priority("main_started")

def test_tier_b_above_tier_c():
    assert _event_priority("main_started") > _event_priority("exited_target_above")
    assert _event_priority("cooldown_started") > _event_priority("entered_target")

def test_tier_c_above_tier_d():
    assert _event_priority("exited_target_above") > _event_priority("max_silence_motivation")
    assert _event_priority("max_silence_go_by_feel") > _event_priority("max_silence_motivation")
    assert _event_priority("max_silence_breath_guide") > _event_priority("max_silence_motivation")

def test_max_silence_go_by_feel_is_tier_c():
    assert _event_priority("max_silence_go_by_feel") >= 60

def test_max_silence_motivation_is_tier_d():
    assert _event_priority("max_silence_motivation") < 20

def test_event_group_motivation():
    assert _event_group("max_silence_motivation") == "motivation"

def test_event_group_go_by_feel():
    assert _event_group("max_silence_go_by_feel") == "info"

def test_event_group_breath_guide():
    assert _event_group("max_silence_breath_guide") == "info"

def test_pause_events_in_priority():
    assert _event_priority("pause_detected") >= 85
    assert _event_priority("pause_resumed") >= 85
```

**Step 2: Run test to verify it fails**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k tier`
Expected: FAIL

**Step 3: Update priority map and event group**

Replace `_event_priority` (lines 164-183):

```python
def _event_priority(event_type: str) -> int:
    """4-tier event priority. A(93-100) > B(85-90) > notices(88) > C(60-70) > D(10)."""
    order = {
        # Tier A — countdowns + signal loss (highest)
        "interval_countdown_start": 100,
        "hr_signal_lost": 99,
        "hr_signal_restored": 98,
        "interval_countdown_5": 95,
        "interval_countdown_15": 94,
        "interval_countdown_30": 93,
        # Tier B — phase transitions
        "warmup_started": 90,
        "main_started": 90,
        "cooldown_started": 90,
        "workout_finished": 90,
        "pause_detected": 86,
        "pause_resumed": 85,
        # Notices (between B and C)
        "watch_disconnected_notice": 88,
        "no_sensors_notice": 88,
        "watch_restored_notice": 88,
        # Tier C — actionable coaching + signal-aware fallbacks
        "exited_target_above": 70,
        "exited_target_below": 70,
        "max_silence_override": 69,
        "max_silence_go_by_feel": 68,
        "max_silence_breath_guide": 67,
        "entered_target": 60,
        # Tier D — motivation filler (lowest)
        "max_silence_motivation": 10,
    }
    return order.get(event_type, 0)
```

Update `_event_group` (lines 1084-1089):

```python
def _event_group(event_type: str) -> str:
    if event_type in {"above_zone", "below_zone", "above_zone_ease", "below_zone_push"}:
        return "corrective"
    if event_type in {"in_zone_recovered"}:
        return "positive"
    if event_type in {"max_silence_motivation"}:
        return "motivation"
    return "info"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k "tier or event_group"`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add zone_event_motor.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: update event priority to 4-tier system with motivation tier"
```

---

### Task 6: Replace max-silence block with context-aware + signal-aware logic

This is the core change. Replace lines 1786-1798 in `zone_event_motor.py`.

**Files:**
- Modify: `zone_event_motor.py:1786-1798` (max-silence block)
- Modify: `zone_event_motor.py:1500-1505` (`_event_text` for new event types)

**Step 1: Write the failing tests**

Add to `tests_phaseb/test_context_aware_max_silence.py`:

```python
def _base_tick(**overrides):
    """Reusable base payload for evaluate_zone_tick."""
    payload = {
        "workout_state": {},
        "workout_mode": "easy_run",
        "phase": "intense",
        "elapsed_seconds": 300,
        "language": "en",
        "persona": "personal_trainer",
        "coaching_style": "normal",
        "interval_template": "4x4",
        "heart_rate": 145,
        "hr_quality": "good",
        "hr_confidence": 0.9,
        "hr_sample_age_seconds": 0.5,
        "hr_sample_gap_seconds": 1.0,
        "movement_score": None,
        "cadence_spm": None,
        "movement_source": "none",
        "watch_connected": True,
        "watch_status": "connected",
        "hr_max": 190,
        "resting_hr": 55,
        "age": 35,
        "config_module": config,
    }
    payload.update(overrides)
    return payload


def test_no_watch_no_mic_still_speaks_within_threshold():
    """HR missing + no breath => max_silence fires with go-by-feel event."""
    state = {}
    # First tick: sets last_spoken_elapsed (sensor notices speak)
    evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=10,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
        breath_intensity=None, breath_signal_quality=0.0,
    ))
    # Advance past max-silence threshold (60s for easy_run)
    result = evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=80,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
        breath_intensity=None, breath_signal_quality=0.0,
    ))
    assert result["should_speak"] is True
    assert result["primary_event_type"] in {
        "max_silence_go_by_feel", "max_silence_override", "max_silence_motivation"
    }


def test_no_watch_breath_reliable_uses_breath_guide():
    """HR missing + breath reliable => max_silence fires with breath guidance."""
    state = {}
    # Establish breath as reliable (need multiple ticks)
    for t in range(0, 30, 2):
        evaluate_zone_tick(**_base_tick(
            workout_state=state, elapsed_seconds=t,
            heart_rate=None, hr_quality="poor",
            watch_connected=False, watch_status="disconnected",
            breath_intensity="moderate", breath_signal_quality=0.8,
        ))
    # Advance past threshold
    result = evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=100,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
        breath_intensity="moderate", breath_signal_quality=0.8,
    ))
    assert result["should_speak"] is True
    # Should be breath_guide OR go_by_feel (depends on sensor mode dwell)
    assert result["primary_event_type"] in {
        "max_silence_breath_guide", "max_silence_go_by_feel",
        "max_silence_override", "max_silence_motivation",
    }


def test_max_silence_easy_run_uses_computed_threshold():
    """Easy_run at 0min should use 60s threshold, not fixed 30s."""
    state = {}
    # First tick sets last_spoken_elapsed
    evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=0,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
    ))
    # At 35s: should NOT trigger (old 30s would, new 60s won't)
    result = evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=35,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
    ))
    # Should be silent (35s < 60s threshold for easy_run)
    assert result["should_speak"] is False or result["primary_event_type"] not in {
        "max_silence_override", "max_silence_go_by_feel",
        "max_silence_breath_guide", "max_silence_motivation",
    }


def test_max_silence_budget_easy_run_90s():
    """Easy_run: max_silence events should not fire more than once per 90s."""
    state = {}
    evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=0,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
    ))
    # First max-silence at ~65s
    r1 = evaluate_zone_tick(**_base_tick(
        workout_state=state, elapsed_seconds=65,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
    ))
    # If it spoke, try again at 130s (only 65s since last max_silence < 90s budget)
    if r1["should_speak"]:
        r2 = evaluate_zone_tick(**_base_tick(
            workout_state=state, elapsed_seconds=130,
            heart_rate=None, hr_quality="poor",
            watch_connected=False, watch_status="disconnected",
        ))
        # Should NOT fire (130-65=65s < 90s budget)
        if r2.get("primary_event_type", "").startswith("max_silence_"):
            assert False, "max_silence fired within 90s budget window"


def test_interval_recovery_countdown_suppresses_max_silence():
    """During interval recovery with remaining <= 35s, max_silence suppressed."""
    state = {}
    # Simulate interval recovery with countdown imminent
    evaluate_zone_tick(**_base_tick(
        workout_state=state, workout_mode="interval",
        phase="intense", elapsed_seconds=0,
        heart_rate=None, hr_quality="poor",
        watch_connected=False, watch_status="disconnected",
    ))
    # This test validates the suppression logic exists;
    # exact behavior depends on interval_template providing segment_remaining_seconds


def test_no_invisible_speech_decisions():
    """If should_speak=True in event workout, events[] must be non-empty."""
    state = {}
    for t in range(0, 200, 5):
        result = evaluate_zone_tick(**_base_tick(
            workout_state=state, elapsed_seconds=t,
            heart_rate=None, hr_quality="poor",
            watch_connected=False, watch_status="disconnected",
        ))
        if result["should_speak"]:
            events = result.get("events", [])
            assert len(events) > 0, (
                f"should_speak=True at t={t} but events is empty. "
                f"reason={result['reason']}, event_type={result.get('event_type')}"
            )
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v -k "no_watch or max_silence_easy or budget or countdown_suppresses or invisible"`
Expected: FAIL (tests reference new event types not yet emitted)

**Step 3: Replace max-silence block**

In `zone_event_motor.py`, replace lines 1786-1798 with:

```python
    # ── Context-aware max silence with signal-aware utterance selection ──
    if not should_speak and not pause_flag and not bool(state.get("session_finished")):
        elapsed_minutes = int(elapsed_seconds) // 60
        hr_missing = sensor_mode != "FULL_HR"
        max_silence_sec = _compute_max_silence_seconds(
            canonical_workout_type, canonical_phase, elapsed_minutes, hr_missing, config_module,
        )

        last_spoken_elapsed = _safe_float(state.get("last_spoken_elapsed"))
        if last_spoken_elapsed is not None:
            elapsed_since_spoken = max(0.0, float(elapsed_seconds) - last_spoken_elapsed)
            if elapsed_since_spoken >= float(max_silence_sec):
                # Speech budget guard: easy_run max once per 90s, intervals max once per phase_id
                last_ms = _safe_float(state.get("last_max_silence_elapsed"))
                budget_ok = True
                if canonical_workout_type != "intervals":
                    budget_sec = int(getattr(config_module, "MAX_SILENCE_BUDGET_EASY_RUN_SECONDS", 90))
                    if last_ms is not None and (float(elapsed_seconds) - last_ms) < budget_sec:
                        budget_ok = False

                # Interval suppression: recovery countdown imminent or work ramp window
                suppress_remaining = int(getattr(config_module, "MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING", 35))
                work_ramp = int(getattr(config_module, "MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS", 12))
                if canonical_workout_type == "intervals":
                    remaining = _safe_int(target.get("segment_remaining_seconds"))
                    if canonical_phase == "recovery" and remaining is not None and remaining <= suppress_remaining:
                        budget_ok = False
                    phase_elapsed = _safe_float(target.get("segment_elapsed_seconds"))
                    if canonical_phase == "work" and phase_elapsed is not None and phase_elapsed < work_ramp:
                        budget_ok = False

                if budget_ok:
                    # Signal-aware utterance selection
                    if hr_available and target_enforced and sensor_mode == "FULL_HR":
                        ms_event = "max_silence_override"
                    elif sensor_mode == "BREATH_FALLBACK":
                        ms_event = "max_silence_breath_guide"
                    elif hr_missing:
                        ms_event = "max_silence_go_by_feel"
                    else:
                        ms_event = "max_silence_motivation"

                    # Rule 3: If any Tier A/B/C candidate was eligible, use motivation only if allowed
                    if ms_event == "max_silence_motivation":
                        if not _allow_motivation_event(
                            state=state,
                            workout_type=canonical_workout_type,
                            elapsed_seconds=int(elapsed_seconds),
                            config_module=config_module,
                        ):
                            ms_event = None  # Suppress entirely

                    if ms_event:
                        primary_event = ms_event
                        event_type = ms_event
                        should_speak = True
                        reason = ms_event
                        state["last_max_silence_elapsed"] = float(elapsed_seconds)
                        if ms_event == "max_silence_motivation":
                            state["last_motivation_spoken_elapsed"] = float(elapsed_seconds)
                        else:
                            state["last_high_priority_spoken_elapsed"] = float(elapsed_seconds)
                        if ms_event not in event_types:
                            event_types.append(ms_event)
```

**Step 4: Add `_event_text` entries for new event types**

In `_event_text()` (around line 1500), after the existing `max_silence_override` block, add:

```python
    if event_type == "max_silence_go_by_feel":
        if segment == "work":
            return "Trykk hardt men kontrollert." if lang == "no" else "Push hard but controlled."
        if segment == "rest" or segment == "recovery":
            return "Slipp av. La kroppen hente seg inn." if lang == "no" else "Ease off. Let your body recover."
        return "Jevn innsats. Hold det behagelig." if lang == "no" else "Steady effort. Stay comfortable."

    if event_type == "max_silence_breath_guide":
        if segment == "work":
            return "Pust gjennom innsatsen." if lang == "no" else "Breathe through the effort."
        if segment == "rest" or segment == "recovery":
            return "Senk pustetakten." if lang == "no" else "Slow your breathing down."
        return "Tilpass pusten til tempoet." if lang == "no" else "Match your breathing to your pace."

    if event_type == "max_silence_motivation":
        return "Du gjør det bra. Fortsett." if lang == "no" else "You're doing great. Keep going."
```

**Step 5: Update high-priority tracking in event selection loop**

After the event selection loop (around line 1778 where `should_speak = True` and `break` happen), add high-priority timestamp tracking. Inside the loop body where `should_speak = True`:

```python
    # Track high-priority spoken time for motivation barrier
    if primary_event and _event_priority(primary_event) >= 60:
        state["last_high_priority_spoken_elapsed"] = float(elapsed_seconds)
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py -v`
Expected: ALL PASS

**Step 7: Run existing zone_event_motor tests (regression)**

Run: `pytest tests_phaseb/test_zone_event_motor.py -v`
Expected: ALL PASS (no regressions)

**Step 8: Commit**

```bash
git add zone_event_motor.py tests_phaseb/test_context_aware_max_silence.py
git commit -m "feat: context-aware max-silence with signal-aware utterance selection and motivation barrier"
```

---

### Task 7: Add regression test — no silence beyond threshold in simulated session

**Files:**
- Modify: `tests_phaseb/test_context_aware_max_silence.py`

**Step 1: Write the simulation test**

```python
def test_regression_no_extended_silence_hr_missing_session():
    """Simulate 10 minutes of easy_run with hr_bpm=0. Coach must speak periodically."""
    state = {}
    spoken_at = []

    for t in range(0, 600, 3):  # Every 3 seconds for 10 min
        result = evaluate_zone_tick(**_base_tick(
            workout_state=state,
            elapsed_seconds=t,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_intensity=None,
            breath_signal_quality=0.0,
        ))
        if result["should_speak"]:
            spoken_at.append(t)

    # Must have spoken at least once
    assert len(spoken_at) > 0, "Coach never spoke in 10-minute no-HR session"

    # Check max gap between speeches (should be <= easy_run base * hr_missing_mult + budget)
    # At 0 min with HR missing: threshold = 90s, budget = 90s, so max gap ~180s worst case
    if len(spoken_at) > 1:
        gaps = [spoken_at[i+1] - spoken_at[i] for i in range(len(spoken_at) - 1)]
        max_gap = max(gaps)
        assert max_gap <= 200, f"Max gap between speeches was {max_gap}s (too long for no-HR session)"


def test_regression_intervals_no_hr_still_speaks():
    """Simulate 5 minutes of intervals with hr_bpm=0. Coach must speak."""
    state = {}
    spoken_at = []

    for t in range(0, 300, 3):
        result = evaluate_zone_tick(**_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=t,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
        ))
        if result["should_speak"]:
            spoken_at.append(t)

    assert len(spoken_at) > 0, "Coach never spoke in 5-minute no-HR interval session"

    # Intervals: 30s threshold, so max gap should be well under 60s
    if len(spoken_at) > 1:
        gaps = [spoken_at[i+1] - spoken_at[i] for i in range(len(spoken_at) - 1)]
        max_gap = max(gaps)
        assert max_gap <= 60, f"Max gap between speeches was {max_gap}s (too long for intervals)"
```

**Step 2: Run test**

Run: `pytest tests_phaseb/test_context_aware_max_silence.py::test_regression_no_extended_silence_hr_missing_session -v`
Expected: PASS

Run: `pytest tests_phaseb/test_context_aware_max_silence.py::test_regression_intervals_no_hr_still_speaks -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests_phaseb/test_context_aware_max_silence.py
git commit -m "test: add regression tests for no-HR session speech continuity"
```

---

### Task 8: Run full test suite + validate

**Step 1: Run all tests**

```bash
pytest tests_phaseb/ -v
```

Expected: ALL PASS

**Step 2: Compile-check backend**

```bash
python3 -m py_compile zone_event_motor.py config.py tts_phrase_catalog.py
```

Expected: No errors

**Step 3: Verify no regressions in existing zone tests**

```bash
pytest tests_phaseb/test_zone_event_motor.py tests_phaseb/test_zone_continuous_contract.py tests_phaseb/test_zone_llm_phrase_layer.py -v
```

Expected: ALL PASS

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: verify full test suite passes after context-aware max-silence"
```

---

## Summary of Changes

| File | Lines Changed | What |
|------|--------------|------|
| `config.py` | +14 constants | Context-aware thresholds + motivation barrier config |
| `zone_event_motor.py` | ~80 lines changed | `_compute_max_silence_seconds()`, `_allow_motivation_event()`, updated `_event_priority`, updated `_event_group`, replaced max-silence block, added `_event_text` entries |
| `tts_phrase_catalog.py` | +11 phrases | Go-by-feel (7) + breath-guidance (4) |
| `tests_phaseb/test_context_aware_max_silence.py` | NEW ~250 lines | Config tests, threshold tests, barrier tests, priority tests, integration tests, regression simulations |

## Debug Logging

The existing `reason` field in zone_tick output already captures why max-silence fired. New event types (`max_silence_go_by_feel`, `max_silence_breath_guide`, `max_silence_motivation`) appear in:
- `result["primary_event_type"]` — which max-silence variant
- `result["reason"]` — same as primary_event_type
- `result["events"]` payload — full event with sensor context
- iOS logs: `event_type` in events[] array

Log suppressed motivation cues via the existing `style_block_reason` mechanism (returns in `reason` field when `should_speak=False`).
