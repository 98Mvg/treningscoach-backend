#!/usr/bin/env python3
"""
Copy a curated core subset from generated audio pack into iOS bundled resources.

Usage:
  python3 tools/select_core_bundle.py --version v1
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tts_phrase_catalog import PHRASE_CATALOG

LANGUAGES = ("en", "no")
MAX_VARIANTS_PER_CATEGORY = 5


# Categories to keep bundled offline. We include up to MAX_VARIANTS_PER_CATEGORY
# variants for each category in each language.
CORE_BUNDLE_CATEGORIES = [
    "coach.critical",
    "cont.critical",
    "cont.warmup",
    "cont.intense.calm",
    "cont.intense.mod",
    "cont.intense.intense",
    "cont.cooldown",
    "zone.countdown",
    "zone.main_started",
    "zone.workout_finished",
    "zone.phase.warmup",
    "zone.phase.cooldown",
    "zone.above.minimal",
    "zone.below.minimal",
    "zone.in_zone.minimal",
    "zone.in_zone.default",
    "zone.watch_disconnected",
    "zone.no_sensors",
    "zone.watch_restored",
    "zone.hr_poor_timing",
    "breath.interrupt.cant_breathe",
    "breath.interrupt.slow_down",
    "breath.interrupt.dizzy",
    "welcome.standard",
    "wake_ack.en",
    "wake_ack.no",
    "zone.silence.work",
    "zone.silence.rest",
    "zone.silence.default",
    "zone.structure.work",
    "zone.structure.recovery",
    "zone.structure.steady",
    "zone.structure.finish",
    "interval.motivate.s1",
    "interval.motivate.s2",
    "interval.motivate.s3",
    "interval.motivate.s4",
    "easy_run.motivate.s1",
    "easy_run.motivate.s2",
    "easy_run.motivate.s3",
    "easy_run.motivate.s4",
]


def _phrase_sort_key(phrase_id: str) -> tuple[int, int, str]:
    tail = phrase_id.split(".")[-1]
    if tail == "default":
        return (0, 0, phrase_id)
    if tail.isdigit():
        return (1, int(tail), phrase_id)
    return (2, 999, phrase_id)


def _build_core_bundle_ids() -> list[str]:
    all_ids = [entry["id"] for entry in PHRASE_CATALOG]
    ordered_ids: list[str] = []
    seen: set[str] = set()

    for prefix in CORE_BUNDLE_CATEGORIES:
        matches = [pid for pid in all_ids if pid == prefix or pid.startswith(prefix + ".")]
        matches.sort(key=_phrase_sort_key)
        for pid in matches[:MAX_VARIANTS_PER_CATEGORY]:
            if pid not in seen:
                seen.add(pid)
                ordered_ids.append(pid)

    return ordered_ids


def _manifest_bundle_ids(manifest_path: Path) -> list[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    ids = []
    for item in payload.get("phrases", []):
        phrase_id = str(item.get("id") or "").strip()
        if phrase_id:
            ids.append(phrase_id)
    return ids


def _clear_bundled_mp3s(target_root: Path) -> int:
    removed = 0
    if not target_root.exists():
        return 0
    for file_path in target_root.rglob("*.mp3"):
        file_path.unlink()
        removed += 1
    return removed


def _bundle_ids_for_version(version: str, source_root: Path) -> tuple[list[str], str]:
    if version == "v2":
        manifest_path = source_root / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing manifest for V2 bundle copy: {manifest_path}")
        return _manifest_bundle_ids(manifest_path), "manifest"
    return _build_core_bundle_ids(), "curated"


def select_bundle(version: str) -> int:
    source_root = PROJECT_ROOT / "output" / "audio_pack" / version
    target_root = PROJECT_ROOT / "TreningsCoach" / "TreningsCoach" / "Resources" / "CoreAudioPack"

    if not source_root.exists():
        print(f"ERROR: source folder not found: {source_root}")
        print("Run tools/generate_audio_pack.py first.")
        return 1

    try:
        core_bundle_ids, selection_mode = _bundle_ids_for_version(version, source_root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    removed = _clear_bundled_mp3s(target_root)

    copied = 0
    missing = 0
    overwritten = 0

    for lang in LANGUAGES:
        lang_target = target_root / lang
        lang_target.mkdir(parents=True, exist_ok=True)

        for phrase_id in core_bundle_ids:
            src = source_root / lang / f"{phrase_id}.mp3"
            dst = lang_target / f"{phrase_id}.mp3"
            if not src.exists():
                print(f"MISSING: {lang}/{phrase_id}.mp3")
                missing += 1
                continue
            shutil.copy2(src, dst)
            copied += 1

    expected_total = len(core_bundle_ids) * len(LANGUAGES)
    print(f"Core bundle complete")
    print(f"  Version: {version}")
    print(f"  Selection mode: {selection_mode}")
    if selection_mode == "curated":
        print(f"  Categories: {len(CORE_BUNDLE_CATEGORIES)} (max {MAX_VARIANTS_PER_CATEGORY} each)")
    print(f"  IDs: {len(core_bundle_ids)}")
    print(f"  Expected files: {expected_total}")
    print(f"  Copied: {copied}")
    print(f"  Overwritten: {overwritten}")
    print(f"  Removed stale bundle files: {removed}")
    print(f"  Missing: {missing}")
    print(f"  Target: {target_root}")
    return 0 if missing == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Select and copy iOS core audio bundle")
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    return select_bundle(args.version)


if __name__ == "__main__":
    raise SystemExit(main())
