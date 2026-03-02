import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_intelligence import VoiceIntelligence
from main import _infer_emotional_mode


def test_apply_text_rhythm_inserts_clause_break_for_long_plain_text():
    vi = VoiceIntelligence()
    text = "Hold fokus gjennom hele draget og finn jevn rytme"
    paced = vi.apply_text_rhythm(text, language="no", emotional_mode="supportive", pacing={"pause_after": 0})
    assert "," in paced


def test_apply_text_rhythm_adds_sentence_boundary_for_supportive_mode():
    vi = VoiceIntelligence()
    text = "Bra tempo hold trykket"
    paced = vi.apply_text_rhythm(text, language="no", emotional_mode="supportive", pacing={})
    assert paced.endswith(".")


def test_infer_emotional_mode_from_intensity():
    assert _infer_emotional_mode("calm") == "supportive"
    assert _infer_emotional_mode("moderate") == "pressing"
    assert _infer_emotional_mode("intense") == "intense"
    assert _infer_emotional_mode("critical") == "peak"
