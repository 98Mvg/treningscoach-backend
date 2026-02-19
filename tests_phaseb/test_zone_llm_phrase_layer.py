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


def _seed_session():
    session_id = main.session_manager.create_session(
        user_id="zone_rephrase_user",
        persona="personal_trainer",
    )
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep rhythm."}]
    state["last_coaching_time"] = seeded
    return session_id


def _fake_zone_tick(event_text: str):
    return {
        "handled": True,
        "should_speak": True,
        "reason": "above_zone",
        "event_type": "above_zone",
        "coach_text": event_text,
        "max_silence_text": event_text,
        "zone_status": "above_zone",
        "target_zone_label": "Z2",
        "target_hr_low": 132,
        "target_hr_high": 148,
        "target_source": "hrr",
        "target_hr_enforced": True,
        "interval_template": None,
        "segment": "intense",
        "segment_key": "easy_run:intense",
        "heart_rate": 154,
        "hr_delta_bpm": 3.0,
        "hr_quality": "good",
        "hr_quality_reasons": [],
        "zone_duration_seconds": 22.0,
        "movement_score": 0.65,
        "cadence_spm": 128.0,
        "movement_source": "cadence",
        "movement_state": "moving",
        "coaching_style": "normal",
        "score": 84,
        "score_line": "CoachScore: 84 - Solid.",
        "score_confidence": "high",
        "time_in_target_pct": 78.0,
        "overshoots": 2,
        "recovery_seconds": None,
        "recovery_avg_seconds": 31.0,
        "recovery_samples_count": 2,
    }


def test_zone_llm_rewrite_changes_text_only(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", lambda **kwargs: _fake_zone_tick("Back off to zone."))
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_ALLOWED_EVENTS", ["above_zone"], raising=False)
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 16, raising=False)
    monkeypatch.setattr(main.brain_router, "rewrite_zone_event_text", lambda *args, **kwargs: "Ease off a touch.")
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "grok", "source": "zone_event_llm", "status": "rewrite_success"},
    )

    session_id = _seed_session()
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "420",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["text"] == "Ease off a touch."
    assert payload["reason"] == "above_zone"
    assert payload["coach_score"] == 84
    assert payload["zone_event"] == "above_zone"
    assert payload["brain_source"] == "zone_event_llm"


def test_zone_llm_rewrite_word_limit_falls_back(monkeypatch):
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_ALLOWED_EVENTS", ["above_zone"], raising=False)
    monkeypatch.setattr(main.config, "ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 5, raising=False)
    monkeypatch.setattr(
        main.brain_router,
        "rewrite_zone_event_text",
        lambda *args, **kwargs: "Ease off now and hold exactly this level please.",
    )

    text, meta = main._maybe_rephrase_zone_event_text(
        base_text="Back off a touch.",
        language="en",
        persona="personal_trainer",
        coaching_style="normal",
        event_type="above_zone",
    )

    assert text == "Back off a touch."
    assert meta["source"] == "zone_event_motor"
    assert meta["status"] == "rewrite_word_limit_fallback"
