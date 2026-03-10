"""
Auth API routes for Treningscoach
Launch-safe auth keeps Apple available and leaves other providers disabled by default
"""

import logging
import time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from database import db, User, UserSettings
from email_sender import send_account_welcome_email
from auth import (
    create_jwt,
    enforce_rate_limit,
    get_request_refresh_token_user_id,
    require_auth,
    rate_limit,
    issue_auth_tokens,
    rotate_refresh_token,
    revoke_refresh_family,
    AppleTokenVerificationError,
    verify_apple_token,
    verify_google_token,
    verify_facebook_token,
    verify_vipps_token,
)
import config

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


_apple_auth_metrics = {
    "success": 0,
    "failure": 0,
    "reasons": {},
}


_PROVIDER_FLAG_BY_NAME = {
    "apple": "APPLE_AUTH_ENABLED",
    "google": "GOOGLE_AUTH_ENABLED",
    "facebook": "FACEBOOK_AUTH_ENABLED",
    "vipps": "VIPPS_AUTH_ENABLED",
}


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _record_apple_auth_metric(*, success: bool, reason: str, started_at: float) -> None:
    """
    Lightweight in-process telemetry for Apple sign-in outcomes.
    """
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    if success:
        _apple_auth_metrics["success"] += 1
    else:
        _apple_auth_metrics["failure"] += 1

    reason_counts = _apple_auth_metrics["reasons"]
    reason_counts[reason] = int(reason_counts.get(reason, 0)) + 1

    logger.info(
        "AUTH_APPLE_METRIC success=%s reason=%s latency_ms=%s success_total=%s failure_total=%s reason_total=%s",
        success,
        reason,
        latency_ms,
        _apple_auth_metrics["success"],
        _apple_auth_metrics["failure"],
        reason_counts[reason],
    )


def _provider_enabled(provider: str) -> bool:
    flag_name = _PROVIDER_FLAG_BY_NAME.get(provider, "")
    if not flag_name:
        return False
    return bool(getattr(config, flag_name, False))


def _provider_unavailable_response(provider: str):
    logger.info("Auth provider disabled for launch surface: %s", provider)
    return jsonify({"error": "Provider unavailable", "error_code": "provider_disabled"}), 404


# ============================================
# HELPER: Find or create user
# ============================================

def find_or_create_user(provider: str, provider_info: dict) -> User:
    """
    Find existing user by provider ID or create new one.

    Args:
        provider: "apple", "google", "facebook", or "vipps"
        provider_info: Dict from verify_*_token()

    Returns:
        User instance
    """
    # Try to find by provider + provider_id
    user = User.query.filter_by(
        auth_provider=provider,
        auth_provider_id=provider_info["provider_id"]
    ).first()

    if user:
        # Update name/avatar if changed
        user.display_name = provider_info.get("display_name") or user.display_name
        user.avatar_url = provider_info.get("avatar_url") or user.avatar_url
        user.updated_at = _utcnow_naive()
        db.session.commit()
        logger.info(f"Existing user signed in: {user.email} ({provider})")
        return user

    # Try to find by email (user might have signed up with different provider)
    email = provider_info.get("email", "")
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link this provider to existing account
            logger.info(f"Linking {provider} to existing user: {email}")
            user.updated_at = _utcnow_naive()
            db.session.commit()
            return user

    # Create new user
    user = User(
        email=email or f"{provider}_{provider_info['provider_id']}@treningscoach.app",
        display_name=provider_info.get("display_name", ""),
        avatar_url=provider_info.get("avatar_url", ""),
        auth_provider=provider,
        auth_provider_id=provider_info["provider_id"],
        language="en",
        training_level="intermediate"
    )
    db.session.add(user)
    db.session.flush()  # Ensure user.id exists before creating dependent rows.

    # Create default settings
    settings = UserSettings(user_id=user.id)
    db.session.add(settings)

    db.session.commit()
    logger.info(f"New user created: {user.email} ({provider})")
    send_account_welcome_email(
        user.email,
        display_name=user.display_name,
        language=user.language,
        provider=provider,
        logger=logger,
    )
    return user


