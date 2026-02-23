from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)


def _viewmodel_text() -> str:
    return WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")


def test_hr_quality_for_request_respects_current_signal_quality() -> None:
    text = _viewmodel_text()
    assert "private func resolvedHRQualityForRequest(" in text
    assert "currentQuality: hrSignalQuality" in text
    assert "let tickQuality = (tickHeartRate != nil && watchConnected) ? \"good\" : \"poor\"" not in text
