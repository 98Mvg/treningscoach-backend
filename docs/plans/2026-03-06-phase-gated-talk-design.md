# Phase-Gated Talk Design

**Date:** 2026-03-06
**Status:** Approved
**Approach:** Backend Phase Gate (Approach A)

## Problem

`/coach/talk` (wake-word + button) treats all workout phases the same. In reality:
- Users **cannot talk** during intense/work phases (high HR, gasping)
- Users **can and do talk** during warmup, recovery, easy run, cooldown
- Q&A answers are generic — they don't reference current HR, zone, phase, or timing
- Motivation during intense phases is already handled by zone events with pre-loaded MP3s

## Design Decisions

1. **Backend phase gate** — `/coach/talk` inspects phase and routes differently. iOS doesn't need to know the rules. Tunable via `config.py`.
2. **Intense/work → motivation-only** — no Grok call, no STT, no TTS. Return a `phrase_id` for pre-loaded MP3. Zero latency.
3. **Calm phases → enriched Q&A** — inject phase, timing, HR/zone (when watch connected) into Grok system prompt.
4. **Pre-compute all values** — iOS or backend pre-computes elapsed, remaining, set index, block time. Grok never calculates from raw timestamps.
5. **Metrics only if watch connected** — when HR > 0, inject HR/zone/targets. When no HR, prompt explicitly says "No heart rate data available. Do not reference specific HR numbers."

## Section 1: Phase Classification

```python
COACH_TALK_ELIGIBLE_PHASES = {"warmup", "prep", "recovery", "rest", "cooldown", "main", "easy_run"}
```

New function in `main.py`:

```python
def is_talk_eligible_phase(phase: str, workout_mode: str = "") -> bool:
    """True if phase allows Q&A conversation, False if motivation-only."""
    canonical = phase.strip().lower()
    if canonical in ("work", "intense"):
        return False
    return canonical in COACH_TALK_ELIGIBLE_PHASES
```

Unknown phases default to motivation-only (safe fallback).

## Section 2: Motivation-Only Response (Intense/Work)

When phase is not talk-eligible, return immediately:

```json
{
    "text": "Keep pushing!",
    "audio_url": "",
    "personality": "personal_trainer",
    "trigger_source": "wake_word",
    "phrase_id": "motivation.1",
    "phase_gated": true,
    "fallback_used": false,
    "latency_ms": 0,
    "provider": "phrase_catalog",
    "mode": "motivation_only"
}
```

- No STT, no Grok, no TTS
- iOS plays cached MP3 via `phrase_id`
- Cycle through `COACH_TALK_MOTIVATION_PHRASE_IDS` to avoid repetition
- Reuse existing motivation phrases from catalog

Config:
```python
COACH_TALK_MOTIVATION_PHRASE_IDS = [
    "motivation.1", "motivation.2", "motivation.3",
]
```

## Section 3: Enriched Q&A Prompt (Calm Phases)

When phase IS talk-eligible, enrich the existing Grok Q&A system prompt with a context block.

### Context block examples

Easy run, watch connected, 18 min in of 35 min total:
```
- Phase: easy run (main set).
- Time: 18 min elapsed, 17 min remaining of 35 min planned.
- Heart rate: 148 bpm. Target zone: 135-155 bpm. Status: in zone.
- Keep answers conversational — the athlete is at talking pace.
```

Interval, recovery, watch connected, set 3 of 4:
```
- Phase: recovery (rest between intervals).
- Set 3 of 4 complete. 2 sets remaining.
- Current block: recovery. Block time remaining: ~1 min 20 sec.
- Heart rate: 158 bpm. Target recovery: 120-135 bpm. Status: above target.
- Tone: calm, reassuring. Focus on recovery advice.
```

Warmup, no watch, 3 min in of 10 min warmup:
```
- Phase: warmup.
- Time: 3 min elapsed, 7 min remaining of 10 min warmup.
- No heart rate data available. Do not reference specific HR numbers.
- Tone: encouraging, preparatory.
```

### Phase tone hints (config)

```python
COACH_TALK_PHASE_HINTS = {
    "en": {
        "warmup": "Athlete is warming up. Encouraging, preparatory tone.",
        "recovery": "Athlete is resting between intervals. Calm, reassuring. Focus on recovery.",
        "cooldown": "Workout is ending. Reflective, summarizing tone. Can discuss how it went.",
        "main": "Easy run pace. Conversational, relaxed tone.",
        "prep": "About to start. Motivating, brief.",
    },
    "no": {
        "warmup": "Utøver varmer opp. Oppmuntrende, forberedende tone.",
        "recovery": "Utøver hviler mellom intervaller. Rolig, betryggende. Fokus på restitusjon.",
        "cooldown": "Økten avsluttes. Reflekterende, oppsummerende tone.",
        "main": "Rolig løping. Avslappet, samtalevennlig tone.",
        "prep": "Skal til å starte. Motiverende, kort.",
    },
}
```

