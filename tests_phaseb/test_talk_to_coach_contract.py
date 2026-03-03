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
    assert "guard !isTalkingToCoach else {" in text


def test_talk_button_uses_unified_capture_request_path() -> None:
    text = _viewmodel_text()
    assert "startWorkoutTalkCapture(triggerSource: .button, playWakeAck: false)" in text
    assert "talkToCoachDuringWorkoutUnified(" in text


def test_wake_word_path_uses_ack_and_unified_capture_request_path() -> None:
    text = _viewmodel_text()
    assert "startWorkoutTalkCapture(triggerSource: .wakeWord, playWakeAck: true)" in text
    assert 'currentLanguage == "no" ? "wake_ack.no.default" : "wake_ack.en.default"' in text
    assert 'eventType: "wake_ack"' in text


def test_talk_path_has_missing_session_fallback_endpoint() -> None:
    text = _viewmodel_text()
    assert "session_id missing for workout talk; using generic talk endpoint fallback" in text
    assert "response = try await apiService.talkToCoach(" in text
    assert 'responseMode: "qa"' in text
    assert 'context: "workout"' in text
    assert "triggerSource: triggerSource.rawValue" in text


def test_talk_path_resets_state_back_to_passive_listening() -> None:
    text = _viewmodel_text()
    assert "private func finalizeWorkoutTalkSession()" in text
    assert "isTalkingToCoach = false" in text
    assert "isWakeWordActive = false" in text
    assert "coachInteractionState = .passiveListening" in text
    assert "voiceState = isContinuousMode && !isPaused ? .listening : .idle" in text


def test_talk_path_suppresses_event_speech_while_active() -> None:
    text = _viewmodel_text()
    assert "if isCoachTalkActive {" in text
    assert 'return (false, "talk_arbitration")' in text


def test_api_service_workout_talk_multipart_contract_includes_trigger_and_context() -> None:
    text = _api_service_text()
    assert "func talkToCoachDuringWorkoutUnified(" in text
    assert 'appendField(name: "response_mode", value: "qa")' in text
    assert 'appendField(name: "context", value: "workout")' in text
    assert 'appendField(name: "trigger_source", value: triggerSource)' in text
    assert 'appendField(name: "workout_phase", value: phase)' in text
    assert 'appendField(name: "workout_heart_rate", value: "\\(bpm)")' in text
    assert 'appendField(name: "workout_zone_state", value: zoneState)' in text

