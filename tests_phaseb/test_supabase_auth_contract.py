import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth_routes
import main
import supabase_auth_service


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text="ok"):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return dict(self._payload)


def test_supabase_auth_service_targets_supabase_auth_endpoints(monkeypatch):
    calls = []

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _FakeResponse(status_code=200, payload={"user": {"email": json.get("email")}})

    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_URL", "https://coachi.supabase.co", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_ANON_KEY", "anon", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_PUBLISHABLE_KEY", "", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_SERVICE_ROLE_KEY", "service", raising=False)
    monkeypatch.setattr(supabase_auth_service.requests, "post", _fake_post)

    ok_request, _ = supabase_auth_service.request_email_otp("runner@example.com")
    ok_verify, payload, _ = supabase_auth_service.verify_email_otp("runner@example.com", "123456")
    ok_reset, _ = supabase_auth_service.send_password_reset_email("runner@example.com")

    assert ok_request is True
    assert ok_verify is True
    assert payload["user"]["email"] == "runner@example.com"
    assert ok_reset is True
    assert calls[0]["url"] == "https://coachi.supabase.co/auth/v1/otp"
    assert calls[1]["url"] == "https://coachi.supabase.co/auth/v1/verify"
    assert calls[2]["url"] == "https://coachi.supabase.co/auth/v1/recover"


def test_supabase_auth_service_accepts_publishable_key_fallback(monkeypatch):
    calls = []

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers})
        return _FakeResponse(status_code=200)

    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_URL", "https://coachi.supabase.co", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_ANON_KEY", "", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test", raising=False)
    monkeypatch.setattr(supabase_auth_service.config, "SUPABASE_SERVICE_ROLE_KEY", "", raising=False)
    monkeypatch.setattr(supabase_auth_service.requests, "post", _fake_post)

    ok_request, _ = supabase_auth_service.request_email_otp("runner@example.com")

    assert ok_request is True
    assert calls[0]["headers"]["apikey"] == "sb_publishable_test"


def test_auth_email_routes_can_delegate_to_supabase(monkeypatch):
    client = main.app.test_client()
    monkeypatch.setattr(auth_routes.config, "SUPABASE_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(auth_routes, "sendLoginEmail", lambda email, logger=None: (True, None))
    monkeypatch.setattr(auth_routes, "verify_email_otp", lambda email, token, logger=None: (True, {"user": {"email": email}}, None))

    response = client.post("/auth/email/request-code", json={"email": "runner@example.com", "language": "en"})
    assert response.status_code == 200
    assert response.get_json()["code_sent"] is True

    verify = client.post("/auth/email/verify", json={"email": "runner@example.com", "code": "123456"})
    assert verify.status_code == 200
    payload = verify.get_json()
    assert payload["user"]["email"] == "runner@example.com"
    assert payload["access_token"]


def test_password_reset_route_uses_email_service(monkeypatch):
    client = main.app.test_client()
    monkeypatch.setattr(auth_routes, "sendPasswordReset", lambda email, logger=None: (True, None))

    response = client.post("/auth/email/password-reset", json={"email": "runner@example.com"})
    assert response.status_code == 200
    assert response.get_json() == {"success": True, "email_sent": True}
