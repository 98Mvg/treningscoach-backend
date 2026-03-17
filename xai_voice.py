"""Helpers for isolated xAI Voice Agent bootstrap.

This module keeps the live voice session setup outside the workout runtime
while still using the single existing Flask backend path for auth and
analytics.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Mapping

import requests

import config
from persona_manager import PersonaManager


def voice_runtime_available() -> bool:
    return bool(getattr(config, "XAI_VOICE_AGENT_ENABLED", False)) and bool(
        str(os.getenv("XAI_API_KEY", "") or "").strip()
    )


def sanitize_post_workout_summary_context(raw_context: Any) -> dict[str, Any]:
    if not isinstance(raw_context, Mapping):
        return {}

    def _clean_string(key: str, limit: int = 160) -> str | None:
        value = raw_context.get(key)
        if value in (None, ""):
            return None
        normalized = " ".join(str(value).split())
        if not normalized:
            return None
        return normalized[:limit]

    def _clean_int(key: str) -> int | None:
        value = raw_context.get(key)
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _clean_float(key: str) -> float | None:
        value = raw_context.get(key)
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    sanitized = {
        "workout_mode": _clean_string("workout_mode", 40),
        "workout_label": _clean_string("workout_label", 80),
        "duration_text": _clean_string("duration_text", 40),
        "final_heart_rate_text": _clean_string("final_heart_rate_text", 40),
        "coach_score": _clean_int("coach_score"),
        "coach_score_summary_line": _clean_string("coach_score_summary_line", 220),
        "zone_time_in_target_pct": _clean_float("zone_time_in_target_pct"),
        "zone_overshoots": _clean_int("zone_overshoots"),
        "phase": _clean_string("phase", 40),
        "elapsed_s": _clean_int("elapsed_s"),
        "time_left_s": _clean_int("time_left_s"),
        "rep_index": _clean_int("rep_index"),
        "reps_total": _clean_int("reps_total"),
        "rep_remaining_s": _clean_int("rep_remaining_s"),
        "reps_remaining_including_current": _clean_int("reps_remaining_including_current"),
        "elapsed_source": _clean_string("elapsed_source", 40),
    }

    return {key: value for key, value in sanitized.items() if value is not None}


def sanitize_workout_history_context(raw_context: Any) -> dict[str, Any]:
    if not isinstance(raw_context, Mapping):
        return {}

    def _clean_string(value: Any, *, limit: int = 80) -> str | None:
        if value in (None, ""):
            return None
        normalized = " ".join(str(value).split())
        if not normalized:
            return None
        return normalized[:limit]

    def _clean_int(value: Any, *, min_value: int = 0, max_value: int = 100_000) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return max(min_value, min(max_value, parsed))

    sanitized: dict[str, Any] = {
        "total_workouts": _clean_int(raw_context.get("total_workouts")),
        "total_duration_minutes": _clean_int(raw_context.get("total_duration_minutes")),
        "workouts_last_7_days": _clean_int(raw_context.get("workouts_last_7_days")),
        "workouts_last_30_days": _clean_int(raw_context.get("workouts_last_30_days")),
    }

    recent_workouts = raw_context.get("recent_workouts")
    if isinstance(recent_workouts, list):
        cleaned_recent: list[dict[str, Any]] = []
        for item in recent_workouts[:20]:
            if not isinstance(item, Mapping):
                continue
            cleaned_entry = {
                "date": _clean_string(item.get("date"), limit=20),
                "duration_minutes": _clean_int(item.get("duration_minutes")),
                "final_phase": _clean_string(item.get("final_phase"), limit=40),
                "avg_intensity": _clean_string(item.get("avg_intensity"), limit=40),
                "language": _clean_string(item.get("language"), limit=8),
            }
            cleaned_entry = {key: value for key, value in cleaned_entry.items() if value is not None}
            if cleaned_entry:
                cleaned_recent.append(cleaned_entry)
        if cleaned_recent:
            sanitized["recent_workouts"] = cleaned_recent

    return {key: value for key, value in sanitized.items() if value is not None}


def _format_zone_pct(raw_value: float | None) -> str | None:
    if raw_value is None:
        return None
    pct = raw_value * 100.0 if raw_value <= 1.0 else raw_value
    pct = max(0.0, min(100.0, pct))
    return f"{pct:.0f}%"


def _summary_lines(summary_context: Mapping[str, Any], language: str) -> list[str]:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    lines: list[str] = []

    workout_label = str(summary_context.get("workout_label") or summary_context.get("workout_mode") or "").strip()
    if workout_label:
        prefix = "Workout" if not is_norwegian else "Økt"
        lines.append(f"{prefix}: {workout_label}")

    duration_text = str(summary_context.get("duration_text") or "").strip()
    if duration_text:
        prefix = "Duration" if not is_norwegian else "Varighet"
        lines.append(f"{prefix}: {duration_text}")

    final_hr = str(summary_context.get("final_heart_rate_text") or "").strip()
    if final_hr:
        prefix = "Final heart rate" if not is_norwegian else "Sluttpuls"
        lines.append(f"{prefix}: {final_hr}")

    coach_score = summary_context.get("coach_score")
    if coach_score is not None:
        prefix = "Coach score" if not is_norwegian else "Coach score"
        lines.append(f"{prefix}: {coach_score}")

    score_line = str(summary_context.get("coach_score_summary_line") or "").strip()
    if score_line:
        prefix = "Coach summary" if not is_norwegian else "Coach-oppsummering"
        lines.append(f"{prefix}: {score_line}")

    zone_pct = _format_zone_pct(summary_context.get("zone_time_in_target_pct"))
    if zone_pct:
        prefix = "Time in target zone" if not is_norwegian else "Tid i målsonen"
        lines.append(f"{prefix}: {zone_pct}")

    overshoots = summary_context.get("zone_overshoots")
    if overshoots is not None:
        prefix = "Zone overshoots" if not is_norwegian else "Sone-overshoots"
        lines.append(f"{prefix}: {overshoots}")

    avg_hr = summary_context.get("average_heart_rate")
    if avg_hr is not None and int(avg_hr) > 0:
        prefix = "Average heart rate" if not is_norwegian else "Gjennomsnittspuls"
        lines.append(f"{prefix}: {int(avg_hr)} BPM")

    distance_m = summary_context.get("distance_meters")
    if distance_m is not None and float(distance_m) > 0:
        km = float(distance_m) / 1000.0
        prefix = "Distance" if not is_norwegian else "Distanse"
        lines.append(f"{prefix}: {km:.2f} km")

    coaching_style = str(summary_context.get("coaching_style") or "").strip()
    if coaching_style:
        prefix = "Chosen intensity level" if not is_norwegian else "Valgt intensitetsnivå"
        lines.append(f"{prefix}: {coaching_style}")

    phase = str(summary_context.get("phase") or "").strip()
    if phase:
        prefix = "Last phase" if not is_norwegian else "Siste fase"
        lines.append(f"{prefix}: {phase}")

    reps_left = summary_context.get("reps_remaining_including_current")
    if reps_left is not None:
        prefix = "Reps left when summary was captured" if not is_norwegian else "Gjenstaende drag i sammendraget"
        lines.append(f"{prefix}: {reps_left}")

    return lines


def _history_lines(history_context: Mapping[str, Any], language: str) -> list[str]:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    lines: list[str] = []

    total_workouts = history_context.get("total_workouts")
    if total_workouts is not None:
        prefix = "Total stored workouts" if not is_norwegian else "Totalt lagrede okter"
        lines.append(f"{prefix}: {total_workouts}")

    total_duration_minutes = history_context.get("total_duration_minutes")
    if total_duration_minutes is not None:
        prefix = "Total stored minutes" if not is_norwegian else "Totalt lagrede minutter"
        lines.append(f"{prefix}: {total_duration_minutes}")

    workouts_last_7_days = history_context.get("workouts_last_7_days")
    if workouts_last_7_days is not None:
        prefix = "Workouts in last 7 days" if not is_norwegian else "Okter siste 7 dager"
        lines.append(f"{prefix}: {workouts_last_7_days}")

    workouts_last_30_days = history_context.get("workouts_last_30_days")
    if workouts_last_30_days is not None:
        prefix = "Workouts in last 30 days" if not is_norwegian else "Okter siste 30 dager"
        lines.append(f"{prefix}: {workouts_last_30_days}")

    recent_workouts = history_context.get("recent_workouts")
    if isinstance(recent_workouts, list):
        item_prefix = "Recent workout" if not is_norwegian else "Nylig okt"
        duration_label = "min"
        phase_label = "phase" if not is_norwegian else "fase"
        intensity_label = "intensity" if not is_norwegian else "intensitet"
        for index, workout in enumerate(recent_workouts, start=1):
            if not isinstance(workout, Mapping):
                continue
            parts: list[str] = []
            date_value = str(workout.get("date") or "").strip()
            if date_value:
                parts.append(date_value)
            duration_value = workout.get("duration_minutes")
            if duration_value is not None:
                parts.append(f"{duration_value} {duration_label}")
            phase_value = str(workout.get("final_phase") or "").strip()
            if phase_value:
                parts.append(f"{phase_label} {phase_value}")
            intensity_value = str(workout.get("avg_intensity") or "").strip()
            if intensity_value:
                parts.append(f"{intensity_label} {intensity_value}")
            if parts:
                lines.append(f"{item_prefix} {index}: {', '.join(parts)}")

    return lines


def _workout_mode_description(workout_mode: str, workout_label: str, is_norwegian: bool) -> str:
    """Return a context paragraph that tells the AI exactly what kind of workout this was."""
    label = workout_label or workout_mode or ""
    label_lower = label.lower()

    if "easy" in label_lower or "rolig" in label_lower:
        if is_norwegian:
            return (
                f"Utøveren valgte '{label}' — en rolig løpetur med lavt tempo. "
                "Fokuser på aerob base, pustekontroll, og jevn innsats. "
                "Ikke nevn intervaller, sprints, eller høy intensitet."
            )
        return (
            f"The athlete chose '{label}' — a low-effort easy run. "
            "Focus on aerobic base building, breathing control, and steady effort. "
            "Do not mention intervals, sprints, or high intensity."
        )

    if "interval" in label_lower:
        if is_norwegian:
            return (
                f"Utøveren valgte '{label}' — intervalltrening med vekslende høy- og lavinnsats. "
                "Fokuser på jobb/hvile-forhold, intensitetstopper, og restitusjon mellom intervallene."
            )
        return (
            f"The athlete chose '{label}' — interval training with alternating high/low effort. "
            "Focus on work/rest ratio, intensity peaks, and recovery between intervals."
        )

    # Generic "Workout" or unknown mode
    if is_norwegian:
        return (
            f"Utøveren valgte '{label}' — en generell treningsøkt. "
            "Fokuser på kardio-innsats, pulssoner, og total varighet. "
            "Ikke anta spesifikke øvelser eller bevegelser."
        )
    return (
        f"The athlete chose '{label}' — a general workout session. "
        "Focus on cardio effort, heart rate zones, and total duration. "
        "Do not assume any specific exercises or movements."
    )


def build_post_workout_voice_instructions(
    *,
    summary_context: Mapping[str, Any] | None,
    history_context: Mapping[str, Any] | None,
    language: str,
    user_name: str | None = None,
) -> str:
    context = sanitize_post_workout_summary_context(summary_context)
    history = sanitize_workout_history_context(history_context)
    is_norwegian = str(language or "").strip().lower().startswith("no")
    language_name = "Norwegian" if is_norwegian else "English"
    athlete_name = str(user_name or "").strip()
    athlete_line = (
        f"The athlete's name is {athlete_name}."
        if athlete_name
        else "The athlete has not shared a name."
    )
    workout_label = str(context.get("workout_label") or "").strip()
    activity_line = f"The athlete just completed: {workout_label}." if workout_label else ""

    summary_lines = _summary_lines(context, language)
    summary_block = "\n".join(f"- {line}" for line in summary_lines) if summary_lines else "- No workout summary was provided."
    history_lines = _history_lines(history, language)
    history_block = (
        "\n".join(f"- {line}" for line in history_lines)
        if history_lines
        else "- No stored workout history overview was provided."
    )

    persona_text = PersonaManager.get_system_prompt(
        persona="personal_trainer",
        language=language,
        emotional_mode="supportive",
        safety_override=False,
    )

    # Build workout-mode awareness block
    workout_mode = str(context.get("workout_mode") or "").strip().lower()
    mode_awareness = _workout_mode_description(workout_mode, workout_label, is_norwegian)

    activity_anchor = f"{activity_line}\n" if activity_line else ""
    common_intro = (
        f"{persona_text}\n\n"
        "You are now in post-workout review mode. "
        f"{activity_anchor}"
        f"{mode_awareness}\n"
        f"Speak in {language_name}. "
        "YOUR OPENING MESSAGE is special and must follow these rules:\n"
        "1. Start by acknowledging the specific workout just completed (use the workout label and duration)\n"
        "2. Mention one standout metric (average heart rate, distance, zone time, or coach score)\n"
        "3. Give a brief, specific coaching insight based on the data\n"
        "4. End with an open question about how the athlete felt\n"
        "Your opening message may be up to 40 words and 3 sentences.\n"
        "After the opening, return to the normal limit of 25 words / 2 sentences.\n\n"
        "CRITICAL — Workout type awareness:\n"
        "The athlete CHOSE this workout type before starting. Tailor ALL feedback to it.\n"
        "NEVER mention specific exercises (squats, lunges, push-ups, burpees, planks, etc.).\n"
        "NEVER guess what the athlete did physically — only reference the workout label and the data below.\n"
        "If the label says 'Easy Run', talk about pace, breathing, and aerobic base.\n"
        "If the label says 'Intervals', talk about work/rest ratio, intensity peaks, and recovery.\n"
        "If the label says 'Workout', keep it general to cardio effort and heart rate zones.\n"
        "Refer to the workout ONLY by its label. Do not invent activity details.\n"
        "The athlete also chose an intensity level (Easy/Medium/Hard) before starting. "
        "Use this to gauge whether their heart rate, zone time, and effort match their intent. "
        "If average heart rate is available, prefer it over final heart rate for overall effort assessment. "
        "If distance is available, you can compute approximate pace (distance / duration).\n\n"
        "Only reference data explicitly present in the summary below. "
        "Always cite specific numbers when available (score, duration, heart rate, zone %). "
        "Never give generic advice when specific workout data exists in the summary. "
        "After your opening message, keep responses under 2 sentences and never exceed 25 words per reply. "
        "Use the just-finished workout summary first. "
        "You may also reference the workout history overview for pattern, progress, and consistency questions. "
        "Do not claim to remember prior conversations or any data beyond the supplied summary and history overview. "
        "If the athlete asks for medical diagnosis, tell them to seek professional care.\n"
        f"{athlete_line}\n"
        "Workout summary:\n"
        f"{summary_block}\n"
        "Workout history overview:\n"
        f"{history_block}"
    )

    if is_norwegian:
        return common_intro

    return common_intro


def build_post_workout_voice_session_update(
    *,
    summary_context: Mapping[str, Any] | None,
    history_context: Mapping[str, Any] | None,
    language: str,
    user_name: str | None = None,
) -> dict[str, Any]:
    session_payload: dict[str, Any] = {
        "voice": str(getattr(config, "XAI_VOICE_AGENT_VOICE", "Rex") or "Rex").strip() or "Rex",
        "instructions": build_post_workout_voice_instructions(
            summary_context=summary_context,
            history_context=history_context,
            language=language,
            user_name=user_name,
        ),
        "turn_detection": {
            "type": "server_vad",
            "threshold": float(getattr(config, "XAI_VOICE_AGENT_VAD_THRESHOLD", 0.5) or 0.5),
            "prefix_padding_ms": int(getattr(config, "XAI_VOICE_AGENT_VAD_PREFIX_PADDING_MS", 300) or 300),
            "silence_duration_ms": int(getattr(config, "XAI_VOICE_AGENT_VAD_SILENCE_DURATION_MS", 300) or 300),
            "create_response": True,
        },
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
    }
    model = str(getattr(config, "XAI_VOICE_AGENT_MODEL", "") or "").strip()
    if model:
        session_payload["model"] = model
    return {
        "type": "session.update",
        "session": session_payload,
    }


def create_realtime_client_secret(*, max_duration_seconds: int, logger: Any = None) -> dict[str, Any]:
    api_key = str(os.getenv("XAI_API_KEY", "") or "").strip()
    if not api_key:
        raise RuntimeError("XAI_API_KEY missing")

    expires_after_seconds = max(60, int(max_duration_seconds))
    endpoint = str(
        getattr(config, "XAI_VOICE_AGENT_CLIENT_SECRET_URL", "https://api.x.ai/v1/realtime/client_secrets")
        or "https://api.x.ai/v1/realtime/client_secrets"
    ).strip()
    client_secret_timeout = float(
        getattr(config, "XAI_VOICE_AGENT_CLIENT_SECRET_TIMEOUT_SECONDS", 20.0) or 20.0
    )
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"expires_after": {"seconds": expires_after_seconds}},
        timeout=client_secret_timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if logger is not None:
        logger.info(
            "XAI voice client secret created endpoint=%s expires_after=%s",
            endpoint,
            expires_after_seconds,
        )
    return payload if isinstance(payload, dict) else {}


def extract_client_secret(payload: Mapping[str, Any]) -> tuple[str, int | None]:
    nested_client_secret = payload.get("client_secret")
    if isinstance(nested_client_secret, Mapping):
        value = str(nested_client_secret.get("value") or "").strip()
        expires_at = nested_client_secret.get("expires_at")
        return value, int(expires_at) if isinstance(expires_at, (int, float)) else None

    for key in ("value", "client_secret", "token", "secret"):
        candidate = str(payload.get(key) or "").strip()
        if candidate:
            expires_at = payload.get("expires_at")
            return candidate, int(expires_at) if isinstance(expires_at, (int, float)) else None

    return "", None


def bootstrap_post_workout_voice_session(
    *,
    summary_context: Mapping[str, Any] | None,
    history_context: Mapping[str, Any] | None,
    language: str,
    user_name: str | None = None,
    voice_session_id: str | None = None,
    max_duration_seconds: int | None = None,
    logger: Any = None,
) -> dict[str, Any]:
    resolved_max_duration_seconds = max(
        60,
        int(max_duration_seconds or getattr(config, "XAI_VOICE_AGENT_MAX_SESSION_SECONDS", 300) or 300),
    )
    realtime_secret_payload = create_realtime_client_secret(
        max_duration_seconds=resolved_max_duration_seconds,
        logger=logger,
    )
    client_secret, expires_at = extract_client_secret(realtime_secret_payload)
    if not client_secret:
        raise RuntimeError("xAI realtime client secret response missing token value")

    session_update = build_post_workout_voice_session_update(
        summary_context=summary_context,
        history_context=history_context,
        language=language,
        user_name=user_name,
    )
    return {
        "voice_session_id": str(voice_session_id or f"voice_{uuid.uuid4().hex}"),
        "websocket_url": str(
            getattr(config, "XAI_VOICE_AGENT_WEBSOCKET_URL", "wss://api.x.ai/v1/realtime")
            or "wss://api.x.ai/v1/realtime"
        ).strip(),
        "client_secret": client_secret,
        "client_secret_expires_at": expires_at,
        "voice": str(getattr(config, "XAI_VOICE_AGENT_VOICE", "Rex") or "Rex").strip() or "Rex",
        "model": str(getattr(config, "XAI_VOICE_AGENT_MODEL", "") or "").strip(),
        "region": str(getattr(config, "XAI_VOICE_AGENT_REGION", "us-east-1") or "us-east-1").strip(),
        "max_duration_seconds": resolved_max_duration_seconds,
        "summary_context": sanitize_post_workout_summary_context(summary_context),
        "session_update": session_update,
        "session_update_json": json.dumps(session_update, separators=(",", ":"), ensure_ascii=True),
    }
