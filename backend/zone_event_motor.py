"""
Deterministic HR zone event motor for running workouts.

Design goals:
- Stable decisions (same inputs -> same events)
- Persona-agnostic decision logic
- Coaching style only affects cue frequency/tone (never decision outcome)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple


logger = logging.getLogger(__name__)


_STYLE_ALIASES = {
    "min": "minimal",
    "minimal": "minimal",
    "normal": "normal",
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
    metrics = state.setdefault("metrics", {})
    metrics.setdefault("total_main_set_ticks", 0)
    metrics.setdefault("in_zone_ticks", 0)
    metrics.setdefault("above_zone_ticks", 0)
    metrics.setdefault("below_zone_ticks", 0)
    metrics.setdefault("poor_ticks", 0)
    metrics.setdefault("overshoots", 0)
    metrics.setdefault("recovery_samples", [])
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
    target_label = "Z2"
    hr_enforced = True
    main_set = False

    if elapsed < warmup:
        segment = "warmup"
        target_label = "Z2"
    elif elapsed < warmup + main_set_duration:
        main_set = True
        segment_elapsed = elapsed - warmup
        rep_index = int(segment_elapsed // cycle) + 1
        within_rep = segment_elapsed % cycle
        if within_rep < work:
            segment = "work"
            target_label = str(cfg.get("work_target", "Z4"))
            hr_enforced = bool(cfg.get("work_hr_enforced", True))
        else:
            segment = "rest"
            target_label = str(cfg.get("rest_target", "Z1-2"))
            hr_enforced = True
    elif elapsed < session_end:
        segment = "cooldown"
        target_label = "Z2"

    low, high, source = _zone_bounds_for_label(target_label, profile, config_module)

    return {
        "segment": segment,
        "rep_index": rep_index,
        "segment_key": f"{segment}:{rep_index}" if segment in {"work", "rest"} else segment,
        "target_zone_label": target_label,
        "target_low": low,
        "target_high": high,
        "target_source": source,
        "hr_enforced": hr_enforced and low is not None and high is not None,
        "main_set": main_set,
    }


def _easy_run_target(phase: str, profile: Dict[str, Any], config_module) -> Dict[str, Any]:
    low, high, source = _zone_bounds_for_label("Z2", profile, config_module)
    return {
        "segment": phase,
        "rep_index": 0,
        "segment_key": f"easy_run:{phase}",
        "target_zone_label": "Z2",
        "target_low": low,
        "target_high": high,
        "target_source": source,
        "hr_enforced": low is not None and high is not None,
        "main_set": phase == "intense",
    }


def _resolve_target(
    workout_mode: str,
    phase: str,
    interval_template: str,
    elapsed_seconds: int,
    profile: Dict[str, Any],
    config_module,
) -> Dict[str, Any]:
    mode = (workout_mode or "").strip().lower()
    if mode == "interval":
        return _interval_target(interval_template, elapsed_seconds, profile, config_module)
    return _easy_run_target(phase, profile, config_module)


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
    if event_type in {"above_zone", "below_zone", "above_zone_ease", "below_zone_push"}:
        return "corrective"
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


def _update_metrics(
    *,
    state: Dict[str, Any],
    zone_status: str,
    in_main_set: bool,
    hr_quality_state: str,
    transition_event: Optional[str],
) -> None:
    if not in_main_set:
        return
    metrics = state.setdefault("metrics", {})
    metrics["total_main_set_ticks"] = int(metrics.get("total_main_set_ticks", 0)) + 1

    if hr_quality_state == "poor":
        metrics["poor_ticks"] = int(metrics.get("poor_ticks", 0)) + 1
        return

    if zone_status == "in_zone":
        metrics["in_zone_ticks"] = int(metrics.get("in_zone_ticks", 0)) + 1
    elif zone_status == "above_zone":
        metrics["above_zone_ticks"] = int(metrics.get("above_zone_ticks", 0)) + 1
    elif zone_status == "below_zone":
        metrics["below_zone_ticks"] = int(metrics.get("below_zone_ticks", 0)) + 1

    if transition_event == "above_zone":
        metrics["overshoots"] = int(metrics.get("overshoots", 0)) + 1


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
        if segment == "rest":
            return "Rolig mellom dragene." if lang == "no" else "Stay easy between reps."
        return "Hold jevn rytme." if lang == "no" else "Hold steady rhythm."

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
) -> Dict[str, Any]:
    _ = persona  # Persona must not influence event decisions.
    state = _zone_state(workout_state)
    style = normalize_coaching_style(coaching_style, config_module)
    template = normalize_interval_template(interval_template, config_module)
    lang = "no" if language == "no" else "en"

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

    target = _resolve_target(
        workout_mode=workout_mode,
        phase=phase,
        interval_template=template,
        elapsed_seconds=int(elapsed_seconds),
        profile=profile,
        config_module=config_module,
    )

    previous_quality = state.get("hr_quality_state", "unknown")
    state["hr_quality_state"] = hr_quality_info["state"]

    movement_signal = _resolve_movement_signal(
        movement_score_value=movement_score,
        cadence_spm_value=cadence_spm,
        movement_source_value=movement_source,
    )
    movement_state, movement_event = _apply_movement_state(
        state=state,
        movement_score=movement_signal.get("movement_score"),
        hr_quality_state=hr_quality_info["state"],
        hr_delta_bpm=hr_quality_info.get("hr_delta_bpm"),
        hr_sample_gap_seconds=hr_quality_info.get("hr_sample_gap_seconds"),
        elapsed_seconds=int(elapsed_seconds),
        config_module=config_module,
    )

    zone_status = "hr_unstable" if hr_quality_info["state"] == "poor" else "timing_control"
    transition_event = None

    if hr_quality_info["state"] == "good" and target["hr_enforced"] and hr_bpm is not None:
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

    sustained_event = _sustained_zone_event(
        state=state,
        zone_status=zone_status,
        elapsed_seconds=int(elapsed_seconds),
        movement_state=movement_state,
        movement_score=movement_signal.get("movement_score"),
        hr_delta_bpm=hr_quality_info.get("hr_delta_bpm"),
        hr_sample_gap_seconds=hr_quality_info.get("hr_sample_gap_seconds"),
        hr_quality_state=hr_quality_info["state"],
        breath_intensity=(str(breath_intensity).strip().lower() if breath_intensity is not None else None),
        config_module=config_module,
    )

    segment_key = target.get("segment_key")
    phase_change_event = None
    if segment_key != state.get("last_segment_key"):
        segment = str(target.get("segment", ""))
        if segment == "work":
            phase_change_event = "phase_change_work"
        elif segment == "rest":
            phase_change_event = "phase_change_rest"
        elif segment == "warmup":
            phase_change_event = "phase_change_warmup"
        elif segment == "cooldown":
            phase_change_event = "phase_change_cooldown"
        state["last_segment_key"] = segment_key

    _update_metrics(
        state=state,
        zone_status=zone_status,
        in_main_set=bool(target.get("main_set")),
        hr_quality_state=hr_quality_info["state"],
        transition_event=transition_event,
    )
    score_payload = _score_from_metrics(state.get("metrics", {}), lang)

    event_type = None
    should_speak = False
    reason = "zone_no_change"

    if hr_quality_info["state"] == "poor" and previous_quality != "poor" and not state.get("hr_poor_announced"):
        event_type = "hr_poor_enter"
        should_speak = True
        reason = event_type
        state["hr_poor_announced"] = True
    elif hr_quality_info["state"] == "poor" and movement_event:
        event_type = movement_event
        should_speak = True
        reason = event_type
    elif hr_quality_info["state"] == "poor" and phase_change_event:
        event_type = phase_change_event
        should_speak = True
        reason = event_type
    elif previous_quality == "poor" and hr_quality_info["state"] == "good":
        event_type = "hr_poor_exit"
        should_speak = True
        reason = event_type
    elif movement_event:
        event_type = movement_event
        should_speak = True
        reason = event_type
    elif phase_change_event:
        event_type = phase_change_event
        should_speak = True
        reason = event_type
    elif transition_event:
        event_type = transition_event
        should_speak = True
        reason = event_type
    elif sustained_event:
        event_type = sustained_event
        should_speak = True
        reason = event_type

    coach_text = None
    if should_speak and event_type:
        allowed, style_reason = _allow_style_event(
            state=state,
            event_type=event_type,
            style=style,
            elapsed_seconds=int(elapsed_seconds),
            hr_quality_state=hr_quality_info["state"],
            config_module=config_module,
        )
        if not allowed:
            should_speak = False
            reason = style_reason
        else:
            coach_text = _event_text(
                event_type=event_type,
                language=lang,
                style=style,
                target_low=target.get("target_low"),
                target_high=target.get("target_high"),
                segment=str(target.get("segment", "")),
            )

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

    return {
        "handled": True,
        "should_speak": should_speak,
        "reason": reason,
        "event_type": event_type,
        "coach_text": coach_text,
        "max_silence_text": max_silence_text,
        "zone_status": zone_status,
        "target_zone_label": target.get("target_zone_label"),
        "target_hr_low": target.get("target_low"),
        "target_hr_high": target.get("target_high"),
        "target_source": target.get("target_source"),
        "target_hr_enforced": bool(target.get("hr_enforced")),
        "interval_template": template if workout_mode == "interval" else None,
        "segment": target.get("segment"),
        "segment_key": target.get("segment_key"),
        "heart_rate": hr_bpm,
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
    }
