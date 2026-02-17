import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from brain_router import BrainRouter


class _FakeBrain:
    def get_realtime_coaching(self, breath_data, phase):
        return "ai cue"

    def get_coaching_response(self, breath_data, phase):
        return "chat cue"


class _RepeatBrain:
    def get_realtime_coaching(self, breath_data, phase):
        return "Push harder."


def test_per_brain_timeout_override_for_grok(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_TIMEOUT", 1.2, raising=False)
    monkeypatch.setattr(config, "BRAIN_TIMEOUTS", {"grok": 6.0}, raising=False)
    monkeypatch.setattr(config, "BRAIN_MODE_TIMEOUTS", {}, raising=False)

    router = BrainRouter(brain_type="config")

    assert router._get_brain_timeout("grok", "realtime_coach") == 6.0
    assert router._get_brain_timeout("openai", "realtime_coach") == 1.2


def test_mode_timeout_override_takes_precedence(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_TIMEOUT", 1.2, raising=False)
    monkeypatch.setattr(config, "BRAIN_TIMEOUTS", {"grok": 6.0}, raising=False)
    monkeypatch.setattr(
        config,
        "BRAIN_MODE_TIMEOUTS",
        {"realtime_coach": {"grok": 5.5, "default": 1.5}},
        raising=False,
    )

    router = BrainRouter(brain_type="config")

    assert router._get_brain_timeout("grok", "realtime_coach") == 5.5
    assert router._get_brain_timeout("openai", "realtime_coach") == 1.5
    assert router._get_brain_timeout("openai", "chat") == 1.2


def test_per_brain_slow_threshold_override_keeps_grok_available(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_SLOW_THRESHOLD", 3.0, raising=False)
    monkeypatch.setattr(config, "BRAIN_SLOW_THRESHOLDS", {"grok": 6.5}, raising=False)

    router = BrainRouter(brain_type="config")
    router.brain_stats["grok"] = {"avg_latency": 4.8}
    router.brain_stats["openai"] = {"avg_latency": 4.8}

    assert router._is_brain_available("grok") is True
    assert router._is_brain_available("openai") is False


def test_route_metadata_reports_selected_ai_provider(monkeypatch):
    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok"]

    monkeypatch.setattr(router, "_is_brain_available", lambda _: True)
    monkeypatch.setattr(router, "_get_brain_instance", lambda _: _FakeBrain())

    result = router.get_coaching_response({}, mode="realtime_coach", language="en")
    meta = router.get_last_route_meta()

    assert result == "ai cue"
    assert meta["provider"] == "grok"
    assert meta["source"] == "ai"
    assert meta["status"] == "success"


def test_route_metadata_reports_config_fallback_after_failure(monkeypatch):
    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok"]

    monkeypatch.setattr(router, "_is_brain_available", lambda _: True)
    monkeypatch.setattr(router, "_get_brain_instance", lambda _: _FakeBrain())

    def _fail_call(brain_name, fn, timeout):
        router.brain_last_outcome[brain_name] = {"status": "timeout", "timeout": timeout}
        return None

    monkeypatch.setattr(router, "_call_brain_with_timeout", _fail_call)

    _ = router.get_coaching_response({}, mode="realtime_coach", language="en")
    meta = router.get_last_route_meta()

    assert meta["provider"] == "config"
    assert meta["source"] == "config_fallback"
    assert meta["status"] == "all_brains_failed_or_skipped"


def test_gemini_quota_error_gets_longer_cooldown(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_COOLDOWN_SECONDS", 60.0, raising=False)
    monkeypatch.setattr(config, "BRAIN_QUOTA_COOLDOWN_SECONDS", 300.0, raising=False)

    router = BrainRouter(brain_type="config")
    cooldown = router._get_failure_cooldown_seconds(
        "gemini",
        RuntimeError("quota exceeded retry_delay { seconds: 24 }"),
    )

    assert cooldown == 300.0
    assert router._get_failure_cooldown_seconds("grok", RuntimeError("quota")) is None


def test_realtime_response_rewrites_recent_repeats(monkeypatch):
    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok"]

    monkeypatch.setattr(router, "_is_brain_available", lambda _: True)
    monkeypatch.setattr(router, "_get_brain_instance", lambda _: _RepeatBrain())
    monkeypatch.setattr(router, "_get_config_response", lambda *args, **kwargs: "Hold rhythm.")

    first = router.get_coaching_response({"session_id": "s1"}, mode="realtime_coach", language="en")
    second = router.get_coaching_response({"session_id": "s1"}, mode="realtime_coach", language="en")

    assert first == "Push harder."
    assert second == "Hold rhythm."


def test_latency_fallback_signal_triggers_when_avg_latency_is_high(monkeypatch):
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", 2.8, raising=False)
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_MIN_CALLS", 2, raising=False)

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "config"]
    router.brain_stats["grok"] = {"calls": 4, "avg_latency": 3.6, "timeouts": 0, "failures": 0}

    signal = router.get_latency_fallback_signal()

    assert signal["should_fallback"] is True
    assert signal["provider"] == "grok"
    assert signal["reason"] == "latency_high"
    assert signal["calls"] == 4


def test_latency_fallback_signal_requires_minimum_samples(monkeypatch):
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", 2.8, raising=False)
    monkeypatch.setattr(config, "LATENCY_FAST_FALLBACK_MIN_CALLS", 3, raising=False)

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "config"]
    router.brain_stats["grok"] = {"calls": 2, "avg_latency": 4.2, "timeouts": 0, "failures": 0}

    signal = router.get_latency_fallback_signal()

    assert signal["should_fallback"] is False
    assert signal["reason"] == "insufficient_samples"


def test_fast_fallback_response_sets_route_metadata():
    router = BrainRouter(brain_type="config")
    text = router.get_fast_fallback_response(
        breath_data={"intensity": "moderate"},
        phase="intense",
        language="en",
        persona="personal_trainer",
    )
    meta = router.get_last_route_meta()

    assert isinstance(text, str) and len(text) > 0
    assert meta["provider"] == "system"
    assert meta["source"] == "latency_fast_fallback"
    assert meta["status"] == "fast_fallback"
