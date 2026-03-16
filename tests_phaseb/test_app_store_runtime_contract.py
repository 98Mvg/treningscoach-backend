import base64
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from app_store_runtime import AppStorePayloadError, decode_app_store_signed_payload, derive_app_store_status


def _issue_certificate(
    common_name: str,
    *,
    subject_key,
    issuer_certificate=None,
    issuer_key=None,
    is_ca: bool,
):
    now = datetime.now(timezone.utc)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    issuer_name = issuer_certificate.subject if issuer_certificate is not None else subject
    signer_key = issuer_key or subject_key

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer_name)
        .public_key(subject_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None if is_ca else None), critical=True)
    )
    return builder.sign(private_key=signer_key, algorithm=hashes.SHA256())


def _build_signed_payload():
    root_key = ec.generate_private_key(ec.SECP256R1())
    root_cert = _issue_certificate(
        "Test Root",
        subject_key=root_key,
        is_ca=True,
    )

    intermediate_key = ec.generate_private_key(ec.SECP256R1())
    intermediate_cert = _issue_certificate(
        "Test Intermediate",
        subject_key=intermediate_key,
        issuer_certificate=root_cert,
        issuer_key=root_key,
        is_ca=True,
    )

    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf_cert = _issue_certificate(
        "Test Leaf",
        subject_key=leaf_key,
        issuer_certificate=intermediate_cert,
        issuer_key=intermediate_key,
        is_ca=False,
    )

    payload = {
        "bundleId": "com.coachi.app",
        "environment": "Sandbox",
        "transactionId": "tx_chain_123",
    }
    x5c = [
        base64.b64encode(leaf_cert.public_bytes(serialization.Encoding.DER)).decode("ascii"),
        base64.b64encode(intermediate_cert.public_bytes(serialization.Encoding.DER)).decode("ascii"),
        base64.b64encode(root_cert.public_bytes(serialization.Encoding.DER)).decode("ascii"),
    ]
    token = jwt.encode(payload, leaf_key, algorithm="ES256", headers={"alg": "ES256", "x5c": x5c})
    root_fingerprint = root_cert.fingerprint(hashes.SHA256()).hex().lower()
    return token, root_fingerprint


def test_decode_app_store_signed_payload_accepts_valid_certificate_chain():
    signed_payload, root_fingerprint = _build_signed_payload()

    payload = decode_app_store_signed_payload(
        signed_payload,
        trusted_root_sha256s={root_fingerprint},
    )

    assert payload["bundleId"] == "com.coachi.app"
    assert payload["transactionId"] == "tx_chain_123"


def test_decode_app_store_signed_payload_rejects_untrusted_root():
    signed_payload, _root_fingerprint = _build_signed_payload()

    try:
        decode_app_store_signed_payload(
            signed_payload,
            trusted_root_sha256s={"deadbeef"},
        )
    except AppStorePayloadError as exc:
        assert str(exc) == "untrusted_root_certificate"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected AppStorePayloadError for untrusted root")


def test_derive_app_store_status_preserves_access_for_cancel_until_expiry():
    future = datetime.now(timezone.utc) + timedelta(days=10)
    assert derive_app_store_status(
        expires_at=future.replace(tzinfo=None),
        revocation_date=None,
        notification_type="CANCEL",
        notification_subtype="",
    ) == "active"


def test_derive_app_store_status_revokes_refunds_immediately():
    future = datetime.now(timezone.utc) + timedelta(days=10)
    assert derive_app_store_status(
        expires_at=future.replace(tzinfo=None),
        revocation_date=None,
        notification_type="REFUND",
        notification_subtype="",
    ) == "revoked"
