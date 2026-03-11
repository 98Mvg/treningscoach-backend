from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
CORE_AUDIO_PACK = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Resources"
    / "CoreAudioPack"
)
PHRASE_REVIEW_DIR = REPO_ROOT / "output" / "phrase_review"


def test_workout_runtime_no_longer_fetches_or_logs_welcome() -> None:
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")

    assert "playWelcomeMessage()" not in text
    assert "getWelcomeMessage(" not in text
    assert "welcome.standard." not in text


def test_core_audio_pack_no_longer_contains_welcome_mp3s() -> None:
    stale = sorted(CORE_AUDIO_PACK.rglob("welcome.standard.*.mp3"))
    assert stale == [], f"CoreAudioPack still contains retired welcome MP3s: {stale}"


def test_phrase_review_artifacts_do_not_include_stale_welcome_exports() -> None:
    stale_files = [
        PHRASE_REVIEW_DIR / "phrase_catalog.tsv",
        PHRASE_REVIEW_DIR / "phrase_catalog_readable.html",
        PHRASE_REVIEW_DIR / "phrase_catalog_readable.rtf",
    ]
    existing = [path for path in stale_files if path.exists()]
    assert existing == [], f"Stale phrase review exports should be removed: {existing}"
