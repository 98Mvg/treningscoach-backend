"""
Authentication module for Treningscoach
Phase 1 launch auth keeps Apple available by default and enables Google when configured.
Issues JWT tokens for session management
"""

import os
import json
import logging
import secrets
import hashlib
import threading
import time
import uuid
import jwt
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
import config

logger = logging.getLogger(__name__)

# JWT Configuration
DEFAULT_INSECURE_JWT_SECRET = "treningscoach-dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRY_DAYS = max(1, int(getattr(config, "JWT_ACCESS_TOKEN_MAX_DAYS", 7)))
JWT_REFRESH_EXPIRY_DAYS = max(1, int(getattr(config, "JWT_REFRESH_TOKEN_MAX_DAYS", 7)))
JWT_SECRET_MAX_AGE_DAYS = max(1, int(getattr(config, "JWT_SECRET_MAX_AGE_DAYS", 90)))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def _persist_runtime_jwt_secret(secret_path: Path) -> str:
    """
    Load a shared runtime JWT secret from disk, creating one when missing.

    This keeps workers consistent without relying on a predictable default.
    """
    def _build_payload(secret: str) -> dict:
        return {
            "secret": secret,
            "created_at": _utcnow().isoformat(),
        }

    def _extract_valid_secret(raw: str) -> str | None:
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                secret_value = str(payload.get("secret") or "").strip()
                created_at_raw = str(payload.get("created_at") or "").strip()
                if secret_value and created_at_raw:
                    try:
                        created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                        age = _utcnow() - created_at.astimezone(timezone.utc)
                        if age <= timedelta(days=JWT_SECRET_MAX_AGE_DAYS):
                            return secret_value
                        logger.warning(
                            "JWT secret file %s is older than %s days; rotating secret",
                            secret_path,
                            JWT_SECRET_MAX_AGE_DAYS,
                        )
                    except ValueError:
                        logger.warning("JWT secret file %s has invalid created_at; rotating secret", secret_path)
        except json.JSONDecodeError:
            # Backward compatibility: legacy files stored raw secret only.
            legacy_secret = raw.strip()
            if legacy_secret:
                logger.warning("JWT secret file %s uses legacy format; keeping existing secret", secret_path)
                return legacy_secret
        return None

    try:
        existing_raw = secret_path.read_text(encoding="utf-8").strip()
        existing_secret = _extract_valid_secret(existing_raw)
        if existing_secret:
            return existing_secret
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning("Could not read JWT secret file %s: %s", secret_path, exc)

    secret = secrets.token_urlsafe(48)
    payload_json = json.dumps(_build_payload(secret))

    try:
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(secret_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload_json)
    except OSError as exc:
        logger.warning("Could not persist JWT secret file %s: %s", secret_path, exc)

    return secret


def _is_production_like_environment() -> bool:
    env_name = (
        os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or os.getenv("FLASK_ENV")
        or ""
    ).strip().lower()
    if env_name in {"prod", "production"}:
        return True

    if (os.getenv("RENDER_SERVICE_ID") or "").strip():
        return True

    render_flag = (os.getenv("RENDER") or "").strip().lower()
    if render_flag in {"1", "true", "yes", "on"}:
        return True

    return False


def _resolve_jwt_secret() -> str:
    configured = (os.getenv("JWT_SECRET") or "").strip()
    if configured and configured != DEFAULT_INSECURE_JWT_SECRET:
        return configured

    if configured == DEFAULT_INSECURE_JWT_SECRET:
        logger.warning("Ignoring insecure default JWT secret from JWT_SECRET env var")

    if _is_production_like_environment():
        raise RuntimeError(
            "JWT_SECRET must be explicitly configured in production-like environments"
        )

    secret_file = Path((os.getenv("JWT_SECRET_FILE") or "/tmp/treningscoach_jwt_secret").strip())
    resolved = _persist_runtime_jwt_secret(secret_file)
    logger.warning("JWT_SECRET missing; using persisted runtime secret from %s", secret_file)
    return resolved


JWT_SECRET = _resolve_jwt_secret()


