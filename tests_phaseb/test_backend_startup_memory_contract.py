from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "main.py"
ELEVENLABS = REPO_ROOT / "elevenlabs_tts.py"
STRATEGIC = REPO_ROOT / "strategic_brain.py"
CONFIG = REPO_ROOT / "config.py"


def test_main_defers_breath_analysis_and_logs_memory_checkpoints() -> None:
    text = MAIN.read_text(encoding="utf-8")

    assert "class _LazyBreathAnalyzer:" in text
    assert "breath_analyzer = _LazyBreathAnalyzer(" in text
    assert 'logger.info("ℹ️ Librosa pre-warm deferred until first breath-analysis request")' in text
    assert '_log_memory_checkpoint("database_initialized")' in text
    assert '_log_memory_checkpoint("elevenlabs_init_start")' in text
    assert '_log_memory_checkpoint("chat_blueprint_registered")' in text
    assert "strategic_brain = get_strategic_brain()" not in text


def test_tts_and_strategic_clients_load_provider_sdks_lazily() -> None:
    elevenlabs_text = ELEVENLABS.read_text(encoding="utf-8")
    strategic_text = STRATEGIC.read_text(encoding="utf-8")

    assert "def _get_elevenlabs_sdk():" in elevenlabs_text
    assert "from elevenlabs import VoiceSettings" in elevenlabs_text
    assert "from elevenlabs.client import ElevenLabs" in elevenlabs_text
    assert "def _get_anthropic_class():" in strategic_text
    assert "from anthropic import Anthropic" in strategic_text


def test_config_exposes_startup_memory_and_prewarm_flags() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert 'BACKEND_STARTUP_MEMORY_LOGGING_ENABLED = _env_bool("BACKEND_STARTUP_MEMORY_LOGGING_ENABLED", True)' in text
    assert 'LIBROSA_STARTUP_PREWARM_ENABLED = _env_bool("LIBROSA_STARTUP_PREWARM_ENABLED", False)' in text


def test_generate_voice_uses_lazy_tts_helper(monkeypatch, tmp_path) -> None:
    fake_audio = tmp_path / "coach.mp3"
    fake_audio.write_bytes(b"ID3")

    class _StubTTS:
        def generate_audio(self, *args, **kwargs):
            _ = (args, kwargs)
            return str(fake_audio)

    monkeypatch.setattr(main, "USE_ELEVENLABS", True, raising=False)
    monkeypatch.setattr(main, "_get_elevenlabs_tts", lambda: _StubTTS(), raising=False)

    result = main.generate_voice("Keep going", language="en", persona="personal_trainer")

    assert result == str(fake_audio)
