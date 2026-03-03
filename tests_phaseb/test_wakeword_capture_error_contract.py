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


def test_wake_word_manager_only_uses_coach_or_coachi() -> None:
    text = _wakeword_text()
    assert '"en": ["coach", "coachi"]' in text
    assert '"no": ["coach", "coachi"]' in text
    assert '"pt"' not in text
    assert '"snakk"' not in text


def test_wake_word_manager_enforces_10_second_cooldown() -> None:
    text = _wakeword_text()
    assert "private let wakeCooldownSeconds: TimeInterval = 10.0" in text
    assert "self.lastWakeDetectionAt = now" in text
    assert "Suppressed by cooldown" in text


def test_wake_word_manager_uses_phrase_spotting_and_no_command_transcription() -> None:
    text = _wakeword_text()
    assert "request.contextualStrings = currentWakeWords" in text
    assert "matchesWakePhrase" in text
    assert "Phase 2: Capturing utterance after wake word" not in text

