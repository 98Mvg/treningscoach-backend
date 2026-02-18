import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def _mock_breath_analysis(_path: str):
    return {
        "intensity": "moderate",
        "tempo": 16.0,
        "volume": 35.0,
        "breath_regularity": 0.55,
        "inhale_exhale_ratio": 0.7,
        "signal_quality": 0.8,
        "respiratory_rate": 16.0,
    }


def _mock_generate_voice_factory(audio_path: str):
    def _mock_generate_voice(_text, language=None, persona=None):
        return audio_path

    return _mock_generate_voice


def _build_client(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", _mock_generate_voice_factory(str(fake_audio)))
    monkeypatch.setattr(main, "strategic_brain", None, raising=False)
    monkeypatch.setattr(main.brain_router, "get_coaching_response", lambda *args, **kwargs: "Keep going!")
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)

    return main.app.test_client()


def test_health_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert payload.get("status") == "healthy"
    assert isinstance(payload.get("version"), str)
    assert isinstance(payload.get("timestamp"), str)
    assert isinstance(payload.get("endpoints"), dict)


def test_welcome_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.get("/welcome?language=en&persona=personal_trainer")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload.get("text"), str)
    assert payload.get("text")
    assert isinstance(payload.get("audio_url"), str)
    assert payload.get("audio_url", "").startswith("/download/")
    assert isinstance(payload.get("category"), str)


def test_brain_health_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.get("/brain/health")

    assert response.status_code in (200, 503)
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "active_brain" in payload
    assert "healthy" in payload
    assert "message" in payload
    assert "brain_stats" in payload


def test_coach_talk_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.post(
        "/coach/talk",
        json={
            "message": "Need a quick cue",
            "context": "workout",
            "phase": "intense",
            "intensity": "moderate",
            "persona": "personal_trainer",
            "language": "en",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload.get("text"), str)
    assert isinstance(payload.get("audio_url"), str)
    assert isinstance(payload.get("personality"), str)


def test_coach_continuous_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": "session_contract_1",
            "phase": "intense",
            "elapsed_seconds": "35",
            "language": "en",
            "persona": "personal_trainer",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "text" in payload
    assert "should_speak" in payload
    assert "breath_analysis" in payload
    assert "wait_seconds" in payload
    assert "phase" in payload
    assert "reason" in payload
