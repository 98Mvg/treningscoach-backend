import importlib
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import main
from auth_routes import find_or_create_user
from database import WorkoutHistory, User, UserSettings, db


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
    assert secret_file.read_text(encoding="utf-8").strip() == first


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
        },
    )
    assert response.status_code == 201

    payload = response.get_json()
    workout = payload["workout"]
    assert workout["user_id"] == user_id
    assert workout["final_phase"] == "cooldown"
    assert workout["avg_intensity"] == "moderate"
    assert workout["persona_used"] == "toxic_mode"
    assert workout["language"] == "no"

    with main.app.app_context():
        _delete_user_and_workouts(user_id)
