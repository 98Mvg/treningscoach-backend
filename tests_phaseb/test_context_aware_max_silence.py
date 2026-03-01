import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from tts_phrase_catalog import PHRASE_CATALOG
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


def test_phrase_catalog_has_go_by_feel_easy_run():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.easy_run.1" in ids
    assert "zone.feel.easy_run.2" in ids
    assert "zone.feel.easy_run.3" in ids


def test_phrase_catalog_has_go_by_feel_work():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.work.1" in ids
    assert "zone.feel.work.2" in ids


def test_phrase_catalog_has_go_by_feel_recovery():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.feel.recovery.1" in ids
    assert "zone.feel.recovery.2" in ids


def test_phrase_catalog_has_breath_guide_phrases():
    ids = {p["id"] for p in PHRASE_CATALOG}
    assert "zone.breath.easy_run.1" in ids
    assert "zone.breath.easy_run.2" in ids
    assert "zone.breath.work.1" in ids
    assert "zone.breath.recovery.1" in ids


def test_go_by_feel_phrases_are_bilingual():
    for phrase in PHRASE_CATALOG:
        if phrase["id"].startswith("zone.feel."):
            assert phrase.get("en"), f"{phrase['id']} missing English"
            assert phrase.get("no"), f"{phrase['id']} missing Norwegian"
            assert phrase.get("persona") == "personal_trainer"
            assert phrase.get("priority") == "core"


def test_breath_guide_phrases_are_bilingual():
    for phrase in PHRASE_CATALOG:
        if phrase["id"].startswith("zone.breath."):
            assert phrase.get("en"), f"{phrase['id']} missing English"
            assert phrase.get("no"), f"{phrase['id']} missing Norwegian"


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


def test_tier_c_above_tier_d():
    assert _event_priority("max_silence_go_by_feel") > _event_priority("max_silence_motivation")
    assert _event_priority("max_silence_breath_guide") > _event_priority("max_silence_motivation")


def test_event_group_motivation():
    assert _event_group("max_silence_motivation") == "motivation"


def test_event_group_go_by_feel():
    assert _event_group("max_silence_go_by_feel") == "info"


def test_event_group_breath_guide():
    assert _event_group("max_silence_breath_guide") == "info"


def test_max_silence_uses_go_by_feel_when_no_hr_and_no_breath():
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
    assert forced["event_type"] == "max_silence_go_by_feel"
    assert forced["should_speak"] is True


def test_max_silence_uses_breath_guide_when_hr_missing_breath_reliable():
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
    assert forced["event_type"] == "max_silence_breath_guide"
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
