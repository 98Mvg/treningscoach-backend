"""Helpers for App Store subscription payload decoding and state derivation.

These helpers keep the main runtime on the single existing Flask path while
isolating the JWS parsing details needed for subscription sync and webhooks.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


ACTIVE_APP_STORE_STATUSES = {"active", "trial", "grace_period"}


class AppStorePayloadError(ValueError):
    """Raised when an App Store signed payload is malformed or unsupported."""


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean_string(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _millis_to_naive(value: Any) -> datetime | None:
    if value in (None, "", 0):
        return None
    try:
        millis = int(value)
    except (TypeError, ValueError):
        return None
    if millis <= 0:
        return None
    return datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc).replace(tzinfo=None)


def decode_app_store_signed_payload(
    signed_payload: str,
    *,
    verify_signature: bool = True,
    trusted_root_sha256s: set[str] | None = None,
) -> dict[str, Any]:
    token = str(signed_payload or "").strip()
    if token.count(".") != 2:
        raise AppStorePayloadError("invalid_signed_payload")

    if not verify_signature:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["ES256"],
        )
        if not isinstance(payload, dict):
            raise AppStorePayloadError("invalid_signed_payload_body")
        return payload

    header = jwt.get_unverified_header(token)
    algorithm = str(header.get("alg") or "").strip()
    if algorithm != "ES256":
        raise AppStorePayloadError("unsupported_signed_payload_algorithm")

    x5c = header.get("x5c")
    if not isinstance(x5c, list) or not x5c:
        raise AppStorePayloadError("missing_certificate_chain")

    try:
        certificates = _decode_certificate_chain(x5c)
    except Exception as exc:  # pragma: no cover - cryptography specifics vary by version
        raise AppStorePayloadError("invalid_certificate_chain") from exc

    _validate_certificate_chain(
        certificates,
        trusted_root_sha256s=trusted_root_sha256s,
    )

    certificate = certificates[0]

    try:
        payload = jwt.decode(
            token,
            key=certificate.public_key(),
            algorithms=["ES256"],
            options={"verify_aud": False, "verify_iss": False},
        )
    except jwt.InvalidTokenError as exc:
        raise AppStorePayloadError("signature_verification_failed") from exc

    if not isinstance(payload, dict):
        raise AppStorePayloadError("invalid_signed_payload_body")
    return payload


def _decode_certificate_chain(x5c: list[Any]) -> list[x509.Certificate]:
    certificates: list[x509.Certificate] = []
    for entry in x5c:
        certificate_der = base64.b64decode(str(entry).encode("ascii"))
        certificates.append(x509.load_der_x509_certificate(certificate_der))
    if not certificates:
        raise AppStorePayloadError("missing_certificate_chain")
    return certificates


def _assert_ca_certificate(certificate: x509.Certificate, *, is_root: bool) -> None:
    try:
        constraints = certificate.extensions.get_extension_for_class(x509.BasicConstraints).value
    except x509.ExtensionNotFound as exc:
        raise AppStorePayloadError("missing_basic_constraints") from exc
    if not constraints.ca:
        raise AppStorePayloadError("invalid_certificate_authority")
    if is_root and certificate.subject != certificate.issuer:
        raise AppStorePayloadError("root_certificate_not_self_issued")


def _verify_certificate_signature(
    certificate: x509.Certificate,
    *,
    issuer_certificate: x509.Certificate,
) -> None:
    public_key = issuer_certificate.public_key()
    signature_hash_algorithm = certificate.signature_hash_algorithm
    if signature_hash_algorithm is None:
        raise AppStorePayloadError("unsupported_certificate_algorithm")

    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                padding.PKCS1v15(),
                signature_hash_algorithm,
            )
            return
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                ec.ECDSA(signature_hash_algorithm),
            )
            return
    except Exception as exc:  # pragma: no cover - cryptography error details vary
        raise AppStorePayloadError("invalid_certificate_chain_signature") from exc

    raise AppStorePayloadError("unsupported_certificate_algorithm")


def _validate_certificate_chain(
    certificates: list[x509.Certificate],
    *,
    trusted_root_sha256s: set[str] | None,
) -> None:
    now = datetime.now(timezone.utc)
    normalized_roots = {
        str(fingerprint or "").strip().lower()
        for fingerprint in (trusted_root_sha256s or set())
        if str(fingerprint or "").strip()
    }

    for index, certificate in enumerate(certificates):
        not_valid_before = getattr(certificate, "not_valid_before_utc", None) or certificate.not_valid_before.replace(tzinfo=timezone.utc)
        not_valid_after = getattr(certificate, "not_valid_after_utc", None) or certificate.not_valid_after.replace(tzinfo=timezone.utc)
        if not_valid_before > now or not_valid_after < now:
            raise AppStorePayloadError("certificate_out_of_validity_window")

        is_root = index == len(certificates) - 1
        if is_root:
            _assert_ca_certificate(certificate, is_root=True)
            _verify_certificate_signature(certificate, issuer_certificate=certificate)
            if normalized_roots:
                fingerprint = certificate.fingerprint(hashes.SHA256()).hex().lower()
                if fingerprint not in normalized_roots:
                    raise AppStorePayloadError("untrusted_root_certificate")
            continue

        issuer_certificate = certificates[index + 1]
        if certificate.issuer != issuer_certificate.subject:
            raise AppStorePayloadError("certificate_issuer_mismatch")
        _assert_ca_certificate(issuer_certificate, is_root=(index + 1 == len(certificates) - 1))
        _verify_certificate_signature(certificate, issuer_certificate=issuer_certificate)


def extract_transaction_fields(
    transaction_payload: dict[str, Any],
    *,
    notification_type: str | None = None,
    notification_subtype: str | None = None,
) -> dict[str, Any]:
    expires_at = _millis_to_naive(transaction_payload.get("expiresDate"))
    revocation_date = _millis_to_naive(transaction_payload.get("revocationDate"))
    signed_at = _millis_to_naive(transaction_payload.get("signedDate"))

    return {
        "app_account_token": _clean_string(transaction_payload.get("appAccountToken")),
        "bundle_id": _clean_string(transaction_payload.get("bundleId")),
        "environment": _clean_string(transaction_payload.get("environment")),
        "expires_at": expires_at,
        "notification_subtype": _clean_string(notification_subtype),
        "notification_type": _clean_string(notification_type),
        "original_transaction_id": _clean_string(transaction_payload.get("originalTransactionId")),
        "ownership_type": _clean_string(transaction_payload.get("inAppOwnershipType")),
        "product_id": _clean_string(transaction_payload.get("productId")),
        "purchase_date": _millis_to_naive(transaction_payload.get("purchaseDate")),
        "revocation_date": revocation_date,
        "signed_at": signed_at,
        "status": derive_app_store_status(
            expires_at=expires_at,
            revocation_date=revocation_date,
            notification_type=notification_type,
            notification_subtype=notification_subtype,
        ),
        "transaction_id": _clean_string(transaction_payload.get("transactionId")),
    }


def derive_app_store_status(
    *,
    expires_at: datetime | None,
    revocation_date: datetime | None,
    notification_type: str | None,
    notification_subtype: str | None,
) -> str:
    normalized_type = str(notification_type or "").strip().upper()
    normalized_subtype = str(notification_subtype or "").strip().upper()

    if revocation_date is not None or normalized_type in {"REFUND", "REVOKE"}:
        return "revoked"

    if normalized_type == "EXPIRED":
        return "expired"

    if normalized_type == "DID_FAIL_TO_RENEW":
        if normalized_subtype == "GRACE_PERIOD":
            return "grace_period"
        if expires_at is not None and expires_at > _utcnow_naive():
            return "grace_period"
        return "expired"

    if expires_at is not None and expires_at <= _utcnow_naive():
        return "expired"

    return "active"


def tier_from_status(status: str | None) -> str:
    normalized = str(status or "").strip().lower()
    return "premium" if normalized in ACTIVE_APP_STORE_STATUSES else "free"
