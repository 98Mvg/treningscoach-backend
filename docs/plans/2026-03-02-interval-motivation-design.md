# Interval & Easy-Run Motivation System — Design

**Date:** 2026-03-02
**Status:** Approved

## Summary

Add stage-based motivation events that fire when the user holds their target HR zone during work intervals and easy runs. Motivation intensity escalates by rep (intervals) or elapsed time (easy_run). Guard rails (too-high/too-low corrections) always win.

---

## 1. Phrase Catalog

Keep existing `coach.no.*` phrases for AI/persona reference. Add new deterministic event-routed IDs.

### Interval Motivation (16 entries: 8 phrase IDs × en + no)

| Phrase ID | Stage | NO text | EN text |
|---|---|---|---|
| `interval.motivate.s1.1` | 1 (supportive) | Nydelig. Jevnt og rolig. | Beautiful. Smooth and steady. |
| `interval.motivate.s1.2` | 1 (supportive) | Bra. Pust rolig. | Good. Breathe easy. |
| `interval.motivate.s2.1` | 2 (pressing) | Kom igjen! | Come on! |
| `interval.motivate.s2.2` | 2 (pressing) | Herlig! | Lovely! |
| `interval.motivate.s3.1` | 3 (intense) | Helt inn nå! Trøkk i beina! | All the way! Drive your legs! |
| `interval.motivate.s3.2` | 3 (intense) | Nå må du jobbe! Jevnt og godt. | Time to work! Smooth and strong. |
| `interval.motivate.s4.1` | 4 (peak) | ALT. NÅ. | EVERYTHING. NOW. |
| `interval.motivate.s4.2` | 4 (peak) | KOM IGJEN! Helt inn nå! | COME ON! All the way! |

### Easy-Run Motivation (16 entries: 8 phrase IDs × en + no)

| Phrase ID | Stage | NO text | EN text |
|---|---|---|---|
| `easy_run.motivate.s1.1` | 1 (supportive) | Kjør på! | Go for it! |
| `easy_run.motivate.s1.2` | 1 (supportive) | Senk tempoet. Godt. | Ease the pace. Good. |
| `easy_run.motivate.s2.1` | 2 (pressing) | Hold trykket jevnt. Hold kontrollen. | Steady pressure. Stay in control. |
| `easy_run.motivate.s2.2` | 2 (pressing) | JA! | YES! |
| `easy_run.motivate.s3.1` | 3 (intense) | En til. Ikke stopp. | One more. Don't stop. |
| `easy_run.motivate.s3.2` | 3 (intense) | Disiplin. Gjennomfør. | Discipline. Execute. |
| `easy_run.motivate.s4.1` | 4 (peak) | Fullfør draget. Nå. | Finish the rep. Now. |
| `easy_run.motivate.s4.2` | 4 (peak) | KOM IGJEN! Helt inn nå! | COME ON! All the way! |

**Total new entries:** 32 (16 phrase IDs × 2 languages)

---

## 2. Backend: `zone_event_motor.py`

### 2a. New event: `interval_in_target_sustained`

**Trigger conditions (ALL must be true):**
1. `workout_type == "intervals"` AND `segment == "work"`
2. `confirmed_zone_status == "in_zone"` continuously for `SUSTAIN_SEC_WORK` seconds
   - `SUSTAIN_SEC_WORK = clamp(round(0.30 * work_seconds), 12, 30)`
3. `work_elapsed_seconds >= 10` (avoid early HR lag)
4. No high-priority event (`priority >= 60`) spoken in last `MOTIVATION_BARRIER_SEC = 20`
5. Current motivation slot is eligible (see §2c)
6. `motivation_count_this_work_phase < budget` (see §2c)

**Payload additions:** `rep_index`, `stage` (1-4 from rep_index)

**Stage from rep_index (1-based):**
- rep 1 → stage 1 (supportive)
- rep 2 → stage 2 (pressing)
- rep 3 → stage 3 (intense)
- rep ≥ 4 → stage 4 (peak)

### 2b. New event: `easy_run_in_target_sustained`

