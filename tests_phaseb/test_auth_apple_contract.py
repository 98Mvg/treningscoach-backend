import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import auth_routes
from auth import AppleTokenVerificationError
from database import User, UserSettings, db


def _cleanup_user_by_email(email: str) -> None:
    with main.app.app_context():
        user = User.query.filter_by(email=email).first()
        if user is None:
            return
        settings = UserSettings.query.filter_by(user_id=user.id).first()
        if settings is not None:
            db.session.delete(settings)
        db.session.delete(user)
        db.session.commit()


def test_auth_apple_requires_identity_token():
    client = main.app.test_client()
    response = client.post("/auth/apple", json={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Missing identity_token"
    assert payload["error_code"] == "apple_missing_identity_token"


def test_auth_apple_success(monkeypatch):
    provider_id = f"apple-{uuid.uuid4().hex[:12]}"
    email = f"apple-user-{uuid.uuid4().hex[:10]}@example.com"

    def _fake_verify(identity_token, email=None, full_name=None):
        return {
            "provider_id": provider_id,
            "email": email or "",
            "display_name": full_name or "",
            "avatar_url": "",
        }

    monkeypatch.setattr(auth_routes, "verify_apple_token", _fake_verify)
    client = main.app.test_client()

    response = client.post(
        "/auth/apple",
        json={
            "identity_token": "fake-identity-token",
            "email": email,
            "full_name": "Marius",
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload.get("token"), str) and payload["token"]
    assert payload["user"]["auth_provider"] == "apple"
    assert payload["user"]["email"] == email

    _cleanup_user_by_email(email)


def test_auth_apple_invalid_token_returns_401(monkeypatch):
    def _fake_verify(identity_token, email=None, full_name=None):
        raise AppleTokenVerificationError("apple_token_invalid", "Invalid Apple sign-in token.")

    monkeypatch.setattr(auth_routes, "verify_apple_token", _fake_verify)
    client = main.app.test_client()
    response = client.post("/auth/apple", json={"identity_token": "bad"})
    assert response.status_code == 401
    payload = response.get_json()
    assert payload["error"] == "Invalid Apple sign-in token."
    assert payload["error_code"] == "apple_token_invalid"
