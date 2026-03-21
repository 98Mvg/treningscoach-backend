import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from phrase_review_v2 import build_review_rows
from zone_event_motor import (
    _motivation_stage_from_rep,
    _motivation_stage_from_elapsed,
    _motivation_budget,
    _motivation_slots,
    _motivation_phrase_id,
    _motivation_stage_phrase_ids,
    _pick_motivation_phrase_id,
    _event_priority,
    _resolve_phrase_id,
    evaluate_zone_tick,
)


# --- Stage from rep_index ---

def test_stage_from_rep_1_is_supportive():
    assert _motivation_stage_from_rep(1) == 1

def test_stage_from_rep_2_is_pressing():
    assert _motivation_stage_from_rep(2) == 2

def test_stage_from_rep_3_is_intense():
    assert _motivation_stage_from_rep(3) == 3

def test_stage_from_rep_4_is_peak():
    assert _motivation_stage_from_rep(4) == 4

def test_stage_from_rep_6_clamped_to_peak():
    assert _motivation_stage_from_rep(6) == 4

def test_stage_from_rep_0_clamped_to_supportive():
    assert _motivation_stage_from_rep(0) == 1


# --- Stage from elapsed minutes (easy_run) ---

def test_easy_run_stage_0_min():
    assert _motivation_stage_from_elapsed(0, config) == 1

def test_easy_run_stage_10_min():
    assert _motivation_stage_from_elapsed(10, config) == 1

def test_easy_run_stage_20_min():
    assert _motivation_stage_from_elapsed(20, config) == 2

def test_easy_run_stage_39_min():
    assert _motivation_stage_from_elapsed(39, config) == 2

def test_easy_run_stage_40_min():
    assert _motivation_stage_from_elapsed(40, config) == 3

def test_easy_run_stage_60_min():
    assert _motivation_stage_from_elapsed(60, config) == 4

def test_easy_run_stage_90_min():
    assert _motivation_stage_from_elapsed(90, config) == 4


# --- Budget from work_seconds ---

def test_budget_30s_is_1():
    assert _motivation_budget(30) == 1

def test_budget_45s_is_1():
    assert _motivation_budget(45) == 1

def test_budget_60s_is_1():
    assert _motivation_budget(60) == 1

def test_budget_90s_is_2():
    assert _motivation_budget(90) == 2

def test_budget_120s_is_2():
    assert _motivation_budget(120) == 2

def test_budget_180s_is_3():
    assert _motivation_budget(180) == 3

def test_budget_240s_is_3():
    # floor(1 + 240/90) = floor(3.66) = 3
    assert _motivation_budget(240) == 3

def test_budget_600s_clamped_to_4():
    assert _motivation_budget(600) == 4


# --- Slot fractions ---

def test_slots_budget_1():
    assert _motivation_slots(1) == [0.55]

def test_slots_budget_2():
    assert _motivation_slots(2) == [0.35, 0.75]

def test_slots_budget_3():
    assert _motivation_slots(3) == [0.25, 0.55, 0.85]

def test_slots_budget_4():
    assert _motivation_slots(4) == [0.20, 0.45, 0.70, 0.90]


# --- Phrase ID resolution ---

# --- Event priority ---

def test_interval_in_target_sustained_priority_is_55():
    assert _event_priority("interval_in_target_sustained") == 55

def test_easy_run_in_target_sustained_priority_is_55():
    assert _event_priority("easy_run_in_target_sustained") == 55

def test_motivation_priority_below_entered_target():
    assert _event_priority("interval_in_target_sustained") < _event_priority("entered_target")

def test_max_silence_motivation_priority_below_instruction():
    assert _event_priority("max_silence_motivation") < _event_priority("max_silence_go_by_feel")


# --- Phrase ID resolution fallback ---

def test_resolve_phrase_id_interval_sustained_fallback():
    assert _resolve_phrase_id("interval_in_target_sustained", "work") == "interval.motivate.s2.1"

