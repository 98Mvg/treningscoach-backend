import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import main
from database import RefreshToken, User, UserProfile, UserSettings, UserSubscription, WorkoutHistory, db


def _create_user(email_prefix: str, *, tier: str = "free") -> User:
    suffix = uuid.uuid4().hex[:10]
    user = User(
        email=f"{email_prefix}-{suffix}@example.com",
        display_name=f"{email_prefix}-{suffix}",
        auth_provider="apple",
        auth_provider_id=f"{email_prefix}-{suffix}",
        language="en",
        training_level="intermediate",
    )
    db.session.add(user)
    db.session.flush()
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


def test_voice_session_requires_auth(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    client = main.app.test_client()

    response = client.post("/voice/session", json={"summary_context": {"coach_score": 88}})
    assert response.status_code == 401
    assert response.get_json()["error_code"] == "authentication_required"


def test_voice_session_rejects_non_premium_users(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", False, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", True, raising=False)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-free", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.post(
            "/voice/session",
            json={"summary_context": {"coach_score": 88}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        payload = response.get_json()
        assert payload["error_code"] == "premium_required"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_allows_free_users_while_app_free_mode(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", True, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", False, raising=False)

    def _fake_bootstrap(*, summary_context, language, user_name=None, logger=None):
        _ = (summary_context, language, user_name, logger)
        return {
            "voice_session_id": "voice_free_mode_123",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_free_mode",
            "client_secret_expires_at": 1_763_000_100,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": 300,
            "summary_context": {"coach_score": 88},
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-free-mode", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.post(
            "/voice/session",
            json={"summary_context": {"coach_score": 88}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["voice_session_id"] == "voice_free_mode_123"
        assert payload["subscription_tier"] == "free"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_returns_bootstrap_for_premium_users(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", False, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", True, raising=False)
    captured = {}

    def _fake_bootstrap(*, summary_context, language, user_name=None, logger=None):
        captured["summary_context"] = dict(summary_context)
        captured["language"] = language
        captured["user_name"] = user_name
        _ = logger
        return {
            "voice_session_id": "voice_test_123",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_test",
            "client_secret_expires_at": 1_763_000_000,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": 300,
            "summary_context": dict(summary_context),
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-premium", tier="premium")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.post(
            "/voice/session",
            json={
                "language": "no",
                "summary_context": {
                    "workout_label": "Intervaller",
                    "coach_score": 91,
                    "duration_text": "32:10",
                },
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["voice_session_id"] == "voice_test_123"
        assert payload["websocket_url"] == "wss://api.x.ai/v1/realtime"
        assert payload["client_secret"] == "ek_test"
        assert payload["voice"] == "Rex"
        assert payload["max_duration_seconds"] == 300
        assert payload["subscription_tier"] == "premium"
        assert payload["session_update_json"] == "{\"type\":\"session.update\"}"
        assert captured["language"] == "no"
        assert captured["summary_context"]["coach_score"] == 91
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_auth_me_includes_subscription_tier(monkeypatch):
    monkeypatch.setattr(main.config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60, raising=False)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("auth-tier", tier="premium")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["user"]["subscription_tier"] == "premium"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_telemetry_accepts_allowed_events(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    calls = []

    def _fake_capture(event, *, user_id, metadata=None):
        calls.append((event, user_id, dict(metadata or {})))

    monkeypatch.setattr(main, "_capture_voice_event", _fake_capture)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-telemetry", tier="premium")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.post(
            "/voice/telemetry",
            json={
                "event": "voice_session_started",
                "metadata": {"voice_session_id": "voice_test_123", "turn_count": 1},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert calls == [
            (
                "voice_session_started",
                user_id,
                {
                    "voice_session_id": "voice_test_123",
                    "turn_count": 1,
                    "subscription_tier": "premium",
                },
            )
        ]
    finally:
        with main.app.app_context():
            _delete_user(user_id)
