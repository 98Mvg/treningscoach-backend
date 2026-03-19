from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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

CURATION_CATEGORY_FAMILIES = {
    "instruction": {
        "zone.above",
        "zone.below",
        "zone.in_zone",
        "zone.silence",
        "zone.structure.work",
        "zone.structure.recovery",
        "zone.structure.steady",
        "zone.structure.finish",
    },
    "context_progress": {
        "zone.phase.warmup",
        "zone.phase.work",
        "zone.phase.rest",
        "zone.phase.cooldown",
        "zone.main_started",
        "zone.pause",
        "zone.hr_poor_enter",
        "zone.hr_poor_exit",
        "zone.hr_poor_timing",
        "zone.countdown",
        "zone.workout_finished",
    },
}
CURATION_ACTIVE_STATUSES = {"active", "active_secondary"}
RUNTIME_ACTIVE_STATUSES = {"active", "active_secondary"}


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
    ReviewSeed("instruction", "zone.above.default.2", "instruction", "zone.above", "above_zone", "HR", "Heart rate slightly above target.", "Pulsen er litt høy.", "active", "secondary HR correction"),
    ReviewSeed("instruction", "zone.below.default.1", "instruction", "zone.below", "below_zone", "HR", "Pick it up.", "Øk litt nå.", "active", "primary HR correction"),
    ReviewSeed("instruction", "zone.in_zone.default.1", "instruction", "zone.in_zone", "in_zone", "HR", "Stay right here.", "Bli her.", "active", "primary HR hold cue"),
    ReviewSeed("instruction", "zone.in_zone.default.2", "instruction", "zone.in_zone", "in_zone", "HR", "You are in correct zone.", "Hold tempoet.", "active", "active HR hold cue"),
    ReviewSeed("instruction", "zone.in_zone.default.3", "instruction", "zone.in_zone", "in_zone", "HR", "Hold this phase.", "Hold dette tempoet.", "active", "active HR hold cue"),
    ReviewSeed("instruction", "zone.silence.work.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Hold the rhythm.", "Hold rytmen.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.silence.rest.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Relax your shoulders.", "Senk skuldrene.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.silence.default.1", "instruction", "zone.silence", "max_silence_hold", "BOTH", "Find your pace.", "Finn rytmen.", "active", "low-urgency hold guidance"),
    ReviewSeed("instruction", "zone.structure.work.1", "instruction", "zone.structure.work", "interval_start", "NO_HR", "Interval starts now. Bring up the pace.", "Drag starter nå. Øk farten.", "active", "primary no-HR work cue"),
    ReviewSeed("instruction", "zone.structure.recovery.1", "instruction", "zone.structure.recovery", "recovery_start", "NO_HR", "Recovery now. Ease off and reset.", "Pause nå. Ro ned og hent deg inn.", "active", "primary no-HR recovery cue"),
    ReviewSeed("instruction", "zone.structure.steady.1", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Easy pace now. Keep it steady.", "Rolig tempo nå. Hold det jevnt.", "active", "primary no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.2", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Stay with the rhythm.", "Bli i rytmen.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.3", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Stay smooth and relaxed.", "Rolig og avslappet.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.4", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Control the effort here.", "Kontroll på innsatsen.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.5", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Keep the pace steady.", "Hold tempoet jevnt.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.steady.6", "instruction", "zone.structure.steady", "steady_run", "NO_HR", "Hold the phase.", "Hold det her.", "active", "no-HR steady cue"),
    ReviewSeed("instruction", "zone.structure.finish.1", "instruction", "zone.structure.finish", "final_effort", "NO_HR", "Final push now. Finish strong.", "Siste drag nå. Avslutt sterkt.", "active", "primary no-HR finish cue"),
    ReviewSeed("context", "zone.phase.warmup.1", "context", "zone.phase.warmup", "warmup", "BOTH", "Warmup starts now.", "Oppvarming starter nå.", "active", "shared warmup context"),
    ReviewSeed("context", "zone.main_started.1", "context", "zone.main_started", "main_started", "BOTH", "Main set starts now.", "Hoveddelen starter nå.", "active", "shared main-set context"),
    ReviewSeed("context", "zone.main_started.2", "context", "zone.main_started", "main_started", "BOTH", "Workout starts now", "Treningen starter nå.", "active", "shared main-set context"),
    ReviewSeed("context", "zone.phase.work.default.1", "context", "zone.phase.work", "phase_change_work", "BOTH", "Interval starts now. Bring up the pace.", "Drag starter nå. Øk farten.", "active", "shared work transition"),
    ReviewSeed("motivation", "zone.phase.work.motivational.1", "motivation", "zone.phase.work", "phase_change_work", "BOTH", "Time to work.", "Nå jobber vi.", "active", "motivational work transition"),
    ReviewSeed("context", "zone.phase.rest.1", "context", "zone.phase.rest", "phase_change_rest", "BOTH", "Recovery starts now.", "Pause starter nå.", "active", "shared recovery context"),
    ReviewSeed("context", "zone.phase.cooldown.1", "context", "zone.phase.cooldown", "cooldown", "BOTH", "Cooldown starts now.", "Nedtrapping starter nå.", "active", "shared cooldown context"),
    ReviewSeed("context", "zone.pause.detected.1", "context", "zone.pause", "pause_detected", "BOTH", "Workout paused.", "Du har pauset økten.", "active", "shared pause context"),
    ReviewSeed("context", "zone.pause.resumed.1", "context", "zone.pause", "pause_resumed", "BOTH", "Workout resumed.", "Økten er i gang igjen.", "active", "shared pause context"),
    ReviewSeed("context", "zone.hr_poor_enter.1", "context", "zone.hr_poor_enter", "hr_signal_lost", "HR", "Heart rate signal is weak.", "Pulssignalet er svakt.", "active", "HR-dependent context"),
    ReviewSeed("context", "zone.hr_poor_exit.1", "context", "zone.hr_poor_exit", "hr_signal_restored", "HR", "Heart rate is back.", "Pulsen er tilbake.", "active", "HR-dependent context"),
    ReviewSeed("context", "zone.hr_poor_timing.1", "context", "zone.hr_poor_timing", "no_hr_mode_notice", "NO_HR", "No heart rate signal. I'll coach you by time and effort.", "Mangler pulssignal. Jeg guider deg på tid og innsats.", "active", "primary no-HR mode switch"),
    ReviewSeed("progress", "zone.countdown.30", "progress", "zone.countdown", "countdown_30", "BOTH", "30 seconds left.", "30 sekunder.", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.15", "progress", "zone.countdown", "countdown_15", "BOTH", "15", "15", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.5", "progress", "zone.countdown", "countdown_5", "BOTH", "Five.", "fem", "active", "shared countdown cue"),
    ReviewSeed("progress", "zone.countdown.start", "progress", "zone.countdown", "countdown_start", "BOTH", "Start", "Start", "active", "shared countdown start cue"),
    ReviewSeed("progress", "zone.countdown.warmup_recovery.30.1", "progress", "zone.countdown.warmup_recovery", "countdown_warmup_recovery_30", "BOTH", "30 seconds left. Get ready.", "30 sekunder igjen. Gjør deg klar.", "active", "warmup/recovery prep countdown cue"),
    ReviewSeed("progress", "zone.countdown.warmup_recovery.10.1", "progress", "zone.countdown.warmup_recovery", "countdown_warmup_recovery_10", "BOTH", "Get ready. Starting soon.", "Gjør deg klar. Starter snart.", "active", "warmup/recovery prep countdown cue"),
    ReviewSeed("progress", "zone.countdown.warmup_recovery.5.1", "progress", "zone.countdown.warmup_recovery", "countdown_warmup_recovery_5", "BOTH", "Five.", "Fem.", "active", "warmup/recovery prep countdown cue"),
    ReviewSeed("progress", "zone.countdown.warmup_recovery.start.1", "progress", "zone.countdown.warmup_recovery", "countdown_warmup_recovery_start", "BOTH", "Start.", "Start.", "active", "warmup/recovery prep countdown cue"),
    ReviewSeed("progress", "zone.countdown.halfway.dynamic", "progress", "zone.countdown", "countdown_halfway", "BOTH", "You are halfway through", "Du er halvveis nå.", "active", "shared halfway countdown cue"),
    ReviewSeed("progress", "zone.countdown.session_halfway.dynamic", "progress", "zone.countdown", "countdown_session_halfway", "BOTH", "You are halfway through the workout", "Du er halvveis nå.", "active", "shared session-halfway countdown cue"),
    ReviewSeed("progress", "zone.workout_finished.1", "progress", "zone.workout_finished", "workout_finish", "BOTH", "Workout finished. Nice work.", "Økten er ferdig. Bra jobbet.", "active", "shared workout closure"),
    ReviewSeed("motivation", "interval.motivate.s1.1", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "BOTH", "Control your breath.", "Kontroller pusten.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s1.2", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "BOTH", "Good start.", "God start.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s2.1", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "BOTH", "Nice work.", "Bra jobba.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s2.2", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "BOTH", "Hold the rhythm.", "Hold rytmen.", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s3.1", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "BOTH", "Perfect!", "Herlig!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s3.2", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "BOTH", "Stay with it!", "Stå i det!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s4.1", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "BOTH", "Finish strong!", "Kjør på nå!", "active", "active interval motivation"),
    ReviewSeed("motivation", "interval.motivate.s4.2", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "BOTH", "All the way in.", "Helt inn!", "active", "active interval motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s1.1", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "BOTH", "Focus on breath and rhythm.", "Fokuser på pust og rytme.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s1.2", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "BOTH", "Settle your pace.", "Finn ditt tempo.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s2.1", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "BOTH", "Good rhythm.", "Bra rytme.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s2.2", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "BOTH", "Keep it steady.", "Hold det jevnt.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s3.1", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "BOTH", "Nice work!", "Bra jobba!", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s3.2", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "BOTH", "Keep it strong.", "Hold det sterkt.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s4.1", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "BOTH", "Stay smooth.", "Hold det rolig.", "active", "active easy-run motivation"),
    ReviewSeed("motivation", "easy_run.motivate.s4.2", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "BOTH", "Keep it steady.", "Hold det jevnt.", "active", "active easy-run motivation"),
    ReviewSeed("diagnostic secondary", "zone.watch_disconnected.1", "context", "zone.watch", "watch_lost", "DIAGNOSTIC", "Watch disconnected.", "Klokken ble koblet fra.", "active_secondary", "secondary watch-loss diagnostic"),
    ReviewSeed("diagnostic secondary", "zone.watch_restored.1", "context", "zone.watch", "watch_restored", "DIAGNOSTIC", "Watch connected and heart rate is back.", "Klokken er tilkoblet, og pulsen er tilbake.", "active_secondary", "secondary watch-restore diagnostic"),
    ReviewSeed("diagnostic secondary", "zone.no_sensors.1", "context", "zone.no_sensors", "no_sensors", "DIAGNOSTIC", "Coaching by breath.", "Coacher med pust.", "active_secondary", "secondary no-sensors diagnostic"),
)

FUTURE_SEEDS: tuple[ReviewSeed, ...] = (
    ReviewSeed("future additions", "zone.above.default.3", "instruction", "zone.above", "above_zone", "HR", "Ease the effort.", "Ro ned innsatsen.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.above.default.4", "instruction", "zone.above", "above_zone", "HR", "Settle it down.", "La det roe seg.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.above.default.5", "instruction", "zone.above", "above_zone", "HR", "Relax the pace.", "Slipp litt opp.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.2", "instruction", "zone.below", "below_zone", "HR", "Bring the effort up.", "Litt mer innsats.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.3", "instruction", "zone.below", "below_zone", "HR", "Lift the pace.", "Øk tempoet litt.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.4", "instruction", "zone.below", "below_zone", "HR", "Drive the pace.", "Trykk til litt.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.below.default.5", "instruction", "zone.below", "below_zone", "HR", "Build the effort.", "Bygg opp innsatsen.", "future", "future HR correction variant"),
    ReviewSeed("future additions", "zone.in_zone.default.4", "instruction", "zone.in_zone", "in_zone", "HR", "Stay steady.", "Hold det jevnt.", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.in_zone.default.5", "instruction", "zone.in_zone", "in_zone", "HR", "Right there.", "Der ja!", "future", "future HR hold variant"),
    ReviewSeed("future additions", "zone.phase.warmup.2", "context", "zone.phase.warmup", "warmup", "BOTH", "Easy start.", "Rolig start.", "future", "future shared warmup variant"),
    ReviewSeed("future additions", "zone.phase.warmup.3", "context", "zone.phase.warmup", "warmup", "BOTH", "Start nice and easy.", "Start rolig.", "future", "future shared warmup variant"),
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
    ReviewSeed("future additions", "interval.motivate.s1.3", "motivation", "interval.motivate.s1", "interval_sustain_stage_1", "BOTH", "Steady pace.", "Finn rytmen.", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s2.3", "motivation", "interval.motivate.s2", "interval_sustain_stage_2", "BOTH", "Keep it steady.", "Hold det jevnt.", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s3.3", "motivation", "interval.motivate.s3", "interval_sustain_stage_3", "BOTH", "Stay strong!", "Hold deg sterk!", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "interval.motivate.s4.3", "motivation", "interval.motivate.s4", "interval_sustain_stage_4", "BOTH", "Perfect!", "Herlig!", "future", "future interval motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s1.3", "motivation", "easy_run.motivate.s1", "easy_run_sustain_stage_1", "BOTH", "Nice and easy.", "Start rolig!", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s2.3", "motivation", "easy_run.motivate.s2", "easy_run_sustain_stage_2", "BOTH", "Stay relaxed.", "Hold deg avslappet.", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s3.3", "motivation", "easy_run.motivate.s3", "easy_run_sustain_stage_3", "BOTH", "Keep your flow.", "Hold flyten.", "future", "future easy-run motivation variant"),
    ReviewSeed("future additions", "easy_run.motivate.s4.3", "motivation", "easy_run.motivate.s4", "easy_run_sustain_stage_4", "BOTH", "Right to the end.", "Helt til slutt.", "future", "future easy-run motivation variant"),
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

WORKOUT_CUE_PERSONA = "personal_trainer"
WORKOUT_CUE_PRIORITY = "core"

COMPATIBILITY_TEXT_MAP: dict[str, tuple[str, str]] = {
    "zone.above.minimal.1": ("Ease off 10-15 seconds.", "Litt ned 10-15 sekunder."),
    "zone.above_ease.minimal.1": ("HR still climbing. Ease down.", "Pulsen stiger. Rolig ned."),
    "zone.above_ease.default.1": ("Still high. Ease down 20 seconds.", "Fortsatt høy. Ro ned 20 sekunder."),
    "zone.below.minimal.1": ("Build slightly now.", "Bygg litt opp nå."),
    "zone.below_push.minimal.1": ("You're moving. Add a little.", "Du er i gang. Litt opp."),
    "zone.below_push.default.1": ("You're moving. Pick it up slightly.", "Du er i gang. Øk litt."),
    "zone.in_zone.minimal.1": ("Good. Stay here.", "Bli her."),
    "zone.feel.easy_run.1": ("Steady effort. Stay comfortable.", "Jevn innsats. Hold det behagelig."),
    "zone.feel.easy_run.2": ("Find your rhythm and hold it.", "Finn rytmen din og hold den."),
    "zone.feel.easy_run.3": ("Easy and controlled. You set the pace.", "Rolig og kontrollert. Du bestemmer tempoet."),
    "zone.feel.work.1": ("Push hard but controlled.", "Hold en jevn rytme"),
    "zone.feel.work.2": ("Strong effort now. Stay focused.", "Sterk innsats nå. Hold fokus."),
    "zone.feel.recovery.1": ("Ease off. Let your body recover.", "Slipp av. La kroppen hente seg inn."),
    "zone.feel.recovery.2": ("Relax and breathe. Recovery counts.", "Slapp av og pust. Hvile teller."),
    "zone.breath.easy_run.1": ("Match your breathing to your pace.", "Tilpass pusten til tempoet."),
    "zone.breath.easy_run.2": ("Smooth breaths. You're doing well.", "Jevn pust. Du gjør det bra."),
    "zone.breath.work.1": ("Breathe through the effort.", "Herlig"),
    "zone.breath.recovery.1": ("Slow your breathing down.", "Senk pustetakten."),
    "motivation.1": ("Nice work!", "Hold det sterkt."),
    "motivation.2": ("Keep it up.", "Bra jobba!"),
    "motivation.3": ("That's the effort I want to see.", "Det skal kjennes litt. Det er prisen for endring.."),
    "motivation.4": ("One step at a time. You got this.", "Ett steg om gangen. Du klarer det."),
    "motivation.5": ("Discipline beats motivation. Keep going.", "Disiplin slår motivasjon. Fortsett."),
    "motivation.6": ("This is where it counts.", "Det er nå det gjelder."),
    "motivation.7": ("You showed up. thats the hard part.", "Du møtte opp. Det er det vanskelige."),
    "motivation.8": ("Trust the process.", "Stol på prosessen."),
    "motivation.9": ("Every rep matters.", "Hvert steg teller."),
    "motivation.10": ("Finish what you started.", "Fullfør det du begynte på."),
}


def _seed_text_map(*, include_future: bool = False) -> dict[str, tuple[str, str]]:
    mapping = {
        seed.phrase_id: (seed.english_locked, seed.norwegian_locked)
        for seed in ACTIVE_SEEDS
    }
    if include_future:
        mapping.update(
            {
                seed.phrase_id: (seed.english_locked, seed.norwegian_locked)
                for seed in FUTURE_SEEDS
            }
        )
    return mapping


def build_workout_phrase_catalog_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()

    for seed in ACTIVE_SEEDS:
        if seed.phrase_id in seen:
            continue
        seen.add(seed.phrase_id)
        entries.append(
            {
                "id": seed.phrase_id,
                "en": seed.english_locked,
                "no": seed.norwegian_locked,
                "persona": WORKOUT_CUE_PERSONA,
                "priority": WORKOUT_CUE_PRIORITY,
            }
        )

    for phrase_id, (en, no) in COMPATIBILITY_TEXT_MAP.items():
        if phrase_id in seen:
            continue
        seen.add(phrase_id)
        entries.append(
            {
                "id": phrase_id,
                "en": en,
                "no": no,
                "persona": WORKOUT_CUE_PERSONA,
                "priority": WORKOUT_CUE_PRIORITY,
            }
        )

    return entries


_WORKOUT_PHRASE_CATALOG_BY_ID = {
    str(entry["id"]): entry
    for entry in build_workout_phrase_catalog_entries()
}


def get_workout_phrase_entry(phrase_id: str) -> dict[str, str] | None:
    normalized = str(phrase_id or "").strip()
    if not normalized:
        return None
    return _WORKOUT_PHRASE_CATALOG_BY_ID.get(normalized)


def get_workout_phrase_text(phrase_id: str, language: str) -> str | None:
    entry = get_workout_phrase_entry(phrase_id)
    if not entry:
        return None
    lang_key = (language or "en").strip().lower()
    if lang_key not in {"en", "no"}:
        lang_key = "en"
    text = entry.get(lang_key)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def _catalog_text_map() -> dict[str, tuple[str, str]]:
    mapping = _seed_text_map()
    mapping.update(COMPATIBILITY_TEXT_MAP)
    return mapping


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


def build_curation_rows(category: str) -> list[ReviewRow]:
    allowed_families = CURATION_CATEGORY_FAMILIES.get(category)
    if allowed_families is None:
        raise ValueError(f"Unsupported curation category: {category}")

    return [
        row
        for row in build_review_rows()
        if row.active_status in CURATION_ACTIVE_STATUSES and row.family in allowed_families
    ]


def build_runtime_pack_rows() -> list[ReviewRow]:
    return [
        row
        for row in build_review_rows()
        if row.active_status in RUNTIME_ACTIVE_STATUSES
    ]


def build_runtime_event_phrase_map() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for seed in ACTIVE_SEEDS:
        if seed.active_status not in RUNTIME_ACTIVE_STATUSES:
            continue
        grouped.setdefault(seed.event, []).append(seed.phrase_id)
    return grouped


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
