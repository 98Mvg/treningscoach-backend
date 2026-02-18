import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_router import BrainRouter


def test_prune_expired_cooldowns_removes_only_stale_entries():
    router = BrainRouter(brain_type="config")
    now = time.time()
    router.brain_cooldowns = {
        "grok": now - 1,
        "config": now + 60,
    }

    router._prune_expired_cooldowns()

    assert "grok" not in router.brain_cooldowns
    assert "config" in router.brain_cooldowns
