import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from zone_event_motor import (
    _motivation_stage_phrase_ids,
    _pick_runtime_phrase_id,
    evaluate_zone_tick,
)


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
    }
    payload.update(overrides)
    return payload


def test_zone2_uses_hrr_when_resting_hr_present():
    result = evaluate_zone_tick(**_base_tick())
    assert result["target_source"] == "hrr"
    assert result["target_hr_low"] == 147
    assert result["target_hr_high"] == 163


def test_zone2_falls_back_to_hrmax_when_resting_hr_missing():
    result = evaluate_zone_tick(**_base_tick(resting_hr=None))
    assert result["target_source"] == "hrmax"
    assert result["target_hr_low"] == 142
    assert result["target_hr_high"] == 162


def test_hr_poor_mode_bootstrap_is_silent_for_signal_loss():
    state = {}
    result = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
        )
    )
    assert result["hr_quality"] == "poor"
    assert result["zone_status"] == "hr_unstable"
    # Startup without HR should not emit hr_signal_lost / hr_poor_enter.
    # We only speak loss cues after a real connected -> disconnected transition.
    events = [item.get("event_type") for item in result.get("events", []) if isinstance(item, dict)]
    assert "hr_signal_lost" not in events
    assert result["event_type"] != "hr_poor_enter"


def test_no_hr_startup_emits_structure_notice_without_sensor_specific_cues():
    state = {}
    result = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    events = [item.get("event_type") for item in result.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in events
    assert "watch_disconnected_notice" not in events
    assert "no_sensors_notice" not in events


def test_watch_starting_suppresses_structure_and_sensor_notices_during_grace():
    state = {}
    result = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=True,
            watch_status="watch_starting",
            breath_signal_quality=None,
        )
    )
    events = [item.get("event_type") for item in result.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" not in events
    assert "watch_disconnected_notice" not in events
    assert "no_sensors_notice" not in events


def test_watch_starting_allows_structure_notice_after_grace_expires() -> None:
    state = {}
    first = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=True,
            watch_status="watch_starting",
            breath_signal_quality=None,
        )
    )
    first_events = [item.get("event_type") for item in first.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" not in first_events

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=60,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=True,
            watch_status="no_live_hr",
            breath_signal_quality=None,
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in later_events


def test_style_matrix_blocks_too_frequent_corrective_cues():
    state = {}

    # First transition into above_zone (needs dwell before event).
    evaluate_zone_tick(**_base_tick(workout_state=state, coaching_style="minimal", elapsed_seconds=0, heart_rate=170))
    first_event = evaluate_zone_tick(**_base_tick(workout_state=state, coaching_style="minimal", elapsed_seconds=9, heart_rate=170))
    assert first_event["event_type"] == "above_zone"
    assert first_event["should_speak"] is True

    # Transition into below_zone soon after; event should be style-rate-limited.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="minimal",
            elapsed_seconds=20,
            heart_rate=118,
            hr_sample_gap_seconds=3.0,
        )
    )
    blocked = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="minimal",
            elapsed_seconds=29,
            heart_rate=118,
            hr_sample_gap_seconds=3.0,
        )
    )
    assert blocked["event_type"] == "below_zone"
    assert blocked["should_speak"] is False
    assert blocked["reason"] == "style_cooldown_any"


def test_zone_decision_is_persona_invariant():
    first_state = {}
    second_state = {}

    first = evaluate_zone_tick(**_base_tick(workout_state=first_state, persona="personal_trainer"))
    second = evaluate_zone_tick(**_base_tick(workout_state=second_state, persona="toxic_mode"))

    assert first["should_speak"] == second["should_speak"]
    assert first["reason"] == second["reason"]
    assert first["zone_status"] == second["zone_status"]
    assert first["score"] == second["score"]


def test_score_switches_to_low_confidence_when_poor_signal_dominates():
    state = {}
    latest = None
    for tick in range(1, 8):
        latest = evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=300 + tick * 10,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
            )
        )

    assert latest is not None
    assert latest["score_confidence"] == "low"
    assert latest["time_in_target_pct"] is None


def test_main_started_does_not_reappear_late_if_state_is_recreated():
    state = {}

    late_tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=149,
            workout_mode="intervals",
            phase="intense",
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )

    events = [item.get("event_type") for item in late_tick.get("events", []) if isinstance(item, dict)]
    assert "main_started" not in events
    assert late_tick["event_type"] != "main_started"
    assert state["zone_engine"]["main_started_emitted"] is True


