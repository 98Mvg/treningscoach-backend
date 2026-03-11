import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth_routes
import main
from database import EmailAuthCode, RefreshToken, User, UserSettings, db


def _cleanup_user_and_codes(email: str) -> None:
    with main.app.app_context():
        EmailAuthCode.query.filter_by(email=email).delete()

        user = User.query.filter_by(email=email).first()
        if user is not None:
            refresh_tokens = RefreshToken.query.filter_by(user_id=user.id).all()
            for token in refresh_tokens:
                db.session.delete(token)
            settings = UserSettings.query.filter_by(user_id=user.id).first()
            if settings is not None:
                db.session.delete(settings)
            db.session.delete(user)

        db.session.commit()


def test_auth_email_request_code_requires_valid_email():
    client = main.app.test_client()
    response = client.post("/auth/email/request-code", json={"email": "invalid"})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error_code"] == "email_invalid"


def test_auth_email_request_code_and_verify_success(monkeypatch):
    email = f"email-user-{uuid.uuid4().hex[:10]}@example.com"
    sent_codes: list[str] = []

    monkeypatch.setattr(auth_routes, "_generate_email_auth_code", lambda: "123456")

    def _fake_send_sign_in_code_email(target_email, *, code, language="en", logger=None):
        assert target_email == email
        sent_codes.append(code)
        return True

    monkeypatch.setattr(auth_routes, "send_sign_in_code_email", _fake_send_sign_in_code_email)

    client = main.app.test_client()

    request_code = client.post("/auth/email/request-code", json={"email": email, "language": "en"})
    assert request_code.status_code == 200
    request_payload = request_code.get_json()
    assert request_payload["success"] is True
    assert request_payload["code_sent"] is True
    assert request_payload["expires_in"] == 600
    assert sent_codes == ["123456"]

    verify = client.post("/auth/email/verify", json={"email": email, "code": "123456"})
    assert verify.status_code == 200
    payload = verify.get_json()
    assert isinstance(payload.get("token"), str) and payload["token"]
    assert isinstance(payload.get("access_token"), str) and payload["access_token"]
    assert isinstance(payload.get("refresh_token"), str) and payload["refresh_token"]
    assert payload["user"]["email"] == email

    with main.app.app_context():
        code = EmailAuthCode.query.filter_by(email=email).order_by(EmailAuthCode.created_at.desc()).first()
        assert code is not None
        assert code.used_at is not None

    _cleanup_user_and_codes(email)


def test_auth_email_verify_rejects_wrong_code(monkeypatch):
    email = f"email-user-{uuid.uuid4().hex[:10]}@example.com"
    monkeypatch.setattr(auth_routes, "_generate_email_auth_code", lambda: "123456")
    monkeypatch.setattr(auth_routes, "send_sign_in_code_email", lambda *args, **kwargs: True)
    client = main.app.test_client()

    request_code = client.post("/auth/email/request-code", json={"email": email, "language": "en"})
    assert request_code.status_code == 200

    verify = client.post("/auth/email/verify", json={"email": email, "code": "654321"})
    assert verify.status_code == 401
    payload = verify.get_json()
    assert payload["error_code"] == "email_code_mismatch"

    _cleanup_user_and_codes(email)
