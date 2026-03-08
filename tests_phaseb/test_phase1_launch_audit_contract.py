import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from zone_event_motor import (
    _motivation_stage_phrase_ids,
    _pick_structure_phrase_id,
    _resolve_phrase_id,
)
import main


def test_structure_instruction_rotation_avoids_immediate_repeat():
    state = {}

    first = _pick_structure_phrase_id(
        state=state,
        event_type="structure_instruction_steady",
    )
    second = _pick_structure_phrase_id(
        state=state,
        event_type="structure_instruction_steady",
    )

    assert first == "zone.structure.steady.1"
    assert second == "zone.structure.steady.2"
    assert first != second


def test_motivation_stage_pool_currently_uses_two_variants_per_stage():
    assert _motivation_stage_phrase_ids("intervals", 3) == [
        "interval.motivate.s3.1",
        "interval.motivate.s3.2",
    ]
    assert _motivation_stage_phrase_ids("easy_run", 4) == [
        "easy_run.motivate.s4.1",
        "easy_run.motivate.s4.2",
    ]


def test_hr_correction_phrase_resolution_stays_on_canonical_variant_one():
    assert _resolve_phrase_id("entered_target", "main") == "zone.in_zone.default.1"
    assert _resolve_phrase_id("exited_target_above", "main") == "zone.above.default.1"
    assert _resolve_phrase_id("exited_target_below", "main") == "zone.below.default.1"


def test_launch_default_coach_score_version_is_v2():
    assert config.COACH_SCORE_VERSION == "cs_v2"


def test_launch_audit_coach_score_caps_when_targets_are_unenforced():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=2400,
        breath_data={"signal_quality": 0.9, "breath_regularity": 0.9, "intensity_confidence": 0.9},
        zone_tick={
            "heart_rate": 152,
            "hr_quality": "good",
            "main_set_seconds": 2400,
            "hr_valid_main_set_seconds": 2000,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
            "zone_compliance": None,
        },
        watch_connected=True,
        heart_rate=152,
        hr_quality="good",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )

    assert "ZONE_MISSING_OR_UNENFORCED" in payload["cap_reason_codes"]
    assert "DURATION_ONLY_CAP" in payload["cap_reason_codes"]
    assert payload["cap_applied_reason"] == "DURATION_ONLY_CAP"
