import os
import re
import sys

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
