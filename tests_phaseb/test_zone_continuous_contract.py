import io
import os
import sys
from datetime import datetime, timedelta

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


def test_continuous_zone_contract_exposes_zone_fields(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_contract_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["workout_mode"] == "easy_run"
    assert payload["coaching_style"] == "normal"
    assert payload["zone_status"] in {"in_zone", "above_zone", "below_zone", "timing_control", "hr_unstable"}
    assert "target_zone_label" in payload
    assert "target_hr_low" in payload
    assert "target_hr_high" in payload
    assert "hr_quality" in payload
    assert "hr_delta_bpm" in payload
    assert "zone_duration_seconds" in payload
    assert "movement_score" in payload
    assert "cadence_spm" in payload
    assert "movement_source" in payload
    assert "movement_state" in payload
    assert "zone_score_confidence" in payload
    assert "zone_overshoots" in payload
    assert "coach_score_v2" in payload
    assert "coach_score_components" in payload
    assert "cap_reason_codes" in payload
    assert "cap_applied" in payload
    assert "cap_applied_reason" in payload
    assert "hr_valid_main_set_seconds" in payload
    assert "zone_valid_main_set_seconds" in payload
    assert "zone_compliance" in payload
    assert "breath_available_reliable" in payload


def test_continuous_logs_transcript_and_score_summary(monkeypatch, tmp_path, caplog):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_logs_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    caplog.set_level("INFO", logger=main.logger.name)
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "600",
            "language": "no",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "COACH_TRANSCRIPT" in messages
    assert "lang=no" in messages
    assert "CS_DEBUG_SUMMARY" in messages
    assert "cap_applied=" in messages
    assert "final_cs=" in messages
