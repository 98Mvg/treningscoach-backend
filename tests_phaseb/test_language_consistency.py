import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_router import BrainRouter
from brains.openai_brain import OpenAIBrain
from brains.claude_brain import ClaudeBrain
from brains.gemini_brain import GeminiBrain
from brains.grok_brain import GrokBrain
from main import enforce_language_consistency, _looks_english


def test_router_normalizes_english_locale_for_config_fallback():
    router = BrainRouter(brain_type="config")
    response = router.get_coaching_response(
        breath_data={"intensity": "unknown"},
        phase="unsupported_phase",
        mode="chat",
        language="EN-us",
    )
    assert response == "Keep going!"


def test_router_toxic_fallback_stays_english_for_en_locale():
    router = BrainRouter(brain_type="config")
    response = router.get_coaching_response(
        breath_data={"intensity": "unknown"},
        phase="unsupported_phase",
        mode="chat",
        language="EN",
        persona="toxic_mode",
    )
    assert response == "KEEP GOING!"


def test_provider_fallbacks_use_requested_language_for_default_message():
    providers = [OpenAIBrain, ClaudeBrain, GeminiBrain, GrokBrain]

    for provider in providers:
        brain = provider.__new__(provider)
        assert brain._get_fallback_message("unknown", "intense", "en") == "Keep going!"
        assert brain._get_fallback_message("unknown", "intense", "no") == "Fortsett!"


def test_english_detected_when_language_is_norwegian():
    """English coaching phrases should be detected and replaced when language=no."""
    english_phrases = ["Keep going!", "Good job!", "Push harder.", "You got this!"]
    for phrase in english_phrases:
        result = enforce_language_consistency(phrase, "no")
        assert "æ" in result or "ø" in result or "å" in result or result in {
            "Fortsett!", "Kjør på!", "Bra jobba!"
        } or result != phrase, f"English phrase '{phrase}' was not corrected for Norwegian"


def test_looks_english_detects_common_phrases():
    """_looks_english should detect common English coaching phrases."""
    assert _looks_english("Keep going!") is True
    assert _looks_english("Good job!") is True
    assert _looks_english("Push harder") is True
    assert _looks_english("You are doing great") is True  # "are" + "you" markers


def test_looks_english_passes_norwegian():
    """_looks_english should NOT flag actual Norwegian text."""
    assert _looks_english("Kjør på!") is False
    assert _looks_english("Bra jobba!") is False
    assert _looks_english("Fortsett!") is False
    assert _looks_english("Helt inn nå!") is False


def test_language_guard_leaves_norwegian_untouched():
    """Norwegian text should pass through the guard unchanged."""
    norwegian_phrases = ["Kjør på!", "Bra jobba!", "Helt inn nå!", "Nydelig!"]
    for phrase in norwegian_phrases:
        result = enforce_language_consistency(phrase, "no")
        assert result == phrase, f"Norwegian phrase '{phrase}' was incorrectly modified to '{result}'"


def test_norwegian_quality_guard_rewrites_known_awkward_phrases():
    assert enforce_language_consistency("Vakkert.", "no", phase="intense") == "Bra jobba."
    assert enforce_language_consistency("Gi meg mer kraft!", "no", phase="intense") == "Mer trykk nå!"
    assert enforce_language_consistency("Trykk hardere.", "no", phase="intense") == "Press hardere."
    assert enforce_language_consistency("Jevn opp.", "no", phase="intense") == "Finn jevn rytme."


def test_norwegian_quality_guard_blocks_warmup_phrases_after_warmup():
    result = enforce_language_consistency("Forsiktig, fortsett å varme opp.", "no", phase="intense")
    assert result == "Nå øker vi trykket."
