from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.select_core_bundle import (
    CORE_BUNDLE_CATEGORIES,
    MAX_VARIANTS_PER_CATEGORY,
    _build_core_bundle_ids,
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
        "motivation",
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


def test_core_bundle_keeps_default_wake_ack_ids() -> None:
    ids = _build_core_bundle_ids()
    assert "wake_ack.en.default" in ids
    assert "wake_ack.no.default" in ids
