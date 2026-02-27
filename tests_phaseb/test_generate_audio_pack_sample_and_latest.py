import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "generate_audio_pack.py"
SPEC = importlib.util.spec_from_file_location("generate_audio_pack", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _mk_phrase(pid: str, lang: str) -> object:
    return mod.PhraseItem(
        phrase_id=pid,
        language=lang,
        text=f"text-{pid}-{lang}",
        persona="personal_trainer",
        priority="core",
    )


def test_select_phrases_sample_one_respects_language():
    phrases = [_mk_phrase("b", "no"), _mk_phrase("a", "en"), _mk_phrase("a", "no")]
    selected = mod._select_phrases_for_run(
        phrases=phrases,
        sample_one=True,
        sample_phrase_id=None,
        sample_language="en",
    )
    assert len(selected) == 1
    assert selected[0].phrase_id == "a"
    assert selected[0].language == "en"


def test_select_phrases_by_id_raises_if_missing():
    phrases = [_mk_phrase("a", "en")]
    try:
        mod._select_phrases_for_run(
            phrases=phrases,
            sample_one=False,
            sample_phrase_id="missing.id",
            sample_language="en",
        )
        assert False, "Expected ValueError for missing phrase id"
    except ValueError as exc:
        assert "Sample phrase not found" in str(exc)


def test_manifest_counts_only_existing_files(tmp_path: Path):
    out = tmp_path / "v1"
    (out / "en").mkdir(parents=True)
    # Create exactly one file
    f = out / "en" / "zone.main_started.1.mp3"
    f.write_bytes(b"fake")
    phrases = [_mk_phrase("zone.main_started.1", "en"), _mk_phrase("zone.main_started.1", "no")]

    manifest = mod._manifest_for_output("v1", out, phrases)
    assert manifest["languages"] == ["en"]
    assert manifest["total_files"] == 1
    assert len(manifest["phrases"]) == 1
    assert "en" in manifest["phrases"][0]
    assert "no" not in manifest["phrases"][0]


def test_latest_payload_points_to_versioned_manifest(monkeypatch):
    monkeypatch.setenv("R2_PUBLIC_URL", "https://pub.example.r2.dev")
    payload = mod._build_latest_payload(version="v1", manifest_key="v1/manifest.json")
    assert payload["latest_version"] == "v1"
    assert payload["manifest_key"] == "v1/manifest.json"
    assert payload["manifest_url"] == "https://pub.example.r2.dev/v1/manifest.json"
    # JSON serializable contract
    json.dumps(payload)


def test_pack_persona_policy_non_toxic_ids_are_personal_trainer():
    phrases = mod._build_phrase_list(core_only=False)
    offenders = [
        item
        for item in phrases
        if not item.phrase_id.startswith("toxic.") and item.persona != "personal_trainer"
    ]
    assert offenders == []
