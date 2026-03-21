import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from tts_phrase_catalog import PHRASE_CATALOG
from workout_cue_catalog import is_active_deterministic_workout_phrase_id
from zone_event_motor import (
    _allow_motivation_event,
    _compute_max_silence_seconds,
    _event_group,
    _event_priority,
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
        "breath_signal_quality": 0.8,
    }
    payload.update(overrides)
    return payload


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


def test_legacy_go_by_feel_family_still_exists_in_catalog():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.easy_run.1" in ids
    assert "zone.feel.easy_run.2" in ids
    assert "zone.feel.easy_run.3" in ids


def test_legacy_go_by_feel_work_family_still_exists_in_catalog():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.work.1" in ids
    assert "zone.feel.work.2" in ids


def test_legacy_go_by_feel_recovery_family_still_exists_in_catalog():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.recovery.1" in ids
    assert "zone.feel.recovery.2" in ids


def test_legacy_breath_family_still_exists_in_catalog():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.breath.easy_run.1" in ids
    assert "zone.breath.easy_run.2" in ids
    assert "zone.breath.work.1" in ids
    assert "zone.breath.recovery.1" in ids


def test_legacy_go_by_feel_and_breath_are_not_active_runtime_ids():
    for phrase in PHRASE_CATALOG:
        phrase_id = phrase["id"]
        if phrase_id.startswith(("zone.feel.", "zone.breath.")):
            assert is_active_deterministic_workout_phrase_id(phrase_id) is False


def test_max_silence_intervals_work():
    assert _compute_max_silence_seconds("intervals", "work", 5, False, config) == 30


def test_max_silence_intervals_recovery():
    assert _compute_max_silence_seconds("intervals", "recovery", 5, False, config) == 45


def test_max_silence_easy_run_base():
    assert _compute_max_silence_seconds("easy_run", "main", 0, False, config) == 60


def test_max_silence_easy_run_20min():
    assert _compute_max_silence_seconds("easy_run", "main", 20, False, config) == 75


def test_max_silence_easy_run_30min():
    assert _compute_max_silence_seconds("easy_run", "main", 30, False, config) == 90


def test_max_silence_easy_run_50min_cap():
    assert _compute_max_silence_seconds("easy_run", "main", 50, False, config) == 120


def test_max_silence_easy_run_hr_missing_multiplier():
    assert _compute_max_silence_seconds("easy_run", "main", 0, True, config) == 90


def test_max_silence_intervals_hr_missing_unchanged():
    assert _compute_max_silence_seconds("intervals", "work", 5, True, config) == 30
    assert _compute_max_silence_seconds("intervals", "recovery", 5, True, config) == 45


def test_motivation_allowed_when_no_recent_high_priority():
    state = {}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True


def test_motivation_blocked_by_barrier_easy_run():
    state = {"last_high_priority_spoken_elapsed": 280.0}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is False


def test_motivation_allowed_after_barrier_easy_run():
    state = {"last_high_priority_spoken_elapsed": 250.0}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True


def test_motivation_blocked_by_min_spacing_easy_run():
    state = {"last_motivation_spoken_elapsed": 200.0}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is False


def test_motivation_allowed_after_min_spacing_easy_run():
    state = {"last_motivation_spoken_elapsed": 170.0}
    assert _allow_motivation_event(state=state, workout_type="easy_run", elapsed_seconds=300, config_module=config) is True


def test_tier_a_highest_priority():
    assert _event_priority("interval_countdown_start") > _event_priority("main_started")
    assert _event_priority("hr_signal_lost") > _event_priority("main_started")


def test_tier_b_above_tier_c():
    assert _event_priority("main_started") > _event_priority("exited_target_above")
    assert _event_priority("cooldown_started") > _event_priority("entered_target")


def test_max_silence_motivation_below_instruction_cues():
    assert _event_priority("max_silence_motivation") < _event_priority("max_silence_go_by_feel")
    assert _event_priority("max_silence_motivation") < _event_priority("max_silence_breath_guide")


def test_event_group_motivation():
    assert _event_group("max_silence_motivation") == "motivation"


def test_event_group_go_by_feel():
    assert _event_group("max_silence_go_by_feel") == "instruction"


def test_event_group_breath_guide():
    assert _event_group("max_silence_breath_guide") == "instruction"


