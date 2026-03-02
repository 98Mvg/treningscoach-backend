from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
BACKEND_API_SERVICE = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "BackendAPIService.swift"
)


def _viewmodel_text() -> str:
    return WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")


def _api_service_text() -> str:
    return BACKEND_API_SERVICE.read_text(encoding="utf-8")


def test_talk_button_requires_active_unpaused_workout() -> None:
    text = _viewmodel_text()
    assert "func talkToCoachButtonPressed()" in text
    assert "guard isContinuousMode else { return }" in text
    assert "guard !isPaused else { return }" in text
    assert "guard coachInteractionState != .responding else {" in text


def test_talk_button_uses_capture_utterance_path() -> None:
    text = _viewmodel_text()
    assert "wakeWordManager.captureUtterance(duration: 6.0)" in text
    assert "sendUserMessageToCoach(" in text


def test_talk_path_has_missing_session_fallback_endpoint() -> None:
    text = _viewmodel_text()
    assert "session_id missing for workout talk; using generic talk endpoint fallback" in text
    assert "response = try await apiService.talkToCoach(" in text
    assert 'responseMode: "qa"' in text
    assert 'context: "workout"' in text


def test_talk_path_resets_state_back_to_passive_listening() -> None:
    text = _viewmodel_text()
    assert "isTalkingToCoach = false" in text
    assert "isWakeWordActive = false" in text
    assert "coachInteractionState = .passiveListening" in text
    assert "voiceState = isContinuousMode && !isPaused ? .listening : .idle" in text


def test_api_service_marks_workout_talk_as_qna_mode() -> None:
    text = _api_service_text()
    assert "func talkToCoachDuringWorkout(" in text
    assert '"response_mode": "qa"' in text


def test_viewmodel_exposes_capture_specific_talk_state() -> None:
    text = _viewmodel_text()
    assert "var isCoachCapturingSpeech: Bool {" in text
    assert "coachInteractionState == .commandMode || isWakeWordActive" in text
