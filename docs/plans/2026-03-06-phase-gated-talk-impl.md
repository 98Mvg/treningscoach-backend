# Phase-Gated Talk Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Gate `/coach/talk` by workout phase — intense phases get instant motivation phrase_id (no Grok), calm phases get enriched Q&A with phase-aware system prompt and workout structure context.

**Architecture:** Backend-only phase gate in `main.py` `coach_talk()`. Extend `WorkoutTalkContext` on iOS with `workoutMode`, `elapsedTimeS`, `totalPlannedTimeS`. Enrich `_build_qa_system_prompt()` in `brain_router.py` with phase tone hints and workout metrics. No changes to zone_event_motor or /coach/continuous.

**Tech Stack:** Python (Flask), Swift (SwiftUI), pytest

**Design doc:** `docs/plans/2026-03-06-phase-gated-talk-design.md`

**Key discovery:** Much plumbing already exists:
- iOS already sends `timeLeftS`, `repIndex`, `repsTotal`, `repRemainingS`, `repsRemainingIncludingCurrent`
- Backend `collect_workout_context()` already collects all of these
- `build_workout_talk_prompt()` already injects context into the user prompt
- What's missing: phase gate, phase tone hints in system prompt, `elapsed_time_s`/`total_planned_time_s`/`workout_mode` fields

---

### Task 1: Config — Phase Gate Constants

**Files:**
- Modify: `config.py` (after line ~475, near existing `COACH_TALK_*` constants)

**Step 1: Write the failing test**

Create `tests_phaseb/test_phase_gated_talk.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def test_eligible_phases_is_a_set():
    phases = config.COACH_TALK_ELIGIBLE_PHASES
    assert isinstance(phases, (set, frozenset))
    assert "warmup" in phases
    assert "recovery" in phases
    assert "cooldown" in phases
    assert "main" in phases
    assert "prep" in phases
    assert "rest" in phases
    # Intense/work must NOT be eligible
    assert "intense" not in phases
    assert "work" not in phases


def test_motivation_phrase_ids_is_a_list():
    ids = config.COACH_TALK_MOTIVATION_PHRASE_IDS
    assert isinstance(ids, (list, tuple))
    assert len(ids) >= 3
    for pid in ids:
        assert pid.startswith("motivation.")


def test_phase_hints_has_both_languages():
    hints = config.COACH_TALK_PHASE_HINTS
    assert "en" in hints
    assert "no" in hints
    for lang in ("en", "no"):
        assert "warmup" in hints[lang]
        assert "recovery" in hints[lang]
        assert "cooldown" in hints[lang]
        assert "main" in hints[lang]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: FAIL — `AttributeError: module 'config' has no attribute 'COACH_TALK_ELIGIBLE_PHASES'`

**Step 3: Write minimal implementation**

Add to `config.py` after the existing `COACH_TALK_WORKOUT_FALLBACKS` block (~line 475):

```python
# Phase-gated talk: which phases allow Q&A vs motivation-only
COACH_TALK_ELIGIBLE_PHASES = frozenset({
    "warmup", "prep", "recovery", "rest", "cooldown", "main", "easy_run",
})

COACH_TALK_MOTIVATION_PHRASE_IDS = [
    "motivation.1", "motivation.2", "motivation.3",
    "motivation.4", "motivation.5", "motivation.6",
    "motivation.7", "motivation.8", "motivation.9",
]

COACH_TALK_PHASE_HINTS = {
    "en": {
        "warmup": "Athlete is warming up. Encouraging, preparatory tone.",
        "recovery": "Athlete is resting between intervals. Calm, reassuring. Focus on recovery.",
        "cooldown": "Workout is ending. Reflective, summarizing tone. Can discuss how it went.",
        "main": "Easy run pace. Conversational, relaxed tone.",
        "prep": "About to start. Motivating, brief.",
        "rest": "Athlete is resting between intervals. Calm, reassuring. Focus on recovery.",
    },
    "no": {
        "warmup": "Utøver varmer opp. Oppmuntrende, forberedende tone.",
        "recovery": "Utøver hviler mellom intervaller. Rolig, betryggende. Fokus på restitusjon.",
        "cooldown": "Økten avsluttes. Reflekterende, oppsummerende tone.",
        "main": "Rolig løping. Avslappet, samtalevennlig tone.",
        "prep": "Skal til å starte. Motiverende, kort.",
        "rest": "Utøver hviler mellom intervaller. Rolig, betryggende. Fokus på restitusjon.",
    },
}
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add config.py tests_phaseb/test_phase_gated_talk.py
git commit -m "feat: add phase gate config — eligible phases, motivation IDs, phase hints"
```

---

### Task 2: Backend — Phase Gate Function + Motivation Response

**Files:**
- Modify: `main.py` (add `is_talk_eligible_phase()` and `pick_motivation_phrase()` near other talk helpers ~line 420)
- Modify: `tests_phaseb/test_phase_gated_talk.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_phase_gated_talk.py`:

```python
# Import after config tests pass
from main import is_talk_eligible_phase, pick_motivation_phrase


