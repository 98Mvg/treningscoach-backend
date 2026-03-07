from __future__ import annotations

import sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.select_core_bundle import (
    CORE_BUNDLE_CATEGORIES,
    MAX_VARIANTS_PER_CATEGORY,
    _build_core_bundle_ids,
    _bundle_ids_for_version,
)
from tts_phrase_catalog import PHRASE_CATALOG


def _category_members(prefix: str, ids: list[str]) -> list[str]:
    return [pid for pid in ids if pid == prefix or pid.startswith(prefix + ".")]


def test_core_bundle_ids_are_unique() -> None:
    ids = _build_core_bundle_ids()
    assert len(ids) == len(set(ids)), "Core bundle IDs must not contain duplicates"


def test_core_bundle_categories_are_capped_to_max_variants() -> None:
    ids = _build_core_bundle_ids()
    for prefix in CORE_BUNDLE_CATEGORIES:
        members = _category_members(prefix, ids)
        assert len(members) <= MAX_VARIANTS_PER_CATEGORY, (
            f"{prefix} has {len(members)} entries, expected <= {MAX_VARIANTS_PER_CATEGORY}"
        )


def test_core_bundle_has_full_five_for_dense_categories() -> None:
    ids = _build_core_bundle_ids()
    dense_categories = [
        "welcome.standard",
        "cont.warmup",
        "cont.cooldown",
    ]
    catalog_ids = [entry["id"] for entry in PHRASE_CATALOG]
    for prefix in dense_categories:
        available = _category_members(prefix, catalog_ids)
        assert len(available) >= MAX_VARIANTS_PER_CATEGORY, f"Expected >=5 catalog entries for {prefix}"
        selected = _category_members(prefix, ids)
        assert len(selected) == MAX_VARIANTS_PER_CATEGORY, (
            f"Expected exactly {MAX_VARIANTS_PER_CATEGORY} for {prefix}, got {len(selected)}"
        )


def test_core_bundle_includes_staged_motivation_families() -> None:
    ids = _build_core_bundle_ids()
    for prefix in (
        "interval.motivate.s1",
        "interval.motivate.s2",
        "interval.motivate.s3",
        "interval.motivate.s4",
        "easy_run.motivate.s1",
        "easy_run.motivate.s2",
        "easy_run.motivate.s3",
        "easy_run.motivate.s4",
    ):
        members = _category_members(prefix, ids)
        assert len(members) == 2, f"Expected both staged motivation variants for {prefix}"


def test_core_bundle_includes_no_hr_structure_families() -> None:
    ids = _build_core_bundle_ids()
    assert "zone.hr_poor_timing.1" in ids
    assert "zone.structure.work.1" in ids
    assert "zone.structure.recovery.1" in ids
    assert "zone.structure.finish.1" in ids
    steady_members = _category_members("zone.structure.steady", ids)
    assert len(steady_members) == 5


def test_core_bundle_excludes_flat_motivation_pool() -> None:
    ids = _build_core_bundle_ids()
    assert all(not pid.startswith("motivation.") for pid in ids)


def test_core_bundle_keeps_default_wake_ack_ids() -> None:
    ids = _build_core_bundle_ids()
    assert "wake_ack.en.default" in ids
    assert "wake_ack.no.default" in ids


def test_v2_bundle_ids_come_from_manifest(tmp_path: Path) -> None:
    source_root = tmp_path / "v2"
    source_root.mkdir(parents=True)
    manifest_path = source_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "v2",
                "phrases": [
                    {"id": "zone.above.default.1", "en": {"file": "en/zone.above.default.1.mp3"}},
                    {"id": "zone.hr_poor_timing.1", "no": {"file": "no/zone.hr_poor_timing.1.mp3"}},
                ],
            }
        ),
        encoding="utf-8",
    )
    ids, selection_mode = _bundle_ids_for_version("v2", source_root)
    assert selection_mode == "manifest"
    assert ids == ["zone.above.default.1", "zone.hr_poor_timing.1"]


def test_v1_bundle_ids_stay_curated(tmp_path: Path) -> None:
    ids, selection_mode = _bundle_ids_for_version("v1", tmp_path / "v1")
    assert selection_mode == "curated"
    assert ids == _build_core_bundle_ids()
