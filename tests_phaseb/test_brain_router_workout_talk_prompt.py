import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_router import BrainRouter


def test_workout_talk_prompt_includes_sets_and_time():
    router = BrainRouter()
    prompt = router.build_workout_talk_prompt(
        question="How am I doing?",
        language="en",
        workout_context={
            "phase": "work",
            "time_left_s": 300,
            "reps_remaining_including_current": 2,
            "heart_rate": 0,
            "zone_state": "hr_missing",
        },
    )
    lowered = prompt.lower()
    assert "time_left_s=300" in lowered
    assert "reps_remaining_including_current=2" in lowered
    assert "heart_rate=unavailable" in lowered
    assert "do not state current hr numbers" in lowered


def test_workout_talk_prompt_allows_hr_when_valid():
    router = BrainRouter()
    prompt = router.build_workout_talk_prompt(
        question="Should I speed up?",
        language="no",
        workout_context={
            "phase": "main",
            "heart_rate": 152,
            "zone_state": "in_zone",
            "target_hr_low": 145,
            "target_hr_high": 160,
        },
    )
    lowered = prompt.lower()
    assert "heart_rate=152" in lowered
    assert "target_hr_range=145-160" in lowered


def test_workout_talk_prompt_includes_recent_conversation_and_zone_events():
    router = BrainRouter()
    prompt = router.build_workout_talk_prompt(
        question="And how long?",
        language="en",
        workout_context={"phase": "work", "time_left_s": 180},
        conversation_history=[
            {"role": "user", "content": "How many intervals are left?"},
            {"role": "assistant", "content": "Two intervals left."},
        ],
        recent_zone_events=[
            {
                "event_type": "above_zone",
                "text": "Ease off a touch.",
                "seconds_since_last_event": 6,
            }
        ],
    )
    lowered = prompt.lower()
    assert "recent conversation:" in lowered
    assert "user: how many intervals are left?" in lowered
    assert "coach: two intervals left." in lowered
    assert "recent deterministic workout events:" in lowered
    assert "above_zone: ease off a touch. (6s ago)" in lowered
    assert "treat short follow-up questions as a continuation" in lowered
