"""
Workout contract normalization helpers.

Single source of truth for request v2 parsing so main.py stays an orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json


def _coerce_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def _pick(form, payload: dict, *keys: str) -> Any:
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            return payload.get(key)
        if form is not None:
            value = form.get(key)
            if value not in (None, ""):
                return value
    return None


def _parse_jsonish(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


@dataclass
class WorkoutPlan:
    workout_type: str = "easy_run"
    warmup_s: Optional[int] = None
    cooldown_s: Optional[int] = None
    intervals: Dict[str, int] = field(default_factory=dict)


@dataclass
class WorkoutTickState:
    session_id: str
    elapsed_s: int = 0
    phase: str = "intense"
    paused: bool = False
    watch_connected: Optional[bool] = None
    hr_bpm: Optional[int] = None
    hr_quality: Optional[str] = None
    hr_confidence: Optional[float] = None
    movement_state: Optional[str] = None
    movement_score: Optional[float] = None
    cadence_spm: Optional[float] = None
    breath_quality: Optional[float] = None
    breath_reliable: Optional[bool] = None


@dataclass
class UserProfilePayload:
    name: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    max_hr_bpm: Optional[int] = None
    resting_hr_bpm: Optional[int] = None
    profile_updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "sex": self.sex,
            "age": self.age,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "max_hr_bpm": self.max_hr_bpm,
            "resting_hr_bpm": self.resting_hr_bpm,
            "profile_updated_at": self.profile_updated_at,
        }

    def normalized_updated_at(self) -> Optional[str]:
        if not self.profile_updated_at:
            return None
        raw = str(self.profile_updated_at).strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            return None


def profile_validation_errors(profile: UserProfilePayload) -> list[str]:
    errors: list[str] = []
    if profile.age is not None and not (10 <= int(profile.age) <= 100):
        errors.append("age_out_of_range")
    if profile.height_cm is not None and not (100 <= float(profile.height_cm) <= 250):
        errors.append("height_cm_out_of_range")
    if profile.weight_kg is not None and not (30 <= float(profile.weight_kg) <= 300):
        errors.append("weight_kg_out_of_range")
    if profile.max_hr_bpm is not None and not (120 <= int(profile.max_hr_bpm) <= 240):
        errors.append("max_hr_bpm_out_of_range")
    if profile.resting_hr_bpm is not None and not (30 <= int(profile.resting_hr_bpm) <= 120):
        errors.append("resting_hr_bpm_out_of_range")
    if profile.max_hr_bpm is not None and profile.resting_hr_bpm is not None:
        if int(profile.max_hr_bpm) <= int(profile.resting_hr_bpm):
            errors.append("max_hr_le_resting_hr")
    return errors


def normalize_continuous_contract(form, payload: Optional[dict] = None) -> dict:
    """
    Normalize v1/v2 continuous request shapes into one canonical dict.
    """
    payload = payload or {}
    contract_version = str(_pick(form, payload, "contract_version") or "1")
    plan_raw = _parse_jsonish(_pick(form, payload, "workout_plan"))
    state_raw = _parse_jsonish(_pick(form, payload, "workout_state"))
    profile_raw = _parse_jsonish(_pick(form, payload, "user_profile"))

    workout_type = (
        _pick(form, payload, "workout_type")
        or _pick(form, payload, "workout_mode")
        or plan_raw.get("workout_type")
        or "easy_run"
    )
    normalized_plan = WorkoutPlan(
        workout_type=str(workout_type).strip().lower(),
        warmup_s=_coerce_int(_pick(form, payload, "warmup_s", "warmup_seconds")) or _coerce_int(plan_raw.get("warmup_s")),
        cooldown_s=_coerce_int(_pick(form, payload, "cooldown_s")) or _coerce_int(plan_raw.get("cooldown_s")),
        intervals={
            "repeats": _coerce_int(_pick(form, payload, "repeats")) or _coerce_int(plan_raw.get("intervals", {}).get("repeats")),
            "work_s": _coerce_int(_pick(form, payload, "work_s")) or _coerce_int(plan_raw.get("intervals", {}).get("work_s")),
            "recovery_s": _coerce_int(_pick(form, payload, "recovery_s")) or _coerce_int(plan_raw.get("intervals", {}).get("recovery_s")),
        },
    )

    session_id = str(_pick(form, payload, "session_id") or state_raw.get("session_id") or "").strip()
    elapsed_s = _coerce_int(_pick(form, payload, "elapsed_s", "elapsed_seconds")) or _coerce_int(state_raw.get("elapsed_s")) or 0
    phase = str(_pick(form, payload, "phase") or state_raw.get("phase") or "intense").strip().lower()
    paused = bool(
        _coerce_bool(_pick(form, payload, "paused"))
        if _pick(form, payload, "paused") is not None
        else bool(state_raw.get("paused") or False)
    )
    tick_state = WorkoutTickState(
        session_id=session_id,
        elapsed_s=max(0, int(elapsed_s)),
        phase=phase,
        paused=paused,
        watch_connected=(
            _coerce_bool(_pick(form, payload, "watch_connected"))
            if _pick(form, payload, "watch_connected") is not None
            else _coerce_bool(state_raw.get("watch_connected"))
        ),
        hr_bpm=_coerce_int(_pick(form, payload, "hr_bpm", "heart_rate")) or _coerce_int(state_raw.get("hr_bpm")),
        hr_quality=(
            str(_pick(form, payload, "hr_quality") or state_raw.get("hr_quality")).strip().lower()
            if (_pick(form, payload, "hr_quality") or state_raw.get("hr_quality")) is not None
            else None
        ),
        hr_confidence=_coerce_float(_pick(form, payload, "hr_confidence")) or _coerce_float(state_raw.get("hr_confidence")),
        movement_state=(
            str(_pick(form, payload, "movement_state") or state_raw.get("movement_state")).strip().lower()
            if (_pick(form, payload, "movement_state") or state_raw.get("movement_state")) is not None
            else None
        ),
        movement_score=_coerce_float(_pick(form, payload, "movement_score")) or _coerce_float(state_raw.get("movement_score")),
        cadence_spm=_coerce_float(_pick(form, payload, "cadence_spm")) or _coerce_float(state_raw.get("cadence_spm")),
        breath_quality=_coerce_float(_pick(form, payload, "breath_quality")) or _coerce_float(state_raw.get("breath_quality")),
        breath_reliable=(
            _coerce_bool(_pick(form, payload, "breath_reliable"))
            if _pick(form, payload, "breath_reliable") is not None
            else _coerce_bool(state_raw.get("breath_reliable"))
        ),
    )

    profile = UserProfilePayload(
        name=(str(profile_raw.get("name")).strip() if profile_raw.get("name") not in (None, "") else None),
        sex=(str(profile_raw.get("sex")).strip().lower() if profile_raw.get("sex") not in (None, "") else None),
        age=_coerce_int(profile_raw.get("age")),
        height_cm=_coerce_float(profile_raw.get("height_cm")),
        weight_kg=_coerce_float(profile_raw.get("weight_kg")),
        max_hr_bpm=_coerce_int(profile_raw.get("max_hr_bpm")),
        resting_hr_bpm=_coerce_int(profile_raw.get("resting_hr_bpm")),
        profile_updated_at=(
            str(profile_raw.get("profile_updated_at")).strip()
            if profile_raw.get("profile_updated_at") not in (None, "")
            else None
        ),
    )

    return {
        "contract_version": contract_version,
        "workout_plan": normalized_plan,
        "workout_state": tick_state,
        "user_profile": profile,
    }


def normalize_talk_contract(form=None, payload: Optional[dict] = None) -> dict:
    payload = payload or {}
    contract_version = str(_pick(form, payload, "contract_version") or "1")
    summary_raw = _parse_jsonish(_pick(form, payload, "workout_context_summary"))
    if not summary_raw:
        summary_raw = {}
    return {
        "contract_version": contract_version,
        "workout_context_summary": {
            "phase": _pick(form, payload, "phase", "workout_phase") or summary_raw.get("phase"),
            "elapsed_s": _coerce_int(_pick(form, payload, "elapsed_s")) or _coerce_int(summary_raw.get("elapsed_s")),
            "time_left_s": _coerce_int(_pick(form, payload, "time_left_s")) or _coerce_int(summary_raw.get("time_left_s")),
            "rep_index": _coerce_int(_pick(form, payload, "rep_index")) or _coerce_int(summary_raw.get("rep_index")),
            "reps_total": _coerce_int(_pick(form, payload, "reps_total")) or _coerce_int(summary_raw.get("reps_total")),
            "rep_remaining_s": _coerce_int(_pick(form, payload, "rep_remaining_s")) or _coerce_int(summary_raw.get("rep_remaining_s")),
            "reps_remaining_including_current": _coerce_int(_pick(form, payload, "reps_remaining_including_current")) or _coerce_int(summary_raw.get("reps_remaining_including_current")),
        },
    }
