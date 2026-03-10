import os
import re
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def test_workout_talk_never_claims_hr_when_hr_is_invalid(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main.brain_router,
        "get_question_response",
        lambda *args, **kwargs: "Your heart rate is 170 BPM. Keep pushing.",
    )
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "grok", "source": "ai_qna", "status": "success"},
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "message": "What should I do now?",
            "context": "workout",
            "trigger_source": "button",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 300,
                "rep_index": 3,
                "reps_total": 4,
                "rep_remaining_s": 45,
                "reps_remaining_including_current": 2,
            },
            "workout_context": {
                "phase": "work",
                "heart_rate": 0,
                "zone_state": "hr_missing",
                "target_hr_low": 150,
                "target_hr_high": 165,
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    text = payload["text"]
    assert not re.search(r"\b\d{2,3}\s*bpm\b", text.lower())
    assert "2 intervals left" in text.lower()
    assert payload["fallback_used"] is True


def test_workout_talk_can_reference_hr_when_hr_is_valid(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main.brain_router,
        "get_question_response",
        lambda *args, **kwargs: "Your heart rate is 150 BPM, stay smooth.",
    )
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "grok", "source": "ai_qna", "status": "success"},
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "message": "How is my pace?",
            "context": "workout",
            "trigger_source": "button",
            "language": "en",
            "workout_context_summary": {
                "phase": "main",
                "time_left_s": 240,
                "reps_remaining_including_current": None,
            },
            "workout_context": {
                "phase": "main",
                "heart_rate": 150,
                "zone_state": "in_zone",
                "target_hr_low": 145,
                "target_hr_high": 160,
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    text = payload["text"].lower()
    assert "150 bpm" in text
    assert payload["fallback_used"] is False


def test_workout_talk_replaces_generic_qa_fallback_with_short_workout_fallback(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main.brain_router,
        "get_question_response",
        lambda *args, **kwargs: (
            "Training improves endurance, heart health, and day-to-day energy. "
            "Start easy and stay consistent."
        ),
    )
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {
            "provider": "config",
            "source": "config_fallback",
            "status": "all_question_brains_failed_or_skipped",
        },
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "message": "How am I doing?",
            "context": "workout",
            "trigger_source": "wake_word",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 180,
                "reps_remaining_including_current": 2,
            },
            "workout_context": {
                "phase": "work",
                "heart_rate": 0,
                "zone_state": "hr_missing",
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["fallback_used"] is True
    assert "Training improves endurance" not in payload["text"]
    assert "2 intervals left" in payload["text"]


def test_workout_talk_replaces_non_grok_provider_with_short_workout_fallback(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main.brain_router,
        "get_question_response",
        lambda *args, **kwargs: "Here is a long generic answer that should not survive.",
    )
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {
            "provider": "config",
            "source": "config_fallback",
            "status": "success",
        },
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "message": "How many intervals are left?",
            "context": "workout",
            "trigger_source": "button",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 180,
                "reps_remaining_including_current": 2,
            },
            "workout_context": {
                "phase": "work",
                "heart_rate": 0,
                "zone_state": "hr_missing",
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["fallback_used"] is True
    assert "generic answer" not in payload["text"].lower()
    assert "2 intervals left" in payload["text"]


def test_workout_talk_uses_session_history_and_recent_zone_events(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    session_id = main.session_manager.create_session(
        user_id="talk_context_user",
        persona="personal_trainer",
    )
    main.session_manager.init_workout_state(session_id, phase="work")
    main.session_manager.add_message(session_id, "user", "How many intervals are left?")
    main.session_manager.add_message(session_id, "assistant", "Two intervals left.")
    main.session_manager.sessions[session_id]["metadata"]["recent_zone_events"] = [
        {
            "event_type": "above_zone",
            "text": "Ease off a touch.",
            "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=7)).isoformat(),
        }
    ]

    captured = {}

    def _capture_prompt(prompt: str, **kwargs):
        captured["prompt"] = prompt
        return "Two left. About three minutes."

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.brain_router, "get_question_response", _capture_prompt)
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "grok", "source": "ai_qna", "status": "success"},
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "session_id": session_id,
            "message": "How long is left in this workout?",
            "context": "workout",
            "trigger_source": "button",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 180,
                "reps_remaining_including_current": 2,
            },
            "workout_context": {
                "phase": "work",
                "heart_rate": 0,
                "zone_state": "hr_missing",
            },
        },
    )

    assert response.status_code == 200
    prompt = captured["prompt"].lower()
    assert "recent conversation:" in prompt
    assert "user: how many intervals are left?" in prompt
    assert "coach: two intervals left." in prompt
    assert "recent deterministic workout events:" in prompt
    assert "above_zone: ease off a touch." in prompt


