import importlib
import io
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import auth_routes
import main
from auth_routes import find_or_create_user
from database import CoachingScore, WorkoutHistory, User, UserSettings, db


def _create_user(email_prefix: str) -> User:
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
    db.session.commit()
    return user


def _delete_user_and_workouts(user_id: str) -> None:
    CoachingScore.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    workouts = WorkoutHistory.query.filter_by(user_id=user_id).all()
    for workout in workouts:
        db.session.delete(workout)
    user = db.session.get(User, user_id)
    if user is not None:
        db.session.delete(user)
    db.session.commit()


def test_jwt_secret_uses_runtime_file_when_env_missing(monkeypatch, tmp_path):
    secret_file = tmp_path / "jwt_secret.txt"

    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("JWT_SECRET_FILE", str(secret_file))

    reloaded = importlib.reload(auth)
    assert reloaded.JWT_SECRET
    assert reloaded.JWT_SECRET != reloaded.DEFAULT_INSECURE_JWT_SECRET
    first = reloaded.JWT_SECRET

    reloaded_again = importlib.reload(auth)
    assert reloaded_again.JWT_SECRET == first
    assert secret_file.exists()
    secret_payload = json.loads(secret_file.read_text(encoding="utf-8").strip())
    assert secret_payload["secret"] == first
    assert isinstance(secret_payload.get("created_at"), str) and secret_payload["created_at"]


def test_find_or_create_user_creates_settings_for_real_user_id():
    provider_id = f"provider-{uuid.uuid4().hex[:12]}"
    provider_info = {
        "provider_id": provider_id,
        "email": f"new-user-{uuid.uuid4().hex[:10]}@example.com",
        "display_name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
    }

    with main.app.app_context():
        user = find_or_create_user("google", provider_info)
        settings = UserSettings.query.filter_by(user_id=user.id).first()

        assert user.id is not None
        assert settings is not None
        assert settings.user_id == user.id

        db.session.delete(settings)
        db.session.delete(user)
        db.session.commit()


def test_find_or_create_user_sends_welcome_email_only_for_new_user(monkeypatch):
    calls = []
    provider_id = f"provider-{uuid.uuid4().hex[:12]}"
    provider_info = {
        "provider_id": provider_id,
        "email": f"new-user-{uuid.uuid4().hex[:10]}@example.com",
        "display_name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
    }

    def _fake_send_account_welcome_email(email, *, display_name="", language="en", provider="apple", logger=None):
        calls.append(
            {
                "email": email,
                "display_name": display_name,
                "language": language,
                "provider": provider,
            }
        )
        return True

    monkeypatch.setattr(auth_routes, "send_account_welcome_email", _fake_send_account_welcome_email)

    with main.app.app_context():
        user = find_or_create_user("google", provider_info)
        assert calls == [
            {
                "email": user.email,
                "display_name": "Test User",
                "language": "en",
                "provider": "google",
            }
        ]

        same_user = find_or_create_user("google", provider_info)
        assert same_user.id == user.id
        assert len(calls) == 1

        settings = UserSettings.query.filter_by(user_id=user.id).first()
        if settings is not None:
            db.session.delete(settings)
        db.session.delete(user)
        db.session.commit()