def test_intense_is_not_eligible():
    assert is_talk_eligible_phase("intense") is False
    assert is_talk_eligible_phase("work") is False
    assert is_talk_eligible_phase("INTENSE") is False
    assert is_talk_eligible_phase("Work") is False


def test_calm_phases_are_eligible():
    for phase in ("warmup", "recovery", "cooldown", "main", "prep", "rest", "easy_run"):
        assert is_talk_eligible_phase(phase) is True, f"{phase} should be eligible"


def test_unknown_phase_is_not_eligible():
    assert is_talk_eligible_phase("") is False
    assert is_talk_eligible_phase("blah") is False


def test_pick_motivation_phrase_returns_valid_id():
    phrase_id, text_en, text_no = pick_motivation_phrase("en", session_id="test-1")
    assert phrase_id.startswith("motivation.")
    assert isinstance(text_en, str) and len(text_en) > 0

    phrase_id_no, _, text_no = pick_motivation_phrase("no", session_id="test-1")
    assert isinstance(text_no, str) and len(text_no) > 0


def test_pick_motivation_phrase_cycles():
    """Consecutive calls with same session should not always return the same phrase."""
    results = set()
    for i in range(20):
        pid, _, _ = pick_motivation_phrase("en", session_id="cycle-test")
        results.add(pid)
    assert len(results) >= 2, "Should cycle through multiple phrases"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py::test_intense_is_not_eligible -v`
Expected: FAIL — `ImportError: cannot import name 'is_talk_eligible_phase' from 'main'`

**Step 3: Write minimal implementation**

Add to `main.py` near the other talk helper functions (after `workout_talk_fallback`, around line ~420):

```python
def is_talk_eligible_phase(phase: str) -> bool:
    """True if phase allows Q&A conversation, False if motivation-only."""
    canonical = (phase or "").strip().lower()
    eligible = getattr(config, "COACH_TALK_ELIGIBLE_PHASES", frozenset())
    return canonical in eligible


# Simple per-session counter for motivation phrase cycling
_motivation_phrase_counters: dict[str, int] = {}


def pick_motivation_phrase(language: str, session_id: str = "") -> tuple[str, str, str]:
    """
    Pick the next motivation phrase for an intense-phase talk trigger.
    Returns (phrase_id, en_text, no_text).
    """
    from tts_phrase_catalog import PHRASE_CATALOG

    phrase_ids = list(getattr(config, "COACH_TALK_MOTIVATION_PHRASE_IDS", []))
    if not phrase_ids:
        phrase_ids = ["motivation.1"]

    key = session_id or "_global"
    counter = _motivation_phrase_counters.get(key, 0)
    idx = counter % len(phrase_ids)
    _motivation_phrase_counters[key] = counter + 1

    phrase_id = phrase_ids[idx]

    # Look up text from catalog
    en_text = "Keep going!"
    no_text = "Fortsett!"
    for entry in PHRASE_CATALOG:
        if entry.get("id") == phrase_id:
            en_text = entry.get("en", en_text)
            no_text = entry.get("no", no_text)
            break

    lang = normalize_language_code(language)
    return phrase_id, en_text, no_text
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: 8 passed

**Step 5: Commit**

```bash
git add main.py tests_phaseb/test_phase_gated_talk.py
git commit -m "feat: add is_talk_eligible_phase and pick_motivation_phrase helpers"
```

---

### Task 3: Backend — Wire Phase Gate into coach_talk()

**Files:**
- Modify: `main.py` (`coach_talk()` function, around line 4163)
- Modify: `tests_phaseb/test_phase_gated_talk.py`

**Step 1: Write the failing test**

Append to `tests_phaseb/test_phase_gated_talk.py`:

```python
import io
from tests_phaseb.test_api_contracts import _build_client


def test_intense_phase_returns_motivation_only(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.post(
        "/coach/talk",
        json={
            "message": "How am I doing?",
            "trigger_source": "wake_word",
            "context": "workout",
            "phase": "intense",
            "language": "en",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("mode") == "motivation_only"
    assert payload.get("phase_gated") is True
    assert payload.get("latency_ms", 999) < 100  # near-instant
    phrase_id = payload.get("phrase_id", "")
    assert phrase_id.startswith("motivation.")
    assert payload.get("provider") == "phrase_catalog"


def test_work_phase_returns_motivation_only(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.post(
        "/coach/talk",
        json={
            "message": "Quick tip",
            "trigger_source": "button",
            "context": "workout",
            "phase": "work",
            "language": "no",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("mode") == "motivation_only"
    assert payload.get("phase_gated") is True


def test_recovery_phase_uses_qa(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.post(
        "/coach/talk",
        json={
            "message": "How was that set?",
            "trigger_source": "button",
            "context": "workout",
            "phase": "recovery",
            "language": "en",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("phase_gated") is not True
    assert payload.get("mode") != "motivation_only"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py::test_intense_phase_returns_motivation_only -v`
Expected: FAIL — response will not have `mode: "motivation_only"` or `phase_gated: true`

**Step 3: Wire phase gate into coach_talk()**

In `main.py`, inside `coach_talk()`, after the phase/workout_context extraction (~line 4040) and BEFORE the policy check (~line 4100), add the phase gate early return:

```python
        # --- Phase gate: intense/work phases get instant motivation phrase ---
        if context == "workout" and not is_talk_eligible_phase(phase):
            phrase_id, en_text, no_text = pick_motivation_phrase(
                language, session_id=talk_session_id or ""
            )
            lang = normalize_language_code(language)
            coach_text = no_text if lang == "no" else en_text
            latency_ms = int(round((time.perf_counter() - started_at) * 1000))
            logger.info(
                "Coach talk phase-gated trigger=%s phase=%s phrase_id=%s latency_ms=%s",
                trigger_source, phase, phrase_id, latency_ms,
            )
            return jsonify({
                "contract_version": contract_version,
                "text": coach_text,
                "audio_url": "",
                "personality": persona,
                "trigger_source": trigger_source,
                "phrase_id": phrase_id,
                "phase_gated": True,
                "provider": "phrase_catalog",
                "mode": "motivation_only",
                "latency_ms": latency_ms,
                "fallback_used": False,
                "stt_source": "none",
            })
```

Also add `"phase_gated": False` to the existing normal response jsonify at the end of `coach_talk()`.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add main.py tests_phaseb/test_phase_gated_talk.py
git commit -m "feat: wire phase gate into /coach/talk — intense gets motivation, calm gets Q&A"
```

---

### Task 4: Backend — Enrich QA System Prompt with Phase + Metrics

**Files:**
- Modify: `brain_router.py` (`_build_qa_system_prompt` and `get_question_response`)
- Modify: `tests_phaseb/test_phase_gated_talk.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_phase_gated_talk.py`:

```python
from brain_router import BrainRouter


def test_qa_system_prompt_includes_phase_hint():
    router = BrainRouter()
    prompt = router._build_qa_system_prompt(
        language="en",
        persona="personal_trainer",
        context="workout",
        user_name=None,
        phase="recovery",
        workout_context=None,
    )
    assert "recovery" in prompt.lower()
    assert "calm" in prompt.lower() or "reassuring" in prompt.lower()


def test_qa_system_prompt_includes_hr_when_available():
    router = BrainRouter()
    prompt = router._build_qa_system_prompt(
        language="en",
        persona="personal_trainer",
        context="workout",
        user_name=None,
        phase="main",
        workout_context={
            "heart_rate": 152,
            "target_hr_low": 140,
            "target_hr_high": 160,
            "zone_state": "in_zone",
        },
    )
    assert "152" in prompt
    assert "140" in prompt or "160" in prompt
    assert "in zone" in prompt.lower() or "in_zone" in prompt.lower()


def test_qa_system_prompt_omits_hr_when_zero():
    router = BrainRouter()
    prompt = router._build_qa_system_prompt(
        language="no",
        persona="personal_trainer",
        context="workout",
        user_name=None,
        phase="warmup",
        workout_context={"heart_rate": 0},
    )
    assert "do not reference" in prompt.lower() or "ikke oppgi" in prompt.lower()


