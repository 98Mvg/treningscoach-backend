#!/usr/bin/env python3
"""
Generate and optionally upload Coachi audio packs.

Usage examples:
  python3 tools/generate_audio_pack.py --version v1 --dry-run
  python3 tools/generate_audio_pack.py --version v1
  python3 tools/generate_audio_pack.py --version v2 --changed-only
  python3 tools/generate_audio_pack.py --version v2 --sync-r2
  python3 tools/generate_audio_pack.py --version v1 --sample-one --sample-language en
  python3 tools/generate_audio_pack.py --version v1 --sample-phrase-id zone.main_started.1 --sample-language en
  python3 tools/generate_audio_pack.py --version v1 --upload
  python3 tools/generate_audio_pack.py --version v1 --upload-only
"""

from __future__ import annotations

import argparse
import csv
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
from coaching_engine import validate_coaching_text  # noqa: E402
from elevenlabs_tts import ElevenLabsTTS  # noqa: E402
from phrase_review_v2 import build_runtime_pack_rows, get_workout_phrase_entry  # noqa: E402
from tts_phrase_catalog import (  # noqa: E402
    expand_dynamic_templates,
    get_all_static_phrases,
    get_core_phrases,
    get_phrase_by_id,
)
from workout_cue_catalog import validate_active_workout_cue_phrase  # noqa: E402


LANGUAGES = ("en", "no")
APPROVED_ACTIVE_STATUSES = {"active", "active_secondary"}
TRUTHY_APPROVALS = {"yes", "true", "1", "y"}
V2_FORCE_VOICE_IDS = {
    "en": "9MPvdQh2pLsLhn7SuiIS",
    "no": "nhvaqgRyAq6BmFs3WcdX",
}
V2_BUNDLE_INFRASTRUCTURE_IDS = {
    "wake_ack.en.default",
    "wake_ack.no.default",
}

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
    voice_id_override: Optional[str] = None


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


def _content_hash(phrase: "PhraseItem", voice_settings: dict[str, Any]) -> str:
    """Hash of everything that determines the generated MP3.

    If any of text/language/persona/voice settings change, this hash changes
    and the MP3 gets regenerated. No need to manually delete files.
    """
    payload = json.dumps(
        {
            "phrase_id": phrase.phrase_id,
            "language": phrase.language,
            "text": phrase.text,
            "persona": phrase.persona,
            "voice_id_override": phrase.voice_id_override or "",
            "voice_settings": voice_settings,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _load_build_cache(cache_path: Path) -> dict[str, str]:
    """Load {file_key: content_hash} from build_cache.json."""
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_build_cache(cache_path: Path, cache: dict[str, str]) -> None:
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def _validation_mode(phrase_id: str) -> str:
    """Determine coaching_engine validation mode from phrase ID.

    Summary / notice / signal phrases allow up to 30 words (strategic).
    Short workout cues are validated with the tighter 1-15 word realtime limit.
    """
    _strategic_prefixes = (
        "summary.",
        "session.",
        "workout_complete.",
        # Signal/notice phrases are informational, not mid-rep cues
        "zone.hr_poor",
        "zone.watch_disconnected",
        "zone.watch_restored",
        "zone.no_sensors",
    )
    for prefix in _strategic_prefixes:
        if phrase_id.startswith(prefix):
            return "strategic"
    return "realtime"


def _validate_phrase(phrase: PhraseItem) -> tuple[bool, str]:
    """Run coaching_engine validation on a phrase.

    Returns (passed, reason) where reason is empty on success.
    """
    mode = _validation_mode(phrase.phrase_id)
    passed = validate_coaching_text(
        text=phrase.text,
        phase="intense",
        intensity="moderate",
        persona=phrase.persona,
        language=phrase.language,
        mode=mode,
    )
    if not passed:
        word_count = len(phrase.text.split())
        limit = "1-15" if mode == "realtime" else "2-30"
        return False, f"words={word_count} limit={limit} mode={mode}"
    active_ok, active_reason = validate_active_workout_cue_phrase(phrase.phrase_id, phrase.text)
    if not active_ok:
        return False, active_reason
    return True, ""


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
                voice_id_override=None,
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
                    voice_id_override=None,
                )
            )

    return phrases


