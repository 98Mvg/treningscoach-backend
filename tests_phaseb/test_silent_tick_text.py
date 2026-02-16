import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _get_silent_debug_text


def test_silent_debug_text_language_defaults():
    assert _get_silent_debug_text("no_change", "en") == "Hold rhythm."
    assert _get_silent_debug_text("no_change", "no") == "Hold rytmen."
    assert _get_silent_debug_text("no_change", "da") == "Hold rytmen."


def test_silent_debug_text_reason_specific():
    assert _get_silent_debug_text("near_zero_signal", "en") == "Listening..."
    assert _get_silent_debug_text("too_frequent", "no") == "Hold jevnt."
    assert _get_silent_debug_text("unknown_reason", "en") == "Hold form."