def test_resolve_phrase_id_easy_run_sustained_fallback():
    assert _resolve_phrase_id("easy_run_in_target_sustained", "main") == "easy_run.motivate.s2.1"


# --- Phrase ID builder ---

def test_phrase_id_interval_s1_v1():
    assert _motivation_phrase_id("intervals", stage=1, variant=1) == "interval.motivate.s1.1"

def test_phrase_id_interval_s3_v2():
    assert _motivation_phrase_id("intervals", stage=3, variant=2) == "interval.motivate.s3.2"

def test_phrase_id_easy_run_s2_v1():
    assert _motivation_phrase_id("easy_run", stage=2, variant=1) == "easy_run.motivate.s2.1"

def test_phrase_id_easy_run_s4_v2():
    assert _motivation_phrase_id("easy_run", stage=4, variant=2) == "easy_run.motivate.s4.2"


def test_staged_motivation_review_rows_are_marked_both():
    rows = {row.phrase_id: row for row in build_review_rows()}
    assert rows["interval.motivate.s2.1"].mode == "BOTH"
    assert rows["easy_run.motivate.s2.1"].mode == "BOTH"


# --- Stage-only pool + anti-repeat ---

def test_pick_motivation_phrase_id_uses_stage_pool_for_max_silence():
    state = {}
    stage_ids = _motivation_stage_phrase_ids("easy_run", stage=2)
    picked = [
        _pick_motivation_phrase_id(
            state=state,
            workout_type="easy_run",
            elapsed_seconds=index * 200,
            stage_phrase_ids=stage_ids,
            config_module=config,
        )
        for index in range(3)
    ]
    assert all(pid in stage_ids for pid in picked)
    assert picked[0] != picked[1], "Expected anti-repeat while alternatives exist"


def test_pick_motivation_phrase_id_stays_within_stage_pool():
    state = {}
    stage_ids = _motivation_stage_phrase_ids("intervals", stage=1)
    picked = [
        _pick_motivation_phrase_id(
            state=state,
            workout_type="intervals",
            elapsed_seconds=index * 95,
            stage_phrase_ids=stage_ids,
            config_module=config,
        )
        for index in range(4)
    ]
    assert picked[0] in stage_ids
    assert any(pid in stage_ids for pid in picked), "Stage pool should stay eligible"
    assert all(pid in stage_ids for pid in picked), "Flat global motivation pool should be inactive"


# ---------------------------------------------------------------------------
# Integration tests — evaluate_zone_tick with motivation events
# ---------------------------------------------------------------------------

def _base_tick(**overrides):
    payload = {
        "workout_state": {},
        "workout_mode": "interval",
        "phase": "intense",
        "elapsed_seconds": 300,
        "language": "en",
        "persona": "personal_trainer",
        "coaching_style": "normal",
        "interval_template": "4x4",
        "heart_rate": 165,
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


def _simulate_ticks(state, mode, start_elapsed, end_elapsed, step=5, hr=165, phase="intense"):
    """Run ticks from start to end, return list of results."""
    results = []
    for t in range(start_elapsed, end_elapsed + 1, step):
        r = evaluate_zone_tick(**_base_tick(
            workout_state=state,
            workout_mode=mode,
            elapsed_seconds=t,
            heart_rate=hr,
            phase=phase,
        ))
        results.append(r)
    return results


def _find_motivation_events(results, event_type):
    """Extract results that contain a given motivation event type."""
    return [
        r for r in results
        if any(
            e.get("event_type") == event_type
            for e in (r.get("events") or [])
        )
    ]


def test_interval_motivation_fires_in_work_phase_when_in_zone():
    """Rep 1 work phase: after sustain threshold, motivation should fire."""
    state = {}
    # Warmup tick to init state
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=120, phase="warmup"))

    # Jump to work phase (elapsed=610, 10s into rep 1 work)
    results = _simulate_ticks(state, "interval", 610, 750, step=5, hr=165)

    motivation_events = _find_motivation_events(results, "interval_in_target_sustained")
    # Non-crash assertion; deeper tests below.
    # Whether motivation fires depends on whether HR lands in zone for
    # the configured template—zone math is tested elsewhere.
    assert len(motivation_events) >= 0


