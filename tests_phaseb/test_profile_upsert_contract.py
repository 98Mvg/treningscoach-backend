import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from auth import create_jwt
from database import db, User, UserProfile


def _create_test_user() -> User:
    email = f"profile_upsert_{datetime.now(tz=timezone.utc).timestamp()}@example.com"
    user = User(
        email=email,
        display_name="Profile Upsert",
        auth_provider="google",
        auth_provider_id=email,
        language="en",
        training_level="beginner",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_profile_upsert_requires_auth():
    client = main.app.test_client()
    response = client.post("/profile/upsert", json={"name": "Marius"})
    assert response.status_code == 401


def test_profile_upsert_insert_update_and_stale_ignore():
    client = main.app.test_client()
    with main.app.app_context():
        user = _create_test_user()
        token = create_jwt(user.id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        ts1 = datetime.now(tz=timezone.utc).isoformat()
        insert_response = client.post(
            "/profile/upsert",
            json={
                "name": "Marius",
                "sex": "male",
                "age": 29,
                "height_cm": 182,
                "weight_kg": 79,
                "max_hr_bpm": 192,
                "resting_hr_bpm": 52,
                "profile_updated_at": ts1,
            },
            headers=headers,
        )
        assert insert_response.status_code == 200
        inserted = insert_response.get_json()
        assert inserted["action"] == "insert"
        assert inserted["user_profile"]["name"] == "Marius"

        ts2 = (datetime.now(tz=timezone.utc) + timedelta(seconds=10)).isoformat()
        update_response = client.post(
            "/profile/upsert",
            json={"weight_kg": 80, "profile_updated_at": ts2},
            headers=headers,
        )
        assert update_response.status_code == 200
        updated = update_response.get_json()
        assert updated["action"] == "update"
        assert float(updated["user_profile"]["weight_kg"]) == 80.0

        ts_stale = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
        stale_response = client.post(
            "/profile/upsert",
            json={"weight_kg": 85, "profile_updated_at": ts_stale},
            headers=headers,
        )
        assert stale_response.status_code == 200
        stale = stale_response.get_json()
        assert stale["action"] == "stale_ignored"
        assert stale["stale_ignored"] is True
        assert float(stale["user_profile"]["weight_kg"]) == 80.0

        profile = UserProfile.query.filter_by(user_id=user.id).first()
        db.session.delete(profile)
        db.session.delete(user)
        db.session.commit()


def test_profile_upsert_validates_ranges():
    client = main.app.test_client()
    with main.app.app_context():
        user = _create_test_user()
        token = create_jwt(user.id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/profile/upsert",
            json={"age": 5, "max_hr_bpm": 80, "resting_hr_bpm": 90},
            headers=headers,
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "validation_errors" in payload

        db.session.delete(user)
        db.session.commit()
