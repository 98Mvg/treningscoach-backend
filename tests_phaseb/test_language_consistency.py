import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_router import BrainRouter
from brains.openai_brain import OpenAIBrain
from brains.claude_brain import ClaudeBrain
from brains.gemini_brain import GeminiBrain
from brains.grok_brain import GrokBrain


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