def _build_v2_phrase_list() -> list[PhraseItem]:
    phrases: list[PhraseItem] = []
    seen: set[tuple[str, str]] = set()

    for row in build_runtime_pack_rows():
        catalog_entry = get_workout_phrase_entry(row.phrase_id)
        source_persona = str(catalog_entry.get("persona", "personal_trainer")) if catalog_entry else "personal_trainer"
        priority = str(catalog_entry.get("priority", "core")) if catalog_entry else "core"
        persona = _persona_for_pack(row.phrase_id, source_persona)

        for language, text in (("en", row.english_locked), ("no", row.norwegian_locked)):
            phrases.append(
                PhraseItem(
                    phrase_id=row.phrase_id,
                    language=language,
                    text=text,
                    persona=persona,
                    priority=priority,
                    voice_id_override=V2_FORCE_VOICE_IDS.get(language),
                )
            )
            seen.add((row.phrase_id, language))

    for phrase_id in sorted(V2_BUNDLE_INFRASTRUCTURE_IDS):
        catalog_entry = get_phrase_by_id(phrase_id)
        if not catalog_entry:
            raise RuntimeError(f"Missing V2 infrastructure phrase in catalog: {phrase_id}")
        persona = _persona_for_pack(phrase_id, str(catalog_entry.get("persona", "personal_trainer")))
        priority = str(catalog_entry.get("priority", "core"))
        for language in LANGUAGES:
            key = (phrase_id, language)
            if key in seen:
                continue
            phrases.append(
                PhraseItem(
                    phrase_id=phrase_id,
                    language=language,
                    text=str(catalog_entry.get(language, "")),
                    persona=persona,
                    priority=priority,
                    voice_id_override=V2_FORCE_VOICE_IDS.get(language),
                )
            )
            seen.add(key)

    return sorted(phrases, key=lambda phrase: (phrase.phrase_id, phrase.language))


def _phrases_for_build(
    *,
    version: str,
    core_only: bool,
    review_path: Optional[Path],
) -> list[PhraseItem]:
    if version == "v2":
        return _build_v2_phrase_list()
    return _filter_phrases_for_version(
        phrases=_build_phrase_list(core_only=core_only),
        version=version,
        review_path=review_path,
    )


def _is_truthy(value: str) -> bool:
    return (value or "").strip().lower() in TRUTHY_APPROVALS


def _load_review_rows_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _approved_v2_phrase_ids(review_path: Path) -> set[str]:
    rows = _load_review_rows_csv(review_path)
    approved_ids = {
        str(row.get("phrase_id") or "").strip()
        for row in rows
        if str(row.get("active_status") or "").strip() in APPROVED_ACTIVE_STATUSES
        and _is_truthy(str(row.get("approved_for_import") or ""))
        and _is_truthy(str(row.get("approved_for_recording") or ""))
    }
    if not approved_ids:
        raise RuntimeError(
            f"No approved active rows found in review artifact: {review_path}. "
            "Mark approved_for_import=yes and approved_for_recording=yes first."
        )
    return approved_ids | V2_BUNDLE_INFRASTRUCTURE_IDS


def _filter_phrases_for_version(
    *,
    phrases: list[PhraseItem],
    version: str,
    review_path: Optional[Path],
) -> list[PhraseItem]:
    filtered = phrases
    if version == "v2":
        if review_path is None or not review_path.exists():
            raise RuntimeError(
                "V2 generation requires a review artifact. "
                "Expected phrase_catalog_sorted.csv to exist."
            )
        approved_ids = _approved_v2_phrase_ids(review_path)
        filtered = [phrase for phrase in phrases if phrase.phrase_id in approved_ids]

    if version == "v2":
        return [
            PhraseItem(
                phrase_id=phrase.phrase_id,
                language=phrase.language,
                text=phrase.text,
                persona=phrase.persona,
                priority=phrase.priority,
                voice_id_override=V2_FORCE_VOICE_IDS.get(phrase.language),
            )
            for phrase in filtered
        ]
    return filtered


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


