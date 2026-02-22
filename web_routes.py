"""Web and landing related Flask routes extracted from main runtime path.

This module keeps the same endpoint behavior while reducing main.py surface.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import re
from typing import Any, Callable

from flask import Blueprint, jsonify, make_response, render_template, request
from sqlalchemy.exc import IntegrityError


def create_web_blueprint(
    *,
    config_module: Any,
    waitlist_model: Any,
    db: Any,
    normalize_language_code: Callable[[str], str],
    quality_guard_snapshot_fn: Callable[[], dict],
    product_flags_snapshot_fn: Callable[[], dict],
    landing_link_context_fn: Callable[[], dict],
    resolve_web_variant_fn: Callable[[str | None], tuple[str, str]],
    logger: Any,
) -> Blueprint:
    """Create blueprint for landing/web + lightweight runtime endpoints."""
    web_bp = Blueprint("web_routes", __name__)

    valid_landing_events = {
        "waitlist_signup",
        "app_store_click",
        "google_play_click",
        "android_early_access_click",
    }

    @web_bp.route("/")
    def home():
        """Homepage - launch page (app download funnel)."""
        response = make_response(render_template("index_launch.html", **landing_link_context_fn()))
        response.headers["X-Web-Variant"] = "launch"
        return response

    @web_bp.route("/preview")
    def preview_compare():
        """Side-by-side compare page for claude vs codex web variants."""
        return render_template("site_compare.html")

    @web_bp.route("/preview/<variant>")
    def preview_variant(variant):
        """Preview a specific web variant without changing deploy defaults."""
        resolved_variant, template = resolve_web_variant_fn(variant)
        response = make_response(render_template(template, **landing_link_context_fn()))
        response.headers["X-Web-Variant"] = resolved_variant
        return response

    @web_bp.route("/health")
    def health():
        """Simple health endpoint."""
        return jsonify(
            {
                "status": "healthy",
                "version": config_module.APP_VERSION,
                "timestamp": datetime.now().isoformat(),
                "quality_guards": quality_guard_snapshot_fn(),
                "product_flags": product_flags_snapshot_fn(),
                "endpoints": {
                    "analyze": "/analyze",
                    "coach": "/coach",
                    "download": "/download/<filename>",
                    "welcome": "/welcome",
                    "app_runtime": "/app/runtime",
                },
            }
        )

    @web_bp.route("/app/runtime", methods=["GET"])
    def app_runtime():
        """Runtime flags for mobile/web clients (free mode now, billing-ready later)."""
        return jsonify(
            {
                "status": "ok",
                "version": config_module.APP_VERSION,
                "timestamp": datetime.now().isoformat(),
                "product_flags": product_flags_snapshot_fn(),
            }
        )

    @web_bp.route("/waitlist", methods=["POST"])
    def waitlist_signup():
        """
        Capture landing-page waitlist emails in database.
        Rate limited to 5 submissions per IP hash per hour.
        """
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        default_language = getattr(config_module, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(data.get("language", default_language))
        source = (data.get("source") or "website").strip().lower()[:50] or "website"

        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return jsonify({"error": "Invalid email"}), 400

        remote_addr = request.remote_addr or "unknown"
        ip_hash = hashlib.sha256(remote_addr.encode()).hexdigest()
        now = datetime.utcnow()
        window_start = now - timedelta(hours=1)

        recent_count = waitlist_model.query.filter(
            waitlist_model.ip_hash == ip_hash,
            waitlist_model.created_at >= window_start,
        ).count()
        if recent_count >= 5:
            return jsonify({"error": "Rate limit exceeded"}), 429

        existing = waitlist_model.query.filter_by(email=email).first()
        if existing:
            logger.info("Waitlist signup duplicate ignored: %s (lang=%s)", email, language)
            return jsonify({"success": True, "duplicate": True}), 200

        signup = waitlist_model(
            email=email,
            language=language,
            source=source,
            ip_hash=ip_hash,
        )
        db.session.add(signup)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.info("Waitlist signup duplicate raced: %s (lang=%s)", email, language)
            return jsonify({"success": True, "duplicate": True}), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Waitlist signup failed: %s", exc)
            return jsonify({"error": "Failed to capture waitlist signup"}), 500

        logger.info("Waitlist signup persisted: %s (lang=%s, source=%s)", email, language, source)
        return jsonify({"success": True}), 200

    @web_bp.route("/analytics/event", methods=["POST"])
    def analytics_event():
        """
        Lightweight landing analytics endpoint.
        Accepts JSON or sendBeacon text payloads.
        """
        raw = request.get_data(as_text=True)
        try:
            data = json.loads(raw) if raw else (request.get_json(silent=True) or {})
        except (json.JSONDecodeError, ValueError):
            data = request.get_json(silent=True) or {}

        event = (data.get("event") or "").strip()
        metadata = data.get("metadata", {})

        if event not in valid_landing_events:
            return jsonify({"error": "Invalid event"}), 400

        logger.info("Landing analytics event: %s | %s", event, json.dumps(metadata))
        return jsonify({"success": True}), 200

    return web_bp

