import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def test_brain_priority_env_override(monkeypatch):
    monkeypatch.setenv("BRAIN_PRIORITY", "grok,openai,gemini,claude")
    monkeypatch.setenv("ACTIVE_BRAIN", "grok")
    monkeypatch.setenv("USE_PRIORITY_ROUTING", "true")

    importlib.reload(config)

    assert config.BRAIN_PRIORITY == ["grok", "openai", "gemini", "claude"]
    assert config.ACTIVE_BRAIN == "grok"
    assert config.USE_PRIORITY_ROUTING is True


def test_timeout_and_threshold_json_overrides(monkeypatch):
    monkeypatch.setenv("BRAIN_TIMEOUTS_JSON", '{"grok": 5.5, "openai": 2.2}')
    monkeypatch.setenv("BRAIN_SLOW_THRESHOLDS_JSON", '{"grok": 7.0}')
    monkeypatch.setenv("BRAIN_MODE_TIMEOUTS_JSON", '{"realtime_coach": {"grok": 4.6}}')

    importlib.reload(config)

    assert config.BRAIN_TIMEOUTS["grok"] == 5.5
    assert config.BRAIN_TIMEOUTS["openai"] == 2.2
    assert config.BRAIN_SLOW_THRESHOLDS["grok"] == 7.0
    assert config.BRAIN_MODE_TIMEOUTS["realtime_coach"]["grok"] == 4.6


def test_latency_strategy_env_overrides(monkeypatch):
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", "3.4")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_MIN_CALLS", "5")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS", "18")

    importlib.reload(config)

    assert config.LATENCY_FAST_FALLBACK_ENABLED is False
    assert config.LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS == 3.4
    assert config.LATENCY_FAST_FALLBACK_MIN_CALLS == 5
    assert config.LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS == 18.0


def test_zone_layer_env_overrides(monkeypatch):
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_ENABLED", "true")
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS", "1.1")
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_MAX_WORDS", "12")
    monkeypatch.setenv("ZONE_PERSONALIZATION_ENABLED", "false")
    monkeypatch.setenv("ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES", "18")

    importlib.reload(config)

    assert config.ZONE_EVENT_LLM_REWRITE_ENABLED is True
    assert config.ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS == 1.1
    assert config.ZONE_EVENT_LLM_REWRITE_MAX_WORDS == 12
    assert config.ZONE_PERSONALIZATION_ENABLED is False
    assert config.ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES == 18


def test_launch_lock_env_overrides(monkeypatch):
    monkeypatch.setenv("DEFAULT_LANGUAGE", "no")
    monkeypatch.setenv("MIN_SIGNAL_QUALITY_TO_FORCE", "0.2")
    monkeypatch.setenv("COACHING_VALIDATION_ENFORCE", "true")
    monkeypatch.setenv("BREATHING_TIMELINE_ENFORCE", "false")
    monkeypatch.setenv("USE_HYBRID_BRAIN", "false")

    importlib.reload(config)

    assert config.DEFAULT_LANGUAGE == "no"
    assert config.MIN_SIGNAL_QUALITY_TO_FORCE == 0.2
    assert config.COACHING_VALIDATION_ENFORCE is True
    assert config.BREATHING_TIMELINE_ENFORCE is False
    assert config.USE_HYBRID_BRAIN is False


def test_monetization_free_mode_lock(monkeypatch):
    monkeypatch.setenv("APP_FREE_MODE", "true")
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("PREMIUM_SURFACES_ENABLED", "true")

    importlib.reload(config)

    assert config.APP_FREE_MODE is True
    # Free mode must hard-lock paid surfaces off, regardless of env intent.
    assert config.BILLING_ENABLED is False
    assert config.PREMIUM_SURFACES_ENABLED is False


def test_monetization_can_be_enabled_later(monkeypatch):
    monkeypatch.setenv("APP_FREE_MODE", "false")
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("PREMIUM_SURFACES_ENABLED", "true")

    importlib.reload(config)

    assert config.APP_FREE_MODE is False
    assert config.BILLING_ENABLED is True
    assert config.PREMIUM_SURFACES_ENABLED is True


def test_coach_score_version_env_override(monkeypatch):
    monkeypatch.setenv("COACH_SCORE_VERSION", "shadow")
    monkeypatch.setenv("SPEECH_DECISION_OWNER_V2", "false")
    importlib.reload(config)
    assert config.COACH_SCORE_VERSION == "shadow"
    assert config.SPEECH_DECISION_OWNER_V2 is False

    monkeypatch.setenv("COACH_SCORE_VERSION", "invalid")
    importlib.reload(config)
    assert config.COACH_SCORE_VERSION == "cs_v2"
