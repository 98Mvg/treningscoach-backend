"""
Coaching decision pipeline for /coach/continuous.

Single ordered decision chain:
1) zone event decision
2) breath logic decision
3) phase fallback decision
4) max silence override (except unified zone-owner path)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import config


@dataclass
class CoachingDecision:
    speak: bool
    reason: str
    owner: str
    owner_base: str
    zone_forced_text: Optional[str] = None
    max_silence_override_used: bool = False
    events: Optional[List[Dict[str, Any]]] = None
    mark_first_breath_consumed: bool = False
    mark_use_welcome_phrase: bool = False


def run(
    *,
    is_first_breath: bool,
    zone_mode_active: bool,
    zone_tick: Optional[Dict[str, Any]],
    breath_quality_state: str,
    speech_decision_owner_v2: bool,
    unified_zone_router_active: bool,
    voice_intelligence: Any,
    should_coach_speak_fn: Callable[..., Tuple[bool, str]],
    apply_max_silence_override_fn: Callable[..., Tuple[bool, str]],
    phase_fallback_interval_seconds_fn: Callable[[str], float],
    breath_data: Dict[str, Any],
    phase: str,
    last_coaching: str,
    elapsed_seconds: int,
    last_breath: Optional[Dict[str, Any]],
    coaching_history: List[Dict[str, Any]],
    training_level: str,
    session_id: str,
    elapsed_since_last: Optional[float],
    max_silence_seconds: float,
) -> CoachingDecision:
    zone_forced_text = (zone_tick or {}).get("coach_text") if isinstance(zone_tick, dict) else None
    max_silence_override_used = False

    if is_first_breath:
        return CoachingDecision(
            speak=True,
            reason="welcome_message",
            owner="welcome",
            owner_base="welcome",
            zone_forced_text=zone_forced_text,
            max_silence_override_used=False,
            events=(zone_tick or {}).get("events") if isinstance(zone_tick, dict) else [],
            mark_first_breath_consumed=True,
            mark_use_welcome_phrase=True,
        )

    if speech_decision_owner_v2:
        if zone_mode_active and zone_tick is not None:
            owner_base = "zone_event"
            speak_decision = bool(zone_tick.get("should_speak"))
            reason = zone_tick.get("primary_event_type") or zone_tick.get("reason") or "zone_no_change"
        elif breath_quality_state == "reliable":
            owner_base = "breath_logic"
            should_be_silent, silence_reason = voice_intelligence.should_stay_silent(
                breath_data=breath_data,
                phase=phase,
                last_coaching=last_coaching,
                elapsed_seconds=elapsed_seconds,
                session_id=session_id,
            )
            if should_be_silent:
                speak_decision = False
                reason = silence_reason
            else:
                speak_decision, reason = should_coach_speak_fn(
                    current_analysis=breath_data,
                    last_analysis=last_breath,
                    coaching_history=coaching_history,
                    phase=phase,
                    training_level=training_level,
                    elapsed_seconds=elapsed_seconds,
                )
        else:
            owner_base = "phase_fallback"
            fallback_interval = phase_fallback_interval_seconds_fn(phase)
            if elapsed_since_last is None or elapsed_since_last >= fallback_interval:
                speak_decision = True
                reason = "phase_fallback_interval"
            else:
                speak_decision = False
                reason = "phase_fallback_wait"

        if unified_zone_router_active and owner_base == "zone_event":
            owner = owner_base
        else:
            pre_override_speak = bool(speak_decision)
            speak_decision, reason = apply_max_silence_override_fn(
                should_speak=speak_decision,
                reason=reason,
                elapsed_since_last=elapsed_since_last,
                max_silence_seconds=max_silence_seconds,
            )
            if (not pre_override_speak) and speak_decision and reason == "max_silence_override":
                max_silence_override_used = True
                owner = "max_silence_override"
            else:
                owner = owner_base
            if (
                speak_decision
                and reason == "max_silence_override"
                and zone_mode_active
                and zone_tick is not None
                and not zone_forced_text
            ):
                zone_forced_text = zone_tick.get("max_silence_text")
    else:
        if zone_mode_active and zone_tick is not None:
            speak_decision = bool(zone_tick.get("should_speak"))
            reason = zone_tick.get("reason") or "zone_no_change"
            owner_base = "zone_event"
        else:
            should_be_silent, silence_reason = voice_intelligence.should_stay_silent(
                breath_data=breath_data,
                phase=phase,
                last_coaching=last_coaching,
                elapsed_seconds=elapsed_seconds,
                session_id=session_id,
            )

            if should_be_silent:
                min_quality = getattr(config, "MIN_SIGNAL_QUALITY_TO_FORCE", 0.0)
                signal_quality = breath_data.get("signal_quality") or 0.0
                if (
                    elapsed_since_last is not None
                    and elapsed_since_last >= max_silence_seconds
                    and signal_quality >= min_quality
                ):
                    speak_decision = True
                    reason = "max_silence_override"
                else:
                    speak_decision = False
                    reason = silence_reason
            else:
                speak_decision, reason = should_coach_speak_fn(
                    current_analysis=breath_data,
                    last_analysis=last_breath,
                    coaching_history=coaching_history,
                    phase=phase,
                    training_level=training_level,
                    elapsed_seconds=elapsed_seconds,
                )
            owner_base = "breath_logic"

        pre_override_speak = bool(speak_decision)
        speak_decision, reason = apply_max_silence_override_fn(
            should_speak=speak_decision,
            reason=reason,
            elapsed_since_last=elapsed_since_last,
            max_silence_seconds=max_silence_seconds,
        )
        if (not pre_override_speak) and speak_decision and reason == "max_silence_override":
            max_silence_override_used = True
            owner = "max_silence_override"
        else:
            owner = owner_base
        if (
            speak_decision
            and reason == "max_silence_override"
            and zone_mode_active
            and zone_tick is not None
            and not zone_forced_text
        ):
            zone_forced_text = zone_tick.get("max_silence_text")

    return CoachingDecision(
        speak=bool(speak_decision),
        reason=str(reason or "none"),
        owner=str(owner),
        owner_base=str(owner_base),
        zone_forced_text=zone_forced_text,
        max_silence_override_used=bool(max_silence_override_used),
        events=(zone_tick or {}).get("events") if isinstance(zone_tick, dict) else [],
    )