def _find_existing_user(provider: str, provider_info: dict) -> User | None:
    user = User.query.filter_by(
        auth_provider=provider,
        auth_provider_id=provider_info["provider_id"],
    ).first()
    if user is not None:
        return user

    email = str(provider_info.get("email") or "").strip()
    if email:
        return User.query.filter_by(email=email).first()
    return None


def _enforce_register_rate_limit_if_new_user(provider: str, provider_info: dict):
    if _find_existing_user(provider, provider_info) is not None:
        return None

    limited = enforce_rate_limit(
        getattr(config, "AUTH_REGISTER_RATE_LIMIT_PER_10_MINUTES", 3),
        10 * 60,
        key_prefix="auth.register",
        scope="ip",
    )
    if limited is not None:
        return limited

    return enforce_rate_limit(
        getattr(config, "AUTH_REGISTER_RATE_LIMIT_PER_DAY", 10),
        24 * 3600,
        key_prefix="auth.register",
        scope="ip",
    )


# ============================================
# AUTH ENDPOINTS
# ============================================

@auth_bp.route("/apple", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_HOUR", 20),
    window_seconds=3600,
    key_prefix="auth.login",
    scope="ip",
)
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", 5),
    window_seconds=60,
    key_prefix="auth.login",
    scope="ip",
)
def auth_apple():
    """
    Authenticate with Apple Sign-In.

    Request body:
    {
        "identity_token": "eyJhbGciOi...",
        "authorization_code": "optional",
        "email": "optional@first.login",
        "full_name": "Optional Name"
    }

    Returns:
    {
        "token": "jwt_token",
        "user": { ... }
    }
    """
    started_at = time.perf_counter()
    if not _provider_enabled("apple"):
        reason = "apple_provider_disabled"
        _record_apple_auth_metric(success=False, reason=reason, started_at=started_at)
        return _provider_unavailable_response("apple")
    try:
        data = request.get_json()
        if not data or "identity_token" not in data:
            reason = "apple_missing_identity_token"
            _record_apple_auth_metric(success=False, reason=reason, started_at=started_at)
            return jsonify({
                "error": "Missing identity_token",
                "error_code": reason,
            }), 400

        provider_info = verify_apple_token(
            data["identity_token"],
            email=data.get("email"),
            full_name=data.get("full_name"),
        )
        register_limited = _enforce_register_rate_limit_if_new_user("apple", provider_info)
        if register_limited is not None:
            _record_apple_auth_metric(success=False, reason="apple_register_rate_limited", started_at=started_at)
            return register_limited
        user = find_or_create_user("apple", provider_info)
        token_bundle = issue_auth_tokens(user.id, user.email)
        _record_apple_auth_metric(success=True, reason="ok", started_at=started_at)

        return jsonify({
            "token": token_bundle["access_token"],  # backward-compatible key
            "access_token": token_bundle["access_token"],
            "refresh_token": token_bundle["refresh_token"],
            "token_type": token_bundle["token_type"],
            "expires_in": token_bundle["expires_in"],
            "refresh_expires_in": token_bundle["refresh_expires_in"],
            "user": user.to_dict()
        }), 200

    except AppleTokenVerificationError as e:
        logger.warning("Apple auth failed: %s (%s)", e.message, e.reason)
        _record_apple_auth_metric(success=False, reason=e.reason, started_at=started_at)
        return jsonify({"error": e.message, "error_code": e.reason}), 401
    except ValueError as e:
        reason = "apple_token_invalid"
        logger.warning("Apple auth failed: %s", e)
        _record_apple_auth_metric(success=False, reason=reason, started_at=started_at)
        return jsonify({"error": str(e), "error_code": reason}), 401
    except Exception as e:
        logger.error(f"Apple auth error: {e}", exc_info=True)
        reason = "apple_auth_internal_error"
        _record_apple_auth_metric(success=False, reason=reason, started_at=started_at)
        return jsonify({
            "error": "Authentication failed",
            "error_code": reason,
        }), 500


