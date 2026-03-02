from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WAKEWORD_MANAGER = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "WakeWordManager.swift"
)


def _wakeword_text() -> str:
    return WAKEWORD_MANAGER.read_text(encoding="utf-8")


def test_button_capture_ignores_late_cancel_errors() -> None:
    text = _wakeword_text()
    assert "guard self.isCapturingUtterance else { return }" in text
    assert "let canceled = self.isCancellationLikeError(error)" in text


def test_wake_listener_suppresses_transitional_noise_errors() -> None:
    text = _wakeword_text()
    assert "if canceled || (!self.isListening && (self.isButtonCaptureSession || noSpeech)) {" in text


def test_cancellation_error_helper_covers_assistant_domain() -> None:
    text = _wakeword_text()
    assert 'nsError.domain == "kAFAssistantErrorDomain"' in text
    assert "nsError.code == 1101" in text