class AppleTokenVerificationError(ValueError):
    """Structured Apple token verification error with telemetry-friendly reason code."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


def create_jwt(user_id: str, email: str = None) -> str:
    """
    Create a JWT token for authenticated user.

    Args:
        user_id: The user's database ID
        email: Optional email for token payload

    Returns:
        JWT token string
    """
    now = _utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(days=JWT_ACCESS_EXPIRY_DAYS),
        "typ": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256((raw_token or "").encode("utf-8")).hexdigest()


def issue_refresh_token(user_id: str, *, family_id: str | None = None) -> tuple[str, str]:
    """
    Issue a refresh token and persist only its hash.

    Returns:
        (raw_refresh_token, family_id)
    """
    from database import db, RefreshToken

    token = secrets.token_urlsafe(64)
    token_hash = _hash_token(token)
    resolved_family = family_id or str(uuid.uuid4())
    expires_at = _utcnow() + timedelta(days=JWT_REFRESH_EXPIRY_DAYS)
    record = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=resolved_family,
        expires_at=expires_at.replace(tzinfo=None),
        created_at=_utcnow().replace(tzinfo=None),
        issued_ip=(request.remote_addr or "")[:64],
        issued_user_agent=(request.user_agent.string or "")[:512],
    )
    db.session.add(record)
    db.session.commit()
    return token, resolved_family


def rotate_refresh_token(refresh_token: str) -> tuple[str, str, str]:
    """
    Refresh token rotation: current token is revoked and replaced atomically.

    Returns:
        (new_refresh_token, family_id, user_id)
    """
    from database import db, RefreshToken

    incoming_hash = _hash_token(refresh_token)
    record = RefreshToken.query.filter_by(token_hash=incoming_hash).first()
    now = _utcnow().replace(tzinfo=None)
    if record is None:
        raise ValueError("Invalid refresh token")
    if record.revoked_at is not None:
        raise ValueError("Refresh token revoked")
    if record.expires_at <= now:
        raise ValueError("Refresh token expired")

    new_token, family_id = issue_refresh_token(record.user_id, family_id=record.family_id)
    record.revoked_at = now
    record.last_used_at = now
    record.replaced_by_hash = _hash_token(new_token)
    db.session.commit()
    return new_token, family_id, record.user_id


def revoke_refresh_family(refresh_token: str) -> int:
    """Revoke all refresh tokens in the same token family."""
    from database import db, RefreshToken

    incoming_hash = _hash_token(refresh_token)
    record = RefreshToken.query.filter_by(token_hash=incoming_hash).first()
    if record is None:
        return 0
    now = _utcnow().replace(tzinfo=None)
    updated = RefreshToken.query.filter_by(family_id=record.family_id, revoked_at=None).update(
        {"revoked_at": now},
        synchronize_session=False,
    )
    db.session.commit()
    return int(updated or 0)


def issue_auth_tokens(user_id: str, email: str | None = None) -> dict:
    """Issue access + refresh token pair."""
    access_token = create_jwt(user_id, email)
    refresh_token, family_id = issue_refresh_token(user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(timedelta(days=JWT_ACCESS_EXPIRY_DAYS).total_seconds()),
        "refresh_expires_in": int(timedelta(days=JWT_REFRESH_EXPIRY_DAYS).total_seconds()),
        "refresh_family_id": family_id,
    }


# ============================================
# AUTH DECORATOR
# ============================================

def require_auth(f):
    """
    Flask decorator to require authentication.
    Sets g.current_user_id and g.current_user_email on success.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split("Bearer ")[1]

        try:
            payload = decode_jwt(token)
            g.current_user_id = payload["user_id"]
            g.current_user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def _testing_bypass_enabled(flag_name: str, default: bool = False) -> bool:
    if "PYTEST_CURRENT_TEST" not in os.environ:
        return False
    raw = os.getenv(flag_name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def require_mobile_auth(f):
    """
    Auth guard for mobile API endpoints.

    Enforced by default in runtime, but can be bypassed for tests to avoid
    rewriting broad endpoint contract tests in one security hardening pass.
    """
    strict_mobile_auth = bool(getattr(config, "MOBILE_API_AUTH_REQUIRED", True))
    @wraps(f)
    def decorated(*args, **kwargs):
        if not strict_mobile_auth:
            return f(*args, **kwargs)

        if _testing_bypass_enabled(
            "AUTH_BYPASS_FOR_TESTS",
            bool(getattr(config, "AUTH_BYPASS_FOR_TESTS", False)),
        ):
            g.current_user_id = "test-user"
            g.current_user_email = "test@example.com"
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify(
                {
                    "error": "Missing or invalid Authorization header",
                    "error_code": "authentication_required",
                }
            ), 401

        token = auth_header.split("Bearer ")[1]

        try:
            payload = decode_jwt(token)
            g.current_user_id = payload["user_id"]
            g.current_user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify(
                {
                    "error": "Token expired",
                    "error_code": "authentication_required",
                }
            ), 401
        except jwt.InvalidTokenError:
            return jsonify(
                {
                    "error": "Invalid token",
                    "error_code": "authentication_required",
                }
            ), 401

        return f(*args, **kwargs)

    return decorated


# Compatibility vestige for local tests that referenced the old in-memory store.
_RATE_LIMIT_STORE: dict[str, list[float]] = {}
_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_CLEANUP_LOCK = threading.Lock()
_LAST_RATE_LIMIT_CLEANUP_AT = 0.0


def _request_ip_address() -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded
    return (request.remote_addr or "unknown").strip() or "unknown"


def get_request_auth_user_id() -> str | None:
    current_user_id = getattr(g, "current_user_id", None)
    if current_user_id:
        return str(current_user_id).strip() or None

    auth_header = (request.headers.get("Authorization") or "").strip()
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    try:
        payload = decode_jwt(token)
    except jwt.InvalidTokenError:
        return None

    user_id = str(payload.get("user_id") or "").strip()
    return user_id or None


def get_request_refresh_token_user_id() -> str | None:
    data = request.get_json(silent=True) or {}
    refresh_token = str(data.get("refresh_token") or "").strip()
    if not refresh_token:
        return None

    from database import RefreshToken

    record = RefreshToken.query.filter_by(token_hash=_hash_token(refresh_token)).first()
    if record is None:
        return None
    return str(record.user_id or "").strip() or None


def resolve_user_subscription_tier(user_id: str | None) -> str:
    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        return "free"

    from database import db, User, UserSubscription, user_has_active_app_store_subscription

    if config.user_has_premium_override(user_id=normalized_user_id):
        return "premium"

    user = db.session.get(User, normalized_user_id)
    if user is not None and config.user_has_premium_override(user_id=normalized_user_id, email=user.email):
        return "premium"

    subscription = UserSubscription.query.filter_by(user_id=normalized_user_id).first()
    raw_tier = str(getattr(subscription, "tier", "") or "").strip().lower()
    if raw_tier == "premium":
        return "premium"

    if user_has_active_app_store_subscription(normalized_user_id):
        return "premium"
    return "free"


def _rate_limit_rule_name(prefix: str, window_seconds: int) -> str:
    return f"{prefix}:{max(0, int(window_seconds))}"


def _rate_limit_window_start(now_ts: float, window_seconds: int) -> int:
    normalized_window = int(window_seconds)
    if normalized_window <= 0:
        return 0
    return int(now_ts // normalized_window) * normalized_window


def _rate_limit_retry_after(now_ts: float, window_seconds: int) -> int | None:
    normalized_window = int(window_seconds)
    if normalized_window <= 0:
        return None
    window_start = _rate_limit_window_start(now_ts, normalized_window)
    return max(1, int(window_start + normalized_window - now_ts))


def _cleanup_rate_limit_counters_if_due(now_ts: float) -> None:
    global _LAST_RATE_LIMIT_CLEANUP_AT

    retention = max(3600, int(getattr(config, "RATE_LIMIT_RETENTION_SECONDS", 7 * 24 * 3600)))
    cleanup_interval = min(300, retention)
    if now_ts - _LAST_RATE_LIMIT_CLEANUP_AT < cleanup_interval:
        return

    with _RATE_LIMIT_CLEANUP_LOCK:
        if now_ts - _LAST_RATE_LIMIT_CLEANUP_AT < cleanup_interval:
            return

        from database import RateLimitCounter, db

        cutoff = datetime.fromtimestamp(max(0, now_ts - retention), tz=timezone.utc).replace(tzinfo=None)
        try:
            RateLimitCounter.query.filter(RateLimitCounter.updated_at < cutoff).delete(synchronize_session=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.debug("Rate limit counter cleanup failed", exc_info=True)
        finally:
            _LAST_RATE_LIMIT_CLEANUP_AT = now_ts


def _increment_rate_limit_counter(subject_key: str, rule_name: str, window_seconds: int, now_ts: float) -> int:
    from database import RateLimitCounter, db

    now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc).replace(tzinfo=None)
    window_start = _rate_limit_window_start(now_ts, window_seconds)
    values = {
        "subject_key": subject_key,
        "rule_name": rule_name,
        "window_start": window_start,
        "window_seconds": int(window_seconds),
        "count": 1,
        "created_at": now_dt,
        "updated_at": now_dt,
    }
    table = RateLimitCounter.__table__
    bind = db.session.get_bind()
    dialect_name = bind.dialect.name if bind is not None else ""

    try:
        if dialect_name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as dialect_insert
        elif dialect_name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as dialect_insert
        else:
            raise RuntimeError("dialect_fallback")

        stmt = dialect_insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["subject_key", "rule_name", "window_start"],
            set_={
                "count": table.c.count + 1,
                "updated_at": now_dt,
            },
        ).returning(table.c.count)
        count = int(db.session.execute(stmt).scalar_one())
        db.session.commit()
        return count
    except Exception:
        db.session.rollback()

    row = db.session.get(
        RateLimitCounter,
        {
            "subject_key": subject_key,
            "rule_name": rule_name,
            "window_start": window_start,
        },
    )
    if row is None:
        row = RateLimitCounter(**values)
        db.session.add(row)
        count = 1
    else:
        row.count = int(row.count or 0) + 1
        row.updated_at = now_dt
        count = row.count
    db.session.commit()
    return int(count)


def _resolve_rate_limit_subject(*, scope: str, key_func=None) -> str | None:
    if callable(key_func):
        custom_value = key_func()
        normalized_custom = str(custom_value or "").strip()
        return normalized_custom or None

    normalized_scope = str(scope or "auto").strip().lower()
    if normalized_scope == "user":
        return get_request_auth_user_id()
    if normalized_scope == "ip":
        return _request_ip_address()
    if normalized_scope == "auto":
        return get_request_auth_user_id() or _request_ip_address()
    return None


def _rate_limit_response(retry_after: int | None):
    payload = {"error": "Rate limit exceeded"}
    if retry_after is not None:
        payload["retry_after_seconds"] = retry_after
    response = jsonify(payload)
    response.status_code = 429
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return response


def enforce_rate_limit(
    limit: int,
    window_seconds: int,
    *,
    key_prefix: str,
    scope: str = "auto",
    key_func=None,
):
    enforced = bool(getattr(config, "RATE_LIMIT_ENABLED", True))
    if not enforced:
        return None

    if _testing_bypass_enabled(
        "RATE_LIMIT_BYPASS_FOR_TESTS",
        bool(getattr(config, "RATE_LIMIT_BYPASS_FOR_TESTS", False)),
    ):
        return None

    subject = _resolve_rate_limit_subject(scope=scope, key_func=key_func)
    if not subject:
        return None

    max_requests = max(1, int(limit))
    window = int(window_seconds)
    now_ts = time.time()
    _cleanup_rate_limit_counters_if_due(now_ts)

    rule_name = _rate_limit_rule_name(key_prefix, window)
    subject_key = f"{scope}:{subject}"
    count = _increment_rate_limit_counter(subject_key, rule_name, window, now_ts)
    if count <= max_requests:
        return None
    return _rate_limit_response(_rate_limit_retry_after(now_ts, window))


def rate_limit(
    limit: int,
    window_seconds: int,
    *,
    key_prefix: str,
    scope: str = "auto",
    key_func=None,
) -> callable:
    """
    Database-backed fixed-window rate limiter shared across workers.
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            limited = enforce_rate_limit(
                limit,
                window_seconds,
                key_prefix=key_prefix,
                scope=scope,
                key_func=key_func,
            )
            if limited is not None:
                return limited
            return f(*args, **kwargs)

        return decorated

    return decorator


# ============================================
# PROVIDER TOKEN VERIFICATION
# ============================================

def _resolve_google_client_ids() -> list[str]:
    configured = list(getattr(config, "GOOGLE_CLIENT_IDS", []) or [])
    normalized = [item.strip() for item in configured if str(item).strip()]
    if normalized:
        return normalized

    fallback = (os.getenv("GOOGLE_CLIENT_IDS") or os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    if not fallback:
        return []
    return [item.strip() for item in fallback.split(",") if item.strip()]


def verify_google_token(id_token: str) -> dict:
    """
    Verify Google ID token and extract user info.

    Args:
        id_token: Google ID token from iOS Sign-In

    Returns:
        Dict with: provider_id, email, display_name, avatar_url

    Raises:
        ValueError: If token is invalid
    """
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        allowed_client_ids = _resolve_google_client_ids()
        if not allowed_client_ids:
            raise ValueError("GOOGLE_CLIENT_IDS not configured")

        idinfo = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            None
        )

        token_audience = str(idinfo.get("aud") or "").strip()
        if token_audience not in allowed_client_ids:
            raise ValueError("Google token audience mismatch")

        return {
            "provider_id": idinfo["sub"],
            "email": idinfo.get("email", ""),
            "display_name": idinfo.get("name", ""),
            "avatar_url": idinfo.get("picture", "")
        }
    except ImportError:
        # Fallback: verify via Google's tokeninfo endpoint
        allowed_client_ids = _resolve_google_client_ids()
        if not allowed_client_ids:
            raise ValueError("GOOGLE_CLIENT_IDS not configured")

        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=10
        )
        if response.status_code != 200:
            raise ValueError(f"Google token verification failed: {response.text}")

        data = response.json()
        token_audience = str(data.get("aud") or data.get("azp") or "").strip()
        if token_audience not in allowed_client_ids:
            raise ValueError("Google token audience mismatch")

        return {
            "provider_id": data["sub"],
            "email": data.get("email", ""),
            "display_name": data.get("name", ""),
            "avatar_url": data.get("picture", "")
        }
    except Exception as e:
        logger.error(f"Google token verification error: {e}")
        raise ValueError(f"Invalid Google token: {str(e)}")


def _resolve_apple_client_ids() -> list[str]:
    """
    Resolve allowed Apple audiences (services IDs / bundle IDs).
    """
    configured = (os.getenv("APPLE_CLIENT_IDS") or os.getenv("APPLE_CLIENT_ID") or "").strip()
    if configured:
        values = [item.strip() for item in configured.split(",") if item.strip()]
        if values:
            return values
    # Default to app bundle ID when env is not configured.
    return ["com.coachi.app"]


def verify_apple_token(
    identity_token: str,
    email: str | None = None,
    full_name: str | None = None,
) -> dict:
    """
    Verify Apple identity token and extract user info.

    Args:
        identity_token: Apple identity token (JWT) from ASAuthorizationAppleIDCredential
        email: Optional fallback email from iOS first-sign-in payload
        full_name: Optional fallback full name from iOS first-sign-in payload

    Returns:
        Dict with: provider_id, email, display_name, avatar_url

    Raises:
        ValueError: If token is invalid
    """
    try:
        signing_key_client = jwt.PyJWKClient("https://appleid.apple.com/auth/keys")
        signing_key = signing_key_client.get_signing_key_from_jwt(identity_token)
        decoded = jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_resolve_apple_client_ids(),
            issuer="https://appleid.apple.com",
        )
    except jwt.ExpiredSignatureError as exc:
        logger.warning("Apple token expired: %s", exc)
        raise AppleTokenVerificationError("apple_token_expired", "Apple sign-in token expired. Please try again.") from exc
    except jwt.InvalidAudienceError as exc:
        logger.warning("Apple token audience mismatch: %s", exc)
        raise AppleTokenVerificationError("apple_audience_mismatch", "Unable to verify Apple identity.") from exc
    except jwt.InvalidIssuerError as exc:
        logger.warning("Apple token issuer mismatch: %s", exc)
        raise AppleTokenVerificationError("apple_identity_unverified", "Unable to verify Apple identity.") from exc
    except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidTokenError) as exc:
        logger.warning("Apple token invalid: %s", exc)
        raise AppleTokenVerificationError("apple_token_invalid", "Invalid Apple sign-in token.") from exc
    except Exception as exc:
        logger.error("Apple token verification error: %s", exc)
        raise AppleTokenVerificationError("apple_identity_unverified", "Unable to verify Apple identity.") from exc

    profile_email = decoded.get("email") or (email or "").strip()
    profile_name = (full_name or "").strip()
    if not profile_name:
        # Apple can omit name after first authorization; avoid empty display names.
        profile_name = profile_email.split("@")[0] if profile_email else ""

    provider_id = decoded.get("sub", "")
    if not provider_id:
        raise AppleTokenVerificationError("apple_token_invalid", "Invalid Apple sign-in token.")

    return {
        "provider_id": provider_id,
        "email": profile_email,
        "display_name": profile_name,
        "avatar_url": "",
    }


def verify_facebook_token(access_token: str) -> dict:
    """
    Verify Facebook access token and extract user info.

    Args:
        access_token: Facebook access token from iOS Login

    Returns:
        Dict with: provider_id, email, display_name, avatar_url

    Raises:
        ValueError: If token is invalid
    """
    try:
        # Call Facebook Graph API to get user info
        response = requests.get(
            "https://graph.facebook.com/me",
            params={
                "access_token": access_token,
                "fields": "id,email,name,picture.type(large)"
            },
            timeout=10
        )

        if response.status_code != 200:
            raise ValueError(f"Facebook token verification failed: {response.text}")

        data = response.json()

        avatar_url = ""
        if "picture" in data and "data" in data["picture"]:
            avatar_url = data["picture"]["data"].get("url", "")

        return {
            "provider_id": data["id"],
            "email": data.get("email", ""),
            "display_name": data.get("name", ""),
            "avatar_url": avatar_url
        }
    except requests.RequestException as e:
        logger.error(f"Facebook token verification error: {e}")
        raise ValueError(f"Facebook API error: {str(e)}")


def verify_vipps_token(access_token: str) -> dict:
    """
    Verify Vipps access token and extract user info.

    Uses Vipps Login API userinfo endpoint.

    Args:
        access_token: Vipps access token from iOS Vipps Login

    Returns:
        Dict with: provider_id, email, display_name, avatar_url, phone_number

    Raises:
        ValueError: If token is invalid
    """
    try:
        # Determine Vipps API base URL
        vipps_env = os.getenv("VIPPS_ENVIRONMENT", "test")  # "test" or "production"
        if vipps_env == "production":
            base_url = "https://api.vipps.no"
        else:
            base_url = "https://apitest.vipps.no"

        # Call Vipps userinfo endpoint
        response = requests.get(
            f"{base_url}/vipps-userinfo-api/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code != 200:
            raise ValueError(f"Vipps token verification failed: {response.status_code}")

        data = response.json()

        # Vipps provides name parts separately
        given_name = data.get("given_name", "")
        family_name = data.get("family_name", "")
        display_name = f"{given_name} {family_name}".strip()

        return {
            "provider_id": data.get("sub", ""),
            "email": data.get("email", ""),
            "display_name": display_name,
            "avatar_url": "",  # Vipps doesn't provide avatar
            "phone_number": data.get("phone_number", "")
        }
    except requests.RequestException as e:
        logger.error(f"Vipps token verification error: {e}")
        raise ValueError(f"Vipps API error: {str(e)}")
