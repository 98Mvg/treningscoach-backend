import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth
import main
from database import (
    AppStoreServerNotification,
    AppStoreSubscriptionState,
    RefreshToken,
    User,
    UserProfile,
    UserSettings,
    UserSubscription,
    WorkoutHistory,
    db,
)


def _future_millis(days: int = 30) -> int:
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp() * 1000)


def _now_millis() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _create_user(email_prefix: str, *, tier: str = "free") -> User:
    suffix = uuid.uuid4().hex[:10]
    user = User(
        email=f"{email_prefix}-{suffix}@example.com",
        display_name=f"{email_prefix}-{suffix}",
        auth_provider="apple",
        auth_provider_id=f"{email_prefix}-{suffix}",
        language="en",
        training_level="intermediate",
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(UserSubscription(user_id=user.id, tier=tier))
    db.session.commit()
    return user


def _delete_user(user_id: str) -> None:
    RefreshToken.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    WorkoutHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserProfile.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserSettings.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    UserSubscription.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    AppStoreServerNotification.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    AppStoreSubscriptionState.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    user = db.session.get(User, user_id)
    if user is not None:
        db.session.delete(user)
    db.session.commit()


def test_subscription_validate_accepts_signed_transaction_and_persists_state(monkeypatch):
    client = main.app.test_client()
    transaction_payload = {
        "appAccountToken": None,
        "bundleId": "com.coachi.app",
        "environment": "Sandbox",
        "expiresDate": _future_millis(20),
        "inAppOwnershipType": "PURCHASED",
        "originalTransactionId": "orig_123",
        "productId": "app.coachi.premium.monthly",
        "purchaseDate": _now_millis(),
        "signedDate": _now_millis(),
        "transactionId": "tx_123",
    }
    monkeypatch.setattr(main.config, "APP_STORE_BUNDLE_IDS", ["com.coachi.app"], raising=False)
    monkeypatch.setattr(main, "decode_app_store_signed_payload", lambda *_args, **_kwargs: dict(transaction_payload))

    with main.app.app_context():
        user = _create_user("app-store-validate", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    try:
        transaction_payload["appAccountToken"] = user_id
        response = client.post(
            "/subscription/validate",
            json={
                "platform": "ios",
                "transaction_id": "tx_123",
                "signed_transaction_info": "signed_tx_info",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["tier"] == "premium"
        assert payload["status"] == "active"
        assert payload["transaction_id"] == "tx_123"

        with main.app.app_context():
            state = db.session.get(AppStoreSubscriptionState, "orig_123")
            assert state is not None
            assert state.user_id == user_id
            assert state.status == "active"
            assert state.product_id == "app.coachi.premium.monthly"
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            assert subscription is not None
            assert subscription.tier == "premium"
            assert auth.resolve_user_subscription_tier(user_id) == "premium"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_subscription_validate_rejects_mismatched_app_account_token(monkeypatch):
    client = main.app.test_client()
    monkeypatch.setattr(main.config, "APP_STORE_BUNDLE_IDS", ["com.coachi.app"], raising=False)

    with main.app.app_context():
        user = _create_user("app-store-mismatch", tier="free")
        user_id = user.id
        token = auth.create_jwt(user.id, user.email)

    transaction_payload = {
        "appAccountToken": str(uuid.uuid4()),
        "bundleId": "com.coachi.app",
        "environment": "Sandbox",
        "expiresDate": _future_millis(20),
        "originalTransactionId": "orig_mismatch",
        "productId": "app.coachi.premium.monthly",
        "purchaseDate": _now_millis(),
        "signedDate": _now_millis(),
        "transactionId": "tx_mismatch",
    }
    monkeypatch.setattr(main, "decode_app_store_signed_payload", lambda *_args, **_kwargs: dict(transaction_payload))

    try:
        response = client.post(
            "/subscription/validate",
            json={"signed_transaction_info": "signed_tx_info"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert response.get_json()["error"] == "app_account_token_mismatch"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_app_store_webhook_dedupes_notifications_and_updates_state(monkeypatch):
    client = main.app.test_client()
    monkeypatch.setattr(main.config, "APP_STORE_SERVER_NOTIFICATIONS_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "APP_STORE_BUNDLE_IDS", ["com.coachi.app"], raising=False)

    with main.app.app_context():
        user = _create_user("app-store-webhook", tier="free")
        user_id = user.id

    notification_payload = {
        "notificationUUID": "notif_123",
        "notificationType": "DID_RENEW",
        "subtype": "",
        "signedDate": _now_millis(),
        "data": {"signedTransactionInfo": "signed_tx_info"},
    }
    transaction_payload = {
        "appAccountToken": user_id,
        "bundleId": "com.coachi.app",
        "environment": "Production",
        "expiresDate": _future_millis(30),
        "originalTransactionId": "orig_webhook",
        "productId": "app.coachi.premium.yearly",
        "purchaseDate": _now_millis(),
        "signedDate": _now_millis(),
        "transactionId": "tx_webhook",
    }

    def _fake_decode(signed_payload, **_kwargs):
        if signed_payload == "signed_notification":
            return dict(notification_payload)
        if signed_payload == "signed_tx_info":
            return dict(transaction_payload)
        raise AssertionError(f"Unexpected signed payload: {signed_payload}")

    monkeypatch.setattr(main, "decode_app_store_signed_payload", _fake_decode)

    try:
        response = client.post("/webhooks/app-store", json={"signedPayload": "signed_notification"})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert payload["processed"] is True
        assert payload["tier"] == "premium"

        duplicate = client.post("/webhooks/app-store", json={"signedPayload": "signed_notification"})
        assert duplicate.status_code == 200
        assert duplicate.get_json()["deduped"] is True

        with main.app.app_context():
            state = db.session.get(AppStoreSubscriptionState, "orig_webhook")
            assert state is not None
            assert state.user_id == user_id
            assert state.status == "active"
            assert state.product_id == "app.coachi.premium.yearly"
            notification = db.session.get(AppStoreServerNotification, "notif_123")
            assert notification is not None
            assert notification.user_id == user_id
            assert notification.notification_type == "DID_RENEW"
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            assert subscription is not None
            assert subscription.tier == "premium"
    finally:
        with main.app.app_context():
            _delete_user(user_id)


def test_any_active_app_store_chain_keeps_user_premium(monkeypatch):
    monkeypatch.setattr(main.config, "APP_STORE_BUNDLE_IDS", ["com.coachi.app"], raising=False)

    with main.app.app_context():
        user = _create_user("app-store-multi-chain", tier="free")
        user_id = user.id

        db.session.add(
            AppStoreSubscriptionState(
                original_transaction_id="orig_active_chain",
                user_id=user_id,
                transaction_id="tx_active_chain",
                product_id="app.coachi.premium.monthly",
                bundle_id="com.coachi.app",
                environment="Production",
                status="active",
                purchase_date=datetime.now(timezone.utc).replace(tzinfo=None),
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=20),
                source="test",
            )
        )
        db.session.add(
            AppStoreSubscriptionState(
                original_transaction_id="orig_expired_chain",
                user_id=user_id,
                transaction_id="tx_expired_chain",
                product_id="app.coachi.premium.monthly",
                bundle_id="com.coachi.app",
                environment="Production",
                status="expired",
                purchase_date=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60),
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1),
                source="test",
            )
        )
        db.session.commit()

        resolved_tier = main._update_user_subscription_tier_record(user_id=user_id, status="expired")
        subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        refreshed_user = db.session.get(User, user_id)

        assert resolved_tier == "premium"
        assert subscription is not None
        assert subscription.tier == "premium"
        assert auth.resolve_user_subscription_tier(user_id) == "premium"
        assert refreshed_user is not None
        assert refreshed_user.to_dict()["subscription_tier"] == "premium"

    with main.app.app_context():
        _delete_user(user_id)


def test_mobile_analytics_accepts_guest_events_with_anonymous_id(monkeypatch):
    client = main.app.test_client()
    captured = {}

    def _fake_capture(event, *, metadata=None, distinct_id=None, logger=None):
        captured["event"] = event
        captured["metadata"] = dict(metadata or {})
        captured["distinct_id"] = distinct_id
        _ = logger
        return True

    monkeypatch.setattr(main, "capture_posthog_event", _fake_capture)

    response = client.post(
        "/analytics/mobile",
        json={
            "event": "app_opened",
            "anonymous_id": "anon_launch_12345",
            "metadata": {"surface": "cold_start"},
        },
    )
    assert response.status_code == 200
    assert captured["event"] == "app_opened"
    assert captured["distinct_id"] == "mobile:anon_launch_12345"
    assert captured["metadata"]["subscription_tier"] == "guest"

    missing = client.post("/analytics/mobile", json={"event": "app_opened"})
    assert missing.status_code == 400
    assert missing.get_json()["error_code"] == "anonymous_id_required"
