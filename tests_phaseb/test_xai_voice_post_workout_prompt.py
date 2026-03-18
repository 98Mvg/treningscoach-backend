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
    assert "00:07 means 7 seconds, not 7 minutes." in instructions
    assert "The workout lasted only 7 seconds." in instructions
    assert "Do not reinterpret it as a hold, plank, set, or any non-running exercise." in instructions


def test_post_workout_voice_instructions_keep_generic_workout_running_only() -> None:
    instructions = xai_voice.build_post_workout_voice_instructions(
        summary_context={
            "workout_mode": "standard",
            "workout_label": "Workout",
            "duration_text": "12:30",
            "elapsed_s": 750,
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
    assert "Do not use workout history in the opening message." in instructions
    assert "If the summary is generic, short, or sparse, keep the opening generic and running-specific." in instructions
    assert "If the summary does not explicitly name an exercise, assume no exercise name is known." in instructions
    assert "NEVER say you noticed the athlete doing a plank, squat, or any other exercise earlier." in instructions
    assert "NEVER mention specific exercises (squats, lunges, push-ups, burpees, planks, etc.)." in instructions
    assert "NEVER mention gym, strength, lifting, bodyweight circuits, studio classes, or cross-training examples." in instructions
