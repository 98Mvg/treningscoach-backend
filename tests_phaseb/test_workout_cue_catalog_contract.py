import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_phrase_catalog import PHRASE_CATALOG
from workout_cue_catalog import (
    INSTRUCTION_LOW_URGENCY,
    count_words,
    get_event_catalog,
    get_instruction_urgency,
    get_motivation_stage_label,
    get_workout_cue_catalog,
    is_active_deterministic_workout_phrase_id,
    validate_active_workout_cue_phrase,
)


def test_phrase_catalog_maps_representative_ids_to_four_catalogs():
    assert get_workout_cue_catalog("zone.above.default.1") == "instruction"
    assert get_workout_cue_catalog("zone.silence.work.1") == "instruction"
    assert get_workout_cue_catalog("zone.structure.steady.1") == "instruction"
    assert get_workout_cue_catalog("zone.phase.warmup.1") == "context"
    assert get_workout_cue_catalog("zone.hr_poor_timing.1") == "context"
    assert get_workout_cue_catalog("zone.main_started.1") == "context"
    assert get_workout_cue_catalog("zone.countdown.15") == "progress"
    assert get_workout_cue_catalog("zone.workout_finished.1") == "progress"
    assert get_workout_cue_catalog("interval.motivate.s3.1") == "motivation"
    assert get_workout_cue_catalog("easy_run.motivate.s4.2") == "motivation"


def test_zone_silence_is_low_urgency_instruction():
    assert get_instruction_urgency("zone.silence.work.1") == INSTRUCTION_LOW_URGENCY
    assert get_instruction_urgency("zone.above.default.1") != INSTRUCTION_LOW_URGENCY


def test_legacy_feel_and_breath_families_are_not_active_runtime_ids():
    assert is_active_deterministic_workout_phrase_id("zone.feel.easy_run.1") is False
    assert is_active_deterministic_workout_phrase_id("zone.breath.work.1") is False


def test_flat_motivation_pool_is_not_active_runtime_path():
    assert get_workout_cue_catalog("motivation.1") == "motivation"
    assert get_motivation_stage_label("motivation.1") == "legacy_fallback"
    assert is_active_deterministic_workout_phrase_id("motivation.1") is False


def test_staged_motivation_has_logical_stage_labels():
    assert get_motivation_stage_label("interval.motivate.s1.1") == "start"
    assert get_motivation_stage_label("interval.motivate.s2.1") == "steady"
    assert get_motivation_stage_label("interval.motivate.s3.1") == "push"
    assert get_motivation_stage_label("easy_run.motivate.s4.2") == "finish"


def test_event_catalogs_match_runtime_contract():
    assert get_event_catalog("max_silence_go_by_feel") == "instruction"
    assert get_event_catalog("max_silence_breath_guide") == "instruction"
    assert get_event_catalog("structure_instruction_steady") == "instruction"
    assert get_event_catalog("hr_structure_mode_notice") == "context"
    assert get_event_catalog("max_silence_motivation") == "motivation"
    assert get_event_catalog("warmup_started") == "context"
    assert get_event_catalog("interval_countdown_start") == "progress"


def test_all_active_deterministic_workout_phrases_meet_catalog_word_caps():
    failures = []
    for phrase in PHRASE_CATALOG:
        phrase_id = phrase["id"]
        if not is_active_deterministic_workout_phrase_id(phrase_id):
            continue
        for language in ("en", "no"):
            text = str(phrase.get(language, "")).strip()
            ok, reason = validate_active_workout_cue_phrase(phrase_id, text)
            if not ok:
                failures.append(f"[{language}] {phrase_id}: {reason} text={text!r}")
    assert failures == [], "Active deterministic workout cue cap failures:\n" + "\n".join(failures)


def test_progress_and_instruction_samples_are_within_expected_word_counts():
    assert count_words("Stay controlled. Rep by rep.") <= 6
    assert count_words("Paused. Start easy when ready.") <= 8