def test_qa_system_prompt_includes_timing():
    router = BrainRouter()
    prompt = router._build_qa_system_prompt(
        language="en",
        persona="personal_trainer",
        context="workout",
        user_name=None,
        phase="main",
        workout_context={
            "elapsed_time_s": 1200,
            "total_planned_time_s": 2100,
            "time_remaining_s": 900,
        },
    )
    # Should show human-readable minutes
    assert "20" in prompt  # 1200s = 20 min
    assert "15" in prompt  # 900s = 15 min


def test_qa_system_prompt_includes_interval_structure():
    router = BrainRouter()
    prompt = router._build_qa_system_prompt(
        language="en",
        persona="personal_trainer",
        context="workout",
        user_name=None,
        phase="recovery",
        workout_context={
            "workout_mode": "interval",
            "current_set": 3,
            "total_sets": 4,
            "sets_remaining": 1,
            "current_block": "recovery",
            "block_time_remaining_s": 95,
        },
    )
    assert "3" in prompt  # current set
    assert "4" in prompt  # total sets
    assert "1" in prompt  # sets remaining
    assert "recovery" in prompt.lower()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py::test_qa_system_prompt_includes_phase_hint -v`
Expected: FAIL — `_build_qa_system_prompt() got an unexpected keyword argument 'phase'`

**Step 3: Modify `_build_qa_system_prompt` in `brain_router.py`**

Update the method signature and append workout context enrichment:

```python
    def _build_qa_system_prompt(
        self,
        language: str,
        persona: Optional[str],
        context: str,
        user_name: Optional[str],
        phase: Optional[str] = None,
        workout_context: Optional[dict] = None,
    ) -> str:
        # ... existing prompt building stays identical ...
        # After assembling base_prompt (the existing return value), append enrichment:

        if context != "workout" or not phase:
            return base_prompt

        enrichment_parts = []

        # Phase tone hint
        hints = getattr(config, "COACH_TALK_PHASE_HINTS", {})
        lang_hints = hints.get(language, hints.get("en", {}))
        phase_hint = lang_hints.get(phase, "")
        if phase_hint:
            enrichment_parts.append(f"- {phase_hint}")

        wctx = workout_context if isinstance(workout_context, dict) else {}

        # Timing
        elapsed = wctx.get("elapsed_time_s")
        total = wctx.get("total_planned_time_s")
        remaining = wctx.get("time_remaining_s")
        if isinstance(elapsed, (int, float)) and isinstance(remaining, (int, float)):
            e_min = int(elapsed) // 60
            r_min = int(remaining) // 60
            if isinstance(total, (int, float)):
                t_min = int(total) // 60
                enrichment_parts.append(f"- Time: {e_min} min elapsed, {r_min} min remaining of {t_min} min planned.")
            else:
                enrichment_parts.append(f"- Time: {e_min} min elapsed, {r_min} min remaining.")

        # Interval structure
        workout_mode = str(wctx.get("workout_mode") or "").strip().lower()
        if workout_mode == "interval":
            c_set = wctx.get("current_set")
            t_sets = wctx.get("total_sets")
            s_rem = wctx.get("sets_remaining")
            c_block = str(wctx.get("current_block") or "").strip().lower()
            block_rem = wctx.get("block_time_remaining_s")
            if isinstance(c_set, int) and isinstance(t_sets, int):
                parts_line = f"- Set {c_set} of {t_sets}."
                if isinstance(s_rem, int):
                    parts_line += f" {s_rem} remaining."
                enrichment_parts.append(parts_line)
            if c_block:
                block_line = f"- Current block: {c_block}."
                if isinstance(block_rem, (int, float)):
                    b_min = int(block_rem) // 60
                    b_sec = int(block_rem) % 60
                    block_line += f" ~{b_min}m {b_sec}s remaining."
                enrichment_parts.append(block_line)

        # HR metrics (only when watch connected)
        hr = wctx.get("heart_rate")
        if isinstance(hr, (int, float)) and int(hr) > 0:
            hr_line = f"- Heart rate: {int(hr)} bpm."
            low = wctx.get("target_hr_low")
            high = wctx.get("target_hr_high")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                hr_line += f" Target: {int(low)}-{int(high)} bpm."
            zone = str(wctx.get("zone_state") or "").strip().lower()
            if zone:
                hr_line += f" Status: {zone.replace('_', ' ')}."
            enrichment_parts.append(hr_line)
        else:
            if language == "no":
                enrichment_parts.append("- Ingen pulsdata tilgjengelig. Ikke oppgi pulstall.")
            else:
                enrichment_parts.append("- No heart rate data available. Do not reference specific HR numbers.")

        if enrichment_parts:
            return base_prompt + "\n" + "\n".join(enrichment_parts)
        return base_prompt
