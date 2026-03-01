"""
Deterministic HR zone event motor for running workouts.

Design goals:
- Stable decisions (same inputs -> same events)
- Persona-agnostic decision logic
- Coaching style only affects cue frequency/tone (never decision outcome)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


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
    """4-tier event priority: A (countdown/signal) > B (phase/notices) > C (coaching) > D (motivation)."""
    order = {
        # Tier A — countdowns + signal
        "interval_countdown_start": 100,
        "hr_signal_lost": 99,
        "hr_signal_restored": 98,
        "interval_countdown_5": 95,
        "interval_countdown_15": 94,
        "interval_countdown_30": 93,

        # Tier B — phase transitions
        "warmup_started": 90,
        "main_started": 90,
        "cooldown_started": 90,
        "workout_finished": 90,
        "pause_detected": 86,
        "pause_resumed": 85,

        # Signal notices (between B and C)
        "watch_disconnected_notice": 88,
        "no_sensors_notice": 88,
        "watch_restored_notice": 88,

        # Tier C — actionable coaching
        "exited_target_above": 70,
        "exited_target_below": 70,
        "max_silence_override": 68,
        "max_silence_breath_guide": 68,
        "max_silence_go_by_feel": 66,
        "recovery_hr_above_relax_ceiling": 65,
        "recovery_hr_ok_relax": 64,
        "entered_target": 60,

        # Tier D — motivational filler
        "max_silence_motivation": 10,
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
    config_module,
) -> Dict[str, Any]:
    templates = getattr(config_module, "INTERVAL_TEMPLATES", {})
    cfg = templates.get(interval_template) or templates.get(getattr(config_module, "DEFAULT_INTERVAL_TEMPLATE", "4x4"), {})

    warmup = int(cfg.get("warmup_seconds", 600))
    work = int(cfg.get("work_seconds", 240))
    rest = int(cfg.get("rest_seconds", 180))
    reps = int(cfg.get("reps", 4))
    cooldown = int(cfg.get("cooldown_seconds", 480))
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
        "work_seconds": work,
        "rest_seconds": rest,
        "session_end_seconds": session_end,
    }


def _easy_run_target(phase: str, profile: Dict[str, Any], intensity: str, config_module) -> Dict[str, Any]:
    normalized_phase = (phase or "").strip().lower() or "intense"
    target_intensity = "easy" if normalized_phase in {"warmup", "cooldown"} else intensity
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
        "main_set": normalized_phase == "intense",
        "segment_elapsed_seconds": None,
        "segment_remaining_seconds": None,
        "work_seconds": None,
        "rest_seconds": None,
        "session_end_seconds": None,
    }


def _resolve_target(
    workout_mode: str,
    phase: str,
    coaching_style: Optional[str],
    interval_template: str,
    elapsed_seconds: int,
    profile: Dict[str, Any],
    config_module,
) -> Dict[str, Any]:
    mode = (workout_mode or "").strip().lower()
    intensity = _style_to_intensity(coaching_style)
    if mode == "interval":
        return _interval_target(interval_template, elapsed_seconds, profile, intensity, config_module)
    return _easy_run_target(phase, profile, intensity, config_module)


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
        # - Missing/poor HR starts in "lost" and emits one loss event for compatibility.
        signal_state = "ok" if hr_good_now else "lost"
        valid_streak = 5.0 if hr_good_now else 0.0
        invalid_streak = 4.0 if not hr_good_now else 0.0
        if not hr_good_now:
            events.append("hr_signal_lost")

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

    required_samples = int(getattr(config_module, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
    required_quality = float(getattr(config_module, "CS_BREATH_MIN_RELIABLE_QUALITY", 0.35))
    median_quality = _median(samples[-max(required_samples, 6):])
    reliable_now = (
        len(samples) >= required_samples
        and median_quality is not None
        and median_quality >= required_quality
    )

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
    elapsed_seconds: int,
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

    if desired != current_mode:
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

                if (
                    previous_mode == "FULL_HR"
                    and desired in {"BREATH_FALLBACK", "NO_SENSORS"}
                    and not bool(state.get("notice_watch_disconnected_sent"))
                ):
                    events.append("watch_disconnected_notice")
                    state["notice_watch_disconnected_sent"] = True

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
                    and not bool(state.get("notice_watch_restored_sent"))
                ):
                    events.append("watch_restored_notice")
                    state["notice_watch_restored_sent"] = True
    else:
        state["sensor_mode_candidate"] = current_mode
        state["sensor_mode_candidate_since"] = float(elapsed_seconds)

    return events


def _countdown_thresholds(recovery_seconds: int) -> List[int]:
    if recovery_seconds < 30:
        return [5, 0]
    if recovery_seconds < 45:
        return [15, 5, 0]
    return [30, 15, 5, 0]


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
    gap_seconds = _safe_float(hr_sample_gap_seconds)

    if hint == "poor":
        reasons.append("client_reported_poor")

    if watch_connected is False:
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
    if event_type in {"max_silence_motivation"}:
        return "motivation"
    if event_type in {"above_zone", "below_zone", "above_zone_ease", "below_zone_push"}:
        return "corrective"
    if event_type in {"max_silence_go_by_feel", "max_silence_breath_guide", "max_silence_override"}:
        return "info"
    if event_type in {"in_zone_recovered"}:
        return "positive"
    return "info"


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
    is_phase_change = event_type.startswith("phase_change_")

    if cue_group == "corrective" and hr_quality_state == "poor":
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
    last_same = _safe_float(last_by_type.get(cue_group))
    if last_same is not None and (float(elapsed_seconds) - last_same) < min_same and not is_phase_change:
        return False, "style_cooldown_same_type"

    if cue_group == "positive":
        last_positive = _safe_float(last_by_type.get("positive"))
        if last_positive is not None and (float(elapsed_seconds) - last_positive) < praise_min:
            return False, "style_praise_cooldown"

    state["style_last_any_elapsed"] = float(elapsed_seconds)
    last_by_type[cue_group] = float(elapsed_seconds)
    state["style_history"].append(
        {"elapsed": float(elapsed_seconds), "event": event_type, "group": cue_group}
    )
    return True, "allowed"


def _allow_motivation_event(
    *,
    state: Dict[str, Any],
    workout_type: str,
    elapsed_seconds: int,
    config_module,
) -> bool:
    """Motivation cooldown barrier for Tier D events."""
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
            return "Klokken er frakoblet. Jeg coacher videre med pust og timing."
        return "Watch disconnected. I'll coach using breathing and timing."

    if event_type == "no_sensors_notice":
        if lang == "no":
            return "Ingen sensorer nå. Løp på følelse."
        return "No sensors now. Run by feel."

    if event_type == "watch_restored_notice":
        if lang == "no":
            return "Klokken er tilbake. Sonecoaching er aktiv igjen."
        return "Watch restored. Zone coaching is back."

    if event_type == "interval_countdown_30":
        return "30 sekunder igjen." if lang == "no" else "30 seconds left."

    if event_type == "interval_countdown_15":
        return "15 sekunder igjen." if lang == "no" else "15 seconds left."

    if event_type == "interval_countdown_5":
        return "5 sekunder igjen." if lang == "no" else "5 seconds left."

    if event_type == "interval_countdown_start":
        return "Neste drag nå." if lang == "no" else "Next interval now."

    if event_type == "main_started":
        if lang == "no":
            return "Hoveddel nå. Hold kontroll."
        return "Main set now. Stay controlled."

    if event_type == "workout_finished":
        if lang == "no":
            return "Økten er ferdig. Bra jobbet."
        return "Workout finished. Nice work."

    if event_type == "hr_poor_enter":
        if lang == "no":
            return "Puls-signalet er svakt akkurat nå. Jeg coacher med timing og pust til det stabiliserer seg. Stram klokka litt."
        return "Heart-rate signal is weak right now. I'll coach using timing and breathing until it stabilizes. Tighten your watch strap."

    if event_type == "hr_poor_exit":
        return "Pulsen er stabil igjen. Vi går tilbake til sonecoaching." if lang == "no" else "Heart-rate signal is stable again. Returning to zone coaching."

    if event_type == "above_zone":
        if lang == "no":
            if tone == "minimal":
                return "Litt ned 10-15 sekunder."
            if target_low is not None and target_high is not None:
                return f"Rolig ned mot {target_low}-{target_high} bpm."
            return "Litt ned. Finn kontroll."
        if tone == "minimal":
            return "Ease off 10-15 seconds."
        if target_low is not None and target_high is not None:
            return f"Back off to {target_low}-{target_high} bpm."
        return "Ease off and regain control."

    if event_type == "above_zone_ease":
        if lang == "no":
            if tone == "minimal":
                return "Pulsen stiger. Rolig ned."
            return "Pulsen stiger fortsatt. Ro ned 20 sekunder."
        if tone == "minimal":
            return "HR still climbing. Ease down."
        return "Your heart rate is still climbing. Ease down for 20 seconds."

    if event_type == "below_zone":
        if lang == "no":
            if tone == "minimal":
                return "Bygg litt opp nå."
            if target_low is not None and target_high is not None:
                return f"Løft rolig mot {target_low}-{target_high} bpm."
            return "Litt opp i innsats nå."
        if tone == "minimal":
            return "Build slightly now."
        if target_low is not None and target_high is not None:
            return f"Build toward {target_low}-{target_high} bpm."
        return "Build effort slightly now."

    if event_type == "below_zone_push":
        if lang == "no":
            if tone == "minimal":
                return "Du er i gang. Litt opp."
            return "Du er i gang. Øk litt nå og hold flyten."
        if tone == "minimal":
            return "You're moving. Add a little."
        return "You're moving well. Add a little effort and keep the flow."

    if event_type == "in_zone_recovered":
        if lang == "no":
            return "Bra. Hold deg her." if tone == "minimal" else "Der ja. Hold deg i denne sonen."
        return "Good. Stay here." if tone == "minimal" else "Nice. Hold this zone."

    if event_type == "phase_change_work":
        if lang == "no":
            return "Dragstart. Kontroller hardt." if tone != "motivational" else "Nytt drag. Sterk kontroll nå."
        return "Work block. Controlled hard." if tone != "motivational" else "New work block. Controlled hard now."

    if event_type == "phase_change_rest":
        if lang == "no":
            return "Pauseblokk. Rolig jogg."
        return "Recovery block. Easy jog."

    if event_type == "phase_change_warmup":
        if lang == "no":
            return "Oppvarming nå. Hold det lett."
        return "Warm-up now. Keep it easy."

    if event_type == "phase_change_cooldown":
        if lang == "no":
            return "Nedjogg nå. Senk pulsen."
        return "Cooldown now. Bring heart rate down."

    if event_type == "pause_detected":
        if lang == "no":
            return "Du ser ut til å ha stoppet. Start rolig igjen når du er klar."
        return "Looks like you paused. Start easy again when ready."

    if event_type == "pause_resumed":
        if lang == "no":
            return "Bra, du er i gang igjen. Hold rolig kontroll."
        return "Good, you're moving again. Keep it controlled."

    if event_type == "max_silence_override":
        if segment == "work":
            return "Hold kontroll. Ett drag av gangen." if lang == "no" else "Stay controlled. One rep at a time."
        if segment in {"rest", "recovery"}:
            return "Rolig mellom dragene." if lang == "no" else "Stay easy between reps."
        return "Hold jevn rytme." if lang == "no" else "Hold steady rhythm."

    if event_type == "max_silence_breath_guide":
        if segment == "work":
            return "Pust gjennom innsatsen." if lang == "no" else "Breathe through the effort."
        if segment in {"rest", "recovery"}:
            return "Senk pustetakten." if lang == "no" else "Slow your breathing down."
        return "Tilpass pusten til tempoet." if lang == "no" else "Match your breathing to your pace."

    if event_type == "max_silence_go_by_feel":
        if segment == "work":
            return "Trykk hardt men kontrollert." if lang == "no" else "Push hard but controlled."
        if segment in {"rest", "recovery"}:
            return "Slipp av. La kroppen hente seg inn." if lang == "no" else "Ease off. Let your body recover."
        return "Jevn innsats. Hold det behagelig." if lang == "no" else "Steady effort. Stay comfortable."

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
    breath_intensity: Any = None,
    breath_signal_quality: Any = None,
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

    breath_reliable = _update_breath_reliability(
        state=state,
        breath_signal_quality=breath_signal_quality,
        dt_seconds=dt_seconds,
        config_module=config_module,
    )
    sensor_notice_events = _resolve_sensor_mode(
        state=state,
        hr_signal_state=hr_signal_state,
        breath_reliable=breath_reliable,
        elapsed_seconds=int(elapsed_seconds),
        config_module=config_module,
    )
    sensor_mode = str(state.get("sensor_mode") or "NO_SENSORS")

    target = _resolve_target(
        workout_mode=workout_mode,
        phase=phase,
        coaching_style=style,
        interval_template=template,
        elapsed_seconds=int(elapsed_seconds),
        profile=profile,
        config_module=config_module,
    )

    canonical_phase = _canonical_phase(
        workout_mode=workout_mode,
        request_phase=phase,
        segment=str(target.get("segment", "")),
    )

    phase_events: List[str] = []
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

    if canonical_phase in {"main", "work", "recovery"} and not bool(state.get("main_started_emitted")):
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

    pause_flag = (_safe_bool(paused) is True) or movement_state == "paused"
    target_enforced = bool(target.get("hr_enforced"))
    hr_available = (
        hr_signal_state == "ok"
        and hr_quality_info["state"] == "good"
        and hr_bpm is not None
        and hr_bpm > 0
    )
    hr_ok_for_zone_events = hr_available and float(state.get("hr_valid_streak_seconds", 0.0)) >= 5.0

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

    event_types: List[str] = []
    for candidate_event in phase_events + hr_signal_events + sensor_notice_events:
        if candidate_event and candidate_event not in event_types:
            event_types.append(candidate_event)

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
            for threshold in _countdown_thresholds(recovery_seconds_total):
                event_key = f"{phase_id}:{threshold}"
                if remaining <= threshold and not bool(fired.get(event_key)):
                    event_name = "interval_countdown_start" if threshold == 0 else f"interval_countdown_{threshold}"
                    event_types.append(event_name)
                    fired[event_key] = True

    if not pause_flag and target_enforced and hr_ok_for_zone_events and sensor_mode == "FULL_HR":
        if transition_event == "above_zone":
            event_types.append("exited_target_above")
        elif transition_event == "below_zone":
            event_types.append("exited_target_below")
        elif transition_event == "in_zone_recovered":
            event_types.append("entered_target")

    event_types = [event for event in event_types if event]
    event_types = sorted(event_types, key=_event_priority, reverse=True)

    legacy_style_event_map = {
        "entered_target",
        "exited_target_above",
        "exited_target_below",
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
                    if hr_available and target_enforced and sensor_mode == "FULL_HR":
                        max_silence_candidate = "max_silence_override"
                    elif breath_reliable:
                        max_silence_candidate = "max_silence_breath_guide"
                    elif not hr_available:
                        max_silence_candidate = "max_silence_go_by_feel"
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

                if max_silence_candidate:
                    primary_event = max_silence_candidate
                    event_type = max_silence_candidate
                    should_speak = True
                    reason = max_silence_candidate
                    if max_silence_candidate not in event_types:
                        event_types.append(max_silence_candidate)

    event_types = sorted(set(event_types), key=_event_priority, reverse=True)

    coach_text = None
    if should_speak and primary_event:
        state["last_spoken_elapsed"] = float(elapsed_seconds)
        if primary_event.startswith("max_silence_"):
            state["last_max_silence_elapsed"] = float(elapsed_seconds)
            if canonical_workout_type == "intervals":
                state["last_max_silence_phase_id"] = int(state.get("phase_id", 1))
        if primary_event == "max_silence_motivation":
            state["last_motivation_spoken_elapsed"] = float(elapsed_seconds)
        else:
            # Tier A/B/C events reset the motivation barrier window.
            if _event_priority(primary_event) >= 60:
                state["last_high_priority_spoken_elapsed"] = float(elapsed_seconds)

        coach_text = _event_text(
            event_type=primary_event,
            language=lang,
            style=style,
            target_low=target.get("target_low"),
            target_high=target.get("target_high"),
            segment=str(target.get("segment", "")),
        )
        if not coach_text and event_type:
            coach_text = _event_text(
                event_type=event_type,
                language=lang,
                style=style,
                target_low=target.get("target_low"),
                target_high=target.get("target_high"),
                segment=str(target.get("segment", "")),
            )
        if not coach_text:
            should_speak = False
            reason = "zone_no_text"

    max_silence_text = _event_text(
        event_type="max_silence_override",
        language=lang,
        style=style,
        target_low=target.get("target_low"),
        target_high=target.get("target_high"),
        segment=str(target.get("segment", "")),
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
    }
    events_payload = [
        {
            "event_type": event_name,
            "ts": now_ts,
            "payload": dict(event_payload_base),
        }
        for event_name in event_types
    ]

    return {
        "handled": True,
        "should_speak": should_speak,
        "reason": reason,
        "event_type": event_type,
        "primary_event_type": primary_event,
        "coach_text": coach_text,
        "max_silence_text": max_silence_text,
        "events": events_payload,
        "phase_id": phase_id_value,
        "sensor_mode": sensor_mode,
        "zone_status": zone_status,
        "zone_state": canonical_zone,
        "delta_to_band": delta_to_band,
        "target_zone_label": target.get("target_zone_label"),
        "target_hr_low": target.get("target_low"),
        "target_hr_high": target.get("target_high"),
        "target_source": target.get("target_source"),
        "target_hr_enforced": bool(target_enforced),
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
    }
