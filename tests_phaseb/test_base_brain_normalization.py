import os
import sys
from typing import AsyncIterator, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brains.base_brain import BaseBrain


class DummyBrain(BaseBrain):
    def get_coaching_response(self, breath_data: Dict, phase: str = "intense") -> str:
        return "ok"

    def get_realtime_coaching(self, breath_data: Dict, phase: str = "intense") -> str:
        return "ok"

    def supports_streaming(self) -> bool:
        return False

    async def stream_chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        if False:
            yield ""

    async def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        return "ok"

    def get_provider_name(self) -> str:
        return "dummy"


def test_language_and_intensity_normalization_helpers():
    brain = DummyBrain()

    assert brain.normalize_language("EN-us") == "en"
    assert brain.normalize_language("nb-NO") == "no"
    assert brain.normalize_language("da-DK") == "da"

    assert brain.normalize_intensity("moderat") == "moderate"
    assert brain.normalize_intensity("kritisk") == "critical"
    assert brain.normalize_intensity("hard") == "intense"
    assert brain.normalize_intensity("rolig") == "calm"


def test_extract_intensity_supports_legacy_and_new_keys():
    brain = DummyBrain()

    assert brain.extract_intensity({"intensity": "moderate"}) == "moderate"
    assert brain.extract_intensity({"intensitet": "kritisk"}) == "critical"
    assert brain.extract_intensity({}) == "moderate"


def test_localized_keep_going():
    brain = DummyBrain()

    assert brain.localized_keep_going("en") == "Keep going!"
    assert brain.localized_keep_going("no") == "Fortsett!"


def test_persona_directives_include_role_character_humor():
    brain = DummyBrain()

    directives = brain.build_persona_directives(
        {"persona": "toxic_mode", "training_level": "advanced"},
        language="en",
        mode="realtime_coach",
    )

    assert "Persona role: toxic_mode drill-sergeant coach." in directives
    assert "Character: confrontational, high-energy, darkly humorous." in directives
    assert "Humor: sarcasm/playful roasting" in directives
    assert "Level: advanced, increase challenge and precision." not in directives


def test_persona_directives_default_to_personal_trainer():
    brain = DummyBrain()

    directives = brain.build_persona_directives(
        {"persona": "unknown_mode"},
        language="en",
        mode="chat",
    )

    assert "Persona role: personal_trainer elite endurance coach." in directives
    assert "Humor: light and rare, never sarcastic." in directives


def test_persona_directives_include_emotional_segment():
    brain = DummyBrain()

    directives = brain.build_persona_directives(
        {
            "persona": "toxic_mode",
            "training_level": "advanced",
            "persona_mode": "peak",
            "emotional_trend": "rising",
            "emotional_intensity": 0.82,
        },
        language="en",
        mode="realtime_coach",
    )

    assert "Emotional segment: mode=peak." in directives
    assert "Trend: rising." in directives
    assert "Emotional intensity: 0.82." in directives


def test_persona_directives_safety_override_forces_supportive_segment():
    brain = DummyBrain()

    directives = brain.build_persona_directives(
        {
            "persona": "toxic_mode",
            "safety_override": True,
            "persona_mode": "peak",
        },
        language="en",
        mode="realtime_coach",
    )

    assert "Emotional segment: SAFETY override active, force supportive mode now." in directives


def test_persona_directives_ignore_training_level_for_tone():
    brain = DummyBrain()

    beginner = brain.build_persona_directives(
        {"persona": "personal_trainer", "training_level": "beginner"},
        language="en",
        mode="realtime_coach",
    )
    advanced = brain.build_persona_directives(
        {"persona": "personal_trainer", "training_level": "advanced"},
        language="en",
        mode="realtime_coach",
    )

    assert beginner == advanced
