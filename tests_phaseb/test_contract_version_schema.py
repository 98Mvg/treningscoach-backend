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


def test_continuous_response_includes_contract_version_and_summary(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="contract_v2_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="warmup")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "contract_version": "2",
            "session_id": session_id,
            "phase": "warmup",
            "elapsed_seconds": "30",
            "language": "no",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "watch_connected": "false",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("contract_version") == "2"
    assert "workout_context_summary" in payload


def test_talk_response_includes_contract_version(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.brain_router, "get_question_response", lambda *args, **kwargs: "Keep steady.")
    monkeypatch.setattr(main.brain_router, "get_last_route_meta", lambda: {"provider": "config", "status": "success"})

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "contract_version": "2",
            "message": "How am I doing?",
            "trigger_source": "button",
            "context": "workout",
            "language": "en",
            "persona": "personal_trainer",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("contract_version") == "2"
