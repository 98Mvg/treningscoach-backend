import io
import inspect
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from coaching_intelligence import calculate_next_interval, should_coach_speak


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


def _build_client(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    def _persona_text(_breath_data, _phase, language="en", persona=None, user_name=None):
        _ = (language, user_name)
        if persona == "toxic_mode":
            return "Move now."
        return "Hold rhythm."

    monkeypatch.setattr(main, "get_coach_response_continuous", _persona_text)
    return main.app.test_client()


def _create_seeded_session(persona: str) -> str:
    session_id = main.session_manager.create_session(
        user_id=f"persona_contract_{persona}",
        persona=persona,
    )
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)

    seed_time = (datetime.now() - timedelta(seconds=90)).isoformat()
    state["is_first_breath"] = False
    state["breath_history"] = [
        {
            "timestamp": seed_time,
            "intensity": "moderate",
            "tempo": 16.0,
            "volume": 35.0,
            "breath_regularity": 0.55,
            "inhale_exhale_ratio": 0.7,
            "signal_quality": 0.8,
            "respiratory_rate": 16.0,
        }
    ]
    state["coaching_history"] = [{"timestamp": seed_time, "text": "Hold rhythm."}]
    state["last_coaching_time"] = seed_time
    return session_id


def _continuous_call(client, session_id: str, persona: str):
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "120",
            "language": "en",
            "persona": persona,
            "training_level": "intermediate",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    return response.get_json()


def test_event_motor_functions_do_not_accept_persona():
    assert "persona" not in inspect.signature(should_coach_speak).parameters
    assert "persona" not in inspect.signature(calculate_next_interval).parameters


def test_event_motor_outputs_are_persona_invariant(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    personal_session = _create_seeded_session("personal_trainer")
    toxic_session = _create_seeded_session("toxic_mode")

    personal_payload = _continuous_call(client, personal_session, "personal_trainer")
    toxic_payload = _continuous_call(client, toxic_session, "toxic_mode")

    assert personal_payload["text"] != toxic_payload["text"]

    invariant_fields = [
        "should_speak",
        "reason",
        "wait_seconds",
        "coach_score",
        "coach_score_line",
    ]
    for field in invariant_fields:
        assert personal_payload[field] == toxic_payload[field], field
