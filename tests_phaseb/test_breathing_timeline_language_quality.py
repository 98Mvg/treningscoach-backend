import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathing_timeline import BREATHING_INTERRUPTS, BREATHING_TIMELINE


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
