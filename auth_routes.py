"""
Auth API routes for Treningscoach
Handles Google, Facebook, and Vipps authentication
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from database import db, User, UserSettings
from auth import (
    create_jwt, require_auth,
    verify_google_token, verify_facebook_token, verify_vipps_token
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ============================================
# HELPER: Find or create user
# ============================================

def find_or_create_user(provider: str, provider_info: dict) -> User:
    """
    Find existing user by provider ID or create new one.

    Args:
        provider: "google", "facebook", or "vipps"
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
        user.updated_at = datetime.utcnow()
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
            user.updated_at = datetime.utcnow()
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

    # Create default settings
    settings = UserSettings(user_id=user.id)
    db.session.add(settings)

    db.session.commit()
    logger.info(f"New user created: {user.email} ({provider})")
    return user


# ============================================
# AUTH ENDPOINTS
# ============================================

@auth_bp.route("/google", methods=["POST"])
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
    try:
        data = request.get_json()
        if not data or "id_token" not in data:
            return jsonify({"error": "Missing id_token"}), 400

        # Verify with Google
        provider_info = verify_google_token(data["id_token"])

        # Find or create user
        user = find_or_create_user("google", provider_info)

        # Issue JWT
        token = create_jwt(user.id, user.email)

        return jsonify({
            "token": token,
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Google auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Google auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/facebook", methods=["POST"])
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
    try:
        data = request.get_json()
        if not data or "access_token" not in data:
            return jsonify({"error": "Missing access_token"}), 400

        # Verify with Facebook
        provider_info = verify_facebook_token(data["access_token"])

        # Find or create user
        user = find_or_create_user("facebook", provider_info)

        # Issue JWT
        token = create_jwt(user.id, user.email)

        return jsonify({
            "token": token,
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Facebook auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Facebook auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/vipps", methods=["POST"])
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
    try:
        data = request.get_json()
        if not data or "access_token" not in data:
            return jsonify({"error": "Missing access_token"}), 400

        # Verify with Vipps
        provider_info = verify_vipps_token(data["access_token"])

        # Find or create user
        user = find_or_create_user("vipps", provider_info)

        # Default Norwegian language for Vipps users
        if user.language == "en":
            user.language = "no"
            db.session.commit()

        # Issue JWT
        token = create_jwt(user.id, user.email)

        return jsonify({
            "token": token,
            "user": user.to_dict()
        }), 200

    except ValueError as e:
        logger.warning(f"Vipps auth failed: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Vipps auth error: {e}", exc_info=True)
        return jsonify({"error": "Authentication failed"}), 500


# ============================================
# USER PROFILE ENDPOINTS
# ============================================

@auth_bp.route("/me", methods=["GET"])
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
    user = User.query.get(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["PUT"])
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
    user = User.query.get(g.current_user_id)
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

    user.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"Profile updated: {user.email}")
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["DELETE"])
@require_auth
def delete_account():
    """
    Delete current user account and all associated data.

    Requires: Authorization: Bearer <token>
    """
    user = User.query.get(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    email = user.email
    db.session.delete(user)
    db.session.commit()

    logger.info(f"Account deleted: {email}")
    return jsonify({"success": True, "message": "Account deleted"}), 200
