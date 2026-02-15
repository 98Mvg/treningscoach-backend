import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching_intelligence import apply_max_silence_override


def test_max_silence_override_forces_speech_when_limit_reached():
    should_speak, reason = apply_max_silence_override(
        should_speak=False,
        reason="no_change",
        elapsed_since_last=31.0,
        max_silence_seconds=30,
    )
    assert should_speak is True
    assert reason == "max_silence_override"


def test_max_silence_override_does_not_force_before_limit():
    should_speak, reason = apply_max_silence_override(
        should_speak=False,
        reason="no_change",
        elapsed_since_last=12.0,
        max_silence_seconds=30,
    )
    assert should_speak is False
    assert reason == "no_change"


def test_max_silence_override_preserves_existing_speak_decision():
    should_speak, reason = apply_max_silence_override(
        should_speak=True,
        reason="critical_breathing",
        elapsed_since_last=120.0,
        max_silence_seconds=30,
    )
    assert should_speak is True
    assert reason == "critical_breathing"


def test_max_silence_override_ignores_missing_elapsed_time():
    should_speak, reason = apply_max_silence_override(
        should_speak=False,
        reason="no_change",
        elapsed_since_last=None,
        max_silence_seconds=30,
    )
    assert should_speak is False
    assert reason == "no_change"
