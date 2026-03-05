from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"


def test_continuous_start_is_not_blocked_without_auth_token() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "func startWorkout() {\n        activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "private func startContinuousWorkoutInternal() {\n        guard !isContinuousMode else { return }\n        clearWatchStartPendingState()" in text
    assert "Continuous workout blocked: missing auth token" not in text
    assert "You must sign in to start coaching." not in text


def test_continuous_loop_stops_on_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if handleAuthFailureIfNeeded(error) {" in text
    assert "private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {" in text
    assert "stopContinuousWorkout()" in text
    assert "workoutState = .idle" in text


def test_backend_continuous_request_allows_missing_auth_header() -> None:
    text = API.read_text(encoding="utf-8")
    assert "createContinuousMultipartRequest" in text
    assert "addAuthHeader(to: &request)" in text
    assert "guard addAuthHeader(to: &request) else {" not in text
    assert "case authenticationRequired" in text
