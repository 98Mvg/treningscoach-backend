import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brains.grok_brain import GrokBrain
import config


def _brain() -> GrokBrain:
    return GrokBrain(api_key="xai-test-key", model="grok-3-mini")


def test_realtime_prompt_includes_toxic_mode_rules():
    brain = _brain()
    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona="toxic_mode",
        training_level="intermediate",
    )

    assert "Persona mode: toxic_mode." in prompt
    assert "aggressive drill-sergeant" in prompt
    assert "Do not repeat the exact same cue" in prompt


def test_realtime_prompt_includes_personal_trainer_rules():
    brain = _brain()
    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona="personal_trainer",
        training_level="intermediate",
    )

    assert "Persona mode: personal_trainer." in prompt
    assert "calm and disciplined elite coach" in prompt
    assert "No sarcasm and no shouting." in prompt


def test_realtime_prompt_does_not_add_training_level_tone_rules():
    brain = _brain()
    prompt = brain._build_realtime_system_prompt(
        phase="warmup",
        intensity="calm",
        language="en",
        persona="toxic_mode",
        training_level="beginner",
    )

    assert "Beginner athlete: prioritize clarity and control over aggression." not in prompt
    assert "Advanced athlete: increase challenge and precision." not in prompt


def test_realtime_prompt_includes_emotional_segment_directives():
    brain = _brain()
    prompt = brain._build_realtime_system_prompt(
        phase="intense",
        intensity="moderate",
        language="en",
        persona="toxic_mode",
        training_level="advanced",
        persona_mode="peak",
        emotional_trend="rising",
        emotional_intensity=0.91,
        safety_override=False,
    )

    assert "Emotional segment: mode=peak." in prompt
    assert "Trend: rising." in prompt
    assert "Emotional intensity: 0.91." in prompt


def test_grok_client_disables_retries():
    brain = _brain()
    assert brain.client.max_retries == 0
    assert brain.async_client.max_retries == 0


def test_grok_timeout_for_realtime_stays_within_router_budget():
    brain = _brain()
    timeout = brain._timeout_for_mode("realtime_coach")
    router_budget = float(getattr(config, "BRAIN_TIMEOUTS", {}).get("grok", getattr(config, "BRAIN_TIMEOUT", 6.0)))
    assert timeout > 0
    assert timeout <= router_budget
