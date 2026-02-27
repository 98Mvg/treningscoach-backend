#!/usr/bin/env python3
"""
Generate and optionally upload Coachi audio packs.

Usage examples:
  python3 tools/generate_audio_pack.py --version v1 --dry-run
  python3 tools/generate_audio_pack.py --version v1
  python3 tools/generate_audio_pack.py --version v1 --sample-one --sample-language en
  python3 tools/generate_audio_pack.py --version v1 --sample-phrase-id zone.main_started.1 --sample-language en
  python3 tools/generate_audio_pack.py --version v1 --upload
  python3 tools/generate_audio_pack.py --version v1 --upload-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from elevenlabs_tts import ElevenLabsTTS  # noqa: E402
from tts_phrase_catalog import (  # noqa: E402
    expand_dynamic_templates,
    get_all_static_phrases,
    get_core_phrases,
)


LANGUAGES = ("en", "no")

VOICE_SETTINGS = {
    "v1": {
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.0,
        "speed": 1.0,
    },
}


@dataclass
class PhraseItem:
    phrase_id: str
    language: str
    text: str
    persona: str
    priority: str


def _persona_for_pack(phrase_id: str, source_persona: str) -> str:
    """
    Keep pack persona deterministic:
    - toxic.* ids are always toxic/performance voice
    - all other ids are always personal_trainer
    This prevents personal-trainer cues from being generated with toxic voice by mistake.
    """
    if phrase_id.startswith("toxic."):
        return "toxic_mode"
    return "personal_trainer"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_phrase_list(core_only: bool) -> list[PhraseItem]:
    static_items = get_core_phrases() if core_only else get_all_static_phrases()
    phrases: list[PhraseItem] = []

    for item in static_items:
        persona = _persona_for_pack(item["id"], item["persona"])
        phrases.append(
            PhraseItem(
                phrase_id=item["id"],
                language=item["language"],
                text=item["text"],
                persona=persona,
                priority=item.get("priority", "core"),
            )
        )

    # Dynamic templates don't carry explicit priority; treat as core for generation.
    for item in expand_dynamic_templates():
        for lang in LANGUAGES:
            persona = _persona_for_pack(item["id"], item["persona"])
            phrases.append(
                PhraseItem(
                    phrase_id=item["id"],
                    language=lang,
                    text=item[lang],
                    persona=persona,
                    priority="core",
                )
            )

    return phrases


def _select_phrases_for_run(
    *,
    phrases: list[PhraseItem],
    sample_one: bool,
    sample_phrase_id: Optional[str],
    sample_language: str,
) -> list[PhraseItem]:
    selected = sorted(phrases, key=lambda p: (p.phrase_id, p.language))

    if sample_phrase_id:
        filtered = [
            item
            for item in selected
            if item.phrase_id == sample_phrase_id and item.language == sample_language
        ]
        if not filtered:
            raise ValueError(
                f"Sample phrase not found for id='{sample_phrase_id}' language='{sample_language}'"
            )
        return filtered

    if sample_one:
        by_language = [item for item in selected if item.language == sample_language]
        if not by_language:
            raise ValueError(f"No phrases available for language '{sample_language}'")
        return [by_language[0]]

    return selected


def _manifest_for_output(version: str, output_dir: Path, generated_phrases: list[PhraseItem]) -> dict[str, Any]:
    phrase_map: dict[str, dict[str, Any]] = {}
    total_size = 0
    available_languages: set[str] = set()
    total_files = 0

    for phrase in generated_phrases:
        file_rel = f"{phrase.language}/{phrase.phrase_id}.mp3"
        file_path = output_dir / file_rel
        if not file_path.exists():
            continue
        size = file_path.stat().st_size
        total_size += size
        total_files += 1
        available_languages.add(phrase.language)

        entry = phrase_map.setdefault(phrase.phrase_id, {"id": phrase.phrase_id})
        entry[phrase.language] = {
            "file": file_rel,
            "size": size,
            "sha256": _sha256(file_path),
        }

    phrase_entries = [phrase_map[key] for key in sorted(phrase_map.keys())]

    manifest = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voice": "elevenlabs_flash_v2_5",
        "languages": sorted(available_languages) if available_languages else list(LANGUAGES),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "phrases": phrase_entries,
    }
    return manifest


def _build_latest_payload(*, version: str, manifest_key: str) -> dict[str, Any]:
    payload = {
        "latest_version": version,
        "manifest_key": manifest_key,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    public_base = (getattr(config, "R2_PUBLIC_URL", "") or os.getenv("R2_PUBLIC_URL", "")).strip().rstrip("/")
    if public_base:
        payload["manifest_url"] = f"{public_base}/{manifest_key}"
    return payload


def _generate_audio(
    version: str,
    output_dir: Path,
    core_only: bool,
    dry_run: bool,
    sample_one: bool,
    sample_phrase_id: Optional[str],
    sample_language: str,
) -> tuple[list[PhraseItem], Path]:
    all_phrases = _build_phrase_list(core_only=core_only)
    phrases = _select_phrases_for_run(
        phrases=all_phrases,
        sample_one=sample_one,
        sample_phrase_id=sample_phrase_id,
        sample_language=sample_language,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for lang in LANGUAGES:
        (output_dir / lang).mkdir(parents=True, exist_ok=True)

    print(f"Audio Pack Generator")
    print(f"  Version: {version}")
    print(f"  Core only: {core_only}")
    print(f"  Sample one: {sample_one}")
    if sample_phrase_id:
        print(f"  Sample phrase id: {sample_phrase_id}")
    print(f"  Sample language: {sample_language}")
    print(f"  Dry run: {dry_run}")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Output: {output_dir}")

    if dry_run:
        for phrase in phrases[:10]:
            preview = phrase.text.replace("\n", " ")[:72]
            print(f"  [{phrase.language}] {phrase.phrase_id}: {preview}")
        if len(phrases) > 10:
            print(f"  ... and {len(phrases) - 10} more")
        return phrases, output_dir

    api_key = os.getenv("ELEVENLABS_API_KEY") or getattr(config, "ELEVENLABS_API_KEY", None)
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is required to generate audio pack")

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")
    tts = ElevenLabsTTS(api_key=api_key, voice_id=voice_id)
    voice_pacing = VOICE_SETTINGS.get(version, VOICE_SETTINGS["v1"])

    generated = 0
    skipped = 0

    for phrase in phrases:
        file_path = output_dir / phrase.language / f"{phrase.phrase_id}.mp3"
        if file_path.exists() and file_path.stat().st_size > 0:
            skipped += 1
            continue
        tts.generate_audio(
            text=phrase.text,
            output_path=str(file_path),
            language=phrase.language,
            persona=phrase.persona,
            voice_pacing=voice_pacing,
        )
        generated += 1

    print(f"  Generated: {generated}")
    print(f"  Skipped existing: {skipped}")
    return phrases, output_dir


def _upload_to_r2(version: str, output_dir: Path, manifest_path: Path, latest_path: Optional[Path] = None) -> None:
    account_id = getattr(config, "R2_ACCOUNT_ID", "") or os.getenv("R2_ACCOUNT_ID", "")
    access_key = getattr(config, "R2_ACCESS_KEY_ID", "") or os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = getattr(config, "R2_SECRET_ACCESS_KEY", "") or os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket = getattr(config, "R2_BUCKET_NAME", "coachi-audio") or os.getenv("R2_BUCKET_NAME", "coachi-audio")

    if not account_id or not access_key or not secret_key:
        raise RuntimeError("R2 credentials are missing. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")

    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for --upload/--upload-only") from exc

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    uploads = 0
    for lang in LANGUAGES:
        lang_dir = output_dir / lang
        if not lang_dir.exists():
            continue
        for file_path in sorted(lang_dir.glob("*.mp3")):
            key = f"{version}/{lang}/{file_path.name}"
            s3.upload_file(str(file_path), bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})
            uploads += 1

    manifest_key = f"{version}/manifest.json"
    s3.upload_file(
        str(manifest_path),
        bucket,
        manifest_key,
        ExtraArgs={"ContentType": "application/json"},
    )
    if latest_path and latest_path.exists():
        s3.upload_file(
            str(latest_path),
            bucket,
            "latest.json",
            ExtraArgs={"ContentType": "application/json"},
        )
        print(f"Uploaded {uploads} MP3 files + {manifest_key} + latest.json to R2 bucket '{bucket}'")
    else:
        print(f"Uploaded {uploads} MP3 files + {manifest_key} to R2 bucket '{bucket}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and upload Coachi audio packs")
    parser.add_argument("--version", default=getattr(config, "AUDIO_PACK_VERSION", "v1"))
    parser.add_argument("--core-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample-one", action="store_true", help="Generate only one sample MP3 (deterministic pick)")
    parser.add_argument("--sample-phrase-id", default="", help="Generate only this phrase id (requires --sample-language)")
    parser.add_argument("--sample-language", choices=list(LANGUAGES), default="en", help="Language for sample generation")
    parser.add_argument("--upload", action="store_true", help="Generate then upload")
    parser.add_argument("--upload-only", action="store_true", help="Upload existing output folder only")
    args = parser.parse_args()

    version = (args.version or "v1").strip()
    output_dir = PROJECT_ROOT / "output" / "audio_pack" / version
    manifest_path = output_dir / "manifest.json"
    latest_path = output_dir.parent / "latest.json"
    sample_phrase_id = (args.sample_phrase_id or "").strip()

    if args.upload_only:
        if not output_dir.exists():
            raise RuntimeError(f"Output folder does not exist: {output_dir}")
        if not manifest_path.exists():
            raise RuntimeError(f"Manifest missing: {manifest_path}")
        if not latest_path.exists():
            latest_payload = _build_latest_payload(version=version, manifest_key=f"{version}/manifest.json")
            latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
            print(f"Latest pointer written: {latest_path}")
        _upload_to_r2(version, output_dir, manifest_path, latest_path)
        return 0

    phrases, output_dir = _generate_audio(
        version=version,
        output_dir=output_dir,
        core_only=args.core_only,
        dry_run=args.dry_run,
        sample_one=args.sample_one,
        sample_phrase_id=sample_phrase_id if sample_phrase_id else None,
        sample_language=args.sample_language,
    )

    if not args.dry_run:
        manifest = _manifest_for_output(version=version, output_dir=output_dir, generated_phrases=phrases)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Manifest written: {manifest_path}")
        latest_payload = _build_latest_payload(version=version, manifest_key=f"{version}/manifest.json")
        latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
        print(f"Latest pointer written: {latest_path}")

    if args.upload and not args.dry_run:
        _upload_to_r2(version, output_dir, manifest_path, latest_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