def test_runtime_phrase_picker_rotates_main_started_variants():
    state = {}

    first = _pick_runtime_phrase_id(state=state, event_type="main_started", phase="main")
    second = _pick_runtime_phrase_id(state=state, event_type="main_started", phase="main")

    assert first in {"zone.main_started.1", "zone.main_started.2"}
    assert second in {"zone.main_started.1", "zone.main_started.2"}
    assert first != second


def test_runtime_phrase_picker_rotates_in_zone_variants_without_immediate_repeat():
    state = {}

    picks = [
        _pick_runtime_phrase_id(state=state, event_type="entered_target", phase="main")
        for _ in range(4)
    ]

    assert all(
        pick in {
            "zone.in_zone.default.1",
            "zone.in_zone.default.2",
            "zone.in_zone.default.3",
        }
        for pick in picks
    )
    assert picks[0] != picks[1]


def test_motivation_stage_phrase_ids_follow_active_runtime_review_variants():
    assert _motivation_stage_phrase_ids("intervals", 1) == [
        "interval.motivate.s1.1",
        "interval.motivate.s1.2",
    ]
    assert _motivation_stage_phrase_ids("easy_run", 2) == [
        "easy_run.motivate.s2.1",
        "easy_run.motivate.s2.2",
    ]


def test_movement_pause_and_resume_events_after_dwell():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=0,
            heart_rate=150,
            hr_sample_gap_seconds=4.0,
            movement_score=0.8,
            cadence_spm=120.0,
            movement_source="cadence",
        )
    )

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=4,
            heart_rate=150,
            hr_sample_gap_seconds=4.0,
            movement_score=0.05,
            cadence_spm=35.0,
            movement_source="cadence",
        )
    )

    paused = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=13,
            heart_rate=147,
            hr_sample_gap_seconds=5.0,
            movement_score=0.05,
            cadence_spm=35.0,
            movement_source="cadence",
        )
    )
    assert paused["event_type"] is None

    paused_confirmed = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=22,
            heart_rate=145,
            hr_sample_gap_seconds=4.0,
            movement_score=0.05,
            cadence_spm=35.0,
            movement_source="cadence",
        )
    )
    assert paused_confirmed["event_type"] is None
    assert paused_confirmed["should_speak"] is False
    assert paused_confirmed["movement_state"] == "paused"
    paused_events = [item.get("event_type") for item in paused_confirmed.get("events", []) if isinstance(item, dict)]
    assert "pause_detected" not in paused_events

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=50,
            heart_rate=146,
            hr_sample_gap_seconds=28.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    resumed = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=72,
            heart_rate=147,
            hr_sample_gap_seconds=22.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    # Motivation events (priority 55) can fire before max_silence (priority 10)
    # when user is in-zone during easy_run. Both are valid silence breakers.
    assert resumed["event_type"] in ("max_silence_override", "easy_run_in_target_sustained")
    assert resumed["movement_state"] == "moving"
    resumed_events = [item.get("event_type") for item in resumed.get("events", []) if isinstance(item, dict)]
    assert "pause_resumed" not in resumed_events


def test_pause_requires_hr_fall_when_hr_signal_is_good():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=150,
            hr_sample_gap_seconds=5.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )

    # Low movement alone should not trigger pause while HR is stable.
    no_pause = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=5,
            heart_rate=150,
            hr_sample_gap_seconds=5.0,
            movement_score=0.05,
            cadence_spm=30.0,
            movement_source="cadence",
        )
    )
    assert no_pause["movement_state"] != "paused"
    assert no_pause["event_type"] is None

    # After dwell + falling HR, pause is confirmed.
    paused = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=14,
            heart_rate=147,
            hr_sample_gap_seconds=5.0,
            movement_score=0.05,
            cadence_spm=30.0,
            movement_source="cadence",
        )
    )
    assert paused["event_type"] is None

    paused_confirmed = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=23,
            heart_rate=145,
            hr_sample_gap_seconds=9.0,
            movement_score=0.05,
            cadence_spm=30.0,
            movement_source="cadence",
        )
    )
    assert paused_confirmed["event_type"] is None
    assert paused_confirmed["movement_state"] == "paused"
    paused_events = [item.get("event_type") for item in paused_confirmed.get("events", []) if isinstance(item, dict)]
    assert "pause_detected" not in paused_events


