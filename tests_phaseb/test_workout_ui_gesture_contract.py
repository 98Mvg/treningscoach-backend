from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_WORKOUT_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ActiveWorkoutView.swift"
)


def _active_workout_view_text() -> str:
    return ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")


def test_orb_stop_requires_long_press_and_confirmation() -> None:
    text = _active_workout_view_text()
    assert ".onLongPressGesture(minimumDuration: 2.0" in text
    assert "showStopConfirmation = true" in text

    start = text.index(".onLongPressGesture(minimumDuration: 2.0")
    snippet = text[start : start + 320]
    assert "stopWorkout()" not in snippet


def test_mic_long_press_opens_pulse_control_panel() -> None:
    text = _active_workout_view_text()
    assert "LongPressGesture(minimumDuration: 1.5" in text
    assert "AudioPipelineDiagnostics.shared.diagnosticTab = .pulse" in text
    assert "showDiagnostics = true" in text


def test_diagnostics_panel_uses_sheet_presentation() -> None:
    text = _active_workout_view_text()
    assert ".sheet(isPresented: $showDiagnostics)" in text


def test_main_workout_surface_has_no_coach_text_line() -> None:
    text = _active_workout_view_text()
    assert "Text(guidanceLine)" not in text