def test_max_silence_uses_motivation_when_no_hr_and_no_breath():
    state = {}

    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=145))
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
    evaluate_zone_tick(
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

    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert forced["event_type"] == "max_silence_motivation"
    assert forced["phrase_id"].startswith("easy_run.motivate.")
    assert forced["should_speak"] is True


def test_max_silence_uses_motivation_when_hr_missing_breath_reliable():
    state = {}

    # Build stable, reliable breath signal first.
    for second in [0, 5, 10, 15, 20, 25, 30]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=145,
                breath_signal_quality=0.8,
            )
        )

    # Then lose HR while breath remains reliable.
    for second in [40, 45]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
            )
        )

    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=136,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
        )
    )
    assert forced["event_type"] == "max_silence_motivation"
    assert forced["phrase_id"].startswith("easy_run.motivate.")
    assert forced["should_speak"] is True


def test_max_silence_uses_motivation_when_targets_not_enforced():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
                elapsed_seconds=0,
                heart_rate=145,
                hr_max=None,
                resting_hr=None,
                age=None,
                breath_signal_quality=None,
            )
        )
    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=70,
            heart_rate=145,
            hr_max=None,
            resting_hr=None,
            age=None,
            breath_signal_quality=None,
        )
    )
    assert forced["event_type"] == "max_silence_motivation"
    assert forced["should_speak"] is True


def test_max_silence_uses_motivation_when_hr_missing_without_targets():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            hr_max=None,
            resting_hr=None,
            age=None,
            breath_signal_quality=None,
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=9,
            heart_rate=None,
            hr_quality="poor",
            hr_max=None,
            resting_hr=None,
            age=None,
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )

    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            hr_max=None,
            resting_hr=None,
            age=None,
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert forced["event_type"] == "max_silence_motivation"
    assert forced["phrase_id"].startswith("easy_run.motivate.")
    assert forced["should_speak"] is True


def test_structure_driven_easy_run_rotates_motivation_without_late_structure_entry():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=None,
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=None,
            )
        )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["phrase_id"].startswith("easy_run.motivate.")

    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=240,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert second_forced["event_type"] == "max_silence_motivation"
    assert second_forced["phrase_id"].startswith("easy_run.motivate.")
    assert second_forced["phrase_id"] != first_forced["phrase_id"]
    assert second_forced["should_speak"] is True


def test_structure_driven_easy_run_uses_go_by_feel_tone_after_startup_motivation():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=None,
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=None,
            )
        )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"

    engine_state = state.setdefault("zone_engine", {})
    engine_state["last_motivation_spoken_elapsed"] = 200.0
    engine_state["last_easy_run_motivation_elapsed"] = 200.0
    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=240,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
        )
    )
    assert second_forced["event_type"] == "max_silence_go_by_feel"
    assert second_forced["phrase_id"] in {
        "zone.silence.work.1",
        "zone.silence.default.1",
    }
    assert second_forced["should_speak"] is True


def test_structure_driven_easy_run_medium_breath_confidence_keeps_phase_neutral_tone():
    state = {}
    medium_conf_breath_summary = {
        "cue_interval_seconds": 20,
        "cue_due": False,
        "quality_sample_count": 8,
        "quality_median": 0.62,
        "quality_reliable": True,
    }

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=0.8,
            breath_summary=medium_conf_breath_summary,
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
                breath_summary=medium_conf_breath_summary,
            )
        )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=medium_conf_breath_summary,
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["phrase_id"] in {
        "easy_run.motivate.s3.1",
        "easy_run.motivate.s3.2",
    }

    engine_state = state.setdefault("zone_engine", {})
    engine_state["last_motivation_spoken_elapsed"] = 200.0
    engine_state["last_easy_run_motivation_elapsed"] = 200.0
    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=240,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=medium_conf_breath_summary,
        )
    )
    assert second_forced["event_type"] == "max_silence_go_by_feel"
    assert second_forced["phrase_id"] in {
        "zone.silence.rest.1",
        "zone.silence.default.1",
    }
    assert second_forced["should_speak"] is True


def test_structure_driven_easy_run_high_confidence_heavy_breath_uses_breath_tone():
    state = {}
    high_conf_breath_summary = {
        "cue_interval_seconds": 20,
        "cue_due": False,
        "quality_sample_count": 8,
        "quality_median": 0.85,
        "quality_reliable": True,
    }

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
                breath_summary=high_conf_breath_summary,
                breath_intensity="intense",
            )
        )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=110,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["phrase_id"] in {
        "easy_run.motivate.s1.1",
        "easy_run.motivate.s1.2",
        "easy_run.motivate.s4.1",
    }

    engine_state = state.setdefault("zone_engine", {})
    engine_state["last_motivation_spoken_elapsed"] = 200.0
    engine_state["last_easy_run_motivation_elapsed"] = 200.0
    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=240,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
        )
    )
    assert second_forced["event_type"] == "max_silence_breath_guide"
    assert second_forced["phrase_id"] in {
        "zone.silence.rest.1",
        "zone.silence.default.1",
    }
    assert second_forced["should_speak"] is True


