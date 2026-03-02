import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathing_timeline import BREATHING_INTERRUPTS, BREATHING_TIMELINE, BreathingTimeline


def test_norwegian_timeline_has_no_ascii_fallback_artifacts():
    norwegian_text = []
    for phase in BREATHING_TIMELINE.values():
        for key, value in phase.items():
            if key.endswith("_no"):
                if isinstance(value, list):
                    norwegian_text.extend(value)
                elif isinstance(value, str):
                    norwegian_text.append(value)

    for interrupt in BREATHING_INTERRUPTS.values():
        for key, value in interrupt.items():
            if key.endswith("_no"):
                if isinstance(value, list):
                    norwegian_text.extend(value)
                elif isinstance(value, str):
                    norwegian_text.append(value)

    blob = " ".join(norwegian_text).lower()
    bad_tokens = [" aa ", " oe ", " ae ", "kjor", "foel", "foer", "oekt", "gjore", "toey", "faar"]
    for token in bad_tokens:
        assert token not in blob


def test_get_recent_summary_is_deterministic_and_non_mutating():
    timeline = BreathingTimeline()
    timeline.last_cue_time = 12
    timeline.cues_given = 2
    timeline.prep_safety_given = True

    before = (timeline.last_cue_time, timeline.cues_given, timeline.prep_safety_given)
    summary = timeline.get_recent_summary(phase="warmup", elapsed_seconds=50, language="no")
    after = (timeline.last_cue_time, timeline.cues_given, timeline.prep_safety_given)

    assert before == after
    assert summary["phase"] == "warmup"
    assert summary["language"] == "no"
    assert summary["pattern"] == "4-4"
    assert summary["cue_interval_seconds"] == 45
    assert summary["time_since_last_cue_seconds"] == 38
    assert summary["cue_due"] is False
    assert summary["cues_given"] == 2
    assert summary["prep_safety_given"] is True


def test_get_recent_summary_marks_cue_due_when_interval_passed():
    timeline = BreathingTimeline()
    timeline.last_cue_time = 0
    timeline.cues_given = 1
    summary = timeline.get_recent_summary(phase="recovery", elapsed_seconds=31, language="en")
    assert summary["cue_interval_seconds"] == 30
    assert summary["cue_due"] is True