def test_workout_talk_fast_falls_back_when_stt_errors(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    called = {"router": False}

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main,
        "transcribe_talk_audio",
        lambda filepath, language, timeout_seconds: (None, "stt_error"),
    )

    def _unexpected_router(*args, **kwargs):
        called["router"] = True
        return "Should not be used."

    monkeypatch.setattr(main.brain_router, "get_question_response", _unexpected_router)
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    with open(fake_audio, "rb") as audio_handle:
        response = client.post(
            "/coach/talk",
            data={
                "context": "workout",
                "trigger_source": "wake_word",
                "language": "en",
                "persona": "personal_trainer",
                "audio": (audio_handle, "talk.wav"),
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["fallback_used"] is True
    assert payload["provider"] == "config"
    assert payload["stt_source"] == "stt_error"
    assert called["router"] is False
    assert "Stay smooth and controlled" in payload["text"]


def test_workout_talk_fast_falls_back_when_stt_is_disabled(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    called = {"router": False}

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main,
        "transcribe_talk_audio",
        lambda filepath, language, timeout_seconds: (None, "stt_disabled"),
    )

    def _unexpected_router(*args, **kwargs):
        called["router"] = True
        return "Should not be used."

    monkeypatch.setattr(main.brain_router, "get_question_response", _unexpected_router)
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    with open(fake_audio, "rb") as audio_handle:
        response = client.post(
            "/coach/talk",
            data={
                "context": "workout",
                "trigger_source": "wake_word",
                "language": "en",
                "persona": "personal_trainer",
                "audio": (audio_handle, "talk.wav"),
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["fallback_used"] is True
    assert payload["provider"] == "config"
    assert payload["stt_source"] == "stt_disabled"
    assert called["router"] is False
    assert "Stay smooth and controlled" in payload["text"]


def test_workout_talk_fast_falls_back_when_stt_is_quota_limited(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    called = {"router": False}

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main,
        "transcribe_talk_audio",
        lambda filepath, language, timeout_seconds: (None, "stt_quota_limited"),
    )

    def _unexpected_router(*args, **kwargs):
        called["router"] = True
        return "Should not be used."

    monkeypatch.setattr(main.brain_router, "get_question_response", _unexpected_router)
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    with open(fake_audio, "rb") as audio_handle:
        response = client.post(
            "/coach/talk",
            data={
                "context": "workout",
                "trigger_source": "wake_word",
                "language": "en",
                "persona": "personal_trainer",
                "audio": (audio_handle, "talk.wav"),
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["fallback_used"] is True
    assert payload["provider"] == "config"
    assert payload["stt_source"] == "stt_quota_limited"
    assert called["router"] is False
    assert "Stay smooth and controlled" in payload["text"]


def test_workout_talk_forces_grok_only_for_button_and_wake_word(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk.wav"
    fake_audio.write_bytes(b"RIFF")

    captured = {}

    def _capture_question_response(prompt: str, **kwargs):
        captured["prompt"] = prompt
        captured["kwargs"] = kwargs
        return "Hold the pace."

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.brain_router, "get_question_response", _capture_question_response)
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "grok", "source": "ai_qna", "status": "success"},
    )
    monkeypatch.setattr(main.config, "TALK_CONTEXT_SUMMARY_ENABLED", True, raising=False)

    client = main.app.test_client()
    response = client.post(
        "/coach/talk",
        json={
            "message": "How am I doing?",
            "context": "workout",
            "trigger_source": "button",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 180,
                "reps_remaining_including_current": 2,
            },
        },
    )

    assert response.status_code == 200
    assert captured["kwargs"]["restrict_brains"] == ["grok"]

    wake_response = client.post(
        "/coach/talk",
        json={
            "message": "Coach, what should I focus on?",
            "context": "workout",
            "trigger_source": "wake_word",
            "language": "en",
            "workout_context_summary": {
                "phase": "work",
                "time_left_s": 120,
                "reps_remaining_including_current": 1,
            },
        },
    )

    assert wake_response.status_code == 200
    assert captured["kwargs"]["restrict_brains"] == ["grok"]
