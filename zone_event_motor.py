"""
Deterministic HR zone event motor for running workouts.

Design goals:
- Stable decisions (same inputs -> same events)
- Persona-agnostic decision logic
- Coaching style only affects cue frequency/tone (never decision outcome)
"""

from __future__ import annotations

import json
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from breath_reliability import summarize_breath_quality, is_breath_quality_reliable
from phrase_review_v2 import build_runtime_event_phrase_map, get_workout_phrase_text
from workout_cue_catalog import (
    event_cooldown_key,
    get_event_catalog,
    get_event_instruction_urgency,
)


logger = logging.getLogger(__name__)

# Event types that use phrase_id-based cached audio (no backend coach_text needed).
_MOTIVATION_EVENT_TYPES = (
    "interval_in_target_sustained",
    "easy_run_in_target_sustained",
    "max_silence_motivation",
)

_STRUCTURE_INSTRUCTION_EVENT_TYPES = (
    "structure_instruction_work",
    "structure_instruction_recovery",
    "structure_instruction_steady",
    "structure_instruction_finish",
)

_FALLBACK_TONE_EVENT_TYPES = (
    "max_silence_breath_guide",
    "max_silence_go_by_feel",
)

_STRUCTURE_INSTRUCTION_PHRASE_IDS = {
    "structure_instruction_work": ("zone.structure.work.1",),
    "structure_instruction_recovery": ("zone.structure.recovery.1",),
    "structure_instruction_steady": (
        "zone.structure.steady.1",
        "zone.structure.steady.2",
        "zone.structure.steady.3",
        "zone.structure.steady.4",
        "zone.structure.steady.5",
        "zone.structure.steady.6",
    ),
    "structure_instruction_finish": ("zone.structure.finish.1",),
}

_MOTIVATION_TONE_BUCKET_PHRASE_IDS = {
    "interval": {
        "calm": (
            "interval.motivate.s1.1",
            "interval.motivate.s2.2",
            "interval.motivate.s3.2",
        ),
        "neutral": (
            "interval.motivate.s1.2",
            "interval.motivate.s2.1",
            "interval.motivate.s2.2",
        ),
        "push": (
            "interval.motivate.s3.1",
            "interval.motivate.s3.2",
            "interval.motivate.s4.1",
            "interval.motivate.s4.2",
        ),
    },
    "easy_run": {
        "calm": (
            "easy_run.motivate.s1.1",
            "easy_run.motivate.s1.2",
            "easy_run.motivate.s4.1",
        ),
        "neutral": (
            "easy_run.motivate.s2.1",
            "easy_run.motivate.s2.2",
            "easy_run.motivate.s4.2",
        ),
        "supportive": (
            "easy_run.motivate.s3.1",
            "easy_run.motivate.s3.2",
        ),
    },
}

_FALLBACK_TONE_BUCKET_PHRASE_IDS = {
    "neutral": (
        "zone.silence.work.1",
        "zone.silence.default.1",
    ),
    "calm": (
        "zone.silence.rest.1",
        "zone.silence.default.1",
    ),
}

_RUNTIME_REVIEW_EVENT_KEYS = {
    "warmup_started": "warmup",
    "main_started": "main_started",
    "cooldown_started": "cooldown",
    "workout_finished": "workout_finish",
    "entered_target": "in_zone",
    "exited_target_above": "above_zone",
    "exited_target_below": "below_zone",
    "hr_signal_lost": "hr_signal_lost",
    "hr_signal_restored": "hr_signal_restored",
    "hr_structure_mode_notice": "no_hr_mode_notice",
    "pause_detected": "pause_detected",
    "pause_resumed": "pause_resumed",
    "interval_countdown_30": "countdown_30",
    "interval_countdown_10": "countdown_10",
    "interval_countdown_15": "countdown_15",
    "interval_countdown_5": "countdown_5",
    "interval_countdown_start": "countdown_start",
    "interval_countdown_halfway": "countdown_halfway",
    "interval_countdown_session_halfway": "countdown_session_halfway",
}

_RUNTIME_REVIEW_EVENT_PHRASE_MAP = build_runtime_event_phrase_map()

_STYLE_ALIASES = {
    "easy": "minimal",
    "min": "minimal",
    "minimal": "minimal",
    "medium": "normal",
    "normal": "normal",
    "hard": "motivational",
    "motivational": "motivational",
    "motivation": "motivational",
    "coachy": "motivational",
}

_HRMAX_ZONE_PCT = {
    "Z1": (0.60, 0.70),
    "Z2": (0.70, 0.80),
    "Z3": (0.80, 0.87),
    "Z4": (0.87, 0.93),
    "Z5": (0.93, 1.00),
}

_HRR_ZONE_PCT = {
    "Z1": (0.50, 0.60),
    "Z2": (0.60, 0.70),
    "Z3": (0.70, 0.80),
    "Z4": (0.80, 0.90),
    "Z5": (0.90, 1.00),
}


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _safe_int(value: Any) -> Optional[int]:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    try:
        return int(round(parsed))
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    if not raw:
        return None
    if raw in {"1", "true", "yes", "on", "connected"}:
        return True
    if raw in {"0", "false", "no", "off", "disconnected"}:
        return False
    return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _median(values) -> Optional[float]:
    cleaned = [float(v) for v in values if v is not None]
    if not cleaned:
        return None
    cleaned.sort()
    n = len(cleaned)
    mid = n // 2
    if n % 2 == 1:
        return cleaned[mid]
    return (cleaned[mid - 1] + cleaned[mid]) / 2.0


def _canonical_workout_type(workout_mode: str) -> str:
    return "intervals" if (workout_mode or "").strip().lower() == "interval" else "easy_run"


def _canonical_phase(*, workout_mode: str, request_phase: str, segment: str) -> str:
    mode = (workout_mode or "").strip().lower()
    seg = (segment or "").strip().lower()
    req = (request_phase or "").strip().lower()
    if mode == "interval":
        if seg == "rest":
            return "recovery"
        if seg == "work":
            return "work"
        if seg in {"warmup", "cooldown"}:
            return seg
        return "main"
    if req == "intense":
        return "main"
    if req in {"warmup", "cooldown"}:
        return req
    return "main"


def _canonical_zone_state(
    *,
    target_enforced: bool,
    hr_available: bool,
    zone_status: str,
) -> str:
    if not target_enforced:
        return "TARGETS_UNENFORCED"
    if not hr_available:
        return "HR_MISSING"

    mapping = {
        "in_zone": "IN_TARGET",
        "above_zone": "ABOVE_TARGET",
        "below_zone": "BELOW_TARGET",
    }
    return mapping.get((zone_status or "").strip().lower(), "HR_MISSING")


def _delta_to_band(
    *,
    hr_bpm: int,
    target_low: Optional[int],
    target_high: Optional[int],
    target_enforced: bool,
) -> Optional[int]:
    if not target_enforced or target_low is None or target_high is None:
        return None
    if hr_bpm <= 0:
        return None
    if hr_bpm < int(target_low):
        return int(hr_bpm - int(target_low))
    if hr_bpm > int(target_high):
        return int(hr_bpm - int(target_high))
    return 0


def _event_priority(event_type: str) -> int:
    """
    Deterministic event priority owned by the event motor.

    Catalogs describe wording intent only; they never decide timing or
    selection. Phase transitions and finish cues intentionally outrank the
    simpler catalog ordering because they are structurally important runtime
    events.
    """
    order = {
        # Tier A — countdowns + signal
        "interval_countdown_start": 100,
        "hr_signal_lost": 99,
        "hr_signal_restored": 98,
        "interval_countdown_5": 95,
        "interval_countdown_10": 94,
        "interval_countdown_15": 94,
        "interval_countdown_30": 93,
        "interval_countdown_halfway": 92,
        "interval_countdown_session_halfway": 91,

        # Tier B — phase transitions
        "warmup_started": 90,
        "main_started": 90,
        "cooldown_started": 90,
        "workout_finished": 90,
        "pause_detected": 86,
        "pause_resumed": 85,
        "hr_structure_mode_notice": 84,

        # Signal notices (between B and C)
        "watch_disconnected_notice": 88,
        "no_sensors_notice": 88,
        "watch_restored_notice": 88,

        # Tier C — actionable coaching
        "exited_target_above": 70,
        "exited_target_below": 70,
        "structure_instruction_work": 68,
        "structure_instruction_recovery": 68,
        "structure_instruction_steady": 68,
        "structure_instruction_finish": 68,
        "max_silence_override": 68,
        "max_silence_breath_guide": 68,
        "max_silence_go_by_feel": 68,
        "max_silence_motivation": 54,
        "recovery_hr_above_relax_ceiling": 65,
        "recovery_hr_ok_relax": 64,
        "entered_target": 60,

        # Tier C.5 — stage-based motivation (positive reinforcement)
        "interval_in_target_sustained": 55,
        "easy_run_in_target_sustained": 55,
    }
    return order.get(event_type, 0)


