"""Coachi email boundary for auth and subscription notifications."""

from __future__ import annotations

from typing import Any

from email_sender import send_subscription_receipt_email
from supabase_auth_service import request_email_otp, send_password_reset_email


def sendLoginEmail(email: str, *, logger: Any = None) -> tuple[bool, str | None]:
    return request_email_otp(email, logger=logger)


def sendPasswordReset(email: str, *, logger: Any = None) -> tuple[bool, str | None]:
    return send_password_reset_email(email, logger=logger)


def sendSubscriptionReceipt(
    email: str,
    *,
    plan: str,
    status: str,
    language: str = "en",
    logger: Any = None,
) -> bool:
    return send_subscription_receipt_email(
        email,
        plan=plan,
        status=status,
        language=language,
        logger=logger,
    )


def send_login_email(email: str, *, logger: Any = None) -> tuple[bool, str | None]:
    return sendLoginEmail(email, logger=logger)


def send_password_reset(email: str, *, logger: Any = None) -> tuple[bool, str | None]:
    return sendPasswordReset(email, logger=logger)


def send_subscription_receipt(
    email: str,
    *,
    plan: str,
    status: str,
    language: str = "en",
    logger: Any = None,
) -> bool:
    return sendSubscriptionReceipt(
        email,
        plan=plan,
        status=status,
        language=language,
        logger=logger,
    )
