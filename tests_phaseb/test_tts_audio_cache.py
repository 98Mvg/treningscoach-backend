import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import elevenlabs_tts


def _fake_elevenlabs_class(counter):
    class _FakeTextToSpeech:
        def __init__(self, calls):
            self._calls = calls

        def convert(self, **kwargs):
            self._calls["count"] += 1
            marker = kwargs.get("text", "tts").encode("utf-8")
            return [b"ID3", marker]

    class _FakeElevenLabs:
        def __init__(self, api_key):
            _ = api_key
            self.text_to_speech = _FakeTextToSpeech(counter)

    return _FakeElevenLabs


def _build_tts(monkeypatch, tmp_path, counter):
    monkeypatch.setattr(elevenlabs_tts, "ElevenLabs", _fake_elevenlabs_class(counter))
    tts = elevenlabs_tts.ElevenLabsTTS(api_key="test_key", voice_id="default_voice")
    tts.cache_dir = str(tmp_path)
    os.makedirs(tts.cache_dir, exist_ok=True)
    return tts


def test_tts_audio_cache_hit_skips_second_provider_call(monkeypatch, tmp_path):
    counter = {"count": 0}
    tts = _build_tts(monkeypatch, tmp_path, counter)

    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_READ_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_WRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_VERSION", "v1", raising=False)

    first_path = tts.generate_audio("Perfect! Keep going!", language="en", persona="personal_trainer")
    second_path = tts.generate_audio("Perfect! Keep going!", language="en", persona="personal_trainer")

    assert counter["count"] == 1
    assert first_path == second_path
    assert os.path.exists(second_path)


def test_tts_audio_cache_disabled_calls_provider_each_time(monkeypatch, tmp_path):
    counter = {"count": 0}
    tts = _build_tts(monkeypatch, tmp_path, counter)

    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_ENABLED", False, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_READ_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_WRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_VERSION", "v1", raising=False)

    path_one = str(tmp_path / "one.mp3")
    path_two = str(tmp_path / "two.mp3")

    tts.generate_audio("Perfect! Keep going!", output_path=path_one, language="en")
    tts.generate_audio("Perfect! Keep going!", output_path=path_two, language="en")

    assert counter["count"] == 2
    assert os.path.exists(path_one)
    assert os.path.exists(path_two)


def test_tts_audio_cache_version_change_forces_regeneration(monkeypatch, tmp_path):
    counter = {"count": 0}
    tts = _build_tts(monkeypatch, tmp_path, counter)

    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_READ_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_WRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_VERSION", "v1", raising=False)

    path_v1 = tts.generate_audio("Perfect! Keep going!", language="en")
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_VERSION", "v2", raising=False)
    path_v2 = tts.generate_audio("Perfect! Keep going!", language="en")

    assert counter["count"] == 2
    assert path_v1 != path_v2


def test_tts_audio_cache_cleanup_respects_max_files(monkeypatch, tmp_path):
    counter = {"count": 0}
    tts = _build_tts(monkeypatch, tmp_path, counter)

    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_READ_ENABLED", False, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_WRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_VERSION", "v1", raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_MAX_FILES", 2, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_MAX_AGE_SECONDS", 86400, raising=False)
    monkeypatch.setattr(config, "TTS_AUDIO_CACHE_CLEANUP_INTERVAL_WRITES", 1, raising=False)

    tts.generate_audio("A", language="en")
    tts.generate_audio("B", language="en")
    tts.generate_audio("C", language="en")

    cache_files = [p for p in os.listdir(tmp_path) if p.startswith("tts_") and p.endswith(".mp3")]
    assert len(cache_files) <= 2
    assert counter["count"] == 3
