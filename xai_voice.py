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
        "average_heart_rate": _clean_int("average_heart_rate"),
        "distance_meters": _clean_float("distance_meters"),
        "coaching_style": _clean_string("coaching_style", 40),
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


def _duration_seconds_from_context(summary_context: Mapping[str, Any]) -> int | None:
    elapsed_s = summary_context.get("elapsed_s")
    if elapsed_s is not None:
        try:
            parsed = int(elapsed_s)
            if parsed >= 0:
                return parsed
        except (TypeError, ValueError):
            pass

    duration_text = str(summary_context.get("duration_text") or "").strip()
    if not duration_text or ":" not in duration_text:
        return None

    parts = duration_text.split(":")
    if not 2 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
        return None

    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        return (minutes * 60) + seconds

    hours, minutes, seconds = numbers
    return (hours * 3600) + (minutes * 60) + seconds


def _spoken_duration_from_seconds(total_seconds: int, language: str) -> str:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    total_seconds = max(0, int(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts: list[str] = []
    if hours:
        parts.append(f"{hours} {'time' if is_norwegian and hours == 1 else 'timer' if is_norwegian else 'hour' if hours == 1 else 'hours'}")
    if minutes:
        parts.append(f"{minutes} {'minutt' if is_norwegian and minutes == 1 else 'minutter' if is_norwegian else 'minute' if minutes == 1 else 'minutes'}")
    if seconds or not parts:
        parts.append(f"{seconds} {'sekund' if is_norwegian and seconds == 1 else 'sekunder' if is_norwegian else 'second' if seconds == 1 else 'seconds'}")
    return " ".join(parts)


def _spoken_duration_text(summary_context: Mapping[str, Any], language: str) -> str | None:
    parsed_seconds = _duration_seconds_from_context(summary_context)
    if parsed_seconds is not None:
        return _spoken_duration_from_seconds(parsed_seconds, language)

    raw_duration_text = str(summary_context.get("duration_text") or "").strip()
    return raw_duration_text or None


def _opening_metric_candidates(summary_context: Mapping[str, Any], language: str) -> list[str]:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    candidates: list[str] = []

    average_hr = summary_context.get("average_heart_rate")
    if average_hr is not None and int(average_hr) > 0:
        label = "Gjennomsnittspuls" if is_norwegian else "Average heart rate"
        candidates.append(f"{label}: {int(average_hr)} BPM")

    distance_m = summary_context.get("distance_meters")
    if distance_m is not None and float(distance_m) > 0:
        distance_km = float(distance_m) / 1000.0
        label = "Distanse" if is_norwegian else "Distance"
        candidates.append(f"{label}: {distance_km:.2f} km")

    zone_pct = _format_zone_pct(summary_context.get("zone_time_in_target_pct"))
    if zone_pct:
        label = "Tid i målsonen" if is_norwegian else "Time in target zone"
        candidates.append(f"{label}: {zone_pct}")

    coach_score = summary_context.get("coach_score")
    if coach_score is not None:
        label = "Coach score" if is_norwegian else "Coach score"
        candidates.append(f"{label}: {coach_score}")

    final_hr = str(summary_context.get("final_heart_rate_text") or "").strip()
    if final_hr:
        label = "Sluttpuls" if is_norwegian else "Final heart rate"
        candidates.append(f"{label}: {final_hr}")

    return candidates[:2]


def _opening_insight_cue(summary_context: Mapping[str, Any], language: str) -> str:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    zone_pct = _format_zone_pct(summary_context.get("zone_time_in_target_pct"))
    overshoots = summary_context.get("zone_overshoots")
    average_hr = summary_context.get("average_heart_rate")
    coaching_style = str(summary_context.get("coaching_style") or "").strip()
    distance_m = summary_context.get("distance_meters")
    duration_seconds = _duration_seconds_from_context(summary_context)
    coach_score_summary_line = str(summary_context.get("coach_score_summary_line") or "").strip()

    if zone_pct:
        if overshoots is not None and int(overshoots) > 0:
            return (
                f"Comment briefly on zone control using {zone_pct} time in zone and {int(overshoots)} overshoots."
                if not is_norwegian
                else f"Kommenter kort sonekontrollen med {zone_pct} tid i sonen og {int(overshoots)} overshoots."
            )
        return (
            f"Comment briefly on steady zone control using {zone_pct} time in zone."
            if not is_norwegian
            else f"Kommenter kort jevn sonekontroll med {zone_pct} tid i sonen."
        )

    if average_hr is not None and int(average_hr) > 0 and coaching_style:
        return (
            f"Comment briefly on effort control using the chosen intensity '{coaching_style}' and average heart rate {int(average_hr)} BPM."
            if not is_norwegian
            else f"Kommenter kort innsatskontroll med valgt intensitet '{coaching_style}' og gjennomsnittspuls {int(average_hr)} BPM."
        )

    if distance_m is not None and float(distance_m) > 0 and duration_seconds and duration_seconds > 0:
        pace_seconds = int(round(duration_seconds / (float(distance_m) / 1000.0)))
        pace_minutes = pace_seconds // 60
        pace_remainder = pace_seconds % 60
        pace_text = f"{pace_minutes}:{pace_remainder:02d} min/km"
        return (
            f"Comment briefly on pacing using the approximate pace of {pace_text}."
            if not is_norwegian
            else f"Kommenter kort tempoet med omtrentlig fart på {pace_text}."
        )

    if coach_score_summary_line:
        return coach_score_summary_line

    return (
        "Give one short running-specific insight grounded in the summary details above."
        if not is_norwegian
        else "Gi ett kort løpsspesifikt innblikk som er forankret i sammendraget over."
    )


def _opening_recap_brief(summary_context: Mapping[str, Any], language: str) -> dict[str, Any]:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    workout_reference = _canonical_workout_reference(
        str(summary_context.get("workout_mode") or "").strip(),
        str(summary_context.get("workout_label") or "").strip(),
        is_norwegian,
    )
    return {
        "workout_reference": workout_reference,
        "duration": _spoken_duration_text(summary_context, language),
        "stats": _opening_metric_candidates(summary_context, language),
        "insight_cue": _opening_insight_cue(summary_context, language),
    }


def _summary_lines(summary_context: Mapping[str, Any], language: str) -> list[str]:
    is_norwegian = str(language or "").strip().lower().startswith("no")
    lines: list[str] = []

    workout_label = _canonical_workout_reference(
        str(summary_context.get("workout_mode") or "").strip(),
        str(summary_context.get("workout_label") or "").strip(),
        is_norwegian,
    )
    if workout_label:
        prefix = "Workout" if not is_norwegian else "Økt"
        lines.append(f"{prefix}: {workout_label}")

    duration_text = _spoken_duration_text(summary_context, language)
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


def _general_running_reference(is_norwegian: bool) -> str:
    return "generell løpeøkt" if is_norwegian else "general running workout"


def _canonical_workout_reference(workout_mode: str, workout_label: str, is_norwegian: bool) -> str:
    mode = str(workout_mode or "").strip().lower()
    label = str(workout_label or "").strip()
    label_lower = label.lower()
    generic_labels = {"", "workout", "standard", "økt", "okt"}

    if mode == "easy_run" or "easy" in label_lower or "rolig" in label_lower:
        return "Rolig tur" if is_norwegian else "Easy Run"

    if mode == "interval" or "intervall" in label_lower or "interval" in label_lower:
        return "Intervaller" if is_norwegian else "Intervals"

    if mode == "standard" or label_lower in generic_labels:
        return _general_running_reference(is_norwegian)

    return label or _general_running_reference(is_norwegian)


def _workout_mode_description(workout_mode: str, workout_label: str, is_norwegian: bool) -> str:
    """Return a context paragraph that tells the AI exactly what kind of workout this was."""
    mode = str(workout_mode or "").strip().lower()
    label = _canonical_workout_reference(workout_mode, workout_label, is_norwegian)
    label_lower = label.lower()
    general_reference = _general_running_reference(is_norwegian)

    if mode == "easy_run" or "easy" in label_lower or "rolig" in label_lower:
        if is_norwegian:
            return (
                f"Utøveren valgte '{label}' — en rolig løpetur med lavt tempo. "
                "Start med aerob base, pustekontroll, og jevn innsats."
            )
        return (
            f"The athlete chose '{label}' — a low-effort easy run. "
            "Start with aerobic base building, breathing control, and steady effort."
        )

    if mode == "interval" or "intervall" in label_lower or "interval" in label_lower:
        if is_norwegian:
            return (
                f"Utøveren valgte '{label}' — intervalltrening med vekslende høy- og lavinnsats. "
                "Start med jobb/hvile-forhold, intensitetstopper, og restitusjon mellom intervallene."
            )
        return (
            f"The athlete chose '{label}' — interval training with alternating high/low effort. "
            "Start with work/rest ratio, intensity peaks, and recovery between intervals."
        )

    # Generic "Workout" or unknown mode
    if label == general_reference:
        if is_norwegian:
            return (
                "Utøveren valgte en generell løpeøkt. "
                "Start med kondisjon, tempo, pust, pulssoner, og total varighet."
            )
        return (
            "The athlete chose a general running workout. "
            "Start with cardio effort, pacing, breathing, heart rate zones, and total duration."
        )

    if is_norwegian:
        return (
            f"Utøveren valgte '{label}' — en generell løpeøkt. "
            "Start med kondisjon, tempo, pust, pulssoner, og total varighet."
        )
    return (
        f"The athlete chose '{label}' — a general running workout. "
        "Start with cardio effort, pacing, breathing, heart rate zones, and total duration."
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
    workout_mode = str(context.get("workout_mode") or "").strip().lower()
    raw_workout_label = str(context.get("workout_label") or "").strip()
    workout_reference = _canonical_workout_reference(workout_mode, raw_workout_label, is_norwegian)
    general_reference = _general_running_reference(is_norwegian)
    if workout_reference == general_reference:
        activity_line = (
            "Utøveren fullførte nettopp en generell løpeøkt."
            if is_norwegian
            else "The athlete just completed a general running workout."
        )
    else:
        activity_line = f"The athlete just completed: {workout_reference}." if workout_reference else ""
    duration_seconds = _duration_seconds_from_context(context)
    short_duration_guard = ""
    if duration_seconds is not None and duration_seconds < 60:
        spoken_duration = _spoken_duration_from_seconds(duration_seconds, language)
        short_duration_guard = (
            f"The workout lasted only {spoken_duration}. "
            "Treat it as a very short running attempt or an early-stopped run. "
            "Do not reinterpret it as a hold, plank, set, or any non-running exercise.\n"
        )

    summary_lines = _summary_lines(context, language)
    summary_block = "\n".join(f"- {line}" for line in summary_lines) if summary_lines else "- No workout summary was provided."
    history_lines = _history_lines(history, language)
    history_block = (
        "\n".join(f"- {line}" for line in history_lines)
        if history_lines
        else "- No stored workout history overview was provided."
    )
    opening_brief = _opening_recap_brief(context, language)
    opening_stats = opening_brief["stats"]
    opening_stats_block = (
        "\n".join(f"- {line}" for line in opening_stats)
        if opening_stats
        else (
            "- No additional stat beyond duration is available; do not invent one."
            if not is_norwegian
            else "- Ingen ekstra statistikk utover varighet er tilgjengelig; ikke finn på noe."
        )
    )
    opening_workout_line = (
        opening_brief["workout_reference"]
        or ("general running workout" if not is_norwegian else "generell løpeøkt")
    )
    opening_duration_line = (
        opening_brief["duration"]
        or ("No duration provided" if not is_norwegian else "Ingen varighet oppgitt")
    )

    # Inline persona — single source of truth for post-workout voice coach.
    # Keep short: the model gets this + workout data + history in one prompt.
    persona_text = (
        "You are a personal trainer reviewing a running workout that just ended.\n"
        "Calm, direct, disciplined. Short sentences — max 2 per reply, under 25 words.\n"
        "Only reference stats explicitly provided below. Do not invent numbers, workout types, or step counts.\n"
        "One question at a time, then wait for the athlete to answer."
    )

    # Build workout-mode awareness block
    mode_awareness = _workout_mode_description(workout_mode, raw_workout_label, is_norwegian)
    if workout_reference == general_reference:
        opening_reference_rule = (
            "I åpningen skal du omtale økten som 'generell løpeøkt'. "
            "Ikke gjenta den generiske etiketten 'Økt' eller 'Standard'."
            if is_norwegian
            else "For this opening, refer to the workout as 'general running workout'. "
            "Do not repeat the raw generic label 'Workout' or 'Standard'."
        )
    else:
        opening_reference_rule = (
            f"I åpningen skal du omtale økten som '{workout_reference}'."
            if is_norwegian
            else f"For this opening, refer to the workout as '{workout_reference}'."
        )

    activity_anchor = f"{activity_line}\n" if activity_line else ""
    has_real_stats = bool(opening_stats)
    has_duration = bool(opening_brief.get("duration"))
    if has_real_stats:
        opening_rules = (
            "YOUR FIRST RESPONSE — opening recap (up to 45 words, 3 sentences):\n"
            "1. Name the workout and duration.\n"
            "2. Mention one or two stats from the recap brief below.\n"
            "3. End with a short insight or one question.\n\n"
            f"{opening_reference_rule}\n"
            "Interpret timer strings literally (00:07 = 7 seconds, not 7 minutes).\n"
            f"{short_duration_guard}"
            "If average heart rate is available, prefer it over final heart rate.\n"
            "If distance is available, you can estimate pace.\n\n"
            "Opening recap brief:\n"
            f"- Workout: {opening_workout_line}\n"
            f"- Duration: {opening_duration_line}\n"
            "- Stats (pick one or two):\n"
            f"{opening_stats_block}\n"
            f"- Insight cue: {opening_brief['insight_cue']}\n\n"
        )
    elif has_duration:
        opening_rules = (
            "YOUR FIRST RESPONSE — opening recap (up to 30 words, 2 sentences):\n"
            f"1. Acknowledge the {opening_workout_line} lasting {opening_duration_line}.\n"
            "2. Ask how the athlete felt.\n"
            "No stats are available — do NOT mention heart rate, steps, distance, score, or any numbers.\n\n"
        )
    else:
        opening_rules = (
            "YOUR FIRST RESPONSE — opening (up to 20 words, 1-2 sentences):\n"
            "Acknowledge the workout is done and ask how the athlete felt.\n"
            "No stats are available — do NOT mention heart rate, steps, distance, duration, score, or any numbers.\n\n"
        )
    common_intro = (
        f"{persona_text}\n\n"
        "You are in post-workout review mode. "
        f"{activity_anchor}"
        f"{mode_awareness}\n"
        f"Speak in {language_name}. "
        f"{athlete_line}\n\n"
        f"{opening_rules}"
        "Workout summary:\n"
        f"{summary_block}\n"
        "Workout history:\n"
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
            "threshold": float(getattr(config, "XAI_VOICE_AGENT_VAD_THRESHOLD", 0.4) or 0.4),
            "prefix_padding_ms": int(getattr(config, "XAI_VOICE_AGENT_VAD_PREFIX_PADDING_MS", 300) or 300),
            "silence_duration_ms": int(getattr(config, "XAI_VOICE_AGENT_VAD_SILENCE_DURATION_MS", 500) or 500),
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
    instructions_text = session_update.get("session", {}).get("instructions", "")
    _log = logger or __import__("logging").getLogger(__name__)
    _log.info("[voice bootstrap] instructions length=%d", len(instructions_text))
    _log.info("[voice bootstrap] instructions:\n%s", instructions_text)
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
