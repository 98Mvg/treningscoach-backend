import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import email_sender


def test_smtp_is_default_provider(monkeypatch):
    monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
    assert email_sender._email_provider() == "smtp"


def test_resend_requires_api_key_and_from_email(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "resend")
    monkeypatch.setenv("EMAIL_SENDING_ENABLED", "true")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("EMAIL_FROM", "AI.Coachi@hotmail.com")

    assert email_sender.is_email_configured() is False


def test_resend_is_configured_when_enabled_and_key_present(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "resend")
    monkeypatch.setenv("EMAIL_SENDING_ENABLED", "true")
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("EMAIL_FROM", "AI.Coachi@hotmail.com")

    assert email_sender.is_email_configured() is True


def test_send_email_skips_cleanly_when_provider_not_configured(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "resend")
    monkeypatch.setenv("EMAIL_SENDING_ENABLED", "false")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)

    assert email_sender._send_email(
        to_email="user@example.com",
        subject="Test",
        body="Body",
    ) is False
