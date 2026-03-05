from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Models" / "Models.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"
VIEW_MODEL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
LAUNCH_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "WorkoutLaunchView.swift"


def test_easy_run_session_mode_enum_exists() -> None:
    text = MODELS.read_text(encoding="utf-8")
    assert "enum EasyRunSessionMode" in text
    assert "case timed = \"timed\"" in text
    assert "case freeRun = \"free_run\"" in text


def test_continuous_request_includes_easy_run_free_mode_fields() -> None:
    text = API.read_text(encoding="utf-8")
    assert "easyRunFreeMode: Bool = false" in text
    assert 'appendField(name: "easy_run_free_mode", value: easyRunFreeMode ? "true" : "false")' in text
    assert 'workoutPlan["main_s"] = 0' in text
    assert 'workoutPlan["free_run"] = true' in text
    assert "mainSeconds: Int? = nil" in text
    assert "cooldownSeconds: Int? = nil" in text
    assert "intervalRepeats: Int? = nil" in text
    assert 'workoutPlan["intervals"] = [' in text


def test_workout_view_model_uses_total_time_in_free_run_main_phase() -> None:
    text = VIEW_MODEL.read_text(encoding="utf-8")
    assert "var isEasyRunFreeRunActive: Bool {" in text
    assert 'if isEasyRunFreeRunActive && (resolvedPhaseKey == "main" || resolvedPhaseKey == "work") {' in text
    assert 'currentLanguage == "no"' in text
    assert '"Total tid: \\(elapsedFormatted)"' in text
    assert '"Total time: \\(elapsedFormatted)"' in text


def test_workout_launch_has_timed_free_run_toggle_and_locks_free_run_pickers() -> None:
    text = LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "private var easyRunModeToggle: some View" in text
    assert "ForEach(EasyRunSessionMode.allCases)" in text
    assert "viewModel.selectedEasyRunSessionMode == .freeRun" in text
    assert ".allowsHitTesting(false)" in text
    assert "Duration and warm-up are locked in Free Run." in text