```

Also update `get_question_response()` to pass `phase` and `workout_context` through to `_build_qa_system_prompt()`:

Add `phase: Optional[str] = None` and `workout_context: Optional[dict] = None` to `get_question_response()` signature.

In the method body, where `_build_qa_system_prompt()` is called, pass the new params:

```python
system_prompt = self._build_qa_system_prompt(
    language=language,
    persona=persona,
    context=context,
    user_name=user_name,
    phase=phase,
    workout_context=workout_context,
)
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add brain_router.py tests_phaseb/test_phase_gated_talk.py
git commit -m "feat: enrich QA system prompt with phase hints, timing, HR, interval structure"
```

---

### Task 5: Backend — Pass Phase + Context from coach_talk() to get_question_response()

**Files:**
- Modify: `main.py` (the `get_question_response()` call inside `coach_talk()`, ~line 4184)

**Step 1: Verify the existing call site**

Read `main.py:4183-4191`. The current call is:
```python
coach_text = brain_router.get_question_response(
    prompt_for_router,
    language=language,
    persona=persona,
    context=context,
    user_name=user_name or None,
    timeout_cap_seconds=timeout_budget,
)
```

**Step 2: Add phase and workout_context params**

Change to:
```python
coach_text = brain_router.get_question_response(
    prompt_for_router,
    language=language,
    persona=persona,
    context=context,
    user_name=user_name or None,
    timeout_cap_seconds=timeout_budget,
    phase=phase,
    workout_context=workout_context,
)
```

**Step 3: Run existing tests to verify no regressions**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py tests_phaseb/test_brain_router_workout_talk_prompt.py -v`
Expected: All passed

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: pass phase + workout_context to get_question_response for enriched prompts"
```

---

### Task 6: Backend — Expand collect_workout_context() with New Fields

**Files:**
- Modify: `main.py` (`collect_workout_context()`, ~line 463)
- Modify: `tests_phaseb/test_phase_gated_talk.py`

**Step 1: Write the failing test**

Append to `tests_phaseb/test_phase_gated_talk.py`:

```python
from main import collect_workout_context


def test_collect_workout_context_picks_new_fields():
    """New timing and interval fields are collected from form data."""

    class FakeForm:
        def __init__(self, data):
            self._data = data

        def get(self, key, default=None):
            return self._data.get(key, default)

    form = FakeForm({
        "elapsed_time_s": "600",
        "total_planned_time_s": "1800",
        "time_remaining_s": "1200",
        "workout_mode": "interval",
        "current_set": "2",
        "total_sets": "4",
        "sets_remaining": "2",
        "current_block": "work",
        "block_time_remaining_s": "180",
    })
    ctx = collect_workout_context(payload={}, form=form)
    assert ctx["elapsed_time_s"] == 600
    assert ctx["total_planned_time_s"] == 1800
    assert ctx["time_remaining_s"] == 1200
    assert ctx["workout_mode"] == "interval"
    assert ctx["current_set"] == 2
    assert ctx["total_sets"] == 4
    assert ctx["sets_remaining"] == 2
    assert ctx["current_block"] == "work"
    assert ctx["block_time_remaining_s"] == 180


def test_collect_workout_context_ignores_missing_new_fields():
    ctx = collect_workout_context(payload={"phase": "warmup"}, form=None)
    assert ctx.get("phase") == "warmup"
    assert "elapsed_time_s" not in ctx
    assert "workout_mode" not in ctx
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py::test_collect_workout_context_picks_new_fields -v`
Expected: FAIL — `KeyError: 'elapsed_time_s'`

**Step 3: Add new field collection**

In `collect_workout_context()` in `main.py`, add after the existing `reps_remaining_including_current` line (~503):

```python
    elapsed_time_s = _coerce_int(_pick("elapsed_time_s"))
    total_planned_time_s = _coerce_int(_pick("total_planned_time_s"))
    time_remaining_s = _coerce_int(_pick("time_remaining_s"))
    workout_mode = _pick("workout_mode")
    current_set = _coerce_int(_pick("current_set"))
    total_sets = _coerce_int(_pick("total_sets"))
    sets_remaining = _coerce_int(_pick("sets_remaining"))
    current_block = _pick("current_block")
    block_time_remaining_s = _coerce_int(_pick("block_time_remaining_s"))
