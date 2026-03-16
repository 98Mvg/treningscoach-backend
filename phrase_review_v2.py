from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tts_phrase_catalog import PHRASE_CATALOG
from workout_cue_catalog import ACTIVE_WORKOUT_CUE_WORD_LIMITS, count_sentences, count_words

PROJECT_ROOT = Path(__file__).resolve().parent
AUDIO_PACK_ROOT = PROJECT_ROOT / "output" / "audio_pack"

REVIEW_COLUMNS = [
    "phrase_id",
    "catalog",
    "family",
    "event",
    "mode",
    "english_locked",
    "norwegian_locked",
    "active_status",
    "action",
    "record_now",
    "approved_for_import",
    "approved_for_recording",
    "notes",
]
MODE_VALUES = {"HR", "NO_HR", "BOTH", "DIAGNOSTIC"}
ACTIVE_STATUS_VALUES = {"active", "active_secondary", "compatibility", "future"}
ACTION_VALUES = {"keep", "replace_text", "record_missing", "compatibility_only", "future_add"}
TRUTHY_APPROVALS = {"yes", "true", "1", "y"}
GROUP_ORDER = {
    "instruction": 0,
    "context": 1,
    "progress": 2,
    "motivation": 3,
    "diagnostic secondary": 4,
    "compatibility only": 5,
    "future additions": 6,
}


@dataclass(frozen=True)
class ReviewSeed:
    group: str
    phrase_id: str
    catalog: str
    family: str
    event: str
    mode: str
    english_locked: str
    norwegian_locked: str
    active_status: str
    notes: str


@dataclass(frozen=True)
class ReviewRow:
    group: str
    phrase_id: str
    catalog: str
    family: str
    event: str
    mode: str
    english_locked: str
    norwegian_locked: str
    active_status: str
    action: str
    record_now: str
    approved_for_import: str = ""
    approved_for_recording: str = ""
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "phrase_id": self.phrase_id,
            "catalog": self.catalog,
            "family": self.family,
            "event": self.event,
            "mode": self.mode,
            "english_locked": self.english_locked,
            "norwegian_locked": self.norwegian_locked,
            "active_status": self.active_status,
            "action": self.action,
            "record_now": self.record_now,
            "approved_for_import": self.approved_for_import,
            "approved_for_recording": self.approved_for_recording,
            "notes": self.notes,
        }


