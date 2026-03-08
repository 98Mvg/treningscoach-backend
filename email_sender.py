"""Small transactional email helpers for launch-safe backend flows.

Emails are optional and env-gated. Signup and auth paths must continue to work
even when email is not configured or sending fails.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any


DEFAULT_SUPPORT_EMAIL = "AI.Coachi@hotmail.com"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _smtp_settings() -> dict[str, Any]:
    return {
        "host": (os.getenv("SMTP_HOST") or "").strip(),
        "port": int((os.getenv("SMTP_PORT") or "587").strip()),
        "username": (os.getenv("SMTP_USERNAME") or "").strip(),
        "password": (os.getenv("SMTP_PASSWORD") or "").strip(),
        "use_tls": not _truthy(os.getenv("SMTP_DISABLE_TLS")),
        "from_email": (os.getenv("EMAIL_FROM") or os.getenv("SUPPORT_EMAIL") or DEFAULT_SUPPORT_EMAIL).strip(),
        "reply_to": (os.getenv("EMAIL_REPLY_TO") or os.getenv("SUPPORT_EMAIL") or DEFAULT_SUPPORT_EMAIL).strip(),
        "enabled": _truthy(os.getenv("EMAIL_SENDING_ENABLED")),
    }


def is_email_configured() -> bool:
    settings = _smtp_settings()
    return bool(
        settings["enabled"]
        and settings["host"]
        and settings["username"]
        and settings["password"]
        and settings["from_email"]
    )


def _logger(logger: Any):
    return logger if logger is not None else _NoOpLogger()


class _NoOpLogger:
    def info(self, *_args, **_kwargs) -> None:
        return None

    def warning(self, *_args, **_kwargs) -> None:
        return None

    def error(self, *_args, **_kwargs) -> None:
        return None


def _send_email(*, to_email: str, subject: str, body: str, logger: Any = None) -> bool:
    log = _logger(logger)
    settings = _smtp_settings()
    if not is_email_configured():
        log.info("EMAIL_SEND_SKIPPED reason=not_configured to=%s", to_email)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings["from_email"]
    message["To"] = to_email
    if settings["reply_to"]:
        message["Reply-To"] = settings["reply_to"]
    message.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings["host"], settings["port"], timeout=5) as server:
            if settings["use_tls"]:
                server.starttls(context=context)
            server.login(settings["username"], settings["password"])
            server.send_message(message)
        log.info("EMAIL_SEND_OK to=%s subject=%s", to_email, subject)
        return True
    except Exception as exc:
        log.warning("EMAIL_SEND_FAILED to=%s subject=%s error=%s", to_email, subject, exc)
        return False


def send_waitlist_welcome_email(
    email: str,
    *,
    language: str = "en",
    source: str = "website",
    logger: Any = None,
) -> bool:
    normalized_language = (language or "en").strip().lower()
    if normalized_language == "no":
        subject = "Takk for interessen i Coachi"
        body = (
            "Hei!\n\n"
            "Takk for at du skrev deg opp for Coachi.\n"
            "Vi sier ifra når vi har nyheter, tidlig tilgang eller viktige oppdateringer.\n\n"
            f"Registreringskilde: {source}\n\n"
            f"Spørsmål? Svar på denne e-posten eller kontakt {os.getenv('SUPPORT_EMAIL') or DEFAULT_SUPPORT_EMAIL}.\n\n"
            "Hilsen\n"
            "Coachi"
        )
    else:
        subject = "Thanks for joining the Coachi list"
        body = (
            "Hi!\n\n"
            "Thanks for signing up for Coachi.\n"
            "We will email you when we have updates, early access, or launch news.\n\n"
            f"Signup source: {source}\n\n"
            f"Questions? Reply to this email or contact {os.getenv('SUPPORT_EMAIL') or DEFAULT_SUPPORT_EMAIL}.\n\n"
            "Regards,\n"
            "Coachi"
        )

    return _send_email(to_email=email, subject=subject, body=body, logger=logger)


def send_account_welcome_email(
    email: str,
    *,
    display_name: str = "",
    language: str = "en",
    provider: str = "apple",
    logger: Any = None,
) -> bool:
    normalized_language = (language or "en").strip().lower()
    greeting_name = display_name.strip()
    if normalized_language == "no":
        greeting = f"Hei {greeting_name}," if greeting_name else "Hei,"
        subject = "Velkommen til Coachi"
        body = (
            f"{greeting}\n\n"
            "Kontoen din er nå klar i Coachi.\n"
            "Du kan bruke appen til å starte økter, lagre historikk og få oppsummeringer over tid.\n\n"
            f"Innloggingsmetode: {provider}\n\n"
            f"Trenger du hjelp? Kontakt {os.getenv('SUPPORT_EMAIL') or DEFAULT_SUPPORT_EMAIL}.\n\n"
            "Hilsen\n"
            "Coachi"
        )
    else:
        greeting = f"Hi {greeting_name}," if greeting_name else "Hi,"
        subject = "Welcome to Coachi"
        body = (
            f"{greeting}\n\n"
            "Your Coachi account is ready.\n"
            "You can now start workouts, save history, and see summaries over time.\n\n"
            f"Sign-in method: {provider}\n\n"
            f"Need help? Contact {os.getenv('SUPPORT_EMAIL') or DEFAULT_SUPPORT_EMAIL}.\n\n"
            "Regards,\n"
            "Coachi"
        )

    return _send_email(to_email=email, subject=subject, body=body, logger=logger)
