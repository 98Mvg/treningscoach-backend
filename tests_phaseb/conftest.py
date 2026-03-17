import os
import sys
import uuid

import pytest
from flask.testing import FlaskClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import main


_MOBILE_AUTH_PATHS = {"/coach/continuous", "/coach/talk"}


def _request_path(args, kwargs) -> str | None:
    if args:
        first = args[0]
        if isinstance(first, str):
            return first.split("?", 1)[0]
    path = kwargs.get("path")
    if isinstance(path, str):
        return path.split("?", 1)[0]
    return None


def _default_mobile_auth_headers(existing_headers, authorization_header: str) -> dict:
    headers = dict(existing_headers or {})
    if "Authorization" in headers:
        return headers
    headers["Authorization"] = authorization_header
    return headers


@pytest.fixture(autouse=True)
def _inject_mobile_auth_for_authenticated_routes(monkeypatch):
    original_open = FlaskClient.open
    user_id = f"pytest_mobile_user_{uuid.uuid4().hex}"
    token = auth.create_jwt(user_id, f"{user_id}@example.com")
    authorization_header = f"Bearer {token}"

    def _open(self, *args, **kwargs):
        path = _request_path(args, kwargs)
        if path in _MOBILE_AUTH_PATHS:
            kwargs["headers"] = _default_mobile_auth_headers(kwargs.get("headers"), authorization_header)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(FlaskClient, "open", _open)


@pytest.fixture(autouse=True)
def _accept_synthetic_test_audio(monkeypatch):
    monkeypatch.setattr(main, "_validate_audio_upload_signature", lambda _file: True)
