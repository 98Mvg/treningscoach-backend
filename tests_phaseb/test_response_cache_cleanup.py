import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from response_cache import ResponseCache


def test_periodic_cleanup_evicts_expired_entries():
    cache = ResponseCache(ttl_seconds=0)
    cache._cleanup_interval_ops = 1

    cache.set(
        intensity="moderate",
        phase="intense",
        tempo=20.0,
        volume=40.0,
        text="Keep going!",
    )
    assert len(cache.cache) == 1

    time.sleep(0.001)
    hit = cache.get(
        intensity="moderate",
        phase="intense",
        tempo=20.0,
        volume=40.0,
    )

    assert hit is None
    assert len(cache.cache) == 0
