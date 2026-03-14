import io
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import auth_routes
import main
from database import (
    RateLimitCounter,
    RefreshToken,
    User,
    UserProfile,
    UserSettings,
    UserSubscription,
    WorkoutHistory,
    db,
)


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
        _ = (language, persona, emotional_mode)
        return audio_path

    return _mock_generate_voice


def _build_media_client(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", _mock_generate_voice_factory(str(fake_audio)))
    monkeypatch.setattr(main, "_analyze_breath_with_timeout", lambda *args, **kwargs: _mock_breath_analysis(""))
    monkeypatch.setattr(main.brain_router, "get_coaching_response", lambda *args, **kwargs: "Keep going!")
    monkeypatch.setattr(main.brain_router, "get_question_response", lambda *args, **kwargs: "Hold this pace.")
    monkeypatch.setattr(
        main.brain_router,
        "get_last_route_meta",
        lambda: {"provider": "config", "source": "test", "status": "success"},
        raising=False,
    )
    return main.app.test_client()


def _disable_rate_limit_bypass(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BYPASS_FOR_TESTS", "false")
    monkeypatch.setattr(auth.config, "RATE_LIMIT_BYPASS_FOR_TESTS", False, raising=False)


def _clear_rate_limit_counters():
    with main.app.app_context():
        RateLimitCounter.query.delete(synchronize_session=False)
        db.session.commit()


def _create_user(email_prefix: str, *, tier: str = "free") -> User:
    suffix = uuid.uuid4().hex[:10]
    user = User(
        email=f"{email_prefix}-{suffix}@example.com",
        display_name=f"{email_prefix}-{suffix}",
        auth_provider="google",
        auth_provider_id=f"{email_prefix}-{suffix}",
        language="en",
        training_level="intermediate",
    )
    db.session.add(user)
    db.session.flush()
    if tier:
        db.session.add(UserSubscription(user_id=user.id, tier=tier))
    db.session.commit()
    return user


def _delete_user(user_id: str) -> None:
    RefreshToken.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    WorkoutHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserProfile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserSettings.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserSubscription.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    user = db.session.get(User, user_id)
    if user is not None:
        db.session.delete(user)
    db.session.commit()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _talk_payload(*, session_id: str, user_id: str) -> dict:
    return {
        "message": "Need a quick cue",
        "context": "workout",
        "phase": "intense",
        "intensity": "moderate",
        "persona": "personal_trainer",
        "language": "en",
        "session_id": session_id,
        "user_profile_id": user_id,
    }


def _continuous_payload(*, session_id: str, user_id: str):
    return {
        "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
        "contract_version": "2",
        "session_id": session_id,
        "phase": "intense",
        "elapsed_seconds": "35",
        "language": "en",
        "persona": "personal_trainer",
        "user_profile_id": user_id,
    }


def test_public_auth_rate_limit_is_per_ip(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_IDS", raising=False)
    monkeypatch.setattr(auth_routes.config, "GOOGLE_AUTH_CONFIGURED", False, raising=False)
    _clear_rate_limit_counters()
    client = main.app.test_client()

    try:
        for _ in range(5):
            response = client.post("/auth/google", environ_overrides={"REMOTE_ADDR": "10.0.0.10"})
            assert response.status_code == 404

        blocked = client.post("/auth/google", environ_overrides={"REMOTE_ADDR": "10.0.0.10"})
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"

        other_ip = client.post("/auth/google", environ_overrides={"REMOTE_ADDR": "10.0.0.11"})
        assert other_ip.status_code == 404
    finally:
        _clear_rate_limit_counters()


def test_refresh_rate_limit_is_per_user_even_across_ips(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("refresh-limit")
        user_id = user.id

    try:
        with main.app.test_request_context("/", environ_base={"REMOTE_ADDR": "10.0.0.20"}):
            refresh_tokens = [auth.issue_refresh_token(user_id)[0] for _ in range(31)]

        for idx, token in enumerate(refresh_tokens[:30]):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": token},
                environ_overrides={"REMOTE_ADDR": f"10.0.0.{20 + (idx % 3)}"},
            )
            assert response.status_code == 200

        blocked = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_tokens[30]},
            environ_overrides={"REMOTE_ADDR": "10.0.0.99"},
        )
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_auth_me_rate_limit_is_per_user(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("auth-me-limit")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        for idx in range(60):
            response = client.get("/auth/me", headers=headers, environ_overrides={"REMOTE_ADDR": f"10.0.1.{idx % 4}"})
            assert response.status_code == 200

        blocked = client.get("/auth/me", headers=headers, environ_overrides={"REMOTE_ADDR": "10.0.1.99"})
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_profile_upsert_rate_limit_returns_429_after_20_requests(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("profile-limit")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        payload = {
            "name": "Marius",
            "profile_updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        for _ in range(20):
            response = client.post("/profile/upsert", json=payload, headers=headers)
            assert response.status_code == 200

        blocked = client.post("/profile/upsert", json=payload, headers=headers)
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_workouts_rate_limit_is_per_user_not_per_ip(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = main.app.test_client()

    with main.app.app_context():
        user_a = _create_user("workouts-limit-a")
        user_b = _create_user("workouts-limit-b")
        token_a = auth.create_jwt(user_a.id, user_a.email)
        token_b = auth.create_jwt(user_b.id, user_b.email)
        user_a_id = user_a.id
        user_b_id = user_b.id

    try:
        headers_a = _auth_headers(token_a)
        headers_b = _auth_headers(token_b)
        for _ in range(60):
            response = client.get("/workouts", headers=headers_a, environ_overrides={"REMOTE_ADDR": "10.0.2.10"})
            assert response.status_code == 200

        blocked = client.get("/workouts", headers=headers_a, environ_overrides={"REMOTE_ADDR": "10.0.2.10"})
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"

        other_user = client.get("/workouts", headers=headers_b, environ_overrides={"REMOTE_ADDR": "10.0.2.10"})
        assert other_user.status_code == 200
    finally:
        with main.app.app_context():
            _delete_user(user_a_id)
            _delete_user(user_b_id)
        _clear_rate_limit_counters()


def test_continuous_rate_limit_returns_429_after_30_requests(monkeypatch, tmp_path):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = _build_media_client(monkeypatch, tmp_path)

    with main.app.app_context():
        user = _create_user("continuous-limit")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        for _ in range(30):
            response = client.post(
                "/coach/continuous",
                data=_continuous_payload(session_id="session_continuous_limit", user_id=user_id),
                headers=headers,
                content_type="multipart/form-data",
            )
            assert response.status_code == 200

        blocked = client.post(
            "/coach/continuous",
            data=_continuous_payload(session_id="session_continuous_limit", user_id=user_id),
            headers=headers,
            content_type="multipart/form-data",
        )
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_free_talk_rate_limit_tracks_session_usage(monkeypatch, tmp_path):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = _build_media_client(monkeypatch, tmp_path)

    with main.app.app_context():
        user = _create_user("talk-free-session", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        for _ in range(3):
            response = client.post("/coach/talk", json=_talk_payload(session_id="session_free_cap", user_id=user_id), headers=headers)
            assert response.status_code == 200

        blocked = client.post("/coach/talk", json=_talk_payload(session_id="session_free_cap", user_id=user_id), headers=headers)
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_free_talk_rate_limit_caps_daily_usage_across_sessions(monkeypatch, tmp_path):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = _build_media_client(monkeypatch, tmp_path)

    with main.app.app_context():
        user = _create_user("talk-free-day", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        for index in range(6):
            response = client.post(
                "/coach/talk",
                json=_talk_payload(session_id=f"session_free_day_{index}", user_id=user_id),
                headers=headers,
            )
            assert response.status_code == 200

        blocked = client.post(
            "/coach/talk",
            json=_talk_payload(session_id="session_free_day_blocked", user_id=user_id),
            headers=headers,
        )
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_premium_talk_rate_limit_uses_premium_quota_not_free_session_cap(monkeypatch, tmp_path):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    client = _build_media_client(monkeypatch, tmp_path)

    with main.app.app_context():
        user = _create_user("talk-premium", tier="premium")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = _auth_headers(token)
        for _ in range(15):
            response = client.post(
                "/coach/talk",
                json=_talk_payload(session_id="session_premium_cap", user_id=user_id),
                headers=headers,
            )
            assert response.status_code == 200

        blocked = client.post(
            "/coach/talk",
            json=_talk_payload(session_id="session_premium_cap", user_id=user_id),
            headers=headers,
        )
        assert blocked.status_code == 429
        assert blocked.get_json()["error"] == "Rate limit exceeded"
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()
