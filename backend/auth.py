"""
Authentication module for Treningscoach
Supports: Google Sign-In, Facebook Login, Vipps Login
Issues JWT tokens for session management
"""

import os
import logging
import jwt
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "treningscoach-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

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
