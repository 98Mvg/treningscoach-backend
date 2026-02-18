#
# response_cache.py
# Smart caching for coaching responses
#
# Cache Strategy:
# - Same breath pattern + phase → Same response (no Claude call)
# - Uses TTL to prevent stale responses
# - Memory-based cache (fast, simple)
#

import hashlib
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class CachedResponse:
    """Cached coaching response with metadata."""
    text: str
    audio_bytes: Optional[bytes]
    timestamp: float
    hit_count: int = 0


class ResponseCache:
    """
    Smart cache for coaching responses.

    Cache Key Strategy:
    - Bucket tempo into ranges (avoid cache misses for minor variations)
    - Use intensity + phase as primary key
    - TTL to prevent stale responses
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize response cache.

        Args:
            ttl_seconds: Time-to-live for cached responses (default: 1 hour)
        """
        self.cache: Dict[str, CachedResponse] = {}
        self.ttl_seconds = ttl_seconds
        self._ops_since_cleanup = 0
        self._cleanup_interval_ops = 100
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _maybe_clear_expired(self):
        """Run periodic expired-entry cleanup without adding timer threads."""
        self._ops_since_cleanup += 1
        if self._ops_since_cleanup >= self._cleanup_interval_ops:
            self.clear_expired()
            self._ops_since_cleanup = 0

    def _bucket_tempo(self, tempo: float) -> str:
        """
        Bucket tempo into ranges to improve cache hit rate.

        Instead of exact tempo (15.3 vs 15.5), use buckets:
        - 0-10: "very_slow"
        - 10-20: "slow"
        - 20-30: "moderate"
        - 30-40: "fast"
        - 40+: "very_fast"
        """
        if tempo < 10:
            return "very_slow"
        elif tempo < 20:
            return "slow"
        elif tempo < 30:
            return "moderate"
        elif tempo < 40:
            return "fast"
        else:
            return "very_fast"

    def _bucket_volume(self, volume: float) -> str:
        """
        Bucket volume into ranges.

        - 0-30: "quiet"
        - 30-60: "normal"
        - 60+: "loud"
        """
        if volume < 30:
            return "quiet"
        elif volume < 60:
            return "normal"
        else:
            return "loud"

    def _generate_key(
        self,
        intensity: str,
        phase: str,
        tempo: float,
        volume: float,
        mode: str = "realtime_coach"
    ) -> str:
        """
        Generate cache key from breath metrics.

        Key format: "intensity_phase_tempo_bucket_volume_bucket_mode"
        Example: "moderate_intense_slow_normal_realtime_coach"
        """
        tempo_bucket = self._bucket_tempo(tempo)
        volume_bucket = self._bucket_volume(volume)

        key_parts = [
            intensity,
            phase,
            tempo_bucket,
            volume_bucket,
            mode
        ]

        return "_".join(key_parts)

    def get(
        self,
        intensity: str,
        phase: str,
        tempo: float,
        volume: float,
        mode: str = "realtime_coach"
    ) -> Optional[CachedResponse]:
        """
        Get cached response if available and not expired.

        Returns:
            CachedResponse if cache hit, None if miss
        """
        self._maybe_clear_expired()
        key = self._generate_key(intensity, phase, tempo, volume, mode)

        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        cached = self.cache[key]

        # Check if expired
        age = time.time() - cached.timestamp
        if age > self.ttl_seconds:
            # Expired - remove and return miss
            del self.cache[key]
            self.stats["evictions"] += 1
            self.stats["misses"] += 1
            return None

        # Cache hit!
        cached.hit_count += 1
        self.stats["hits"] += 1

        return cached

    def set(
        self,
        intensity: str,
        phase: str,
        tempo: float,
        volume: float,
        text: str,
        audio_bytes: Optional[bytes] = None,
        mode: str = "realtime_coach"
    ):
        """
        Store response in cache.

        Args:
            intensity: Breath intensity
            phase: Workout phase
            tempo: Breathing tempo
            volume: Breath volume
            text: Coaching text
            audio_bytes: Generated audio (optional)
            mode: Coach mode
        """
        self._maybe_clear_expired()
        key = self._generate_key(intensity, phase, tempo, volume, mode)

        self.cache[key] = CachedResponse(
            text=text,
            audio_bytes=audio_bytes,
            timestamp=time.time(),
            hit_count=0
        )

    def clear_expired(self):
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [
            key for key, cached in self.cache.items()
            if (now - cached.timestamp) > self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, size, etc.
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate_percent": round(hit_rate, 1),
            "cache_size": len(self.cache),
            "most_popular": self._get_most_popular()
        }

    def _get_most_popular(self) -> Dict[str, int]:
        """Get top 5 most hit cache entries."""
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].hit_count,
            reverse=True
        )[:5]

        return {
            key: cached.hit_count
            for key, cached in sorted_entries
        }

    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }


# Global cache instance
_response_cache = ResponseCache(ttl_seconds=3600)  # 1 hour TTL


def get_cache() -> ResponseCache:
    """Get global cache instance."""
    return _response_cache
