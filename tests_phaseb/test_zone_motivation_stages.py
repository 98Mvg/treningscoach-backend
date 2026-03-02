import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from zone_event_motor import (
    _motivation_stage_from_rep,
    _motivation_stage_from_elapsed,
    _motivation_budget,
    _motivation_slots,
    _motivation_phrase_id,
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

def test_phrase_id_interval_s1_v1():
    assert _motivation_phrase_id("intervals", stage=1, variant=1) == "interval.motivate.s1.1"

def test_phrase_id_interval_s3_v2():
    assert _motivation_phrase_id("intervals", stage=3, variant=2) == "interval.motivate.s3.2"

def test_phrase_id_easy_run_s2_v1():
    assert _motivation_phrase_id("easy_run", stage=2, variant=1) == "easy_run.motivate.s2.1"

def test_phrase_id_easy_run_s4_v2():
    assert _motivation_phrase_id("easy_run", stage=4, variant=2) == "easy_run.motivate.s4.2"
