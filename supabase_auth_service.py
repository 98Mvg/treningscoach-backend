"""Supabase Auth bridge for the existing Flask auth API.

This keeps Coachi's public `/auth/email/*` routes stable while allowing the
backend to delegate email OTP and password-reset delivery to Supabase Auth when
project credentials are configured.
"""

from __future__ import annotations

from typing import Any

import requests

import config

try:  # pragma: no cover - optional dependency guard
    from supabase import Client, create_client
except Exception:  # pragma: no cover - local env may not have package installed yet
    Client = None
    create_client = None


def _logger(logger: Any):
    return logger if logger is not None else _NoOpLogger()


class _NoOpLogger:
    def info(self, *_args, **_kwargs) -> None:
        return None

    def warning(self, *_args, **_kwargs) -> None:
        return None

    def error(self, *_args, **_kwargs) -> None:
        return None


def is_supabase_auth_configured() -> bool:
    return bool(getattr(config, "SUPABASE_AUTH_ENABLED", False))


def get_supabase_client() -> Client | None:
    if not is_supabase_auth_configured() or create_client is None:
        return None
    service_role = str(getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "") or "").strip()
    anon_key = str(getattr(config, "SUPABASE_ANON_KEY", "") or "").strip()
    publishable_key = str(getattr(config, "SUPABASE_PUBLISHABLE_KEY", "") or "").strip()
    api_key = service_role or anon_key or publishable_key
    if not api_key:
        return None
    return create_client(config.SUPABASE_URL, api_key)


def _auth_headers() -> dict[str, str]:
    api_key = (
        str(getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "") or "").strip()
        or str(getattr(config, "SUPABASE_ANON_KEY", "") or "").strip()
        or str(getattr(config, "SUPABASE_PUBLISHABLE_KEY", "") or "").strip()
    )
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def request_email_otp(
    email: str,
    *,
    should_create_user: bool = True,
    logger: Any = None,
) -> tuple[bool, str | None]:
    if not is_supabase_auth_configured():
        return False, "supabase_auth_not_configured"

    payload: dict[str, Any] = {
        "email": email,
        "create_user": bool(should_create_user),
    }
    redirect_to = str(getattr(config, "SUPABASE_AUTH_REDIRECT_URL", "") or "").strip()
    if redirect_to:
        payload["options"] = {"email_redirect_to": redirect_to}

    try:
        response = requests.post(
            f"{config.SUPABASE_URL}/auth/v1/otp",
            headers=_auth_headers(),
            json=payload,
            timeout=8,
        )
    except Exception as exc:
        _logger(logger).warning("SUPABASE_AUTH_OTP_REQUEST_FAILED email=%s error=%s", email, exc)
        return False, "supabase_auth_request_failed"

    if response.status_code >= 400:
        _logger(logger).warning(
            "SUPABASE_AUTH_OTP_REQUEST_REJECTED email=%s status=%s body=%s",
            email,
            response.status_code,
            response.text[:240],
        )
        return False, "supabase_auth_request_rejected"

    _logger(logger).info("SUPABASE_AUTH_OTP_REQUEST_OK email=%s", email)
    return True, None


def verify_email_otp(
    email: str,
    token: str,
    *,
    logger: Any = None,
) -> tuple[bool, dict[str, Any] | None, str | None]:
    if not is_supabase_auth_configured():
        return False, None, "supabase_auth_not_configured"

    payload = {
        "email": email,
        "token": token,
        "type": "email",
    }
    try:
        response = requests.post(
            f"{config.SUPABASE_URL}/auth/v1/verify",
            headers=_auth_headers(),
            json=payload,
            timeout=8,
        )
    except Exception as exc:
        _logger(logger).warning("SUPABASE_AUTH_VERIFY_FAILED email=%s error=%s", email, exc)
        return False, None, "supabase_auth_verify_failed"

    if response.status_code >= 400:
        _logger(logger).warning(
            "SUPABASE_AUTH_VERIFY_REJECTED email=%s status=%s body=%s",
            email,
            response.status_code,
            response.text[:240],
        )
        return False, None, "supabase_auth_verify_rejected"

    try:
        payload_json = response.json()
    except ValueError:
        payload_json = {}

    _logger(logger).info("SUPABASE_AUTH_VERIFY_OK email=%s", email)
    return True, payload_json if isinstance(payload_json, dict) else {}, None


def send_password_reset_email(
    email: str,
    *,
    logger: Any = None,
) -> tuple[bool, str | None]:
    if not is_supabase_auth_configured():
        return False, "supabase_auth_not_configured"

    payload: dict[str, Any] = {"email": email}
    redirect_to = str(getattr(config, "SUPABASE_AUTH_REDIRECT_URL", "") or "").strip()
    if redirect_to:
        payload["redirect_to"] = redirect_to

    try:
        response = requests.post(
            f"{config.SUPABASE_URL}/auth/v1/recover",
            headers=_auth_headers(),
            json=payload,
            timeout=8,
        )
    except Exception as exc:
        _logger(logger).warning("SUPABASE_PASSWORD_RESET_FAILED email=%s error=%s", email, exc)
        return False, "supabase_password_reset_failed"

    if response.status_code >= 400:
        _logger(logger).warning(
            "SUPABASE_PASSWORD_RESET_REJECTED email=%s status=%s body=%s",
            email,
            response.status_code,
            response.text[:240],
        )
        return False, "supabase_password_reset_rejected"

    _logger(logger).info("SUPABASE_PASSWORD_RESET_OK email=%s", email)
    return True, None