**Trigger conditions:**
1. `workout_type == "easy_run"` AND `phase in {"main", "intense"}`
2. `confirmed_zone_status == "in_zone"` continuously for `SUSTAIN_SEC_EASY = 45` seconds
3. No high-priority event in last 20s
4. Cooldown between firings: `EASY_RUN_MOTIVATION_COOLDOWN = 120` seconds

**Stage from elapsed time into main phase:**
- 0–20 min → stage 1 (supportive)
- 20–40 min → stage 2 (pressing)
- 40–60 min → stage 3 (intense)
- 60+ min → stage 4 (peak)

### 2c. Dynamic Motivation Budget (Intervals Only)

**Budget per work phase:**
```
budget = clamp(floor(1 + work_seconds / 90), 1, 4)
```

Examples:
- 30s work → budget 1
- 45s work → budget 1
- 60s work → budget 1
- 120s work → budget 2
- 180s work → budget 3
- 240s work → budget 4

**Slot schedule (fractions of work phase):**
- budget=1: `[0.55]`
- budget=2: `[0.35, 0.75]`
- budget=3: `[0.25, 0.55, 0.85]`
- budget=4: `[0.20, 0.45, 0.70, 0.90]`

**Slot eligibility:**
- `work_elapsed_seconds >= slot_fraction * work_seconds`
- AND `confirmed_zone_status == "in_zone"` for `SUSTAIN_SEC_WORK`
- AND no higher priority cue in last `MOTIVATION_BARRIER_SEC`
- AND `motivation_count_this_work_phase < budget`
- AND slot not yet used (track `used_slots` per `phase_id`)
- AND `work_elapsed_seconds >= 10`

**State reset:** `motivation_count_this_work_phase` and `used_slots` reset on each new work `phase_id`.

### 2d. Phrase ID Resolution

**`_resolve_phrase_id` additions:**
- `interval_in_target_sustained` → `interval.motivate.s{stage}.{variant}`
- `easy_run_in_target_sustained` → `easy_run.motivate.s{stage}.{variant}`

Variant alternation: `.1` / `.2` alternating per `phase_id` (intervals) or per firing count (easy_run).

**Priority:** 55 (below `entered_target` at 60, above `max_silence_motivation` at 10).

### 2e. Config constants (added to `config.py`)

```python
MOTIVATION_BARRIER_SEC = 20
SUSTAIN_SEC_EASY = 45
EASY_RUN_MOTIVATION_COOLDOWN = 120
MOTIVATION_WORK_MIN_ELAPSED = 10
```

`SUSTAIN_SEC_WORK` is computed dynamically: `clamp(round(0.30 * work_seconds), 12, 30)`

---

## 3. iOS: `WorkoutViewModel.swift`

### `eventPriority(for:)`
```swift
case "interval_in_target_sustained", "easy_run_in_target_sustained":
    return 55
```

### `utteranceID(for:)`
Backend sends `phrase_id` in event payload → iOS uses `selected.phraseId` (already preferred over local mapping). Add fallback:
```swift
case "interval_in_target_sustained", "easy_run_in_target_sustained":
    // Backend provides phrase_id; this is fallback only
    return "interval.motivate.s2.1"
```

### `CoachingEventPayload` — no changes needed
`phaseId` and `elapsedSeconds` already present. Stage is resolved backend-side.

---

## 4. What stays unchanged

- Guard rails (`exited_target_above/below`) — priority 70, always win
- Countdown events — priority 93-100, always win
- `max_silence_motivation` — still fires on prolonged silence (different purpose)
- Recovery phase — no motivation events (relax + countdown only)
- `coach.no.*` phrases — remain for AI/persona coaching

---

## 5. Files to change

| File | Change |
|---|---|
| `tts_phrase_catalog.py` | Add 16 new phrase IDs (32 entries with en+no) |
| `zone_event_motor.py` | Add motivation event logic, slot scheduling, budget, sustain tracking |
| `config.py` | Add MOTIVATION_BARRIER_SEC, SUSTAIN_SEC_EASY, EASY_RUN_MOTIVATION_COOLDOWN, MOTIVATION_WORK_MIN_ELAPSED |
| `WorkoutViewModel.swift` | Add priority + utteranceID fallback for 2 new events |
| `tests_phaseb/` | Add tests for stage computation, budget, slot scheduling, phrase resolution |