def test_auth_profile_avatar_upload_and_delete_cleanup():
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("avatar-user")
        token = auth.create_jwt(user.id, user.email)
        user_id = user.id

    upload = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        data={"avatar": (io.BytesIO(b"fake-jpeg-data"), "avatar.jpg")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    payload = upload.get_json()
    avatar_url = payload["user"]["avatar_url"]
    assert avatar_url.startswith("/auth/avatar/avatar_")

    fetched = client.get(avatar_url)
    assert fetched.status_code == 200
    assert fetched.data == b"fake-jpeg-data"

    deleted = client.delete("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert deleted.status_code == 200

    missing = client.get(avatar_url)
    assert missing.status_code == 404

    with main.app.app_context():
        _delete_user_and_workouts(user_id)


def test_workouts_require_auth_and_scope_results_to_current_user():
    client = main.app.test_client()

    with main.app.app_context():
        user_a = _create_user("workout-user-a")
        user_b = _create_user("workout-user-b")

        db.session.add(
            WorkoutHistory(
                user_id=user_a.id,
                duration_seconds=300,
                final_phase="intense",
                avg_intensity="moderate",
                persona_used="personal_trainer",
                language="en",
            )
        )
        db.session.add(
            WorkoutHistory(
                user_id=user_b.id,
                duration_seconds=420,
                final_phase="cooldown",
                avg_intensity="calm",
                persona_used="toxic_mode",
                language="no",
            )
        )
        db.session.commit()

        user_a_id = user_a.id
        user_b_id = user_b.id
        token_a = auth.create_jwt(user_a.id, user_a.email)

    unauthorized = client.get("/workouts")
    assert unauthorized.status_code == 401

    authorized = client.get("/workouts", headers={"Authorization": f"Bearer {token_a}"})
    assert authorized.status_code == 200
    payload = authorized.get_json()
    assert isinstance(payload.get("workouts"), list)
    assert payload["workouts"]
    assert all(row["user_id"] == user_a_id for row in payload["workouts"])
    assert all(row["user_id"] != user_b_id for row in payload["workouts"])

    with main.app.app_context():
        _delete_user_and_workouts(user_a_id)
        _delete_user_and_workouts(user_b_id)


def test_save_workout_accepts_mobile_field_aliases():
    client = main.app.test_client()

    with main.app.app_context():
        user = _create_user("workout-alias-user")
        token = auth.create_jwt(user.id, user.email)
        user_id = user.id

    unauthorized = client.post(
        "/workouts",
        json={"duration_seconds": 60, "phase": "warmup", "intensity": "moderate"},
    )
    assert unauthorized.status_code == 401

    response = client.post(
        "/workouts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "duration_seconds": 615,
            "phase": "cooldown",
            "intensity": "moderate",
            "persona": "toxic_mode",
            "language": "no",
            "coach_score": 82,
            "hr_score": 79,
            "breath_score": 76,
            "duration_score": 88,
        },
    )
    assert response.status_code == 201

    payload = response.get_json()
    workout = payload["workout"]
    coaching_score = payload["coaching_score"]
    assert workout["user_id"] == user_id
    assert workout["final_phase"] == "cooldown"
    assert workout["avg_intensity"] == "moderate"
    assert workout["persona_used"] == "toxic_mode"
    assert workout["language"] == "no"
    assert coaching_score["score"] == 82
    assert coaching_score["hr_score"] == 79
    assert coaching_score["breath_score"] == 76
    assert coaching_score["duration_score"] == 88

    with main.app.app_context():
        persisted = CoachingScore.query.filter_by(user_id=user_id).first()
        assert persisted is not None
        assert persisted.score == 82
        assert persisted.hr_score == 79

    with main.app.app_context():
        _delete_user_and_workouts(user_id)


def test_guest_preview_header_allows_coach_continuous_without_bearer_token(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(
        main.breath_analyzer,
        "analyze",
        lambda _path: {
            "intensity": "moderate",
            "tempo": 16.0,
            "volume": 35.0,
            "breath_regularity": 0.55,
            "inhale_exhale_ratio": 0.7,
            "signal_quality": 0.8,
            "respiratory_rate": 16.0,
        },
    )
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))

    session_id = main.session_manager.create_session(user_id="guest_preview_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        headers={
            "Authorization": "",
            "X-Coachi-Guest-Preview": "1",
        },
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "12",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "should_speak" in payload
    assert payload.get("reason")


def test_guest_preview_header_does_not_open_workout_talk_without_auth():
    client = main.app.test_client()

    response = client.post(
        "/coach/talk",
        headers={
            "Authorization": "",
            "X-Coachi-Guest-Preview": "1",
        },
        json={"message": "How am I doing?"},
    )

    assert response.status_code == 401
    assert response.get_json()["error_code"] == "authentication_required"