def _compute_max_silence_seconds(
    workout_type: str,
    phase: str,
    elapsed_minutes: int,
    hr_missing: bool,
    config_module,
) -> int:
    """Context-aware max-silence threshold."""
    if workout_type == "intervals":
        if phase == "work":
            return int(getattr(config_module, "MAX_SILENCE_INTERVALS_WORK", 30))
        return int(getattr(config_module, "MAX_SILENCE_INTERVALS_RECOVERY", 45))

    easy_run_base = int(getattr(config_module, "MAX_SILENCE_EASY_RUN_BASE", 60))
    ramp_per_10min = int(getattr(config_module, "MAX_SILENCE_RAMP_PER_10MIN", 15))
    raw = 45 + (max(0, int(elapsed_minutes)) // 10) * ramp_per_10min
    threshold = min(120, max(easy_run_base, raw))

    if hr_missing:
        multiplier = float(getattr(config_module, "MAX_SILENCE_HR_MISSING_MULTIPLIER", 1.5))
        threshold = int(round(float(threshold) * multiplier))

    return max(1, threshold)


def _should_emit_main_started(
    *,
    state: Dict[str, Any],
    previous_phase: Optional[str],
    canonical_phase: str,
    elapsed_seconds: int,
    config_module,
) -> bool:
    if canonical_phase not in {"main", "work", "recovery"}:
        return False
    if bool(state.get("main_started_emitted")):
        return False
    if previous_phase == "warmup":
        return True

    grace_seconds = max(
        45,
        int(getattr(config_module, "EARLY_WORKOUT_GRACE_SECONDS", 30)),
    )
    if int(max(0, elapsed_seconds or 0)) <= grace_seconds:
        return True

    # Defensive guard: if backend state is recreated late in the workout,
    # do not surface a stale "main started" cue.
    state["main_started_emitted"] = True
    return False


def _resolve_phrase_id(event_type: Optional[str], phase: str) -> Optional[str]:
    """Map a canonical event type to its phrase catalog ID (mirrors iOS utteranceID mapping)."""
    if not event_type:
        return None
    normalized_phase = str(phase or "").strip().lower()
    if normalized_phase in {"warmup", "recovery", "rest"}:
        phase_countdown_map = {
            "interval_countdown_30": "zone.countdown.warmup_recovery.30.1",
            "interval_countdown_10": "zone.countdown.warmup_recovery.10.1",
            "interval_countdown_5": "zone.countdown.warmup_recovery.5.1",
            "interval_countdown_start": "zone.countdown.warmup_recovery.start.1",
        }
        if event_type in phase_countdown_map:
            return phase_countdown_map[event_type]
    _map = {
        "warmup_started": "zone.phase.warmup.1",
        "main_started": "zone.main_started.1",
        "cooldown_started": "zone.phase.cooldown.1",
        "workout_finished": "zone.workout_finished.1",
        "entered_target": "zone.in_zone.default.1",
        "exited_target_above": "zone.above.default.1",
        "exited_target_below": "zone.below.default.1",
        "hr_signal_lost": "zone.hr_poor_enter.1",
        "hr_signal_restored": "zone.hr_poor_exit.1",
        "watch_disconnected_notice": "zone.watch_disconnected.1",
        "no_sensors_notice": "zone.no_sensors.1",
        "watch_restored_notice": "zone.watch_restored.1",
        "interval_countdown_30": "zone.countdown.30",
        "interval_countdown_10": None,
        "interval_countdown_15": "zone.countdown.15",
        "interval_countdown_5": "zone.countdown.5",
        "interval_countdown_start": "zone.countdown.start",
        "interval_countdown_halfway": "zone.countdown.halfway.dynamic",
        "interval_countdown_session_halfway": "zone.countdown.session_halfway.dynamic",
        "pause_detected": "zone.pause.detected.1",
        "pause_resumed": "zone.pause.resumed.1",
        "hr_structure_mode_notice": "zone.hr_poor_timing.1",
        "structure_instruction_work": "zone.structure.work.1",
        "structure_instruction_recovery": "zone.structure.recovery.1",
        "structure_instruction_steady": "zone.structure.steady.1",
        "structure_instruction_finish": "zone.structure.finish.1",
    }
    direct = _map.get(event_type)
    if direct:
        return direct
    p = phase.lower()
    if event_type == "max_silence_override":
        if p == "work":
            return "zone.silence.work.1"
        if p == "recovery":
            return "zone.silence.rest.1"
        return "zone.silence.default.1"
    if event_type == "max_silence_go_by_feel":
        if p == "work":
            return "zone.silence.work.1"
        if p == "recovery":
            return "zone.silence.rest.1"
        return "zone.silence.default.1"
    if event_type == "max_silence_breath_guide":
        if p == "work":
            return "zone.silence.work.1"
        if p == "recovery":
            return "zone.silence.rest.1"
        return "zone.silence.default.1"
    if event_type == "max_silence_motivation":
        return "interval.motivate.s2.1" if p in {"work", "recovery"} else "easy_run.motivate.s2.1"
    if event_type in ("interval_in_target_sustained", "easy_run_in_target_sustained"):
        # Dynamic phrase_id is computed at emission time and stored in state.
        # This is a static fallback for the mapping path.
        return "interval.motivate.s2.1" if event_type == "interval_in_target_sustained" else "easy_run.motivate.s2.1"
    return None


def _canonical_to_legacy_event(event_type: Optional[str]) -> Optional[str]:
    mapping = {
        "entered_target": "in_zone_recovered",
        "exited_target_above": "above_zone",
        "exited_target_below": "below_zone",
        "hr_signal_lost": "hr_poor_enter",
        "hr_signal_restored": "hr_poor_exit",
        "warmup_started": "phase_change_warmup",
        "cooldown_started": "phase_change_cooldown",
    }
    if not event_type:
        return None
    return mapping.get(event_type, event_type)


def _resolve_instruction_mode(
    *,
    target_enforced: bool,
    hr_signal_state: str,
    sensor_mode: str,
) -> str:
    # Instruction mode tracks live-HR availability, not whether zone targets are
    # currently enforced. If HR is usable, the runtime can stay in the normal
    # path; if HR is missing/stale, switch to structure-driven coaching.
    if hr_signal_state == "ok" and sensor_mode == "FULL_HR":
        return "hr_driven"
    return "structure_driven"


def _timed_easy_run_is_final_effort(
    *,
    canonical_workout_type: str,
    canonical_phase: str,
    target: Dict[str, Any],
    workout_state: Optional[Dict[str, Any]],
    config_module,
) -> bool:
    if canonical_workout_type != "easy_run" or canonical_phase not in {"main", "work", "intense"}:
        return False
    if isinstance(workout_state, dict) and bool(workout_state.get("plan_free_run")):
        return False
    remaining_seconds = _safe_int(target.get("segment_remaining_seconds"))
    if remaining_seconds is None:
        return False
    threshold = int(getattr(config_module, "NO_HR_STRUCTURE_FINAL_EFFORT_SECONDS", 60))
    return remaining_seconds <= max(1, threshold)


def _select_structure_instruction_event(
    *,
    canonical_workout_type: str,
    canonical_phase: str,
    target: Dict[str, Any],
    workout_state: Optional[Dict[str, Any]],
    config_module,
) -> str:
    reps_total = _safe_int(target.get("reps")) or 0
    rep_index = _safe_int(target.get("rep_index")) or 0

    interval_final_effort = (
        canonical_workout_type == "intervals"
        and canonical_phase == "work"
        and reps_total > 0
        and rep_index > 0
        and rep_index >= reps_total
    )
    timed_easy_run_final_effort = _timed_easy_run_is_final_effort(
        canonical_workout_type=canonical_workout_type,
        canonical_phase=canonical_phase,
        target=target,
        workout_state=workout_state,
        config_module=config_module,
    )
    if interval_final_effort or timed_easy_run_final_effort:
        return "structure_instruction_finish"

    if canonical_phase in {"recovery", "rest"}:
        return "structure_instruction_recovery"
    if canonical_workout_type == "intervals" and canonical_phase == "work":
        return "structure_instruction_work"
    return "structure_instruction_steady"


def _prefer_structure_mode_motivation(
    *,
    state: Dict[str, Any],
    canonical_workout_type: str,
    canonical_phase: str,
    target: Dict[str, Any],
    elapsed_seconds: int,
    config_module,
) -> bool:
    if canonical_phase in {"warmup", "recovery", "rest", "cooldown"}:
        return False

    if canonical_workout_type not in {"intervals", "easy_run"}:
        return False

    segment_key = str(target.get("segment_key") or canonical_phase)
    prior_structure_segment_key = str(state.get("last_structure_instruction_segment_key") or "").strip()
    if not prior_structure_segment_key or prior_structure_segment_key != segment_key:
        return False

    return _allow_motivation_event(
        state=state,
        workout_type=canonical_workout_type,
        elapsed_seconds=elapsed_seconds,
        config_module=config_module,
    )


def _pick_structure_phrase_id(
    *,
    state: Dict[str, Any],
    event_type: str,
) -> Optional[str]:
    phrase_ids = _STRUCTURE_INSTRUCTION_PHRASE_IDS.get(event_type) or ()
    if not phrase_ids:
        return _resolve_phrase_id(event_type, "main")
    if len(phrase_ids) == 1:
        return phrase_ids[0]

    indices = state.setdefault("structure_phrase_rotation_index", {})
    last_phrase = state.setdefault("structure_last_phrase_id", {})
    rotation_key = str(event_type)
    next_index = int(indices.get(rotation_key, 0))

    for offset in range(len(phrase_ids)):
        candidate_index = (next_index + offset) % len(phrase_ids)
        candidate_phrase = phrase_ids[candidate_index]
        if candidate_phrase != last_phrase.get(rotation_key):
            indices[rotation_key] = (candidate_index + 1) % len(phrase_ids)
            last_phrase[rotation_key] = candidate_phrase
            return candidate_phrase

    indices[rotation_key] = (next_index + 1) % len(phrase_ids)
    candidate_phrase = phrase_ids[next_index % len(phrase_ids)]
    last_phrase[rotation_key] = candidate_phrase
    return candidate_phrase


def _runtime_review_phrase_ids_for_event(event_type: str) -> List[str]:
    review_event_key = _RUNTIME_REVIEW_EVENT_KEYS.get(str(event_type or ""))
    if not review_event_key:
        return []
    return list(_RUNTIME_REVIEW_EVENT_PHRASE_MAP.get(review_event_key) or [])


def _pick_runtime_phrase_id(
    *,
    state: Dict[str, Any],
    event_type: str,
    phase: str,
) -> Optional[str]:
    if str(event_type or "").startswith("interval_countdown_"):
        return _resolve_phrase_id(event_type, phase)
    phrase_ids = _runtime_review_phrase_ids_for_event(event_type)
    if not phrase_ids:
        return _resolve_phrase_id(event_type, phase)
    if len(phrase_ids) == 1:
        return phrase_ids[0]

    indices = state.setdefault("runtime_phrase_rotation_index", {})
    last_phrase = state.setdefault("runtime_last_phrase_id", {})
    rotation_key = str(event_type)
    next_index = int(indices.get(rotation_key, 0))

    for offset in range(len(phrase_ids)):
        candidate_index = (next_index + offset) % len(phrase_ids)
        candidate_phrase = phrase_ids[candidate_index]
        if candidate_phrase != last_phrase.get(rotation_key):
            indices[rotation_key] = (candidate_index + 1) % len(phrase_ids)
            last_phrase[rotation_key] = candidate_phrase
            return candidate_phrase

    indices[rotation_key] = (next_index + 1) % len(phrase_ids)
    candidate_phrase = phrase_ids[next_index % len(phrase_ids)]
    last_phrase[rotation_key] = candidate_phrase
    return candidate_phrase


def _pick_phrase_pool_entry(
    *,
    state: Dict[str, Any],
    rotation_key: str,
    phrase_ids: Tuple[str, ...],
) -> Optional[str]:
    if not phrase_ids:
        return None
    if len(phrase_ids) == 1:
        return phrase_ids[0]

    indices = state.setdefault("fallback_phrase_rotation_index", {})
    last_phrase = state.setdefault("fallback_last_phrase_id", {})
    next_index = int(indices.get(rotation_key, 0))

    for offset in range(len(phrase_ids)):
        candidate_index = (next_index + offset) % len(phrase_ids)
        candidate_phrase = phrase_ids[candidate_index]
        if candidate_phrase != last_phrase.get(rotation_key):
            indices[rotation_key] = (candidate_index + 1) % len(phrase_ids)
            last_phrase[rotation_key] = candidate_phrase
            return candidate_phrase

    indices[rotation_key] = (next_index + 1) % len(phrase_ids)
    candidate_phrase = phrase_ids[next_index % len(phrase_ids)]
    last_phrase[rotation_key] = candidate_phrase
    return candidate_phrase


def _has_high_confidence_breath_guidance(
    *,
    breath_quality_reliable: bool,
    breath_quality_median: Optional[float],
    config_module,
) -> bool:
    return _breath_guidance_level(
        breath_quality_reliable=breath_quality_reliable,
        breath_quality_median=breath_quality_median,
        config_module=config_module,
    ) == "high"


def _breath_guidance_level(
    *,
    breath_quality_reliable: bool,
    breath_quality_median: Optional[float],
    config_module,
) -> str:
    if not breath_quality_reliable:
        return "low"
    required = float(getattr(config_module, "CS_BREATH_PASS_MIN_CONFIDENCE", 0.60))
    if breath_quality_median is None:
        return "medium"
    median = float(breath_quality_median)
    if median < required:
        return "low"
    high_required = min(0.95, max(required + 0.15, 0.75))
    if median >= high_required:
        return "high"
    return "medium"


def _normalize_breath_intensity_level(breath_intensity: Optional[str]) -> str:
    intensity = str(breath_intensity or "").strip().lower()
    if intensity in {"critical", "intense"}:
        return "heavy"
    if intensity in {"calm", "moderate"}:
        return "steady"
    return "unknown"


def _motivation_tone_bucket(
    *,
    phase_family: str,
    breath_guidance_level: str,
    breath_intensity: Optional[str],
) -> str:
    intensity_level = _normalize_breath_intensity_level(breath_intensity)
    family = str(phase_family or "").strip().lower()

    if family == "interval":
        if breath_guidance_level == "high":
            return "calm" if intensity_level == "heavy" else "push"
        if breath_guidance_level == "medium":
            return "calm"
        return "neutral"

    if breath_guidance_level == "high":
        return "calm" if intensity_level == "heavy" else "supportive"
    if breath_guidance_level == "medium":
        return "supportive"
    return "neutral"


def _motivation_candidate_phrase_ids_for_context(
    *,
    workout_type: str,
    target: Dict[str, Any],
    elapsed_seconds: int,
    instruction_mode: str,
    breath_guidance_level: str,
    breath_intensity: Optional[str],
    config_module,
) -> List[str]:
    if instruction_mode != "structure_driven":
        return _motivation_stage_phrase_ids_for_context(
            workout_type=workout_type,
            target=target,
            elapsed_seconds=elapsed_seconds,
            config_module=config_module,
        )

    phase_family = "interval" if workout_type == "intervals" else "easy_run"
    tone_bucket = _motivation_tone_bucket(
        phase_family=phase_family,
        breath_guidance_level=breath_guidance_level,
        breath_intensity=breath_intensity,
    )
    phrase_ids = _MOTIVATION_TONE_BUCKET_PHRASE_IDS.get(phase_family, {}).get(tone_bucket) or ()
    if phrase_ids:
        return list(phrase_ids)
    return _motivation_stage_phrase_ids_for_context(
        workout_type=workout_type,
        target=target,
        elapsed_seconds=elapsed_seconds,
        config_module=config_module,
    )


def _fallback_tone_bucket(
    *,
    segment: str,
    breath_guidance_level: str,
    breath_intensity: Optional[str],
) -> str:
    normalized_segment = str(segment or "").strip().lower()
    intensity_level = _normalize_breath_intensity_level(breath_intensity)
    if normalized_segment in {"rest", "recovery"}:
        return "calm"
    if normalized_segment == "work":
        return "calm" if breath_guidance_level == "high" and intensity_level == "heavy" else "neutral"
    if breath_guidance_level == "medium":
        return "calm"
    if breath_guidance_level == "high" and intensity_level == "heavy":
        return "calm"
    return "neutral"


def _pick_fallback_tone_selection(
    *,
    state: Dict[str, Any],
    segment: str,
    breath_guidance_level: str,
    breath_intensity: Optional[str],
) -> Tuple[str, Optional[str]]:
    tone_bucket = _fallback_tone_bucket(
        segment=segment,
        breath_guidance_level=breath_guidance_level,
        breath_intensity=breath_intensity,
    )
    phrase_ids = _FALLBACK_TONE_BUCKET_PHRASE_IDS.get(tone_bucket) or ()
    phrase_id = _pick_phrase_pool_entry(
        state=state,
        rotation_key=f"fallback:{str(segment or '').strip().lower()}:{tone_bucket}",
        phrase_ids=phrase_ids,
    )
    event_type = (
        "max_silence_breath_guide"
        if breath_guidance_level == "high" and _normalize_breath_intensity_level(breath_intensity) == "heavy"
        else "max_silence_go_by_feel"
    )
    return event_type, phrase_id


def is_zone_mode(workout_mode: str, config_module) -> bool:
    modes = set(getattr(config_module, "ZONE_COACHING_WORKOUT_MODES", ["easy_run", "interval"]))
    return (workout_mode or "").strip().lower() in modes


def normalize_coaching_style(style: Optional[str], config_module) -> str:
    raw = (style or "").strip().lower()
    resolved = _STYLE_ALIASES.get(raw, raw)
    supported = getattr(config_module, "SUPPORTED_COACHING_STYLES", ["minimal", "normal", "motivational"])
    if resolved in supported:
        return resolved
    return getattr(config_module, "DEFAULT_COACHING_STYLE", "normal")


def normalize_interval_template(template: Optional[str], config_module) -> str:
    raw = (template or "").strip()
    supported = set(getattr(config_module, "SUPPORTED_INTERVAL_TEMPLATES", ["4x4", "8x1", "10x30/30"]))
    if raw in supported:
        return raw
    return getattr(config_module, "DEFAULT_INTERVAL_TEMPLATE", "4x4")


def _zone_state(workout_state: Dict[str, Any]) -> Dict[str, Any]:
    state = workout_state.setdefault("zone_engine", {})
    state.setdefault("confirmed_zone_status", "in_zone")
    state.setdefault("zone_status_since", 0.0)
    state.setdefault("candidate_zone_status", "in_zone")
    state.setdefault("candidate_since", 0.0)
    state.setdefault("last_hr", None)
    state.setdefault("hr_quality_state", "unknown")
    state.setdefault("hr_poor_announced", False)
    state.setdefault("movement_state", "unknown")
    state.setdefault("movement_candidate_state", "unknown")
    state.setdefault("movement_candidate_since", 0.0)
    state.setdefault("last_segment_key", None)
    state.setdefault("style_last_any_elapsed", None)
    state.setdefault("style_last_by_type", {})
    state.setdefault("style_history", [])
    state.setdefault("last_sustained_event_elapsed", {})
    state.setdefault("last_above_zone_elapsed", None)
    state.setdefault("phase_id", 0)
    state.setdefault("event_last_elapsed_seconds", None)
    state.setdefault("sensor_mode", None)
    state.setdefault("sensor_mode_candidate", None)
    state.setdefault("sensor_mode_candidate_since", None)
    state.setdefault("notice_watch_disconnected_sent", False)
    state.setdefault("notice_no_sensors_sent", False)
    state.setdefault("notice_watch_restored_sent", False)
    state.setdefault("watch_disconnect_pending_restore", False)
    state.setdefault("countdown_fired_map", {})
    state.setdefault("session_finished", False)
    state.setdefault("main_started_emitted", False)
    state.setdefault("hr_signal_state", None)
    state.setdefault("hr_valid_streak_seconds", 0.0)
    state.setdefault("hr_invalid_streak_seconds", 0.0)
    state.setdefault("last_spoken_elapsed", None)
    state.setdefault("breath_reliable_streak_seconds", 0.0)
    state.setdefault("breath_unreliable_streak_seconds", 0.0)
    state.setdefault("breath_quality_samples", [])
    state.setdefault("last_high_priority_spoken_elapsed", None)
    state.setdefault("last_motivation_spoken_elapsed", None)
    state.setdefault("last_max_silence_elapsed", None)
    state.setdefault("last_max_silence_phase_id", None)
    metrics = state.setdefault("metrics", {})
    metrics.setdefault("total_main_set_ticks", 0)
    metrics.setdefault("in_zone_ticks", 0)
    metrics.setdefault("above_zone_ticks", 0)
    metrics.setdefault("below_zone_ticks", 0)
    metrics.setdefault("poor_ticks", 0)
    metrics.setdefault("overshoots", 0)
    metrics.setdefault("recovery_samples", [])
    metrics.setdefault("main_set_seconds", 0.0)
    metrics.setdefault("hr_valid_main_set_seconds", 0.0)
    metrics.setdefault("zone_valid_main_set_seconds", 0.0)
    metrics.setdefault("in_target_zone_valid_seconds", 0.0)
    metrics.setdefault("interval_work_zone_valid_seconds", 0.0)
    metrics.setdefault("interval_work_in_target_seconds", 0.0)
    metrics.setdefault("interval_recovery_zone_valid_seconds", 0.0)
    metrics.setdefault("interval_recovery_in_target_seconds", 0.0)
    metrics.setdefault("target_enforced_main_set_seconds", 0.0)
    metrics.setdefault("last_elapsed_seconds", None)
    return state


def _resolve_hr_profile(
    hr_max_value: Any,
    resting_hr_value: Any,
    age_value: Any,
) -> Dict[str, Any]:
    hr_max = _safe_int(hr_max_value)
    age = _safe_int(age_value)
    if hr_max is None and age is not None and 10 <= age <= 95:
        hr_max = 220 - age

    resting_hr = _safe_int(resting_hr_value)
    if hr_max is not None and resting_hr is not None:
        if resting_hr <= 20 or resting_hr >= hr_max:
            resting_hr = None

    return {
        "hr_max": hr_max,
        "resting_hr": resting_hr,
        "method": "hrr" if (hr_max is not None and resting_hr is not None) else "hrmax",
    }


def _style_to_intensity(style: Optional[str]) -> str:
    normalized = (style or "").strip().lower()
    if normalized in {"minimal", "easy"}:
        return "easy"
    if normalized in {"motivational", "hard"}:
        return "hard"
    return "medium"


def _target_band(
    *,
    workout_mode: str,
    segment: str,
    intensity: str,
    method: str,
    config_module,
) -> Tuple[Optional[float], Optional[float]]:
    key = intensity if intensity in {"easy", "medium", "hard"} else "medium"
    mode = (workout_mode or "").strip().lower()
    seg = (segment or "").strip().lower()

    if seg in {"warmup", "cooldown"}:
        key = "easy"

    if mode == "interval":
        if seg == "work":
            table_name = "INTERVAL_WORK_HRR_BANDS" if method == "hrr" else "INTERVAL_WORK_HRMAX_BANDS"
            table = getattr(config_module, table_name, {}) or {}
            return table.get(key, table.get("medium", (None, None)))
        if seg == "rest":
            if method == "hrr":
                table = getattr(config_module, "INTERVAL_RECOVERY_HRR_BANDS", {}) or {}
                return table.get(key, table.get("medium", (None, None)))
            # HRmax fallback recovery derives from work band:
            work_table = getattr(config_module, "INTERVAL_WORK_HRMAX_BANDS", {}) or {}
            work_low, _ = work_table.get(key, work_table.get("medium", (None, None)))
            if work_low is None:
                return None, None
            rec_low = max(0.60, float(work_low) - 0.15)
            rec_high = float(work_low) - 0.05
            if rec_high <= rec_low:
                rec_high = rec_low + 0.05
            return rec_low, rec_high

    # Steady/easy run
    table_name = "STEADY_HRR_BANDS" if method == "hrr" else "STEADY_HRMAX_BANDS"
    table = getattr(config_module, table_name, {}) or {}
    return table.get(key, table.get("medium", (None, None)))


def _apply_target_safety(
    *,
    low: int,
    high: int,
    profile: Dict[str, Any],
    config_module,
) -> Tuple[int, int]:
    min_half_width = int(getattr(config_module, "TARGET_MIN_HALF_WIDTH_BPM", 8))
    min_half_width = max(4, min_half_width)
    min_width = max(2, min_half_width * 2)

    low_int = int(low)
    high_int = int(high)
    if high_int < low_int:
        low_int, high_int = high_int, low_int

    if (high_int - low_int) < min_width:
        mid = int(round((low_int + high_int) / 2.0))
        low_int = mid - min_half_width
        high_int = mid + min_half_width

    hr_max = _safe_int(profile.get("hr_max"))
    if hr_max is not None:
        upper_cap = min(hr_max - 3, int(getattr(config_module, "TARGET_HR_UPPER_ABSOLUTE_CAP", 195)))
        high_int = min(high_int, upper_cap)
        if (high_int - low_int) < min_width:
            low_int = high_int - min_width

    low_int = max(40, low_int)
    if high_int <= low_int:
        high_int = low_int + 1

    return low_int, high_int


def _resolve_intensity_target_bounds(
    *,
    workout_mode: str,
    segment: str,
    intensity: str,
    profile: Dict[str, Any],
    config_module,
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    hr_max = _safe_int(profile.get("hr_max"))
    resting_hr = _safe_int(profile.get("resting_hr"))
    method = "hrr" if (hr_max is not None and resting_hr is not None) else "hrmax"

    if hr_max is None:
        return None, None, None

    low_pct, high_pct = _target_band(
        workout_mode=workout_mode,
        segment=segment,
        intensity=intensity,
        method=method,
        config_module=config_module,
    )
    if low_pct is None or high_pct is None:
        return None, None, None

    if method == "hrr":
        hrr = hr_max - resting_hr
        low = int(round(resting_hr + float(low_pct) * hrr))
        high = int(round(resting_hr + float(high_pct) * hrr))
    else:
        low = int(round(float(low_pct) * hr_max))
        high = int(round(float(high_pct) * hr_max))

    low, high = _apply_target_safety(low=low, high=high, profile=profile, config_module=config_module)
    return low, high, method


def _zone_bounds_for_label(label: Optional[str], profile: Dict[str, Any], config_module) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    if not label:
        return None, None, None

    normalized = label.upper().replace(" ", "")
    if not normalized.startswith("Z"):
        return None, None, None

    hr_max = profile.get("hr_max")
    resting_hr = profile.get("resting_hr")
    if hr_max is None:
        return None, None, None

    method = "hrr" if resting_hr is not None else "hrmax"

    if normalized == "Z2":
        if method == "hrr":
            hrr = hr_max - resting_hr
            low = resting_hr + float(getattr(config_module, "ZONE2_HRR_LOW", 0.60)) * hrr
            high = resting_hr + float(getattr(config_module, "ZONE2_HRR_HIGH", 0.70)) * hrr
            return int(round(low)), int(round(high)), "hrr"
        low = float(getattr(config_module, "ZONE2_HRMAX_LOW", 0.70)) * hr_max
        high = float(getattr(config_module, "ZONE2_HRMAX_HIGH", 0.80)) * hr_max
        return int(round(low)), int(round(high)), "hrmax"

    if "-" in normalized:
        parts = normalized.split("-")
        if len(parts) == 2 and parts[0].startswith("Z") and not parts[1].startswith("Z"):
            parts[1] = "Z" + parts[1]
        if len(parts) != 2:
            return None, None, None
        low_a, high_a, method_a = _zone_bounds_for_label(parts[0], profile, config_module)
        low_b, high_b, method_b = _zone_bounds_for_label(parts[1], profile, config_module)
        if low_a is None or high_b is None:
            return None, None, None
        return low_a, high_b, method_a or method_b

    table = _HRR_ZONE_PCT if method == "hrr" else _HRMAX_ZONE_PCT
    if normalized not in table:
        return None, None, None

    low_pct, high_pct = table[normalized]
    if method == "hrr":
        hrr = hr_max - resting_hr
        low = resting_hr + low_pct * hrr
        high = resting_hr + high_pct * hrr
        return int(round(low)), int(round(high)), "hrr"
    return int(round(low_pct * hr_max)), int(round(high_pct * hr_max)), "hrmax"


def _interval_target(
    interval_template: str,
    elapsed_seconds: int,
    profile: Dict[str, Any],
    intensity: str,
    workout_state: Optional[Dict[str, Any]],
    config_module,
) -> Dict[str, Any]:
    templates = getattr(config_module, "INTERVAL_TEMPLATES", {})
    cfg = templates.get(interval_template) or templates.get(getattr(config_module, "DEFAULT_INTERVAL_TEMPLATE", "4x4"), {})

    warmup = int(cfg.get("warmup_seconds", 600))
    work = int(cfg.get("work_seconds", 240))
    rest = int(cfg.get("rest_seconds", 180))
    reps = int(cfg.get("reps", 4))
    cooldown = int(cfg.get("cooldown_seconds", 480))

    if isinstance(workout_state, dict):
        plan_warmup = _safe_int(workout_state.get("plan_warmup_s"))
        plan_repeats = _safe_int(workout_state.get("plan_interval_repeats"))
        plan_work = _safe_int(workout_state.get("plan_interval_work_s"))
        plan_recovery = _safe_int(workout_state.get("plan_interval_recovery_s"))
        plan_cooldown = _safe_int(workout_state.get("plan_cooldown_s"))
        if plan_warmup is not None:
            warmup = max(0, int(plan_warmup))
        if plan_work is not None:
            work = max(1, int(plan_work))
        if plan_recovery is not None:
            rest = max(0, int(plan_recovery))
        if plan_repeats is not None:
            reps = max(1, int(plan_repeats))
        if plan_cooldown is not None:
            cooldown = max(0, int(plan_cooldown))

    cycle = max(1, work + rest)
    main_set_duration = reps * cycle
    session_end = warmup + main_set_duration + cooldown
    elapsed = max(0, int(elapsed_seconds))

    segment = "cooldown"
    rep_index = 0
    target_label = "easy"
    hr_enforced = True
    main_set = False
    segment_elapsed_seconds = 0
    segment_remaining_seconds = None

    if elapsed < warmup:
        segment = "warmup"
        target_label = "easy"
        segment_elapsed_seconds = elapsed
        segment_remaining_seconds = max(0, warmup - elapsed)
    elif elapsed < warmup + main_set_duration:
        main_set = True
        segment_elapsed = elapsed - warmup
        rep_index = int(segment_elapsed // cycle) + 1
        within_rep = segment_elapsed % cycle
        if within_rep < work:
            segment = "work"
            target_label = intensity
            hr_enforced = bool(cfg.get("work_hr_enforced", True))
            segment_elapsed_seconds = int(within_rep)
            segment_remaining_seconds = max(0, work - int(within_rep))
        else:
            segment = "rest"
            target_label = "easy"
            hr_enforced = True
            rest_elapsed = int(within_rep - work)
            segment_elapsed_seconds = rest_elapsed
            segment_remaining_seconds = max(0, rest - rest_elapsed)
    elif elapsed < session_end:
        segment = "cooldown"
        target_label = "easy"
        cooldown_elapsed = max(0, elapsed - (warmup + main_set_duration))
        segment_elapsed_seconds = int(cooldown_elapsed)
        segment_remaining_seconds = max(0, cooldown - int(cooldown_elapsed))
    else:
        segment = "cooldown"
        target_label = "easy"
        segment_elapsed_seconds = cooldown
        segment_remaining_seconds = 0

    low, high, source = _resolve_intensity_target_bounds(
        workout_mode="interval",
        segment=segment,
        intensity=intensity,
        profile=profile,
        config_module=config_module,
    )

    return {
        "segment": segment,
        "rep_index": rep_index,
        "segment_key": f"{segment}:{rep_index}" if segment in {"work", "rest"} else segment,
        "target_zone_label": target_label.capitalize(),
        "target_low": low,
        "target_high": high,
        "target_source": source,
        "hr_enforced": hr_enforced and low is not None and high is not None,
        "main_set": main_set,
        "segment_elapsed_seconds": segment_elapsed_seconds,
        "segment_remaining_seconds": segment_remaining_seconds,
        "warmup_seconds": warmup,
        "work_seconds": work,
        "rest_seconds": rest,
        "reps": reps,
        "session_end_seconds": session_end,
    }


def _easy_run_target(
    phase: str,
    warmup_remaining_seconds: Optional[int],
    elapsed_seconds: int,
    profile: Dict[str, Any],
    intensity: str,
    workout_state: Optional[Dict[str, Any]],
    config_module,
) -> Dict[str, Any]:
    normalized_phase = (phase or "").strip().lower() or "intense"
    plan_warmup = _safe_int(workout_state.get("plan_warmup_s")) if isinstance(workout_state, dict) else None
    plan_main = _safe_int(workout_state.get("plan_main_s")) if isinstance(workout_state, dict) else None
    plan_cooldown = _safe_int(workout_state.get("plan_cooldown_s")) if isinstance(workout_state, dict) else None
    plan_free_run = bool(workout_state.get("plan_free_run")) if isinstance(workout_state, dict) else False

    if plan_free_run and normalized_phase == "warmup":
        normalized_phase = "intense"

    target_intensity = "easy" if normalized_phase in {"warmup", "cooldown"} else intensity
    segment_elapsed_seconds: Optional[int] = None
    segment_remaining_seconds: Optional[int] = None
    session_end_seconds: Optional[int] = None
    elapsed = max(0, int(elapsed_seconds))

    warmup_total = max(0, int(plan_warmup)) if plan_warmup is not None else None
    main_total = max(0, int(plan_main)) if plan_main is not None else None
    cooldown_total = max(0, int(plan_cooldown)) if plan_cooldown is not None else None

    if normalized_phase == "warmup":
        if warmup_remaining_seconds is not None:
            segment_remaining_seconds = max(0, int(warmup_remaining_seconds))
        elif warmup_total is not None:
            segment_remaining_seconds = max(0, warmup_total - elapsed)
            segment_elapsed_seconds = max(0, min(warmup_total, elapsed))
    elif normalized_phase in {"intense", "main"} and main_total is not None:
        warmup_offset = 0 if plan_free_run else (warmup_total or 0)
        elapsed_in_main = max(0, elapsed - warmup_offset)
        segment_elapsed_seconds = max(0, min(main_total, elapsed_in_main))
        segment_remaining_seconds = max(0, main_total - elapsed_in_main)
    elif normalized_phase == "cooldown" and cooldown_total is not None:
        warmup_offset = warmup_total or 0
        main_offset = main_total or 0
        elapsed_in_cooldown = max(0, elapsed - warmup_offset - main_offset)
        segment_elapsed_seconds = max(0, min(cooldown_total, elapsed_in_cooldown))
        segment_remaining_seconds = max(0, cooldown_total - elapsed_in_cooldown)

    if not plan_free_run and main_total is not None:
        total = (warmup_total or 0) + main_total + (cooldown_total or 0)
        session_end_seconds = max(0, int(total))

    low, high, source = _resolve_intensity_target_bounds(
        workout_mode="easy_run",
        segment=normalized_phase,
        intensity=target_intensity,
        profile=profile,
        config_module=config_module,
    )
    return {
        "segment": normalized_phase,
        "rep_index": 0,
        "segment_key": f"easy_run:{normalized_phase}",
        "target_zone_label": target_intensity.capitalize(),
        "target_low": low,
        "target_high": high,
        "target_source": source,
        "hr_enforced": low is not None and high is not None,
        "main_set": normalized_phase in {"intense", "main"},
        "segment_elapsed_seconds": segment_elapsed_seconds,
        "segment_remaining_seconds": segment_remaining_seconds,
        "work_seconds": None,
        "rest_seconds": None,
        "session_end_seconds": session_end_seconds,
    }


def _resolve_target(
    workout_mode: str,
    phase: str,
    coaching_style: Optional[str],
    interval_template: str,
    elapsed_seconds: int,
    warmup_remaining_seconds: Optional[int],
    workout_state: Optional[Dict[str, Any]],
    profile: Dict[str, Any],
    config_module,
) -> Dict[str, Any]:
    mode = (workout_mode or "").strip().lower()
    intensity = _style_to_intensity(coaching_style)
    if mode == "interval":
        return _interval_target(interval_template, elapsed_seconds, profile, intensity, workout_state, config_module)
    return _easy_run_target(
        phase=phase,
        warmup_remaining_seconds=warmup_remaining_seconds,
        elapsed_seconds=elapsed_seconds,
        profile=profile,
        intensity=intensity,
        workout_state=workout_state,
        config_module=config_module,
    )


def _build_workout_context_summary(
    *,
    workout_type: str,
    phase: str,
    elapsed_seconds: int,
    target: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic progress context for UI and talk, independent of HR availability.
    """
    session_end_seconds = _safe_int(target.get("session_end_seconds"))
    segment_remaining_seconds = _safe_int(target.get("segment_remaining_seconds"))
    rep_index = _safe_int(target.get("rep_index")) or 0
    reps_total = None
    if workout_type == "intervals":
        reps_total = _safe_int(target.get("reps")) or 0

    reps_remaining_including_current = None
    if workout_type == "intervals" and reps_total is not None and rep_index > 0:
        reps_remaining_including_current = max(0, int(reps_total) - int(rep_index) + 1)

    return {
        "phase": phase,
        "elapsed_s": max(0, int(elapsed_seconds)),
        "time_left_s": (
            max(0, int(session_end_seconds) - max(0, int(elapsed_seconds)))
            if session_end_seconds is not None
            else segment_remaining_seconds
        ),
        "rep_index": int(rep_index),
        "reps_total": int(reps_total) if reps_total is not None else None,
        "rep_remaining_s": int(segment_remaining_seconds) if segment_remaining_seconds is not None else None,
        "reps_remaining_including_current": (
            int(reps_remaining_including_current)
            if reps_remaining_including_current is not None
            else None
        ),
        "elapsed_source": "server_authoritative",
    }


def _tick_delta_seconds(state: Dict[str, Any], elapsed_seconds: int, config_module) -> float:
    now_elapsed = max(0.0, float(elapsed_seconds))
    prev_elapsed = _safe_float(state.get("event_last_elapsed_seconds"))
    state["event_last_elapsed_seconds"] = now_elapsed
    if prev_elapsed is None:
        return 0.0
    delta = now_elapsed - prev_elapsed
    if delta <= 0.0:
        return 0.0
    max_tick_seconds = float(getattr(config_module, "MAX_COACHING_INTERVAL", 15))
    return min(delta, max(1.0, max_tick_seconds))


def _update_hr_signal_state(
    *,
    state: Dict[str, Any],
    hr_good_now: bool,
    dt_seconds: float,
    config_module,
) -> List[str]:
    events: List[str] = []
    valid_streak = float(state.get("hr_valid_streak_seconds", 0.0))
    invalid_streak = float(state.get("hr_invalid_streak_seconds", 0.0))
    signal_state = state.get("hr_signal_state")

    if signal_state is None:
        # First tick bootstrap:
        # - Good HR starts in "ok" with no event.
        # - Missing/poor HR starts in "lost" silently.
        #   Emit hr_signal_lost only after a real connected -> disconnected transition.
        signal_state = "ok" if hr_good_now else "lost"
        valid_streak = 5.0 if hr_good_now else 0.0
        invalid_streak = 4.0 if not hr_good_now else 0.0

    if hr_good_now:
        valid_streak += dt_seconds
        invalid_streak = 0.0
    else:
        invalid_streak += dt_seconds
        valid_streak = 0.0

    loss_threshold = float(getattr(config_module, "UNIFIED_EVENT_HR_LOST_SECONDS", 4.0))
    restore_threshold = float(getattr(config_module, "UNIFIED_EVENT_HR_RESTORED_SECONDS", 5.0))

    if signal_state != "lost" and invalid_streak >= loss_threshold:
        signal_state = "lost"
        events.append("hr_signal_lost")
    elif signal_state == "lost" and valid_streak >= restore_threshold:
        signal_state = "ok"
        events.append("hr_signal_restored")

    state["hr_signal_state"] = signal_state
    state["hr_valid_streak_seconds"] = valid_streak
    state["hr_invalid_streak_seconds"] = invalid_streak
    return events


def _update_breath_reliability(
    *,
    state: Dict[str, Any],
    breath_signal_quality: Any,
    breath_summary: Any,
    dt_seconds: float,
    config_module,
) -> bool:
    samples = state.setdefault("breath_quality_samples", [])
    current_quality = _safe_float(breath_signal_quality)
    if current_quality is not None:
        samples.append(current_quality)
    max_samples = int(getattr(config_module, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6)) * 3
    if len(samples) > max(12, max_samples):
        del samples[:-max(12, max_samples)]

    quality_summary = summarize_breath_quality(
        breath_data={"signal_quality": current_quality} if current_quality is not None else {},
        recent_samples=samples,
        config_module=config_module,
        include_current_signal=False,
    )
    required_samples = int(quality_summary.get("required_samples", 6))
    required_quality = float(quality_summary.get("required_quality", 0.35))
    median_quality = quality_summary.get("median_quality")
    summary_data = breath_summary if isinstance(breath_summary, dict) else {}
    summary_sample_count = _safe_int(summary_data.get("quality_sample_count"))
    summary_median_quality = _safe_float(summary_data.get("quality_median"))
    summary_reliable_hint = summary_data.get("quality_reliable")
    summary_reliable = (
        bool(summary_reliable_hint)
        if isinstance(summary_reliable_hint, bool)
        else (
            summary_sample_count is not None
            and is_breath_quality_reliable(
                sample_count=summary_sample_count,
                median_quality=summary_median_quality,
                config_module=config_module,
            )
        )
    )
    reliable_now = (
        len(samples) >= required_samples
        and median_quality is not None
        and median_quality >= required_quality
    )
    reliable_now = bool(reliable_now or summary_reliable)

    reliable_streak = float(state.get("breath_reliable_streak_seconds", 0.0))
    unreliable_streak = float(state.get("breath_unreliable_streak_seconds", 0.0))
    if reliable_now:
        reliable_streak += dt_seconds
        unreliable_streak = 0.0
    else:
        unreliable_streak += dt_seconds
        reliable_streak = 0.0

    state["breath_reliable_streak_seconds"] = reliable_streak
    state["breath_unreliable_streak_seconds"] = unreliable_streak
    persistence_seconds = float(getattr(config_module, "UNIFIED_EVENT_BREATH_PERSIST_SECONDS", 4.0))

    if reliable_now and reliable_streak >= persistence_seconds:
        return True
    if not reliable_now and unreliable_streak >= persistence_seconds:
        return False

    # If not yet stable in current streak, keep previous stable interpretation.
    prior_mode = state.get("sensor_mode")
    return prior_mode == "BREATH_FALLBACK"


def _resolve_sensor_mode(
    *,
    state: Dict[str, Any],
    hr_signal_state: str,
    breath_reliable: bool,
    movement_available: bool,
    elapsed_seconds: int,
    watch_connected: Optional[bool],
    watch_status: Optional[str],
    config_module,
) -> List[str]:
    events: List[str] = []
    if hr_signal_state == "ok":
        desired = "FULL_HR"
    elif breath_reliable:
        desired = "BREATH_FALLBACK"
    else:
        desired = "NO_SENSORS"

    current_mode = state.get("sensor_mode")
    if current_mode is None:
        state["sensor_mode"] = desired
        state["sensor_mode_candidate"] = desired
        state["sensor_mode_candidate_since"] = float(elapsed_seconds)
        current_mode = desired

    if bool(getattr(config_module, "SENSOR_MODE_TABLE_V2_ENABLED", True)):
        transition_table = {
            "FULL_HR": {"BREATH_FALLBACK", "NO_SENSORS"},
            "BREATH_FALLBACK": {"FULL_HR", "NO_SENSORS"},
            "NO_SENSORS": {"FULL_HR", "BREATH_FALLBACK"},
        }
    else:
        transition_table = {
            "FULL_HR": {"BREATH_FALLBACK", "NO_SENSORS"},
            "BREATH_FALLBACK": {"FULL_HR", "NO_SENSORS"},
            "NO_SENSORS": {"FULL_HR", "BREATH_FALLBACK"},
        }

    if desired != current_mode:
        allowed_targets = transition_table.get(str(current_mode), set())
        if desired not in allowed_targets:
            state["sensor_mode_candidate"] = current_mode
            state["sensor_mode_candidate_since"] = float(elapsed_seconds)
            return events

        candidate = state.get("sensor_mode_candidate")
        candidate_since = _safe_float(state.get("sensor_mode_candidate_since"))
        if candidate != desired:
            state["sensor_mode_candidate"] = desired
            state["sensor_mode_candidate_since"] = float(elapsed_seconds)
        else:
            dwell_seconds = float(getattr(config_module, "UNIFIED_EVENT_SENSOR_MODE_DWELL_SECONDS", 2.0))
            candidate_age = 0.0 if candidate_since is None else max(0.0, float(elapsed_seconds) - candidate_since)
            if candidate_age >= dwell_seconds:
                previous_mode = current_mode
                current_mode = desired
                state["sensor_mode"] = desired
                state["sensor_mode_candidate"] = desired
                state["sensor_mode_candidate_since"] = float(elapsed_seconds)
                watch_state = (watch_status or "").strip().lower()
                watch_starting = watch_state == "watch_starting"
                watch_unavailable = (
                    (watch_connected is False and not watch_starting)
                    or watch_state in {"disconnected", "workout_not_running", "not_worn", "no_permission"}
                )

                if (
                    previous_mode == "FULL_HR"
                    and desired in {"BREATH_FALLBACK", "NO_SENSORS"}
                    and watch_unavailable
                    and not bool(state.get("notice_watch_disconnected_sent"))
                ):
                    events.append("watch_disconnected_notice")
                    state["notice_watch_disconnected_sent"] = True
                    state["watch_disconnect_pending_restore"] = True

                if (
                    desired == "NO_SENSORS"
                    and previous_mode != "NO_SENSORS"
                    and not bool(state.get("notice_no_sensors_sent"))
                ):
                    events.append("no_sensors_notice")
                    state["notice_no_sensors_sent"] = True

                if (
                    previous_mode != "FULL_HR"
                    and desired == "FULL_HR"
                    and bool(state.get("watch_disconnect_pending_restore"))
                    and not bool(state.get("notice_watch_restored_sent"))
                ):
                    events.append("watch_restored_notice")
                    state["notice_watch_restored_sent"] = True
                    state["watch_disconnect_pending_restore"] = False
    else:
        state["sensor_mode_candidate"] = current_mode
        state["sensor_mode_candidate_since"] = float(elapsed_seconds)

    return events


def _resolve_sensor_fusion_mode(
    *,
    sensor_mode: str,
    hr_ok_for_zone_events: bool,
    target_enforced: bool,
    breath_reliable: bool,
    movement_available: bool,
) -> str:
    """
    Normalize sensor usage into one deterministic fusion mode.

    This keeps cadence/movement connected to coaching decisions whenever available,
    while preserving HR as the primary source for zone enforcement.
    """
    if sensor_mode == "FULL_HR" and hr_ok_for_zone_events and target_enforced:
        return "HR_ZONE"
    if breath_reliable and movement_available:
        return "BREATH_MOVEMENT"
    if breath_reliable:
        return "BREATH_ONLY"
    if movement_available:
        return "MOVEMENT_ONLY"
    return "TIMING_ONLY"


def _prep_countdown_thresholds(total_seconds: int) -> List[int]:
    if total_seconds < 10:
        return [5, 0]
    if total_seconds < 30:
        return [10, 5, 0]
    return [30, 10, 5, 0]


def _segment_halfway_remaining_threshold(total_seconds: Optional[int]) -> Optional[int]:
    total = _safe_int(total_seconds)
    if total is None or total <= 1:
        return None
    return max(0, total // 2)


def _interval_session_halfway_text(
    *,
    language: str,
    workout_context_summary: Optional[Dict[str, Any]],
) -> str:
    _ = workout_context_summary
    lang = (language or "en").strip().lower()
    if lang == "no":
        return "Du er halvveis nå."
    return "You are halfway through the workout"


def _evaluate_hr_quality(
    *,
    hr_bpm: Optional[int],
    hr_quality_hint: Optional[str],
    hr_confidence: Optional[float],
    hr_sample_age_seconds: Optional[float],
    hr_sample_gap_seconds: Optional[float],
    watch_connected: Optional[bool],
    watch_status: Optional[str],
    state: Dict[str, Any],
    config_module,
) -> Dict[str, Any]:
    reasons = []
    hint = (hr_quality_hint or "").strip().lower()
    watch_state = (watch_status or "").strip().lower()
    watch_starting = watch_state == "watch_starting"
    gap_seconds = _safe_float(hr_sample_gap_seconds)

    if hint == "poor":
        reasons.append("client_reported_poor")

    if watch_connected is False and not watch_starting:
        reasons.append("watch_not_connected")

    if watch_state in {"not_worn", "no_permission", "workout_not_running", "disconnected"}:
        reasons.append(watch_state)

    if hr_bpm is None:
        reasons.append("missing_hr")

    stale_seconds = float(getattr(config_module, "HR_QUALITY_STALE_SECONDS", 8.0))
    if hr_sample_age_seconds is not None and hr_sample_age_seconds > stale_seconds:
        reasons.append("stale_hr")

    spike_delta = float(getattr(config_module, "HR_QUALITY_SPIKE_DELTA_BPM", 20.0))
    spike_window = float(getattr(config_module, "HR_QUALITY_SPIKE_WINDOW_SECONDS", 2.0))
    prev_hr = _safe_int(state.get("last_hr"))
    if (
        hr_bpm is not None
        and prev_hr is not None
        and gap_seconds is not None
        and gap_seconds < spike_window
        and abs(hr_bpm - prev_hr) > spike_delta
    ):
        reasons.append("hr_spike")

    min_conf = float(getattr(config_module, "HR_QUALITY_MIN_CONFIDENCE", 0.5))
    if hr_confidence is not None and hr_confidence < min_conf:
        reasons.append("low_confidence")

    if hr_bpm is not None:
        state["last_hr"] = hr_bpm

    hr_delta_bpm = None
    if hr_bpm is not None and prev_hr is not None:
        hr_delta_bpm = float(hr_bpm - prev_hr)

    quality = "poor" if reasons else "good"
    return {
        "state": quality,
        "reasons": reasons,
        "hr_delta_bpm": hr_delta_bpm,
        "hr_sample_gap_seconds": gap_seconds,
    }


def _resolve_movement_signal(
    *,
    movement_score_value: Any,
    cadence_spm_value: Any,
    movement_source_value: Any,
) -> Dict[str, Any]:
    cadence_spm = _safe_float(cadence_spm_value)
    movement_score = _safe_float(movement_score_value)
    movement_source = (str(movement_source_value).strip().lower() if movement_source_value is not None else "")

    if movement_score is None and cadence_spm is not None:
        # Convert cadence to coarse movement score: 30 spm -> 0, 180 spm -> 1
        movement_score = _clamp((cadence_spm - 30.0) / 150.0, 0.0, 1.0)
    elif movement_score is not None:
        movement_score = _clamp(movement_score, 0.0, 1.0)

    if not movement_source:
        if cadence_spm is not None:
            movement_source = "cadence"
        elif movement_score is not None:
            movement_source = "movement_score"
        else:
            movement_source = "none"

    return {
        "movement_score": movement_score,
        "cadence_spm": cadence_spm,
        "movement_source": movement_source,
    }


def _apply_movement_state(
    *,
    state: Dict[str, Any],
    movement_score: Optional[float],
    hr_quality_state: str,
    hr_delta_bpm: Optional[float],
    hr_sample_gap_seconds: Optional[float],
    elapsed_seconds: int,
    config_module,
) -> Tuple[str, Optional[str]]:
    confirmed = str(state.get("movement_state", "unknown"))
    candidate = str(state.get("movement_candidate_state", confirmed))
    candidate_since_raw = _safe_float(state.get("movement_candidate_since"))
    candidate_since = float(elapsed_seconds) if candidate_since_raw is None else candidate_since_raw

    pause_threshold = float(getattr(config_module, "MOVEMENT_SCORE_PAUSE_THRESHOLD", 0.12))
    active_threshold = float(getattr(config_module, "MOVEMENT_SCORE_ACTIVE_THRESHOLD", 0.25))
    pause_min_hr_drop = float(getattr(config_module, "MOVEMENT_PAUSE_MIN_HR_DROP_BPM", 1.0))
    pause_hr_gap_max = float(getattr(config_module, "MOVEMENT_PAUSE_HR_DROP_MAX_GAP_SECONDS", 10.0))
    rapid_drop_bpm = float(getattr(config_module, "HR_PAUSE_RAPID_DROP_BPM", 6.0))
    rapid_drop_gap_max = float(getattr(config_module, "HR_PAUSE_RAPID_DROP_MAX_GAP_SECONDS", 8.0))

    hr_gap_valid = hr_sample_gap_seconds is None or hr_sample_gap_seconds <= pause_hr_gap_max
    hr_falling = (
        hr_delta_bpm is not None
        and hr_delta_bpm <= -pause_min_hr_drop
        and hr_gap_valid
    )
    rapid_gap_valid = hr_sample_gap_seconds is None or hr_sample_gap_seconds <= rapid_drop_gap_max
    rapid_hr_drop = (
        hr_delta_bpm is not None
        and hr_delta_bpm <= -rapid_drop_bpm
        and rapid_gap_valid
    )

    if movement_score is None:
        # Fallback when movement is unavailable: only infer pause from clear HR drop.
        if hr_quality_state == "good" and rapid_hr_drop:
            new_candidate = "paused"
        else:
            new_candidate = "unknown"
    else:
        if movement_score <= pause_threshold:
            # With reliable HR, require HR fall to confirm an actual pause.
            if hr_quality_state == "good":
                new_candidate = "paused" if hr_falling else confirmed
            else:
                # HR-poor mode: use movement as primary fallback.
                new_candidate = "paused"
        elif movement_score >= active_threshold:
            new_candidate = "moving"
        else:
            new_candidate = confirmed

    if new_candidate == confirmed:
        state["movement_candidate_state"] = confirmed
        state["movement_candidate_since"] = float(elapsed_seconds)
        state["movement_state"] = confirmed
        return confirmed, None

    if new_candidate != candidate:
        state["movement_candidate_state"] = new_candidate
        state["movement_candidate_since"] = float(elapsed_seconds)
        return confirmed, None

    dwell = float(getattr(config_module, "MOVEMENT_PAUSE_DWELL_SECONDS", 8.0))
    if float(elapsed_seconds) - candidate_since < dwell:
        return confirmed, None

    previous = confirmed
    state["movement_state"] = new_candidate
    state["movement_candidate_state"] = new_candidate
    state["movement_candidate_since"] = float(elapsed_seconds)

    if previous != "paused" and new_candidate == "paused":
        return new_candidate, "pause_detected"
    if previous == "paused" and new_candidate == "moving":
        return new_candidate, "pause_resumed"
    return new_candidate, None


def _zone_candidate(
    *,
    hr_bpm: int,
    low: int,
    high: int,
    prev_confirmed: str,
    config_module,
) -> str:
    hysteresis = float(getattr(config_module, "HR_ZONE_HYSTERESIS_BPM", 3.0))
    lower_guard = low - hysteresis
    upper_guard = high + hysteresis

    if hr_bpm < lower_guard:
        return "below_zone"
    if hr_bpm > upper_guard:
        return "above_zone"
    if low <= hr_bpm <= high:
        return "in_zone"
    # Inside the hysteresis band near the boundary: keep stable previous state.
    return prev_confirmed or "in_zone"


def _apply_zone_transition(
    *,
    state: Dict[str, Any],
    candidate: str,
    elapsed_seconds: int,
    config_module,
) -> Tuple[str, Optional[str]]:
    confirmed = state.get("confirmed_zone_status", "in_zone")
    current_candidate = state.get("candidate_zone_status", confirmed)
    if state.get("zone_status_since") is None:
        state["zone_status_since"] = float(elapsed_seconds)
    candidate_since_raw = _safe_float(state.get("candidate_since"))
    candidate_since = float(elapsed_seconds) if candidate_since_raw is None else candidate_since_raw

    if candidate == confirmed:
        state["candidate_zone_status"] = confirmed
        state["candidate_since"] = float(elapsed_seconds)
        return confirmed, None

    if candidate != current_candidate:
        state["candidate_zone_status"] = candidate
        state["candidate_since"] = float(elapsed_seconds)
        return confirmed, None

    dwell_required = float(getattr(config_module, "HR_ZONE_DWELL_SECONDS", 8.0))
    if float(elapsed_seconds) - candidate_since < dwell_required:
        return confirmed, None

    previous = confirmed
    state["confirmed_zone_status"] = candidate
    state["candidate_zone_status"] = candidate
    state["candidate_since"] = float(elapsed_seconds)
    state["zone_status_since"] = float(elapsed_seconds)

    if candidate == "above_zone":
        return candidate, "above_zone"
    if candidate == "below_zone":
        return candidate, "below_zone"
    if candidate == "in_zone" and previous in {"above_zone", "below_zone"}:
        return candidate, "in_zone_recovered"
    return candidate, None


def _sustained_zone_event(
    *,
    state: Dict[str, Any],
    zone_status: str,
    elapsed_seconds: int,
    movement_state: str,
    movement_score: Optional[float],
    hr_delta_bpm: Optional[float],
    hr_sample_gap_seconds: Optional[float],
    hr_quality_state: str,
    breath_intensity: Optional[str],
    config_module,
) -> Optional[str]:
    if hr_quality_state != "good":
        return None

    zone_since_raw = _safe_float(state.get("zone_status_since"))
    if zone_since_raw is None:
        return None
    zone_duration = float(elapsed_seconds) - zone_since_raw
    if zone_duration < 0:
        return None

    repeat_guard = state.setdefault("last_sustained_event_elapsed", {})
    repeat_seconds = float(getattr(config_module, "ZONE_SUSTAINED_EVENT_REPEAT_SECONDS", 45.0))

    if zone_status == "below_zone":
        min_seconds = float(getattr(config_module, "ZONE_BELOW_PUSH_SUSTAIN_SECONDS", 25.0))
        min_movement = float(getattr(config_module, "ZONE_BELOW_PUSH_MIN_MOVEMENT_SCORE", 0.30))
        moving_enough = movement_state == "moving" and (movement_score or 0.0) >= min_movement
        if zone_duration >= min_seconds and moving_enough:
            last_emit = _safe_float(repeat_guard.get("below_zone_push"))
            if last_emit is None or (float(elapsed_seconds) - last_emit) >= repeat_seconds:
                repeat_guard["below_zone_push"] = float(elapsed_seconds)
                return "below_zone_push"

    if zone_status == "above_zone":
        min_seconds = float(getattr(config_module, "ZONE_ABOVE_EASE_SUSTAIN_SECONDS", 20.0))
        rise_min = float(getattr(config_module, "ZONE_ABOVE_EASE_MIN_HR_RISE_BPM", 1.5))
        rise_gap_max = float(getattr(config_module, "ZONE_ABOVE_EASE_RISE_MAX_GAP_SECONDS", 10.0))
        gap_ok = hr_sample_gap_seconds is None or hr_sample_gap_seconds <= rise_gap_max
        hr_rising = hr_delta_bpm is not None and hr_delta_bpm >= rise_min and gap_ok
        intensity = (breath_intensity or "").strip().lower()
        breath_stress = intensity in {"intense", "critical"}
        if zone_duration >= min_seconds and (hr_rising or breath_stress):
            last_emit = _safe_float(repeat_guard.get("above_zone_ease"))
            if last_emit is None or (float(elapsed_seconds) - last_emit) >= repeat_seconds:
                repeat_guard["above_zone_ease"] = float(elapsed_seconds)
                return "above_zone_ease"

    return None


def _event_group(event_type: str) -> str:
    return get_event_catalog(event_type) or "context"


def _allow_style_event(
    *,
    state: Dict[str, Any],
    event_type: str,
    style: str,
    elapsed_seconds: int,
    hr_quality_state: str,
    config_module,
) -> Tuple[bool, str]:
    policies = getattr(config_module, "COACHING_STYLE_COOLDOWNS", {})
    policy = policies.get(style) or policies.get(getattr(config_module, "DEFAULT_COACHING_STYLE", "normal")) or {}

    min_any = int(policy.get("min_seconds_between_any_speech", 30))
    min_same = int(policy.get("min_seconds_between_same_cue_type", 60))
    max_cues = int(policy.get("max_cues_per_10min", 16))
    praise_min = int(policy.get("praise_min_seconds", 240))

    cue_group = _event_group(event_type)
    cooldown_key = event_cooldown_key(event_type)
    is_phase_change = event_type.startswith("phase_change_")

    if cue_group == "instruction" and hr_quality_state == "poor":
        min_any += 15

    history = state.setdefault("style_history", [])
    pruned = []
    for item in history:
        item_elapsed = _safe_float(item.get("elapsed"))
        if item_elapsed is not None and (float(elapsed_seconds) - item_elapsed) <= 600.0:
            pruned.append(item)
    state["style_history"] = pruned

    if len(pruned) >= max_cues and not is_phase_change:
        return False, "style_budget_limit"

    last_any = _safe_float(state.get("style_last_any_elapsed"))
    if last_any is not None and (float(elapsed_seconds) - last_any) < min_any and not is_phase_change:
        return False, "style_cooldown_any"

    last_by_type = state.setdefault("style_last_by_type", {})
    last_same = _safe_float(last_by_type.get(cooldown_key))
    if last_same is not None and (float(elapsed_seconds) - last_same) < min_same and not is_phase_change:
        return False, "style_cooldown_same_type"

    if cue_group == "motivation":
        last_positive = _safe_float(last_by_type.get("motivation"))
        if last_positive is not None and (float(elapsed_seconds) - last_positive) < praise_min:
            return False, "style_praise_cooldown"

    state["style_last_any_elapsed"] = float(elapsed_seconds)
    last_by_type[cooldown_key] = float(elapsed_seconds)
    state["style_history"].append(
        {
            "elapsed": float(elapsed_seconds),
            "event": event_type,
            "group": cue_group,
            "instruction_urgency": get_event_instruction_urgency(event_type),
            "cooldown_key": cooldown_key,
        }
    )
    return True, "allowed"


def _allow_motivation_event(
    *,
    state: Dict[str, Any],
    workout_type: str,
    elapsed_seconds: int,
    config_module,
) -> bool:
    """Motivation cooldown barrier for max-silence motivation events."""
    is_intervals = workout_type == "intervals"

    barrier = int(
        getattr(
            config_module,
            "MOTIVATION_BARRIER_SECONDS_INTERVALS" if is_intervals else "MOTIVATION_BARRIER_SECONDS_EASY_RUN",
            25 if is_intervals else 45,
        )
    )
    last_high_priority = _safe_float(state.get("last_high_priority_spoken_elapsed"))
    if last_high_priority is not None and (float(elapsed_seconds) - last_high_priority) < float(barrier):
        return False

    min_spacing = int(
        getattr(
            config_module,
            "MOTIVATION_MIN_SPACING_INTERVALS" if is_intervals else "MOTIVATION_MIN_SPACING_EASY_RUN",
            60 if is_intervals else 120,
        )
    )
    last_motivation = _safe_float(state.get("last_motivation_spoken_elapsed"))
    if last_motivation is not None and (float(elapsed_seconds) - last_motivation) < float(min_spacing):
        return False

    return True


# ---------------------------------------------------------------------------
# Stage-based motivation helpers (interval_in_target_sustained / easy_run)
# ---------------------------------------------------------------------------

def _motivation_stage_from_rep(rep_index: int) -> int:
    """Map 1-based rep_index to motivation stage 1-4."""
    return max(1, min(4, rep_index))


def _motivation_stage_from_elapsed(elapsed_minutes: int, config_module) -> int:
    """Map elapsed minutes into main phase to motivation stage 1-4 (easy_run)."""
    thresholds = getattr(config_module, "EASY_RUN_STAGE_THRESHOLDS", [20, 40, 60])
    stage = 1
    for threshold in thresholds:
        if elapsed_minutes >= threshold:
            stage += 1
    return max(1, min(4, stage))


def _motivation_budget(work_seconds: int) -> int:
    """Compute max motivation cues per work phase from interval duration."""
    import math
    return max(1, min(4, math.floor(1 + work_seconds / 90)))


def _motivation_slots(budget: int) -> list:
    """Return slot fractions for a given budget."""
    _SLOT_MAP = {
        1: [0.55],
        2: [0.35, 0.75],
        3: [0.25, 0.55, 0.85],
        4: [0.20, 0.45, 0.70, 0.90],
    }
    return _SLOT_MAP.get(max(1, min(4, budget)), [0.55])


def _motivation_phrase_id(workout_type: str, stage: int, variant: int) -> str:
    """Build phrase_id for stage-based motivation events."""
    prefix = "interval" if workout_type == "intervals" else "easy_run"
    s = max(1, min(4, stage))
    v = 1 if variant not in (1, 2) else variant
    return f"{prefix}.motivate.s{s}.{v}"


def _motivation_stage_phrase_ids(workout_type: str, stage: int) -> List[str]:
    """Return stage-local phrase IDs in deterministic order."""
    normalized_stage = max(1, min(4, int(stage or 1)))
    review_event = (
        f"interval_sustain_stage_{normalized_stage}"
        if workout_type == "intervals"
        else f"easy_run_sustain_stage_{normalized_stage}"
    )
    phrase_ids = list(_RUNTIME_REVIEW_EVENT_PHRASE_MAP.get(review_event) or [])
    if phrase_ids:
        return phrase_ids
    return [
        _motivation_phrase_id(workout_type, stage=normalized_stage, variant=1),
        _motivation_phrase_id(workout_type, stage=normalized_stage, variant=2),
    ]


def _motivation_stage_phrase_ids_for_context(
    *,
    workout_type: str,
    target: Dict[str, Any],
    elapsed_seconds: int,
    config_module,
) -> List[str]:
    if workout_type == "intervals":
        stage = _motivation_stage_from_rep(int(target.get("rep_index") or 1))
        return _motivation_stage_phrase_ids("intervals", stage)

    elapsed_minutes = max(0, int(elapsed_seconds) // 60)
    stage = _motivation_stage_from_elapsed(elapsed_minutes, config_module)
    return _motivation_stage_phrase_ids("easy_run", stage)


def _pick_motivation_phrase_id(
    *,
    state: Dict[str, Any],
    stage_phrase_ids: Optional[List[str]],
    config_module,
) -> str:
    """
    Select a stage-based motivation phrase with anti-repeat.

    The flat `motivation.1..10` pool is kept in the catalog for compatibility
    and editing workflow continuity, but deterministic workout events no longer
    consume it once staged catalog/audio parity is in place.
    """
    stage_ids = [phrase_id for phrase_id in (stage_phrase_ids or []) if phrase_id]
    candidates = list(dict.fromkeys(stage_ids))
    if not candidates:
        return "interval.motivate.s2.1"

    recent_k = int(getattr(config_module, "MOTIVATION_RECENT_HISTORY_SIZE", 2))
    recent_k = max(0, min(8, recent_k))
    recent = [
        str(item).strip()
        for item in (state.get("recent_motivation_phrase_ids") or [])
        if str(item).strip()
    ]
    recent = recent[-recent_k:] if recent_k > 0 else []

    filtered = [phrase_id for phrase_id in candidates if phrase_id not in recent]
    if not filtered:
        filtered = candidates

    rotation_index = int(state.get("motivation_rotation_index", 0))
    selected = filtered[rotation_index % len(filtered)]
    state["motivation_rotation_index"] = rotation_index + 1

    updated_recent = recent + [selected]
    if recent_k > 0:
        updated_recent = updated_recent[-recent_k:]
    else:
        updated_recent = []
    state["recent_motivation_phrase_ids"] = updated_recent

    return selected


def _evaluate_motivation_event(
    *,
    state: Dict[str, Any],
    canonical_workout_type: str,
    canonical_phase: str,
    zone_status: str,
    target: Dict[str, Any],
    elapsed_seconds: int,
    pause_flag: bool,
    hr_ok_for_zone_events: bool,
    target_enforced: bool,
    sensor_mode: str,
    instruction_mode: str,
    event_types: List[str],
    breath_guidance_level: str,
    breath_intensity: Optional[str],
    config_module,
) -> Optional[str]:
    """Evaluate whether a stage-based motivation event should fire."""
    if pause_flag:
        return None

    is_intervals = canonical_workout_type == "intervals"
    is_easy_run = canonical_workout_type == "easy_run"

    if not (is_intervals or is_easy_run):
        state["motivation_in_zone_since"] = None
        state["motivation_context_key"] = None
        return None

    # Intervals: only in work phase
    if is_intervals and canonical_phase != "work":
        state["motivation_in_zone_since"] = None
        state["motivation_context_key"] = None
        return None
    # Easy run: only in main phase
    if is_easy_run and canonical_phase not in ("main", "work"):
        state["motivation_in_zone_since"] = None
        state["motivation_context_key"] = None
        return None

    segment_key = str(target.get("segment_key") or canonical_phase or canonical_workout_type).strip()
    previous_context_key = str(state.get("motivation_context_key") or "").strip()
    if previous_context_key != segment_key:
        state["motivation_context_key"] = segment_key
        state["motivation_in_zone_since"] = None
    else:
        state["motivation_context_key"] = segment_key

    hr_motivation_ready = (
        zone_status == "in_zone"
        and hr_ok_for_zone_events
        and target_enforced
        and sensor_mode == "FULL_HR"
    )
    structure_motivation_ready = (
        instruction_mode == "structure_driven"
        and str(state.get("last_structure_instruction_segment_key") or "").strip() == segment_key
    )

    if not (hr_motivation_ready or structure_motivation_ready):
        # Reset sustained tracking whenever the current segment is not ready for
        # stage-based motivation. For structure-driven mode, readiness begins
        # only after the first real structure cue in the current segment.
        state["motivation_in_zone_since"] = None
        return None

    # --- Sustained in-zone tracking ---
    in_zone_since = _safe_float(state.get("motivation_in_zone_since"))
    if in_zone_since is None:
        state["motivation_in_zone_since"] = float(elapsed_seconds)
        return None
    sustained_seconds = float(elapsed_seconds) - in_zone_since

    # --- Barrier: no high-priority event recently ---
    barrier_sec = int(getattr(config_module, "MOTIVATION_BARRIER_SEC", 20))
    last_high = _safe_float(state.get("last_high_priority_spoken_elapsed"))
    if last_high is not None and (float(elapsed_seconds) - last_high) < float(barrier_sec):
        return None

    # --- Higher-priority events in this tick block motivation ---
    motivation_priority = _event_priority("interval_in_target_sustained")
    if any(_event_priority(e) > motivation_priority for e in event_types if e):
        return None

    candidate_phrase_ids = _motivation_candidate_phrase_ids_for_context(
        workout_type=canonical_workout_type,
        target=target,
        elapsed_seconds=elapsed_seconds,
        instruction_mode=instruction_mode,
        breath_guidance_level=breath_guidance_level,
        breath_intensity=breath_intensity,
        config_module=config_module,
    )

    if is_intervals:
        return _evaluate_interval_motivation(
            state=state,
            target=target,
            sustained_seconds=sustained_seconds,
            elapsed_seconds=elapsed_seconds,
            candidate_phrase_ids=candidate_phrase_ids,
            config_module=config_module,
        )
    else:
        return _evaluate_easy_run_motivation(
            state=state,
            sustained_seconds=sustained_seconds,
            elapsed_seconds=elapsed_seconds,
            candidate_phrase_ids=candidate_phrase_ids,
            config_module=config_module,
        )


def _evaluate_interval_motivation(
    *,
    state: Dict[str, Any],
    target: Dict[str, Any],
    sustained_seconds: float,
    elapsed_seconds: int,
    candidate_phrase_ids: Optional[List[str]],
    config_module,
) -> Optional[str]:
    """Check slot scheduling and budget for interval work phase motivation."""
    work_seconds = int(target.get("work_seconds") or 240)
    segment_elapsed = int(target.get("segment_elapsed_seconds") or 0)
    phase_id = int(state.get("phase_id", 1))
    rep_index = int(target.get("rep_index") or 1)

    # Guard: no motivation in first 10s of work (HR lag)
    min_elapsed = int(getattr(config_module, "MOTIVATION_WORK_MIN_ELAPSED", 10))
    if segment_elapsed < min_elapsed:
        return None

    # Sustain threshold: dynamic based on work duration
    sustain_threshold = max(12, min(30, round(0.30 * work_seconds)))
    if sustained_seconds < sustain_threshold:
        return None

    # Budget
    budget = _motivation_budget(work_seconds)

    # State per phase_id
    phase_key = f"motivation_phase_{phase_id}"
    phase_state = state.setdefault(phase_key, {"count": 0, "used_slots": set()})

    # Reset if phase_id changed
    last_motivation_phase_id = _safe_int(state.get("last_motivation_phase_id"))
    if last_motivation_phase_id != phase_id:
        state[phase_key] = {"count": 0, "used_slots": set()}
        phase_state = state[phase_key]
        state["last_motivation_phase_id"] = phase_id

    if phase_state["count"] >= budget:
        return None

    # Slot check
    slots = _motivation_slots(budget)
    eligible_slot = None
    for idx, frac in enumerate(slots):
        slot_time = frac * work_seconds
        if segment_elapsed >= slot_time and idx not in phase_state["used_slots"]:
            eligible_slot = idx
            break  # Take first eligible unused slot

    if eligible_slot is None:
        return None

    # Fire!
    phase_state["count"] += 1
    phase_state["used_slots"].add(eligible_slot)
    state["last_motivation_phase_id"] = phase_id

    # Compute stage
    stage = _motivation_stage_from_rep(rep_index)
    phrase_id = _pick_motivation_phrase_id(
        state=state,
        stage_phrase_ids=candidate_phrase_ids or _motivation_stage_phrase_ids("intervals", stage),
        config_module=config_module,
    )

    # Store for phrase_id resolution in event payload
    state["_pending_motivation_phrase_id"] = phrase_id
    state["_pending_motivation_stage"] = stage
    state["motivation_in_zone_since"] = None  # Reset for next sustained window

    return "interval_in_target_sustained"


def _evaluate_easy_run_motivation(
    *,
    state: Dict[str, Any],
    sustained_seconds: float,
    elapsed_seconds: int,
    candidate_phrase_ids: Optional[List[str]],
    config_module,
) -> Optional[str]:
    """Check cooldown and sustain for easy_run motivation."""
    sustain_sec = int(getattr(config_module, "MOTIVATION_SUSTAIN_SEC_EASY", 45))
    cooldown_sec = int(getattr(config_module, "EASY_RUN_MOTIVATION_COOLDOWN", 120))

    if sustained_seconds < sustain_sec:
        return None

    # Cooldown
    last_easy_motivation = _safe_float(state.get("last_easy_run_motivation_elapsed"))
    if last_easy_motivation is not None and (float(elapsed_seconds) - last_easy_motivation) < float(cooldown_sec):
        return None

    # Fire!
    state["last_easy_run_motivation_elapsed"] = float(elapsed_seconds)

    # Stage from elapsed minutes
    elapsed_minutes = max(0, elapsed_seconds // 60)
    stage = _motivation_stage_from_elapsed(elapsed_minutes, config_module)

    phrase_id = _pick_motivation_phrase_id(
        state=state,
        stage_phrase_ids=candidate_phrase_ids or _motivation_stage_phrase_ids("easy_run", stage),
        config_module=config_module,
    )

    state["_pending_motivation_phrase_id"] = phrase_id
    state["_pending_motivation_stage"] = stage
    state["motivation_in_zone_since"] = None  # Reset for next sustained window

    return "easy_run_in_target_sustained"


def _update_metrics(
    *,
    state: Dict[str, Any],
    zone_status: str,
    in_main_set: bool,
    hr_quality_state: str,
    transition_event: Optional[str],
    elapsed_seconds: int,
    hr_bpm: Optional[int],
    target: Dict[str, Any],
    movement_state: str,
    config_module,
) -> None:
    metrics = state.setdefault("metrics", {})
    current_elapsed = max(0.0, float(elapsed_seconds))
    previous_elapsed = _safe_float(metrics.get("last_elapsed_seconds"))
    if previous_elapsed is None:
        metrics["last_elapsed_seconds"] = current_elapsed
        return

    delta = current_elapsed - previous_elapsed
    metrics["last_elapsed_seconds"] = current_elapsed
    if delta <= 0.0:
        return

    # Protect metrics from large timestamp jumps after app backgrounding.
    max_tick_seconds = float(getattr(config_module, "MAX_COACHING_INTERVAL", 15))
    delta = min(delta, max(1.0, max_tick_seconds))

    if not in_main_set:
        return
    if movement_state == "paused":
        return

    metrics["total_main_set_ticks"] = int(metrics.get("total_main_set_ticks", 0)) + 1
    metrics["main_set_seconds"] = float(metrics.get("main_set_seconds", 0.0)) + delta

    hr_valid = (
        hr_bpm is not None
        and 35 <= int(hr_bpm) <= 230
        and hr_quality_state == "good"
    )
    if hr_valid:
        metrics["hr_valid_main_set_seconds"] = float(metrics.get("hr_valid_main_set_seconds", 0.0)) + delta
    else:
        metrics["poor_ticks"] = int(metrics.get("poor_ticks", 0)) + 1

    target_low = _safe_int(target.get("target_low"))
    target_high = _safe_int(target.get("target_high"))
    target_enforced = bool(target.get("hr_enforced")) and target_low is not None and target_high is not None
    if target_enforced:
        metrics["target_enforced_main_set_seconds"] = float(metrics.get("target_enforced_main_set_seconds", 0.0)) + delta

    in_target = False
    if hr_valid and target_enforced:
        metrics["zone_valid_main_set_seconds"] = float(metrics.get("zone_valid_main_set_seconds", 0.0)) + delta
        in_target = target_low <= int(hr_bpm) <= target_high
        if in_target:
            metrics["in_target_zone_valid_seconds"] = float(metrics.get("in_target_zone_valid_seconds", 0.0)) + delta

        segment = str(target.get("segment", "")).strip().lower()
        if segment == "work":
            metrics["interval_work_zone_valid_seconds"] = float(metrics.get("interval_work_zone_valid_seconds", 0.0)) + delta
            if in_target:
                metrics["interval_work_in_target_seconds"] = float(metrics.get("interval_work_in_target_seconds", 0.0)) + delta
        elif segment in {"rest", "recovery"}:
            metrics["interval_recovery_zone_valid_seconds"] = float(metrics.get("interval_recovery_zone_valid_seconds", 0.0)) + delta
            if in_target:
                metrics["interval_recovery_in_target_seconds"] = float(metrics.get("interval_recovery_in_target_seconds", 0.0)) + delta

    if hr_valid:
        if zone_status == "in_zone":
            metrics["in_zone_ticks"] = int(metrics.get("in_zone_ticks", 0)) + 1
        elif zone_status == "above_zone":
            metrics["above_zone_ticks"] = int(metrics.get("above_zone_ticks", 0)) + 1
        elif zone_status == "below_zone":
            metrics["below_zone_ticks"] = int(metrics.get("below_zone_ticks", 0)) + 1

    if transition_event == "above_zone":
        metrics["overshoots"] = int(metrics.get("overshoots", 0)) + 1


def _interval_weighted_zone_compliance(metrics: Dict[str, Any], config_module) -> Optional[float]:
    min_phase_seconds = float(getattr(config_module, "CS_MIN_PHASE_VALID_SECONDS", 30.0))
    work_valid = float(metrics.get("interval_work_zone_valid_seconds", 0.0))
    work_in = float(metrics.get("interval_work_in_target_seconds", 0.0))
    recovery_valid = float(metrics.get("interval_recovery_zone_valid_seconds", 0.0))
    recovery_in = float(metrics.get("interval_recovery_in_target_seconds", 0.0))

    work_component = None
    recovery_component = None
    if work_valid >= min_phase_seconds and work_valid > 0.0:
        work_component = _clamp(work_in / work_valid, 0.0, 1.0)
    if recovery_valid >= min_phase_seconds and recovery_valid > 0.0:
        recovery_component = _clamp(recovery_in / recovery_valid, 0.0, 1.0)

    if work_component is None and recovery_component is None:
        return None
    if work_component is not None and recovery_component is not None:
        return _clamp((0.7 * work_component) + (0.3 * recovery_component), 0.0, 1.0)
    return work_component if work_component is not None else recovery_component


def _resolve_zone_compliance(metrics: Dict[str, Any], segment: str, config_module) -> Optional[float]:
    zone_valid = float(metrics.get("zone_valid_main_set_seconds", 0.0))
    in_target = float(metrics.get("in_target_zone_valid_seconds", 0.0))

    segment_name = (segment or "").strip().lower()
    if segment_name in {"work", "rest", "recovery"}:
        interval_compliance = _interval_weighted_zone_compliance(metrics, config_module)
        if interval_compliance is not None:
            return interval_compliance

    if zone_valid <= 0.0:
        return None
    return _clamp(in_target / zone_valid, 0.0, 1.0)


def _score_label(score: int) -> str:
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Solid"
    if score >= 55:
        return "Mixed"
    return "Needs control"


def _score_from_metrics(metrics: Dict[str, Any], language: str) -> Dict[str, Any]:
    total = int(metrics.get("total_main_set_ticks", 0))
    if total <= 0:
        return {
            "score": 80,
            "score_line": "CoachScore: 80 - Solid start." if language != "no" else "CoachScore: 80 - God start.",
            "score_confidence": "low",
            "time_in_target_pct": None,
            "overshoots": int(metrics.get("overshoots", 0)),
        }

    poor_ticks = int(metrics.get("poor_ticks", 0))
    poor_ratio = poor_ticks / float(total)
    effective = max(0, total - poor_ticks)
    in_zone = int(metrics.get("in_zone_ticks", 0))
    above_ticks = int(metrics.get("above_zone_ticks", 0))
    overshoots = int(metrics.get("overshoots", 0))

    time_in_target = None
    if effective > 0:
        time_in_target = round((in_zone / float(effective)) * 100.0, 1)

    base = float(time_in_target or 0.0)
    penalty = float(overshoots) * 2.0 + float(above_ticks) * 0.4
    score = int(round(_clamp(base - penalty, 0.0, 100.0)))
    label = _score_label(score)

    if poor_ratio > 0.30:
        if language == "no":
            line = "CoachScore: Lav datakvalitet. Tid i sone skjules."
        else:
            line = "CoachScore: Low confidence. Time in zone hidden."
        return {
            "score": score,
            "score_line": line,
            "score_confidence": "low",
            "time_in_target_pct": None,
            "overshoots": overshoots,
        }

    if time_in_target is None:
        if language == "no":
            line = f"CoachScore: {score} - {label}. Ingen stabil pulssone-data."
        else:
            line = f"CoachScore: {score} - {label}. No stable HR zone data."
        return {
            "score": score,
            "score_line": line,
            "score_confidence": "low",
            "time_in_target_pct": None,
            "overshoots": overshoots,
        }

    if poor_ratio > 0.0:
        if language == "no":
            line = f"CoachScore: {score} - {label}. {time_in_target:.0f}% i målsonen (noen puls-hull)."
        else:
            line = f"CoachScore: {score} - {label}. {time_in_target:.0f}% in target zone (some HR gaps)."
        confidence = "partial"
    else:
        if language == "no":
            line = f"CoachScore: {score} - {label}. {time_in_target:.0f}% i målsonen."
        else:
            line = f"CoachScore: {score} - {label}. {time_in_target:.0f}% in target zone."
        confidence = "high"

    return {
        "score": score,
        "score_line": line,
        "score_confidence": confidence,
        "time_in_target_pct": time_in_target,
        "overshoots": overshoots,
    }


def _event_text(
    *,
    event_type: str,
    language: str,
    style: str,
    target_low: Optional[int],
    target_high: Optional[int],
    segment: str,
    workout_context_summary: Optional[Dict[str, Any]] = None,
) -> str:
    lang = "no" if language == "no" else "en"
    tone = style
    if tone not in {"minimal", "normal", "motivational"}:
        tone = "normal"

    if event_type == "hr_signal_lost":
        event_type = "hr_poor_enter"
    elif event_type == "hr_signal_restored":
        event_type = "hr_poor_exit"
    elif event_type == "entered_target":
        event_type = "in_zone_recovered"
    elif event_type == "exited_target_above":
        event_type = "above_zone"
    elif event_type == "exited_target_below":
        event_type = "below_zone"

    if event_type == "watch_disconnected_notice":
        if lang == "no":
            return "Klokken ble koblet fra."
        return "Watch disconnected."

    if event_type == "hr_structure_mode_notice":
        if lang == "no":
            return "Mangler pulssignal. Jeg guider deg på tid og innsats."
        return "No heart rate signal. I'll coach you by time and effort."

    if event_type == "no_sensors_notice":
        if lang == "no":
            return "Coacher med pust."
        return "Coaching by breath."

    if event_type == "watch_restored_notice":
        if lang == "no":
            return "Klokken er tilkoblet, og pulsen er tilbake."
        return "Watch connected and heart rate is back."

    if event_type == "interval_countdown_30":
        if str(segment or "").strip().lower() in {"warmup", "recovery", "rest"}:
            return "30 sekunder igjen. Gjør deg klar." if lang == "no" else "30 seconds left. Get ready."
        return "30 sekunder." if lang == "no" else "30 seconds left."

    if event_type == "interval_countdown_10":
        if str(segment or "").strip().lower() in {"warmup", "recovery", "rest"}:
            return "Gjør deg klar. Starter snart." if lang == "no" else "Get ready. Starting soon."
        return None

    if event_type == "interval_countdown_15":
        return "15" if lang == "no" else "15"

    if event_type == "interval_countdown_5":
        if str(segment or "").strip().lower() in {"warmup", "recovery", "rest"}:
            return "Fem." if lang == "no" else "Five."
        return "fem" if lang == "no" else "Five."

    if event_type == "interval_countdown_start":
        if str(segment or "").strip().lower() in {"warmup", "recovery", "rest"}:
            return "Start."
        return "Start"

    if event_type == "interval_countdown_halfway":
        return "Du er halvveis nå." if lang == "no" else "You are halfway through"

    if event_type == "interval_countdown_session_halfway":
        return _interval_session_halfway_text(
            language=lang,
            workout_context_summary=workout_context_summary,
        )

    if event_type == "main_started":
        if lang == "no":
            return "Hoveddelen starter nå."
        return "Main set starts now."

    if event_type == "workout_finished":
        if lang == "no":
            return "Økten er ferdig. Bra jobbet."
        return "Workout finished. Nice work."

    if event_type == "hr_poor_enter":
        if lang == "no":
            return "Pulssignalet er svakt."
        return "Heart rate signal is weak."

    if event_type == "hr_poor_exit":
        return "Pulsen er tilbake." if lang == "no" else "Heart rate is back."

    if event_type == "above_zone":
        if lang == "no":
            if tone == "minimal":
                return "Litt ned 10-15 sekunder."
            if target_low is not None and target_high is not None:
                return f"Rolig ned mot {target_low}-{target_high} bpm."
            return "Ro ned litt."
        if tone == "minimal":
            return "Ease off 10-15 seconds."
        if target_low is not None and target_high is not None:
            return f"Back off to {target_low}-{target_high} bpm."
        return "Ease back slightly."

    if event_type == "above_zone_ease":
        if lang == "no":
            if tone == "minimal":
                return "Pulsen stiger. Rolig ned."
            return "Fortsatt høy. Ro ned 20 sekunder."
        if tone == "minimal":
            return "HR still climbing. Ease down."
        return "Still high. Ease down 20 seconds."

    if event_type == "below_zone":
        if lang == "no":
            if tone == "minimal":
                return "Bygg litt opp nå."
            if target_low is not None and target_high is not None:
                return f"Løft rolig mot {target_low}-{target_high} bpm."
            return "Øk litt nå."
        if tone == "minimal":
            return "Build slightly now."
        if target_low is not None and target_high is not None:
            return f"Build toward {target_low}-{target_high} bpm."
        return "Pick it up."

    if event_type == "below_zone_push":
        if lang == "no":
            if tone == "minimal":
                return "Du er i gang. Litt opp."
            return "Du er i gang. Øk litt."
        if tone == "minimal":
            return "You're moving. Add a little."
        return "You're moving. Pick it up slightly."

    if event_type == "in_zone_recovered":
        if lang == "no":
            return "Bli her."
        return "Stay right here."

    if event_type == "phase_change_work":
        if lang == "no":
            return "Drag starter nå. Øk farten." if tone != "motivational" else "Nå jobber vi."
        return "Interval starts now. Bring up the pace." if tone != "motivational" else "Time to work."

    if event_type == "phase_change_rest":
        if lang == "no":
            return "Pause starter nå."
        return "Recovery starts now."

    if event_type == "phase_change_warmup":
        if lang == "no":
            return "Oppvarming starter nå."
        return "Warmup starts now."

    if event_type == "phase_change_cooldown":
        if lang == "no":
            return "Nedtrapping starter nå."
        return "Cooldown starts now."

    if event_type == "pause_detected":
        if lang == "no":
            return "Du har pauset økten."
        return "Workout paused."

    if event_type == "pause_resumed":
        if lang == "no":
            return "Økten er i gang igjen."
        return "Workout resumed."

    if event_type == "structure_instruction_work":
        return "Drag starter nå. Øk farten." if lang == "no" else "Interval starts now. Bring up the pace."

    if event_type == "structure_instruction_recovery":
        return "Pause nå. Ro ned og hent deg inn." if lang == "no" else "Recovery now. Ease off and reset."

    if event_type == "structure_instruction_steady":
        return "Rolig tempo nå. Hold det jevnt." if lang == "no" else "Easy pace now. Keep it steady."

    if event_type == "structure_instruction_finish":
        return "Siste drag nå. Avslutt sterkt." if lang == "no" else "Final push now. Finish strong."

    if event_type == "max_silence_override":
        if segment == "work":
            return "Hold rytmen." if lang == "no" else "Hold the rhythm."
        if segment in {"rest", "recovery"}:
            return "Senk skuldrene." if lang == "no" else "Relax your shoulders."
        return "Finn rytmen." if lang == "no" else "Find your pace."

    if event_type == "max_silence_breath_guide":
        if segment == "work":
            return "Hold rytmen." if lang == "no" else "Hold the rhythm."
        if segment in {"rest", "recovery"}:
            return "Senk skuldrene." if lang == "no" else "Relax your shoulders."
        return "Finn rytmen." if lang == "no" else "Find your pace."

    if event_type == "max_silence_go_by_feel":
        if segment == "work":
            return "Hold rytmen." if lang == "no" else "Hold the rhythm."
        if segment in {"rest", "recovery"}:
            return "Senk skuldrene." if lang == "no" else "Relax your shoulders."
        return "Finn rytmen." if lang == "no" else "Find your pace."

    if event_type == "max_silence_motivation":
        if lang == "no":
            return "Bra innsats. Fortsett slik."
        return "Strong work. Keep it up."

    return ""


def evaluate_zone_tick(
    *,
    workout_state: Dict[str, Any],
    workout_mode: str,
    phase: str,
    elapsed_seconds: int,
    language: str,
    persona: str,
    coaching_style: Optional[str],
    interval_template: Optional[str],
    heart_rate: Any,
    hr_quality: Any,
    hr_confidence: Any,
    hr_sample_age_seconds: Any,
    hr_sample_gap_seconds: Any,
    movement_score: Any,
    cadence_spm: Any,
    movement_source: Any,
    watch_connected: Any,
    watch_status: Any,
    hr_max: Any,
    resting_hr: Any,
    age: Any,
    config_module,
    warmup_seconds: Any = None,
    breath_intensity: Any = None,
    breath_signal_quality: Any = None,
    breath_summary: Any = None,
    session_id: Optional[str] = None,
    paused: Any = None,
) -> Dict[str, Any]:
    _ = persona  # Persona must not influence event decisions.
    state = _zone_state(workout_state)
    style = normalize_coaching_style(coaching_style, config_module)
    template = normalize_interval_template(interval_template, config_module)
    lang = "no" if language == "no" else "en"

    canonical_workout_type = _canonical_workout_type(workout_mode)
    selected_intensity = _style_to_intensity(style)
    session_identifier = (
        str(session_id).strip()
        if session_id is not None and str(session_id).strip()
        else "unknown_session"
    )

    profile = _resolve_hr_profile(hr_max, resting_hr, age)
    hr_bpm = _safe_int(heart_rate)
    hr_quality_info = _evaluate_hr_quality(
        hr_bpm=hr_bpm,
        hr_quality_hint=(str(hr_quality).strip().lower() if hr_quality is not None else None),
        hr_confidence=_safe_float(hr_confidence),
        hr_sample_age_seconds=_safe_float(hr_sample_age_seconds),
        hr_sample_gap_seconds=_safe_float(hr_sample_gap_seconds),
        watch_connected=_safe_bool(watch_connected),
        watch_status=(str(watch_status).strip().lower() if watch_status is not None else None),
        state=state,
        config_module=config_module,
    )
    state["hr_quality_state"] = hr_quality_info["state"]

    dt_seconds = _tick_delta_seconds(state, int(elapsed_seconds), config_module)
    hr_good_now = hr_quality_info["state"] == "good" and hr_bpm is not None and hr_bpm > 0
    hr_signal_events = _update_hr_signal_state(
        state=state,
        hr_good_now=hr_good_now,
        dt_seconds=dt_seconds,
        config_module=config_module,
    )
    hr_signal_state = str(state.get("hr_signal_state") or "lost")

    movement_signal = _resolve_movement_signal(
        movement_score_value=movement_score,
        cadence_spm_value=cadence_spm,
        movement_source_value=movement_source,
    )
    movement_state, _movement_event = _apply_movement_state(
        state=state,
        movement_score=movement_signal.get("movement_score"),
        hr_quality_state=hr_quality_info["state"],
        hr_delta_bpm=hr_quality_info.get("hr_delta_bpm"),
        hr_sample_gap_seconds=hr_quality_info.get("hr_sample_gap_seconds"),
        elapsed_seconds=int(elapsed_seconds),
        config_module=config_module,
    )
    movement_available = (
        movement_signal.get("movement_score") is not None
        or movement_signal.get("cadence_spm") is not None
    )

    breath_reliable = _update_breath_reliability(
        state=state,
        breath_signal_quality=breath_signal_quality,
        breath_summary=breath_summary,
        dt_seconds=dt_seconds,
        config_module=config_module,
    )
    sensor_notice_events = _resolve_sensor_mode(
        state=state,
        hr_signal_state=hr_signal_state,
        breath_reliable=breath_reliable,
        movement_available=movement_available,
        elapsed_seconds=int(elapsed_seconds),
        watch_connected=_safe_bool(watch_connected),
        watch_status=(str(watch_status).strip().lower() if watch_status is not None else None),
        config_module=config_module,
    )
    sensor_mode = str(state.get("sensor_mode") or "NO_SENSORS")
    breath_summary_data = breath_summary if isinstance(breath_summary, dict) else {}
    breath_cue_due = bool(breath_summary_data.get("cue_due"))
    breath_cue_interval_seconds = _safe_int(breath_summary_data.get("cue_interval_seconds"))
    breath_quality_median = _safe_float(breath_summary_data.get("quality_median"))
    breath_quality_sample_count = _safe_int(breath_summary_data.get("quality_sample_count"))
    breath_quality_reliable = bool(breath_summary_data.get("quality_reliable"))
    breath_guidance_level = _breath_guidance_level(
        breath_quality_reliable=breath_quality_reliable,
        breath_quality_median=breath_quality_median,
        config_module=config_module,
    )
    high_confidence_breath_guidance = _has_high_confidence_breath_guidance(
        breath_quality_reliable=breath_quality_reliable,
        breath_quality_median=breath_quality_median,
        config_module=config_module,
    )

    state_warmup_remaining = _safe_int(workout_state.get("warmup_remaining_s"))
    resolved_warmup_remaining = state_warmup_remaining
    if resolved_warmup_remaining is None:
        legacy_warmup_total = _safe_int(warmup_seconds)
        if legacy_warmup_total is not None and (phase or "").strip().lower() == "warmup":
            # Legacy fallback for older callers that still pass warmup_seconds total.
            resolved_warmup_remaining = max(0, int(legacy_warmup_total) - max(0, int(elapsed_seconds)))

    target = _resolve_target(
        workout_mode=workout_mode,
        phase=phase,
        coaching_style=style,
        interval_template=template,
        elapsed_seconds=int(elapsed_seconds),
        warmup_remaining_seconds=resolved_warmup_remaining,
        workout_state=workout_state,
        profile=profile,
        config_module=config_module,
    )

    canonical_phase = _canonical_phase(
        workout_mode=workout_mode,
        request_phase=phase,
        segment=str(target.get("segment", "")),
    )
    workout_context_summary = _build_workout_context_summary(
        workout_type=canonical_workout_type,
        phase=canonical_phase,
        elapsed_seconds=int(elapsed_seconds),
        target=target,
    )

    phase_events: List[str] = []
    countdown_phase_overrides: Dict[str, str] = {}
    if int(state.get("phase_id", 0)) <= 0:
        state["phase_id"] = 1
    previous_phase = state.get("canonical_phase")
    if previous_phase != canonical_phase:
        if previous_phase is not None:
            state["phase_id"] = int(state.get("phase_id", 1)) + 1
        state["canonical_phase"] = canonical_phase
        if canonical_phase == "warmup":
            phase_events.append("warmup_started")
        elif canonical_phase == "cooldown":
            phase_events.append("cooldown_started")
        if previous_phase == "warmup" and canonical_phase in {"main", "work", "recovery"}:
            phase_events.append("interval_countdown_start")
            countdown_phase_overrides["interval_countdown_start"] = "warmup"

    if _should_emit_main_started(
        state=state,
        previous_phase=previous_phase,
        canonical_phase=canonical_phase,
        elapsed_seconds=int(elapsed_seconds),
        config_module=config_module,
    ):
        phase_events.append("main_started")
        state["main_started_emitted"] = True

    if (
        not bool(state.get("session_finished"))
        and canonical_workout_type == "intervals"
        and target.get("session_end_seconds") is not None
        and int(elapsed_seconds) >= int(target.get("session_end_seconds") or 0)
    ):
        phase_events.append("workout_finished")
        state["session_finished"] = True

    pause_flag = (_safe_bool(paused) is True) or movement_state == "paused"
    target_enforced = bool(target.get("hr_enforced"))
    hr_available = (
        hr_signal_state == "ok"
        and hr_quality_info["state"] == "good"
        and hr_bpm is not None
        and hr_bpm > 0
    )
    hr_ok_for_zone_events = hr_available and float(state.get("hr_valid_streak_seconds", 0.0)) >= 5.0
    sensor_fusion_mode = _resolve_sensor_fusion_mode(
        sensor_mode=sensor_mode,
        hr_ok_for_zone_events=hr_ok_for_zone_events,
        target_enforced=target_enforced,
        breath_reliable=breath_reliable,
        movement_available=movement_available,
    )
    instruction_mode = _resolve_instruction_mode(
        target_enforced=target_enforced,
        hr_signal_state=hr_signal_state,
        sensor_mode=sensor_mode,
    )
    previous_instruction_mode = state.get("instruction_mode")
    state["instruction_mode"] = instruction_mode

    if instruction_mode == "hr_driven":
        state["structure_mode_notice_pending"] = False
        # Only re-arm the no-HR mode notice after real live-HR restoration, not
        # on transient state churn. The next loss episode can then announce once.
        if hr_ok_for_zone_events:
            state["structure_mode_notice_sent"] = False
    elif (
        previous_instruction_mode != "structure_driven"
        and not bool(state.get("structure_mode_notice_sent"))
    ):
        state["structure_mode_notice_pending"] = True

    zone_status = "hr_unstable" if not hr_available else "timing_control"
    transition_event = None

    if hr_ok_for_zone_events and target_enforced and sensor_mode == "FULL_HR":
        candidate = _zone_candidate(
            hr_bpm=hr_bpm,
            low=int(target["target_low"]),
            high=int(target["target_high"]),
            prev_confirmed=state.get("confirmed_zone_status", "in_zone"),
            config_module=config_module,
        )
        zone_status, transition_event = _apply_zone_transition(
            state=state,
            candidate=candidate,
            elapsed_seconds=int(elapsed_seconds),
            config_module=config_module,
        )
    elif not target_enforced:
        zone_status = "timing_control"

    recovery_seconds = None
    if transition_event == "above_zone":
        state["last_above_zone_elapsed"] = float(elapsed_seconds)
    elif transition_event == "in_zone_recovered":
        last_above = _safe_float(state.get("last_above_zone_elapsed"))
        if last_above is not None and float(elapsed_seconds) >= last_above:
            recovery_seconds = max(0.0, float(elapsed_seconds) - last_above)
            metrics = state.setdefault("metrics", {})
            samples = metrics.setdefault("recovery_samples", [])
            samples.append(recovery_seconds)
            max_samples = int(getattr(config_module, "ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES", 24))
            if len(samples) > max_samples:
                del samples[:-max_samples]
        state["last_above_zone_elapsed"] = None

    _update_metrics(
        state=state,
        zone_status=zone_status,
        in_main_set=bool(target.get("main_set")),
        hr_quality_state=("good" if hr_available else "poor"),
        transition_event=transition_event,
        elapsed_seconds=int(elapsed_seconds),
        hr_bpm=hr_bpm,
        target=target,
        movement_state=movement_state,
        config_module=config_module,
    )
    metrics_snapshot = state.get("metrics", {})
    score_payload = _score_from_metrics(metrics_snapshot, lang)

    suppressed_notice_events: set[str] = set()
    if instruction_mode == "structure_driven":
        suppressed_notice_events.update({
            "hr_signal_lost",
            "watch_disconnected_notice",
            "no_sensors_notice",
        })
    if (str(watch_status or "").strip().lower() == "watch_starting"):
        suppressed_notice_events.update({
            "hr_structure_mode_notice",
            "watch_disconnected_notice",
            "no_sensors_notice",
        })
    if target_enforced and "hr_signal_restored" in hr_signal_events:
        suppressed_notice_events.add("watch_restored_notice")

    event_types: List[str] = []
    for candidate_event in phase_events + hr_signal_events + sensor_notice_events:
        if candidate_event in suppressed_notice_events:
            continue
        if candidate_event and candidate_event not in event_types:
            event_types.append(candidate_event)

    if (
        instruction_mode == "structure_driven"
        and bool(state.get("structure_mode_notice_pending"))
        and not bool(state.get("structure_mode_notice_sent"))
        and "hr_structure_mode_notice" not in suppressed_notice_events
        and "hr_structure_mode_notice" not in event_types
    ):
        event_types.append("hr_structure_mode_notice")

    if canonical_phase == "warmup" and not pause_flag and target.get("segment_remaining_seconds") is not None:
        remaining = int(max(0, target.get("segment_remaining_seconds") or 0))
        fired = state.setdefault("countdown_fired_map", {})
        phase_id = int(state.get("phase_id", 1))
        # Compatibility note: keep interval_countdown_* names for iOS v1 router.
        # Warmup meaning is disambiguated by canonical phase + key namespace.
        for threshold in (30, 10, 5):
            countdown_kind = f"countdown_{threshold}"
            event_key = f"{phase_id}:warmup:{countdown_kind}"
            if remaining <= threshold and not bool(fired.get(event_key)):
                event_name = f"interval_countdown_{threshold}"
                event_types.append(event_name)
                countdown_phase_overrides[event_name] = "warmup"
                fired[event_key] = True
                logger.info(
                    "COUNTDOWN_EMIT phase=warmup threshold=%s phase_id=%s remaining=%s",
                    threshold,
                    phase_id,
                    remaining,
                )

    if (
        canonical_workout_type == "intervals"
        and canonical_phase == "recovery"
        and not pause_flag
        and target.get("rest_seconds") is not None
        and target.get("segment_remaining_seconds") is not None
    ):
        recovery_seconds_total = int(target.get("rest_seconds") or 0)
        remaining = int(max(0, target.get("segment_remaining_seconds") or 0))
        if recovery_seconds_total > 0:
            fired = state.setdefault("countdown_fired_map", {})
            phase_id = int(state.get("phase_id", 1))
            for threshold in _prep_countdown_thresholds(recovery_seconds_total):
                countdown_kind = "countdown_start" if threshold == 0 else f"countdown_{threshold}"
                event_key = f"{phase_id}:recovery:{countdown_kind}"
                if remaining <= threshold and not bool(fired.get(event_key)):
                    event_name = "interval_countdown_start" if threshold == 0 else f"interval_countdown_{threshold}"
                    event_types.append(event_name)
                    countdown_phase_overrides[event_name] = "recovery"
                    fired[event_key] = True
                    logger.info(
                        "COUNTDOWN_EMIT phase=recovery threshold=%s phase_id=%s remaining=%s",
                        "start" if threshold == 0 else threshold,
                        phase_id,
                        remaining,
                    )

    if not pause_flag:
        fired = state.setdefault("countdown_fired_map", {})
        phase_id = int(state.get("phase_id", 1))

        halfway_phase_key: Optional[str] = None
        halfway_total_seconds: Optional[int] = None
        halfway_remaining_seconds: Optional[int] = None

        if canonical_phase == "warmup" and target.get("segment_remaining_seconds") is not None:
            halfway_phase_key = "warmup"
            halfway_total_seconds = _safe_int(target.get("warmup_seconds"))
            halfway_remaining_seconds = int(max(0, target.get("segment_remaining_seconds") or 0))
        elif canonical_workout_type == "intervals" and canonical_phase == "work" and target.get("segment_remaining_seconds") is not None:
            halfway_phase_key = "work"
            halfway_total_seconds = _safe_int(target.get("work_seconds"))
            halfway_remaining_seconds = int(max(0, target.get("segment_remaining_seconds") or 0))
        elif canonical_workout_type == "easy_run" and canonical_phase == "main" and target.get("segment_remaining_seconds") is not None:
            halfway_phase_key = "main"
            elapsed_segment = _safe_int(target.get("segment_elapsed_seconds"))
            remaining_segment = _safe_int(target.get("segment_remaining_seconds"))
            if elapsed_segment is not None and remaining_segment is not None:
                halfway_total_seconds = max(0, int(elapsed_segment) + int(remaining_segment))
                halfway_remaining_seconds = int(max(0, remaining_segment))

        halfway_threshold = _segment_halfway_remaining_threshold(halfway_total_seconds)
        if (
            halfway_phase_key is not None
            and halfway_threshold is not None
            and halfway_remaining_seconds is not None
        ):
            event_key = f"{phase_id}:{halfway_phase_key}:countdown_halfway"
            if halfway_remaining_seconds <= halfway_threshold and not bool(fired.get(event_key)):
                if "interval_countdown_30" not in event_types:
                    event_types.append("interval_countdown_halfway")
                    logger.info(
                        "COUNTDOWN_EMIT phase=%s threshold=halfway phase_id=%s remaining=%s total=%s",
                        halfway_phase_key,
                        phase_id,
                        halfway_remaining_seconds,
                        halfway_total_seconds,
                    )
                else:
                    logger.info(
                        "COUNTDOWN_SUPPRESS phase=%s threshold=halfway reason=countdown_30 phase_id=%s remaining=%s total=%s",
                        halfway_phase_key,
                        phase_id,
                        halfway_remaining_seconds,
                        halfway_total_seconds,
                    )
                fired[event_key] = True

        if canonical_workout_type == "intervals" and canonical_phase in {"work", "recovery"}:
            warmup_seconds_total = _safe_int(target.get("warmup_seconds")) or 0
            work_seconds_total = _safe_int(target.get("work_seconds")) or 0
            rest_seconds_total = _safe_int(target.get("rest_seconds")) or 0
            reps_total = _safe_int(target.get("reps")) or 0
            cycle_seconds = max(0, work_seconds_total + rest_seconds_total)
            main_set_total_seconds = max(0, reps_total * cycle_seconds)
            main_set_elapsed_seconds = max(0, int(elapsed_seconds) - warmup_seconds_total)
            main_set_elapsed_seconds = min(main_set_total_seconds, main_set_elapsed_seconds)
            main_halfway_threshold = int(math.ceil(float(main_set_total_seconds) / 2.0)) if main_set_total_seconds > 0 else None
            event_key = "session:countdown_session_halfway"
            if (
                main_halfway_threshold is not None
                and main_set_elapsed_seconds >= main_halfway_threshold
                and not bool(fired.get(event_key))
            ):
                if "interval_countdown_30" not in event_types:
                    event_types.append("interval_countdown_session_halfway")
                    logger.info(
                        "COUNTDOWN_EMIT phase=interval_session threshold=halfway elapsed=%s total=%s reps=%s",
                        main_set_elapsed_seconds,
                        main_set_total_seconds,
                        reps_total,
                    )
                else:
                    logger.info(
                        "COUNTDOWN_SUPPRESS phase=interval_session threshold=halfway reason=countdown_30 elapsed=%s total=%s reps=%s",
                        main_set_elapsed_seconds,
                        main_set_total_seconds,
                        reps_total,
                    )
                fired[event_key] = True

    if not pause_flag and target_enforced and hr_ok_for_zone_events and sensor_mode == "FULL_HR":
        if transition_event == "above_zone":
            event_types.append("exited_target_above")
        elif transition_event == "below_zone":
            event_types.append("exited_target_below")
        elif transition_event == "in_zone_recovered":
            event_types.append("entered_target")

    # ---- Stage-based motivation events ----
    # Fires when user holds target zone during work (intervals) or main (easy_run).
    _motivation_event = _evaluate_motivation_event(
        state=state,
        canonical_workout_type=canonical_workout_type,
        canonical_phase=canonical_phase,
        zone_status=zone_status,
        target=target,
        elapsed_seconds=int(elapsed_seconds),
        pause_flag=pause_flag,
        hr_ok_for_zone_events=hr_ok_for_zone_events,
        target_enforced=target_enforced,
        sensor_mode=sensor_mode,
        instruction_mode=instruction_mode,
        event_types=event_types,
        breath_guidance_level=breath_guidance_level,
        breath_intensity=breath_intensity,
        config_module=config_module,
    )
    if _motivation_event:
        event_types.append(_motivation_event)

    event_types = [event for event in event_types if event]
    event_types = sorted(event_types, key=_event_priority, reverse=True)

    legacy_style_event_map = {
        "entered_target",
        "exited_target_above",
        "exited_target_below",
        "hr_structure_mode_notice",
    }
    primary_event: Optional[str] = None
    event_type: Optional[str] = None
    should_speak = False
    reason = "zone_no_change"
    style_block_reason: Optional[str] = None
    blocked_event_type: Optional[str] = None

    for candidate_event in event_types:
        mapped_legacy_event = _canonical_to_legacy_event(candidate_event)
        if candidate_event in legacy_style_event_map:
            allowed, allow_reason = _allow_style_event(
                state=state,
                event_type=mapped_legacy_event or candidate_event,
                style=style,
                elapsed_seconds=int(elapsed_seconds),
                hr_quality_state=hr_quality_info["state"],
                config_module=config_module,
            )
            if not allowed:
                style_block_reason = allow_reason
                if blocked_event_type is None:
                    blocked_event_type = mapped_legacy_event or candidate_event
                continue

        primary_event = candidate_event
        event_type = mapped_legacy_event or candidate_event
        should_speak = True
        reason = candidate_event
        break

    if not should_speak and blocked_event_type is not None:
        event_type = blocked_event_type

    if not should_speak and style_block_reason:
        reason = style_block_reason

    # Unified event path owns bounded silence behavior for event-capable workouts.
    if not should_speak and not pause_flag and not bool(state.get("session_finished")):
        context_aware_enabled = bool(getattr(config_module, "CONTEXT_AWARE_MAX_SILENCE_ENABLED", True))
        max_silence_seconds = max(1, int(getattr(config_module, "MAX_SILENCE_SECONDS", 30)))
        if context_aware_enabled:
            max_silence_seconds = _compute_max_silence_seconds(
                workout_type=canonical_workout_type,
                phase=canonical_phase,
                elapsed_minutes=max(0, int(elapsed_seconds) // 60),
                hr_missing=not hr_available,
                config_module=config_module,
            )
        if (
            sensor_mode in {"BREATH_FALLBACK", "NO_SENSORS"}
            and high_confidence_breath_guidance
            and breath_cue_interval_seconds is not None
            and breath_cue_interval_seconds > 0
        ):
            # Align no-HR fallback cadence with breathing timeline to avoid long generic silence.
            timeline_cap = max(8, int(breath_cue_interval_seconds))
            if breath_cue_due:
                max_silence_seconds = min(max_silence_seconds, timeline_cap)
            else:
                max_silence_seconds = min(max_silence_seconds, timeline_cap + 8)

        last_spoken_elapsed = _safe_float(state.get("last_spoken_elapsed"))
        if last_spoken_elapsed is not None:
            elapsed_since_spoken = max(0.0, float(elapsed_seconds) - last_spoken_elapsed)
            if elapsed_since_spoken >= float(max_silence_seconds):
                max_silence_allowed = True
                max_silence_candidate: Optional[str] = None

                if canonical_workout_type == "easy_run":
                    last_max_silence_elapsed = _safe_float(state.get("last_max_silence_elapsed"))
                    easy_run_budget_seconds = float(
                        getattr(config_module, "MAX_SILENCE_BUDGET_EASY_RUN_SECONDS", 90)
                    )
                    if (
                        last_max_silence_elapsed is not None
                        and (float(elapsed_seconds) - last_max_silence_elapsed) < easy_run_budget_seconds
                    ):
                        max_silence_allowed = False

                if canonical_workout_type == "intervals":
                    phase_id = int(state.get("phase_id", 1))
                    if _safe_int(state.get("last_max_silence_phase_id")) == phase_id:
                        max_silence_allowed = False

                    remaining_phase_seconds = _safe_int(target.get("segment_remaining_seconds"))
                    suppress_remaining = int(
                        getattr(config_module, "MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING", 35)
                    )
                    if (
                        canonical_phase == "recovery"
                        and remaining_phase_seconds is not None
                        and remaining_phase_seconds <= suppress_remaining
                    ):
                        max_silence_allowed = False

                    work_ramp_seconds = int(
                        getattr(config_module, "MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS", 12)
                    )
                    elapsed_in_phase_seconds = _safe_int(target.get("segment_elapsed_seconds"))
                    if (
                        canonical_phase == "work"
                        and elapsed_in_phase_seconds is not None
                        and elapsed_in_phase_seconds < work_ramp_seconds
                    ):
                        max_silence_allowed = False

                if max_silence_allowed:
                    if instruction_mode == "structure_driven":
                        if not bool(state.get("structure_mode_notice_pending")):
                            segment_key = str(target.get("segment_key") or canonical_phase).strip()
                            prior_structure_segment_key = str(
                                state.get("last_structure_instruction_segment_key") or ""
                            ).strip()
                            if _prefer_structure_mode_motivation(
                                state=state,
                                canonical_workout_type=canonical_workout_type,
                                canonical_phase=canonical_phase,
                                target=target,
                                elapsed_seconds=int(elapsed_seconds),
                                config_module=config_module,
                            ):
                                max_silence_candidate = "max_silence_motivation"
                            elif prior_structure_segment_key == segment_key:
                                (
                                    max_silence_candidate,
                                    state["_pending_fallback_phrase_id"],
                                ) = _pick_fallback_tone_selection(
                                    state=state,
                                    segment=str(target.get("segment", "")),
                                    breath_guidance_level=breath_guidance_level,
                                    breath_intensity=breath_intensity,
                                )
                            else:
                                max_silence_candidate = _select_structure_instruction_event(
                                    canonical_workout_type=canonical_workout_type,
                                    canonical_phase=canonical_phase,
                                    target=target,
                                    workout_state=workout_state if isinstance(workout_state, dict) else None,
                                    config_module=config_module,
                                )
                    elif sensor_fusion_mode == "HR_ZONE":
                        max_silence_candidate = "max_silence_override"
                    elif sensor_fusion_mode in {"BREATH_MOVEMENT", "BREATH_ONLY"}:
                        (
                            max_silence_candidate,
                            state["_pending_fallback_phrase_id"],
                        ) = _pick_fallback_tone_selection(
                            state=state,
                            segment=str(target.get("segment", "")),
                            breath_guidance_level=breath_guidance_level,
                            breath_intensity=breath_intensity,
                        )
                    elif not hr_available:
                        # No HR + no reliable breath: keep deterministic go-by-feel fallback.
                        (
                            max_silence_candidate,
                            state["_pending_fallback_phrase_id"],
                        ) = _pick_fallback_tone_selection(
                            state=state,
                            segment=str(target.get("segment", "")),
                            breath_guidance_level=breath_guidance_level,
                            breath_intensity=breath_intensity,
                        )
                    elif sensor_fusion_mode in {"MOVEMENT_ONLY", "TIMING_ONLY"}:
                        max_silence_candidate = "max_silence_motivation"
                    else:
                        max_silence_candidate = "max_silence_motivation"

                if max_silence_candidate == "max_silence_motivation":
                    # Drop motivation when stronger events are present in this tick.
                    motivation_priority = _event_priority("max_silence_motivation")
                    stronger_event_present = any(
                        _event_priority(candidate) > motivation_priority for candidate in event_types
                    )
                    if stronger_event_present:
                        max_silence_candidate = None
                        reason = "motivation_blocked_by_higher_tier"
                    elif not _allow_motivation_event(
                        state=state,
                        workout_type=canonical_workout_type,
                        elapsed_seconds=int(elapsed_seconds),
                        config_module=config_module,
                    ):
                        max_silence_candidate = None
                        reason = "motivation_cooldown"
                    else:
                        stage_phrase_ids = _motivation_candidate_phrase_ids_for_context(
                            workout_type=canonical_workout_type,
                            target=target,
                            elapsed_seconds=int(elapsed_seconds),
                            instruction_mode=instruction_mode,
                            breath_guidance_level=breath_guidance_level,
                            breath_intensity=breath_intensity,
                            config_module=config_module,
                        )
                        state["_pending_motivation_phrase_id"] = _pick_motivation_phrase_id(
                            state=state,
                            stage_phrase_ids=stage_phrase_ids,
                            config_module=config_module,
                        )
                elif max_silence_candidate in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
                    state["_pending_structure_phrase_id"] = _pick_structure_phrase_id(
                        state=state,
                        event_type=max_silence_candidate,
                    )

                if max_silence_candidate:
                    primary_event = max_silence_candidate
                    event_type = max_silence_candidate
                    should_speak = True
                    reason = max_silence_candidate
                    if max_silence_candidate not in event_types:
                        event_types.append(max_silence_candidate)

    event_types = sorted(set(event_types), key=_event_priority, reverse=True)

    selected_runtime_phrase_id: Optional[str] = None
    if should_speak and primary_event:
        if primary_event in _MOTIVATION_EVENT_TYPES:
            selected_runtime_phrase_id = state.get("_pending_motivation_phrase_id") or _resolve_phrase_id(primary_event, canonical_phase)
        elif primary_event in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
            selected_runtime_phrase_id = state.get("_pending_structure_phrase_id") or _resolve_phrase_id(primary_event, canonical_phase)
        elif primary_event in _FALLBACK_TONE_EVENT_TYPES:
            selected_runtime_phrase_id = state.get("_pending_fallback_phrase_id") or _resolve_phrase_id(primary_event, canonical_phase)
        else:
            selected_runtime_phrase_id = _pick_runtime_phrase_id(
                state=state,
                event_type=primary_event,
                phase=countdown_phase_overrides.get(primary_event, canonical_phase),
            )

    coach_text = None
    if should_speak and primary_event:
        state["last_spoken_elapsed"] = float(elapsed_seconds)
        if primary_event.startswith("max_silence_"):
            state["last_max_silence_elapsed"] = float(elapsed_seconds)
            if canonical_workout_type == "intervals":
                state["last_max_silence_phase_id"] = int(state.get("phase_id", 1))
        if primary_event == "max_silence_motivation":
            state["last_motivation_spoken_elapsed"] = float(elapsed_seconds)
        if primary_event in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
            structure_segment_key = str(target.get("segment_key") or canonical_phase)
            state["last_structure_instruction_segment_key"] = structure_segment_key
            if instruction_mode == "structure_driven" and canonical_workout_type in {"intervals", "easy_run"}:
                state["motivation_context_key"] = structure_segment_key
                if _safe_float(state.get("motivation_in_zone_since")) is None:
                    state["motivation_in_zone_since"] = float(elapsed_seconds)
        # Tier A/B/C events reset the motivation barrier window.
        if _event_priority(primary_event) >= 60:
            state["last_high_priority_spoken_elapsed"] = float(elapsed_seconds)
        if primary_event == "hr_structure_mode_notice":
            state["structure_mode_notice_pending"] = False
            state["structure_mode_notice_sent"] = True

        coach_text = _event_text(
            event_type=primary_event,
            language=lang,
            style=style,
            target_low=target.get("target_low"),
            target_high=target.get("target_high"),
            segment=countdown_phase_overrides.get(primary_event, str(target.get("segment", ""))),
            workout_context_summary=workout_context_summary,
        )
        if primary_event in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
            pending_structure_phrase_id = state.get("_pending_structure_phrase_id") or _resolve_phrase_id(primary_event, canonical_phase)
            structure_phrase_text = get_workout_phrase_text(str(pending_structure_phrase_id or ""), lang)
            if structure_phrase_text:
                coach_text = structure_phrase_text
        elif primary_event in _FALLBACK_TONE_EVENT_TYPES:
            pending_fallback_phrase_id = state.get("_pending_fallback_phrase_id") or _resolve_phrase_id(primary_event, canonical_phase)
            fallback_phrase_text = get_workout_phrase_text(str(pending_fallback_phrase_id or ""), lang)
            if fallback_phrase_text:
                coach_text = fallback_phrase_text
        if not coach_text and event_type:
            coach_text = _event_text(
                event_type=event_type,
                language=lang,
                style=style,
                target_low=target.get("target_low"),
                target_high=target.get("target_high"),
                segment=countdown_phase_overrides.get(event_type, str(target.get("segment", ""))),
                workout_context_summary=workout_context_summary,
            )
        if not coach_text:
            # Motivation events use phrase_id-based cached audio on iOS.
            # They don't need backend-generated coach_text.
            if primary_event not in _MOTIVATION_EVENT_TYPES:
                should_speak = False
                reason = "zone_no_text"

    max_silence_text = _event_text(
        event_type="max_silence_override",
        language=lang,
        style=style,
        target_low=target.get("target_low"),
        target_high=target.get("target_high"),
        segment=str(target.get("segment", "")),
        workout_context_summary=workout_context_summary,
    )

    zone_duration_seconds = None
    if zone_status in {"in_zone", "above_zone", "below_zone"}:
        zone_since_raw = _safe_float(state.get("zone_status_since"))
        if zone_since_raw is not None:
            zone_duration_seconds = max(0.0, float(elapsed_seconds) - zone_since_raw)

    recovery_samples = state.get("metrics", {}).get("recovery_samples", [])
    recovery_samples = [float(sample) for sample in recovery_samples if sample is not None]
    recovery_avg_seconds = None
    if recovery_samples:
        recovery_avg_seconds = round(sum(recovery_samples) / float(len(recovery_samples)), 1)

    zone_compliance = _resolve_zone_compliance(
        metrics_snapshot,
        str(target.get("segment", "")),
        config_module,
    )

    contract_hr_bpm = int(hr_bpm) if hr_available and hr_bpm is not None else 0
    canonical_zone = _canonical_zone_state(
        target_enforced=target_enforced,
        hr_available=hr_available and sensor_mode == "FULL_HR",
        zone_status=zone_status,
    )
    delta_to_band = _delta_to_band(
        hr_bpm=contract_hr_bpm,
        target_low=_safe_int(target.get("target_low")),
        target_high=_safe_int(target.get("target_high")),
        target_enforced=target_enforced,
    )
    remaining_phase_seconds = _safe_int(target.get("segment_remaining_seconds"))
    phase_id_value = int(state.get("phase_id", 1))
    now_ts = time.time()
    event_payload_base = {
        "session_id": session_identifier,
        "workout_type": canonical_workout_type,
        "phase": canonical_phase,
        "selected_intensity": selected_intensity,
        "hr_bpm": int(contract_hr_bpm),
        "target_low": _safe_int(target.get("target_low")),
        "target_high": _safe_int(target.get("target_high")),
        "target_enforced": bool(target_enforced),
        "zone_state": canonical_zone,
        "delta_to_band": delta_to_band,
        "elapsed_seconds": int(elapsed_seconds),
        "remaining_phase_seconds": int(remaining_phase_seconds) if remaining_phase_seconds is not None else None,
        "phase_id": phase_id_value,
        "sensor_mode": sensor_mode,
        "sensor_fusion_mode": sensor_fusion_mode,
        "movement_available": bool(movement_available),
        "workout_context_summary": workout_context_summary,
    }
    events_payload = []
    for event_name in event_types:
        if event_name == primary_event and selected_runtime_phrase_id:
            _phrase = selected_runtime_phrase_id
        elif event_name in _MOTIVATION_EVENT_TYPES:
            _phrase = state.get("_pending_motivation_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
        elif event_name in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
            _phrase = state.get("_pending_structure_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
        elif event_name in _FALLBACK_TONE_EVENT_TYPES:
            _phrase = state.get("_pending_fallback_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
        else:
            _phrase = _resolve_phrase_id(event_name, countdown_phase_overrides.get(event_name, canonical_phase))
        events_payload.append({
            "event_type": event_name,
            "priority": _event_priority(event_name),
            "phrase_id": _phrase,
            "ts": now_ts,
            "payload": dict(event_payload_base),
        })

    resolved_priority = _event_priority(primary_event) if primary_event else 0
    resolved_phrase_id = selected_runtime_phrase_id if primary_event else None

    # Contract hardening: every speakable event must carry both priority and phrase_id.
    for item in events_payload:
        event_name = str(item.get("event_type") or "")
        if not event_name:
            continue
        if item.get("priority") is None:
            item["priority"] = _event_priority(event_name)
        if not item.get("phrase_id"):
            if event_name == primary_event and selected_runtime_phrase_id:
                item["phrase_id"] = selected_runtime_phrase_id
            elif event_name in _MOTIVATION_EVENT_TYPES:
                item["phrase_id"] = state.get("_pending_motivation_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
            elif event_name in _STRUCTURE_INSTRUCTION_EVENT_TYPES:
                item["phrase_id"] = state.get("_pending_structure_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
            elif event_name in _FALLBACK_TONE_EVENT_TYPES:
                item["phrase_id"] = state.get("_pending_fallback_phrase_id") or _resolve_phrase_id(event_name, canonical_phase)
            else:
                item["phrase_id"] = _resolve_phrase_id(event_name, canonical_phase)

    if should_speak:
        primary_payload = next(
            (item for item in events_payload if item.get("event_type") == primary_event),
            None,
        )
        primary_payload_priority = _safe_int(primary_payload.get("priority")) if primary_payload else None
        primary_payload_phrase = str(primary_payload.get("phrase_id") or "").strip() if primary_payload else ""
        primary_contract_ok = (
            resolved_priority > 0
            and bool(str(resolved_phrase_id or "").strip())
            and primary_payload is not None
            and primary_payload_priority is not None
            and primary_payload_priority > 0
            and bool(primary_payload_phrase)
        )

        if not primary_contract_ok:
            fallback_event = "max_silence_override"
            fallback_priority = _event_priority(fallback_event)
            fallback_phrase = _resolve_phrase_id(fallback_event, canonical_phase)
            fallback_text = _event_text(
                event_type=fallback_event,
                language=lang,
                style=style,
                target_low=target.get("target_low"),
                target_high=target.get("target_high"),
                segment=str(target.get("segment", "")),
                workout_context_summary=workout_context_summary,
            )
            if fallback_priority > 0 and fallback_phrase and fallback_text:
                primary_event = fallback_event
                event_type = fallback_event
                reason = "contract_fallback_missing_phrase_or_priority"
                resolved_priority = fallback_priority
                resolved_phrase_id = fallback_phrase
                coach_text = fallback_text
                should_speak = True
                state["last_spoken_elapsed"] = float(elapsed_seconds)
                state["last_max_silence_elapsed"] = float(elapsed_seconds)
                if canonical_workout_type == "intervals":
                    state["last_max_silence_phase_id"] = int(state.get("phase_id", 1))
                fallback_payload = {
                    "event_type": fallback_event,
                    "priority": fallback_priority,
                    "phrase_id": fallback_phrase,
                    "ts": now_ts,
                    "payload": dict(event_payload_base),
                }
                events_payload = [item for item in events_payload if item.get("event_type") != fallback_event]
                events_payload.append(fallback_payload)
            else:
                should_speak = False
                reason = "contract_drop_missing_phrase_or_priority"
                event_type = None
                primary_event = None
                resolved_priority = 0
                resolved_phrase_id = None
                coach_text = None

    events_payload = sorted(
        events_payload,
        key=lambda item: _safe_int(item.get("priority")) or 0,
        reverse=True,
    )

    # Clean up pending motivation state
    state.pop("_pending_motivation_phrase_id", None)
    state.pop("_pending_motivation_stage", None)
    state.pop("_pending_structure_phrase_id", None)
    state.pop("_pending_fallback_phrase_id", None)

    # Structured observability log — one JSON line per evaluate_zone_tick() call.
    _last_spoken = _safe_float(state.get("last_spoken_elapsed"))
    _silence_secs = round(float(elapsed_seconds) - _last_spoken, 1) if _last_spoken is not None else None
    logger.info(
        "ZONE_TICK %s",
        json.dumps(
            {
                "elapsed": int(elapsed_seconds),
                "event_type": event_type,
                "primary_event": primary_event,
                "priority": resolved_priority,
                "phrase_id": resolved_phrase_id,
                "should_speak": should_speak,
                "reason": reason,
                "silence_seconds": _silence_secs,
                "sensor_mode": sensor_mode,
                "sensor_fusion_mode": sensor_fusion_mode,
                "movement_available": bool(movement_available),
                "breath_cue_due": breath_cue_due,
                "breath_cue_interval_seconds": breath_cue_interval_seconds,
                "breath_quality_median": breath_quality_median,
                "breath_quality_sample_count": breath_quality_sample_count,
                "breath_quality_reliable": breath_quality_reliable,
                "workout_type": canonical_workout_type,
                "phase": canonical_phase,
                "coaching_style": style,
            },
            separators=(",", ":"),
        ),
    )

    return {
        "handled": True,
        "should_speak": should_speak,
        "reason": reason,
        "event_type": event_type,
        "primary_event_type": primary_event,
        "priority": resolved_priority,
        "text": coach_text,
        "phrase_id": resolved_phrase_id,
        "coach_text": coach_text,
        "max_silence_text": max_silence_text,
        "events": events_payload,
        "meta": {
            "sensor_mode": sensor_mode,
            "sensor_fusion_mode": sensor_fusion_mode,
            "movement_available": bool(movement_available),
            "coaching_style": style,
            "workout_type": canonical_workout_type,
            "phase": canonical_phase,
            "elapsed_seconds": int(elapsed_seconds),
            "breath_cue_due": breath_cue_due,
            "breath_cue_interval_seconds": breath_cue_interval_seconds,
            "breath_quality_median": breath_quality_median,
            "breath_quality_sample_count": breath_quality_sample_count,
            "breath_quality_reliable": breath_quality_reliable,
        },
        "phase_id": phase_id_value,
        "sensor_mode": sensor_mode,
        "sensor_fusion_mode": sensor_fusion_mode,
        "movement_available": bool(movement_available),
        "phase": canonical_phase,
        "zone_status": zone_status,
        "zone_state": canonical_zone,
        "delta_to_band": delta_to_band,
        "target_zone_label": target.get("target_zone_label"),
        "target_hr_low": target.get("target_low"),
        "target_hr_high": target.get("target_high"),
        "target_source": target.get("target_source"),
        "target_hr_enforced": bool(target_enforced),
        "remaining_phase_seconds": int(remaining_phase_seconds) if remaining_phase_seconds is not None else None,
        "interval_template": template if workout_mode == "interval" else None,
        "segment": target.get("segment"),
        "segment_key": target.get("segment_key"),
        "heart_rate": contract_hr_bpm,
        "hr_delta_bpm": hr_quality_info.get("hr_delta_bpm"),
        "hr_quality": hr_quality_info["state"],
        "hr_quality_reasons": hr_quality_info["reasons"],
        "zone_duration_seconds": zone_duration_seconds,
        "movement_score": movement_signal.get("movement_score"),
        "cadence_spm": movement_signal.get("cadence_spm"),
        "movement_source": movement_signal.get("movement_source"),
        "movement_state": movement_state,
        "breath_cue_due": breath_cue_due,
        "breath_cue_interval_seconds": breath_cue_interval_seconds,
        "breath_quality_median": breath_quality_median,
        "breath_quality_sample_count": breath_quality_sample_count,
        "breath_quality_reliable": breath_quality_reliable,
        "coaching_style": style,
        "score": score_payload["score"],
        "score_line": score_payload["score_line"],
        "score_confidence": score_payload["score_confidence"],
        "time_in_target_pct": score_payload["time_in_target_pct"],
        "overshoots": score_payload["overshoots"],
        "recovery_seconds": recovery_seconds,
        "recovery_avg_seconds": recovery_avg_seconds,
        "recovery_samples_count": len(recovery_samples),
        "main_set_seconds": float(metrics_snapshot.get("main_set_seconds", 0.0)),
        "hr_valid_main_set_seconds": float(metrics_snapshot.get("hr_valid_main_set_seconds", 0.0)),
        "zone_valid_main_set_seconds": float(metrics_snapshot.get("zone_valid_main_set_seconds", 0.0)),
        "in_target_zone_valid_seconds": float(metrics_snapshot.get("in_target_zone_valid_seconds", 0.0)),
        "interval_work_zone_valid_seconds": float(metrics_snapshot.get("interval_work_zone_valid_seconds", 0.0)),
        "interval_work_in_target_seconds": float(metrics_snapshot.get("interval_work_in_target_seconds", 0.0)),
        "interval_recovery_zone_valid_seconds": float(metrics_snapshot.get("interval_recovery_zone_valid_seconds", 0.0)),
        "interval_recovery_in_target_seconds": float(metrics_snapshot.get("interval_recovery_in_target_seconds", 0.0)),
        "target_enforced_main_set_seconds": float(metrics_snapshot.get("target_enforced_main_set_seconds", 0.0)),
        "zone_compliance": zone_compliance,
        "workout_context_summary": workout_context_summary,
    }