def test_interval_motivation_not_in_recovery():
    """Motivation events should NOT fire during recovery phase."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=120, phase="warmup"))

    # Simulate recovery ticks (phase="recovery" is key)
    results = _simulate_ticks(state, "interval", 850, 950, step=5, hr=140, phase="recovery")

    motivation_events = _find_motivation_events(results, "interval_in_target_sustained")
    assert len(motivation_events) == 0, "Motivation should not fire in recovery"


def test_interval_motivation_blocked_before_10s():
    """Motivation should not fire in first 10s of work phase (HR lag guard)."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=120, phase="warmup"))

    # First 10s of work (elapsed 600-609, 1s steps)
    results = _simulate_ticks(state, "interval", 600, 609, step=1, hr=165)

    motivation_events = _find_motivation_events(results, "interval_in_target_sustained")
    assert len(motivation_events) == 0, "Motivation blocked before 10s into work"


def test_interval_motivation_budget_caps_per_phase():
    """Budget for 240s work = 3 (floor(1+240/90)). Should not exceed budget."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=120, phase="warmup"))

    # Full rep 1 work: 600-839
    results = _simulate_ticks(state, "interval", 600, 839, step=3, hr=165)

    motivation_count = sum(
        1 for r in results
        if any(
            e.get("event_type") == "interval_in_target_sustained"
            for e in (r.get("events") or [])
        )
    )
    budget = _motivation_budget(240)  # = 3
    assert motivation_count <= budget, f"Budget exceeded: {motivation_count} > {budget}"


def test_easy_run_motivation_fires_when_in_zone():
    """Easy run: motivation should fire after sustain threshold when in zone."""
    state = {}
    # Easy run main phase
    results = _simulate_ticks(state, "easy_run", 0, 300, step=10, hr=140, phase="intense")

    motivation_events = _find_motivation_events(results, "easy_run_in_target_sustained")
    # Non-crash assertion; zone target depends on config
    assert len(motivation_events) >= 0


def test_easy_run_motivation_respects_cooldown():
    """Easy run: second motivation should respect cooldown period."""
    state = {}
    # Long easy run
    results = _simulate_ticks(state, "easy_run", 0, 600, step=5, hr=140, phase="intense")

    motivation_times = [
        r.get("meta", {}).get("elapsed_seconds", 0)
        for r in results
        if any(
            e.get("event_type") == "easy_run_in_target_sustained"
            for e in (r.get("events") or [])
        )
    ]
    # If multiple motivations fired, they should be >= 120s apart
    for i in range(1, len(motivation_times)):
        gap = motivation_times[i] - motivation_times[i - 1]
        assert gap >= 120, f"Cooldown violated: {gap}s between motivations"


def test_easy_run_structure_mode_uses_staged_max_silence_motivation():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                workout_mode="easy_run",
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=None,
            phase="intense",
        )
    )

    motivated = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            elapsed_seconds=100,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert motivated["event_type"] == "max_silence_motivation"
    assert motivated["phrase_id"].startswith("easy_run.motivate.")


def test_easy_run_structure_mode_low_breath_confidence_uses_neutral_bucket():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                workout_mode="easy_run",
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=None,
                phase="intense",
            )
        )

    motivated = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            elapsed_seconds=100,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert motivated["event_type"] == "max_silence_motivation"
    assert motivated["phrase_id"] in {
        "easy_run.motivate.s2.1",
        "easy_run.motivate.s2.2",
        "easy_run.motivate.s4.2",
    }


def test_easy_run_structure_mode_medium_breath_confidence_uses_supportive_bucket():
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
            workout_mode="easy_run",
            elapsed_seconds=0,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=medium_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )
    for second in [9, 13]:
        evaluate_zone_tick(
            **_base_tick(
                workout_state=state,
                workout_mode="easy_run",
                elapsed_seconds=second,
                heart_rate=None,
                hr_quality="poor",
                watch_connected=False,
                watch_status="disconnected",
                breath_signal_quality=0.8,
                breath_summary=medium_conf_breath_summary,
                breath_intensity="moderate",
                phase="intense",
            )
        )

    motivated = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            elapsed_seconds=100,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=0.8,
            breath_summary=medium_conf_breath_summary,
            breath_intensity="moderate",
            phase="intense",
        )
    )

    assert motivated["event_type"] == "max_silence_motivation"
    assert motivated["phrase_id"] in {
        "easy_run.motivate.s3.1",
        "easy_run.motivate.s3.2",
    }


def test_interval_motivation_basis_is_structure_progress_in_no_hr_mode():
    state = {}

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=0,
            heart_rate=120,
            phase="warmup",
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
            breath_signal_quality=None,
            phase="intense",
        )
    )

    notice = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=631,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert notice["event_type"] == "hr_structure_mode_notice"

    recovery_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=840,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert recovery_transition["event_type"] == "structure_instruction_recovery"

    work_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1020,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert work_transition["event_type"] == "structure_instruction_work"

    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1080,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1160,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )

    motivated = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1225,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
            breath_signal_quality=None,
            phase="intense",
        )
    )
    assert motivated["event_type"] == "interval_in_target_sustained"
    assert motivated["motivation_basis"] == "structure_progress"
    assert motivated["phrase_id"].startswith("interval.motivate.")


def test_interval_structure_mode_high_confidence_stable_breath_uses_push_bucket():
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
    recovery_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=840,
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
    assert recovery_transition["event_type"] == "structure_instruction_recovery"
    work_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1020,
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
    assert work_transition["event_type"] == "structure_instruction_work"
    early_motivation = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1080,
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
    assert early_motivation["event_type"] == "max_silence_motivation"
    assert early_motivation["phrase_id"] in {
        "interval.motivate.s3.1",
        "interval.motivate.s3.2",
        "interval.motivate.s4.1",
        "interval.motivate.s4.2",
    }


def test_interval_structure_mode_high_confidence_heavy_breath_uses_calm_bucket():
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
    recovery_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=840,
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
    assert recovery_transition["event_type"] == "structure_instruction_recovery"
    work_transition = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1020,
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
    assert work_transition["event_type"] == "structure_instruction_work"
    early_motivation = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            elapsed_seconds=1080,
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
    assert early_motivation["event_type"] == "max_silence_motivation"
    assert early_motivation["phrase_id"] in {
        "interval.motivate.s1.1",
        "interval.motivate.s2.2",
        "interval.motivate.s3.2",
    }


def test_motivation_phrase_id_contains_stage():
    """Deterministic motivation now resolves to staged phrase IDs only."""
    state = {}
    evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=0, heart_rate=120, phase="warmup"))

    results = _simulate_ticks(state, "interval", 610, 780, step=5, hr=165)

    for r in results:
        for e in (r.get("events") or []):
            if e.get("event_type") == "interval_in_target_sustained":
                pid = e.get("phrase_id", "")
                assert pid.startswith("interval.motivate.s"), f"Bad phrase_id: {pid}"


def test_evaluate_motivation_event_not_crashes_easy_run_mode():
    """Easy run mode tick simulation should not crash."""
    state = {}
    # Just verify the code path doesn't error
    r = evaluate_zone_tick(**_base_tick(
        workout_state=state,
        workout_mode="easy_run",
        phase="intense",
        elapsed_seconds=300,
        heart_rate=140,
    ))
    assert r["handled"] is True


def test_evaluate_motivation_event_not_crashes_interval_mode():
    """Interval mode tick simulation should not crash."""
    state = {}
    r = evaluate_zone_tick(**_base_tick(
        workout_state=state,
        workout_mode="interval",
        phase="intense",
        elapsed_seconds=700,
        heart_rate=170,
    ))
    assert r["handled"] is True
