"""
Shared taxonomy for deterministic workout cues.

This module classifies the active deterministic workout cue surface without
creating a second timing system. `zone_event_motor` still owns event timing and
selection; the taxonomy only describes wording intent.
"""

from __future__ import annotations

import re
from typing import Optional


WORKOUT_CUE_CATALOGS = ("instruction", "context", "progress", "motivation")
WORKOUT_CUE_CATALOG_SORT = {name: index for index, name in enumerate(WORKOUT_CUE_CATALOGS)}

INSTRUCTION_CORRECTIVE = "corrective"
INSTRUCTION_LOW_URGENCY = "low_urgency"

MOTIVATION_STAGE_LABELS = {
    1: "start",
    2: "steady",
    3: "push",
    4: "finish",
}

ACTIVE_WORKOUT_CUE_WORD_LIMITS = {
    "instruction": 6,
    "context": 8,
    "progress": 8,
    "motivation": 6,
}

_MOTIVATION_STAGE_PATTERN = re.compile(r"^(?:interval|easy_run)\.motivate\.s([1-4])\.\d+$")
_TOKEN_PATTERN = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ'-]+")
_SENTENCE_PATTERN = re.compile(r"[.!?]+")

_INSTRUCTION_PREFIXES = (
    "zone.above.",
    "zone.below.",
    "zone.in_zone.",
    "zone.silence.",
    "zone.structure.",
)
_CONTEXT_PREFIXES = (
    "zone.phase.",
    "zone.hr_poor_",
    "zone.watch_",
    "zone.no_sensors.",
    "zone.pause.",
)
_PROGRESS_PREFIXES = (
    "zone.countdown.",
    "zone.workout_finished.",
)
_MOTIVATION_PREFIXES = (
    "interval.motivate.",
    "easy_run.motivate.",
    "motivation.",
)


def get_workout_cue_catalog(phrase_id: str) -> Optional[str]:
    normalized = (phrase_id or "").strip()
    if not normalized:
        return None

    if normalized == "zone.main_started.1":
        return "context"

    for prefix in _INSTRUCTION_PREFIXES:
        if normalized.startswith(prefix):
            return "instruction"
    for prefix in _CONTEXT_PREFIXES:
        if normalized.startswith(prefix):
            return "context"
    for prefix in _PROGRESS_PREFIXES:
        if normalized.startswith(prefix):
            return "progress"
    for prefix in _MOTIVATION_PREFIXES:
        if normalized.startswith(prefix):
            return "motivation"
    return None


def get_instruction_urgency(phrase_id: str) -> Optional[str]:
    normalized = (phrase_id or "").strip()
    if not normalized.startswith("zone."):
        return None
    catalog = get_workout_cue_catalog(normalized)
    if catalog != "instruction":
        return None
    if normalized.startswith("zone.silence."):
        return INSTRUCTION_LOW_URGENCY
    return INSTRUCTION_CORRECTIVE


def get_motivation_stage_label(phrase_id: str) -> Optional[str]:
    normalized = (phrase_id or "").strip()
    match = _MOTIVATION_STAGE_PATTERN.match(normalized)
    if match:
        return MOTIVATION_STAGE_LABELS.get(int(match.group(1)))
    if normalized.startswith("motivation."):
        return "legacy_fallback"
    return None


def is_transitional_global_motivation_id(phrase_id: str) -> bool:
    return (phrase_id or "").strip().startswith("motivation.")


def is_active_deterministic_workout_phrase_id(phrase_id: str) -> bool:
    normalized = (phrase_id or "").strip()
    if not normalized:
        return False
    if normalized.startswith(("zone.feel.", "zone.breath.")):
        return False
    if is_transitional_global_motivation_id(normalized):
        return False
    return get_workout_cue_catalog(normalized) is not None


def get_event_catalog(event_type: str) -> Optional[str]:
    normalized = (event_type or "").strip()
    if not normalized:
        return None

    if normalized in {
        "interval_countdown_30",
        "interval_countdown_15",
        "interval_countdown_5",
        "interval_countdown_start",
        "workout_finished",
    }:
        return "progress"

    if normalized in {
        "warmup_started",
        "main_started",
        "cooldown_started",
        "phase_change_work",
        "phase_change_rest",
        "phase_change_warmup",
        "phase_change_cooldown",
        "hr_structure_mode_notice",
        "hr_signal_lost",
        "hr_signal_restored",
        "hr_poor_enter",
        "hr_poor_exit",
        "watch_disconnected_notice",
        "watch_restored_notice",
        "no_sensors_notice",
        "pause_detected",
        "pause_resumed",
    }:
        return "context"

    if normalized in {
        "entered_target",
        "exited_target_above",
        "exited_target_below",
        "in_zone_recovered",
        "above_zone",
        "below_zone",
        "above_zone_ease",
        "below_zone_push",
        "recovery_hr_above_relax_ceiling",
        "recovery_hr_ok_relax",
        "structure_instruction_work",
        "structure_instruction_recovery",
        "structure_instruction_steady",
        "structure_instruction_finish",
        "max_silence_override",
        "max_silence_go_by_feel",
        "max_silence_breath_guide",
    }:
        return "instruction"

    if normalized in {
        "max_silence_motivation",
        "interval_in_target_sustained",
        "easy_run_in_target_sustained",
    }:
        return "motivation"

    return None


def get_event_instruction_urgency(event_type: str) -> Optional[str]:
    normalized = (event_type or "").strip()
    if get_event_catalog(normalized) != "instruction":
        return None
    if normalized in {"max_silence_override", "max_silence_go_by_feel", "max_silence_breath_guide"}:
        return INSTRUCTION_LOW_URGENCY
    return INSTRUCTION_CORRECTIVE


def event_cooldown_key(event_type: str) -> str:
    catalog = get_event_catalog(event_type) or "context"
    if catalog == "instruction":
        urgency = get_event_instruction_urgency(event_type)
        if urgency == INSTRUCTION_LOW_URGENCY:
            return "instruction.low_urgency"
        return "instruction.corrective"
    return catalog


def count_words(text: str) -> int:
    return len(_TOKEN_PATTERN.findall((text or "").strip()))


def count_sentences(text: str) -> int:
    stripped = (text or "").strip()
    if not stripped:
        return 0
    parts = [part.strip() for part in _SENTENCE_PATTERN.split(stripped) if part.strip()]
    return len(parts) or 1


def validate_active_workout_cue_phrase(phrase_id: str, text: str) -> tuple[bool, str]:
    if not is_active_deterministic_workout_phrase_id(phrase_id):
        return True, ""

    catalog = get_workout_cue_catalog(phrase_id)
    if catalog is None:
        return True, ""

    words = count_words(text)
    sentences = count_sentences(text)
    limit = ACTIVE_WORKOUT_CUE_WORD_LIMITS[catalog]

    if words > limit:
        return False, f"catalog={catalog} words={words} limit={limit}"
    if sentences > 2:
        return False, f"catalog={catalog} sentences={sentences} limit=2"
    return True, ""


def workout_catalog_sort_key(phrase_id: str) -> tuple[int, str, str]:
    catalog = get_workout_cue_catalog(phrase_id)
    stage = get_motivation_stage_label(phrase_id) or ""
    catalog_order = WORKOUT_CUE_CATALOG_SORT.get(catalog or "", len(WORKOUT_CUE_CATALOGS))
    return catalog_order, catalog or "", stage
