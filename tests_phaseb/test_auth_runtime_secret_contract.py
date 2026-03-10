import importlib.util
import sys
from pathlib import Path

import pytest


AUTH_PATH = Path("/Users/mariusgaarder/Documents/treningscoach/auth.py")
REPO_ROOT = Path("/Users/mariusgaarder/Documents/treningscoach")


def _load_auth_module(module_name: str):
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, AUTH_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auth_requires_explicit_secret_in_production_like_environment(monkeypatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("JWT_SECRET_FILE", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-123")

    with pytest.raises(RuntimeError, match="JWT_SECRET must be explicitly configured"):
        _load_auth_module("auth_production_secret_guard_test")


def test_auth_allows_runtime_secret_locally(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    secret_file = tmp_path / "jwt_secret.json"
    monkeypatch.setenv("JWT_SECRET_FILE", str(secret_file))

    module = _load_auth_module("auth_local_secret_guard_test")

    assert module.JWT_SECRET
    assert module.JWT_SECRET != module.DEFAULT_INSECURE_JWT_SECRET
    assert secret_file.exists()


def test_env_examples_expose_launch_auth_flags_and_secret_requirements() -> None:
    expected = [
        "JWT_SECRET=",
        "APPLE_AUTH_ENABLED=",
        "GOOGLE_AUTH_ENABLED=",
        "FACEBOOK_AUTH_ENABLED=",
        "VIPPS_AUTH_ENABLED=",
        "APPLE_CLIENT_ID=",
    ]

    for path in [REPO_ROOT / ".env.example", REPO_ROOT / "backend" / ".env.example"]:
        content = path.read_text(encoding="utf-8")
        for key in expected:
            assert key in content
