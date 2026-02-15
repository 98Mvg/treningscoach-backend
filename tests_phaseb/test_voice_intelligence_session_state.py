import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_intelligence import VoiceIntelligence


def _near_zero_signal_breath():
    return {
        "intensity": "moderate",
        "signal_quality": 0.0,
        "breath_regularity": 0.4,
    }


def test_silence_state_is_isolated_per_session():
    voice = VoiceIntelligence()

    # First near-zero tick in session A: allow one silent tick.
    a_silent, a_reason = voice.should_stay_silent(
        breath_data=_near_zero_signal_breath(),
        phase="intense",
        last_coaching="",
        elapsed_seconds=60,
        session_id="session-a",
    )
    assert a_silent is True
    assert a_reason == "near_zero_signal"

    # Second near-zero tick in session A: should speak (silence budget spent).
    a2_silent, _ = voice.should_stay_silent(
        breath_data=_near_zero_signal_breath(),
        phase="intense",
        last_coaching="",
        elapsed_seconds=68,
        session_id="session-a",
    )
    assert a2_silent is False

    # Session B should have its own silence budget and still allow one silent tick.
    b_silent, b_reason = voice.should_stay_silent(
        breath_data=_near_zero_signal_breath(),
        phase="intense",
        last_coaching="",
        elapsed_seconds=60,
        session_id="session-b",
    )
    assert b_silent is True
    assert b_reason == "near_zero_signal"


def test_clear_session_state_resets_silence_budget():
    voice = VoiceIntelligence()
    session_id = "session-reset"

    first_silent, _ = voice.should_stay_silent(
        breath_data=_near_zero_signal_breath(),
        phase="intense",
        last_coaching="",
        elapsed_seconds=60,
        session_id=session_id,
    )
    assert first_silent is True

    voice.clear_session_state(session_id)

    silent_after_clear, reason_after_clear = voice.should_stay_silent(
        breath_data=_near_zero_signal_breath(),
        phase="intense",
        last_coaching="",
        elapsed_seconds=68,
        session_id=session_id,
    )
    assert silent_after_clear is True
    assert reason_after_clear == "near_zero_signal"