```

And in the result dict construction, add after the existing entries:

```python
    if elapsed_time_s is not None:
        result["elapsed_time_s"] = max(0, int(elapsed_time_s))
    if total_planned_time_s is not None:
        result["total_planned_time_s"] = max(0, int(total_planned_time_s))
    if time_remaining_s is not None:
        result["time_remaining_s"] = max(0, int(time_remaining_s))
    if workout_mode:
        result["workout_mode"] = str(workout_mode).strip().lower()
    if current_set is not None:
        result["current_set"] = max(0, int(current_set))
    if total_sets is not None:
        result["total_sets"] = max(0, int(total_sets))
    if sets_remaining is not None:
        result["sets_remaining"] = max(0, int(sets_remaining))
    if current_block:
        result["current_block"] = str(current_block).strip().lower()
    if block_time_remaining_s is not None:
        result["block_time_remaining_s"] = max(0, int(block_time_remaining_s))
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add main.py tests_phaseb/test_phase_gated_talk.py
git commit -m "feat: collect elapsed/total/remaining/interval structure in workout context"
```

---

### Task 7: iOS — Expand WorkoutTalkContext + Send New Fields

**Files:**
- Modify: `TreningsCoach/TreningsCoach/Services/BackendAPIService.swift` (struct + multipart builder)
- Modify: `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift` (`workoutTalkContextPayload()`)
- Modify: `tests_phaseb/test_talk_to_coach_contract.py`

**Step 1: Write the failing Swift contract test**

Append to `tests_phaseb/test_talk_to_coach_contract.py`:

```python
def test_multipart_sends_timing_and_interval_fields() -> None:
    text = _api_service_text()
    assert 'appendField(name: "elapsed_time_s"' in text
    assert 'appendField(name: "total_planned_time_s"' in text
    assert 'appendField(name: "time_remaining_s"' in text
    assert 'appendField(name: "workout_mode"' in text
    assert 'appendField(name: "current_set"' in text
    assert 'appendField(name: "total_sets"' in text
    assert 'appendField(name: "sets_remaining"' in text
    assert 'appendField(name: "current_block"' in text
    assert 'appendField(name: "block_time_remaining_s"' in text


def test_workout_talk_context_has_timing_fields() -> None:
    text = _api_service_text()
    assert "let elapsedTimeS: Int?" in text
    assert "let totalPlannedTimeS: Int?" in text
    assert "let timeRemainingS: Int?" in text
    assert "let workoutMode: String?" in text
    assert "let currentSet: Int?" in text
    assert "let totalSets: Int?" in text
    assert "let setsRemaining: Int?" in text
    assert "let currentBlock: String?" in text
    assert "let blockTimeRemainingS: Int?" in text
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests_phaseb/test_talk_to_coach_contract.py::test_multipart_sends_timing_and_interval_fields -v`
Expected: FAIL — field not found in source text

**Step 3: Modify Swift files**

**BackendAPIService.swift** — expand `WorkoutTalkContext` struct:

```swift
struct WorkoutTalkContext {
    // Existing
    let phase: String?
    let heartRate: Int?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let zoneState: String?
    let timeLeftS: Int?
    let repIndex: Int?
    let repsTotal: Int?
    let repRemainingS: Int?
    let repsRemainingIncludingCurrent: Int?

    // New: global timing
    let elapsedTimeS: Int?
    let totalPlannedTimeS: Int?
    let timeRemainingS: Int?