def test_below_zone_sustained_does_not_emit_legacy_push_fallback():
    state = {}

    # Build movement confidence and enter below-zone state.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=0,
            heart_rate=118,
            hr_sample_gap_seconds=2.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    first = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=9,
            heart_rate=118,
            hr_sample_gap_seconds=2.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    assert first["event_type"] == "below_zone"

    sustained = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=70,
            heart_rate=119,
            hr_sample_gap_seconds=3.0,
            movement_score=0.72,
            cadence_spm=132.0,
            movement_source="cadence",
        )
    )
    assert sustained["event_type"] == "max_silence_override"
    assert sustained["should_speak"] is True
    sustained_events = [item.get("event_type") for item in sustained.get("events", []) if isinstance(item, dict)]
    assert "below_zone_push" not in sustained_events


def test_above_zone_sustained_does_not_emit_legacy_ease_fallback():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=0,
            heart_rate=170,
            hr_sample_gap_seconds=2.0,
            movement_score=0.6,
            cadence_spm=120.0,
            movement_source="cadence",
        )
    )
    first = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=9,
            heart_rate=171,
            hr_sample_gap_seconds=2.0,
            movement_score=0.6,
            cadence_spm=120.0,
            movement_source="cadence",
        )
    )
    assert first["event_type"] == "above_zone"

    sustained = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            coaching_style="normal",
            elapsed_seconds=70,
            heart_rate=176,
            hr_sample_gap_seconds=2.0,
            movement_score=0.6,
            cadence_spm=120.0,
            movement_source="cadence",
        )
    )
    assert sustained["event_type"] == "max_silence_override"
    assert sustained["should_speak"] is True
    sustained_events = [item.get("event_type") for item in sustained.get("events", []) if isinstance(item, dict)]
    assert "above_zone_ease" not in sustained_events


def test_max_silence_override_emits_canonical_event():
    state = {}
    first = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            phase="intense",
            heart_rate=150,
            hr_quality="good",
        )
    )
    assert first["event_type"] == "main_started"
    assert first["should_speak"] is True

    quiet = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=10,
            phase="intense",
            heart_rate=151,
            hr_quality="good",
        )
    )
    assert quiet["should_speak"] is False

    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=70,
            phase="intense",
            heart_rate=150,
            hr_quality="good",
        )
    )
    assert forced["should_speak"] is True
    # Motivation events (priority 55) can fire before max_silence (priority 10)
    # when user is in-zone during easy_run. Both are valid silence breakers.
    _silence_breakers = {"max_silence_override", "easy_run_in_target_sustained"}
    assert forced["event_type"] in _silence_breakers
    assert forced["reason"] in _silence_breakers
    forced_events = [item.get("event_type") for item in forced.get("events", []) if isinstance(item, dict)]
    assert any(e in _silence_breakers for e in forced_events)


def test_recovery_seconds_tracked_when_returning_in_zone():
    state = {}

    # Enter above-zone first (requires dwell to confirm).
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=170,
            hr_sample_gap_seconds=2.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    above = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=170,
            hr_sample_gap_seconds=2.0,
            movement_score=0.7,
            cadence_spm=130.0,
            movement_source="cadence",
        )
    )
    assert above["event_type"] == "above_zone"

    # Move back in zone and wait dwell for recovery transition.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=30,
            heart_rate=150,
            hr_sample_gap_seconds=21.0,
            movement_score=0.65,
            cadence_spm=124.0,
            movement_source="cadence",
        )
    )
    recovered = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=40,
            heart_rate=151,
            hr_sample_gap_seconds=10.0,
            movement_score=0.65,
            cadence_spm=124.0,
            movement_source="cadence",
        )
    )

    assert recovered["event_type"] == "in_zone_recovered"
    assert recovered["recovery_seconds"] is not None
    assert recovered["recovery_seconds"] > 0
    assert recovered["recovery_avg_seconds"] is not None
    assert recovered["recovery_samples_count"] >= 1


