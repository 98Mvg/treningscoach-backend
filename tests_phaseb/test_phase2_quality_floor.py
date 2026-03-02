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


def _seed_nonfirst_session(persona: str = "personal_trainer") -> str:
    session_id = main.session_manager.create_session(user_id="phase2_quality_user", persona=persona)
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    old_ts = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": old_ts, "text": "Hold pace."}]
    state["last_coaching_time"] = old_ts
    return session_id


def test_validation_enforcement_falls_back_to_template(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "_get_or_create_session_timeline", lambda _session_id: None)
    monkeypatch.setattr(main, "get_coach_response_continuous", lambda *args, **kwargs: "Invalid generated cue")
    monkeypatch.setattr(main, "validate_coaching_text", lambda **kwargs: False)
    monkeypatch.setattr(main, "get_template_message", lambda **kwargs: "Template fallback cue")

    monkeypatch.setattr(main.config, "COACHING_VALIDATION_ENFORCE", True, raising=False)
    monkeypatch.setattr(main.config, "COACHING_VALIDATION_SHADOW_MODE", True, raising=False)

    session_id = _seed_nonfirst_session()
    client = main.app.test_client()

    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "90",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "standard",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["text"] == "Template fallback cue"
    assert payload["brain_source"] == "coaching_validation"
    assert payload["brain_status"] == "template_fallback"


def test_timeline_enforcement_preserves_zone_event_priority(monkeypatch, tmp_path):
    class _StubTimeline:
        def get_breathing_cue(self, phase, elapsed_seconds, language):
            _ = (phase, elapsed_seconds, language)
            return "Timeline override cue"

    def _zone_tick(**kwargs):
        _ = kwargs
        return {
            "should_speak": True,
            "reason": "below_zone_push",
            "coach_text": "Zone priority cue",
            "event_type": "below_zone_push",
            "heart_rate": 148,
            "zone_status": "below_zone",
            "target_zone_label": "Z2",
            "target_hr_low": 140,
            "target_hr_high": 150,
            "target_source": "hrr",
            "target_hr_enforced": True,
            "hr_quality": "good",
            "hr_quality_reasons": [],
            "hr_delta_bpm": -4,
            "zone_duration_seconds": 22,
            "movement_score": 0.61,
            "cadence_spm": 162.0,
            "movement_source": "cadence",
            "movement_state": "active",
            "coaching_style": "normal",
            "interval_template": "4x4",
            "recovery_seconds": None,
            "recovery_avg_seconds": None,
        }

    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "validate_coaching_text", lambda **kwargs: True)
    monkeypatch.setattr(main, "evaluate_zone_tick", _zone_tick)
    monkeypatch.setattr(main, "_get_or_create_session_timeline", lambda _session_id: _StubTimeline())

    monkeypatch.setattr(main.config, "BREATHING_TIMELINE_ENFORCE", True, raising=False)
    monkeypatch.setattr(main.config, "BREATHING_TIMELINE_SHADOW_MODE", True, raising=False)

    session_id = _seed_nonfirst_session()
    client = main.app.test_client()

    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "140",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["text"] == "Zone priority cue"
    assert payload["brain_source"].startswith("zone_event")