def _prune_stale_output_files(output_dir: Path, phrases: list[PhraseItem]) -> int:
    allowed = {f"{phrase.language}/{phrase.phrase_id}.mp3" for phrase in phrases}
    removed = 0
    for lang in LANGUAGES:
        lang_dir = output_dir / lang
        if not lang_dir.exists():
            continue
        for file_path in lang_dir.glob("*.mp3"):
            rel = f"{lang}/{file_path.name}"
            if rel not in allowed:
                file_path.unlink()
                removed += 1
    return removed


def _refresh_existing_output(
    *,
    version: str,
    output_dir: Path,
    core_only: bool,
    review_path: Optional[Path],
) -> list[PhraseItem]:
    phrases = _phrases_for_build(
        version=version,
        core_only=core_only,
        review_path=review_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for lang in LANGUAGES:
        (output_dir / lang).mkdir(parents=True, exist_ok=True)

    cache_path = output_dir / "build_cache.json"
    build_cache = _load_build_cache(cache_path)
    active_keys = {f"{phrase.language}/{phrase.phrase_id}" for phrase in phrases}
    stale_keys = [key for key in build_cache if key not in active_keys]
    for key in stale_keys:
        del build_cache[key]
    _save_build_cache(cache_path, build_cache)

    pruned = _prune_stale_output_files(output_dir, phrases)

    print(f"Refreshed existing audio-pack artifacts")
    print(f"  Version: {version}")
    print(f"  Output: {output_dir}")
    print(f"  Active phrases: {len(phrases)}")
    print(f"  Removed stale cache entries: {len(stale_keys)}")
    print(f"  Pruned stale MP3s: {pruned}")
    return phrases


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
    review_path: Optional[Path],
    skip_validation: bool = False,
) -> tuple[list[PhraseItem], Path]:
    all_phrases = _phrases_for_build(
        version=version,
        core_only=core_only,
        review_path=review_path,
    )
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

    # Build cache: content-hash per utterance detects text/voice/settings changes.
    # Regenerates only changed phrases — no need to manually delete MP3s.
    cache_path = output_dir / "build_cache.json"
    build_cache = _load_build_cache(cache_path)

    generated = 0
    skipped = 0
    changed = 0
    validation_failed: list[tuple[PhraseItem, str]] = []

    for phrase in phrases:
        # Coaching engine validation gate — check text before spending TTS credits.
        if not skip_validation:
            ok, reason = _validate_phrase(phrase)
            if not ok:
                validation_failed.append((phrase, reason))
                continue

        file_key = f"{phrase.language}/{phrase.phrase_id}"
        file_path = output_dir / phrase.language / f"{phrase.phrase_id}.mp3"
        new_hash = _content_hash(phrase, voice_pacing)
        cached_hash = build_cache.get(file_key)

        if file_path.exists() and file_path.stat().st_size > 0 and cached_hash == new_hash:
            skipped += 1
            continue

        if file_path.exists() and cached_hash != new_hash:
            changed += 1

        tts.generate_audio(
            text=phrase.text,
            output_path=str(file_path),
            language=phrase.language,
            persona=phrase.persona,
            voice_pacing=voice_pacing,
            voice_id_override=phrase.voice_id_override,
        )
        build_cache[file_key] = new_hash
        generated += 1

    # Remove stale cache entries for phrases no longer in catalog.
    active_keys = {f"{p.language}/{p.phrase_id}" for p in phrases}
    stale_keys = [k for k in build_cache if k not in active_keys]
    for k in stale_keys:
        del build_cache[k]

    _save_build_cache(cache_path, build_cache)
    pruned = _prune_stale_output_files(output_dir, phrases)

    print(f"  Generated: {generated} ({changed} changed, {generated - changed} new)")
    print(f"  Skipped unchanged: {skipped}")
    if validation_failed:
        print(f"  ⚠️  Validation failed: {len(validation_failed)} phrases blocked:")
        for failed_phrase, reason in validation_failed:
            preview = failed_phrase.text.replace("\n", " ")[:60]
            print(f"     BLOCKED [{failed_phrase.language}] {failed_phrase.phrase_id}: {reason}")
            print(f"             \"{preview}\"")
    if stale_keys:
        print(f"  Stale cache entries removed: {len(stale_keys)}")
    if pruned:
        print(f"  Pruned stale MP3s: {pruned}")
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
        raise RuntimeError(
            "boto3 is required for --upload/--upload-only. "
            "Install tool dependencies with `pip install -r requirements-tools.txt`."
        ) from exc

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    uploads = 0
    for phrase in manifest.get("phrases", []):
        for lang in LANGUAGES:
            lang_payload = phrase.get(lang)
            if not isinstance(lang_payload, dict):
                continue
            rel_path = str(lang_payload.get("file") or "").strip()
            if not rel_path:
                continue
            file_path = output_dir / rel_path
            if not file_path.exists():
                raise RuntimeError(f"Manifest references missing audio file: {file_path}")
            key = f"{version}/{rel_path}"
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


