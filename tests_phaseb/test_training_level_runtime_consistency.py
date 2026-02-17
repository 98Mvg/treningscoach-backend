import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching_intelligence import should_coach_speak
from session_manager import EmotionalState


def _analysis(intensity: str = "moderate", tempo: int = 20):
    return {"intensity": intensity, "tempo": tempo, "volume": 0.5}


def test_periodic_interval_is_consistent_across_levels():
    current = _analysis("moderate", 20)
    last = _analysis("moderate", 20)
    history = [{"timestamp": datetime.now() - timedelta(seconds=35), "text": "Hold it."}]

    beginner = should_coach_speak(
        current_analysis=current,
        last_analysis=last,
        coaching_history=history,
        phase="warmup",
        training_level="beginner",
        elapsed_seconds=120,
    )
    advanced = should_coach_speak(
        current_analysis=current,
        last_analysis=last,
        coaching_history=history,
        phase="warmup",
        training_level="advanced",
        elapsed_seconds=120,
    )

    assert beginner == advanced
    assert beginner == (True, "periodic_warmup")


def test_beginner_guardrail_replaces_push_harder_reason():
    current = _analysis("calm", 20)
    last = _analysis("moderate", 20)

    beginner = should_coach_speak(
        current_analysis=current,
        last_analysis=last,
        coaching_history=[],
        phase="intense",
        training_level="beginner",
        elapsed_seconds=120,
    )
    advanced = should_coach_speak(
        current_analysis=current,
        last_analysis=last,
        coaching_history=[],
        phase="intense",
        training_level="advanced",
        elapsed_seconds=120,
    )

    assert beginner == (True, "beginner_guardrail")
    assert advanced == (True, "push_harder")


def test_emotional_escalation_same_for_intermediate_and_advanced():
    intermediate = EmotionalState()
    advanced = EmotionalState()
    beginner = EmotionalState()

    intermediate.update(is_struggling=True, coach_was_silent=False, training_level="intermediate")
    advanced.update(is_struggling=True, coach_was_silent=False, training_level="advanced")
    beginner.update(is_struggling=True, coach_was_silent=False, training_level="beginner")

    assert advanced.intensity == intermediate.intensity
    assert beginner.intensity < intermediate.intensity
