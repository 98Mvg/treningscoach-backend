from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"


def test_continuous_start_is_not_blocked_without_auth_token() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "func startWorkout() {" in text
    assert "activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "private func startContinuousWorkoutInternal() {" in text
    assert "guard !isContinuousMode else { return }" in text
    assert "clearWatchStartPendingState()" in text
    assert "Continuous workout blocked: missing auth token" not in text
    assert "You must sign in to start coaching." not in text


def test_continuous_loop_stops_on_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if handleAuthFailureIfNeeded(error) {" in text
    assert "private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {" in text
    assert "stopContinuousWorkout()" in text
    assert "workoutState = .idle" in text


def test_guest_mode_suppresses_further_backend_calls_after_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var guestBackendSuppressed = false" in text
    assert "private func shouldSuppressProtectedBackendRequests() -> Bool {" in text
    assert "private func suppressProtectedBackendRequestsForGuest() {" in text
    assert "private func primeGuestBackendSuppressionIfNeeded() {" in text
    assert "suppressProtectedBackendRequestsForGuest()" in text
    assert "print(\"⚠️ TALK_BACKEND_SUPPRESSED" in text
    assert "print(\"⚠️ COACHING_BACKEND_SUPPRESSED" in text
    assert "if !AppConfig.Auth.requireSignInForWorkoutStart, !authManager.hasUsableSession() {" in text


def test_continuous_start_prearms_guest_backend_suppression_without_session() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    start_block = text.split("private func startContinuousWorkoutInternal() {", 1)[1].split("do {", 1)[0]
    assert "resetGuestBackendSuppression()" in start_block
    assert "primeGuestBackendSuppressionIfNeeded()" in start_block
    assert 'print("⚠️ GUEST_BACKEND_PRESET active=true")' in text


def test_backend_continuous_request_allows_missing_auth_header() -> None:
    text = API.read_text(encoding="utf-8")
    assert "createContinuousMultipartRequest" in text
    assert "addAuthHeader(to: &request)" in text
    assert "guard addAuthHeader(to: &request) else {" not in text
    assert "case authenticationRequired" in text
