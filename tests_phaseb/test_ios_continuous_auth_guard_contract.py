from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"


def test_continuous_start_is_blocked_without_auth_token() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "guard hasValidAuthToken() else {" in text
    assert "Continuous workout blocked: missing auth token" in text
    assert "You must sign in to start coaching." in text


def test_continuous_loop_stops_on_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if handleAuthFailureIfNeeded(error) {" in text
    assert "private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {" in text
    assert "stopContinuousWorkout()" in text
    assert "workoutState = .idle" in text


def test_backend_continuous_request_requires_auth_header() -> None:
    text = API.read_text(encoding="utf-8")
    assert "guard addAuthHeader(to: &request) else {" in text
    assert "throw APIError.authenticationRequired" in text
    assert "case authenticationRequired" in text
