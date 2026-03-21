from __future__ import annotations

import xai_voice


def test_post_workout_voice_instructions_treat_mmss_as_seconds() -> None:
    instructions = xai_voice.build_post_workout_voice_instructions(
        summary_context={
            "workout_mode": "standard",
            "workout_label": "Workout",
            "duration_text": "00:07",
            "elapsed_s": 7,
            "coach_score": 12,
            "coach_score_summary_line": "Short effort captured.",
        },
        history_context={},
        language="en",
        user_name="Marius",
    )

    assert "Duration: 7 seconds" in instructions
    assert "00:07 = 7 seconds, not 7 minutes" in instructions
    assert "The workout lasted only 7 seconds." in instructions
    assert "Do not reinterpret it as a hold, plank, set, or any non-running exercise." in instructions
    assert "YOUR FIRST RESPONSE" in instructions
    assert "Mention one or two stats from the recap brief below." in instructions
    assert "End with a short insight or one question." in instructions


def test_post_workout_voice_instructions_keep_generic_workout_running_only() -> None:
    instructions = xai_voice.build_post_workout_voice_instructions(
        summary_context={
            "workout_mode": "standard",
            "workout_label": "Workout",
            "duration_text": "12:30",
            "elapsed_s": 750,
            "average_heart_rate": 148,
            "distance_meters": 2200,
            "coach_score": 71,
            "coach_score_summary_line": "Solid aerobic session.",
        },
        history_context={},
        language="en",
        user_name=None,
    )

    assert "The athlete chose a general running workout." in instructions
    assert "The athlete just completed a general running workout." in instructions
    assert "Workout: general running workout" in instructions
    assert "Workout: Workout" not in instructions
    assert "For this opening, refer to the workout as 'general running workout'." in instructions
    # Context awareness lives in the post_workout_voice persona
    assert "Do not assume exercises that were not done" in instructions
    assert "Only invent or assume details that are clearly implied" in instructions
    assert "Opening recap brief:" in instructions
    assert "- Workout: general running workout" in instructions
    assert "- Duration: 12 minutes 30 seconds" in instructions
    assert "- Average heart rate: 148 BPM" in instructions
    assert "- Distance: 2.20 km" in instructions
    assert "- Insight cue:" in instructions
