#!/usr/bin/env python3
"""
Copy a curated core subset from generated audio pack into iOS bundled resources.

Usage:
  python3 tools/select_core_bundle.py --version v1
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "no")

# ~54 phrase ids that should always be available offline in the app bundle.
CORE_BUNDLE_IDS = [
    "coach.critical.1",
    "cont.critical.1", "cont.critical.2", "cont.critical.3", "cont.critical.4",
    "cont.warmup.1", "cont.warmup.2", "cont.warmup.3", "cont.warmup.4", "cont.warmup.5",
    "cont.intense.calm.1", "cont.intense.calm.2",
    "cont.intense.mod.1", "cont.intense.mod.2",
    "cont.intense.intense.1",
    "cont.cooldown.1", "cont.cooldown.2", "cont.cooldown.3", "cont.cooldown.4", "cont.cooldown.5",
    "zone.countdown.30", "zone.countdown.15", "zone.countdown.5", "zone.countdown.start",
    "zone.main_started.1", "zone.workout_finished.1", "zone.phase.warmup.1", "zone.phase.cooldown.1",
    "zone.above.minimal.1", "zone.below.minimal.1", "zone.in_zone.minimal.1", "zone.in_zone.default.1",
    "zone.watch_disconnected.1", "zone.no_sensors.1", "zone.watch_restored.1",
    "breath.interrupt.cant_breathe.1", "breath.interrupt.slow_down.1", "breath.interrupt.dizzy.1",
    "welcome.standard.1", "welcome.standard.2", "welcome.beginner.1",
    "motivation.1", "motivation.2", "motivation.3", "motivation.4", "motivation.5",
    "motivation.6", "motivation.7", "motivation.8", "motivation.9", "motivation.10",
    "zone.silence.work.1", "zone.silence.rest.1", "zone.silence.default.1",
]


def select_bundle(version: str) -> int:
    source_root = PROJECT_ROOT / "output" / "audio_pack" / version
    target_root = PROJECT_ROOT / "TreningsCoach" / "TreningsCoach" / "Resources" / "CoreAudioPack"

    if not source_root.exists():
        print(f"ERROR: source folder not found: {source_root}")
        print("Run tools/generate_audio_pack.py first.")
        return 1

    copied = 0
    missing = 0
    overwritten = 0

    for lang in LANGUAGES:
        lang_target = target_root / lang
        lang_target.mkdir(parents=True, exist_ok=True)

        for phrase_id in CORE_BUNDLE_IDS:
            src = source_root / lang / f"{phrase_id}.mp3"
            dst = lang_target / f"{phrase_id}.mp3"
            if not src.exists():
                print(f"MISSING: {lang}/{phrase_id}.mp3")
                missing += 1
                continue
            if dst.exists():
                overwritten += 1
            shutil.copy2(src, dst)
            copied += 1

    expected_total = len(CORE_BUNDLE_IDS) * len(LANGUAGES)
    print(f"Core bundle complete")
    print(f"  Version: {version}")
    print(f"  IDs: {len(CORE_BUNDLE_IDS)}")
    print(f"  Expected files: {expected_total}")
    print(f"  Copied: {copied}")
    print(f"  Overwritten: {overwritten}")
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
