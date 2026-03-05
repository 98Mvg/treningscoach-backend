import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import auth_routes
from auth import AppleTokenVerificationError
from database import RefreshToken, User, UserSettings, db


def _cleanup_user_by_email(email: str) -> None:
    with main.app.app_context():
        user = User.query.filter_by(email=email).first()
        if user is None:
            return
        refresh_tokens = RefreshToken.query.filter_by(user_id=user.id).all()
        for token in refresh_tokens:
            db.session.delete(token)
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
    assert isinstance(payload.get("access_token"), str) and payload["access_token"]
    assert isinstance(payload.get("refresh_token"), str) and payload["refresh_token"]
    assert payload.get("token_type") == "bearer"
    assert isinstance(payload.get("expires_in"), int) and payload["expires_in"] > 0
    assert isinstance(payload.get("refresh_expires_in"), int) and payload["refresh_expires_in"] > 0
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


def test_auth_refresh_rotates_token_family(monkeypatch):
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

    login = client.post(
        "/auth/apple",
        json={
            "identity_token": "fake-identity-token",
            "email": email,
            "full_name": "Marius",
        },
    )
    assert login.status_code == 200
    login_payload = login.get_json()
    first_refresh = login_payload.get("refresh_token")
    assert first_refresh

    refresh = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert refresh.status_code == 200
    refresh_payload = refresh.get_json()
    second_refresh = refresh_payload.get("refresh_token")
    assert second_refresh and second_refresh != first_refresh

    # Old refresh token should be revoked after rotation.
    stale = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert stale.status_code == 401

    logout = client.post("/auth/logout", json={"refresh_token": second_refresh})
    assert logout.status_code == 200
    logout_payload = logout.get_json()
    assert logout_payload.get("success") is True
    assert isinstance(logout_payload.get("revoked_tokens"), int)

    _cleanup_user_by_email(email)
