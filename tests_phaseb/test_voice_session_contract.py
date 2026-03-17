import os
import sys
import uuid
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import main
from database import RateLimitCounter, RefreshToken, User, UserProfile, UserSettings, UserSubscription, WorkoutHistory, db


def _disable_rate_limit_bypass(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BYPASS_FOR_TESTS", "false")
    monkeypatch.setattr(auth.config, "RATE_LIMIT_BYPASS_FOR_TESTS", False, raising=False)
    monkeypatch.setattr(main.config, "RATE_LIMIT_BYPASS_FOR_TESTS", False, raising=False)


def _clear_rate_limit_counters():
    with main.app.app_context():
        RateLimitCounter.query.delete(synchronize_session=False)
        db.session.commit()


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


def _create_workout_history(
    user_id: str,
    *,
    days_ago: int,
    duration_seconds: int,
    final_phase: str,
    avg_intensity: str,
    language: str = "en",
) -> None:
    workout = WorkoutHistory(
        user_id=user_id,
        date=main._utcnow_naive() - timedelta(days=days_ago),
        duration_seconds=duration_seconds,
        final_phase=final_phase,
        avg_intensity=avg_intensity,
        language=language,
    )
    db.session.add(workout)
    db.session.commit()


def test_voice_session_requires_auth(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    client = main.app.test_client()

    response = client.post("/voice/session", json={"summary_context": {"coach_score": 88}})
    assert response.status_code == 401
    assert response.get_json()["error_code"] == "authentication_required"


def test_voice_session_returns_free_tier_bootstrap_for_non_premium_users(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", False, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", 120, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", 2, raising=False)
    captured = {}

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        captured["summary_context"] = dict(summary_context)
        captured["history_context"] = dict(history_context or {})
        captured["language"] = language
        captured["user_name"] = user_name
        captured["max_duration_seconds"] = max_duration_seconds
        _ = logger
        return {
            "voice_session_id": "voice_free_123",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_free",
            "client_secret_expires_at": 1_763_000_000,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": max_duration_seconds,
            "summary_context": dict(summary_context),
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
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
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["subscription_tier"] == "free"
        assert payload["voice_access_tier"] == "free"
        assert payload["max_duration_seconds"] == 120
        assert payload["daily_session_limit"] == 2
        assert captured["max_duration_seconds"] == 120
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_allows_free_users_while_app_free_mode(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", True, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", False, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", 120, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", 2, raising=False)

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        _ = (summary_context, history_context, language, user_name, logger)
        return {
            "voice_session_id": "voice_free_mode_123",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_free_mode",
            "client_secret_expires_at": 1_763_000_100,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": max_duration_seconds,
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
        assert payload["voice_access_tier"] == "free"
        assert payload["max_duration_seconds"] == 120
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_returns_bootstrap_for_premium_users(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_FREE_MODE", False, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_SURFACES_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS", 420, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY", 8, raising=False)
    captured = {}

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        captured["summary_context"] = dict(summary_context)
        captured["history_context"] = dict(history_context or {})
        captured["language"] = language
        captured["user_name"] = user_name
        captured["max_duration_seconds"] = max_duration_seconds
        _ = logger
        return {
            "voice_session_id": "voice_test_123",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_test",
            "client_secret_expires_at": 1_763_000_000,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": max_duration_seconds,
            "summary_context": dict(summary_context),
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-premium", tier="premium")
        user_id = user.id
        _create_workout_history(
            user_id,
            days_ago=1,
            duration_seconds=1_800,
            final_phase="cooldown",
            avg_intensity="moderate",
            language="no",
        )
        _create_workout_history(
            user_id,
            days_ago=4,
            duration_seconds=2_400,
            final_phase="intense",
            avg_intensity="intense",
        )
        _create_workout_history(
            user_id,
            days_ago=40,
            duration_seconds=1_500,
            final_phase="warmup",
            avg_intensity="calm",
        )
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
        assert payload["max_duration_seconds"] == 420
        assert payload["subscription_tier"] == "premium"
        assert payload["voice_access_tier"] == "premium"
        assert payload["daily_session_limit"] == 8
        assert payload["session_update_json"] == "{\"type\":\"session.update\"}"
        assert captured["language"] == "no"
        assert captured["summary_context"]["coach_score"] == 91
        assert captured["history_context"]["total_workouts"] == 3
        assert captured["history_context"]["total_duration_minutes"] == 95
        assert captured["history_context"]["workouts_last_7_days"] == 2
        assert captured["history_context"]["workouts_last_30_days"] == 2
        assert captured["history_context"]["recent_workouts"][0]["duration_minutes"] == 30
        assert set(captured["history_context"].keys()) == {
            "total_workouts",
            "total_duration_minutes",
            "workouts_last_7_days",
            "workouts_last_30_days",
            "recent_workouts",
        }
        assert set(captured["history_context"]["recent_workouts"][0].keys()) == {
            "date",
            "duration_minutes",
            "final_phase",
            "avg_intensity",
            "language",
        }
        assert captured["max_duration_seconds"] == 420
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_sanitizes_history_context_before_bootstrap(monkeypatch):
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    captured = {}

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        captured["summary_context"] = dict(summary_context)
        captured["history_context"] = dict(history_context or {})
        _ = (language, user_name, max_duration_seconds, logger)
        return {
            "voice_session_id": "voice_history_sanitized",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_history",
            "client_secret_expires_at": 1_763_000_000,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": 120,
            "summary_context": dict(summary_context),
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-sanitize", tier="premium")
        user_id = user.id
        _create_workout_history(
            user_id,
            days_ago=0,
            duration_seconds=-120,
            final_phase=" cooldown\\nwith extra internal detail that should not keep going forever ",
            avg_intensity=" very intense   but controlled and much longer than expected for the prompt layer ",
            language="norwegian-bookmal-long",
        )
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.post(
            "/voice/session",
            json={"summary_context": {"coach_score": 88, "coach_score_summary_line": "Great\\njob"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        recent = captured["history_context"]["recent_workouts"][0]
        assert recent["duration_minutes"] == 0
        assert "\n" not in recent["final_phase"]
        assert len(recent["final_phase"]) <= 40
        assert len(recent["avg_intensity"]) <= 40
        assert len(recent["language"]) <= 8
        assert "\n" not in captured["summary_context"]["coach_score_summary_line"]
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_voice_session_free_daily_limit_returns_429(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", 2, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", 120, raising=False)

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        _ = (summary_context, history_context, language, user_name, max_duration_seconds, logger)
        return {
            "voice_session_id": f"voice_free_limit_{uuid.uuid4().hex[:6]}",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_limit",
            "client_secret_expires_at": 1_763_000_500,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": 120,
            "summary_context": {"coach_score": 88},
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-free-limit", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(2):
            response = client.post("/voice/session", json={"summary_context": {"coach_score": 88}}, headers=headers)
            assert response.status_code == 200

        blocked = client.post("/voice/session", json={"summary_context": {"coach_score": 88}}, headers=headers)
        assert blocked.status_code == 429
        payload = blocked.get_json()
        assert payload["error"] == "Rate limit exceeded"
        assert blocked.headers.get("Retry-After")
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


def test_voice_session_premium_daily_limit_is_higher(monkeypatch):
    _disable_rate_limit_bypass(monkeypatch)
    _clear_rate_limit_counters()
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY", 3, raising=False)
    monkeypatch.setattr(main.config, "XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS", 420, raising=False)

    def _fake_bootstrap(
        *,
        summary_context,
        history_context=None,
        language,
        user_name=None,
        max_duration_seconds=None,
        logger=None,
    ):
        _ = (summary_context, history_context, language, user_name, max_duration_seconds, logger)
        return {
            "voice_session_id": f"voice_premium_limit_{uuid.uuid4().hex[:6]}",
            "websocket_url": "wss://api.x.ai/v1/realtime",
            "client_secret": "ek_premium_limit",
            "client_secret_expires_at": 1_763_000_900,
            "voice": "Rex",
            "model": "grok-3-mini",
            "region": "us-east-1",
            "max_duration_seconds": 420,
            "summary_context": {"coach_score": 92},
            "session_update": {"type": "session.update"},
            "session_update_json": "{\"type\":\"session.update\"}",
        }

    monkeypatch.setattr(main, "bootstrap_post_workout_voice_session", _fake_bootstrap)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("voice-premium-limit", tier="premium")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(3):
            response = client.post("/voice/session", json={"summary_context": {"coach_score": 92}}, headers=headers)
            assert response.status_code == 200

        blocked = client.post("/voice/session", json={"summary_context": {"coach_score": 92}}, headers=headers)
        assert blocked.status_code == 429
        payload = blocked.get_json()
        assert payload["error"] == "Rate limit exceeded"
        assert blocked.headers.get("Retry-After")
    finally:
        with main.app.app_context():
            _delete_user(user_id)
        _clear_rate_limit_counters()


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


def test_auth_me_includes_profile_name_from_user_profile(monkeypatch):
    monkeypatch.setattr(main.config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60, raising=False)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("auth-profile-name", tier="free")
        user_id = user.id
        user.display_name = f"random-{uuid.uuid4().hex[:8]}"
        db.session.add(UserProfile(user_id=user.id, name="Marius Gaarder"))
        db.session.commit()
        token = auth.create_jwt(user.id, user.email)

    try:
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        payload = response.get_json()["user"]
        assert payload["display_name"].startswith("random-")
        assert payload["profile_name"] == "Marius Gaarder"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_auth_me_uses_configured_premium_override(monkeypatch):
    monkeypatch.setattr(main.config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60, raising=False)
    monkeypatch.setattr(main.config, "PREMIUM_TIER_OVERRIDE_EMAILS", ["override@example.com"], raising=False)
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("override-tier", tier="free")
        user_id = user.id
        user.email = "override@example.com"
        db.session.commit()
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
