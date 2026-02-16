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
