import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brains.openai_brain import OpenAIBrain
from brains.claude_brain import ClaudeBrain
from brains.gemini_brain import GeminiBrain


def _hint(brain):
    return brain.build_persona_directives(
        {
            "persona": "toxic_mode",
            "training_level": "advanced",
            "persona_mode": "intense",
            "emotional_trend": "rising",
            "emotional_intensity": 0.66,
        },
        language="en",
        mode="realtime_coach",
    )


def test_openai_prompt_includes_persona_directives():
    brain = OpenAIBrain.__new__(OpenAIBrain)
    hint = _hint(brain)

    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona_directives=hint,
    )

    assert "Persona role: toxic_mode drill-sergeant coach." in prompt
    assert "darkly humorous" in prompt
    assert "Emotional segment: mode=intense." in prompt


def test_claude_prompt_includes_persona_directives():
    brain = ClaudeBrain.__new__(ClaudeBrain)
    hint = _hint(brain)

    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona_directives=hint,
    )

    assert "Persona role: toxic_mode drill-sergeant coach." in prompt
    assert "darkly humorous" in prompt
    assert "Emotional segment: mode=intense." in prompt


def test_gemini_prompt_includes_persona_directives():
    brain = GeminiBrain.__new__(GeminiBrain)
    hint = _hint(brain)

    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona_directives=hint,
    )

    assert "Persona role: toxic_mode drill-sergeant coach." in prompt
    assert "darkly humorous" in prompt
    assert "Emotional segment: mode=intense." in prompt