    // New: interval structure
    let workoutMode: String?
    let currentSet: Int?
    let totalSets: Int?
    let setsRemaining: Int?
    let currentBlock: String?
    let blockTimeRemainingS: Int?
}
```

**BackendAPIService.swift** — in `createTalkMultipartRequest()`, after the existing `reps_remaining_including_current` field, add:

```swift
        if let elapsed = workoutContext.elapsedTimeS {
            appendField(name: "elapsed_time_s", value: "\(elapsed)")
        }
        if let total = workoutContext.totalPlannedTimeS {
            appendField(name: "total_planned_time_s", value: "\(total)")
        }
        if let remaining = workoutContext.timeRemainingS {
            appendField(name: "time_remaining_s", value: "\(remaining)")
        }
        if let mode = workoutContext.workoutMode, !mode.isEmpty {
            appendField(name: "workout_mode", value: mode)
        }
        if let currentSet = workoutContext.currentSet {
            appendField(name: "current_set", value: "\(currentSet)")
        }
        if let totalSets = workoutContext.totalSets {
            appendField(name: "total_sets", value: "\(totalSets)")
        }
        if let setsRemaining = workoutContext.setsRemaining {
            appendField(name: "sets_remaining", value: "\(setsRemaining)")
        }
        if let block = workoutContext.currentBlock, !block.isEmpty {
            appendField(name: "current_block", value: block)
        }
        if let blockRemaining = workoutContext.blockTimeRemainingS {
            appendField(name: "block_time_remaining_s", value: "\(blockRemaining)")
        }
```

**WorkoutViewModel.swift** — update `workoutTalkContextPayload()`:

```swift
    private func workoutTalkContextPayload() -> WorkoutTalkContext {
        let elapsed = Int(elapsedSeconds)
        let total = Int(totalWorkoutDuration)
        let remaining = max(0, total - elapsed)

        // Interval-specific (nil for non-interval)
        let isInterval = selectedWorkoutMode == .interval
        let intervalSet: Int? = isInterval ? (workoutContextSummary?.repIndex).map { $0 + 1 } : nil
        let intervalTotal: Int? = isInterval ? workoutContextSummary?.repsTotal : nil
        let intervalRemaining: Int? = isInterval ? workoutContextSummary?.repsRemainingIncludingCurrent : nil
        let intervalBlock: String? = isInterval ? currentPhase.rawValue : nil
        let intervalBlockRemaining: Int? = isInterval ? workoutContextSummary?.repRemainingS : nil

        return WorkoutTalkContext(
            phase: currentPhase.rawValue,
            heartRate: heartRate ?? 0,
            targetHRLow: targetHRLow,
            targetHRHigh: targetHRHigh,
            zoneState: zoneStatus,
            timeLeftS: workoutContextSummary?.timeLeftS,
            repIndex: workoutContextSummary?.repIndex,
            repsTotal: workoutContextSummary?.repsTotal,
            repRemainingS: workoutContextSummary?.repRemainingS,
            repsRemainingIncludingCurrent: workoutContextSummary?.repsRemainingIncludingCurrent,
            elapsedTimeS: elapsed,
            totalPlannedTimeS: total,
            timeRemainingS: remaining,
            workoutMode: selectedWorkoutMode.rawValue,
            currentSet: intervalSet,
            totalSets: intervalTotal,
            setsRemaining: intervalRemaining,
            currentBlock: intervalBlock,
            blockTimeRemainingS: intervalBlockRemaining
        )
    }
```

Note: The implementer should verify exact property names (`elapsedSeconds`, `totalWorkoutDuration`, `selectedWorkoutMode`) by reading WorkoutViewModel.swift. These are the expected names based on codebase conventions.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests_phaseb/test_talk_to_coach_contract.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add TreningsCoach/TreningsCoach/Services/BackendAPIService.swift TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift tests_phaseb/test_talk_to_coach_contract.py
git commit -m "feat(ios): send timing + interval structure in workout talk context"
```

---

### Task 8: Compile Check + Full Test Suite

**Files:** None (verification only)

**Step 1: Python compile check**

Run: `python3 -m py_compile main.py && python3 -m py_compile config.py && python3 -m py_compile brain_router.py && echo "All compile OK"`
Expected: `All compile OK`

**Step 2: Run all phase-gated talk tests**

Run: `python3 -m pytest tests_phaseb/test_phase_gated_talk.py tests_phaseb/test_talk_to_coach_contract.py tests_phaseb/test_wakeword_capture_error_contract.py tests_phaseb/test_brain_router_workout_talk_prompt.py tests_phaseb/test_audio_pack_manifest_coverage.py -v`
Expected: All passed, no regressions

**Step 3: Run full test suite**

Run: `python3 -m pytest tests_phaseb/ -q`
Expected: All tests pass (ignoring known import failures from missing packages)

**Step 4: Verify no changes to zone_event_motor or /coach/continuous**

Run: `git diff HEAD -- zone_event_motor.py`
Expected: No output (file unchanged)

**Step 5: Final commit with all verification passing**

```bash
git add -A
git commit -m "verify: phase-gated talk — all tests pass, no regressions"
```