def test_phase1_hr_structure_notice_emits_once_with_breath_fallback():
    state = {}

    # Build breath reliability while HR is valid/full.
    for second in range(0, 6):
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=145,
                hr_quality="good",
                watch_connected=True,
                watch_status="connected",
                breath_signal_quality=0.8,
            )
        )

    # First lost-HR tick starts structure coaching and announces the mode switch.
    switched = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
        )
    )
    switched_events = [item.get("event_type") for item in switched.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in switched_events
    assert "watch_disconnected_notice" not in switched_events
    assert switched["sensor_mode"] == "FULL_HR"
    assert switched["zone_state"] == "HR_MISSING"
    assert "entered_target" not in switched_events
    assert "exited_target_above" not in switched_events
    assert "exited_target_below" not in switched_events

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=13,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" not in later_events
    assert later["sensor_mode"] == "BREATH_FALLBACK"


def test_phase1_no_hr_structure_notice_emits_once_without_sensor_specific_cues():
    state = {}

    # Start in full-HR mode.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )

    # Move to no-sensors via stable HR loss + missing breath reliability.
    switched = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    switched_events = [item.get("event_type") for item in switched.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in switched_events
    assert "watch_disconnected_notice" not in switched_events
    assert "no_sensors_notice" not in switched_events
    assert switched["sensor_mode"] == "FULL_HR"
    assert switched["event_type"] not in {"below_zone_push", "above_zone_ease", "pause_detected", "pause_resumed"}

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=13,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" not in later_events
    assert later["sensor_mode"] == "NO_SENSORS"


def test_phase1_movement_available_keeps_fusion_mode_when_hr_lost_and_breath_unreliable():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
            movement_score=0.62,
            cadence_spm=112.0,
            movement_source="cadence",
        )
    )

    switched = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=0.58,
            cadence_spm=108.0,
            movement_source="cadence",
        )
    )
    switched_events = [item.get("event_type") for item in switched.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in switched_events
    assert "watch_disconnected_notice" not in switched_events
    assert "no_sensors_notice" not in switched_events

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=13,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=0.58,
            cadence_spm=108.0,
            movement_source="cadence",
        )
    )
    assert later["sensor_mode"] == "NO_SENSORS"
    assert later["sensor_fusion_mode"] == "MOVEMENT_ONLY"
    assert later["movement_available"] is True


def test_hr_structure_notice_defers_when_loss_matches_phase_transition():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=595,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
            breath_signal_quality=None,
        )
    )

    transition_tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=600,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    transition_events = [item.get("event_type") for item in transition_tick.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in transition_events
    assert transition_tick["event_type"] == "interval_countdown_start"

    deferred_notice = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=626,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert deferred_notice["event_type"] == "hr_structure_mode_notice"


def test_hr_structure_notice_resets_after_hr_restores():
    state = {}

    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=145))
    first_loss = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert "hr_structure_mode_notice" in [item.get("event_type") for item in first_loss.get("events", []) if isinstance(item, dict)]

    restored = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=19,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
            breath_signal_quality=None,
        )
    )
    restored_events = [item.get("event_type") for item in restored.get("events", []) if isinstance(item, dict)]
    assert "hr_signal_restored" in restored_events

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=34,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    second_loss = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=38,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    second_loss_events = [item.get("event_type") for item in second_loss.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" in second_loss_events


def test_hr_structure_notice_does_not_rearm_without_real_hr_restore():
    state = {
        "zone_engine": {
            "instruction_mode": "structure_driven",
            "structure_mode_notice_pending": False,
            "structure_mode_notice_sent": True,
            "hr_signal_state": "lost",
            "hr_valid_streak_seconds": 0.0,
            "hr_invalid_streak_seconds": 10.0,
            "main_started_emitted": True,
            "canonical_phase": "main",
            "phase_id": 1,
        }
    }

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=42,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )

    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "hr_structure_mode_notice" not in events


def test_phase1_no_sensors_mode_persists_when_movement_signal_later_disappears():
    state = {}

    # Enter NO_SENSORS with movement still available.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
            movement_score=0.62,
            cadence_spm=112.0,
            movement_source="cadence",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=13,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=0.58,
            cadence_spm=108.0,
            movement_source="cadence",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=17,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=0.58,
            cadence_spm=108.0,
            movement_source="cadence",
        )
    )
    mid = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=19,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=0.58,
            cadence_spm=108.0,
            movement_source="cadence",
        )
    )
    assert mid["sensor_mode"] == "NO_SENSORS"
    assert mid["sensor_fusion_mode"] == "MOVEMENT_ONLY"

    # Remove movement too; mode stays NO_SENSORS but fusion drops to TIMING_ONLY.
    no_sensors = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=21,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=None,
            cadence_spm=None,
            movement_source="none",
        )
    )
    no_sensors = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=24,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            movement_score=None,
            cadence_spm=None,
            movement_source="none",
        )
    )
    no_sensor_events = [item.get("event_type") for item in no_sensors.get("events", []) if isinstance(item, dict)]
    assert no_sensors["sensor_mode"] == "NO_SENSORS"
    assert no_sensors["sensor_fusion_mode"] == "TIMING_ONLY"
    assert no_sensors["movement_available"] is False
    assert "no_sensors_notice" not in no_sensor_events


