import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zone_event_motor import _motivation_phrase_id, _resolve_phrase_id


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIO_PACK_ROOT = REPO_ROOT / "output" / "audio_pack"


def _active_manifest_path() -> Path:
    latest_path = AUDIO_PACK_ROOT / "latest.json"
    assert latest_path.exists(), f"Missing active audio pack pointer: {latest_path}"

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    manifest_key = str(latest.get("manifest_key") or "").strip()
    assert manifest_key, "latest.json is missing manifest_key"

    manifest_path = AUDIO_PACK_ROOT / manifest_key
    assert manifest_path.exists(), f"Missing active manifest file: {manifest_path}"
    return manifest_path


def _manifest_phrase_ids(manifest_path: Path) -> set[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        str(item.get("id")).strip()
        for item in payload.get("phrases", [])
        if str(item.get("id") or "").strip()
    }


def _zone_event_phrase_ids() -> set[str]:
    event_types = {
        "warmup_started",
        "main_started",
        "cooldown_started",
        "workout_finished",
        "entered_target",
        "exited_target_above",
        "exited_target_below",
        "hr_signal_lost",
        "hr_signal_restored",
        "watch_disconnected_notice",
        "no_sensors_notice",
        "watch_restored_notice",
        "interval_countdown_30",
        "interval_countdown_15",
        "interval_countdown_5",
        "interval_countdown_start",
        "pause_detected",
        "pause_resumed",
        "max_silence_override",
        "max_silence_go_by_feel",
        "max_silence_breath_guide",
        "max_silence_motivation",
        "interval_in_target_sustained",
        "easy_run_in_target_sustained",
    }
    phases = ("warmup", "main", "work", "recovery", "cooldown")
    phrase_ids: set[str] = set()
    for event_type in event_types:
        for phase in phases:
            phrase_id = _resolve_phrase_id(event_type, phase)
            if phrase_id:
                phrase_ids.add(phrase_id)

    for workout_type in ("intervals", "easy_run"):
        for stage in range(1, 5):
            for variant in (1, 2):
                phrase_ids.add(_motivation_phrase_id(workout_type, stage, variant))

    return phrase_ids


def test_zone_event_phrase_ids_exist_in_active_manifest():
    manifest_path = _active_manifest_path()
    manifest_ids = _manifest_phrase_ids(manifest_path)
    required_ids = _zone_event_phrase_ids()
    missing = sorted(required_ids - manifest_ids)
    assert not missing, (
        f"Active audio pack manifest is missing phrase IDs used by zone events "
        f"({manifest_path}):\n- " + "\n- ".join(missing)
    )
