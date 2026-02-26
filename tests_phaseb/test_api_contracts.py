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
    def _mock_generate_voice(_text, language=None, persona=None, emotional_mode=None):
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
    assert isinstance(payload.get("quality_guards"), dict)
    assert isinstance(payload.get("product_flags"), dict)
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


def test_tts_cache_stats_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)

    class _StubTTS:
        def get_cache_stats(self):
            return {
                "enabled": True,
                "files": 3,
                "total_bytes": 1200,
                "cache_hits": 4,
                "cache_misses": 2,
                "hit_rate": 0.667,
                "version": "v1",
                "max_files": 1000,
                "max_age_seconds": 1209600,
            }

    monkeypatch.setattr(main, "USE_ELEVENLABS", True, raising=False)
    monkeypatch.setattr(main, "elevenlabs_tts", _StubTTS(), raising=False)

    response = client.get("/tts/cache/stats")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get("enabled") is True
    assert isinstance(payload.get("files"), int)
    assert isinstance(payload.get("cache_hits"), int)
    assert isinstance(payload.get("cache_misses"), int)


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


def test_coach_talk_question_uses_qna_path(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    called = {"qna": False}

    def _mock_qna(*args, **kwargs):
        called["qna"] = True
        _ = (args, kwargs)
        return "Training builds endurance. It improves heart health. It boosts daily energy."

    monkeypatch.setattr(main.brain_router, "get_question_response", _mock_qna)

    response = client.post(
        "/coach/talk",
        json={
            "message": "Why should I train?",
            "context": "chat",
            "persona": "personal_trainer",
            "language": "en",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert called["qna"] is True
    assert isinstance(payload.get("text"), str)
    assert payload["text"].count(".") <= 3
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
    assert "coach_score" in payload
    assert "coach_score_line" in payload
    assert "coach_score_v2" in payload
    assert "coach_score_components" in payload
    assert "cap_reason_codes" in payload
    assert "cap_applied" in payload
    assert "cap_applied_reason" in payload
    assert "hr_valid_main_set_seconds" in payload
    assert "zone_valid_main_set_seconds" in payload
    assert "zone_compliance" in payload
    assert "breath_available_reliable" in payload
    assert "decision_owner" in payload
    assert "decision_reason" in payload
    assert "breath_quality_state" in payload
    assert isinstance(payload["coach_score"], int)
    assert isinstance(payload["coach_score_line"], str)


def test_launch_home_uses_store_links_from_context(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    monkeypatch.setattr(main, "APP_STORE_URL", "https://apps.apple.com/app/id1234567890", raising=False)
    monkeypatch.setattr(main, "GOOGLE_PLAY_URL", "https://play.google.com/store/apps/details?id=com.coachi.app", raising=False)
    monkeypatch.setattr(main, "ANDROID_EARLY_ACCESS_URL", "https://coachi.example/android-early", raising=False)

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers.get("X-Web-Variant") == "launch"
    assert "https://apps.apple.com/app/id1234567890" in html
    assert "https://play.google.com/store/apps/details?id=com.coachi.app" in html
    assert "https://coachi.example/android-early" in html


def test_app_runtime_contract(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)
    response = client.get("/app/runtime")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert payload.get("status") == "ok"
    assert isinstance(payload.get("version"), str)
    assert isinstance(payload.get("timestamp"), str)
    flags = payload.get("product_flags")
    assert isinstance(flags, dict)
    assert isinstance(flags.get("app_free_mode"), bool)
    assert isinstance(flags.get("billing_enabled"), bool)
    assert isinstance(flags.get("premium_surfaces_enabled"), bool)
    assert isinstance(flags.get("monetization_phase"), str)


def test_landing_analytics_accepts_download_events_and_rejects_legacy_demo(monkeypatch, tmp_path):
    client = _build_client(monkeypatch, tmp_path)

    accepted = client.post(
        "/analytics/event",
        json={"event": "app_store_click", "metadata": {"language": "no", "source": "test"}},
    )
    assert accepted.status_code == 200
    assert accepted.get_json()["success"] is True

    legacy = client.post(
        "/analytics/event",
        json={"event": "demo_started", "metadata": {"language": "no"}},
    )
    assert legacy.status_code == 400