def test_interval_warmup_end_emits_countdown_sequence():
    state = {}

    # 4x4 template warmup is 600s.
    tick_30 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=570,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_30 = [item.get("event_type") for item in tick_30.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in events_30

    tick_15 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=585,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_15 = [item.get("event_type") for item in tick_15.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_15" in events_15

    tick_5 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=595,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_5 = [item.get("event_type") for item in tick_5.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_5" in events_5

    tick_start = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=600,
            heart_rate=148,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_start = [item.get("event_type") for item in tick_start.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_start" in events_start


def test_easy_run_warmup_end_emits_countdown_sequence():
    state = {}

    tick_30 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=90,
            heart_rate=135,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_30 = [item.get("event_type") for item in tick_30.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in events_30

    tick_15 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=105,
            heart_rate=136,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_15 = [item.get("event_type") for item in tick_15.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_15" in events_15

    tick_5 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=115,
            heart_rate=136,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_5 = [item.get("event_type") for item in tick_5.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_5" in events_5

    tick_start = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="intense",
            warmup_seconds=120,
            elapsed_seconds=120,
            heart_rate=144,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_start = [item.get("event_type") for item in tick_start.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_start" in events_start


def test_easy_run_warmup_countdown_handles_coarse_tick_budget():
    state = {}

    # Remaining 50s: no warmup countdown yet.
    first = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=70,
            heart_rate=135,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    first_events = [item.get("event_type") for item in first.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" not in first_events
    assert "interval_countdown_15" not in first_events

    # Coarse jump to remaining 14s should still emit both 30 and 15 once.
    second = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=106,
            heart_rate=136,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    second_events = [item.get("event_type") for item in second.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in second_events
    assert "interval_countdown_15" in second_events
    assert second_events.count("interval_countdown_30") == 1
    assert second_events.count("interval_countdown_15") == 1

    third = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=120,
            elapsed_seconds=118,
            heart_rate=136,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    third_events = [item.get("event_type") for item in third.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_5" in third_events


def test_easy_run_warmup_countdown_uses_workout_state_warmup_seconds_without_kwarg():
    state = {"warmup_remaining_s": 30}

    tick_30 = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            elapsed_seconds=90,
            heart_rate=135,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events_30 = [item.get("event_type") for item in tick_30.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in events_30


def test_warmup_halfway_is_suppressed_when_it_collides_with_30_seconds_left():
    state = {}

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            warmup_seconds=60,
            elapsed_seconds=30,
            heart_rate=135,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in events
    assert "interval_countdown_halfway" not in events


def test_interval_work_halfway_emits_once_for_long_work_segments():
    state = {}

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=720,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_halfway" in events

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=730,
            heart_rate=146,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_halfway" not in later_events


def test_easy_run_main_halfway_emits_once_for_timed_main_segment():
    state = {
        "plan_warmup_s": 0,
        "plan_main_s": 3600,
        "plan_cooldown_s": 0,
    }

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="intense",
            elapsed_seconds=1800,
            heart_rate=140,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_halfway" in events


def test_interval_session_halfway_emits_dynamic_progress_text():
    state = {
        "plan_warmup_s": 0,
        "plan_interval_work_s": 240,
        "plan_interval_recovery_s": 180,
        "plan_interval_repeats": 4,
        "plan_cooldown_s": 0,
    }

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=840,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_session_halfway" in events
    assert tick["event_type"] == "interval_countdown_session_halfway"
    assert tick["phrase_id"] == "zone.countdown.session_halfway.dynamic"
    assert tick["coach_text"] == "You are halfway through the workout"


def test_countdown_fired_keys_are_namespaced_by_phase_kind():
    state = {
        "phase_id": 7,
        "canonical_phase": "warmup",
        "countdown_fired_map": {"7:recovery:countdown_30": True},
        "warmup_remaining_s": 30,
    }

    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            elapsed_seconds=90,
            heart_rate=135,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    events = [item.get("event_type") for item in tick.get("events", []) if isinstance(item, dict)]
    assert "interval_countdown_30" in events
