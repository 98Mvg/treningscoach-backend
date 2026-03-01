import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from tts_phrase_catalog import PHRASE_CATALOG


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
