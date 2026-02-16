"""Tests for brain init-retry with short cooldown and skip logging."""

import os
import sys
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_init_failure_uses_short_cooldown():
    """Init failure should use BRAIN_INIT_RETRY_SECONDS (5s), not the 60s runtime cooldown."""
    from brain_router import BrainRouter

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "config"]

    # Simulate init failure — _create_brain raises
    with patch.object(router, "_create_brain", side_effect=Exception("no API key")):
        result = router._get_brain_instance("grok")
        assert result is None

    # Check cooldown was set — should be short (<=10s), not the 60s runtime cooldown
    cooldown_until = router.brain_cooldowns.get("grok", 0)
    remaining = cooldown_until - time.time()
    assert remaining <= 10, f"Init cooldown too long: {remaining:.1f}s (expected <=10s)"
    assert remaining > 0, "Cooldown should be set (not zero)"


def test_init_failure_retries_after_short_cooldown():
    """After init cooldown expires, the brain should be retried (not stuck in cache)."""
    from brain_router import BrainRouter

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "config"]

    # First call: init fails
    call_count = {"n": 0}
    original_create = router._create_brain

    def failing_then_ok(name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("no API key")
        # Second call: succeed with a mock brain
        mock_brain = MagicMock()
        mock_brain.model = "grok-test"
        return mock_brain

    with patch.object(router, "_create_brain", side_effect=failing_then_ok):
        # First attempt: fails
        result1 = router._get_brain_instance("grok")
        assert result1 is None

        # Expire the cooldown immediately for testing
        router.brain_cooldowns["grok"] = time.time() - 1

        # Second attempt: should retry and succeed
        result2 = router._get_brain_instance("grok")
        assert result2 is not None, "Brain should have been retried after cooldown expired"

    assert call_count["n"] == 2, f"Expected 2 create attempts, got {call_count['n']}"


def test_skip_reason_logged_in_priority_response(capsys):
    """When a brain is skipped, the reason should be logged."""
    from brain_router import BrainRouter

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "config"]

    # Put grok on cooldown so it's skipped
    router.brain_cooldowns["grok"] = time.time() + 300

    # Call priority response — grok should be skipped with a log message
    breath = {"intensity": "moderate", "volume": 0.3, "tempo": 12.0}
    result = router._get_priority_response(breath, "warmup", "realtime_coach", "en", None)

    captured = capsys.readouterr()
    # Should contain skip log with brain name and reason
    assert "grok" in captured.out.lower() or "SKIP" in captured.out, \
        f"Expected skip log for grok, got: {captured.out!r}"


def test_pool_status_in_health_check():
    """health_check() should include pool_status showing which brains are cached."""
    from brain_router import BrainRouter

    router = BrainRouter(brain_type="config")
    router.use_priority_routing = True
    router.priority_brains = ["grok", "gemini", "openai", "claude"]

    # Simulate grok in pool (failed init)
    router.brain_pool["grok"] = None
    router.brain_cooldowns["grok"] = time.time() + 30

    # Simulate gemini in pool (successful init)
    mock_gemini = MagicMock()
    mock_gemini.health_check.return_value = True
    router.brain_pool["gemini"] = mock_gemini

    health = router.health_check()

    assert "pool_status" in health, f"health_check() missing pool_status, got keys: {list(health.keys())}"
    pool = health["pool_status"]
    assert "grok" in pool, f"pool_status should include grok, got: {pool}"
    assert pool["grok"] == "failed_init", f"grok should be 'failed_init', got: {pool['grok']}"
    assert pool["gemini"] == "ready", f"gemini should be 'ready', got: {pool['gemini']}"