def _build_r2_client():
    account_id = getattr(config, "R2_ACCOUNT_ID", "") or os.getenv("R2_ACCOUNT_ID", "")
    access_key = getattr(config, "R2_ACCESS_KEY_ID", "") or os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = getattr(config, "R2_SECRET_ACCESS_KEY", "") or os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket = getattr(config, "R2_BUCKET_NAME", "coachi-audio") or os.getenv("R2_BUCKET_NAME", "coachi-audio")

    if not account_id or not access_key or not secret_key:
        raise RuntimeError("R2 credentials are missing. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")

    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required for R2 pruning/upload. "
            "Install tool dependencies with `pip install -r requirements-tools.txt`."
        ) from exc

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )
    return s3, bucket


def _list_r2_keys(s3: Any, bucket: str, prefix: str) -> list[str]:
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = str(item.get("Key") or "").strip()
            if key:
                keys.append(key)
    return keys


def _delete_r2_keys(s3: Any, bucket: str, keys: list[str]) -> int:
    if not keys:
        return 0

    deleted = 0
    for idx in range(0, len(keys), 1000):
        batch = keys[idx : idx + 1000]
        s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
        )
        deleted += len(batch)
    return deleted


def _manifest_audio_keys(version: str, manifest_path: Path) -> set[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for phrase in payload.get("phrases", []):
        for lang in LANGUAGES:
            rel_path = str((phrase.get(lang) or {}).get("file") or "").strip()
            if rel_path:
                keys.add(f"{version}/{rel_path}")
    return keys


def _prune_removed_r2_keys(version: str, manifest_path: Path) -> int:
    s3, bucket = _build_r2_client()
    desired_keys = _manifest_audio_keys(version, manifest_path)
    existing_keys: set[str] = set()
    for lang in LANGUAGES:
        existing_keys.update(
            key for key in _list_r2_keys(s3, bucket, f"{version}/{lang}/") if key.endswith(".mp3")
        )
    stale_keys = sorted(existing_keys - desired_keys)
    deleted = _delete_r2_keys(s3, bucket, stale_keys)
    print(f"Pruned {deleted} stale R2 MP3 objects for {version}")
    return deleted


def _known_audio_pack_versions(audio_pack_root: Path) -> list[str]:
    if not audio_pack_root.exists():
        return []
    return sorted(
        path.name
        for path in audio_pack_root.iterdir()
        if path.is_dir() and path.name.startswith("v")
    )


def _prune_welcome_r2_keys(audio_pack_root: Path) -> int:
    s3, bucket = _build_r2_client()
    stale_keys: set[str] = set()
    for version in _known_audio_pack_versions(audio_pack_root):
        for lang in LANGUAGES:
            prefix = f"{version}/{lang}/welcome.standard."
            stale_keys.update(
                key for key in _list_r2_keys(s3, bucket, prefix) if key.endswith(".mp3")
            )
    deleted = _delete_r2_keys(s3, bucket, sorted(stale_keys))
    print(f"Pruned {deleted} legacy welcome MP3 objects from R2")
    return deleted


def _prune_welcome_r2(audio_pack_root: Path) -> int:
    return _prune_welcome_r2_keys(audio_pack_root)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and upload Coachi audio packs")
    parser.add_argument("--version", default=getattr(config, "AUDIO_PACK_VERSION", "v1"))
    parser.add_argument("--core-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Alias for the existing build-cache incremental generation behavior.",
    )
    parser.add_argument("--sample-one", action="store_true", help="Generate only one sample MP3 (deterministic pick)")
    parser.add_argument("--sample-phrase-id", default="", help="Generate only this phrase id (requires --sample-language)")
    parser.add_argument("--sample-language", choices=list(LANGUAGES), default="en", help="Language for sample generation")
    parser.add_argument("--skip-validation", action="store_true", help="Skip coaching_engine text validation")
    parser.add_argument(
        "--review-input",
        default=str(PROJECT_ROOT / "output" / "spreadsheet" / "phrase_catalog_sorted.csv"),
        help="Legacy V2 review artifact path. V2 pack generation now sources runtime rows from phrase_review_v2.py.",
    )
    parser.add_argument("--upload", action="store_true", help="Generate then upload")
    parser.add_argument(
        "--sync-r2",
        action="store_true",
        help="One-step sync: generate/update manifest, upload to R2, and prune stale R2 MP3s.",
    )
    parser.add_argument("--upload-only", action="store_true", help="Upload existing output folder only")
    parser.add_argument(
        "--refresh-existing-only",
        action="store_true",
        help="Refresh manifests/build_cache and prune stale local MP3s without generating new audio.",
    )
    parser.add_argument(
        "--prune-removed-r2",
        action="store_true",
        help="Delete stale MP3 objects in R2 that are no longer referenced by the current manifest.",
    )
    parser.add_argument(
        "--prune-welcome-r2",
        action="store_true",
        help="Delete all legacy welcome.standard.* MP3 objects from R2 across known pack versions.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    version = (args.version or "v1").strip()
    if args.sync_r2 and args.dry_run:
        raise RuntimeError("--sync-r2 cannot be used with --dry-run")
    if args.sync_r2:
        args.upload = True
        args.prune_removed_r2 = True
    output_dir = PROJECT_ROOT / "output" / "audio_pack" / version
    manifest_path = output_dir / "manifest.json"
    latest_path = output_dir.parent / "latest.json"
    sample_phrase_id = (args.sample_phrase_id or "").strip()
    review_path = Path(args.review_input)
    if not review_path.is_absolute():
        review_path = PROJECT_ROOT / review_path

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

    if args.refresh_existing_only:
        phrases = _refresh_existing_output(
            version=version,
            output_dir=output_dir,
            core_only=args.core_only,
            review_path=review_path,
        )
        manifest = _manifest_for_output(version=version, output_dir=output_dir, generated_phrases=phrases)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Manifest written: {manifest_path}")
        latest_payload = _build_latest_payload(version=version, manifest_key=f"{version}/manifest.json")
        latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
        print(f"Latest pointer written: {latest_path}")
        if args.prune_removed_r2:
            _prune_removed_r2_keys(version, manifest_path)
        if args.prune_welcome_r2:
            _prune_welcome_r2(output_dir.parent)
        return 0

    phrases, output_dir = _generate_audio(
        version=version,
        output_dir=output_dir,
        core_only=args.core_only,
        dry_run=args.dry_run,
        sample_one=args.sample_one,
        sample_phrase_id=sample_phrase_id if sample_phrase_id else None,
        sample_language=args.sample_language,
        review_path=review_path,
        skip_validation=args.skip_validation,
    )

    if args.changed_only and not args.dry_run:
        print("Changed-only mode requested: build cache will skip unchanged MP3s.")

    if not args.dry_run:
        manifest = _manifest_for_output(version=version, output_dir=output_dir, generated_phrases=phrases)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Manifest written: {manifest_path}")
        latest_payload = _build_latest_payload(version=version, manifest_key=f"{version}/manifest.json")
        latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
        print(f"Latest pointer written: {latest_path}")

    if args.upload and not args.dry_run:
        _upload_to_r2(version, output_dir, manifest_path, latest_path)
    if args.prune_removed_r2 and not args.dry_run:
        _prune_removed_r2_keys(version, manifest_path)
    if args.prune_welcome_r2 and not args.dry_run:
        _prune_welcome_r2(output_dir.parent)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
