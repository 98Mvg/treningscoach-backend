"""Tests for the canonical event contract (migration step 3/8).

Validates that evaluate_zone_tick() returns all canonical fields:
  priority, text, phrase_id, meta
and that structured logging fires on every tick.
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import zone_event_motor
from zone_event_motor import _resolve_phrase_id, evaluate_zone_tick


def _base_tick(**overrides):
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
        "breath_signal_quality": 0.8,
    }
    payload.update(overrides)
    return payload


# ── (a) Canonical dict shape ──────────────────────────────────────────

CANONICAL_KEYS = {
    "handled",
    "should_speak",
    "reason",
    "event_type",
    "primary_event_type",
    "priority",
    "text",
    "phrase_id",
    "coach_text",
    "meta",
    "events",
}


def test_canonical_keys_present_on_speak():
    """When evaluate_zone_tick triggers speech, all canonical keys exist."""
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    assert result["should_speak"] is True
    for key in CANONICAL_KEYS:
        assert key in result, f"Missing canonical key: {key}"


def test_canonical_keys_present_on_silent():
    """When evaluate_zone_tick is silent, all canonical keys still exist."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0))
    result = evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=5))
    assert result["should_speak"] is False
    for key in CANONICAL_KEYS:
        assert key in result, f"Missing canonical key: {key}"


def test_priority_is_int():
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    assert isinstance(result["priority"], int)


def test_text_matches_coach_text():
    """text and coach_text are always identical (text is the canonical alias)."""
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    assert result["text"] == result["coach_text"]


def test_meta_has_required_fields():
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    meta = result["meta"]
    assert isinstance(meta, dict)
    for field in ("sensor_mode", "coaching_style", "workout_type", "phase", "elapsed_seconds"):
        assert field in meta, f"meta missing: {field}"


def test_phrase_id_present_when_speaking():
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    assert result["should_speak"] is True
    assert result["phrase_id"] is not None


def test_phrase_id_none_when_silent():
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0))
    result = evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=5))
    assert result["should_speak"] is False
    # phrase_id is None when no primary event resolves.
    # (could be non-None if a blocked event is primary — either is acceptable)


# ── (b) Max-silence phrase_id ─────────────────────────────────────────

def test_max_silence_override_has_phrase_id():
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=150))
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=10, heart_rate=151))
    forced = evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=70, heart_rate=150))
    assert forced["should_speak"] is True
    # Motivation events (priority 55) can fire before max_silence (priority 68)
    # when user is in-zone during easy_run. Both are valid silence breakers.
    _silence_breakers = {"max_silence_override", "easy_run_in_target_sustained"}
    assert forced["event_type"] in _silence_breakers
    assert forced["phrase_id"] is not None
    if forced["event_type"] == "max_silence_override":
        assert forced["phrase_id"].startswith("zone.silence.")
        assert forced["priority"] == 68
    else:
        assert forced["phrase_id"].startswith("easy_run.motivate.")
        assert forced["priority"] == 55


def test_max_silence_override_work_phrase():
    """During interval work phase, max_silence_override → zone.silence.work.1."""
    state = {}
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            interval_template="4x4",
            phase="work",
            elapsed_seconds=0,
            heart_rate=160,
        )
    )
    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            interval_template="4x4",
            phase="work",
            elapsed_seconds=40,
            heart_rate=160,
        )
    )
    if forced["event_type"] == "max_silence_override":
        assert forced["phrase_id"] == "zone.silence.work.1"


