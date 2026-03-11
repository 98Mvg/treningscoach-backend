from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)


def test_welcome_log_does_not_expose_utterance_id() -> None:
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")

    assert 'print("👋 Welcome: ' in text
    assert 'print("👋 Welcome [\\(welcome.utteranceID)]' not in text
