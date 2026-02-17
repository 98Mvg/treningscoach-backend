import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_manager import PersonaManager


def test_persona_manager_prompt_ignores_training_level():
    beginner = PersonaManager.get_system_prompt(
        persona="personal_trainer",
        language="en",
        training_level="beginner",
    )
    advanced = PersonaManager.get_system_prompt(
        persona="personal_trainer",
        language="en",
        training_level="advanced",
    )

    assert beginner == advanced
    assert "Training level context:" not in beginner
