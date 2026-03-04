import os
import sys

import jwt
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth


class _FakeSigningKey:
    key = "fake-signing-key"


class _FakeJWKClient:
    def __init__(self, _: str):
        pass

    def get_signing_key_from_jwt(self, _: str):
        return _FakeSigningKey()


def _mock_jwks(monkeypatch):
    monkeypatch.setattr(auth.jwt, "PyJWKClient", _FakeJWKClient)


def test_verify_apple_token_success_with_mocked_jwks(monkeypatch):
    _mock_jwks(monkeypatch)

    decoded_payload = {
        "sub": "apple-user-123",
        "email": "apple@example.com",
    }
    monkeypatch.setattr(auth.jwt, "decode", lambda *args, **kwargs: decoded_payload)

    result = auth.verify_apple_token("identity-token", full_name="Marius")

    assert result["provider_id"] == "apple-user-123"
    assert result["email"] == "apple@example.com"
    assert result["display_name"] == "Marius"


def test_verify_apple_token_maps_expired_reason(monkeypatch):
    _mock_jwks(monkeypatch)

    def _raise_expired(*args, **kwargs):
        raise jwt.ExpiredSignatureError("expired")

    monkeypatch.setattr(auth.jwt, "decode", _raise_expired)

    with pytest.raises(auth.AppleTokenVerificationError) as exc:
        auth.verify_apple_token("identity-token")

    assert exc.value.reason == "apple_token_expired"
    assert "expired" in exc.value.message.lower()


def test_verify_apple_token_maps_audience_reason(monkeypatch):
    _mock_jwks(monkeypatch)

    def _raise_audience(*args, **kwargs):
        raise jwt.InvalidAudienceError("bad aud")

    monkeypatch.setattr(auth.jwt, "decode", _raise_audience)

    with pytest.raises(auth.AppleTokenVerificationError) as exc:
        auth.verify_apple_token("identity-token")

    assert exc.value.reason == "apple_audience_mismatch"
    assert "verify apple identity" in exc.value.message.lower()


def test_verify_apple_token_rejects_missing_sub(monkeypatch):
    _mock_jwks(monkeypatch)

    monkeypatch.setattr(auth.jwt, "decode", lambda *args, **kwargs: {"email": "x@example.com"})

    with pytest.raises(auth.AppleTokenVerificationError) as exc:
        auth.verify_apple_token("identity-token")

    assert exc.value.reason == "apple_token_invalid"