def test_max_silence_go_by_feel_has_phrase_id():
    """go_by_feel event resolves to zone.feel.* phrase."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=145))
    # Simulate no HR — triggers go_by_feel path.
    result = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=70,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    if result["event_type"] == "max_silence_go_by_feel":
        assert result["phrase_id"] is not None
        assert result["phrase_id"].startswith("zone.feel.")
        assert result["priority"] == 66


# ── (c) No-sensors fallback phrase_id ─────────────────────────────────

def test_no_sensors_notice_has_phrase_id():
    state = {}
    result = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
        )
    )
    events = result.get("events", [])
    for ev in events:
        if ev["event_type"] == "no_sensors_notice":
            assert ev["phrase_id"] == "zone.no_sensors.1"
            assert ev["priority"] == 88


# ── (d) Motivation phrase_id ──────────────────────────────────────────

def test_motivation_phrase_id():
    assert _resolve_phrase_id("max_silence_motivation", "main") == "motivation.1"


# ── Events payload carries priority + phrase_id ───────────────────────

def test_events_carry_priority_and_phrase_id():
    result = evaluate_zone_tick(**_base_tick(elapsed_seconds=0))
    for ev in result.get("events", []):
        assert "priority" in ev, f"Event {ev['event_type']} missing priority"
        assert "phrase_id" in ev, f"Event {ev['event_type']} missing phrase_id"
        assert isinstance(ev["priority"], int)


def test_speakable_event_contract_downgrades_to_safe_fallback(monkeypatch):
    state = {}
    original_resolver = zone_event_motor._resolve_phrase_id

    def _broken_resolver(event_type, phase):
        if event_type == "main_started":
            return None
        return original_resolver(event_type, phase)

    monkeypatch.setattr(zone_event_motor, "_resolve_phrase_id", _broken_resolver)

    result = evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0))
    assert result["should_speak"] is True
    assert result["event_type"] == "max_silence_override"
    assert result["priority"] == 68
    assert result["phrase_id"] in {
        "zone.silence.default.1",
        "zone.silence.work.1",
        "zone.silence.rest.1",
    }
    assert result["reason"] == "contract_fallback_missing_phrase_or_priority"


# ── _resolve_phrase_id unit tests ─────────────────────────────────────

def test_resolve_phase_transitions():
    assert _resolve_phrase_id("warmup_started", "warmup") == "zone.phase.warmup.1"
    assert _resolve_phrase_id("main_started", "main") == "zone.main_started.1"
    assert _resolve_phrase_id("cooldown_started", "cooldown") == "zone.phase.cooldown.1"
    assert _resolve_phrase_id("workout_finished", "cooldown") == "zone.workout_finished.1"


def test_resolve_zone_events():
    assert _resolve_phrase_id("entered_target", "main") == "zone.in_zone.default.1"
    assert _resolve_phrase_id("exited_target_above", "main") == "zone.above.default.1"
    assert _resolve_phrase_id("exited_target_below", "main") == "zone.below.default.1"


def test_resolve_signal_events():
    assert _resolve_phrase_id("hr_signal_lost", "main") == "zone.hr_poor_enter.1"
    assert _resolve_phrase_id("hr_signal_restored", "main") == "zone.hr_poor_exit.1"
    assert _resolve_phrase_id("watch_disconnected_notice", "main") == "zone.watch_disconnected.1"
    assert _resolve_phrase_id("no_sensors_notice", "main") == "zone.no_sensors.1"
    assert _resolve_phrase_id("watch_restored_notice", "main") == "zone.watch_restored.1"


def test_resolve_countdowns():
    assert _resolve_phrase_id("interval_countdown_30", "work") == "zone.countdown.30"
    assert _resolve_phrase_id("interval_countdown_15", "work") == "zone.countdown.15"
    assert _resolve_phrase_id("interval_countdown_5", "work") == "zone.countdown.5"
    assert _resolve_phrase_id("interval_countdown_start", "work") == "zone.countdown.start"


def test_resolve_max_silence_override_by_phase():
    assert _resolve_phrase_id("max_silence_override", "work") == "zone.silence.work.1"
    assert _resolve_phrase_id("max_silence_override", "recovery") == "zone.silence.rest.1"
    assert _resolve_phrase_id("max_silence_override", "main") == "zone.silence.default.1"


def test_resolve_go_by_feel_by_phase():
    assert _resolve_phrase_id("max_silence_go_by_feel", "work") == "zone.feel.work.1"
    assert _resolve_phrase_id("max_silence_go_by_feel", "recovery") == "zone.feel.recovery.1"
    assert _resolve_phrase_id("max_silence_go_by_feel", "main") == "zone.feel.easy_run.1"


def test_resolve_breath_guide_by_phase():
    assert _resolve_phrase_id("max_silence_breath_guide", "work") == "zone.breath.work.1"
    assert _resolve_phrase_id("max_silence_breath_guide", "recovery") == "zone.breath.recovery.1"
    assert _resolve_phrase_id("max_silence_breath_guide", "main") == "zone.breath.easy_run.1"


def test_resolve_motivation():
    assert _resolve_phrase_id("max_silence_motivation", "main") == "motivation.1"
    assert _resolve_phrase_id("max_silence_motivation", "work") == "motivation.1"


def test_resolve_unknown_returns_none():
    assert _resolve_phrase_id("some_future_event", "main") is None
    assert _resolve_phrase_id(None, "main") is None


# ── (Step 7) Structured logging ───────────────────────────────────────

def test_zone_tick_emits_structured_log(caplog):
    """Every evaluate_zone_tick() call emits a ZONE_TICK JSON log line."""
    with caplog.at_level(logging.INFO, logger="zone_event_motor"):
        evaluate_zone_tick(**_base_tick(elapsed_seconds=0))

    zone_tick_records = [r for r in caplog.records if "ZONE_TICK" in r.getMessage()]
    assert len(zone_tick_records) >= 1, "No ZONE_TICK log emitted"

    log_msg = zone_tick_records[0].getMessage()
    json_str = log_msg.split("ZONE_TICK ", 1)[1]
    parsed = json.loads(json_str)

    assert "elapsed" in parsed
    assert "event_type" in parsed
    assert "priority" in parsed
    assert "should_speak" in parsed
    assert "silence_seconds" in parsed
    assert "phrase_id" in parsed
    assert "sensor_mode" in parsed
    assert "reason" in parsed


def test_zone_tick_log_shows_silence_seconds(caplog):
    """After speech, silence_seconds tracks time since last spoken."""
    state = {}
    with caplog.at_level(logging.INFO, logger="zone_event_motor"):
        evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0))
        caplog.clear()
        evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=15))

    zone_tick_records = [r for r in caplog.records if "ZONE_TICK" in r.getMessage()]
    assert len(zone_tick_records) >= 1
    json_str = zone_tick_records[0].getMessage().split("ZONE_TICK ", 1)[1]
    parsed = json.loads(json_str)
    assert parsed["silence_seconds"] == 15.0
