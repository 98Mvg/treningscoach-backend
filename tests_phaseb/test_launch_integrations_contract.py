import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import email_sender
import launch_integrations
import main
import web_routes

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _FakeResponse:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text


def test_posthog_capture_posts_to_configured_host(monkeypatch):
    calls = {}

    def _fake_post(url, json=None, timeout=None):
        calls["url"] = url
        calls["json"] = json
        calls["timeout"] = timeout
        return _FakeResponse(status_code=200)

    monkeypatch.setattr(config, "POSTHOG_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "POSTHOG_API_KEY", "ph_test_key", raising=False)
    monkeypatch.setattr(config, "POSTHOG_HOST", "https://posthog.example", raising=False)
    monkeypatch.setattr(launch_integrations.requests, "post", _fake_post)

    assert launch_integrations.capture_posthog_event(
        "waitlist_signup",
        metadata={"language": "no"},
        distinct_id="web:abc123",
    ) is True
    assert calls["url"] == "https://posthog.example/capture/"
    assert calls["json"]["api_key"] == "ph_test_key"
    assert calls["json"]["event"] == "waitlist_signup"
    assert calls["json"]["distinct_id"] == "web:abc123"
    assert calls["json"]["properties"]["language"] == "no"


def test_analytics_endpoint_forwards_events_to_posthog(monkeypatch):
    client = main.app.test_client()
    calls = []

    def _fake_capture(event, *, metadata=None, distinct_id=None, logger=None):
        calls.append(
            {
                "event": event,
                "metadata": metadata,
                "distinct_id": distinct_id,
            }
        )
        return True

    monkeypatch.setattr(web_routes, "capture_posthog_event", _fake_capture)

    response = client.post(
        "/analytics/event",
        json={"event": "app_store_click", "metadata": {"language": "no", "source": "test"}},
        environ_overrides={"REMOTE_ADDR": "10.0.0.15"},
    )

    assert response.status_code == 200
    assert calls == [
        {
            "event": "app_store_click",
            "metadata": {"language": "no", "source": "test"},
            "distinct_id": calls[0]["distinct_id"],
        }
    ]
    assert calls[0]["distinct_id"].startswith("web:")


def test_resend_delivery_is_used_when_configured(monkeypatch):
    calls = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        calls["timeout"] = timeout
        return _FakeResponse(status_code=200)

    for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("EMAIL_SENDING_ENABLED", "true")
    monkeypatch.setenv("EMAIL_PROVIDER", "resend")
    monkeypatch.setenv("EMAIL_FROM", "noreply@coachi.app")
    monkeypatch.setenv("EMAIL_REPLY_TO", "support@coachi.app")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setattr(email_sender.requests, "post", _fake_post)

    assert email_sender.send_waitlist_welcome_email("runner@example.com", language="en", source="website") is True
    assert calls["url"] == "https://api.resend.com/emails"
    assert calls["headers"]["Authorization"] == "Bearer re_test_key"
    assert calls["json"]["from"] == "noreply@coachi.app"
    assert calls["json"]["to"] == ["runner@example.com"]
    assert calls["json"]["reply_to"] == "support@coachi.app"


def test_sentry_init_activates_when_sdk_is_available(monkeypatch):
    calls = {}

    class _FakeSDK:
        def init(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(config, "SENTRY_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "SENTRY_DSN", "https://example@sentry.invalid/123", raising=False)
    monkeypatch.setattr(config, "SENTRY_ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(config, "SENTRY_RELEASE", "3.0.0", raising=False)
    monkeypatch.setattr(config, "SENTRY_TRACES_SAMPLE_RATE", 0.25, raising=False)
    monkeypatch.setattr(launch_integrations, "sentry_sdk", _FakeSDK(), raising=False)
    monkeypatch.setattr(launch_integrations, "FlaskIntegration", lambda: "flask", raising=False)

    status = launch_integrations.init_sentry()

    assert status["active"] is True
    assert calls["dsn"] == "https://example@sentry.invalid/123"
    assert calls["environment"] == "production"
    assert calls["release"] == "3.0.0"
    assert calls["traces_sample_rate"] == 0.25
    assert calls["integrations"] == ["flask"]


def test_env_examples_expose_launch_integration_keys():
    expected = [
        "POSTHOG_ENABLED=",
        "POSTHOG_API_KEY=",
        "POSTHOG_HOST=",
        "SENTRY_ENABLED=",
        "SENTRY_DSN=",
        "SENTRY_ENVIRONMENT=",
        "SENTRY_RELEASE=",
        "SENTRY_TRACES_SAMPLE_RATE=",
        "EMAIL_PROVIDER=",
        "RESEND_API_KEY=",
        "RESEND_API_URL=",
        "SUPABASE_URL=",
        "SUPABASE_ANON_KEY=",
        "SUPABASE_PUBLISHABLE_KEY=",
        "SUPABASE_SERVICE_ROLE_KEY=",
        "SUPABASE_AUTH_REDIRECT_URL=",
    ]

    for path in [os.path.join(REPO_ROOT, ".env.example"), os.path.join(REPO_ROOT, "backend", ".env.example")]:
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        for key in expected:
            assert key in content


def test_requirements_include_sentry_sdk():
    with open(os.path.join(REPO_ROOT, "requirements.txt"), encoding="utf-8") as handle:
        content = handle.read()
    assert "sentry-sdk" in content
    assert "supabase" in content
    assert "psycopg" in content