ACTIVE_SEEDS: tuple[ReviewSeed, ...] = (
    ReviewSeed("instruction", "zone.above.default.1", "instruction", "zone.above", "above_zone", "HR", "Ease back slightly.", "Ro ned litt.", "active", "primary HR correction"),
    ReviewSeed("instruction", "zone.below.default.1", "instruction", "zone.below", "below_zone", "HR", "Pick it up.", "Øk litt nå.", "active", "primary HR correction"),
    ReviewSeed("instruction", "zone.in_zone.default.1", "instruction", "zone.in_zone", "in_zone", "HR", "Stay right here.", "Bli her.", "active", "primary HR hold cue"),
    ReviewSeed("instruction", "zone.silence.work.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Hold the rhythm.", "Hold rytmen.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.silence.rest.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Relax your shoulders.", "Senk skuldrene.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.silence.default.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Find your pace.", "Finn rytmen.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.structure.work.1", "instruction", "zone.structure.work", "interval_start", "NO_HR", "Pick it up now.", "Kjør på nå.", "active", "primary no-HR work cue"),
    ReviewSeed("instruction", "zone.structure.recovery.1", "instruction", "zone.structure.recovery", "recovery_start", "NO_HR", "Ease back and recover.", "Ro ned og hent deg inn.", "active", "primary no-HR recovery cue"),
    ReviewSeed("instruction", "zone.structure.steady.1", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Settle into the pace.", "Finn rytmen.", "active", "primary no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.2", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Stay with the rhythm.", "Bli i rytmen.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.3", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Stay smooth and relaxed.", "Rolig og avslappet.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.4", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Control the effort here.", "Kontroll på innsatsen.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.5", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Keep the pace steady.", "Hold tempoet jevnt.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.6", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Hold the phase.", "Hold det her.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.finish.1", "instruction", "zone.structure.finish", "final_effort", "NO_HR", "Final push now!", "Trykk til nå!", "active", "primary no-HR finish cue"),
    ReviewSeed("context", "zone.phase.warmup.1", "context", "zone.phase.warmup", "warmup", "BOTH", "Prepare for the session.", "Forbered deg på økten.", "active", "shared warmup context"),
    ReviewSeed("context", "zone.main_started.1", "context", "zone.main_started", "main_started", "BOTH", "Main set now.", "Nå er du i hoveddelen.", "active", "shared main-set context"),
    ReviewSeed("context", "zone.phase.work.default.1", "context", "zone.phase.work", "phase_change_work", "BOTH", "Work starts now.", "Nå begynner innsatsen.", "active", "shared work transition"),
    ReviewSeed("context", "zone.phase.work.motivational.1", "context", "zone.phase.work", "phase_change_work", "BOTH", "Time to work.", "Nå jobber vi.", "active", "shared work transition"),
    ReviewSeed("context", "zone.phase.rest.1", "context", "zone.phase.rest", "phase_change_rest", "BOTH", "Recovery now.", "Pause nå.", "active", "shared recovery context"),
    ReviewSeed("context", "zone.phase.cooldown.1", "context", "zone.phase.cooldown", "cooldown", "BOTH", "Cooldown now.", "Nå roer vi ned.", "active", "shared cooldown context"),
    ReviewSeed("context", "zone.pause.detected.1", "context", "zone.pause", "pause_detected", "BOTH", "Paused session", "Pauset økten.", "active", "shared pause context"),
    ReviewSeed("context", "zone.pause.resumed.1", "context", "zone.pause", "pause_resumed", "BOTH", "You're moving again.", "Du er i gang igjen.", "active", "shared pause context"),
    ReviewSeed("context", "zone.hr_poor_enter.1", "context", "zone.hr_poor_enter", "hr_signal_lost", "HR", "Heart rate signal is weak.", "Pulssignalet er svakt.", "active", "HR-dependent context"),
    ReviewSeed("context", "zone.hr_poor_exit.1", "context", "zone.hr_poor_exit", "hr_signal_restored", "HR", "Heart rate is back.", "Pulsen er tilbake.", "active", "HR-dependent context"),
    ReviewSeed("context", "zone.hr_poor_timing.1", "context", "zone.hr_poor_timing", "no_hr_mode_notice", "NO_HR", "No heart rate signal. I will continue coaching", "Ingen pulssignal. Jeg fortsetter å coache", "active", "primary no-HR mode switch"),
    ReviewSeed("progress", "zone.countdown.30", "progress", "zone.countdown", "countdown_30", "BOTH", "30 seconds left.", "30 sekunder.", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.15", "progress", "zone.countdown", "countdown_15", "BOTH", "15", "15", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.5", "progress", "zone.countdown", "countdown_5", "BOTH", "5!", "fem", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.start", "progress", "zone.countdown", "countdown_start", "BOTH", "Go", "Start", "active", "shared countdown start cue"),
    ReviewSeed("progress", "zone.workout_finished.1", "progress", "zone.workout_finished", "workout_finish", "BOTH", "Workout finished. Nice work.", "Økten er ferdig. Bra jobbet.", "active", "shared workout closure"),
    ReviewSeed("motivation", "interval.motivate.s1.1", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "HR", "Control your breath.", "Kontroller pusten.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s1.2", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "HR", "Good start.", "God start.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s2.1", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "HR", "Nice work.", "Bra jobba.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s2.2", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "HR", "Hold the rhythm.", "Hold rytmen.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s3.1", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "HR", "Perfect!", "Herlig!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s3.2", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "HR", "Stay with it!", "Stå i det!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s4.1", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "HR", "Finish strong!", "Kjør på nå!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s4.2", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "HR", "All the way in.", "Helt inn!", "active", "active interval motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s1.1", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "HR", "Focus on breath and rhythm.", "Fokuser på pust og rytme.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s1.2", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "HR", "Settle your pace.", "Finn ditt tempo.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s2.1", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "HR", "Good rhythm.", "Bra rytme.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s2.2", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "HR", "Keep it steady.", "Hold det jevnt.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s3.1", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "HR", "Nice work!", "Bra jobba!", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s3.2", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "HR", "Keep it strong.", "Hold det sterkt.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s4.1", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "HR", "Stay smooth.", "Hold det rolig.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s4.2", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "HR", "Keep it steady.", "Hold det jevnt.", "active", "active easy-run motivation"),
    ReviewSeed("diagnostic secondary", "zone.watch_disconnected.1", "context", "zone.watch", "watch_lost", "DIAGNOSTIC", "Watch disconnected", "Pulsklokken ble frakoblet.", "active_secondary", "secondary watch-loss diagnostic"),
    ReviewSeed("diagnostic secondary", "zone.watch_restored.1", "context", "zone.watch", "watch_restored", "DIAGNOSTIC", "Watch connected and heart rate is back.", "Klokken er tilkoblet, og pulsen er tilbake.", "active_secondary", "secondary watch-restore diagnostic"),
    ReviewSeed("diagnostic secondary", "zone.no_sensors.1", "context", "zone.no_sensors", "no_sensors", "DIAGNOSTIC", "Coaching by breath.", "Coacher med pust.", "active_secondary", "secondary no-sensors diagnostic"),
)

FUTURE_SEEDS: tuple[ReviewSeed, ...] = (
    ReviewSeed("future additions", "zone.above.default.2", "instruction", "zone.above", "above_zone", "HR", "Bring it down.", "Senk tempoet litt.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.above.default.3", "instruction", "zone.above", "above_zone", "HR", "Ease the effort.", "Ro ned innsatsen.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.above.default.4", "instruction", "zone.above", "above_zone", "HR", "Settle it down.", "La det roe seg.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.above.default.5", "instruction", "zone.above", "above_zone", "HR", "Relax the pace.", "Slipp litt opp.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.2", "instruction", "zone.below", "below_zone", "HR", "Bring the effort up.", "Litt mer innsats.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.3", "instruction", "zone.below", "below_zone", "HR", "Lift the pace.", "Øk tempoet litt.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.4", "instruction", "zone.below", "below_zone", "HR", "Drive the pace.", "Trykk til litt.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.5", "instruction", "zone.below", "below_zone", "HR", "Build the effort.", "Bygg opp innsatsen.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.in_zone.default.2", "instruction", "zone.in_zone", "in_zone", "HR", "Hold this pace.", "Hold dette tempoet.", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.in_zone.default.3", "instruction", "zone.in_zone", "in_zone", "HR", "Hold the rhythm.", "Hold rytmen.", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.in_zone.default.4", "instruction", "zone.in_zone", "in_zone", "HR", "Stay steady.", "Hold det jevnt.", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.in_zone.default.5", "instruction", "zone.in_zone", "in_zone", "HR", "Right there.", "Der ja!", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.phase.warmup.2", "context", "zone.phase.warmup", "warmup", "BOTH", "Easy start.", "Rolig start.", "future", "future shared warmup variant"),
    ReviewSeed("future additions", "zone.phase.warmup.3", "context", "zone.phase.warmup", "warmup", "BOTH", "Start nice and easy.", "Start rolig.", "future", "future shared warmup variant"),
    ReviewSeed("future additions", "zone.main_started.2", "context", "zone.main_started", "main_started", "BOTH", "The workout begins now.", "Nå begynner økten.", "future", "future shared main-set variant"),
    ReviewSeed("future additions", "zone.main_started.3", "context", "zone.main_started", "main_started", "BOTH", "Main work starts now.", "Hoveddelen starter nå.", "future", "future shared main-set variant"),
    ReviewSeed("future additions", "zone.phase.rest.2", "context", "zone.phase.rest", "phase_change_rest", "BOTH", "Calm your breath now.", "Ro ned pusten nå.", "future", "future shared recovery variant"),
    ReviewSeed("future additions", "zone.phase.rest.3", "context", "zone.phase.rest", "phase_change_rest", "BOTH", "Catch your breath.", "Hent deg inn nå.", "future", "future shared recovery variant"),
    ReviewSeed("future additions", "zone.phase.cooldown.2", "context", "zone.phase.cooldown", "cooldown", "BOTH", "Bring it down.", "Ro ned.", "future", "future shared cooldown variant"),
    ReviewSeed("future additions", "zone.phase.cooldown.3", "context", "zone.phase.cooldown", "cooldown", "BOTH", "Slow it down.", "Vi roer ned nå.", "future", "future shared cooldown variant"),
    ReviewSeed("future additions", "zone.pause.detected.2", "context", "zone.pause", "pause_detected", "BOTH", "Stopped.", "Stoppet.", "future", "future pause-detected variant"),
    ReviewSeed("future additions", "zone.pause.resumed.2", "context", "zone.pause", "pause_resumed", "BOTH", "Workout continues.", "Økten fortsetter.", "future", "future pause-resumed variant"),
    ReviewSeed("future additions", "zone.hr_poor_enter.2", "context", "zone.hr_poor_enter", "hr_signal_lost", "HR", "Heart rate signal dropped.", "Pulssignalet falt ut.", "future", "future HR-loss variant"),
    ReviewSeed("future additions", "zone.hr_poor_exit.2", "context", "zone.hr_poor_exit", "hr_signal_restored", "HR", "Heart rate is stable again.", "Pulsen er stabil igjen.", "future", "future HR-restore variant"),
    ReviewSeed("future additions", "zone.hr_poor_timing.2", "context", "zone.hr_poor_timing", "no_hr_mode_notice", "NO_HR", "Heart rate unavailable. Coaching, keep moving.", "Pulssignal mangler. Jeg fortsetter å coache", "future", "future no-HR mode-switch variant"),
    ReviewSeed("future additions", "zone.countdown.start.2", "progress", "zone.countdown", "countdown_start", "BOTH", "Start!", "Start!", "future", "future countdown-start variant"),
    ReviewSeed("future additions", "zone.workout_finished.2", "progress", "zone.workout_finished", "workout_finish", "BOTH", "That’s the workout done.", "Der er økta ferdig.", "future", "future workout-finish variant"),
    ReviewSeed("future additions", "zone.workout_finished.3", "progress", "zone.workout_finished", "workout_finish", "BOTH", "Session complete. Nice work.", "Økta er fullført. Bra jobbet.", "future", "future workout-finish variant"),
    ReviewSeed("future additions", "interval.motivate.s1.3", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "HR", "Steady pace.", "Finn rytmen.", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s2.3", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "HR", "Keep it steady.", "Hold det jevnt.", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s3.3", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "HR", "Stay strong!", "Hold deg sterk!", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s4.3", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "HR", "Perfect!", "Herlig!", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s1.3", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "HR", "Nice and easy.", "Start rolig!", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s2.3", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "HR", "Stay relaxed.", "Hold deg avslappet.", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s3.3", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "HR", "Keep your flow.", "Hold flyten.", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s4.3", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "HR", "Right to the end.", "Helt til slutt.", "future", "future easy-run motivation variant"),
)

COMPATIBILITY_METADATA: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("zone.above.minimal.1", "instruction", "zone.above", "above_zone", "HR", "legacy HR correction variant"),
    ("zone.above_ease.minimal.1", "instruction", "zone.above_ease", "above_zone_ease", "HR", "legacy sustained HR correction variant"),
    ("zone.above_ease.default.1", "instruction", "zone.above_ease", "above_zone_ease", "HR", "legacy sustained HR correction variant"),
    ("zone.below.minimal.1", "instruction", "zone.below", "below_zone", "HR", "legacy HR correction variant"),
    ("zone.below_push.minimal.1", "instruction", "zone.below_push", "below_zone_push", "HR", "legacy sustained HR push variant"),
    ("zone.below_push.default.1", "instruction", "zone.below_push", "below_zone_push", "HR", "legacy sustained HR push variant"),
    ("zone.in_zone.minimal.1", "instruction", "zone.in_zone", "in_zone", "HR", "legacy HR hold variant"),
    ("zone.feel.easy_run.1", "instruction", "zone.feel.easy_run", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.easy_run.2", "instruction", "zone.feel.easy_run", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.easy_run.3", "instruction", "zone.feel.easy_run", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.work.1", "instruction", "zone.feel.work", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.work.2", "instruction", "zone.feel.work", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.recovery.1", "instruction", "zone.feel.recovery", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.feel.recovery.2", "instruction", "zone.feel.recovery", "max_silence_go_by_feel", "NO_HR", "legacy no-HR feel guidance"),
    ("zone.breath.easy_run.1", "instruction", "zone.breath.easy_run", "max_silence_breath_guide", "NO_HR", "legacy breath guidance"),
    ("zone.breath.easy_run.2", "instruction", "zone.breath.easy_run", "max_silence_breath_guide", "NO_HR", "legacy breath guidance"),
    ("zone.breath.work.1", "instruction", "zone.breath.work", "max_silence_breath_guide", "NO_HR", "legacy breath guidance"),
    ("zone.breath.recovery.1", "instruction", "zone.breath.recovery", "max_silence_breath_guide", "NO_HR", "legacy breath guidance"),
    ("motivation.1", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.2", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.3", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.4", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.5", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.6", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.7", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.8", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.9", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
    ("motivation.10", "motivation", "motivation", "legacy_fallback", "HR", "legacy flat motivation pool"),
)


REQUIRED_ACTIVE_IDS = {seed.phrase_id for seed in ACTIVE_SEEDS}


def _catalog_text_map() -> dict[str, tuple[str, str]]:
    return {
        str(item["id"]): (str(item.get("en", "")), str(item.get("no", "")))
        for item in PHRASE_CATALOG
    }


def _load_active_manifest_ids() -> set[str]:
    latest_path = AUDIO_PACK_ROOT / "latest.json"
    if not latest_path.exists():
        return set()
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    manifest_key = str(payload.get("manifest_key") or "").strip()
    if not manifest_key:
        return set()
    manifest_path = AUDIO_PACK_ROOT / manifest_key
    if not manifest_path.exists():
        return set()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        str(item.get("id") or "").strip()
        for item in manifest.get("phrases", [])
        if str(item.get("id") or "").strip()
    }


def _resolve_action_and_record_now(seed: ReviewSeed, current_text: tuple[str, str] | None, manifest_ids: set[str]) -> tuple[str, str]:
    if seed.active_status == "compatibility":
        return "compatibility_only", "no"
    if seed.active_status == "future":
        return "future_add", "yes"

    missing_audio = seed.phrase_id not in manifest_ids
    text_changed = current_text is None or current_text != (seed.english_locked, seed.norwegian_locked)

    if text_changed:
        return "replace_text", "yes"
    if missing_audio:
        return "record_missing", "yes"
    return "keep", "no"


def _build_compatibility_rows(current_text_map: dict[str, tuple[str, str]]) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    for phrase_id, catalog, family, event, mode, notes in COMPATIBILITY_METADATA:
        en, no = current_text_map.get(phrase_id, ("", ""))
        rows.append(
            ReviewRow(
                group="compatibility only",
                phrase_id=phrase_id,
                catalog=catalog,
                family=family,
                event=event,
                mode=mode,
                english_locked=en,
                norwegian_locked=no,
                active_status="compatibility",
                action="compatibility_only",
                record_now="no",
                notes=notes,
            )
        )
    return rows


def build_review_rows() -> list[ReviewRow]:
    current_text_map = _catalog_text_map()
    manifest_ids = _load_active_manifest_ids()
    rows: list[ReviewRow] = []

    for seed in ACTIVE_SEEDS + FUTURE_SEEDS:
        current_text = current_text_map.get(seed.phrase_id)
        action, record_now = _resolve_action_and_record_now(seed, current_text, manifest_ids)
        rows.append(
            ReviewRow(
                group=seed.group,
                phrase_id=seed.phrase_id,
                catalog=seed.catalog,
                family=seed.family,
                event=seed.event,
                mode=seed.mode,
                english_locked=seed.english_locked,
                norwegian_locked=seed.norwegian_locked,
                active_status=seed.active_status,
                action=action,
                record_now=record_now,
                notes=seed.notes,
            )
        )

    rows.extend(_build_compatibility_rows(current_text_map))
    return sorted(
        rows,
        key=lambda row: (
            GROUP_ORDER[row.group],
            row.catalog,
            row.family,
            row.event,
            row.phrase_id,
        ),
    )


def summarize_review_rows(rows: Iterable[ReviewRow]) -> dict[str, int]:
    row_list = list(rows)
    return {
        "total_rows": len(row_list),
        "active_rows": sum(1 for row in row_list if row.active_status == "active"),
        "record_now_rows": sum(1 for row in row_list if row.record_now == "yes"),
        "compatibility_rows": sum(1 for row in row_list if row.active_status == "compatibility"),
        "future_rows": sum(1 for row in row_list if row.active_status == "future"),
    }


def rows_to_dicts(rows: Iterable[ReviewRow]) -> list[dict[str, str]]:
    return [row.as_dict() for row in rows]


def row_from_dict(data: dict[str, Any]) -> ReviewRow:
    return ReviewRow(
        group=str(data.get("group") or _infer_group(str(data.get("active_status") or ""), str(data.get("catalog") or ""), str(data.get("mode") or ""))),
        phrase_id=str(data.get("phrase_id") or ""),
        catalog=str(data.get("catalog") or ""),
        family=str(data.get("family") or ""),
        event=str(data.get("event") or ""),
        mode=str(data.get("mode") or ""),
        english_locked=str(data.get("english_locked") or ""),
        norwegian_locked=str(data.get("norwegian_locked") or ""),
        active_status=str(data.get("active_status") or ""),
        action=str(data.get("action") or ""),
        record_now=str(data.get("record_now") or ""),
        approved_for_import=str(data.get("approved_for_import") or ""),
        approved_for_recording=str(data.get("approved_for_recording") or ""),
        notes=str(data.get("notes") or ""),
    )


def rows_from_dicts(rows: Iterable[dict[str, Any]]) -> list[ReviewRow]:
    return [row_from_dict(row) for row in rows]


def _infer_group(active_status: str, catalog: str, mode: str) -> str:
    if active_status == "compatibility":
        return "compatibility only"
    if active_status == "future":
        return "future additions"
    if active_status == "active_secondary" or mode == "DIAGNOSTIC":
        return "diagnostic secondary"
    if catalog in {"instruction", "context", "progress", "motivation"}:
        return catalog
    return "context"


def _validate_enum(name: str, value: str, allowed: set[str], phrase_id: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{phrase_id}: invalid {name} '{value}'")


def _validate_length(row: ReviewRow, errors: list[str]) -> None:
    if row.active_status == "compatibility":
        return
    limit = ACTIVE_WORKOUT_CUE_WORD_LIMITS.get(row.catalog)
    if limit is None:
        return
    for language, text in (("en", row.english_locked), ("no", row.norwegian_locked)):
        words = count_words(text)
        if words > limit:
            errors.append(f"{row.phrase_id}: {language} words={words} limit={limit} catalog={row.catalog}")
        sentences = count_sentences(text)
        if sentences > 2:
            errors.append(f"{row.phrase_id}: {language} sentences={sentences} limit=2")


def validate_review_rows(rows: Iterable[ReviewRow]) -> list[str]:
    errors: list[str] = []
    row_list = list(rows)
    seen: set[str] = set()

    for row in row_list:
        if row.phrase_id in seen:
            errors.append(f"duplicate phrase_id: {row.phrase_id}")
        seen.add(row.phrase_id)
        _validate_enum("mode", row.mode, MODE_VALUES, row.phrase_id, errors)
        _validate_enum("active_status", row.active_status, ACTIVE_STATUS_VALUES, row.phrase_id, errors)
        _validate_enum("action", row.action, ACTION_VALUES, row.phrase_id, errors)
        if row.record_now not in {"yes", "no"}:
            errors.append(f"{row.phrase_id}: invalid record_now '{row.record_now}'")
        _validate_length(row, errors)

    missing_required = sorted(REQUIRED_ACTIVE_IDS - seen)
    if missing_required:
        errors.append("missing required active phrase ids: " + ", ".join(missing_required))

    for row in row_list:
        if row.active_status == "future" and _is_truthy(row.approved_for_import):
            errors.append(f"{row.phrase_id}: future row cannot be approved for import")
    return errors


def _is_truthy(value: str) -> bool:
    return (value or "").strip().lower() in TRUTHY_APPROVALS


def filter_approved_import_rows(rows: Iterable[dict[str, str] | ReviewRow]) -> list[dict[str, str]]:
    approved: list[dict[str, str]] = []
    for raw in rows:
        row = raw.as_dict() if isinstance(raw, ReviewRow) else raw
        if not _is_truthy(row.get("approved_for_import", "")):
            continue
        if row.get("active_status") not in {"active", "active_secondary"}:
            raise ValueError(f"{row.get('phrase_id')}: only active or active_secondary rows can be promoted")
        approved.append(
            {
                "id": row["phrase_id"],
                "en": row["english_locked"],
                "no": row["norwegian_locked"],
            }
        )
    return approved


def default_review_payload() -> dict[str, Any]:
    rows = build_review_rows()
    return {
        "summary": summarize_review_rows(rows),
        "rows": rows_to_dicts(rows),
    }
