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


# ── Build cache (changed-only regeneration) ───────────────────────────

def test_content_hash_deterministic():
    p = mod.PhraseItem(phrase_id="a", language="en", text="hello", persona="personal_trainer", priority="core")
    settings = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0}
    h1 = mod._content_hash(p, settings)
    h2 = mod._content_hash(p, settings)
    assert h1 == h2


def test_content_hash_changes_on_text_edit():
    settings = {"stability": 0.5}
    p1 = mod.PhraseItem(phrase_id="a", language="en", text="Keep going!", persona="personal_trainer", priority="core")
    p2 = mod.PhraseItem(phrase_id="a", language="en", text="Push harder!", persona="personal_trainer", priority="core")
    assert mod._content_hash(p1, settings) != mod._content_hash(p2, settings)


def test_content_hash_changes_on_voice_settings():
    p = mod.PhraseItem(phrase_id="a", language="en", text="hello", persona="personal_trainer", priority="core")
    s1 = {"stability": 0.5, "similarity_boost": 0.75}
    s2 = {"stability": 0.7, "similarity_boost": 0.75}
    assert mod._content_hash(p, s1) != mod._content_hash(p, s2)


def test_content_hash_changes_on_persona():
    settings = {"stability": 0.5}
    p1 = mod.PhraseItem(phrase_id="a", language="en", text="hello", persona="personal_trainer", priority="core")
    p2 = mod.PhraseItem(phrase_id="a", language="en", text="hello", persona="toxic_mode", priority="core")
    assert mod._content_hash(p1, settings) != mod._content_hash(p2, settings)


def test_build_cache_roundtrip(tmp_path: Path):
    cache_path = tmp_path / "build_cache.json"
    cache = {"en/zone.main_started.1": "abc123", "no/zone.main_started.1": "def456"}
    mod._save_build_cache(cache_path, cache)
    loaded = mod._load_build_cache(cache_path)
    assert loaded == cache


def test_build_cache_load_missing_file(tmp_path: Path):
    cache_path = tmp_path / "does_not_exist.json"
    assert mod._load_build_cache(cache_path) == {}


def test_build_cache_load_corrupt_file(tmp_path: Path):
    cache_path = tmp_path / "broken.json"
    cache_path.write_text("NOT JSON", encoding="utf-8")
    assert mod._load_build_cache(cache_path) == {}


# ── Coaching engine validation gate ──────────────────────────────────

def test_validation_mode_realtime_for_coaching_cues():
    """Short workout cues (zone.*, coach.*, cont.*) use realtime mode (1-15 words)."""
    for pid in ("zone.in_zone.default.1", "coach.intense.calm.1", "cont.critical.1"):
        assert mod._validation_mode(pid) == "realtime", pid


def test_validation_mode_strategic_for_welcome():
    """Welcome phrases get strategic mode (2-30 words) — they're longer by design."""
    assert mod._validation_mode("welcome.standard.1") == "strategic"
    assert mod._validation_mode("welcome.beginner.3") == "strategic"


def test_validation_mode_strategic_for_signal_notices():
    """Signal/notice phrases are informational, not mid-rep cues — strategic mode."""
    for pid in ("zone.hr_poor_enter.1", "zone.hr_poor_exit.1",
                "zone.watch_disconnected.1", "zone.watch_restored.1",
                "zone.no_sensors.1"):
        assert mod._validation_mode(pid) == "strategic", pid


def test_validate_phrase_passes_short_cue():
    p = mod.PhraseItem(phrase_id="zone.in_zone.default.1", language="en",
                       text="Good. Stay in zone.", persona="personal_trainer", priority="core")
    ok, reason = mod._validate_phrase(p)
    assert ok, reason


def test_validate_phrase_blocks_too_long_realtime():
    p = mod.PhraseItem(
        phrase_id="coach.intense.calm.99", language="en",
        text="This is an extremely long sentence that should never be used as a realtime coaching cue during a workout because it has way too many words",
        persona="personal_trainer", priority="core",
    )
    ok, reason = mod._validate_phrase(p)
    assert not ok
    assert "mode=realtime" in reason


def test_validate_phrase_blocks_forbidden_phrase():
    p = mod.PhraseItem(
        phrase_id="zone.in_zone.default.99", language="en",
        text="Great breathing exercise today!",
        persona="personal_trainer", priority="core",
    )
    ok, reason = mod._validate_phrase(p)
    assert not ok


def test_validate_phrase_passes_strategic_long_text():
    """Welcome / notice phrases can be up to 30 words."""
    p = mod.PhraseItem(
        phrase_id="welcome.standard.99", language="en",
        text="Great to see you today. Take a moment to settle in, find your breath, and get ready for a solid workout session ahead.",
        persona="personal_trainer", priority="core",
    )
    ok, reason = mod._validate_phrase(p)
    assert ok, reason


def test_all_catalog_phrases_pass_validation():
    """Every phrase in the real catalog must pass coaching engine validation."""
    phrases = mod._build_phrase_list(core_only=False)
    failed = []
    for p in phrases:
        ok, reason = mod._validate_phrase(p)
        if not ok:
            failed.append(f"[{p.language}] {p.phrase_id}: {reason}")
    assert failed == [], f"Validation failures:\n" + "\n".join(failed)