def test_structure_driven_interval_work_high_confidence_stable_breath_keeps_phase_push_tone():
    state = {}
    high_conf_breath_summary = {
        "cue_interval_seconds": 20,
        "cue_due": False,
        "quality_sample_count": 8,
        "quality_median": 0.85,
        "quality_reliable": True,
    }

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=0,
            heart_rate=120,
            phase="warmup",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="moderate",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=610,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=631,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=661,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["phrase_id"] in {
        "interval.motivate.s3.1",
        "interval.motivate.s3.2",
        "interval.motivate.s4.1",
        "interval.motivate.s4.2",
    }

    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=700,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )
    assert second_forced["event_type"] != "structure_instruction_work"


def test_structure_driven_interval_work_high_confidence_heavy_breath_uses_control_tone():
    state = {}
    high_conf_breath_summary = {
        "cue_interval_seconds": 20,
        "cue_due": False,
        "quality_sample_count": 8,
        "quality_median": 0.85,
        "quality_reliable": True,
    }

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=0,
            heart_rate=120,
            phase="warmup",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=610,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
            phase="intense",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=631,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
            phase="intense",
        )
    )

    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=661,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
            phase="intense",
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["phrase_id"] in {
        "interval.motivate.s1.1",
        "interval.motivate.s2.2",
        "interval.motivate.s3.2",
    }

    second_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=700,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=high_conf_breath_summary,
            breath_intensity="intense",
            phase="intense",
        )
    )
    assert second_forced["event_type"] != "structure_instruction_work"


def test_easy_run_max_silence_budget_blocks_repeated_forced_cue():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
                elapsed_seconds=0,
                heart_rate=145,
                hr_max=None,
                resting_hr=None,
                age=None,
                breath_signal_quality=None,
            )
        )
    first_forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=70,
            heart_rate=145,
            hr_max=None,
            resting_hr=None,
            age=None,
            breath_signal_quality=None,
        )
    )
    assert first_forced["event_type"] == "max_silence_motivation"
    assert first_forced["should_speak"] is True

    second_forced_attempt = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=120,
            heart_rate=145,
            hr_max=None,
            resting_hr=None,
            age=None,
            breath_signal_quality=None,
        )
    )
    assert second_forced_attempt["should_speak"] is False
    assert second_forced_attempt["event_type"] != "max_silence_motivation"


def test_timeline_summary_caps_max_silence_only_with_high_confidence_breath():
    state = {}

    # First tick: stable HR so we get an initial spoken event and anchor silence timing.
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=0.8,
        )
    )

    # Lose HR while passing reliable breath summary from timeline.
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
                breath_summary={
                    "cue_interval_seconds": 20,
                    "cue_due": False,
                    "quality_sample_count": 8,
                    "quality_median": 0.82,
                    "quality_reliable": True,
                },
            )
        )

    forced = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=34,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary={
                "cue_interval_seconds": 20,
                "cue_due": True,
                "quality_sample_count": 8,
                "quality_median": 0.82,
                "quality_reliable": True,
            },
        )
    )
    assert forced["should_speak"] is True
    assert forced["event_type"] == "max_silence_go_by_feel"
    assert forced["phrase_id"] in {
        "zone.silence.work.1",
        "zone.silence.default.1",
    }


def test_timeline_summary_does_not_cap_max_silence_at_medium_breath_confidence():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=0,
            heart_rate=145,
            breath_signal_quality=0.8,
        )
    )

    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
                breath_summary={
                    "cue_interval_seconds": 20,
                    "cue_due": False,
                    "quality_sample_count": 8,
                    "quality_median": 0.62,
                    "quality_reliable": True,
                },
            )
        )

    not_forced_yet = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            elapsed_seconds=34,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary={
                "cue_interval_seconds": 20,
                "cue_due": True,
                "quality_sample_count": 8,
                "quality_median": 0.62,
                "quality_reliable": True,
            },
        )
    )
    assert not_forced_yet["should_speak"] is False
