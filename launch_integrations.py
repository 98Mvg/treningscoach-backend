"""Launch-safe external integration helpers.

These integrations are best-effort and env-gated:
- Sentry for backend error capture
- PostHog for landing analytics forwarding

They must never block the primary request path when unconfigured or failing.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

import config
from email_sender import active_email_provider, is_email_configured, is_resend_configured

try:  # pragma: no cover - import guard depends on local env
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except Exception as exc:  # pragma: no cover - import guard depends on local env
    sentry_sdk = None
    FlaskIntegration = None
    _SENTRY_IMPORT_ERROR = exc
else:  # pragma: no cover - trivial branch
    _SENTRY_IMPORT_ERROR = None


_SENTRY_RUNTIME_STATUS: dict[str, Any] = {
    "enabled": bool(getattr(config, "SENTRY_ENABLED", False)),
    "configured": bool(str(getattr(config, "SENTRY_DSN", "") or "").strip()),
    "active": False,
    "reason": "not_initialized",
}


def _log(logger: Any) -> Any:
    return logger if logger is not None else logging.getLogger(__name__)


def init_sentry(*, logger: Any = None) -> dict[str, Any]:
    """Initialize Sentry when explicitly enabled and configured."""
    global _SENTRY_RUNTIME_STATUS

    log = _log(logger)
    enabled = bool(getattr(config, "SENTRY_ENABLED", False))
    dsn = str(getattr(config, "SENTRY_DSN", "") or "").strip()
    environment = str(getattr(config, "SENTRY_ENVIRONMENT", "development") or "development").strip()
    release = str(getattr(config, "SENTRY_RELEASE", getattr(config, "APP_VERSION", "unknown")) or "unknown").strip()
    traces_sample_rate = float(getattr(config, "SENTRY_TRACES_SAMPLE_RATE", 0.0) or 0.0)

    if not enabled:
        _SENTRY_RUNTIME_STATUS = {
            "enabled": False,
            "configured": bool(dsn),
            "active": False,
            "reason": "disabled",
        }
        return dict(_SENTRY_RUNTIME_STATUS)

    if not dsn:
        _SENTRY_RUNTIME_STATUS = {
            "enabled": True,
            "configured": False,
            "active": False,
            "reason": "dsn_missing",
        }
        log.warning("SENTRY_INIT_SKIPPED reason=dsn_missing")
        return dict(_SENTRY_RUNTIME_STATUS)

    if sentry_sdk is None or FlaskIntegration is None:
        _SENTRY_RUNTIME_STATUS = {
            "enabled": True,
            "configured": True,
            "active": False,
            "reason": "sdk_missing",
        }
        log.warning("SENTRY_INIT_SKIPPED reason=sdk_missing error=%s", _SENTRY_IMPORT_ERROR)
        return dict(_SENTRY_RUNTIME_STATUS)

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[FlaskIntegration()],
        traces_sample_rate=max(0.0, min(1.0, traces_sample_rate)),
    )
    _SENTRY_RUNTIME_STATUS = {
        "enabled": True,
        "configured": True,
        "active": True,
        "reason": "ok",
    }
    log.info("SENTRY_INIT_OK environment=%s release=%s", environment, release)
    return dict(_SENTRY_RUNTIME_STATUS)


def sentry_status() -> dict[str, Any]:
    return dict(_SENTRY_RUNTIME_STATUS)


def capture_posthog_event(
    event: str,
    *,
    metadata: dict[str, Any] | None = None,
    distinct_id: str | None = None,
    logger: Any = None,
) -> bool:
    """Best-effort PostHog forwarding for launch analytics events."""
    enabled = bool(getattr(config, "POSTHOG_ENABLED", False))
    api_key = str(getattr(config, "POSTHOG_API_KEY", "") or "").strip()
    host = str(getattr(config, "POSTHOG_HOST", "https://us.i.posthog.com") or "").strip().rstrip("/")
    if not enabled or not api_key or not host:
        return False

    props = dict(metadata) if isinstance(metadata, dict) else {}
    resolved_distinct_id = str(distinct_id or props.get("distinct_id") or "anonymous").strip() or "anonymous"
    props.setdefault("source", "backend")
    props.setdefault("$lib", "coachi-backend")

    try:
        response = requests.post(
            f"{host}/capture/",
            json={
                "api_key": api_key,
                "event": str(event or "").strip(),
                "distinct_id": resolved_distinct_id,
                "properties": props,
            },
            timeout=3,
        )
        if response.status_code >= 400:
            _log(logger).warning(
                "POSTHOG_CAPTURE_FAILED status=%s event=%s body=%s",
                response.status_code,
                event,
                response.text[:200],
            )
            return False
        return True
    except Exception as exc:
        _log(logger).warning("POSTHOG_CAPTURE_FAILED event=%s error=%s", event, exc)
        return False


def integration_status_snapshot() -> dict[str, dict[str, Any]]:
    """Expose launch integration readiness without leaking secrets."""
    posthog_enabled = bool(getattr(config, "POSTHOG_ENABLED", False))
    posthog_configured = bool(str(getattr(config, "POSTHOG_API_KEY", "") or "").strip())

    return {
        "posthog": {
            "enabled": posthog_enabled,
            "configured": posthog_configured,
            "active": bool(posthog_enabled and posthog_configured),
        },
        "sentry": sentry_status(),
        "email": {
            "enabled": bool(is_email_configured()),
            "provider": active_email_provider(),
            "resend_configured": bool(is_resend_configured()),
        },
    }