### Metrics injection rules

| Condition | What gets injected |
|-----------|-------------------|
| `heart_rate > 0` | HR value, target range, zone state |
| `heart_rate == 0` or missing | "No heart rate data available. Do not reference specific HR numbers." |
| `elapsed_time_s` present | Elapsed/remaining time in human-readable format |
| `workout_mode == "interval"` | Current set, total sets, sets remaining, current block, block time remaining |

### Changes to brain_router.py

- `get_question_response()` gets new optional params: `phase`, `workout_context`
- `_build_qa_system_prompt()` gets same params, appends the enrichment block after existing prompt content

## Section 4: WorkoutTalkContext Expansion (iOS)

### Current struct
```swift
struct WorkoutTalkContext {
    let phase: String?
    let heartRate: Int?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let zoneState: String?
}
```

### Expanded struct
```swift
struct WorkoutTalkContext {
    // Existing
    let phase: String?
    let heartRate: Int?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let zoneState: String?

    // Global time (all modes)
    let elapsedTimeS: Int?
    let totalPlannedTimeS: Int?
    let timeRemainingS: Int?

    // Interval-only (nil for easy_run/standard)
    let workoutMode: String?          // "interval" | "easy_run" | "standard"
    let currentSet: Int?              // 1-based
    let totalSets: Int?
    let setsRemaining: Int?
    let currentBlock: String?         // "work" | "recovery"
    let blockTimeRemainingS: Int?
}
```

### Multipart field names

| Field | Key | Example |
|-------|-----|---------|
| Elapsed | `elapsed_time_s` | `1080` |
| Total planned | `total_planned_time_s` | `2100` |
| Remaining | `time_remaining_s` | `1020` |
| Workout mode | `workout_mode` | `interval` |
| Current set | `current_set` | `3` |
| Total sets | `total_sets` | `4` |
| Sets remaining | `sets_remaining` | `1` |
| Current block | `current_block` | `recovery` |
| Block remaining | `block_time_remaining_s` | `80` |

iOS pre-computes all values in `workoutTalkContextPayload()`. WorkoutViewModel already tracks elapsed seconds, total duration, interval set index, and segment timers.

Backend `collect_workout_context()` adds the new keys using the existing `_pick()` pattern.

## Section 5: Complete Flow

```
iOS triggers talk (wake-word or button)
  ↓
Backend /coach/talk receives trigger_source + workout_context
  ↓
Extract phase from workout_context
  ↓
Phase in COACH_TALK_ELIGIBLE_PHASES?
  │
  ├─ NO (intense/work)
  │   Skip STT, skip Grok
  │   Pick motivation phrase_id (cycling)
  │   Return {phrase_id, mode: "motivation_only", phase_gated: true, latency_ms: 0}
  │
  └─ YES (warmup/recovery/easy_run/cooldown/prep)
      Run STT (if audio present)
      Build enriched prompt (phase + tone + metrics if watch + timing + interval structure)
      Call Grok Q&A (timeout per trigger_source)
      On failure → phase+zone aware fallback
      TTS → audio_url
      Return {text, audio_url, mode: "qa", phase_gated: false}
```

## What Does NOT Change

- Zone event motor owns `/coach/continuous` — untouched
- Wake-word detection on iOS — untouched
- Talk arbitration (suppress zone events during talk) — untouched
- Trigger source validation (`wake_word`/`button` only) — untouched
- Wake ack phrase playback — untouched

## Files Touched

| File | Change |
|------|--------|
| `main.py` | Add `is_talk_eligible_phase()`, phase gate in `coach_talk()`, prompt enrichment builder |
| `config.py` | Add `COACH_TALK_ELIGIBLE_PHASES`, `COACH_TALK_PHASE_HINTS`, `COACH_TALK_MOTIVATION_PHRASE_IDS` |
| `brain_router.py` | Add `phase`, `workout_context` params to `get_question_response()` + `_build_qa_system_prompt()` |
| `WorkoutViewModel.swift` | Expand `workoutTalkContextPayload()` with timing/interval fields |
| `BackendAPIService.swift` | Send new multipart fields |
| `Models.swift` | Expand `WorkoutTalkContext` struct |
| `tests_phaseb/test_api_contracts.py` | Test phase gate (intense → motivation, recovery → Q&A) |
| `tests_phaseb/test_talk_to_coach_contract.py` | Test iOS sends new context fields |
