"""
Phase 5 personalization store for running/interval zone coaching.

Design constraints:
- Insights only in v1 (no mutation of event decisions/cooldowns/scoring)
- Small durable profile per user
- Deterministic updates from deterministic zone metrics
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from statistics import median
from typing import Any, Dict, Optional


class RunningPersonalizationStore:
    """Persist lightweight running personalization signals."""

    def __init__(
        self,
        storage_path: str = "zone_personalization.json",
        max_recovery_samples: int = 24,
        max_session_history: int = 20,
    ) -> None:
        self.storage_path = storage_path
        self.max_recovery_samples = max(6, int(max_recovery_samples))
        self.max_session_history = max(6, int(max_session_history))
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _default_profile(self) -> Dict[str, Any]:
        return {
            "sessions_completed": 0,
            "recovery_samples": [],
            "session_scores": [],
            "session_time_in_target": [],
            "session_overshoots": [],
            "recovery_baseline_seconds": None,
            "aggressiveness": "neutral",
            "last_tip": "",
            "updated_at": None,
        }

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            self._profiles = {}
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                self._profiles = payload
            else:
                self._profiles = {}
        except Exception:
            self._profiles = {}

    def _save(self) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as handle:
                json.dump(self._profiles, handle, indent=2, ensure_ascii=True)
        except Exception:
            # Personalization should never block runtime coaching.
            pass

    @staticmethod
    def _normalized_user_id(user_id: Optional[str]) -> Optional[str]:
        if user_id is None:
            return None
        cleaned = str(user_id).strip().lower()
        if not cleaned:
            return None
        return cleaned[:128]

    def get_profile(self, user_id: Optional[str]) -> Dict[str, Any]:
        key = self._normalized_user_id(user_id)
        if not key:
            return self._default_profile()
        existing = self._profiles.get(key)
        if isinstance(existing, dict):
            profile = self._default_profile()
            profile.update(existing)
            return profile
        return self._default_profile()

    @staticmethod
    def _append_capped(values: list, item: Any, max_items: int) -> None:
        values.append(item)
        if len(values) > max_items:
            del values[:-max_items]

    @staticmethod
    def _avg(values: list) -> Optional[float]:
        cleaned = [float(v) for v in values if v is not None]
        if not cleaned:
            return None
        return sum(cleaned) / float(len(cleaned))

    def _derive_aggressiveness(self, profile: Dict[str, Any]) -> str:
        avg_overshoots = self._avg(profile.get("session_overshoots", []))
        avg_time_in_target = self._avg(profile.get("session_time_in_target", []))

        if avg_overshoots is not None and avg_overshoots >= 3.0:
            return "conservative"
        if avg_time_in_target is not None and avg_time_in_target < 65.0:
            return "conservative"
        if avg_overshoots is not None and avg_overshoots <= 1.0:
            if avg_time_in_target is not None and avg_time_in_target >= 82.0:
                return "pushy"
        return "neutral"

    def build_next_time_tip(
        self,
        *,
        language: str,
        time_in_target_pct: Optional[float],
        overshoots: Optional[int],
        recovery_avg_seconds: Optional[float],
        recovery_baseline_seconds: Optional[float],
        aggressiveness: str,
    ) -> str:
        lang = "no" if str(language).strip().lower() == "no" else "en"

        if overshoots is not None and overshoots >= 3:
            return (
                "Start 5 bpm lower first 10 minutes."
                if lang != "no"
                else "Start 5 bpm lavere de første 10 minuttene."
            )

        if time_in_target_pct is not None and time_in_target_pct < 70:
            return (
                "Hold back on hills; shorten stride."
                if lang != "no"
                else "Hold litt igjen i bakker; kort ned steget."
            )

        if (
            recovery_avg_seconds is not None
            and recovery_baseline_seconds is not None
            and recovery_avg_seconds >= (recovery_baseline_seconds + 6.0)
        ):
            return (
                "Take 20-30s easier recovery between surges."
                if lang != "no"
                else "Ta 20-30 sek roligere mellom drag."
            )

        if aggressiveness == "pushy":
            return (
                "You can add a slight push in the middle block."
                if lang != "no"
                else "Du kan legge inn et lite ekstra trykk i midtblokken."
            )

        return (
            "Keep this pacing discipline next run."
            if lang != "no"
            else "Hold denne pacing-disiplinen i neste økt."
        )

    def build_recovery_line(
        self,
        *,
        language: str,
        recovery_avg_seconds: Optional[float],
        recovery_baseline_seconds: Optional[float],
    ) -> Optional[str]:
        if recovery_avg_seconds is None or recovery_baseline_seconds is None:
            return None

        lang = "no" if str(language).strip().lower() == "no" else "en"
        delta = round(recovery_baseline_seconds - recovery_avg_seconds, 1)
        if abs(delta) < 2.0:
            return (
                "Recovery was on your baseline today."
                if lang != "no"
                else "Restitusjonen var rundt normalen din i dag."
            )
        if delta > 0:
            return (
                f"Recovery {abs(delta):.0f}s faster than your baseline."
                if lang != "no"
                else f"Restitusjon {abs(delta):.0f}s raskere enn normalen din."
            )
        return (
            f"Recovery {abs(delta):.0f}s slower than your baseline."
            if lang != "no"
            else f"Restitusjon {abs(delta):.0f}s tregere enn normalen din."
        )

    def record_session(
        self,
        *,
        user_id: Optional[str],
        language: str,
        score: Optional[int],
        time_in_target_pct: Optional[float],
        overshoots: Optional[int],
        recovery_avg_seconds: Optional[float],
    ) -> Dict[str, Any]:
        key = self._normalized_user_id(user_id)
        if not key:
            return {
                "profile": self._default_profile(),
                "next_time_tip": "",
                "recovery_line": None,
            }

        profile = self.get_profile(key)
        profile["sessions_completed"] = int(profile.get("sessions_completed", 0)) + 1

        if recovery_avg_seconds is not None:
            self._append_capped(
                profile.setdefault("recovery_samples", []),
                round(float(recovery_avg_seconds), 1),
                self.max_recovery_samples,
            )
        if score is not None:
            self._append_capped(
                profile.setdefault("session_scores", []),
                int(score),
                self.max_session_history,
            )
        if time_in_target_pct is not None:
            self._append_capped(
                profile.setdefault("session_time_in_target", []),
                round(float(time_in_target_pct), 1),
                self.max_session_history,
            )
        if overshoots is not None:
            self._append_capped(
                profile.setdefault("session_overshoots", []),
                int(overshoots),
                self.max_session_history,
            )

        recovery_samples = [float(v) for v in profile.get("recovery_samples", []) if v is not None]
        if recovery_samples:
            profile["recovery_baseline_seconds"] = round(float(median(recovery_samples)), 1)
        else:
            profile["recovery_baseline_seconds"] = None

        profile["aggressiveness"] = self._derive_aggressiveness(profile)
        next_tip = self.build_next_time_tip(
            language=language,
            time_in_target_pct=time_in_target_pct,
            overshoots=overshoots,
            recovery_avg_seconds=recovery_avg_seconds,
            recovery_baseline_seconds=profile.get("recovery_baseline_seconds"),
            aggressiveness=profile.get("aggressiveness", "neutral"),
        )
        profile["last_tip"] = next_tip
        profile["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        self._profiles[key] = profile
        self._save()

        return {
            "profile": profile,
            "next_time_tip": next_tip,
            "recovery_line": self.build_recovery_line(
                language=language,
                recovery_avg_seconds=recovery_avg_seconds,
                recovery_baseline_seconds=profile.get("recovery_baseline_seconds"),
            ),
        }
