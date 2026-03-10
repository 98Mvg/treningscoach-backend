import os
import sys
import types
from concurrent.futures import TimeoutError as FuturesTimeoutError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def test_transcribe_talk_audio_fast_fails_on_quota(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    captured = {}

    class _FakeTranscriptions:
        def create(self, **kwargs):
            _ = kwargs
            raise RuntimeError("429 insufficient_quota")

    class _FakeAudio:
        def __init__(self):
            self.transcriptions = _FakeTranscriptions()

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.audio = _FakeAudio()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(main.config, "TALK_STT_ENABLED", True, raising=False)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_FakeOpenAI))

    text, source = main.transcribe_talk_audio(str(fake_audio), "en", 2.0)

    assert text is None
    assert source == "stt_quota_limited"
    assert captured["max_retries"] == 0


def test_transcribe_talk_audio_is_disabled_by_default(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    def _unexpected_openai(**kwargs):
        _ = kwargs
        raise AssertionError("OpenAI STT should not initialize when TALK_STT_ENABLED is false")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(main.config, "TALK_STT_ENABLED", False, raising=False)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_unexpected_openai))

    text, source = main.transcribe_talk_audio(str(fake_audio), "en", 2.0)

    assert text is None
    assert source == "stt_disabled"


def test_transcribe_talk_audio_uses_quota_cooldown_after_first_429(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    calls = {"clients": 0, "creates": 0}

    class _FakeTranscriptions:
        def create(self, **kwargs):
            _ = kwargs
            calls["creates"] += 1
            raise RuntimeError("429 insufficient_quota")

    class _FakeAudio:
        def __init__(self):
            self.transcriptions = _FakeTranscriptions()

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            _ = kwargs
            calls["clients"] += 1
            self.audio = _FakeAudio()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(main.config, "TALK_STT_ENABLED", True, raising=False)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_FakeOpenAI))
    monkeypatch.setattr(main.config, "TALK_STT_QUOTA_COOLDOWN_SECONDS", 60.0, raising=False)
    with main._talk_stt_lock:
        main._talk_stt_quota_skip_until = 0.0

    first_text, first_source = main.transcribe_talk_audio(str(fake_audio), "en", 2.0)
    second_text, second_source = main.transcribe_talk_audio(str(fake_audio), "en", 2.0)

    with main._talk_stt_lock:
        main._talk_stt_quota_skip_until = 0.0

    assert first_text is None
    assert first_source == "stt_quota_limited"
    assert second_text is None
    assert second_source == "stt_quota_limited"
    assert calls["clients"] == 1
    assert calls["creates"] == 1


def test_breath_analysis_timeout_uses_safe_default_and_cooldown(monkeypatch, tmp_path):
    fake_audio = tmp_path / "chunk.wav"
    fake_audio.write_bytes(b"RIFF")

    calls = {"submit": 0}

    class _FakeFuture:
        def result(self, timeout=None):
            _ = timeout
            raise FuturesTimeoutError()

        def cancel(self):
            return True

    class _FakeExecutor:
        def submit(self, fn, path):
            calls["submit"] += 1
            _ = (fn, path)
            return _FakeFuture()

    monkeypatch.setattr(main, "_breath_analysis_executor", _FakeExecutor())
    monkeypatch.setattr(main.config, "BREATH_ANALYSIS_TIMEOUT_SECONDS", 0.5, raising=False)
    monkeypatch.setattr(main.config, "BREATH_ANALYSIS_TIMEOUT_COOLDOWN_SECONDS", 1.0, raising=False)
    with main._breath_analysis_lock:
        main._breath_analysis_skip_until = 0.0

    first = main._analyze_breath_with_timeout(str(fake_audio), request_context="continuous", trace_id="t1")
    second = main._analyze_breath_with_timeout(str(fake_audio), request_context="continuous", trace_id="t2")

    assert first["analysis_error"] == "analysis_timeout"
    assert second["analysis_error"] == "analysis_timeout_cooldown"
    assert calls["submit"] == 1
