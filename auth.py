"""
Authentication module for Treningscoach
Supports: Apple Sign-In, Google Sign-In, Facebook Login, Vipps Login
Issues JWT tokens for session management
"""

import os
import logging
import secrets
import jwt
import requests
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# JWT Configuration
DEFAULT_INSECURE_JWT_SECRET = "treningscoach-dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def _persist_runtime_jwt_secret(secret_path: Path) -> str:
    """
    Load a shared runtime JWT secret from disk, creating one when missing.

    This keeps workers consistent without relying on a predictable default.
    """
    try:
        existing = secret_path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning("Could not read JWT secret file %s: %s", secret_path, exc)

    secret = secrets.token_urlsafe(48)

    try:
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(secret_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(secret)
    except FileExistsError:
        # Another worker created it first; read canonical value.
        try:
            existing = secret_path.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        except OSError:
            pass
    except OSError as exc:
        logger.warning("Could not persist JWT secret file %s: %s", secret_path, exc)

    return secret


def _resolve_jwt_secret() -> str:
    configured = (os.getenv("JWT_SECRET") or "").strip()
    if configured and configured != DEFAULT_INSECURE_JWT_SECRET:
        return configured

    if configured == DEFAULT_INSECURE_JWT_SECRET:
        logger.warning("Ignoring insecure default JWT secret from JWT_SECRET env var")

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
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS)
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


def optional_auth(f):
    """
    Flask decorator for optional authentication.
    Sets g.current_user_id if token present and valid, otherwise sets to None.
    Does NOT reject unauthenticated requests.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user_id = None
        g.current_user_email = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                payload = decode_jwt(token)
                g.current_user_id = payload["user_id"]
                g.current_user_email = payload.get("email")
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass  # Silently ignore invalid tokens for optional auth

        return f(*args, **kwargs)

    return decorated


# ============================================
# PROVIDER TOKEN VERIFICATION
# ============================================

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

        # Verify the token with Google
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID not configured")

        idinfo = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            google_client_id
        )

        return {
            "provider_id": idinfo["sub"],
            "email": idinfo.get("email", ""),
            "display_name": idinfo.get("name", ""),
            "avatar_url": idinfo.get("picture", "")
        }
    except ImportError:
        # Fallback: verify via Google's tokeninfo endpoint
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=10
        )
        if response.status_code != 200:
            raise ValueError(f"Google token verification failed: {response.text}")

        data = response.json()
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
    return ["com.mariusgaarder.TreningsCoach"]


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
