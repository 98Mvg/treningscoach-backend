from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
ACTIVE_WORKOUT_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ActiveWorkoutView.swift"
)
WORKOUT_LAUNCH_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "WorkoutLaunchView.swift"
)


def test_view_model_exposes_phase_countdown_text_contract():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert "var phaseCountdownPrimaryText: String {" in text
    assert "var phaseCountdownSecondaryText: String?" in text
    assert "workoutContextSummary?.timeLeftS" in text
    assert "summary.repRemainingS" in text
    assert "summary.repsTotal" in text
    assert "summary.repIndex" in text


def test_active_workout_view_renders_phase_countdown_panel():
    text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert "phaseCountdownPanel" in text
    assert "Text(viewModel.phaseCountdownPrimaryText)" in text
    assert "viewModel.phaseCountdownSecondaryText" in text


def test_interval_picker_caps_and_sensitivity_are_applied():
    text = WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "valueRange: 2...10" in text
    assert "valueRange: 1...20" in text
    assert "dragSensitivity: 1.55" in text
    assert "dragSensitivity: 1.45" in text
    assert "var dragSensitivity: Double = 1.0" in text


def test_circular_dial_visual_progress_is_value_synced():
    text = WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "let raw = safeAngle / 360.0" in text
    assert "let boostedProgress = min(1.0, max(0.0, (angle / 360.0) * max(1.0, dragSensitivity)))" in text
    assert "currentAngle = boostedProgress * 360.0" in text
    assert "let nextAngle = normalized * 360.0" in text
