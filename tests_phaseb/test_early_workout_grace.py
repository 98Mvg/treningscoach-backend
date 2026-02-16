import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching_intelligence import should_coach_speak


def test_early_workout_forces_speak():
    """Coach MUST speak in first 30 seconds even with no intensity change."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=10,
    )
    assert should_speak is True
    assert reason == "early_workout_engagement"


def test_early_workout_grace_expires():
    """After grace period, normal rules apply (no change = no speak)."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    # Use a recent timestamp (5 seconds ago) so periodic timer doesn't fire
    recent_ts = datetime.now().isoformat()
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[{"timestamp": recent_ts, "text": "test"}],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=45,
    )
    # After grace, with no change and recent history, should not speak
    assert should_speak is False


def test_early_workout_none_elapsed_no_crash():
    """If elapsed_seconds is None (legacy call), don't crash — skip grace."""
    analysis = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    last = {"intensity": "moderate", "tempo": 12.0, "volume": 0.3}
    should_speak, reason = should_coach_speak(
        current_analysis=analysis,
        last_analysis=last,
        coaching_history=[],
        phase="warmup",
        training_level="intermediate",
        elapsed_seconds=None,
    )
    # Should not crash; result depends on other rules
    assert isinstance(should_speak, bool)