@auth_bp.route("/google", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_HOUR", 20),
    window_seconds=3600,
    key_prefix="auth.login",
    scope="ip",
)
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", 5),
    window_seconds=60,
    key_prefix="auth.login",
    scope="ip",
)
def auth_google():
    """
    Authenticate with Google Sign-In.

    Request body:
    {
        "id_token": "eyJhbGciOi..."
    }

    Returns:
    {
        "token": "jwt_token",
        "user": { ... }
    }
    """
    if not _provider_enabled("google"):
        return _provider_unavailable_response("google")
    try:
        data = request.get_json()
        if not data or "id_token" not in data:
            return jsonify({"error": "Missing id_token"}), 400

        # Verify with Google
        provider_info = verify_google_token(data["id_token"])
        register_limited = _enforce_register_rate_limit_if_new_user("google", provider_info)
        if register_limited is not None:
            return register_limited

        # Find or create user
        user = find_or_create_user("google", provider_info)

        token_bundle = issue_auth_tokens(user.id, user.email)

        return jsonify({
            "token": token_bundle["access_token"],  # backward-compatible key
            "access_token": token_bundle["access_token"],
            "refresh_token": token_bundle["refresh_token"],
            "token_type": token_bundle["token_type"],
            "expires_in": token_bundle["expires_in"],
            "refresh_expires_in": token_bundle["refresh_expires_in"],
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Google auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Google auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/facebook", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_HOUR", 20),
    window_seconds=3600,
    key_prefix="auth.login",
    scope="ip",
)
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", 5),
    window_seconds=60,
    key_prefix="auth.login",
    scope="ip",
)
def auth_facebook():
    """
    Authenticate with Facebook Login.

    Request body:
    {
        "access_token": "EAAGm0..."
    }

    Returns:
    {
        "token": "jwt_token",
        "user": { ... }
    }
    """
    if not _provider_enabled("facebook"):
        return _provider_unavailable_response("facebook")
    try:
        data = request.get_json()
        if not data or "access_token" not in data:
            return jsonify({"error": "Missing access_token"}), 400

        # Verify with Facebook
        provider_info = verify_facebook_token(data["access_token"])
        register_limited = _enforce_register_rate_limit_if_new_user("facebook", provider_info)
        if register_limited is not None:
            return register_limited

        # Find or create user
        user = find_or_create_user("facebook", provider_info)

        token_bundle = issue_auth_tokens(user.id, user.email)

        return jsonify({
            "token": token_bundle["access_token"],  # backward-compatible key
            "access_token": token_bundle["access_token"],
            "refresh_token": token_bundle["refresh_token"],
            "token_type": token_bundle["token_type"],
            "expires_in": token_bundle["expires_in"],
            "refresh_expires_in": token_bundle["refresh_expires_in"],
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Facebook auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Facebook auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/vipps", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_HOUR", 20),
    window_seconds=3600,
    key_prefix="auth.login",
    scope="ip",
)
@rate_limit(
    limit=getattr(config, "AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", 5),
    window_seconds=60,
    key_prefix="auth.login",
    scope="ip",
)
def auth_vipps():
    """
    Authenticate with Vipps Login.

    Request body:
    {
        "access_token": "eyJhbGciOi..."
    }

    Returns:
    {
        "token": "jwt_token",
        "user": { ... }
    }
    """
    if not _provider_enabled("vipps"):
        return _provider_unavailable_response("vipps")
    try:
        data = request.get_json()
        if not data or "access_token" not in data:
            return jsonify({"error": "Missing access_token"}), 400

        # Verify with Vipps
        provider_info = verify_vipps_token(data["access_token"])
        register_limited = _enforce_register_rate_limit_if_new_user("vipps", provider_info)
        if register_limited is not None:
            return register_limited

        # Find or create user
        user = find_or_create_user("vipps", provider_info)

        # Default Norwegian language for Vipps users
        if user.language == "en":
            user.language = "no"
            db.session.commit()

        token_bundle = issue_auth_tokens(user.id, user.email)

        return jsonify({
            "token": token_bundle["access_token"],  # backward-compatible key
            "access_token": token_bundle["access_token"],
            "refresh_token": token_bundle["refresh_token"],
            "token_type": token_bundle["token_type"],
            "expires_in": token_bundle["expires_in"],
            "refresh_expires_in": token_bundle["refresh_expires_in"],
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Vipps auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Vipps auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


# ============================================
# TOKEN REFRESH / LOGOUT
# ============================================

@auth_bp.route("/refresh", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_REFRESH_RATE_LIMIT_PER_MINUTE", 30),
    window_seconds=60,
    key_prefix="auth.refresh",
    scope="user",
    key_func=get_request_refresh_token_user_id,
)
def refresh_tokens():
    """
    Rotate refresh token and issue a new access/refresh pair.
    """
    data = request.get_json(silent=True) or {}
    refresh_token = str(data.get("refresh_token") or "").strip()
    if not refresh_token:
        return jsonify({"error": "Missing refresh_token"}), 400

    try:
        from database import User

        new_refresh_token, _family_id, user_id = rotate_refresh_token(refresh_token)
        user = db.session.get(User, user_id)
        access_token = create_jwt(user_id, user.email if user is not None else None)
        return jsonify(
            {
                "token": access_token,
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": int(getattr(config, "JWT_ACCESS_TOKEN_MAX_DAYS", 7) * 24 * 3600),
                "refresh_expires_in": int(getattr(config, "JWT_REFRESH_TOKEN_MAX_DAYS", 7) * 24 * 3600),
            }
        ), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401
    except Exception as exc:
        logger.error("Refresh token rotation failed: %s", exc, exc_info=True)
        return jsonify({"error": "Token refresh failed"}), 500


@auth_bp.route("/logout", methods=["POST"])
@rate_limit(
    limit=getattr(config, "AUTH_REFRESH_RATE_LIMIT_PER_MINUTE", 30),
    window_seconds=60,
    key_prefix="auth.logout",
    scope="user",
    key_func=get_request_refresh_token_user_id,
)
def logout():
    """
    Revoke current refresh-token family.
    """
    data = request.get_json(silent=True) or {}
    refresh_token = str(data.get("refresh_token") or "").strip()
    if not refresh_token:
        return jsonify({"error": "Missing refresh_token"}), 400
    revoked = revoke_refresh_family(refresh_token)
    return jsonify({"success": True, "revoked_tokens": revoked}), 200


# ============================================
# USER PROFILE ENDPOINTS
# ============================================

@auth_bp.route("/me", methods=["GET"])
@rate_limit(
    limit=getattr(config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60),
    window_seconds=60,
    key_prefix="auth.me",
    scope="user",
)
@require_auth
def get_profile():
    """
    Get current user profile.

    Requires: Authorization: Bearer <token>

    Returns:
    {
        "user": { id, email, display_name, language, training_level, ... }
    }
    """
    user = db.session.get(User, g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["PUT"])
@rate_limit(
    limit=getattr(config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60),
    window_seconds=60,
    key_prefix="auth.me",
    scope="user",
)
@require_auth
def update_profile():
    """
    Update current user profile.

    Requires: Authorization: Bearer <token>

    Request body (all fields optional):
    {
        "display_name": "Marius",
        "language": "no",
        "training_level": "advanced",
        "preferred_persona": "toxic_mode"
    }

    Returns:
    {
        "user": { ... updated ... }
    }
    """
    user = db.session.get(User, g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update allowed fields
    if "display_name" in data:
        user.display_name = data["display_name"]

    if "language" in data:
        if data["language"] in ("en", "no"):
            user.language = data["language"]
        else:
            return jsonify({"error": "Language must be 'en' or 'no'"}), 400

    if "training_level" in data:
        if data["training_level"] in ("beginner", "intermediate", "advanced"):
            user.training_level = data["training_level"]
        else:
            return jsonify({"error": "Training level must be 'beginner', 'intermediate', or 'advanced'"}), 400

    if "preferred_persona" in data:
        user.preferred_persona = data["preferred_persona"]

    user.updated_at = _utcnow_naive()
    db.session.commit()

    logger.info(f"Profile updated: {user.email}")
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["DELETE"])
@rate_limit(
    limit=getattr(config, "AUTH_ME_RATE_LIMIT_PER_MINUTE", 60),
    window_seconds=60,
    key_prefix="auth.me",
    scope="user",
)
@require_auth
def delete_account():
    """
    Delete current user account and all associated data.

    Requires: Authorization: Bearer <token>
    """
    user = db.session.get(User, g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    email = user.email
    db.session.delete(user)
    db.session.commit()

    logger.info(f"Account deleted: {email}")
    return jsonify({"success": True, "message": "Account deleted"}), 200
