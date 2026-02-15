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
