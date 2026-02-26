import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from zone_event_motor import evaluate_zone_tick


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


def test_hr_poor_mode_emits_safe_event_without_zone_claims():
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
    assert result["event_type"] == "hr_poor_enter"
    assert result["should_speak"] is True
    assert "signal" in result["coach_text"].lower()


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
    assert paused_confirmed["event_type"] == "pause_detected"
    assert paused_confirmed["should_speak"] is True
    assert paused_confirmed["movement_state"] == "paused"

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
    assert resumed["event_type"] == "pause_resumed"
    assert resumed["movement_state"] == "moving"


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
    assert paused_confirmed["event_type"] == "pause_detected"
    assert paused_confirmed["movement_state"] == "paused"


def test_below_zone_sustained_triggers_push_when_moving():
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
    assert sustained["event_type"] == "below_zone_push"
    assert sustained["should_speak"] is True


def test_above_zone_sustained_triggers_ease_when_hr_rises():
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
    assert sustained["event_type"] == "above_zone_ease"
    assert sustained["should_speak"] is True


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


def test_phase1_watch_disconnect_notice_emits_once_with_breath_fallback():
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

    # First lost-HR tick starts dwell candidate only.
    evaluate_zone_tick(
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

    # Second lost-HR tick crosses dwell and emits notices.
    switched = evaluate_zone_tick(
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
    switched_events = [item.get("event_type") for item in switched.get("events", []) if isinstance(item, dict)]
    assert "watch_disconnected_notice" in switched_events
    assert switched["sensor_mode"] == "BREATH_FALLBACK"
    assert switched["zone_state"] == "HR_MISSING"
    assert "entered_target" not in switched_events
    assert "exited_target_above" not in switched_events
    assert "exited_target_below" not in switched_events

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=20,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "watch_disconnected_notice" not in later_events


def test_phase1_no_sensors_notice_emits_once_without_fallback_coaching_cues():
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
    evaluate_zone_tick(
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
    switched = evaluate_zone_tick(
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
    switched_events = [item.get("event_type") for item in switched.get("events", []) if isinstance(item, dict)]
    assert "watch_disconnected_notice" in switched_events
    assert "no_sensors_notice" in switched_events
    assert switched["sensor_mode"] == "NO_SENSORS"
    assert switched["event_type"] not in {"below_zone_push", "above_zone_ease", "pause_detected", "pause_resumed"}

    later = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=20,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    later_events = [item.get("event_type") for item in later.get("events", []) if isinstance(item, dict)]
    assert "no_sensors_notice" not in later_events
