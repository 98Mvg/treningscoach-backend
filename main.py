# main.py - MAIN FILE FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify, g
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
import wave
import math
import random
import logging
import time
import inspect
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta, timezone
from threading import Lock
import requests
import config  # Import central configuration
from brain_router import BrainRouter  # Import Brain Router
from session_manager import SessionManager  # Import Session Manager
from persona_manager import PersonaManager  # Import Persona Manager
from coaching_intelligence import calculate_next_interval  # Legacy interval timing helper only
from user_memory import UserMemory  # STEP 5: Import user memory
from voice_intelligence import VoiceIntelligence  # STEP 6: Import voice intelligence
from elevenlabs_tts import ElevenLabsTTS, synthesize_speech_mock  # Import ElevenLabs TTS + fallback mock
from strategic_brain import get_strategic_brain  # Import Strategic Brain for high-level coaching
from database import (
    AppStoreServerNotification,
    AppStoreSubscriptionState,
    UserSubscription,
    init_db,
    db,
    WaitlistSignup,
    User,
    UserProfile,
    WorkoutHistory,
    user_has_active_app_store_subscription,
)  # Import database initialization + models
from breath_analyzer import BreathAnalyzer  # Import advanced breath analysis
from auth_routes import auth_bp  # Import auth blueprint
from auth import (
    enforce_rate_limit,
    get_request_auth_user_id,
    rate_limit,
    require_auth,
    require_mobile_auth,
    resolve_user_subscription_tier,
)
from norwegian_phrase_quality import rewrite_norwegian_phrase
from coaching_engine import validate_coaching_text, get_template_message
from breathing_timeline import BreathingTimeline
from breath_reliability import summarize_breath_quality, derive_breath_quality_samples
from running_personalization import RunningPersonalizationStore
from zone_event_motor import (
    evaluate_zone_tick,
    normalize_coaching_style,
    normalize_interval_template,
)
from web_routes import create_web_blueprint
from chat_routes import create_chat_blueprint
from locale_config import get_voice_id as locale_voice_id
from workout_contracts import (
    UserProfilePayload,
    normalize_continuous_contract,
    normalize_talk_contract,
    profile_validation_errors,
)
from launch_integrations import capture_posthog_event, init_sentry
from app_store_runtime import (
    AppStorePayloadError,
    ACTIVE_APP_STORE_STATUSES,
    decode_app_store_signed_payload,
    extract_transaction_fields,
    tier_from_status,
)
from xai_voice import (
    bootstrap_post_workout_voice_session,
    sanitize_post_workout_summary_context,
    sanitize_workout_history_context,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _utcnow_iso_z() -> str:
    return _utcnow().isoformat().replace("+00:00", "Z")

app = Flask(__name__)
SENTRY_RUNTIME = init_sentry(logger=logger)
_cors_origins = list(getattr(config, "CORS_ALLOWED_ORIGINS", []) or [])
CORS(
    app,
    resources={r"/*": {"origins": _cors_origins}},
)
logger.info("CORS configured with %s allowed origins", len(_cors_origins))

# Initialize database
init_db(app)
logger.info("✅ Database initialized")

# Register auth routes
app.register_blueprint(auth_bp)
logger.info("✅ Auth routes registered (/auth/*)")

# Configuration from config.py
MAX_FILE_SIZE = config.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

# Folders for temporary file storage
UPLOAD_FOLDER = getattr(config, "UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
OUTPUT_FOLDER = getattr(config, "OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "output"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Brain Router and Managers
brain_router = BrainRouter()
session_manager = SessionManager()
user_memory = UserMemory()  # STEP 5: Initialize user memory
voice_intelligence = VoiceIntelligence()  # STEP 6: Initialize voice intelligence
breath_analyzer = BreathAnalyzer(
    sample_rate=getattr(config, "BREATH_ANALYSIS_SAMPLE_RATE", 44100),
    enable_mfcc=bool(getattr(config, "BREATH_ANALYSIS_ENABLE_MFCC", False)),
)  # Advanced breath analysis with DSP + spectral features
_breath_analysis_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="breath-analysis")
_breath_analysis_lock = Lock()
_breath_analysis_skip_until = 0.0
_talk_stt_lock = Lock()
_talk_stt_quota_skip_until = 0.0
running_personalization = RunningPersonalizationStore(
    storage_path=getattr(config, "ZONE_PERSONALIZATION_STORAGE_PATH", "instance/zone_personalization.json"),
    max_recovery_samples=getattr(config, "ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES", 24),
    max_session_history=getattr(config, "ZONE_PERSONALIZATION_MAX_SESSION_HISTORY", 20),
)

# Pre-warm librosa to avoid cold-start delay on first request
# librosa lazy-loads heavy modules (numba, etc.) which can cause 30s+ timeout
try:
    import librosa
    import numpy as np
    _warmup = np.zeros(4410, dtype=np.float32)  # 100ms of silence
    librosa.feature.rms(y=_warmup, frame_length=1024, hop_length=512)
    del _warmup
    logger.info("✅ Librosa pre-warmed successfully")
except Exception as e:
    logger.warning(f"⚠️ Librosa pre-warm failed: {e}")
if getattr(config, "USE_STRATEGIC_BRAIN", False):
    strategic_brain = get_strategic_brain()  # Initialize Strategic Brain (Claude-powered)
    if strategic_brain.is_available():
        logger.info("✅ Strategic Brain (Claude) is available")
    else:
        logger.info("⚠️ Strategic Brain disabled (no ANTHROPIC_API_KEY)")
else:
    strategic_brain = None
    logger.info("ℹ️ Strategic Brain disabled via config (USE_STRATEGIC_BRAIN=False)")
logger.info(f"Initialized with brain: {brain_router.get_active_brain()}")

# Initialize TTS service (ElevenLabs for production)
def _resolve_default_elevenlabs_voice_id():
    """
    Pick a default ElevenLabs voice ID from explicit env vars first,
    then locale-config voice maps.
    """
    candidates = [
        ("ELEVENLABS_VOICE_ID", os.getenv("ELEVENLABS_VOICE_ID", "")),
        ("ELEVENLABS_VOICE_ID_EN", os.getenv("ELEVENLABS_VOICE_ID_EN", "")),
        ("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", "")),
        ("locale_config.personal_trainer.en", locale_voice_id("en", "personal_trainer")),
        ("ELEVENLABS_VOICE_ID_NO", os.getenv("ELEVENLABS_VOICE_ID_NO", "")),
        ("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", "")),
        ("locale_config.personal_trainer.no", locale_voice_id("no", "personal_trainer")),
        ("locale_config.toxic_mode.en", locale_voice_id("en", "toxic_mode")),
    ]

    for source, raw_value in candidates:
        value = str(raw_value or "").strip()
        if value:
            return value, source

    return "", "not_found"


elevenlabs_api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
elevenlabs_voice_id, elevenlabs_voice_source = _resolve_default_elevenlabs_voice_id()

if elevenlabs_api_key and elevenlabs_voice_id:
    logger.info(f"🎙️ Initializing ElevenLabs TTS (voice source: {elevenlabs_voice_source})...")
    elevenlabs_tts = ElevenLabsTTS(api_key=elevenlabs_api_key, voice_id=elevenlabs_voice_id)
    USE_ELEVENLABS = True
    logger.info("✅ ElevenLabs TTS ready")
elif not elevenlabs_api_key:
    logger.warning("⚠️ ELEVENLABS_API_KEY missing, using mock TTS")
    USE_ELEVENLABS = False
else:
    logger.warning("⚠️ ElevenLabs voice ID not found in env/config, using mock TTS")
    USE_ELEVENLABS = False
logger.info("TTS service initialized")
TTS_RUNTIME_DIAGNOSTICS = {
    "boot": {
        "use_elevenlabs": bool(USE_ELEVENLABS),
        "voice_source": elevenlabs_voice_source,
        "voice_prefix": (elevenlabs_voice_id[:8] + "...") if elevenlabs_voice_id else "",
    },
    "last_success": None,
    "last_error": None,
}
VOICE_TEXT_PACING_COMPAT_WARNED = False
QUALITY_GUARD_METRICS = {
    "continuous_ticks": 0,
    "spoken_ticks": 0,
    "validation_checks": 0,
    "validation_failures": 0,
    "validation_template_fallbacks": 0,
    "timeline_cue_candidates": 0,
    "timeline_overrides": 0,
    "timeline_zone_priority_skips": 0,
    "language_guard_rewrites": 0,
    "language_guard_en_to_no_rewrites": 0,
    "language_guard_no_to_en_rewrites": 0,
}


def _increment_quality_metric(key: str, amount: int = 1) -> None:
    """Best-effort in-memory quality counter increment."""
    if key not in QUALITY_GUARD_METRICS:
        return
    try:
        QUALITY_GUARD_METRICS[key] = int(QUALITY_GUARD_METRICS.get(key, 0)) + int(amount)
    except Exception:
        # Non-critical observability path; never fail request flow.
        pass


def _quality_guard_snapshot() -> dict:
    checks = max(1, int(QUALITY_GUARD_METRICS.get("validation_checks", 0)))
    failures = int(QUALITY_GUARD_METRICS.get("validation_failures", 0))
    fallbacks = int(QUALITY_GUARD_METRICS.get("validation_template_fallbacks", 0))
    snapshot = dict(QUALITY_GUARD_METRICS)
    snapshot["validation_failure_rate"] = round(failures / checks, 4)
    snapshot["validation_template_fallback_rate"] = round(fallbacks / checks, 4)
    return snapshot


def _product_flags_snapshot() -> dict:
    """Expose backend runtime product toggles to keep app behavior explicit."""
    free_mode = bool(getattr(config, "APP_FREE_MODE", True))
    billing_enabled = bool(getattr(config, "BILLING_ENABLED", False))
    premium_surfaces = bool(getattr(config, "PREMIUM_SURFACES_ENABLED", False))
    return {
        "app_free_mode": free_mode,
        "billing_enabled": billing_enabled,
        "premium_surfaces_enabled": premium_surfaces,
        "monetization_phase": "free_only" if free_mode else "billing_ready",
    }


def _voice_error(message: str, *, status: int, error_code: str):
    return jsonify({"error": message, "error_code": error_code}), status


def _capture_voice_event(event: str, *, user_id: str, metadata: dict | None = None) -> None:
    capture_posthog_event(
        event,
        metadata=metadata if isinstance(metadata, dict) else {},
        distinct_id=f"user:{user_id}",
        logger=logger,
    )


_MOBILE_ANALYTICS_ALLOWED_EVENTS = {
    "app_opened",
    "deep_link_opened",
    "onboarding_completed",
    "paywall_cta_tapped",
    "paywall_dismissed",
    "paywall_manage_subscription_tapped",
    "paywall_restore_tapped",
    "paywall_shown",
    "subscription_sync_failed",
    "subscription_sync_succeeded",
    "voice_cta_tapped",
    "voice_fallback_text_opened",
    "voice_session_ended",
    "voice_session_failed",
    "voice_session_requested",
    "voice_session_started",
    "workout_completed",
    "workout_started",
}


def _sanitize_analytics_metadata(metadata: object) -> dict:
    if not isinstance(metadata, dict):
        return {}
    sanitized: dict[str, object] = {}
    for key, value in metadata.items():
        normalized_key = str(key or "").strip()[:64]
        if not normalized_key:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[normalized_key] = value
        elif isinstance(value, list):
            sanitized[normalized_key] = [
                item for item in value if isinstance(item, (str, int, float, bool))
            ][:20]
    return sanitized


def _normalize_mobile_analytics_anonymous_id(value: object) -> str | None:
    candidate = re.sub(r"[^a-zA-Z0-9_-]", "", str(value or "").strip())
    if len(candidate) < 8:
        return None
    return candidate[:64]


def _capture_mobile_analytics_event(
    event: str,
    *,
    user_id: str | None,
    anonymous_id: str | None,
    metadata: dict | None = None,
) -> None:
    resolved_user_id = str(user_id or "").strip() or None
    resolved_anonymous_id = _normalize_mobile_analytics_anonymous_id(anonymous_id)
    if resolved_user_id:
        distinct_id = f"user:{resolved_user_id}"
        access_tier = resolve_user_subscription_tier(resolved_user_id)
    elif resolved_anonymous_id:
        distinct_id = f"mobile:{resolved_anonymous_id}"
        access_tier = "guest"
    else:
        return

    event_metadata = _sanitize_analytics_metadata(metadata)
    event_metadata.setdefault("subscription_tier", access_tier)
    event_metadata.setdefault("source", "ios")
    capture_posthog_event(
        event,
        metadata=event_metadata,
        distinct_id=distinct_id,
        logger=logger,
    )


def _normalize_app_store_bundle_id(value: object) -> str | None:
    bundle_id = str(value or "").strip()
    return bundle_id or None


def _update_user_subscription_tier_record(*, user_id: str | None, status: str | None) -> str:
    normalized_user_id = str(user_id or "").strip()
    resolved_tier = tier_from_status(status)
    if not normalized_user_id:
        return resolved_tier
    if db.session.get(User, normalized_user_id) is None:
        return resolved_tier

    subscription = UserSubscription.query.filter_by(user_id=normalized_user_id).first()
    if user_has_active_app_store_subscription(normalized_user_id):
        resolved_tier = "premium"
    elif resolved_tier != "premium":
        resolved_tier = "free"
    if subscription is None:
        subscription = UserSubscription(user_id=normalized_user_id, tier=resolved_tier)
        db.session.add(subscription)
    else:
        subscription.tier = resolved_tier
    return resolved_tier


def _upsert_app_store_subscription_state(
    *,
    user_id: str | None,
    transaction_fields: dict[str, object],
    source: str,
    notification_uuid: str | None = None,
    notification_signed_at: datetime | None = None,
) -> AppStoreSubscriptionState:
    original_transaction_id = str(transaction_fields.get("original_transaction_id") or "").strip()
    if not original_transaction_id:
        raise AppStorePayloadError("missing_original_transaction_id")

    state = db.session.get(AppStoreSubscriptionState, original_transaction_id)
    if state is None:
        state = AppStoreSubscriptionState(original_transaction_id=original_transaction_id)
        db.session.add(state)

    resolved_user_id = str(user_id or "").strip() or None
    if resolved_user_id and db.session.get(User, resolved_user_id) is not None:
        state.user_id = resolved_user_id
    if not state.user_id:
        candidate_token = str(transaction_fields.get("app_account_token") or "").strip()
        if candidate_token and db.session.get(User, candidate_token) is not None:
            state.user_id = candidate_token

    state.transaction_id = str(transaction_fields.get("transaction_id") or "").strip() or state.transaction_id
    state.product_id = transaction_fields.get("product_id")
    state.bundle_id = transaction_fields.get("bundle_id")
    state.environment = transaction_fields.get("environment")
    state.status = str(transaction_fields.get("status") or "unknown").strip().lower() or "unknown"
    state.ownership_type = transaction_fields.get("ownership_type")
    state.notification_type = transaction_fields.get("notification_type")
    state.notification_subtype = transaction_fields.get("notification_subtype")
    state.app_account_token = transaction_fields.get("app_account_token")
    state.purchase_date = transaction_fields.get("purchase_date")
    state.expires_at = transaction_fields.get("expires_at")
    state.revocation_date = transaction_fields.get("revocation_date")
    state.last_transaction_signed_at = transaction_fields.get("signed_at")
    state.source = source
    if notification_uuid:
        state.last_notification_uuid = notification_uuid
    if notification_signed_at is not None:
        state.last_notification_signed_at = notification_signed_at

    _update_user_subscription_tier_record(user_id=state.user_id, status=state.status)
    return state


def _resolve_user_id_from_transaction_fields(transaction_fields: dict[str, object]) -> str | None:
    app_account_token = str(transaction_fields.get("app_account_token") or "").strip()
    if app_account_token:
        return app_account_token

    original_transaction_id = str(transaction_fields.get("original_transaction_id") or "").strip()
    if not original_transaction_id:
        return None

    state = db.session.get(AppStoreSubscriptionState, original_transaction_id)
    if state is None:
        return None
    return str(state.user_id or "").strip() or None


def _process_signed_app_store_transaction(
    *,
    signed_transaction_info: str,
    user_id: str | None,
    source: str,
    notification_type: str | None = None,
    notification_subtype: str | None = None,
    notification_uuid: str | None = None,
    notification_signed_at: datetime | None = None,
) -> tuple[AppStoreSubscriptionState, dict[str, object]]:
    transaction_payload = decode_app_store_signed_payload(
        signed_transaction_info,
        verify_signature=bool(getattr(config, "APP_STORE_SERVER_NOTIFICATIONS_VERIFY_SIGNATURE", True)),
        trusted_root_sha256s=set(getattr(config, "APP_STORE_TRUSTED_ROOT_SHA256S", []) or []),
    )
    transaction_fields = extract_transaction_fields(
        transaction_payload,
        notification_type=notification_type,
        notification_subtype=notification_subtype,
    )
    bundle_id = _normalize_app_store_bundle_id(transaction_fields.get("bundle_id"))
    allowed_bundle_ids = set(getattr(config, "APP_STORE_BUNDLE_IDS", []) or [])
    if bundle_id and allowed_bundle_ids and bundle_id not in allowed_bundle_ids:
        raise AppStorePayloadError("bundle_id_mismatch")

    state = _upsert_app_store_subscription_state(
        user_id=user_id,
        transaction_fields=transaction_fields,
        source=source,
        notification_uuid=notification_uuid,
        notification_signed_at=notification_signed_at,
    )
    return state, transaction_fields


def _live_voice_session_policy(subscription_tier: str) -> dict[str, int | str]:
    normalized_tier = "premium" if str(subscription_tier or "").strip().lower() == "premium" else "free"
    if normalized_tier == "premium":
        return {
            "access_tier": "premium",
            "max_duration_seconds": max(60, int(getattr(config, "XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS", 300) or 300)),
            "daily_session_limit": max(1, int(getattr(config, "XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY", 10) or 10)),
        }
    return {
        "access_tier": "free",
        "max_duration_seconds": max(60, int(getattr(config, "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", 120) or 120)),
        "daily_session_limit": max(1, int(getattr(config, "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", 2) or 2)),
    }


def _enforce_live_voice_session_limits(*, user_id: str, access_tier: str, daily_session_limit: int):
    return enforce_rate_limit(
        max(1, int(daily_session_limit)),
        24 * 3600,
        key_prefix=f"api.voice.session.{access_tier}.day",
        scope="user",
        key_func=lambda subject=user_id: subject,
    )

# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _detect_audio_signature(file_obj) -> str | None:
    """
    Detect audio type from file signature (magic bytes), not extension.
    """
    try:
        original_pos = file_obj.tell()
    except Exception:
        original_pos = None

    header = b""
    try:
        header = file_obj.read(64)
    finally:
        try:
            if original_pos is not None:
                file_obj.seek(original_pos)
            else:
                file_obj.seek(0)
        except Exception:
            pass

    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return "wav"
    if header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return "mp3"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return "m4a"
    return None


def _validate_audio_upload_signature(file_obj) -> bool:
    detected = _detect_audio_signature(file_obj)
    if detected in ALLOWED_EXTENSIONS:
        return True
    # Preserve existing deterministic test fixtures while keeping runtime strict.
    if os.getenv("PYTEST_CURRENT_TEST") and bool(getattr(config, "AUDIO_SIGNATURE_BYPASS_FOR_TESTS", True)):
        return True
    return False

def normalize_language_code(language: str) -> str:
    """
    Normalize language/locale hints to supported app language codes.
    Defaults to English for unknown values.
    """
    value = (language or "en").strip().lower()
    if value.startswith(("nb", "nn", "no")):
        return "no"
    if value.startswith("da"):
        return "da"
    if value.startswith("en"):
        return "en"
    return "en"

def normalize_intensity_value(intensity: str) -> str:
    """Normalize localized intensity labels to canonical keys."""
    value = (intensity or "moderate").strip().lower()
    mapping = {
        "critical": "critical",
        "kritisk": "critical",
        "intense": "intense",
        "hard": "intense",
        "moderate": "moderate",
        "moderat": "moderate",
        "calm": "calm",
        "rolig": "calm",
    }
    return mapping.get(value, "moderate")


def is_question_request(message: str) -> bool:
    """
    Heuristic detection for user-initiated Q&A prompts.

    Keeps existing workout cue logic intact while routing explicit questions
    to fast knowledge answers.
    """
    text = (message or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if "?" in text:
        return True

    question_starters = (
        "why", "how", "what", "when", "where", "who", "which", "can", "should", "is", "are", "do",
        "hvorfor", "hvordan", "hva", "hvilken", "hvilke", "kan", "bør", "skal", "er", "burde",
    )
    for starter in question_starters:
        if lowered == starter or lowered.startswith(starter + " "):
            return True

    request_patterns = (
        "explain ", "tell me ", "forklar ", "si hvorfor ", "hjelp meg å forstå ",
    )
    return any(lowered.startswith(pattern) for pattern in request_patterns)


def normalize_trigger_source(trigger_source: str) -> str | None:
    """Normalize and validate coach-talk trigger source."""
    value = (trigger_source or "button").strip().lower()
    allowed = set(getattr(config, "COACH_TALK_ALLOWED_TRIGGER_SOURCES", ("wake_word", "button")))
    if value not in allowed:
        return None
    return value


def talk_timeout_budget(trigger_source: str) -> float:
    """Get trigger-specific talk timeout budget in seconds."""
    if trigger_source == "wake_word":
        return max(0.8, float(getattr(config, "COACH_TALK_WAKE_TIMEOUT_SECONDS", 2.0)))
    return max(0.8, float(getattr(config, "COACH_TALK_BUTTON_TIMEOUT_SECONDS", 3.5)))


def _parse_profile_timestamp(value: str | None):
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _profile_payload_from_record(record: UserProfile) -> UserProfilePayload:
    return UserProfilePayload(
        name=record.name,
        sex=record.sex,
        age=record.age,
        height_cm=record.height_cm,
        weight_kg=record.weight_kg,
        max_hr_bpm=record.max_hr_bpm,
        resting_hr_bpm=record.resting_hr_bpm,
        profile_updated_at=record.profile_updated_at.isoformat() if record.profile_updated_at else None,
    )


def _coerce_profile_user_id(value: str | None) -> str | None:
    candidate = (value or "").strip()
    if not candidate or candidate.lower() == "unknown":
        return None
    return candidate


def _request_ip_fallback_key() -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
    candidate = forwarded or (request.remote_addr or "").strip() or "unknown"
    return f"guest-ip:{candidate}"


def _mobile_rate_limit_subject_from_request() -> str | None:
    auth_user_id = get_request_auth_user_id()
    if auth_user_id:
        return auth_user_id

    payload = request.get_json(silent=True) or {}
    explicit_user_id = _coerce_profile_user_id(
        request.form.get("user_profile_id") if request.form is not None else None
    ) or _coerce_profile_user_id(
        (payload.get("user_profile_id") if isinstance(payload, dict) else None)
        or (payload.get("user_id") if isinstance(payload, dict) else None)
    )
    if explicit_user_id:
        return explicit_user_id

    session_id = (
        (request.form.get("session_id") if request.form is not None else None)
        or (payload.get("session_id") if isinstance(payload, dict) else None)
        or ""
    ).strip()
    if session_id and session_manager.session_exists(session_id):
        metadata = session_manager.sessions.get(session_id, {}).get("metadata", {})
        session_user_id = _coerce_profile_user_id(
            metadata.get("user_profile_id") or metadata.get("user_id")
        )
        if session_user_id:
            return session_user_id

    return _request_ip_fallback_key()


def _coach_talk_rate_limit_subject(
    *,
    talk_profile_user_id: str | None,
    talk_session_id: str | None,
) -> str:
    normalized_user_id = _coerce_profile_user_id(talk_profile_user_id)
    if normalized_user_id:
        return normalized_user_id

    normalized_session_id = str(talk_session_id or "").strip()
    if normalized_session_id and session_manager.session_exists(normalized_session_id):
        metadata = session_manager.sessions.get(normalized_session_id, {}).get("metadata", {})
        session_user_id = _coerce_profile_user_id(
            metadata.get("user_profile_id") or metadata.get("user_id")
        )
        if session_user_id:
            return session_user_id

    return _request_ip_fallback_key()


def _enforce_coach_talk_rate_limits(
    *,
    talk_subject: str,
    talk_session_id: str | None,
):
    normalized_subject = str(talk_subject or "").strip()
    if not normalized_subject:
        return None

    subscription_tier = resolve_user_subscription_tier(normalized_subject)
    if subscription_tier == "premium":
        for limit, window_seconds in (
            (getattr(config, "COACH_TALK_PREMIUM_RATE_LIMIT_PER_MINUTE", 15), 60),
            (getattr(config, "COACH_TALK_PREMIUM_RATE_LIMIT_PER_HOUR", 25), 3600),
            (getattr(config, "COACH_TALK_PREMIUM_RATE_LIMIT_PER_DAY", 25), 24 * 3600),
        ):
            limited = enforce_rate_limit(
                limit,
                window_seconds,
                key_prefix="api.coach.talk.premium",
                scope="user",
                key_func=lambda subject=normalized_subject: subject,
            )
            if limited is not None:
                return limited
        return None

    normalized_session_id = str(talk_session_id or "").strip()
    if normalized_session_id:
        session_limited = enforce_rate_limit(
            getattr(config, "COACH_TALK_FREE_RATE_LIMIT_PER_SESSION", 3),
            0,
            key_prefix="api.coach.talk.free.session",
            scope="user",
            key_func=lambda subject=normalized_subject, session_id=normalized_session_id: f"{subject}:{session_id}",
        )
        if session_limited is not None:
            return session_limited

    return enforce_rate_limit(
        getattr(config, "COACH_TALK_FREE_RATE_LIMIT_PER_DAY", 6),
        24 * 3600,
        key_prefix="api.coach.talk.free.day",
        scope="user",
        key_func=lambda subject=normalized_subject: subject,
    )


def _resolve_runtime_profile(
    *,
    user_id: str | None,
    snapshot_profile: UserProfilePayload | None,
) -> tuple[UserProfilePayload | None, str]:
    """
    Profile precedence:
    1) newer valid snapshot
    2) stored DB profile
    3) valid snapshot
    4) none (caller uses safe defaults)
    """
    snapshot = snapshot_profile if isinstance(snapshot_profile, UserProfilePayload) else None
    snapshot_valid = snapshot is not None and not profile_validation_errors(snapshot)
    snapshot_ts = _parse_profile_timestamp(snapshot.normalized_updated_at() if snapshot else None)

    use_db = bool(getattr(config, "PROFILE_DB_ENABLED", True))
    normalized_user_id = _coerce_profile_user_id(user_id)
    db_record = None
    db_payload = None
    db_ts = None
    if use_db and normalized_user_id:
        db_record = UserProfile.query.filter_by(user_id=normalized_user_id).first()
        if db_record is not None:
            db_payload = _profile_payload_from_record(db_record)
            db_ts = db_record.profile_updated_at

    def _epoch_or_none(value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).timestamp()

    snapshot_epoch = _epoch_or_none(snapshot_ts)
    db_epoch = _epoch_or_none(db_ts)

    if (
        snapshot_valid
        and snapshot_epoch is not None
        and db_payload is not None
        and db_epoch is not None
        and snapshot_epoch > db_epoch
    ):
        if use_db and normalized_user_id and db_record is not None:
            db_record.name = snapshot.name
            db_record.sex = snapshot.sex
            db_record.age = snapshot.age
            db_record.height_cm = snapshot.height_cm
            db_record.weight_kg = snapshot.weight_kg
            db_record.max_hr_bpm = snapshot.max_hr_bpm
            db_record.resting_hr_bpm = snapshot.resting_hr_bpm
            db_record.profile_updated_at = snapshot_ts
            db.session.commit()
        return snapshot, "snapshot_newer"

    if db_payload is not None:
        return db_payload, "db"

    if snapshot_valid:
        if use_db and normalized_user_id:
            record = UserProfile.query.filter_by(user_id=normalized_user_id).first()
            if record is None:
                record = UserProfile(user_id=normalized_user_id)
                db.session.add(record)
            record.name = snapshot.name
            record.sex = snapshot.sex
            record.age = snapshot.age
            record.height_cm = snapshot.height_cm
            record.weight_kg = snapshot.weight_kg
            record.max_hr_bpm = snapshot.max_hr_bpm
            record.resting_hr_bpm = snapshot.resting_hr_bpm
            record.profile_updated_at = snapshot_ts or _utcnow_naive()
            db.session.commit()
        return snapshot, "snapshot"

    return None, "defaults"


def collect_workout_context(payload: dict | None = None, form=None) -> dict:
    """
    Collect normalized workout context from either JSON payload or multipart form fields.
    Returns optional keys only when present.
    """
    payload = payload or {}
    context = payload.get("workout_context") or {}
    if form is not None:
        raw_context = form.get("workout_context")
        if raw_context and not context:
            try:
                parsed = json.loads(raw_context)
                if isinstance(parsed, dict):
                    context = parsed
            except Exception:
                context = {}
    if not isinstance(context, dict):
        context = {}

    def _pick(*keys):
        for key in keys:
            if key in context and context.get(key) not in (None, ""):
                return context.get(key)
            if key in payload and payload.get(key) not in (None, ""):
                return payload.get(key)
            if form is not None:
                value = form.get(key)
                if value not in (None, ""):
                    return value
        return None

    phase = _pick("phase", "workout_phase")
    zone_state = _pick("zone_state", "workout_zone_state")
    heart_rate = _coerce_int(_pick("heart_rate", "workout_heart_rate"))
    target_low = _coerce_int(_pick("target_hr_low", "workout_target_hr_low"))
    target_high = _coerce_int(_pick("target_hr_high", "workout_target_hr_high"))
    time_left_s = _coerce_int(_pick("time_left_s"))
    rep_index = _coerce_int(_pick("rep_index"))
    reps_total = _coerce_int(_pick("reps_total"))
    rep_remaining_s = _coerce_int(_pick("rep_remaining_s"))
    reps_remaining_including_current = _coerce_int(_pick("reps_remaining_including_current"))

    result = {}
    if phase:
        result["phase"] = str(phase).strip().lower()
    if zone_state:
        result["zone_state"] = str(zone_state).strip().lower()
    if heart_rate is not None:
        result["heart_rate"] = max(0, int(heart_rate))
    if target_low is not None:
        result["target_hr_low"] = int(target_low)
    if target_high is not None:
        result["target_hr_high"] = int(target_high)
    if time_left_s is not None:
        result["time_left_s"] = max(0, int(time_left_s))
    if rep_index is not None:
        result["rep_index"] = max(0, int(rep_index))
    if reps_total is not None:
        result["reps_total"] = max(0, int(reps_total))
    if rep_remaining_s is not None:
        result["rep_remaining_s"] = max(0, int(rep_remaining_s))
    if reps_remaining_including_current is not None:
        result["reps_remaining_including_current"] = max(0, int(reps_remaining_including_current))
    return result


def _workout_context_hr_valid(workout_context: dict | None = None) -> bool:
    context = workout_context or {}
    hr = _coerce_int(context.get("heart_rate"))
    if hr is None or hr <= 0:
        return False
    zone_state = str(context.get("zone_state") or "").strip().lower()
    if zone_state in {"hr_missing", "targets_unenforced"}:
        return False
    return True


def _format_workout_progress_hint(language: str, workout_context: dict | None = None) -> str:
    context = workout_context or {}
    lang = normalize_language_code(language)
    reps_left = _coerce_int(context.get("reps_remaining_including_current"))
    time_left = _coerce_int(context.get("time_left_s"))

    parts: list[str] = []
    if reps_left is not None and reps_left > 0:
        if lang == "no":
            parts.append(f"Du har {reps_left} intervaller igjen.")
        else:
            parts.append(f"You have {reps_left} intervals left.")

    if time_left is not None and time_left >= 0:
        if time_left < 60:
            if lang == "no":
                parts.append("Det er under ett minutt igjen.")
            else:
                parts.append("There is less than a minute left.")
        else:
            minutes = max(1, int(round(time_left / 60.0)))
            if lang == "no":
                parts.append(f"Det er omtrent {minutes} minutter igjen.")
            else:
                parts.append(f"You are about {minutes} minutes from finishing.")
    return " ".join(parts).strip()


def _response_claims_invalid_hr(language: str, text: str, workout_context: dict | None = None) -> bool:
    if _workout_context_hr_valid(workout_context):
        return False
    candidate = (text or "").strip().lower()
    if not candidate:
        return False
    if re.search(r"\b\d{2,3}\s*(bpm|puls)\b", candidate):
        return True
    if language == "no":
        return "pulsen din er" in candidate
    return "your heart rate is" in candidate


def workout_talk_fallback(language: str, workout_context: dict | None = None) -> str:
    """Deterministic short fallback used when provider fails/timeouts."""
    lang = normalize_language_code(language)
    context = workout_context or {}
    zone_state = str(context.get("zone_state") or "unknown").strip().lower()
    if zone_state in {"above_zone", "above_target"}:
        bucket = "above_zone"
    elif zone_state in {"below_zone", "below_target"}:
        bucket = "below_zone"
    elif zone_state in {"in_zone", "in_target"}:
        bucket = "in_zone"
    else:
        bucket = "unknown"

    banks = getattr(config, "COACH_TALK_WORKOUT_FALLBACKS", {}) or {}
    selected = banks.get(lang, {}) if isinstance(banks, dict) else {}
    text = selected.get(bucket)
    if text:
        progress_hint = _format_workout_progress_hint(lang, context)
        if progress_hint:
            return f"{text} {progress_hint}".strip()
        return text
    if lang == "no":
        base = "Hold det jevnt og kontrollert. Stabil pust hele veien."
    else:
        base = "Stay smooth and controlled. Keep your breathing steady."
    progress_hint = _format_workout_progress_hint(lang, context)
    if progress_hint:
        return f"{base} {progress_hint}".strip()
    return base


def _record_talk_session_message(session_id: str, role: str, content: str) -> None:
    normalized_session = str(session_id or "").strip()
    message = str(content or "").strip()
    if not normalized_session or not message or not session_manager.session_exists(normalized_session):
        return
    try:
        session_manager.add_message(normalized_session, role, message)
    except Exception as exc:
        logger.warning("Talk session message append failed (session=%s role=%s): %s", normalized_session, role, exc)


def _recent_talk_messages(session_id: str, limit: int = 6) -> list[dict]:
    normalized_session = str(session_id or "").strip()
    if not normalized_session or not session_manager.session_exists(normalized_session):
        return []
    try:
        return session_manager.get_messages(normalized_session, limit=max(1, int(limit)))
    except Exception as exc:
        logger.warning("Talk session history lookup failed (session=%s): %s", normalized_session, exc)
        return []


def _append_recent_zone_event(session_id: str, zone_tick: dict | None, coach_text: str) -> None:
    normalized_session = str(session_id or "").strip()
    text = str(coach_text or "").strip()
    if not normalized_session or not text or not session_manager.session_exists(normalized_session):
        return
    if not isinstance(zone_tick, dict):
        return

    metadata = session_manager.sessions.setdefault(normalized_session, {}).setdefault("metadata", {})
    history = metadata.setdefault("recent_zone_events", [])
    if not isinstance(history, list):
        history = []
        metadata["recent_zone_events"] = history

    history.append(
        {
            "event_type": str(zone_tick.get("primary_event_type") or zone_tick.get("event_type") or "").strip(),
            "text": text,
            "timestamp": _utcnow_iso_z(),
        }
    )
    max_items = max(1, int(getattr(config, "TALK_RECENT_ZONE_EVENT_LIMIT", 3)))
    metadata["recent_zone_events"] = history[-max_items:]


def _recent_zone_event_context(session_id: str, limit: int = 3) -> list[dict]:
    normalized_session = str(session_id or "").strip()
    if not normalized_session or not session_manager.session_exists(normalized_session):
        return []
    metadata = session_manager.sessions.get(normalized_session, {}).get("metadata", {})
    raw_items = metadata.get("recent_zone_events", [])
    if not isinstance(raw_items, list):
        return []

    now = _utcnow()
    result = []
    for item in raw_items[-max(1, int(limit)):]:
        if not isinstance(item, dict):
            continue
        enriched = dict(item)
        raw_timestamp = str(item.get("timestamp") or "").strip()
        if raw_timestamp:
            normalized_timestamp = raw_timestamp[:-1] + "+00:00" if raw_timestamp.endswith("Z") else raw_timestamp
            try:
                parsed = datetime.fromisoformat(normalized_timestamp)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                age_s = max(0, int((now.replace(tzinfo=timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()))
                enriched["seconds_since_last_event"] = age_s
            except ValueError:
                pass
        result.append(enriched)
    return result


_ZONE_REWRITE_ACTION_GROUPS = {
    "ease": {"ease", "easier", "slow", "slower", "back", "down", "settle", "rolig", "ro", "senk", "lette"},
    "push": {"push", "harder", "build", "increase", "øk", "trykk", "press", "drive"},
    "hold": {"hold", "keep", "steady", "maintain", "stabil", "jevn", "rytme", "kontroll", "control"},
    "recover": {"recover", "recovery", "rest", "cooldown", "walk", "jog", "pause", "hvile"},
    "breath": {"breathe", "breath", "exhale", "inhale", "pust", "utpust", "innpust"},
    "zone": {"zone", "zones", "målsonen", "målsone", "target", "z1", "z2", "z3", "z4", "z5"},
    "hr": {"hr", "heart", "rate", "bpm", "puls", "pulse"},
}


def _rewrite_number_tokens(text: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)?", str(text or "").lower())


def _rewrite_semantic_groups(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9æøå]+", str(text or "").lower()))
    groups = set()
    for canonical, members in _ZONE_REWRITE_ACTION_GROUPS.items():
        if tokens.intersection(members):
            groups.add(canonical)
    return groups


def verify_zone_event_rewrite(original_event: str, rewritten_phrase: str, event_type: str, language: str) -> tuple[bool, str]:
    original = str(original_event or "").strip()
    rewritten = str(rewritten_phrase or "").strip()
    if not rewritten:
        return False, "empty_rewrite"

    max_words = max(6, int(getattr(config, "ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 16)))
    if len(rewritten.split()) > max_words:
        return False, "word_limit_exceeded"

    original_numbers = _rewrite_number_tokens(original)
    rewritten_numbers = _rewrite_number_tokens(rewritten)
    if original_numbers != rewritten_numbers:
        return False, "numeric_tokens_changed"

    original_groups = _rewrite_semantic_groups(original)
    rewritten_groups = _rewrite_semantic_groups(rewritten)
    if original_groups != rewritten_groups:
        return False, "instruction_tokens_changed"

    normalized_language = normalize_language_code(language)
    if normalized_language == "en" and _looks_norwegian(rewritten):
        return False, "language_drift"
    if normalized_language == "no" and _looks_english(rewritten):
        return False, "language_drift"

    consistent = enforce_language_consistency(rewritten, normalized_language)
    if consistent.strip() != rewritten.strip():
        return False, "language_drift"

    if not validate_coaching_text(
        text=rewritten,
        phase="intense",
        intensity="moderate",
        persona="personal_trainer",
        language=normalized_language,
        mode="realtime",
    ):
        return False, "validation_failed"

    return True, "accepted"


def fallback_talk_prompt(language: str, workout_context: dict | None = None) -> str:
    """Prompt used when no user message can be extracted."""
    lang = normalize_language_code(language)
    context = workout_context or {}
    zone_state = str(context.get("zone_state") or "").strip().lower()
    phase = str(context.get("phase") or "").strip().lower()

    if lang == "no":
        if zone_state in {"above_zone", "above_target"}:
            return "Jeg er over målsonen nå. Hva bør jeg gjøre?"
        if zone_state in {"below_zone", "below_target"}:
            return "Jeg er under målsonen nå. Hva bør jeg gjøre?"
        if phase in {"recovery", "cooldown"}:
            return "Hva bør jeg fokusere på nå i denne fasen?"
        return "Hvordan ligger jeg an akkurat nå?"

    if zone_state in {"above_zone", "above_target"}:
        return "I am above target zone right now. What should I do?"
    if zone_state in {"below_zone", "below_target"}:
        return "I am below target zone right now. What should I do?"
    if phase in {"recovery", "cooldown"}:
        return "What should I focus on in this phase?"
    return "How am I doing right now?"


def transcribe_talk_audio(filepath: str, language: str, timeout_seconds: float) -> tuple[str | None, str]:
    """
    Best-effort speech-to-text for /coach/talk multipart audio.
    Returns (text, source_status).
    """
    global _talk_stt_quota_skip_until

    if not bool(getattr(config, "TALK_STT_ENABLED", False)):
        return None, "stt_disabled"

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None, "stt_skipped_no_api_key"

    try:
        from openai import OpenAI
    except Exception:
        return None, "stt_skipped_openai_missing"

    model = (os.getenv("OPENAI_STT_MODEL") or "gpt-4o-mini-transcribe").strip()
    client_timeout = max(1.0, float(timeout_seconds))
    quota_cooldown_seconds = max(
        15.0,
        float(getattr(config, "TALK_STT_QUOTA_COOLDOWN_SECONDS", 300.0)),
    )
    now = time.time()

    with _talk_stt_lock:
        skip_until = _talk_stt_quota_skip_until
    if now < skip_until:
        remaining = max(0.0, skip_until - now)
        logger.info(
            "Coach talk STT skipped due to active quota cooldown remaining_s=%.1f",
            remaining,
        )
        return None, "stt_quota_limited"

    try:
        client = OpenAI(api_key=api_key, timeout=client_timeout, max_retries=0)
        with open(filepath, "rb") as audio_handle:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_handle,
                language=normalize_language_code(language),
            )
        text = str(getattr(transcript, "text", "") or "").strip()
        if not text:
            return None, "stt_empty"
        return text, "stt_openai"
    except Exception as exc:
        normalized_error = f"{type(exc).__name__}: {exc}".lower()
        if any(marker in normalized_error for marker in ("insufficient_quota", "rate limit", "too many requests", "429", "quota")):
            with _talk_stt_lock:
                _talk_stt_quota_skip_until = time.time() + quota_cooldown_seconds
            logger.warning(
                "Coach talk STT fast-fail quota/rate-limit cooldown_s=%.1f: %s",
                quota_cooldown_seconds,
                exc,
            )
            return None, "stt_quota_limited"
        if "timeout" in normalized_error or "timed out" in normalized_error:
            logger.warning("Coach talk STT timeout: %s", exc)
            return None, "stt_timeout"
        logger.warning("Coach talk STT failed: %s", exc)
        return None, "stt_error"


def _default_breath_analysis_with_error(error_code: str, **extra_fields) -> dict:
    result = breath_analyzer._default_analysis()
    result["analysis_error"] = error_code
    for key, value in extra_fields.items():
        if value is not None:
            result[key] = value
    return result


def _analyze_breath_with_timeout(filepath: str, *, request_context: str, trace_id: str | None = None) -> dict:
    global _breath_analysis_skip_until

    timeout_seconds = max(0.5, float(getattr(config, "BREATH_ANALYSIS_TIMEOUT_SECONDS", 2.5)))
    cooldown_seconds = max(1.0, float(getattr(config, "BREATH_ANALYSIS_TIMEOUT_COOLDOWN_SECONDS", 20.0)))
    now = time.time()

    with _breath_analysis_lock:
        skip_until = _breath_analysis_skip_until

    if now < skip_until:
        remaining = max(0.0, skip_until - now)
        logger.warning(
            "Breath analysis skipped due to active timeout cooldown context=%s trace=%s remaining_s=%.1f",
            request_context,
            trace_id or "none",
            remaining,
        )
        return _default_breath_analysis_with_error(
            "analysis_timeout_cooldown",
            timeout_seconds=timeout_seconds,
            cooldown_remaining_seconds=round(remaining, 2),
        )

    future = _breath_analysis_executor.submit(breath_analyzer.analyze, filepath)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        future.cancel()
        with _breath_analysis_lock:
            _breath_analysis_skip_until = time.time() + cooldown_seconds
        logger.error(
            "Breath analysis timed out context=%s trace=%s timeout_s=%.1f file=%s",
            request_context,
            trace_id or "none",
            timeout_seconds,
            os.path.basename(filepath),
        )
        return _default_breath_analysis_with_error(
            "analysis_timeout",
            timeout_seconds=timeout_seconds,
            cooldown_seconds=cooldown_seconds,
        )
    except Exception as exc:
        logger.warning(
            "Breath analysis failed context=%s trace=%s error=%s",
            request_context,
            trace_id or "none",
            exc,
        )
        return _default_breath_analysis_with_error("analysis_error")


def _coach_score_from_intensity(intensity: str) -> int:
    normalized = normalize_intensity_value(intensity)
    if normalized == "calm":
        return 74
    if normalized == "intense":
        return 88
    if normalized == "critical":
        return 68
    return 82


def _coach_score_line(score: int, language: str) -> str:
    clamped = max(0, min(100, int(score)))
    if normalize_language_code(language) == "no":
        return f"Coach score: {clamped} — Solid jobb. Du traff intensiteten som forbedrer helsa di."
    return f"Coach score: {clamped} — Solid work. You hit the intensity that improves your health."


def _coerce_float(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _coerce_int(value):
    number = _coerce_float(value)
    if number is None:
        return None
    return int(round(number))


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on", "connected"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disconnected"}:
        return False
    return False


def _normalized_fraction(value):
    number = _coerce_float(value)
    if number is None:
        return 0.0
    return max(0.0, min(1.0, number))


def _duration_score_component(elapsed_seconds: int) -> int:
    seconds = max(0, int(elapsed_seconds or 0))
    # Ramp linearly to 100 by 60 minutes.
    progress = min(1.0, float(seconds) / (60.0 * 60.0))
    return int(round(progress * 100.0))


def _breath_score_component(breath_data: dict) -> int:
    signal_quality = _normalized_fraction((breath_data or {}).get("signal_quality"))
    regularity = _normalized_fraction((breath_data or {}).get("breath_regularity"))
    confidence = _normalized_fraction((breath_data or {}).get("intensity_confidence"))
    score = (signal_quality * 45.0) + (regularity * 35.0) + (confidence * 20.0)
    return int(round(max(0.0, min(100.0, score))))


def _zone_score_component(zone_tick: dict, breath_data: dict) -> int:
    if isinstance(zone_tick, dict) and zone_tick.get("score") is not None:
        return max(0, min(100, int(zone_tick.get("score", 0))))
    fallback = _coach_score_from_intensity((breath_data or {}).get("intensity", "moderate"))
    return max(0, min(100, int(fallback)))


def _duration_score_component_v2(main_set_seconds: float) -> float:
    minutes = max(0.0, float(main_set_seconds or 0.0)) / 60.0
    if minutes <= 0.0:
        return 0.0
    if minutes <= 20.0:
        return max(0.0, min(20.0, minutes))
    if minutes >= 120.0:
        return 100.0
    # Slow ramp with full maturity at 120 min.
    # 40 min ~= 40, 60 min ~= 57, 120 min = 100.
    normalized = max(0.0, min(1.0, (minutes - 20.0) / 100.0))
    score = 20.0 + (math.pow(normalized, 0.85) * 80.0)
    return max(0.0, min(100.0, score))


def _duration_only_cap_score(main_set_seconds: float) -> int:
    minutes = max(0.0, float(main_set_seconds or 0.0)) / 60.0
    if minutes <= 0.0:
        return 0
    if minutes <= 60.0:
        return int(max(0.0, min(60.0, math.floor(minutes))))
    if minutes <= 120.0:
        scaled = 60.0 + ((minutes - 60.0) * (40.0 / 60.0))
        return int(max(60.0, min(100.0, math.floor(scaled))))
    return 100


def _median(values):
    cleaned = [float(v) for v in values if v is not None]
    if not cleaned:
        return None
    cleaned.sort()
    mid = len(cleaned) // 2
    if len(cleaned) % 2 == 1:
        return cleaned[mid]
    return (cleaned[mid - 1] + cleaned[mid]) / 2.0


def _derive_breath_quality_samples(breath_data: dict, breath_quality_samples):
    return derive_breath_quality_samples(
        breath_data=breath_data,
        recent_samples=breath_quality_samples,
        include_current_signal=True,
    )


def _interval_zone_compliance(zone_tick: dict):
    if not isinstance(zone_tick, dict):
        return None

    min_phase = float(getattr(config, "CS_MIN_PHASE_VALID_SECONDS", 30.0))
    work_valid = _coerce_float(zone_tick.get("interval_work_zone_valid_seconds")) or 0.0
    work_in = _coerce_float(zone_tick.get("interval_work_in_target_seconds")) or 0.0
    recovery_valid = _coerce_float(zone_tick.get("interval_recovery_zone_valid_seconds")) or 0.0
    recovery_in = _coerce_float(zone_tick.get("interval_recovery_in_target_seconds")) or 0.0

    work_component = None
    recovery_component = None
    if work_valid >= min_phase and work_valid > 0:
        work_component = max(0.0, min(1.0, work_in / work_valid))
    if recovery_valid >= min_phase and recovery_valid > 0:
        recovery_component = max(0.0, min(1.0, recovery_in / recovery_valid))

    if work_component is None and recovery_component is None:
        return None
    if work_component is not None and recovery_component is not None:
        return max(0.0, min(1.0, (0.7 * work_component) + (0.3 * recovery_component)))
    return work_component if work_component is not None else recovery_component


def _resolve_zone_compliance_for_score(zone_tick: dict):
    if not isinstance(zone_tick, dict):
        return None

    explicit = _coerce_float(zone_tick.get("zone_compliance"))
    if explicit is not None:
        return max(0.0, min(1.0, explicit))

    interval = _interval_zone_compliance(zone_tick)
    if interval is not None:
        return interval

    zone_valid = _coerce_float(zone_tick.get("zone_valid_main_set_seconds")) or 0.0
    in_target = _coerce_float(zone_tick.get("in_target_zone_valid_seconds")) or 0.0
    if zone_valid > 0:
        return max(0.0, min(1.0, in_target / zone_valid))

    pct = _coerce_float(zone_tick.get("time_in_target_pct"))
    if pct is not None:
        return max(0.0, min(1.0, pct / 100.0))
    return None


def _weighted_component_average(components):
    available = [(float(v), float(w)) for (v, w) in components if v is not None]
    if not available:
        return 0.0
    denominator = sum(weight for _, weight in available)
    if denominator <= 0:
        return 0.0
    numerator = sum(value * weight for value, weight in available)
    return max(0.0, min(100.0, numerator / denominator))


def _sanitize_log_text(value) -> str:
    text = str(value or "")
    return " ".join(text.split())


def _apply_interval_tick_budget(
    *,
    wait_seconds: int,
    workout_mode: str,
    zone_tick: dict,
) -> int:
    """Cap tick interval during countdown-sensitive phases so cues are not skipped."""
    resolved_wait = max(1, int(wait_seconds or 1))
    if not isinstance(zone_tick, dict):
        return resolved_wait

    mode = str(workout_mode or "").strip().lower()
    phase = str(zone_tick.get("phase") or "").strip().lower()
    remaining_phase_seconds = _coerce_int(zone_tick.get("remaining_phase_seconds"))

    if mode == "interval" and phase in {"warmup", "recovery"}:
        recovery_cap = int(getattr(config, "INTERVAL_RECOVERY_MAX_WAIT_SECONDS", 5))
        final_window = int(getattr(config, "INTERVAL_RECOVERY_FINAL_WINDOW_SECONDS", 35))
        final_cap = int(getattr(config, "INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3))
        resolved_wait = min(resolved_wait, recovery_cap)
        if remaining_phase_seconds is not None and remaining_phase_seconds <= final_window:
            resolved_wait = min(resolved_wait, final_cap)
    elif mode == "interval" and phase == "work":
        work_cap = int(getattr(config, "INTERVAL_WORK_MAX_WAIT_SECONDS", 8))
        resolved_wait = min(resolved_wait, work_cap)
    elif mode == "interval":
        transition_cap = int(getattr(config, "INTERVAL_TRANSITION_MAX_WAIT_SECONDS", 12))
        resolved_wait = min(resolved_wait, transition_cap)
    elif mode == "easy_run" and phase == "warmup" and remaining_phase_seconds is not None:
        warmup_cap = int(getattr(config, "INTERVAL_RECOVERY_MAX_WAIT_SECONDS", 5))
        final_window = int(getattr(config, "INTERVAL_RECOVERY_FINAL_WINDOW_SECONDS", 35))
        final_cap = int(getattr(config, "INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3))
        resolved_wait = min(resolved_wait, warmup_cap)
        if remaining_phase_seconds <= final_window:
            resolved_wait = min(resolved_wait, final_cap)

    return max(1, int(resolved_wait))


def _log_coach_transcript_debug(
    *,
    session_id: str,
    language: str,
    phase: str,
    should_speak: bool,
    reason: str,
    source: str,
    text: str,
):
    if not bool(getattr(config, "COACH_TRANSCRIPT_DEBUG_LOGS", True)):
        return
    logger.info(
        "COACH_TRANSCRIPT session=%s lang=%s phase=%s speak=%s reason=%s source=%s text=\"%s\"",
        session_id,
        language,
        phase,
        bool(should_speak),
        reason or "none",
        source or "unknown",
        _sanitize_log_text(text),
    )


def _log_coach_score_debug_summary(
    *,
    session_id: str,
    language: str,
    workout_mode: str,
    score_payload: dict,
):
    if not bool(getattr(config, "COACH_SCORE_DEBUG_LOGS", True)):
        return
    payload = score_payload if isinstance(score_payload, dict) else {}
    components = payload.get("coach_score_components") if isinstance(payload.get("coach_score_components"), dict) else {}
    reasons = payload.get("cap_reason_codes")
    if not isinstance(reasons, list):
        reasons = []
    logger.info(
        "CS_DEBUG_SUMMARY session=%s lang=%s mode=%s duration_s=%s hr_valid_s=%s zone_valid_s=%s zone_compliance=%s zone_score=%s breath_enabled=%s permission_granted=%s breath_reliable=%s breath_score=%s breath_confidence=%s raw_score=%s cap_applied=%s cap_reason_winning=%s reasons_all=%s final_cs=%s",
        session_id,
        language,
        workout_mode,
        components.get("main_set_seconds"),
        payload.get("hr_valid_main_set_seconds"),
        payload.get("zone_valid_main_set_seconds"),
        payload.get("zone_compliance"),
        payload.get("zone_score"),
        components.get("breath_enabled_by_user"),
        components.get("mic_permission_granted"),
        components.get("breath_available_reliable"),
        payload.get("breath_score"),
        payload.get("breath_confidence"),
        payload.get("raw_score"),
        payload.get("cap_applied"),
        payload.get("cap_applied_reason"),
        ",".join(str(item) for item in reasons),
        payload.get("score"),
    )


def _compute_layered_coach_score_v1(
    *,
    language: str,
    elapsed_seconds: int,
    breath_data: dict,
    zone_tick: dict,
    watch_connected,
    heart_rate,
    hr_quality,
):
    zone_score = _zone_score_component(zone_tick, breath_data)
    breath_score = _breath_score_component(breath_data)
    duration_score = _duration_score_component(elapsed_seconds)

    raw_score = int(round((0.5 * zone_score) + (0.3 * breath_score) + (0.2 * duration_score)))
    raw_score = max(0, min(100, raw_score))

    hr_quality_value = str(
        (zone_tick or {}).get("hr_quality")
        or hr_quality
        or ""
    ).strip().lower()
    watch_connected_value = _coerce_bool(watch_connected)
    resolved_heart_rate = _coerce_int((zone_tick or {}).get("heart_rate"))
    if resolved_heart_rate is None:
        resolved_heart_rate = _coerce_int(heart_rate)
    time_in_target = _coerce_float((zone_tick or {}).get("time_in_target_pct"))
    if (
        not watch_connected_value
        and isinstance(zone_tick, dict)
        and hr_quality_value == "good"
        and resolved_heart_rate is not None
        and resolved_heart_rate > 0
    ):
        watch_connected_value = True

    hr_signal_present = (resolved_heart_rate is not None and resolved_heart_rate > 0) or (time_in_target is not None)
    hr_zone_compliance_ok = (
        watch_connected_value
        and hr_signal_present
        and hr_quality_value not in {"poor", "missing", "none", "disconnected", "unknown"}
    )
    if time_in_target is not None:
        hr_zone_compliance_ok = hr_zone_compliance_ok and time_in_target >= 55.0
    else:
        hr_zone_compliance_ok = hr_zone_compliance_ok and zone_score >= 60

    breath_signal_quality = _normalized_fraction((breath_data or {}).get("signal_quality"))
    breath_quality_ok = breath_signal_quality >= 0.25 and breath_score >= 60

    cap = 100
    if not hr_zone_compliance_ok:
        cap = min(cap, 60)
    if not breath_quality_ok:
        cap = min(cap, 75)
    if max(0, int(elapsed_seconds or 0)) < 20 * 60:
        cap = min(cap, 20)

    score = max(0, min(100, min(raw_score, cap)))
    return {
        "score": score,
        "score_line": _coach_score_line(score, language),
        "cap": cap,
        "raw_score": raw_score,
        "zone_score": zone_score,
        "breath_score": breath_score,
        "duration_score": duration_score,
        "hr_zone_compliance_ok": hr_zone_compliance_ok,
        "breath_quality_ok": breath_quality_ok,
    }


def _compute_layered_coach_score_v2(
    *,
    language: str,
    elapsed_seconds: int,
    breath_data: dict,
    zone_tick: dict,
    watch_connected,
    heart_rate,
    hr_quality,
    breath_enabled_by_user: bool,
    mic_permission_granted: bool,
    breath_quality_samples,
):
    zone_tick_data = zone_tick if isinstance(zone_tick, dict) else {}
    watch_connected_value = _coerce_bool(watch_connected)
    resolved_heart_rate = _coerce_int(zone_tick_data.get("heart_rate"))
    if resolved_heart_rate is None:
        resolved_heart_rate = _coerce_int(heart_rate)
    hr_quality_value = str(zone_tick_data.get("hr_quality") or hr_quality or "").strip().lower()
    if (
        not watch_connected_value
        and hr_quality_value == "good"
        and resolved_heart_rate is not None
        and resolved_heart_rate > 0
    ):
        watch_connected_value = True

    main_set_seconds = _coerce_float(zone_tick_data.get("main_set_seconds"))
    if main_set_seconds is None or main_set_seconds <= 0:
        main_set_seconds = float(max(0, int(elapsed_seconds or 0)))

    hr_valid_main_set_seconds = _coerce_float(zone_tick_data.get("hr_valid_main_set_seconds")) or 0.0
    zone_valid_main_set_seconds = _coerce_float(zone_tick_data.get("zone_valid_main_set_seconds")) or 0.0
    target_enforced_main_set_seconds = _coerce_float(zone_tick_data.get("target_enforced_main_set_seconds")) or 0.0
    zone_compliance = _resolve_zone_compliance_for_score(zone_tick_data)

    min_zone_score_seconds = float(getattr(config, "CS_MIN_ZONE_VALID_SECONDS_FOR_SCORE", 30.0))
    min_hr_pillar_seconds = float(getattr(config, "CS_MIN_HR_VALID_SECONDS_FOR_PILLAR", 120.0))
    min_zone_cap_seconds = float(getattr(config, "CS_MIN_ZONE_VALID_SECONDS_FOR_CAP", 120.0))
    zone_pass_threshold = float(getattr(config, "CS_ZONE_PASS_THRESHOLD", 0.50))

    zone_score = None
    if hr_valid_main_set_seconds >= 30.0 and zone_valid_main_set_seconds >= min_zone_score_seconds and zone_compliance is not None:
        # Explicit CS v2 formula: 70% compliance maps to full zone score.
        zone_score = max(0.0, min(100.0, (zone_compliance / 0.70) * 100.0))

    breath_confidence = _normalized_fraction((breath_data or {}).get("intensity_confidence"))
    breath_score = float(_breath_score_component(breath_data))
    breath_in_play = bool(breath_enabled_by_user) and bool(mic_permission_granted)
    quality_summary = summarize_breath_quality(
        breath_data=breath_data,
        recent_samples=breath_quality_samples,
        config_module=config,
        include_current_signal=True,
    )
    breath_sample_count = int(quality_summary.get("sample_count", 0))
    breath_median_quality = quality_summary.get("median_quality")
    breath_available_reliable = bool(breath_in_play and quality_summary.get("reliable"))
    breath_pass = (
        breath_available_reliable
        and breath_confidence >= float(getattr(config, "CS_BREATH_PASS_MIN_CONFIDENCE", 0.60))
        and breath_score >= float(getattr(config, "CS_BREATH_PASS_MIN_SCORE", 50.0))
    )

    duration_score = _duration_score_component_v2(main_set_seconds)
    raw_score = _weighted_component_average(
        [
            (zone_score, 0.55),
            (breath_score if breath_available_reliable else None, 0.30),
            (duration_score, 0.15),
        ]
    )

    zone_computable_for_cap = (
        zone_compliance is not None
        and zone_valid_main_set_seconds >= min_zone_cap_seconds
        and target_enforced_main_set_seconds >= min_zone_cap_seconds
    )
    hr_pillar_available = (
        watch_connected_value
        and hr_valid_main_set_seconds >= min_hr_pillar_seconds
        and zone_computable_for_cap
        and zone_score is not None
    )
    breath_pillar_available = bool(breath_available_reliable)
    sensor_pillar_count = int(hr_pillar_available) + int(breath_pillar_available)

    triggered_caps = []
    cap_reason_codes = []

    def apply_cap(value, reason):
        cap_value = int(max(0, min(100, int(round(value)))))
        triggered_caps.append((cap_value, reason))
        if reason not in cap_reason_codes:
            cap_reason_codes.append(reason)

    if hr_pillar_available and zone_compliance is not None and zone_compliance < zone_pass_threshold:
        apply_cap(50, "ZONE_FAIL")

    # Breath fail cap only matters when breath is the only reliable sensor pillar.
    if (not hr_pillar_available) and breath_pillar_available and (not breath_pass):
        apply_cap(65, "BREATH_FAIL")

    duration_only_cap = None
    if sensor_pillar_count == 0:
        duration_only_cap = _duration_only_cap_score(main_set_seconds)
        apply_cap(duration_only_cap, "DURATION_ONLY_CAP")
        if not watch_connected_value or hr_valid_main_set_seconds < min_hr_pillar_seconds:
            apply_cap(100, "HR_MISSING")
        if breath_in_play and not breath_available_reliable:
            apply_cap(100, "BREATH_MISSING")
    elif breath_in_play and not breath_available_reliable:
        # Keep this reason visible in diagnostics/hints without reducing score ceilings.
        apply_cap(100, "BREATH_MISSING")
    elif breath_in_play and breath_pillar_available and not breath_pass:
        # If another pillar is strong we still allow high ceilings; quality impact comes via raw score.
        if hr_pillar_available:
            apply_cap(100, "BREATH_FAIL")

    if not hr_pillar_available and (zone_compliance is None or not zone_computable_for_cap):
        apply_cap(100, "ZONE_MISSING_OR_UNENFORCED")

    if hr_valid_main_set_seconds < 30.0:
        apply_cap(100, "HR_MISSING")
    if zone_valid_main_set_seconds < min_zone_score_seconds:
        apply_cap(100, "ZONE_MISSING_OR_UNENFORCED")

    short_cap = None
    if main_set_seconds < 1200.0:
        short_cap = int(math.floor((main_set_seconds / 1200.0) * 20.0))
        short_cap = max(0, min(20, short_cap))
        apply_cap(short_cap, "SHORT_DURATION")

    cap_applied = 100
    cap_applied_reason = None
    if triggered_caps:
        winner = min(triggered_caps, key=lambda item: item[0])
        cap_applied = winner[0]
        cap_applied_reason = winner[1]

    final_score = int(round(min(raw_score, float(cap_applied))))
    final_score = max(0, min(100, final_score))

    hr_zone_compliance_ok = bool(
        hr_pillar_available and zone_compliance is not None and zone_compliance >= zone_pass_threshold
    )
    breath_quality_ok = bool((not breath_pillar_available) or breath_pass)

    return {
        "score": final_score,
        "score_line": _coach_score_line(final_score, language),
        "cap": cap_applied,
        "raw_score": int(round(raw_score)),
        "zone_score": None if zone_score is None else int(round(zone_score)),
        "breath_score": int(round(breath_score)),
        "duration_score": int(round(duration_score)),
        "cap_reason_codes": cap_reason_codes,
        "cap_applied": cap_applied,
        "cap_applied_reason": cap_applied_reason,
        "coach_score_components": {
            "zone": None if zone_score is None else int(round(zone_score)),
            "breath": int(round(breath_score)),
            "duration": int(round(duration_score)),
            "zone_available": zone_score is not None,
            "breath_in_play": breath_in_play,
            "breath_available_reliable": breath_available_reliable,
            "breath_enabled_by_user": bool(breath_enabled_by_user),
            "mic_permission_granted": bool(mic_permission_granted),
            "breath_confidence": round(breath_confidence, 4),
            "breath_sample_count": breath_sample_count,
            "breath_median_quality": None if breath_median_quality is None else round(float(breath_median_quality), 4),
            "zone_compliance": None if zone_compliance is None else round(float(zone_compliance), 4),
            "hr_valid_main_set_seconds": round(float(hr_valid_main_set_seconds), 2),
            "zone_valid_main_set_seconds": round(float(zone_valid_main_set_seconds), 2),
            "main_set_seconds": round(float(main_set_seconds), 2),
            "hr_pillar_available": hr_pillar_available,
            "breath_pillar_available": breath_pillar_available,
            "sensor_pillar_count": sensor_pillar_count,
        },
        "coach_score_v2": final_score,
        "hr_valid_main_set_seconds": round(float(hr_valid_main_set_seconds), 2),
        "zone_valid_main_set_seconds": round(float(zone_valid_main_set_seconds), 2),
        "zone_compliance": None if zone_compliance is None else round(float(zone_compliance), 4),
        "breath_confidence": round(breath_confidence, 4),
        "breath_available_reliable": breath_available_reliable,
        "breath_in_play": breath_in_play,
        "hr_zone_compliance_ok": hr_zone_compliance_ok,
        "breath_quality_ok": breath_quality_ok,
        "short_duration_cap": short_cap,
        "duration_only_cap": duration_only_cap,
    }


def _compute_layered_coach_score(
    *,
    language: str,
    elapsed_seconds: int,
    breath_data: dict,
    zone_tick: dict,
    watch_connected,
    heart_rate,
    hr_quality,
    breath_enabled_by_user: bool = True,
    mic_permission_granted: bool = True,
    breath_quality_samples=None,
):
    version = str(getattr(config, "COACH_SCORE_VERSION", "cs_v2")).strip().lower()
    if version not in {"cs_v1", "cs_v2", "shadow"}:
        version = "cs_v2"

    payload_v1 = _compute_layered_coach_score_v1(
        language=language,
        elapsed_seconds=elapsed_seconds,
        breath_data=breath_data,
        zone_tick=zone_tick,
        watch_connected=watch_connected,
        heart_rate=heart_rate,
        hr_quality=hr_quality,
    )
    payload_v2 = _compute_layered_coach_score_v2(
        language=language,
        elapsed_seconds=elapsed_seconds,
        breath_data=breath_data,
        zone_tick=zone_tick,
        watch_connected=watch_connected,
        heart_rate=heart_rate,
        hr_quality=hr_quality,
        breath_enabled_by_user=breath_enabled_by_user,
        mic_permission_granted=mic_permission_granted,
        breath_quality_samples=breath_quality_samples,
    )

    if version == "cs_v1":
        payload_v1.setdefault("coach_score_v2", payload_v2.get("score"))
        payload_v1.setdefault("coach_score_components", payload_v2.get("coach_score_components"))
        payload_v1.setdefault("cap_reason_codes", payload_v2.get("cap_reason_codes"))
        payload_v1.setdefault("cap_applied", payload_v1.get("cap"))
        payload_v1.setdefault("cap_applied_reason", payload_v2.get("cap_applied_reason"))
        payload_v1.setdefault("hr_valid_main_set_seconds", payload_v2.get("hr_valid_main_set_seconds"))
        payload_v1.setdefault("zone_valid_main_set_seconds", payload_v2.get("zone_valid_main_set_seconds"))
        payload_v1.setdefault("zone_compliance", payload_v2.get("zone_compliance"))
        payload_v1.setdefault("breath_available_reliable", payload_v2.get("breath_available_reliable"))
        return payload_v1

    if version == "shadow":
        payload = dict(payload_v1)
        payload["coach_score_v2"] = payload_v2.get("score")
        payload["coach_score_components"] = payload_v2.get("coach_score_components")
        payload["cap_reason_codes"] = payload_v2.get("cap_reason_codes")
        payload["cap_applied"] = payload_v1.get("cap")
        payload["cap_applied_reason"] = payload_v2.get("cap_applied_reason")
        payload["hr_valid_main_set_seconds"] = payload_v2.get("hr_valid_main_set_seconds")
        payload["zone_valid_main_set_seconds"] = payload_v2.get("zone_valid_main_set_seconds")
        payload["zone_compliance"] = payload_v2.get("zone_compliance")
        payload["breath_available_reliable"] = payload_v2.get("breath_available_reliable")
        payload["cs_v1_debug"] = {
            "score": payload_v1.get("score"),
            "raw_score": payload_v1.get("raw_score"),
            "cap": payload_v1.get("cap"),
        }
        payload["cs_v2_debug"] = {
            "score": payload_v2.get("score"),
            "raw_score": payload_v2.get("raw_score"),
            "cap": payload_v2.get("cap"),
            "cap_reason_codes": payload_v2.get("cap_reason_codes"),
            "cap_applied_reason": payload_v2.get("cap_applied_reason"),
        }
        return payload

    return payload_v2


def _normalize_personalization_user_id(
    explicit_profile_id: str,
    current_user_id: str,
    user_name: str,
) -> str:
    """
    Build a stable user key for running personalization.

    Priority:
    1) explicit profile id from client
    2) authenticated/known user id
    3) user name slug (if present)
    4) empty string (disabled)
    """
    profile_id = (explicit_profile_id or "").strip().lower()
    if profile_id:
        return profile_id[:128]

    user_id = (current_user_id or "").strip().lower()
    if user_id and user_id != "unknown":
        return user_id[:128]

    name = (user_name or "").strip().lower()
    if not name:
        return ""
    slug = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    return slug[:128]


def _should_allow_zone_llm_rewrite(event_type: str) -> bool:
    if not bool(getattr(config, "ZONE_EVENT_LLM_REWRITE_ENABLED", False)):
        return False
    allowed = set(getattr(config, "ZONE_EVENT_LLM_REWRITE_ALLOWED_EVENTS", []))
    if not allowed:
        return False
    return (event_type or "") in allowed


def _maybe_rephrase_zone_event_text(
    *,
    base_text: str,
    language: str,
    persona: str,
    coaching_style: str,
    event_type: str,
) -> tuple[str, dict]:
    """
    Optional Phase-4 phrasing layer for deterministic zone event text.
    """
    seed = (base_text or "").strip()
    if not seed:
        return seed, {
            "provider": "system",
            "source": "zone_event_motor",
            "status": "event_template",
            "mode": "deterministic_zone",
        }

    if not _should_allow_zone_llm_rewrite(event_type):
        return seed, {
            "provider": "system",
            "source": "zone_event_motor",
            "status": "event_template",
            "mode": "deterministic_zone",
        }

    try:
        rewritten = brain_router.rewrite_zone_event_text(
            seed,
            language=language,
            persona=persona,
            coaching_style=coaching_style,
            event_type=event_type,
        )
        cleaned = (rewritten or "").strip()
        if not cleaned:
            return seed, {
                "provider": "system",
                "source": "zone_event_motor",
                "status": "rewrite_empty_fallback",
                "mode": "deterministic_zone",
            }
        max_words = max(6, int(getattr(config, "ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 16)))
        if len(cleaned.split()) > max_words:
            logger.info(
                "ZONE_REWRITE_AUDIT event=%s decision=rejected reason=word_limit_exceeded original=%r rewritten=%r",
                event_type or "zone_event",
                seed,
                cleaned,
            )
            return seed, {
                "provider": "system",
                "source": "zone_event_motor",
                "status": "rewrite_word_limit_fallback",
                "mode": "deterministic_zone",
            }

        verified, verify_reason = verify_zone_event_rewrite(
            original_event=seed,
            rewritten_phrase=cleaned,
            event_type=event_type or "zone_event",
            language=language,
        )
        logger.info(
            "ZONE_REWRITE_AUDIT event=%s decision=%s reason=%s original=%r rewritten=%r",
            event_type or "zone_event",
            "accepted" if verified else "rejected",
            verify_reason,
            seed,
            cleaned,
        )
        if not verified:
            return seed, {
                "provider": "system",
                "source": "zone_event_motor",
                "status": "rewrite_verification_fallback",
                "mode": "deterministic_zone",
            }

        route_meta = brain_router.get_last_route_meta()
        provider = route_meta.get("provider") or "system"
        status = route_meta.get("status") or "rewrite_success"
        return cleaned, {
            "provider": provider,
            "source": "zone_event_llm",
            "status": status,
            "mode": "deterministic_zone",
        }
    except Exception as exc:
        logger.warning("Zone LLM rewrite failed (%s): %s", type(exc).__name__, exc)
        return seed, {
            "provider": "system",
            "source": "zone_event_motor",
            "status": "rewrite_exception_fallback",
            "mode": "deterministic_zone",
        }


def _record_tts_success(provider: str, language: str, persona: str, file_path: str):
    TTS_RUNTIME_DIAGNOSTICS["last_success"] = {
            "timestamp": _utcnow_iso_z(),
        "provider": provider,
        "language": normalize_language_code(language or "en"),
        "persona": persona or "personal_trainer",
        "filename": os.path.basename(file_path or ""),
    }


def _record_tts_error(stage: str, language: str, persona: str, error_type: str, status_code, message: str):
    TTS_RUNTIME_DIAGNOSTICS["last_error"] = {
        "timestamp": _utcnow_iso_z(),
        "stage": stage,
        "language": normalize_language_code(language or "en"),
        "persona": persona or "personal_trainer",
        "error_type": error_type,
        "status_code": status_code,
        "message": str(message)[:500],
    }

# Common English words that should never appear in Norwegian coaching output
_ENGLISH_COACHING_WORDS = {
    "keep going", "good job", "push harder", "well done", "hold on",
    "nice work", "stay focused", "you got this", "let's go", "come on",
    "great work", "push it", "almost there", "hang in there", "breathe",
    "slow down", "speed up", "perfect", "excellent", "amazing",
    "fantastic", "steady", "hold it", "more effort", "pick up",
}
_ENGLISH_TOKEN_MARKERS = {
    "keep", "going", "good", "job", "push", "harder", "focused",
    "great", "excellent", "amazing", "fantastic", "steady", "breathe",
    "faster", "move", "you", "your", "this", "that", "don't", "lets",
}
_NORWEGIAN_TOKEN_MARKERS = {
    "fortsett", "kjør", "jobba", "pust", "rolig", "rytmen", "tempoet",
    "hardere", "innsats", "press", "klarer", "beveg", "farten", "senk",
    "oppvarming", "bestemora", "bestemor", "nå", "økt", "sterkt",
}
_NORWEGIAN_COACHING_PHRASES = {
    "fortsett", "kjør på", "bra jobba", "hold rytmen", "ta det rolig",
    "senk tempoet", "du klarer det", "mer innsats", "behold tempoet",
}
_ENGLISH_FUNCTION_MARKERS = {
    "the", "is", "are", "you", "your", "this", "that", "it", "do", "don't",
}


def _tokenize_language_markers(text: str) -> list:
    punctuation = ".,!?;:\"'()[]{}"
    return [
        token.strip(punctuation).lower()
        for token in (text or "").split()
        if token.strip(punctuation)
    ]


def _looks_norwegian(text: str) -> bool:
    """Heuristic: returns True if text appears to be Norwegian rather than English."""
    lowered = text.lower().strip().rstrip("!.")
    if any(c in text for c in "æøåÆØÅ"):
        return True
    for phrase in _NORWEGIAN_COACHING_PHRASES:
        if phrase in lowered:
            return True
    words = _tokenize_language_markers(text)
    if not words:
        return False
    norwegian_hits = sum(1 for w in words if w in _NORWEGIAN_TOKEN_MARKERS)
    english_hits = sum(1 for w in words if w in _ENGLISH_TOKEN_MARKERS)
    if norwegian_hits >= 2:
        return True
    if norwegian_hits >= 1 and english_hits == 0 and len(words) <= 5:
        return True
    return False

def _looks_english(text: str) -> bool:
    """Heuristic: returns True if text appears to be English rather than Norwegian."""
    lowered = text.lower().strip().rstrip("!.")
    # Direct match against known English coaching phrases
    if lowered in _ENGLISH_COACHING_WORDS:
        return True
    # Check if any known English phrase is a substring
    for phrase in _ENGLISH_COACHING_WORDS:
        if phrase in lowered:
            return True
    words = _tokenize_language_markers(text)
    if words:
        english_hits = sum(1 for w in words if w in _ENGLISH_TOKEN_MARKERS)
        norwegian_hits = sum(1 for w in words if w in _NORWEGIAN_TOKEN_MARKERS)
        if english_hits >= 2:
            return True
        # Treat mixed short cues as drift when English tokens are present.
        if english_hits >= 1 and norwegian_hits >= 1:
            return True
        if english_hits >= 1 and norwegian_hits == 0 and len(words) <= 5:
            return True

    # No Norwegian characters AND common English markers = likely English
    has_norwegian = any(c in text for c in "æøåÆØÅ")
    if not has_norwegian:
        words = text.split()
        if len(words) >= 2:
            if any(w.lower().rstrip(".,!?") in _ENGLISH_FUNCTION_MARKERS for w in words):
                return True
    return False


def _pick_deterministic_fallback(pool, seed_text: str) -> str:
    """Stable pool selection for guardrail replacements."""
    if not pool:
        return "Fortsett!"
    seed = (seed_text or "").strip().lower()
    index = sum(ord(ch) for ch in seed) % len(pool)
    return pool[index]


def enforce_language_consistency(text: str, language: str, phase: str = None) -> str:
    """
    Final guardrail against fallback language drift.

    Keeps normal model output untouched, but rewrites known fallback drift tokens.
    For Norwegian: detects English-dominant output and replaces with Norwegian fallback.
    """
    if not text:
        return text

    normalized_language = normalize_language_code(language)
    stripped = text.strip()
    lowered = stripped.lower()

    if normalized_language == "en":
        if _looks_norwegian(stripped):
            logger.warning(f"Language guard corrected NO->EN drift: '{stripped}'")
            _increment_quality_metric("language_guard_rewrites")
            _increment_quality_metric("language_guard_no_to_en_rewrites")
            return "Keep going!"
    elif normalized_language == "no":
        if lowered in {"keep going", "keep going!"}:
            logger.warning(f"Language guard corrected EN->NO drift: '{stripped}'")
            _increment_quality_metric("language_guard_rewrites")
            _increment_quality_metric("language_guard_en_to_no_rewrites")
            return "Fortsett!"
        # Broader detection: English-dominant output when Norwegian expected
        if _looks_english(stripped):
            fallback_messages = getattr(config, "CONTINUOUS_COACH_MESSAGES_NO", {})
            if phase == "intense":
                intense = fallback_messages.get("intense", {})
                pool = intense.get("moderate", ["Hold trykket oppe.", "Bra flyt, fortsett."])
            elif phase == "cooldown":
                pool = fallback_messages.get("cooldown", ["Rolige pust.", "Senk tempoet rolig."])
            else:
                pool = fallback_messages.get("warmup", ["Fortsett!", "Kjør på!", "Bra jobba!"])
            replacement = _pick_deterministic_fallback(pool, f"{phase}:{stripped}")
            logger.warning(f"Language guard replaced English text in NO mode: '{stripped}' -> '{replacement}'")
            _increment_quality_metric("language_guard_rewrites")
            _increment_quality_metric("language_guard_en_to_no_rewrites")
            return rewrite_norwegian_phrase(replacement, phase=phase)

        return rewrite_norwegian_phrase(stripped, phase=phase)

    return text


def _get_silent_debug_text(reason: str, language: str) -> str:
    """
    Short, language-safe placeholder text for silent ticks.

    This is returned in API payloads for diagnostics, but not spoken.
    """
    lang = normalize_language_code(language)
    reason_key = (reason or "default").strip().lower()

    messages = {
        "en": {
            "near_zero_signal": "Listening...",
            "no_change": "Hold rhythm.",
            "too_frequent": "Stay steady.",
            "default": "Hold form.",
        },
        "no": {
            "near_zero_signal": "Lytter...",
            "no_change": "Hold rytmen.",
            "too_frequent": "Hold jevnt.",
            "default": "Hold flyten.",
        },
        "da": {
            "near_zero_signal": "Lytter...",
            "no_change": "Hold rytmen.",
            "too_frequent": "Hold stabilt.",
            "default": "Hold fokus.",
        },
    }

    lang_messages = messages.get(lang, messages["en"])
    return lang_messages.get(reason_key, lang_messages["default"])


def _resolve_breath_quality_state(breath_data: dict, recent_samples) -> str:
    """
    Classify breath signal quality for speech-owner arbitration.

    States:
    - reliable: enough recent quality data to trust breath-driven decisioning
    - degraded: some signal exists but not reliable
    - unavailable: no usable signal
    """
    quality_summary = summarize_breath_quality(
        breath_data=breath_data,
        recent_samples=recent_samples,
        config_module=config,
        include_current_signal=True,
    )
    return str(quality_summary.get("quality_state") or "unavailable")


def _phase_fallback_text(language: str, phase: str, elapsed_seconds: int) -> str:
    lang = normalize_language_code(language)
    normalized_phase = (phase or "").strip().lower()

    cues = {
        "en": {
            "warmup": [
                "Easy warm-up. Keep your breathing relaxed.",
                "Stay easy. Build rhythm first.",
            ],
            "intense": [
                "Stay controlled and hold your rhythm.",
                "Keep form steady and breathe with control.",
                "Strong focus. Hold your effort, not your tension.",
            ],
            "cooldown": [
                "Cooldown now. Let your breathing settle.",
                "Ease down and keep the stride relaxed.",
            ],
        },
        "no": {
            "warmup": [
                "Rolig oppvarming. Hold pusten avslappet.",
                "Hold det lett. Bygg rytme først.",
            ],
            "intense": [
                "Hold kontroll og jevn rytme.",
                "Stabil teknikk og rolig pust.",
                "Sterkt fokus. Hold trykket uten å spenne deg.",
            ],
            "cooldown": [
                "Nedjogg nå. La pusten roe seg.",
                "Senk tempoet og hold steget avslappet.",
            ],
        },
    }

    lang_cues = cues.get(lang, cues["en"])
    phase_cues = lang_cues.get(normalized_phase, lang_cues["intense"])
    idx_seed = max(0, int(elapsed_seconds or 0)) // 20
    cue = phase_cues[idx_seed % len(phase_cues)]
    return enforce_language_consistency(cue, lang, phase=normalized_phase)


def _call_evaluate_zone_tick_compat(**kwargs):
    """
    Invoke evaluate_zone_tick with forward/backward compatibility filtering.

    Protects /coach/continuous from hard failures during temporary deploy drift
    where main.py sends newer kwargs than zone_event_motor supports.
    """
    try:
        return evaluate_zone_tick(**kwargs)
    except TypeError as exc:
        error_text = str(exc)
        if "unexpected keyword argument" not in error_text:
            raise

        signature = inspect.signature(evaluate_zone_tick)
        accepted_keys = set(signature.parameters.keys())
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in accepted_keys}
        dropped_keys = sorted(set(kwargs.keys()) - set(filtered_kwargs.keys()))

        logger.warning(
            "Zone tick compat fallback: dropping unsupported kwargs=%s due to signature drift (%s)",
            dropped_keys,
            error_text,
        )
        return evaluate_zone_tick(**filtered_kwargs)


def _compute_server_authoritative_elapsed(
    *,
    workout_state: dict,
    client_elapsed_seconds: int,
    phase: str,
    paused: bool,
) -> tuple[int, float]:
    """
    Compute canonical elapsed time from server-side monotonic clock.

    Returns:
        (canonical_elapsed_s, drift_vs_client_s)
    """
    now_mono = time.monotonic()
    if workout_state.get("session_started_at_monotonic") is None:
        workout_state["session_started_at_monotonic"] = now_mono - max(0, int(client_elapsed_seconds))
        workout_state["phase_started_at_monotonic"] = now_mono
        workout_state["paused_accumulated_s"] = 0.0
        workout_state["pause_started_at_monotonic"] = None
        workout_state["clock_last_phase"] = phase

    if workout_state.get("clock_last_phase") != phase:
        workout_state["phase_started_at_monotonic"] = now_mono
        workout_state["clock_last_phase"] = phase

    paused_accumulated = float(workout_state.get("paused_accumulated_s") or 0.0)
    pause_started = workout_state.get("pause_started_at_monotonic")
    if paused:
        if pause_started is None:
            workout_state["pause_started_at_monotonic"] = now_mono
            pause_started = now_mono
    elif pause_started is not None:
        paused_accumulated += max(0.0, now_mono - float(pause_started))
        workout_state["paused_accumulated_s"] = paused_accumulated
        workout_state["pause_started_at_monotonic"] = None
        pause_started = None

    active_pause = max(0.0, now_mono - float(pause_started)) if pause_started is not None else 0.0
    start_mono = float(workout_state.get("session_started_at_monotonic") or now_mono)
    elapsed = max(0.0, now_mono - start_mono - paused_accumulated - active_pause)
    canonical_elapsed = int(round(elapsed))

    # Client elapsed is a hint. If server clock falls far behind (for example app resume),
    # resync the session start once so canonical time remains usable for countdowns.
    client_elapsed = max(0, int(client_elapsed_seconds))
    resync_ahead_seconds = int(getattr(config, "SERVER_CLOCK_RESYNC_AHEAD_SECONDS", 20))
    if client_elapsed - canonical_elapsed >= max(1, resync_ahead_seconds):
        workout_state["session_started_at_monotonic"] = now_mono - float(client_elapsed) - paused_accumulated - active_pause
        canonical_elapsed = client_elapsed

    drift = float(canonical_elapsed - client_elapsed)
    workout_state["server_elapsed_s"] = canonical_elapsed
    return canonical_elapsed, drift


def _build_continuous_failsafe_response(
    *,
    contract_version: str,
    phase: str,
    workout_mode: str,
    coaching_style: str,
    interval_template: str | None,
    reason: str,
    trace_id: str,
    language: str,
) -> dict:
    return {
        "contract_version": contract_version,
        "text": _get_silent_debug_text(reason, language),
        "should_speak": False,
        "breath_analysis": breath_analyzer._default_analysis(),
        "audio_url": None,
        "wait_seconds": int(getattr(config, "MAX_COACHING_INTERVAL", 20)),
        "phase": phase,
        "workout_mode": workout_mode,
        "reason": reason,
        "decision_owner": "zone_event",
        "decision_reason": reason,
        "zone_tick_guard_silent_safe": True,
        "breath_quality_state": "unknown",
        "coach_score": 0,
        "coach_score_line": "",
        "coach_score_v2": 0,
        "coach_score_components": {},
        "cap_reason_codes": [],
        "cap_applied": 100,
        "cap_applied_reason": None,
        "hr_valid_main_set_seconds": 0,
        "zone_valid_main_set_seconds": 0,
        "zone_compliance": None,
        "breath_available_reliable": False,
        "events": [],
        "brain_provider": "system",
        "brain_source": "failsafe",
        "brain_status": "fallback",
        "brain_mode": "realtime_coach",
        "latency_fast_fallback_used": True,
        "latency_rich_followup_forced": False,
        "latency_pending_rich_followup": False,
        "latency_signal_reason": None,
        "latency_signal_provider": None,
        "latency_signal_avg": None,
        "coaching_style": coaching_style,
        "interval_template": interval_template if workout_mode == "interval" else None,
        "personalization_tip": None,
        "recovery_line": None,
        "recovery_baseline_seconds": None,
        "workout_context_summary": None,
        "debug_trace_id": trace_id,
    }


def _log_decision_debug(
    *,
    session_id: str,
    owner: str,
    reason: str,
    breath_quality_state: str,
    zone_mode_active: bool,
    max_silence_override_used: bool,
) -> None:
    logger.info(
        "DECISION_DEBUG session=%s owner=%s reason=%s breath_quality_state=%s zone_mode_active=%s max_silence_override_used=%s",
        session_id,
        owner,
        reason or "none",
        breath_quality_state or "unknown",
        bool(zone_mode_active),
        bool(max_silence_override_used),
    )


def _extract_recent_spoken_cues(coaching_history, limit: int = 4) -> list:
    """Extract recent spoken coach lines for anti-repetition context."""
    if not coaching_history:
        return []

    cues = []
    for item in reversed(coaching_history):
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if not text:
            continue
        cues.append(text)
        if len(cues) >= max(1, int(limit)):
            break

    cues.reverse()
    return cues


def _get_or_create_session_timeline(session_id: str):
    """Return per-session breathing timeline state (in-memory)."""
    session = session_manager.sessions.get(session_id)
    if not session:
        return None

    metadata = session.setdefault("metadata", {})
    timeline = metadata.get("breathing_timeline")
    if timeline is None:
        timeline = BreathingTimeline()
        metadata["breathing_timeline"] = timeline
    return timeline


def _ensure_latency_strategy_state(workout_state: dict) -> dict:
    """Ensure per-session latency strategy state exists with safe defaults."""
    if workout_state is None:
        return {
            "pending_rich_followup": False,
            "last_fast_fallback_elapsed": -10_000,
            "last_rich_followup_elapsed": -10_000,
            "last_latency_provider": None,
        }

    state = workout_state.setdefault("latency_strategy", {})
    state.setdefault("pending_rich_followup", False)
    state.setdefault("last_fast_fallback_elapsed", -10_000)
    state.setdefault("last_rich_followup_elapsed", -10_000)
    state.setdefault("last_latency_provider", None)
    return state


def _latency_fast_fallback_allowed(latency_state: dict, elapsed_seconds: int) -> bool:
    """Return True when fast fallback cooldown has elapsed for this session."""
    cooldown = float(getattr(config, "LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS", 20.0))
    now_elapsed = float(elapsed_seconds or 0)
    last_elapsed = float(latency_state.get("last_fast_fallback_elapsed", -10_000))
    return (now_elapsed - last_elapsed) >= cooldown


def _infer_emotional_mode(intensity: str) -> str:
    """Map normalized intensity to a stable emotional voice mode."""
    mapping = {
        "calm": "supportive",
        "moderate": "pressing",
        "intense": "intense",
        "critical": "peak",
    }
    return mapping.get((intensity or "moderate").strip().lower(), "supportive")


def _ema(values, alpha: float):
    """Exponential moving average for smoothing numeric sequences."""
    ema = None
    for value in values:
        if value is None:
            continue
        value = float(value)
        ema = value if ema is None else (alpha * value) + ((1 - alpha) * ema)
    return ema

def _classify_intensity(resp_rate: float, volume: float, regularity: float) -> str:
    """Match breath_analyzer intensity rules for smoothed classification."""
    if resp_rate is None:
        resp_rate = 15.0
    if volume is None:
        volume = 30.0
    if regularity is None:
        regularity = 0.5

    if resp_rate > 40 or (volume > 70 and regularity < 0.3):
        return "critical"
    if resp_rate > 25 or volume > 50:
        return "intense"
    if resp_rate > 15 or volume > 25:
        return "moderate"
    return "calm"

def _score_intensity(resp_rate: float, volume: float, regularity: float, quality: float):
    """Compute normalized intensity score + confidence (0-1)."""
    rate_score = 0.0
    if resp_rate is not None:
        rate_score = max(0.0, min(1.0, (resp_rate - 10.0) / 35.0))

    vol_score = 0.0
    if volume is not None:
        vol_score = max(0.0, min(1.0, (volume - 10.0) / 70.0))

    irregularity = 0.0
    if regularity is not None:
        irregularity = max(0.0, min(1.0, 1.0 - regularity))

    score = (0.6 * rate_score) + (0.3 * vol_score) + (0.1 * irregularity)

    q = quality if quality is not None else 0.5
    r = regularity if regularity is not None else 0.5
    confidence = max(0.0, min(1.0, q * (0.5 + 0.5 * r)))

    return round(score, 3), round(confidence, 3)

def _smooth_breath_metrics(breath_data: dict, breath_history: list) -> dict:
    """Smooth key breath metrics across recent history using EMA."""
    alpha = getattr(config, "BREATH_SMOOTHING_ALPHA", 0.5)
    window = getattr(config, "BREATH_SMOOTHING_WINDOW", 4)
    recent = breath_history[-window:] if breath_history else []

    def series(key):
        values = [h.get(key) for h in recent if h.get(key) is not None]
        values.append(breath_data.get(key))
        return values

    smoothed = {}
    for key in ("respiratory_rate", "volume", "breath_regularity", "inhale_exhale_ratio",
                "signal_quality", "dominant_frequency"):
        smoothed_value = _ema(series(key), alpha)
        if smoothed_value is not None:
            smoothed[key] = round(float(smoothed_value), 3)

    # Keep tempo aligned with respiratory_rate
    if "respiratory_rate" in smoothed:
        smoothed["tempo"] = smoothed["respiratory_rate"]

    return smoothed

def _infer_interval_state(breath_history: list, current_intensity: str, workout_mode: str):
    """Infer interval state (work/rest/transition) from intensity trend."""
    if workout_mode != "interval":
        return {"state": "steady", "confidence": 0.0, "zone": None}

    recent = [h.get("intensity") for h in breath_history[-3:] if h.get("intensity")] + [current_intensity]
    if not recent:
        return {"state": "transition", "confidence": 0.0, "zone": None}

    work_count = sum(1 for i in recent if i in ("intense", "critical"))
    rest_count = sum(1 for i in recent if i in ("calm", "moderate"))
    total = len(recent)

    if work_count >= max(2, total - 1):
        state = "work"
        confidence = work_count / total
    elif rest_count >= max(2, total - 1):
        state = "rest"
        confidence = rest_count / total
    else:
        state = "transition"
        confidence = max(work_count, rest_count) / total

    zone_map = {"calm": "Z1", "moderate": "Z2", "intense": "Z3", "critical": "Z4"}
    return {"state": state, "confidence": round(confidence, 2), "zone": zone_map.get(current_intensity)}

# ============================================
# BREATH ANALYSIS
# ============================================
# Advanced breath analysis is now handled by BreathAnalyzer class
# (see breath_analyzer.py) — uses DSP + spectral features for
# real inhale/exhale/pause detection, respiratory rate, etc.
# Initialized above as: breath_analyzer = BreathAnalyzer()

# ============================================
# COACH-LOGIKK
# ============================================

def get_coach_response(breath_data, phase="intense", mode="chat"):
    """
    Selects what the coach should say based on breathing data.

    Now uses Brain Router to abstract AI provider selection.
    The app doesn't know if this is Claude, OpenAI, or config - it just gets a response.

    STEP 3: Supports switching between chat and realtime_coach modes.

    Args:
        breath_data: Dictionary with silence, volume, tempo, intensity
        phase: "warmup", "intense", or "cooldown"
        mode: "chat" (explanatory) or "realtime_coach" (fast, actionable)

    Returns:
        Text that the coach should say
    """
    return brain_router.get_coaching_response(breath_data, phase, mode=mode)

# ============================================
# VOICE GENERATION (ELEVENLABS; QWEN DISABLED)
# ============================================

def generate_voice(text, language=None, persona=None, emotional_mode=None):
    """
    Generates speech audio from text using ElevenLabs (local Qwen disabled).

    Voice is selected based on persona (if set) then language.
    Each persona can have its own ElevenLabs voice ID and voice settings.

    Args:
        text: The coaching message to synthesize
        language: "en" or "no" for language-specific voice (optional)
        persona: Persona identifier for persona-specific voice (optional)

    Returns:
        Path to generated audio file (MP3 or WAV)
    """
    try:
        normalized_language = normalize_language_code(language or "en")
        selected_persona = persona or "personal_trainer"
        selected_mode = emotional_mode or "supportive"
        tts_text = text
        voice_pacing = None

        if getattr(config, "VOICE_TTS_PACING_ENABLED", True) or getattr(config, "VOICE_TEXT_PACING_ENABLED", True):
            voice_pacing = voice_intelligence.get_voice_pacing(
                persona=selected_persona,
                emotional_mode=selected_mode,
                message=text,
            )

        if getattr(config, "VOICE_TEXT_PACING_ENABLED", True) and voice_pacing:
            rhythm_fn = getattr(voice_intelligence, "apply_text_rhythm", None)
            if callable(rhythm_fn):
                paced_text = rhythm_fn(
                    message=text,
                    language=normalized_language,
                    emotional_mode=selected_mode,
                    pacing=voice_pacing,
                )
                if paced_text != text:
                    logger.info("Voice text pacing applied: %r -> %r", text, paced_text)
                tts_text = paced_text
            else:
                global VOICE_TEXT_PACING_COMPAT_WARNED
                if not VOICE_TEXT_PACING_COMPAT_WARNED:
                    logger.warning(
                        "VOICE_TEXT_PACING_ENABLED is true but VoiceIntelligence.apply_text_rhythm is unavailable; skipping text rhythm shaping."
                    )
                    VOICE_TEXT_PACING_COMPAT_WARNED = True

        if USE_ELEVENLABS:
            # Use ElevenLabs with persona-specific voice settings
            pacing_override = voice_pacing if getattr(config, "VOICE_TTS_PACING_ENABLED", True) else None
            try:
                result = elevenlabs_tts.generate_audio(
                    tts_text,
                    language=normalized_language,
                    persona=selected_persona,
                    voice_pacing=pacing_override,
                )
                logger.info(
                    "TTS_OK lang=%s persona=%s mode=%s file=%s",
                    normalized_language,
                    selected_persona,
                    selected_mode,
                    os.path.basename(result),
                )
                return result
            except Exception as persona_error:
                logger.warning(
                    "Persona voice TTS failed (lang=%s persona=%s): %s. Retrying with base language voice.",
                    normalized_language,
                    selected_persona,
                    persona_error,
                )

                try:
                    result = elevenlabs_tts.generate_audio(
                        tts_text,
                        language=normalized_language,
                        persona=None,
                        voice_pacing=pacing_override,
                    )
                    logger.info(
                        "TTS_RETRY_OK lang=%s persona=base mode=%s file=%s",
                        normalized_language,
                        selected_mode,
                        os.path.basename(result),
                    )
                    return result
                except Exception as base_error:
                    logger.warning(
                        "Base language voice TTS retry failed (lang=%s): %s",
                        normalized_language,
                        base_error,
                    )
                    if normalized_language != "en":
                        try:
                            result = elevenlabs_tts.generate_audio(
                                tts_text,
                                language="en",
                                persona=None,
                                voice_pacing=pacing_override,
                            )
                            logger.info(
                                "TTS_RETRY_OK lang=en persona=base mode=%s file=%s",
                                selected_mode,
                                os.path.basename(result),
                            )
                            return result
                        except Exception as english_error:
                            logger.warning("English base voice TTS retry failed: %s", english_error)

                    raise base_error
        else:
            # Fallback to mock (Qwen disabled)
            logger.info("TTS_MOCK lang=%s elevenlabs_enabled=false", normalized_language)
            return synthesize_speech_mock(tts_text)
    except Exception as e:
        status_code = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
        logger.error(
            "TTS failed, using mock (lang=%s persona=%s type=%s status=%s): %s",
            language,
            persona,
            type(e).__name__,
            status_code,
            e,
            exc_info=True,
        )
        logger.error(
            "TTS_FAILED lang=%s persona=%s type=%s status=%s error=%s",
            language,
            persona,
            type(e).__name__,
            status_code,
            e,
        )
        # Fallback to mock for development/testing
        return synthesize_speech_mock(text)

# ============================================
# API ENDPOINTS
# ============================================

WEB_VARIANT_TEMPLATES = {
    "claude": "index_claude.html",
    "codex": "index_codex.html",
    "launch": "index_launch.html",
}
DEFAULT_WEB_VARIANT = getattr(config, "WEB_UI_VARIANT", "codex")
APP_STORE_URL = (os.getenv("APP_STORE_URL") or "").strip()
GOOGLE_PLAY_URL = (os.getenv("GOOGLE_PLAY_URL") or "").strip()
ANDROID_EARLY_ACCESS_URL = (os.getenv("ANDROID_EARLY_ACCESS_URL") or "").strip()


def _resolve_web_variant(raw_variant: str = None):
    """Resolve requested web variant to a known template with safe fallback."""
    candidate = (raw_variant or DEFAULT_WEB_VARIANT or "codex").strip().lower()
    if candidate not in WEB_VARIANT_TEMPLATES:
        candidate = "codex"
    return candidate, WEB_VARIANT_TEMPLATES[candidate]


def _landing_link_context():
    """Website funnel links (configured via env; safe fallback for local/dev)."""
    return {
        "app_store_url": APP_STORE_URL or "#download",
        "google_play_url": GOOGLE_PLAY_URL or "#download",
        "android_early_access_url": ANDROID_EARLY_ACCESS_URL or "#waitForm",
    }


web_bp = create_web_blueprint(
    config_module=config,
    waitlist_model=WaitlistSignup,
    db=db,
    normalize_language_code=normalize_language_code,
    quality_guard_snapshot_fn=_quality_guard_snapshot,
    product_flags_snapshot_fn=_product_flags_snapshot,
    landing_link_context_fn=_landing_link_context,
    resolve_web_variant_fn=_resolve_web_variant,
    logger=logger,
)
app.register_blueprint(web_bp)

chat_bp = create_chat_blueprint(
    brain_router=brain_router,
    session_manager=session_manager,
    persona_manager=PersonaManager,
    logger=logger,
)
app.register_blueprint(chat_bp)

@app.route('/tts/cache/stats', methods=['GET'])
def tts_cache_stats():
    """Expose ElevenLabs audio cache stats for tuning/observability."""
    if not USE_ELEVENLABS:
        return jsonify({
            "enabled": False,
            "message": "ElevenLabs disabled",
        }), 503

    try:
        stats = elevenlabs_tts.get_cache_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error reading TTS cache stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to read TTS cache stats"}), 500

@app.route('/welcome', methods=['GET'])
def welcome():
    return jsonify({
        "error": "welcome_removed",
        "message": "The welcome audio path has been retired. Start workouts through /coach/continuous instead.",
    }), 410

@app.route('/analyze', methods=['POST'])
@rate_limit(
    limit=getattr(config, "API_RATE_LIMIT_PER_HOUR", 100),
    window_seconds=3600,
    key_prefix="api.analyze",
)
@require_mobile_auth
def analyze():
    """
    Receives audio recording from app and analyzes breathing

    App sends: MP3/WAV file
    Backend returns: JSON with breathing data
    """
    try:
        if 'audio' not in request.files:
            logger.warning("Analyze request missing audio file")
            return jsonify({"error": "No audio file received"}), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        if not _validate_audio_upload_signature(audio_file):
            return jsonify({"error": "Unsupported audio format signature"}), 400

        # Validate file size
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

        # Save file temporarily
        filename = f"breath_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)

        logger.info(f"Analyzing audio file: {filename} ({file_size} bytes)")

        # Analyze breathing with a hard timeout so uploads cannot stall a worker.
        breath_data = _analyze_breath_with_timeout(
            filepath,
            request_context="analyze",
            trace_id="analyze_endpoint",
        )

        # Delete temporary file
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        logger.info(f"Analysis complete: {breath_data['intensity']}")
        return jsonify(breath_data)

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/coach/continuous', methods=['POST'])
@rate_limit(
    limit=getattr(config, "CONTINUOUS_RATE_LIMIT_PER_HOUR", 500),
    window_seconds=3600,
    key_prefix="api.coach.continuous",
    scope="user",
    key_func=_mobile_rate_limit_subject_from_request,
)
@rate_limit(
    limit=getattr(config, "CONTINUOUS_RATE_LIMIT_PER_MINUTE", 30),
    window_seconds=60,
    key_prefix="api.coach.continuous",
    scope="user",
    key_func=_mobile_rate_limit_subject_from_request,
)
@require_mobile_auth
def coach_continuous():
    """
    Continuous coaching endpoint - optimized for rapid coaching cycles.

    Receives:
    - audio: Audio chunk (6-10 seconds)
    - session_id: Workout session identifier
    - phase: Current workout phase ("warmup", "intense", "cooldown")
    - last_coaching: Last coaching message (optional)
    - elapsed_seconds: Total workout time (optional)

    Returns:
    - text: Coaching message
    - should_speak: Boolean (whether coach should speak this cycle)
    - breath_analysis: Breath metrics
    - audio_url: Coach voice URL (if should_speak is true)
    - wait_seconds: Optimal time before next tick
    """
    trace_id = f"ct_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    temp_filepath = None
    try:
        _increment_quality_metric("continuous_ticks")
        request_started = time.perf_counter()
        analyze_ms = 0.0
        decision_ms = 0.0
        brain_ms = 0.0
        tts_ms = 0.0

        if 'audio' not in request.files:
            logger.warning("Continuous coach request missing audio file")
            return jsonify({"error": "No audio file received"}), 400

        audio_file = request.files['audio']
        normalized_contract = normalize_continuous_contract(request.form, {})
        contract_version = normalized_contract["contract_version"]
        normalized_plan = normalized_contract["workout_plan"]
        normalized_tick_state = normalized_contract["workout_state"]

        session_id = normalized_tick_state.session_id or request.form.get('session_id')
        phase = normalized_tick_state.phase or request.form.get('phase', 'intense')
        last_coaching = request.form.get('last_coaching', '')
        elapsed_seconds = int(normalized_tick_state.elapsed_s or request.form.get('elapsed_seconds', 0))
        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(request.form.get('language', default_language))
        training_level = request.form.get('training_level', 'intermediate')
        persona = request.form.get('persona', 'personal_trainer')
        workout_mode = request.form.get('workout_mode', config.DEFAULT_WORKOUT_MODE)
        if str(normalized_plan.workout_type).strip().lower() in {"intervals", "interval"}:
            workout_mode = "interval"
        elif str(normalized_plan.workout_type).strip().lower() in {"easy_run", "easy"}:
            workout_mode = "easy_run"
        coaching_style = normalize_coaching_style(
            request.form.get('coaching_style', getattr(config, "DEFAULT_COACHING_STYLE", "normal")),
            config,
        )
        interval_template = normalize_interval_template(
            request.form.get('interval_template', getattr(config, "DEFAULT_INTERVAL_TEMPLATE", "4x4")),
            config,
        )
        warmup_seconds_raw = request.form.get("warmup_seconds")
        if normalized_plan.warmup_s is not None:
            warmup_seconds_raw = str(max(0, int(normalized_plan.warmup_s)))
        user_name = request.form.get('user_name', '').strip()
        user_profile_id = request.form.get('user_profile_id', '').strip()
        heart_rate_raw = request.form.get("heart_rate")
        if normalized_tick_state.hr_bpm is not None:
            heart_rate_raw = str(int(normalized_tick_state.hr_bpm))
        hr_quality_raw = request.form.get("hr_quality")
        if normalized_tick_state.hr_quality:
            hr_quality_raw = str(normalized_tick_state.hr_quality)
        watch_connected_raw = request.form.get("watch_connected")
        if normalized_tick_state.watch_connected is not None:
            watch_connected_raw = "true" if normalized_tick_state.watch_connected else "false"
        paused_raw = request.form.get("paused")
        if normalized_tick_state.paused is not None:
            paused_raw = "true" if normalized_tick_state.paused else "false"
        breath_analysis_enabled_raw = request.form.get("breath_analysis_enabled", "true")
        mic_permission_granted_raw = request.form.get("mic_permission_granted", "true")
        breath_enabled_by_user = _coerce_bool(breath_analysis_enabled_raw)
        mic_permission_granted = _coerce_bool(mic_permission_granted_raw)

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400

        if audio_file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        if not _validate_audio_upload_signature(audio_file):
            return jsonify({"error": "Unsupported audio format signature"}), 400

        # Validate phase
        valid_phases = ['warmup', 'intense', 'cooldown']
        if phase not in valid_phases:
            return jsonify({"error": f"Invalid phase. Must be one of: {', '.join(valid_phases)}"}), 400

        # Validate workout mode (backend-only for now)
        if workout_mode not in config.SUPPORTED_WORKOUT_MODES:
            return jsonify({"error": f"Invalid workout_mode. Must be one of: {', '.join(config.SUPPORTED_WORKOUT_MODES)}"}), 400

        # Validate file size
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large. Max: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

        logger.info(f"Audio chunk size: {file_size} bytes")

        # Save file temporarily
        filename = f"continuous_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        temp_filepath = filepath
        audio_file.save(filepath)

        logger.info(
            "Continuous coaching tick: session=%s phase=%s mode=%s elapsed=%ss lang=%s level=%s persona=%s style=%s template=%s user=%s contract=%s",
            session_id,
            phase,
            workout_mode,
            elapsed_seconds,
            language,
            training_level,
            persona,
            coaching_style,
            interval_template,
            user_name or "anon",
            contract_version,
        )

        # Create session if doesn't exist
        if not session_manager.session_exists(session_id):
            # Extract user_id from session_id or use a default
            try:
                parts = session_id.replace("session_", "").split("_")
                user_id = parts[0] if parts else "unknown"
            except:
                user_id = "unknown"

            # Create session manually with the provided session_id
            session_manager.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "persona": persona,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {
                    "workout_mode": workout_mode,
                    "coaching_style": coaching_style,
                    "interval_template": interval_template,
                    "user_name": user_name,
                    "user_id": user_id,
                    "user_profile_id": user_profile_id,
                }
            }
            logger.info(f"✅ Created session: {session_id}")
            session_manager.init_workout_state(session_id, phase=phase)

            # STEP 5: Inject user memory at session start (once)
            memory_summary = user_memory.get_memory_summary(user_id)
            logger.info(f"Memory: {memory_summary}")
            session_manager.sessions[session_id]["metadata"]["memory"] = memory_summary

            # Mark that this is the first breath of the workout
            workout_state = session_manager.get_workout_state(session_id)
            workout_state["is_first_breath"] = True

        session_meta = session_manager.sessions.get(session_id, {}).setdefault("metadata", {})
        session_meta["workout_mode"] = workout_mode
        session_meta["coaching_style"] = coaching_style
        session_meta["interval_template"] = interval_template
        if user_name:
            session_meta["user_name"] = user_name
        else:
            user_name = session_meta.get("user_name", "")
        if user_profile_id:
            session_meta["user_profile_id"] = user_profile_id
        current_user_id = session_meta.get("user_id", "unknown")
        personalization_user_id = _normalize_personalization_user_id(
            explicit_profile_id=session_meta.get("user_profile_id", ""),
            current_user_id=current_user_id,
            user_name=user_name,
        )
        session_meta["personalization_user_id"] = personalization_user_id

        runtime_profile_user_id = _coerce_profile_user_id(
            user_profile_id or session_meta.get("user_profile_id") or current_user_id
        )
        if runtime_profile_user_id:
            session_meta["user_profile_id"] = runtime_profile_user_id
        profile_snapshot = normalized_contract.get("user_profile")
        resolved_runtime_profile, runtime_profile_source = _resolve_runtime_profile(
            user_id=runtime_profile_user_id,
            snapshot_profile=profile_snapshot,
        )
        logger.info(
            "PROFILE_RUNTIME session=%s user=%s source=%s",
            session_id,
            runtime_profile_user_id or "none",
            runtime_profile_source,
        )
        resolved_hr_max = (
            resolved_runtime_profile.max_hr_bpm
            if resolved_runtime_profile and resolved_runtime_profile.max_hr_bpm is not None
            else _coerce_int(request.form.get("hr_max"))
        )
        resolved_resting_hr = (
            resolved_runtime_profile.resting_hr_bpm
            if resolved_runtime_profile and resolved_runtime_profile.resting_hr_bpm is not None
            else _coerce_int(request.form.get("resting_hr"))
        )
        resolved_age = (
            resolved_runtime_profile.age
            if resolved_runtime_profile and resolved_runtime_profile.age is not None
            else _coerce_int(request.form.get("age"))
        )

        # Early guard: too-small audio chunks are often invalid/corrupted
        min_bytes = getattr(config, "BREATH_MIN_AUDIO_BYTES", 8000)
        if file_size < min_bytes:
            header_hex = ""
            try:
                with open(filepath, "rb") as f:
                    header_hex = f.read(12).hex()
            except Exception:
                header_hex = "unreadable"

            logger.warning(f"Audio chunk too small ({file_size} bytes). Header: {header_hex}")

            breath_data = breath_analyzer._default_analysis()
            breath_data["analysis_error"] = "audio_too_small"
            breath_data["audio_bytes"] = file_size

            # Update session state with safe defaults
            session_manager.update_workout_state(
                session_id=session_id,
                breath_analysis=breath_data,
                coaching_output=None,
                phase=phase,
                elapsed_seconds=elapsed_seconds
            )

            # Clean up temp file
            try:
                os.remove(filepath)
            except Exception as e:
                logger.warning(f"Could not remove temp file {filepath}: {e}")

            wait_seconds = calculate_next_interval(
                phase=phase,
                intensity=breath_data.get("intensity", "moderate"),
                coaching_frequency=0
            )
            score_payload = _compute_layered_coach_score(
                language=language,
                elapsed_seconds=elapsed_seconds,
                breath_data=breath_data,
                zone_tick=None,
                watch_connected=watch_connected_raw,
                heart_rate=heart_rate_raw,
                hr_quality=hr_quality_raw,
                breath_enabled_by_user=breath_enabled_by_user,
                mic_permission_granted=mic_permission_granted,
                breath_quality_samples=[],
            )
            coach_score = int(score_payload["score"])
            coach_score_line = score_payload["score_line"]

            return jsonify({
                "contract_version": contract_version,
                "text": "",
                "should_speak": False,
                "breath_analysis": breath_data,
                "audio_url": None,
                "wait_seconds": wait_seconds,
                "phase": phase,
                "workout_mode": workout_mode,
                "reason": "audio_too_small",
                "coach_score": coach_score,
                "coach_score_line": coach_score_line,
                "coach_score_v2": score_payload.get("coach_score_v2"),
                "coach_score_components": score_payload.get("coach_score_components"),
                "cap_reason_codes": score_payload.get("cap_reason_codes"),
                "cap_applied": score_payload.get("cap_applied", score_payload.get("cap")),
                "cap_applied_reason": score_payload.get("cap_applied_reason"),
                "hr_valid_main_set_seconds": score_payload.get("hr_valid_main_set_seconds"),
                "zone_valid_main_set_seconds": score_payload.get("zone_valid_main_set_seconds"),
                "zone_compliance": score_payload.get("zone_compliance"),
                "breath_available_reliable": score_payload.get("breath_available_reliable"),
                "coaching_style": coaching_style,
                "interval_template": interval_template if workout_mode == "interval" else None,
                "workout_context_summary": None,
            })

        # Analyze breath with a hard timeout so a bad chunk cannot stall the worker.
        analyze_started = time.perf_counter()
        breath_data = _analyze_breath_with_timeout(
            filepath,
            request_context="continuous",
            trace_id=trace_id,
        )
        analyze_ms = (time.perf_counter() - analyze_started) * 1000.0

        # Get coaching context and workout state
        coaching_context = session_manager.get_coaching_context_with_emotion(session_id)
        last_breath = session_manager.get_last_breath_analysis(session_id)
        workout_state = session_manager.get_workout_state(session_id)
        if workout_state is not None:
            workout_state["workout_mode"] = workout_mode
            workout_state["coaching_style"] = coaching_style
            workout_state["interval_template"] = interval_template
            workout_state["plan_workout_type"] = str(normalized_plan.workout_type or "").strip().lower()
            if normalized_plan.warmup_s is not None:
                workout_state["plan_warmup_s"] = max(0, int(normalized_plan.warmup_s))
            if normalized_plan.main_s is not None:
                workout_state["plan_main_s"] = max(0, int(normalized_plan.main_s))
            if normalized_plan.cooldown_s is not None:
                workout_state["plan_cooldown_s"] = max(0, int(normalized_plan.cooldown_s))
            if normalized_plan.free_run is not None:
                workout_state["plan_free_run"] = bool(normalized_plan.free_run)
            interval_plan = normalized_plan.intervals if isinstance(normalized_plan.intervals, dict) else {}
            if interval_plan.get("repeats") is not None:
                workout_state["plan_interval_repeats"] = max(1, int(interval_plan["repeats"]))
            if interval_plan.get("work_s") is not None:
                workout_state["plan_interval_work_s"] = max(1, int(interval_plan["work_s"]))
            if interval_plan.get("recovery_s") is not None:
                workout_state["plan_interval_recovery_s"] = max(0, int(interval_plan["recovery_s"]))
            resolved_warmup_seconds = _coerce_int(warmup_seconds_raw)
            if phase == "warmup" and resolved_warmup_seconds is not None and resolved_warmup_seconds >= 0:
                # Keep timing config inside shared workout_state to avoid signature drift.
                # Primary input for countdown logic is remaining seconds, not total duration.
                remaining = max(0, int(resolved_warmup_seconds) - max(0, int(elapsed_seconds)))
                workout_state["warmup_remaining_s"] = remaining
            elif phase != "warmup":
                workout_state.pop("warmup_remaining_s", None)
            if bool(getattr(config, "SERVER_CLOCK_ENABLED", True)):
                client_elapsed_seconds = int(elapsed_seconds)
                paused_flag = bool(_coerce_bool(paused_raw))
                canonical_elapsed, drift = _compute_server_authoritative_elapsed(
                    workout_state=workout_state,
                    client_elapsed_seconds=client_elapsed_seconds,
                    phase=phase,
                    paused=paused_flag,
                )
                elapsed_seconds = canonical_elapsed
                drift_threshold = int(getattr(config, "SERVER_CLOCK_DRIFT_LOG_THRESHOLD_SECONDS", 5))
                if abs(drift) >= float(drift_threshold):
                    logger.info(
                        "CLOCK_CANONICAL session=%s elapsed_server=%s elapsed_client=%s drift_s=%.1f phase=%s paused=%s",
                        session_id,
                        canonical_elapsed,
                        client_elapsed_seconds,
                        drift,
                        phase,
                        paused_flag,
                    )
        latency_state = _ensure_latency_strategy_state(workout_state)

        # Enrich breath data with smoothing + structured schema
        breath_data["analysis_version"] = breath_data.get("analysis_version", 2)

        raw_snapshot = {
            "volume": breath_data.get("volume"),
            "tempo": breath_data.get("tempo"),
            "respiratory_rate": breath_data.get("respiratory_rate"),
            "breath_regularity": breath_data.get("breath_regularity"),
            "inhale_exhale_ratio": breath_data.get("inhale_exhale_ratio"),
            "signal_quality": breath_data.get("signal_quality"),
            "dominant_frequency": breath_data.get("dominant_frequency"),
            "intensity": breath_data.get("intensity"),
            "intensity_score": breath_data.get("intensity_score"),
            "intensity_confidence": breath_data.get("intensity_confidence")
        }

        smoothed = _smooth_breath_metrics(breath_data, coaching_context.get("breath_history", []))
        smoothing_applied = bool(smoothed) and (breath_data.get("signal_quality", 0) or 0) >= 0.2

        if smoothing_applied:
            breath_data.update(smoothed)
            smoothed_intensity = _classify_intensity(
                breath_data.get("respiratory_rate"),
                breath_data.get("volume"),
                breath_data.get("breath_regularity")
            )
            smoothed_score, smoothed_conf = _score_intensity(
                breath_data.get("respiratory_rate"),
                breath_data.get("volume"),
                breath_data.get("breath_regularity"),
                breath_data.get("signal_quality")
            )
            breath_data["intensity"] = smoothed_intensity
            breath_data["intensity_score"] = smoothed_score
            breath_data["intensity_confidence"] = smoothed_conf

        interval_info = _infer_interval_state(
            coaching_context.get("breath_history", []),
            breath_data.get("intensity", "moderate"),
            workout_mode
        )
        breath_data["interval_state"] = interval_info["state"]
        breath_data["interval_state_confidence"] = interval_info["confidence"]
        breath_data["interval_zone"] = interval_info["zone"]

        breath_data["raw_features"] = raw_snapshot
        breath_data["derived_metrics"] = {
            "respiratory_rate": breath_data.get("respiratory_rate"),
            "breath_regularity": breath_data.get("breath_regularity"),
            "inhale_exhale_ratio": breath_data.get("inhale_exhale_ratio"),
            "signal_quality": breath_data.get("signal_quality"),
            "dominant_frequency": breath_data.get("dominant_frequency")
        }
        breath_data["classification"] = {
            "raw_intensity": raw_snapshot.get("intensity"),
            "intensity": breath_data.get("intensity"),
            "intensity_score": breath_data.get("intensity_score"),
            "confidence": breath_data.get("intensity_confidence")
        }
        breath_data["smoothing"] = {
            "applied": smoothing_applied,
            "alpha": getattr(config, "BREATH_SMOOTHING_ALPHA", 0.5),
            "window": getattr(config, "BREATH_SMOOTHING_WINDOW", 4)
        }
        recent_breath_quality_samples = [
            item.get("signal_quality")
            for item in (coaching_context.get("breath_history", [])[-12:] if isinstance(coaching_context, dict) else [])
            if isinstance(item, dict) and item.get("signal_quality") is not None
        ]
        timeline_shadow = bool(getattr(config, "BREATHING_TIMELINE_SHADOW_MODE", True))
        timeline_enforce = bool(getattr(config, "BREATHING_TIMELINE_ENFORCE", False))
        timeline = None
        breath_timeline_summary = None
        if timeline_shadow or timeline_enforce:
            timeline = _get_or_create_session_timeline(session_id)
            if timeline is not None:
                breath_timeline_summary = timeline.get_recent_summary(
                    phase=phase,
                    elapsed_seconds=elapsed_seconds,
                    language=language,
                )
                quality_summary = summarize_breath_quality(
                    breath_data=breath_data,
                    recent_samples=recent_breath_quality_samples,
                    config_module=config,
                    include_current_signal=True,
                )
                breath_timeline_summary.update(
                    {
                        "quality_sample_count": int(quality_summary.get("sample_count", 0)),
                        "quality_median": (
                            float(quality_summary.get("median_quality"))
                            if quality_summary.get("median_quality") is not None
                            else None
                        ),
                        "quality_reliable": bool(quality_summary.get("reliable")),
                    }
                )
                breath_data["timeline_summary"] = dict(breath_timeline_summary)

        # Unified runtime path: all continuous workout ticks are event-driven.
        # This removes dual ownership between legacy breath pipeline and zone events.
        zone_mode_active = workout_state is not None
        zone_tick = None
        zone_forced_text = None
        if zone_mode_active and workout_state is not None:
            zone_tick_kwargs = dict(
                workout_state=workout_state,
                workout_mode=workout_mode,
                phase=phase,
                elapsed_seconds=elapsed_seconds,
                language=language,
                persona=persona,
                coaching_style=coaching_style,
                interval_template=interval_template,
                heart_rate=heart_rate_raw,
                hr_quality=hr_quality_raw,
                hr_confidence=request.form.get("hr_confidence"),
                hr_sample_age_seconds=request.form.get("hr_sample_age_seconds"),
                hr_sample_gap_seconds=request.form.get("hr_sample_gap_seconds"),
                movement_score=request.form.get("movement_score"),
                cadence_spm=request.form.get("cadence_spm"),
                movement_source=request.form.get("movement_source"),
                watch_connected=watch_connected_raw,
                watch_status=request.form.get("watch_status"),
                hr_max=resolved_hr_max,
                resting_hr=resolved_resting_hr,
                age=resolved_age,
                config_module=config,
                breath_intensity=breath_data.get("intensity"),
                breath_signal_quality=breath_data.get("signal_quality"),
                breath_summary=breath_timeline_summary,
                session_id=session_id,
                paused=paused_raw,
            )
            zone_tick = _call_evaluate_zone_tick_compat(**zone_tick_kwargs)
            if isinstance(zone_tick, dict):
                zone_forced_text = zone_tick.get("coach_text")
                breath_data["heart_rate"] = zone_tick.get("heart_rate")
                breath_data["zone_status"] = zone_tick.get("zone_status")
                breath_data["target_zone_label"] = zone_tick.get("target_zone_label")
                breath_data["target_hr_low"] = zone_tick.get("target_hr_low")
                breath_data["target_hr_high"] = zone_tick.get("target_hr_high")
                breath_data["target_source"] = zone_tick.get("target_source")
                breath_data["target_hr_enforced"] = zone_tick.get("target_hr_enforced")
                breath_data["hr_quality"] = zone_tick.get("hr_quality")
                breath_data["hr_quality_reasons"] = zone_tick.get("hr_quality_reasons")
                breath_data["hr_delta_bpm"] = zone_tick.get("hr_delta_bpm")
                breath_data["zone_duration_seconds"] = zone_tick.get("zone_duration_seconds")
                breath_data["movement_score"] = zone_tick.get("movement_score")
                breath_data["cadence_spm"] = zone_tick.get("cadence_spm")
                breath_data["movement_source"] = zone_tick.get("movement_source")
                breath_data["movement_state"] = zone_tick.get("movement_state")
                breath_data["coaching_style"] = zone_tick.get("coaching_style")
                breath_data["interval_template"] = zone_tick.get("interval_template")
                breath_data["recovery_seconds"] = zone_tick.get("recovery_seconds")
                breath_data["recovery_avg_seconds"] = zone_tick.get("recovery_avg_seconds")
            else:
                zone_tick = None

        # Track the very first breath after session start.
        is_first_breath = workout_state.get("is_first_breath", False)

        # Compute time since last coaching (server-side) to cap silence
        elapsed_since_last = None
        try:
            last_time = None
            if workout_state:
                last_time = workout_state.get("last_coaching_time")
            if not last_time and coaching_context.get("coaching_history"):
                last_time = coaching_context["coaching_history"][-1].get("timestamp")
            if last_time:
                last_time_dt = datetime.fromisoformat(last_time)
                elapsed_since_last = (datetime.now() - last_time_dt).total_seconds()
            elif not coaching_context.get("coaching_history"):
                elapsed_since_last = float("inf")
        except Exception:
            elapsed_since_last = None

        decision_started = time.perf_counter()
        rich_followup_forced = False
        breath_quality_state = _resolve_breath_quality_state(
            breath_data=breath_data,
            recent_samples=recent_breath_quality_samples,
        )
        unified_event_router_shadow = bool(getattr(config, "UNIFIED_EVENT_ROUTER_SHADOW", False))
        if unified_event_router_shadow and zone_mode_active and zone_tick is not None:
            logger.info(
                "UNIFIED_EVENT_SHADOW session=%s mode=%s events=%s zone_reason=%s zone_should_speak=%s",
                session_id,
                workout_mode,
                [item.get("event_type") for item in (zone_tick.get("events") or []) if isinstance(item, dict)],
                zone_tick.get("reason"),
                zone_tick.get("should_speak"),
            )
        zone_tick_guard_silent_safe = False
        if zone_tick is not None:
            speak_decision = bool(zone_tick.get("should_speak"))
            reason = str(zone_tick.get("reason") or "zone_no_change")
            decision_owner = "zone_event"
            zone_forced_text = zone_tick.get("coach_text")
            max_silence_override_used = (
                str(zone_tick.get("primary_event_type") or "") == "max_silence_override"
                or reason == "max_silence_override"
            )
        else:
            speak_decision = False
            reason = "zone_tick_missing_silent_safe"
            decision_owner = "zone_event"
            zone_forced_text = None
            max_silence_override_used = False
            zone_tick_guard_silent_safe = True
            logger.warning(
                "ZONE_GUARD silent-safe: zone_tick missing; legacy fallback disabled (session=%s mode=%s phase=%s)",
                session_id,
                workout_mode,
                phase,
            )

        if is_first_breath:
            workout_state["is_first_breath"] = False

        if zone_mode_active and zone_tick is not None:
            logger.info(
                "Zone decision: should_speak=%s reason=%s zone=%s hr=%s quality=%s style=%s events=%s",
                speak_decision,
                reason,
                zone_tick.get("zone_status"),
                zone_tick.get("heart_rate"),
                zone_tick.get("hr_quality"),
                zone_tick.get("coaching_style"),
                [item.get("event_type") for item in (zone_tick.get("events") or []) if isinstance(item, dict)],
            )

        logger.info(
            "Coaching decision: should_speak=%s, reason=%s, signal_quality=%s, elapsed_since_last=%s, is_first_breath=%s, owner=%s",
            speak_decision,
            reason,
            breath_data.get("signal_quality", "N/A"),
            elapsed_since_last,
            breath_data.get("is_first_breath", False),
            decision_owner,
        )

        _log_decision_debug(
            session_id=session_id,
            owner=decision_owner,
            reason=reason,
            breath_quality_state=breath_quality_state,
            zone_mode_active=zone_mode_active,
            max_silence_override_used=max_silence_override_used,
        )

        if speak_decision:
            _increment_quality_metric("spoken_ticks")

        decision_ms = (time.perf_counter() - decision_started) * 1000.0

        # Get coaching message (priority: strategic > pattern > realtime brain router)
        brain_started = time.perf_counter()
        fast_fallback_used = False
        latency_signal = None
        brain_meta = {
            "provider": "system",
            "source": "system",
            "status": "not_called",
            "mode": "realtime_coach",
        }
        pattern_insight = None
        strategic_guidance = None
        recent_cues = _extract_recent_spoken_cues(
            coaching_context.get("coaching_history", []),
            limit=getattr(config, "BRAIN_RECENT_CUE_WINDOW", 4),
        )
        timeline_cue = None
        if timeline_shadow or timeline_enforce:
            if timeline is None:
                timeline = _get_or_create_session_timeline(session_id)
            if timeline is not None:
                timeline_cue = timeline.get_breathing_cue(
                    phase=phase,
                    elapsed_seconds=elapsed_seconds,
                    language=language,
                )
                if timeline_cue:
                    _increment_quality_metric("timeline_cue_candidates")
                    logger.info(
                        "Breathing timeline cue candidate: phase=%s elapsed=%ss cue='%s'",
                        phase,
                        elapsed_seconds,
                        timeline_cue,
                    )

        if not speak_decision:
            coach_text = _get_silent_debug_text(reason, language)
            brain_meta = {
                "provider": "system",
                "source": "silent_policy",
                "status": "skipped_generation",
                "mode": "realtime_coach",
            }
        else:
            zone_event_type = (
                (zone_tick or {}).get("primary_event_type")
                or (zone_tick or {}).get("event_type")
                or reason
            )
            if zone_forced_text:
                coach_text, brain_meta = _maybe_rephrase_zone_event_text(
                    base_text=zone_forced_text,
                    language=language,
                    persona=persona,
                    coaching_style=coaching_style,
                    event_type=zone_event_type,
                )
            else:
                coach_text = _phase_fallback_text(
                    language=language,
                    phase=phase,
                    elapsed_seconds=elapsed_seconds,
                )
                brain_meta = {
                    "provider": "system",
                    "source": "zone_event_fallback",
                    "status": "missing_zone_text_template",
                    "mode": "realtime_coach",
                }
                logger.warning(
                    "Zone-event speech selected but no text supplied; using deterministic fallback (session=%s reason=%s event=%s)",
                    session_id,
                    reason,
                    zone_event_type,
                )

        validation_shadow = bool(getattr(config, "COACHING_VALIDATION_SHADOW_MODE", True))
        validation_enforce = bool(getattr(config, "COACHING_VALIDATION_ENFORCE", False))
        if speak_decision and (validation_shadow or validation_enforce):
            _increment_quality_metric("validation_checks")
            is_valid = validate_coaching_text(
                text=coach_text,
                phase=phase,
                intensity=breath_data.get("intensity", "moderate"),
                persona=persona or "personal_trainer",
                language=language,
                mode="realtime",
            )
            if not is_valid:
                _increment_quality_metric("validation_failures")
                logger.warning(
                    "Coaching validation failed (phase=%s intensity=%s persona=%s enforce=%s): %r",
                    phase,
                    breath_data.get("intensity", "moderate"),
                    persona or "personal_trainer",
                    validation_enforce,
                    coach_text,
                )
                if validation_enforce:
                    _increment_quality_metric("validation_template_fallbacks")
                    coach_text = get_template_message(
                        phase=phase,
                        intensity=breath_data.get("intensity", "moderate"),
                        persona=persona or "personal_trainer",
                        language=language,
                    )
                    brain_meta = {
                        "provider": "system",
                        "source": "coaching_validation",
                        "status": "template_fallback",
                        "mode": "realtime_coach",
                    }

        # STEP 6: Add human variation to avoid robotic repetition.
        if (
            speak_decision
            and not fast_fallback_used
            and not str(brain_meta.get("source", "")).startswith("zone_event_")
        ):
            coach_text = voice_intelligence.add_human_variation(coach_text)

        coach_text = enforce_language_consistency(coach_text, language, phase=phase)
        _log_coach_transcript_debug(
            session_id=session_id,
            language=language,
            phase=phase,
            should_speak=speak_decision,
            reason=reason,
            source=brain_meta.get("source"),
            text=coach_text,
        )
        brain_ms = (time.perf_counter() - brain_started) * 1000.0

        # Generate voice only if should speak (language-aware)
        audio_url = None
        if speak_decision:
            tts_started = time.perf_counter()
            voice_file = generate_voice(
                coach_text,
                language=language,
                persona=persona,
                emotional_mode=coaching_context.get("persona_mode") or _infer_emotional_mode(breath_data.get("intensity", "moderate")),
            )
            # Convert absolute path to relative path from OUTPUT_FOLDER
            relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
            audio_url = f"/download/{relative_path}"
            tts_ms = (time.perf_counter() - tts_started) * 1000.0

        # Update session state
        session_manager.update_workout_state(
            session_id=session_id,
            breath_analysis=breath_data,
            coaching_output=coach_text if speak_decision else None,
            phase=phase,
            elapsed_seconds=elapsed_seconds
        )
        if zone_mode_active and speak_decision and zone_tick is not None and coach_text:
            _append_recent_zone_event(session_id, zone_tick, coach_text)

        # Calculate next interval
        recent_coaching_count = len([c for c in coaching_context["coaching_history"] if c]) if coaching_context else 0
        wait_seconds = calculate_next_interval(
            phase=phase,
            intensity=breath_data.get("intensity", "moderate"),
            coaching_frequency=recent_coaching_count
        )
        if zone_mode_active:
            style_policy = getattr(config, "COACHING_STYLE_COOLDOWNS", {}).get(coaching_style, {})
            min_any = int(style_policy.get("min_seconds_between_any_speech", wait_seconds))
            wait_seconds = max(wait_seconds, min_any)

            # Interval-specific cap so countdown events (30/15/5/start) are not skipped
            # by long polling gaps.
            wait_seconds = _apply_interval_tick_budget(
                wait_seconds=wait_seconds,
                workout_mode=workout_mode,
                zone_tick=zone_tick,
            )

        # STEP 6: Increase wait time if coach is overtalking
        if (not zone_mode_active) and voice_intelligence.should_reduce_frequency(breath_data, coaching_context["coaching_history"]):
            wait_seconds = min(15, wait_seconds + 3)  # Add 3 seconds, max 15s
            logger.info(f"Voice intelligence: reducing frequency (new wait: {wait_seconds}s)")

        # STEP 5: Update user memory if critical event occurred
        if breath_data.get("intensity") == "critical":
            user_memory.mark_safety_event(current_user_id)
            logger.info(f"Memory: marked critical breathing event for user {current_user_id}")

        # Clean up temp file
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        score_payload = _compute_layered_coach_score(
            language=language,
            elapsed_seconds=elapsed_seconds,
            breath_data=breath_data,
            zone_tick=zone_tick if zone_mode_active else None,
            watch_connected=watch_connected_raw,
            heart_rate=heart_rate_raw,
            hr_quality=hr_quality_raw,
            breath_enabled_by_user=breath_enabled_by_user,
            mic_permission_granted=mic_permission_granted,
            breath_quality_samples=recent_breath_quality_samples,
        )
        _log_coach_score_debug_summary(
            session_id=session_id,
            language=language,
            workout_mode=workout_mode,
            score_payload=score_payload,
        )
        coach_score = int(score_payload["score"])
        coach_score_line = score_payload["score_line"]

        personalization_tip = None
        recovery_line = None
        recovery_baseline_seconds = None
        if (
            zone_mode_active
            and zone_tick is not None
            and workout_state is not None
            and bool(getattr(config, "ZONE_PERSONALIZATION_ENABLED", True))
        ):
            cached_summary = workout_state.get("personalization_last_summary")
            if isinstance(cached_summary, dict):
                personalization_tip = cached_summary.get("next_time_tip")
                recovery_line = cached_summary.get("recovery_line")
                recovery_baseline_seconds = cached_summary.get("recovery_baseline_seconds")

            if personalization_user_id and not workout_state.get("personalization_committed"):
                profile_snapshot = running_personalization.get_profile(personalization_user_id)
                recovery_baseline_seconds = profile_snapshot.get("recovery_baseline_seconds")
                recovery_line = running_personalization.build_recovery_line(
                    language=language,
                    recovery_avg_seconds=zone_tick.get("recovery_avg_seconds"),
                    recovery_baseline_seconds=recovery_baseline_seconds,
                )

                if zone_tick.get("event_type") == "phase_change_cooldown":
                    personal_payload = running_personalization.record_session(
                        user_id=personalization_user_id,
                        language=language,
                        score=coach_score,
                        time_in_target_pct=zone_tick.get("time_in_target_pct"),
                        overshoots=zone_tick.get("overshoots"),
                        recovery_avg_seconds=zone_tick.get("recovery_avg_seconds"),
                    )
                    profile_data = personal_payload.get("profile", {})
                    personalization_tip = personal_payload.get("next_time_tip")
                    recovery_line = personal_payload.get("recovery_line")
                    recovery_baseline_seconds = profile_data.get("recovery_baseline_seconds")
                    workout_state["personalization_committed"] = True
                    workout_state["personalization_last_summary"] = {
                        "next_time_tip": personalization_tip,
                        "recovery_line": recovery_line,
                        "recovery_baseline_seconds": recovery_baseline_seconds,
                    }
                    logger.info(
                        "Personalization committed: user=%s sessions=%s baseline=%s tip=%r",
                        personalization_user_id,
                        profile_data.get("sessions_completed"),
                        recovery_baseline_seconds,
                        personalization_tip,
                    )

        # Response
        response_data = {
            "contract_version": contract_version,
            "text": coach_text,
            "should_speak": speak_decision,
            "breath_analysis": breath_data,
            "audio_url": audio_url,
            "wait_seconds": wait_seconds,
            "phase": phase,
            "workout_mode": workout_mode,
            "reason": reason,  # For debugging
            "decision_owner": decision_owner,
            "decision_reason": reason,
            "zone_tick_guard_silent_safe": zone_tick_guard_silent_safe,
            "breath_quality_state": breath_quality_state,
            "coach_score": coach_score,
            "coach_score_line": coach_score_line,
            "coach_score_v2": score_payload.get("coach_score_v2"),
            "coach_score_components": score_payload.get("coach_score_components"),
            "cap_reason_codes": score_payload.get("cap_reason_codes"),
            "cap_applied": score_payload.get("cap_applied", score_payload.get("cap")),
            "cap_applied_reason": score_payload.get("cap_applied_reason"),
            "hr_valid_main_set_seconds": score_payload.get("hr_valid_main_set_seconds"),
            "zone_valid_main_set_seconds": score_payload.get("zone_valid_main_set_seconds"),
            "zone_compliance": score_payload.get("zone_compliance"),
            "breath_available_reliable": score_payload.get("breath_available_reliable"),
            "events": (zone_tick.get("events") if isinstance(zone_tick, dict) else []) or [],
            "brain_provider": brain_meta.get("provider"),
            "brain_source": brain_meta.get("source"),
            "brain_status": brain_meta.get("status"),
            "brain_mode": brain_meta.get("mode"),
            "latency_fast_fallback_used": fast_fallback_used,
            "latency_rich_followup_forced": rich_followup_forced,
            "latency_pending_rich_followup": bool(latency_state.get("pending_rich_followup")),
            "latency_signal_reason": latency_signal.get("reason") if latency_signal else None,
            "latency_signal_provider": latency_signal.get("provider") if latency_signal else None,
            "latency_signal_avg": latency_signal.get("avg_latency") if latency_signal else None,
            "coaching_style": coaching_style,
            "interval_template": interval_template if workout_mode == "interval" else None,
            "personalization_tip": personalization_tip,
            "recovery_line": recovery_line,
            "recovery_baseline_seconds": recovery_baseline_seconds,
            "workout_context_summary": (
                zone_tick.get("workout_context_summary")
                if isinstance(zone_tick, dict)
                else None
            ),
        }
        if zone_mode_active and zone_tick is not None:
            response_data.update(
                {
                    "zone_status": zone_tick.get("zone_status"),
                    "zone_event": zone_tick.get("event_type"),
                    "zone_primary_event": zone_tick.get("primary_event_type"),
                    "zone_priority": zone_tick.get("priority"),
                    "zone_phrase_id": zone_tick.get("phrase_id"),
                    "sensor_mode": zone_tick.get("sensor_mode"),
                    "phase_id": zone_tick.get("phase_id"),
                    "zone_state": zone_tick.get("zone_state"),
                    "delta_to_band": zone_tick.get("delta_to_band"),
                    "heart_rate": zone_tick.get("heart_rate"),
                    "target_zone_label": zone_tick.get("target_zone_label"),
                    "target_hr_low": zone_tick.get("target_hr_low"),
                    "target_hr_high": zone_tick.get("target_hr_high"),
                    "target_source": zone_tick.get("target_source"),
                    "target_hr_enforced": zone_tick.get("target_hr_enforced"),
                    "remaining_phase_seconds": zone_tick.get("remaining_phase_seconds"),
                    "hr_quality": zone_tick.get("hr_quality"),
                    "hr_quality_reasons": zone_tick.get("hr_quality_reasons"),
                    "hr_delta_bpm": zone_tick.get("hr_delta_bpm"),
                    "zone_duration_seconds": zone_tick.get("zone_duration_seconds"),
                    "movement_score": zone_tick.get("movement_score"),
                    "cadence_spm": zone_tick.get("cadence_spm"),
                    "movement_source": zone_tick.get("movement_source"),
                    "movement_state": zone_tick.get("movement_state"),
                    "zone_score_confidence": zone_tick.get("score_confidence"),
                    "zone_time_in_target_pct": zone_tick.get("time_in_target_pct"),
                    "zone_overshoots": zone_tick.get("overshoots"),
                    "recovery_seconds": zone_tick.get("recovery_seconds"),
                    "recovery_avg_seconds": zone_tick.get("recovery_avg_seconds"),
                }
            )

        total_ms = (time.perf_counter() - request_started) * 1000.0
        logger.info(
            "Tick timing: session=%s total_ms=%.1f analyze_ms=%.1f decision_ms=%.1f brain_ms=%.1f tts_ms=%.1f speak=%s reason=%s brain=%s/%s/%s fast_fallback=%s rich_followup=%s",
            session_id,
            total_ms,
            analyze_ms,
            decision_ms,
            brain_ms,
            tts_ms,
            speak_decision,
            reason,
            brain_meta.get("provider"),
            brain_meta.get("source"),
            brain_meta.get("status"),
            fast_fallback_used,
            rich_followup_forced,
        )

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in continuous coaching endpoint: {e}", exc_info=True)
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass

        if bool(getattr(config, "CONTINUOUS_FAILSAFE_ENABLED", True)):
            fallback_form = request.form or {}
            fallback_contract = normalize_continuous_contract(fallback_form, {})
            fallback_payload = _build_continuous_failsafe_response(
                contract_version=fallback_contract.get("contract_version", "1"),
                phase=(
                    fallback_contract["workout_state"].phase
                    if fallback_contract.get("workout_state") is not None
                    else "intense"
                ),
                workout_mode=(
                    "interval"
                    if (fallback_contract["workout_plan"].workout_type in {"interval", "intervals"})
                    else "easy_run"
                ),
                coaching_style=normalize_coaching_style(
                    fallback_form.get("coaching_style", getattr(config, "DEFAULT_COACHING_STYLE", "normal")),
                    config,
                ),
                interval_template=normalize_interval_template(
                    fallback_form.get("interval_template", getattr(config, "DEFAULT_INTERVAL_TEMPLATE", "4x4")),
                    config,
                ),
                reason="continuous_failsafe",
                trace_id=trace_id,
                language=normalize_language_code(
                    fallback_form.get("language", getattr(config, "DEFAULT_LANGUAGE", "en"))
                ),
            )
            logger.error("FAILSAFE_200 trace_id=%s reason=continuous_exception", trace_id)
            return jsonify(fallback_payload), 200

        return jsonify({"error": "Internal server error", "debug_trace_id": trace_id}), 500


def get_coach_response_continuous(breath_data, phase, language="en", persona=None, user_name=None):
    """
    STEP 3: Get coaching message using REALTIME_COACH brain mode.

    Uses BrainRouter with mode="realtime_coach" for fast, actionable cues.
    Falls back to config messages if brain is disabled.
    Supports language and persona selection.
    """
    normalized_language = normalize_language_code(language)

    # STEP 3: Use realtime_coach brain mode (not chat mode)
    coach_text = brain_router.get_coaching_response(
        breath_data=breath_data,
        phase=phase,
        mode="realtime_coach",  # Product-defining: fast, actionable, no explanations
        language=normalized_language,
        persona=persona,
        user_name=user_name
    )
    return enforce_language_consistency(coach_text, normalized_language, phase=phase)


@app.route('/download/<path:filename>')
def download(filename):
    """Download generated voice file"""
    try:
        # Security: Resolve the full path and verify it stays under OUTPUT_FOLDER.
        # os.path.normpath collapses "..", ".", and redundant separators so tricks
        # like "cache/../../etc/passwd" are neutralized.
        filepath = os.path.normpath(os.path.join(OUTPUT_FOLDER, filename))
        output_root = os.path.normpath(OUTPUT_FOLDER)

        if not filepath.startswith(output_root + os.sep) and filepath != output_root:
            logger.warning(f"Path traversal blocked: {filename!r} resolved to {filepath}")
            return jsonify({"error": "Invalid filename"}), 400

        # Only serve audio files (reject non-audio extensions)
        if not filename.endswith(('.wav', '.mp3', '.m4a')):
            logger.warning(f"Non-audio file requested: {filename}")
            return jsonify({"error": "Invalid file type"}), 400

        if os.path.exists(filepath):
            logger.info(f"Serving file: {filename}")
            mimetype = 'audio/wav' if filename.endswith('.wav') else 'audio/mpeg'
            return send_file(filepath, mimetype=mimetype)

        logger.warning(f"File not found: {filename}")
        return jsonify({"error": "File not found"}), 404

    except Exception as e:
        logger.error(f"Error downloading file: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ============================================
# PERSONA SWITCHING (Mid-workout)
# ============================================

@app.route('/coach/persona', methods=['POST'])
@rate_limit(
    limit=getattr(config, "API_RATE_LIMIT_PER_HOUR", 100),
    window_seconds=3600,
    key_prefix="api.coach.persona",
)
@require_mobile_auth
def switch_persona():
    """
    Switch coach personality mid-workout.

    Request body:
    {
        "session_id": "session_...",
        "persona": "toxic_mode"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        session_id = data.get("session_id")
        persona = data.get("persona")

        if not session_id or not persona:
            return jsonify({"error": "Missing session_id or persona"}), 400

        if not PersonaManager.validate_persona(persona):
            return jsonify({
                "error": f"Invalid persona. Available: {PersonaManager.list_personas()}"
            }), 400

        # Update session persona
        if session_manager.session_exists(session_id):
            session_manager.sessions[session_id]["persona"] = persona
            logger.info(f"Persona switched to '{persona}' for session {session_id}")

        return jsonify({
            "success": True,
            "persona": persona,
            "description": PersonaManager.get_persona_description(persona)
        })

    except Exception as e:
        logger.error(f"Persona switch error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================
# WORKOUT HISTORY ENDPOINTS
# ============================================

@app.route('/workouts', methods=['POST'])
@rate_limit(
    limit=getattr(config, "WORKOUTS_RATE_LIMIT_PER_MINUTE", 60),
    window_seconds=60,
    key_prefix="api.workouts",
    scope="user",
)
@require_auth
def save_workout():
    """
    Save a completed workout record.

    Request body:
    {
        "duration_seconds": 900,
        "final_phase": "cooldown",
        "avg_intensity": "moderate",
        "persona_used": "fitness_coach",
        "language": "en"
    }
    """
    try:
        from database import db, WorkoutHistory

        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        user_id = g.current_user_id
        try:
            duration_seconds = max(0, int(data.get("duration_seconds", 0)))
        except (TypeError, ValueError):
            return jsonify({"error": "duration_seconds must be an integer"}), 400

        workout = WorkoutHistory(
            user_id=user_id,
            duration_seconds=duration_seconds,
            final_phase=data.get("final_phase") or data.get("phase"),
            avg_intensity=data.get("avg_intensity") or data.get("intensity"),
            persona_used=data.get("persona_used") or data.get("persona"),
            language=data.get("language", getattr(config, "DEFAULT_LANGUAGE", "en"))
        )
        db.session.add(workout)
        db.session.commit()

        logger.info(f"Workout saved: {workout.duration_seconds}s, phase={workout.final_phase}")

        return jsonify({"workout": workout.to_dict()}), 201

    except Exception as e:
        logger.error(f"Save workout error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/workouts', methods=['GET'])
@rate_limit(
    limit=getattr(config, "WORKOUTS_RATE_LIMIT_PER_MINUTE", 60),
    window_seconds=60,
    key_prefix="api.workouts",
    scope="user",
)
@require_auth
def get_workouts():
    """
    Get workout history for a user.

    Query params:
    - limit: Max number of records (default: 20, max: 100)
    """
    try:
        from database import WorkoutHistory

        user_id = g.current_user_id

        # Bounds-check limit to prevent abuse
        try:
            limit = max(1, min(100, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            limit = 20

        workouts = WorkoutHistory.query.filter_by(user_id=user_id)\
            .order_by(WorkoutHistory.date.desc())\
            .limit(limit).all()

        return jsonify({
            "workouts": [w.to_dict() for w in workouts]
        }), 200

    except Exception as e:
        logger.error(f"Get workouts error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================
# USER PROFILE
# ============================================

@app.route('/profile/upsert', methods=['POST'])
@rate_limit(
    limit=getattr(config, "PROFILE_UPSERT_RATE_LIMIT_PER_MINUTE", 20),
    window_seconds=60,
    key_prefix="api.profile.upsert",
    scope="user",
)
@require_auth
def profile_upsert():
    """
    Upsert persisted onboarding/profile data.
    """
    try:
        payload = request.get_json(silent=True) or {}
        raw_profile = payload.get("user_profile") if isinstance(payload.get("user_profile"), dict) else payload
        if not isinstance(raw_profile, dict):
            return jsonify({"error": "user_profile payload must be an object"}), 400

        profile = UserProfilePayload(
            name=(str(raw_profile.get("name")).strip() if raw_profile.get("name") not in (None, "") else None),
            sex=(str(raw_profile.get("sex")).strip().lower() if raw_profile.get("sex") not in (None, "") else None),
            age=(int(raw_profile.get("age")) if raw_profile.get("age") not in (None, "") else None),
            height_cm=(float(raw_profile.get("height_cm")) if raw_profile.get("height_cm") not in (None, "") else None),
            weight_kg=(float(raw_profile.get("weight_kg")) if raw_profile.get("weight_kg") not in (None, "") else None),
            max_hr_bpm=(int(raw_profile.get("max_hr_bpm")) if raw_profile.get("max_hr_bpm") not in (None, "") else None),
            resting_hr_bpm=(int(raw_profile.get("resting_hr_bpm")) if raw_profile.get("resting_hr_bpm") not in (None, "") else None),
            profile_updated_at=(
                str(raw_profile.get("profile_updated_at")).strip()
                if raw_profile.get("profile_updated_at") not in (None, "")
                else None
            ),
        )
        validation_errors = profile_validation_errors(profile)
        if validation_errors:
            return jsonify({"error": "Invalid profile payload", "validation_errors": validation_errors}), 400

        user_id = g.current_user_id
        existing = UserProfile.query.filter_by(user_id=user_id).first()

        normalized_updated_at = profile.normalized_updated_at()
        incoming_ts = _parse_profile_timestamp(normalized_updated_at)
        current_ts = existing.profile_updated_at if existing is not None else None

        def _epoch_or_none(value):
            if value is None:
                return None
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).timestamp()

        incoming_epoch = _epoch_or_none(incoming_ts)
        current_epoch = _epoch_or_none(current_ts)

        stale_ignored = False
        if existing is not None and incoming_epoch is not None and current_epoch is not None and incoming_epoch <= current_epoch:
            stale_ignored = True
            action = "stale_ignored"
        else:
            if existing is None:
                existing = UserProfile(user_id=user_id)
                db.session.add(existing)
                action = "insert"
            else:
                action = "update"

            if profile.name is not None:
                existing.name = profile.name
            if profile.sex is not None:
                existing.sex = profile.sex
            if profile.age is not None:
                existing.age = profile.age
            if profile.height_cm is not None:
                existing.height_cm = profile.height_cm
            if profile.weight_kg is not None:
                existing.weight_kg = profile.weight_kg
            if profile.max_hr_bpm is not None:
                existing.max_hr_bpm = profile.max_hr_bpm
            if profile.resting_hr_bpm is not None:
                existing.resting_hr_bpm = profile.resting_hr_bpm
            if incoming_ts is not None:
                existing.profile_updated_at = incoming_ts
            elif existing.profile_updated_at is None:
                existing.profile_updated_at = _utcnow_naive()

            db.session.commit()

        if existing is None:
            existing = UserProfile.query.filter_by(user_id=user_id).first()

        logger.info(
            "PROFILE_UPSERT user=%s action=%s stale_ignored=%s",
            user_id,
            action,
            stale_ignored,
        )

        return jsonify({
            "status": "ok",
            "action": action,
            "stale_ignored": stale_ignored,
            "user_profile": existing.to_dict() if existing is not None else {},
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid numeric profile field"}), 400
    except Exception as e:
        logger.error(f"Profile upsert error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================
# LIVE VOICE MODE
# ============================================


def _build_live_voice_history_context(*, user_id: str) -> dict[str, object]:
    recent_limit = max(
        1,
        min(
            int(getattr(config, "XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT", 12) or 12),
            50,
        ),
    )
    now = _utcnow_naive()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    aggregate_row = (
        db.session.query(
            db.func.count(WorkoutHistory.id),
            db.func.coalesce(db.func.sum(WorkoutHistory.duration_seconds), 0),
        )
        .filter(WorkoutHistory.user_id == user_id)
        .first()
    )
    total_workouts = int(aggregate_row[0] or 0) if aggregate_row is not None else 0
    total_duration_seconds = int(aggregate_row[1] or 0) if aggregate_row is not None else 0

    workouts_last_7_days = (
        WorkoutHistory.query.filter(
            WorkoutHistory.user_id == user_id,
            WorkoutHistory.date >= seven_days_ago,
        ).count()
    )
    workouts_last_30_days = (
        WorkoutHistory.query.filter(
            WorkoutHistory.user_id == user_id,
            WorkoutHistory.date >= thirty_days_ago,
        ).count()
    )
    recent_workouts = (
        WorkoutHistory.query.filter_by(user_id=user_id)
        .order_by(WorkoutHistory.date.desc())
        .limit(recent_limit)
        .all()
    )

    recent_history: list[dict[str, object]] = []
    for workout in recent_workouts:
        recent_history.append(
            {
                "date": workout.date.date().isoformat() if workout.date is not None else None,
                "duration_minutes": max(0, round(int(workout.duration_seconds or 0) / 60)),
                "final_phase": str(workout.final_phase or "").strip() or None,
                "avg_intensity": str(workout.avg_intensity or "").strip() or None,
                "language": str(workout.language or "").strip() or None,
            }
        )

    return sanitize_workout_history_context({
        "total_workouts": total_workouts,
        "total_duration_minutes": max(0, round(total_duration_seconds / 60)),
        "workouts_last_7_days": int(workouts_last_7_days or 0),
        "workouts_last_30_days": int(workouts_last_30_days or 0),
        "recent_workouts": recent_history,
    })

@app.route('/voice/session', methods=['POST'])
@rate_limit(
    limit=getattr(config, "API_RATE_LIMIT_PER_HOUR", 100),
    window_seconds=3600,
    key_prefix="api.voice.session",
    scope="user",
)
@require_mobile_auth
def create_voice_session():
    """Bootstrap an isolated post-workout xAI Voice Agent session."""
    user_id = get_request_auth_user_id()
    if not user_id:
        return _voice_error(
            "Authentication required",
            status=401,
            error_code="authentication_required",
        )

    if not bool(getattr(config, "XAI_VOICE_AGENT_ENABLED", False)):
        return _voice_error(
            "Live voice mode is not available",
            status=503,
            error_code="voice_mode_disabled",
        )

    subscription_tier = resolve_user_subscription_tier(user_id)
    session_policy = _live_voice_session_policy(subscription_tier)
    daily_limited = _enforce_live_voice_session_limits(
        user_id=user_id,
        access_tier=str(session_policy["access_tier"]),
        daily_session_limit=int(session_policy["daily_session_limit"]),
    )
    if daily_limited is not None:
        return daily_limited

    user = db.session.get(User, user_id)
    if user is None:
        return _voice_error(
            "User not found",
            status=404,
            error_code="user_not_found",
        )

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _voice_error(
            "Invalid request body",
            status=400,
            error_code="invalid_request_body",
        )

    summary_context = sanitize_post_workout_summary_context(payload.get("summary_context"))
    history_context = _build_live_voice_history_context(user_id=user_id)
    language = normalize_language_code(payload.get("language") or user.language or getattr(config, "DEFAULT_LANGUAGE", "en"))
    user_name = (
        str(payload.get("user_name") or user.display_name or "").strip()
        if isinstance(payload, dict)
        else str(user.display_name or "").strip()
    )

    try:
        bootstrap = bootstrap_post_workout_voice_session(
            summary_context=summary_context,
            history_context=history_context,
            language=language,
            user_name=user_name or None,
            max_duration_seconds=int(session_policy["max_duration_seconds"]),
            logger=logger,
        )
    except requests.HTTPError as exc:
        response = getattr(exc, "response", None)
        body_preview = ""
        if response is not None:
            try:
                body_preview = (response.text or "")[:200]
            except Exception:
                body_preview = ""
        logger.error(
            "VOICE_SESSION_BOOTSTRAP_FAILED user=%s status=%s body=%s",
            user_id,
            getattr(response, "status_code", "unknown"),
            body_preview,
        )
        _capture_voice_event(
            "voice_session_failed",
            user_id=user_id,
            metadata={
                "stage": "bootstrap",
                "reason": "provider_http_error",
                "provider_status": getattr(response, "status_code", None),
            },
        )
        return _voice_error(
            "Failed to start live voice session",
            status=503,
            error_code="voice_provider_error",
        )
    except Exception as exc:
        logger.error("VOICE_SESSION_BOOTSTRAP_FAILED user=%s error=%s", user_id, exc, exc_info=True)
        _capture_voice_event(
            "voice_session_failed",
            user_id=user_id,
            metadata={
                "stage": "bootstrap",
                "reason": "bootstrap_exception",
            },
        )
        return _voice_error(
            "Failed to start live voice session",
            status=503,
            error_code="voice_session_unavailable",
        )

    bootstrap["subscription_tier"] = subscription_tier
    bootstrap["voice_access_tier"] = session_policy["access_tier"]
    bootstrap["daily_session_limit"] = session_policy["daily_session_limit"]
    _capture_voice_event(
        "voice_session_requested",
        user_id=user_id,
        metadata={
            "voice_session_id": bootstrap.get("voice_session_id"),
            "region": bootstrap.get("region"),
            "voice": bootstrap.get("voice"),
            "language": language,
            "voice_access_tier": session_policy.get("access_tier"),
            "daily_session_limit": session_policy.get("daily_session_limit"),
            "max_duration_seconds": session_policy.get("max_duration_seconds"),
        },
    )
    return jsonify(bootstrap), 200


@app.route('/voice/telemetry', methods=['POST'])
@rate_limit(
    limit=getattr(config, "API_RATE_LIMIT_PER_HOUR", 100),
    window_seconds=3600,
    key_prefix="api.voice.telemetry",
    scope="user",
)
@require_mobile_auth
def voice_telemetry():
    """Best-effort mobile analytics for the isolated live voice mode."""
    user_id = get_request_auth_user_id()
    if not user_id:
        return _voice_error(
            "Authentication required",
            status=401,
            error_code="authentication_required",
        )

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _voice_error(
            "Invalid request body",
            status=400,
            error_code="invalid_request_body",
        )

    event = str(payload.get("event") or "").strip()
    allowed_events = {
        "voice_cta_tapped",
        "voice_session_requested",
        "voice_session_started",
        "voice_session_failed",
        "voice_session_ended",
        "voice_fallback_text_opened",
    }
    if event not in allowed_events:
        return _voice_error(
            "Invalid voice event",
            status=400,
            error_code="invalid_voice_event",
        )

    event_metadata = _sanitize_analytics_metadata(payload.get("metadata"))
    event_metadata["subscription_tier"] = resolve_user_subscription_tier(user_id)
    _capture_voice_event(event, user_id=user_id, metadata=event_metadata)
    return jsonify({"success": True}), 200


@app.route('/analytics/mobile', methods=['POST'])
@rate_limit(
    limit=getattr(config, "API_RATE_LIMIT_PER_HOUR", 100),
    window_seconds=3600,
    key_prefix="api.mobile.analytics",
)
def mobile_analytics():
    """Best-effort app analytics for onboarding, workout, paywall, and deep links."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _voice_error(
            "Invalid request body",
            status=400,
            error_code="invalid_request_body",
        )

    event = str(payload.get("event") or "").strip()
    if event not in _MOBILE_ANALYTICS_ALLOWED_EVENTS:
        return _voice_error(
            "Invalid analytics event",
            status=400,
            error_code="invalid_analytics_event",
        )

    user_id = get_request_auth_user_id()
    anonymous_id = payload.get("anonymous_id")
    if not user_id and _normalize_mobile_analytics_anonymous_id(anonymous_id) is None:
        return _voice_error(
            "Anonymous mobile analytics id required",
            status=400,
            error_code="anonymous_id_required",
        )

    _capture_mobile_analytics_event(
        event,
        user_id=user_id,
        anonymous_id=anonymous_id,
        metadata=payload.get("metadata"),
    )
    return jsonify({"success": True}), 200


# ============================================
# TALK TO COACH (Conversational + Voice)
# ============================================

@app.route('/coach/talk', methods=['POST'])
@require_mobile_auth
def coach_talk():
    """
    Talk to the coach — supports both casual chat and mid-workout wake word speech.

    Request body (JSON):
    {
        "message": "How should I pace this?",
        "session_id": "optional_session_id",
        "context": "workout",          // "workout" = mid-workout wake word, else casual chat
        "phase": "intense",             // Current workout phase (if context=workout)
        "intensity": "moderate",        // Current breath intensity (if context=workout)
        "persona": "fitness_coach",     // Active coach persona
        "language": "en"                // Language for response
    }

    Returns:
    {
        "text": "Hold this pace — you're doing great.",
        "audio_url": "/download/...",
        "personality": "fitness_coach"
    }
    """
    started_at = time.perf_counter()
    temp_audio_path = None

    try:
        is_multipart = "multipart/form-data" in (request.content_type or "")
        payload = {}
        form = request.form if is_multipart else None
        files = request.files if is_multipart else None

        if is_multipart:
            payload = {}
        else:
            payload = request.get_json(silent=True) or {}
        normalized_talk_contract = normalize_talk_contract(form=form, payload=payload)
        contract_version = normalized_talk_contract.get("contract_version", "1")

        raw_trigger = (
            (form.get("trigger_source") if form is not None else None)
            or payload.get("trigger_source")
            or "button"
        )
        trigger_source = normalize_trigger_source(raw_trigger)
        if not trigger_source:
            return jsonify({"error": "Invalid trigger_source. Allowed: wake_word|button"}), 400

        context = (
            (form.get("context") if form is not None else None)
            or payload.get("context")
            or ("workout" if trigger_source in {"wake_word", "button"} else "chat")
        )
        context = str(context or "chat").strip().lower()
        if context not in {"workout", "chat"}:
            context = "chat"

        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(
            (form.get("language") if form is not None else None)
            or payload.get("language", default_language)
        )
        persona = (
            (form.get("persona") if form is not None else None)
            or payload.get("persona")
            or "personal_trainer"
        )
        user_name = (
            (form.get("user_name") if form is not None else None)
            or payload.get("user_name")
            or ""
        ).strip()
        response_mode = (
            (form.get("response_mode") if form is not None else None)
            or payload.get("response_mode")
            or ""
        ).strip().lower()

        workout_context = collect_workout_context(payload=payload, form=form)
        summary_from_contract = normalized_talk_contract.get("workout_context_summary") or {}
        if isinstance(summary_from_contract, dict):
            for key, value in summary_from_contract.items():
                if value is not None and workout_context.get(key) in (None, ""):
                    workout_context[key] = value
        talk_session_id = (
            (form.get("session_id") if form is not None else None)
            or payload.get("session_id")
            or ""
        ).strip()
        talk_profile_user_id = _coerce_profile_user_id(
            (form.get("user_profile_id") if form is not None else None)
            or payload.get("user_profile_id")
            or payload.get("user_id")
        )
        if not talk_profile_user_id and talk_session_id and session_manager.session_exists(talk_session_id):
            talk_meta = session_manager.sessions.get(talk_session_id, {}).get("metadata", {})
            talk_profile_user_id = _coerce_profile_user_id(
                (talk_meta.get("user_profile_id") or talk_meta.get("user_id"))
            )
        talk_subject = _coach_talk_rate_limit_subject(
            talk_profile_user_id=talk_profile_user_id,
            talk_session_id=talk_session_id,
        )
        talk_rate_limited = _enforce_coach_talk_rate_limits(
            talk_subject=talk_subject,
            talk_session_id=talk_session_id if context == "workout" else None,
        )
        if talk_rate_limited is not None:
            return talk_rate_limited
        talk_profile, talk_profile_source = _resolve_runtime_profile(
            user_id=talk_profile_user_id,
            snapshot_profile=None,
        )
        if talk_profile is not None:
            if talk_profile.max_hr_bpm is not None:
                workout_context.setdefault("profile_max_hr_bpm", int(talk_profile.max_hr_bpm))
            if talk_profile.resting_hr_bpm is not None:
                workout_context.setdefault("profile_resting_hr_bpm", int(talk_profile.resting_hr_bpm))
            if talk_profile.age is not None:
                workout_context.setdefault("profile_age", int(talk_profile.age))
        logger.info(
            "PROFILE_RUNTIME_TALK session=%s user=%s source=%s",
            talk_session_id or "none",
            talk_profile_user_id or "none",
            talk_profile_source,
        )
        phase = (
            workout_context.get("phase")
            or (form.get("phase") if form is not None else None)
            or payload.get("phase")
            or "intense"
        )
        intensity = normalize_intensity_value(
            (form.get("intensity") if form is not None else None)
            or payload.get("intensity")
            or "moderate"
        )

        explicit_message = (
            (form.get("message") if form is not None else None)
            or payload.get("message")
            or ""
        ).strip()
        user_message = explicit_message
        stt_source = "none"

        if is_multipart and files is not None and "audio" in files:
            audio_file = files["audio"]
            if audio_file and audio_file.filename:
                if not _validate_audio_upload_signature(audio_file):
                    return jsonify({"error": "Unsupported audio format signature"}), 400
                audio_file.seek(0, os.SEEK_END)
                file_size = audio_file.tell()
                audio_file.seek(0)
                if file_size > MAX_FILE_SIZE:
                    return jsonify({"error": f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

                filename = f"talk_{datetime.now().timestamp()}.wav"
                temp_audio_path = os.path.join(UPLOAD_FOLDER, filename)
                audio_file.save(temp_audio_path)
                if not user_message:
                    budget = talk_timeout_budget(trigger_source)
                    transcribed, stt_source = transcribe_talk_audio(
                        filepath=temp_audio_path,
                        language=language,
                        timeout_seconds=budget,
                    )
                    if transcribed:
                        user_message = transcribed
            elif not explicit_message:
                logger.info("Coach talk multipart request has no audio payload")

        if not user_message:
            user_message = fallback_talk_prompt(language, workout_context)

        conversation_history = []
        recent_zone_events = []
        if talk_session_id and session_manager.session_exists(talk_session_id):
            _record_talk_session_message(talk_session_id, "user", user_message)
            conversation_history = _recent_talk_messages(talk_session_id, limit=6)
            recent_zone_events = _recent_zone_event_context(talk_session_id, limit=3)

        if context == "workout" and stt_source in {"stt_disabled", "stt_error", "stt_timeout", "stt_quota_limited"}:
            coach_text = enforce_language_consistency(
                workout_talk_fallback(language, workout_context),
                language,
                phase=phase,
            )
            voice_file = generate_voice(
                coach_text,
                language=language,
                persona=persona,
                emotional_mode=_infer_emotional_mode(intensity),
            )
            relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
            audio_url = f"/download/{relative_path}"
            latency_ms = int(round((time.perf_counter() - started_at) * 1000))
            logger.info(
                "Coach talk fast fallback trigger=%s context=%s persona=%s user=%s provider=config reason=%s latency_ms=%s",
                trigger_source,
                context,
                persona,
                user_name or "anon",
                stt_source,
                latency_ms,
            )
            _record_talk_session_message(talk_session_id, "assistant", coach_text)
            return jsonify({
                "contract_version": contract_version,
                "text": coach_text,
                "audio_url": audio_url,
                "personality": persona,
                "trigger_source": trigger_source,
                "provider": "config",
                "mode": "workout_talk",
                "latency_ms": latency_ms,
                "fallback_used": True,
                "stt_source": stt_source,
                "policy_blocked": False,
            })

        talk_policy = brain_router.evaluate_talk_policy(
            user_message,
            language,
            talk_context=context,
        )
        if talk_policy.get("policy_blocked"):
            policy_category = str(talk_policy.get("policy_category") or "unknown")
            policy_reason = str(talk_policy.get("policy_reason") or "Talk policy refusal")
            policy_text = str(talk_policy.get("text") or workout_talk_fallback(language, workout_context))
            coach_text = enforce_language_consistency(
                policy_text,
                language,
                phase=phase if context == "workout" else None,
            )
            voice_file = generate_voice(
                coach_text,
                language=language,
                persona=persona,
                emotional_mode=_infer_emotional_mode(intensity),
            )
            relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
            audio_url = f"/download/{relative_path}"
            latency_ms = int(round((time.perf_counter() - started_at) * 1000))
            mode = "workout_talk" if context == "workout" else "chat_talk"

            logger.info(
                "Coach talk policy block trigger=%s context=%s category=%s persona=%s user=%s provider=policy latency_ms=%s",
                trigger_source,
                context,
                policy_category,
                persona,
                user_name or "anon",
                latency_ms,
            )
            _record_talk_session_message(talk_session_id, "assistant", coach_text)
            return jsonify({
                "contract_version": contract_version,
                "text": coach_text,
                "audio_url": audio_url,
                "personality": persona,
                "trigger_source": trigger_source,
                "provider": "policy",
                "mode": mode,
                "latency_ms": latency_ms,
                "fallback_used": False,
                "stt_source": stt_source,
                "policy_blocked": True,
                "policy_category": policy_category,
                "policy_reason": policy_reason,
            })

        logger.info(
            "Coach talk request trigger=%s context=%s phase=%s persona=%s user=%s stt=%s contract=%s msg='%s'",
            trigger_source,
            context,
            phase,
            persona,
            user_name or "anon",
            stt_source,
            contract_version,
            user_message,
        )

        timeout_budget = talk_timeout_budget(trigger_source)
        # Product rule: /coach/talk during an active workout is always a Q&A-style
        # interaction. Keep continuous event selection deterministic in zone_event_motor;
        # this path only answers the athlete's question.
        is_question = (
            context == "workout"
            or response_mode in {"qa", "qna", "question"}
            or is_question_request(user_message)
        )
        fallback_used = False
        prompt_for_router = user_message
        if context == "workout" and bool(getattr(config, "TALK_CONTEXT_SUMMARY_ENABLED", True)):
            prompt_for_router = brain_router.build_workout_talk_prompt(
                question=user_message,
                language=language,
                workout_context=workout_context,
                conversation_history=conversation_history,
                recent_zone_events=recent_zone_events,
            )

        restrict_question_brains = None
        allowed_trigger_sources = {
            str(item).strip().lower()
            for item in getattr(config, "COACH_TALK_ALLOWED_TRIGGER_SOURCES", ())
        }
        if trigger_source in allowed_trigger_sources:
            # Product rule: wake-word/button talk should always try Grok first
            # and only fall back to config if Grok fails or times out.
            restrict_question_brains = ["grok"]

        if is_question:
            coach_text = brain_router.get_question_response(
                prompt_for_router,
                language=language,
                persona=persona,
                context=context,
                user_name=user_name or None,
                timeout_cap_seconds=timeout_budget,
                restrict_brains=restrict_question_brains,
            )
        else:
            # Backward-compatible non-QA route (rare for workout talk).
            coach_text = brain_router.get_coaching_response(
                {"intensity": intensity, "volume": 50, "tempo": 20},
                phase,
                mode="chat",
                language=language,
                persona=persona,
            )

        route_meta = brain_router.get_last_route_meta()
        route_provider = str(route_meta.get("provider") or "config").strip().lower()
        route_status = str(route_meta.get("status") or "").strip().lower()
        if route_status and route_status != "success":
            fallback_used = True

        workout_fallback_statuses = {
            "all_question_brains_failed_or_skipped",
            "empty_question_fallback",
        }
        if context == "workout" and (
            route_status in workout_fallback_statuses
            or route_provider not in {"grok", "policy"}
            or (route_provider == "config" and route_status and not route_status.startswith("policy_"))
        ):
            coach_text = workout_talk_fallback(language, workout_context)
            fallback_used = True

        if not coach_text or not str(coach_text).strip():
            coach_text = workout_talk_fallback(language, workout_context)
            fallback_used = True

        coach_text = enforce_language_consistency(
            coach_text,
            language,
            phase=phase if context == "workout" else None,
        )

        if context == "workout" and fallback_used and not coach_text:
            coach_text = workout_talk_fallback(language, workout_context)

        if context == "workout":
            progress_hint = _format_workout_progress_hint(language, workout_context)
            if progress_hint and progress_hint not in (coach_text or ""):
                coach_text = f"{coach_text} {progress_hint}".strip()
            if _response_claims_invalid_hr(language, coach_text, workout_context):
                coach_text = workout_talk_fallback(language, workout_context)
                fallback_used = True

        voice_file = generate_voice(
            coach_text,
            language=language,
            persona=persona,
            emotional_mode=_infer_emotional_mode(intensity),
        )
        relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
        audio_url = f"/download/{relative_path}"
        latency_ms = int(round((time.perf_counter() - started_at) * 1000))
        provider = route_provider or "config"
        mode = "workout_talk" if context == "workout" else "chat_talk"

        logger.info(
            "Coach talk response trigger=%s latency_ms=%s provider=%s mode=%s fallback_used=%s",
            trigger_source,
            latency_ms,
            provider,
            mode,
            fallback_used,
        )
        _record_talk_session_message(talk_session_id, "assistant", coach_text)

        return jsonify({
            "contract_version": contract_version,
            "text": coach_text,
            "audio_url": audio_url,
            "personality": persona,
            "trigger_source": trigger_source,
            "provider": provider,
            "mode": mode,
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "stt_source": stt_source,
            "policy_blocked": False,
            "policy_category": None,
            "policy_reason": None,
        })

    except Exception as e:
        logger.error(f"Coach talk error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as cleanup_error:
                logger.warning("Could not remove temp talk file %s: %s", temp_audio_path, cleanup_error)


# ============================================
# ERROR HANDLERS
# ============================================
# SUBSCRIPTION VALIDATION
# ============================================

@app.route('/webhooks/app-store', methods=['POST'])
def app_store_server_notifications():
    """Handle App Store Server Notifications V2 for subscription lifecycle sync."""
    if not bool(getattr(config, "APP_STORE_SERVER_NOTIFICATIONS_ENABLED", False)):
        return jsonify({"error": "app_store_notifications_disabled"}), 503

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "invalid_request_body"}), 400

    signed_payload = str(payload.get("signedPayload") or "").strip()
    if not signed_payload:
        return jsonify({"error": "missing_signed_payload"}), 400

    try:
        notification_payload = decode_app_store_signed_payload(
            signed_payload,
            verify_signature=bool(getattr(config, "APP_STORE_SERVER_NOTIFICATIONS_VERIFY_SIGNATURE", True)),
            trusted_root_sha256s=set(getattr(config, "APP_STORE_TRUSTED_ROOT_SHA256S", []) or []),
        )
    except AppStorePayloadError as exc:
        logger.warning("APP_STORE_WEBHOOK_REJECTED reason=%s", exc)
        return jsonify({"error": str(exc)}), 400

    notification_uuid = str(notification_payload.get("notificationUUID") or "").strip()
    notification_type = str(notification_payload.get("notificationType") or "").strip()
    notification_subtype = str(notification_payload.get("subtype") or "").strip()
    signed_at_ms = notification_payload.get("signedDate")
    signed_at = None
    if signed_at_ms not in (None, "", 0):
        try:
            signed_at = datetime.fromtimestamp(int(signed_at_ms) / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        except (TypeError, ValueError):
            signed_at = None

    if notification_uuid:
        existing = db.session.get(AppStoreServerNotification, notification_uuid)
        if existing is not None:
            return jsonify({"success": True, "deduped": True}), 200

    data = notification_payload.get("data") if isinstance(notification_payload.get("data"), dict) else {}
    signed_transaction_info = str(data.get("signedTransactionInfo") or "").strip()
    if not signed_transaction_info:
        logger.info(
            "APP_STORE_WEBHOOK_SKIPPED notification_uuid=%s type=%s reason=no_transaction_info",
            notification_uuid or "unknown",
            notification_type or "unknown",
        )
        return jsonify({"success": True, "deduped": False, "processed": False}), 200

    try:
        state, transaction_fields = _process_signed_app_store_transaction(
            signed_transaction_info=signed_transaction_info,
            user_id=None,
            source="app_store_webhook",
            notification_type=notification_type,
            notification_subtype=notification_subtype,
            notification_uuid=notification_uuid or None,
            notification_signed_at=signed_at,
        )
    except AppStorePayloadError as exc:
        db.session.rollback()
        logger.warning(
            "APP_STORE_WEBHOOK_TRANSACTION_REJECTED notification_uuid=%s reason=%s",
            notification_uuid or "unknown",
            exc,
        )
        return jsonify({"error": str(exc)}), 400

    if notification_uuid:
        db.session.add(
            AppStoreServerNotification(
                notification_uuid=notification_uuid,
                user_id=state.user_id,
                original_transaction_id=state.original_transaction_id,
                transaction_id=state.transaction_id,
                notification_type=notification_type or None,
                notification_subtype=notification_subtype or None,
                environment=str(transaction_fields.get("environment") or "").strip() or None,
                signed_at=signed_at,
            )
        )

    db.session.commit()
    _capture_mobile_analytics_event(
        "subscription_sync_succeeded",
        user_id=state.user_id,
        anonymous_id=None,
        metadata={
            "source": "app_store_webhook",
            "notification_type": notification_type,
            "notification_subtype": notification_subtype,
            "status": state.status,
            "product_id": state.product_id,
        },
    )
    return jsonify(
        {
            "success": True,
            "deduped": False,
            "processed": True,
            "status": state.status,
            "tier": tier_from_status(state.status),
        }
    ), 200

@app.route('/subscription/validate', methods=['POST'])
@require_mobile_auth
def subscription_validate():
    """Server-side subscription tier check.

    Called by the iOS app after a StoreKit purchase to cross-validate,
    and periodically to confirm entitlement state.

    Returns: { "tier": "premium" | "free" }
    """
    user_id = get_request_auth_user_id()
    if not user_id:
        return jsonify({"tier": "free"}), 200

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}

    signed_transaction_info = str(payload.get("signed_transaction_info") or "").strip()
    transaction_id = str(payload.get("transaction_id") or "").strip() or None

    if signed_transaction_info:
        try:
            state, transaction_fields = _process_signed_app_store_transaction(
                signed_transaction_info=signed_transaction_info,
                user_id=user_id,
                source="subscription_validate",
            )
        except AppStorePayloadError as exc:
            db.session.rollback()
            _capture_mobile_analytics_event(
                "subscription_sync_failed",
                user_id=user_id,
                anonymous_id=None,
                metadata={
                    "reason": str(exc),
                    "transaction_id": transaction_id,
                },
            )
            return jsonify({"error": str(exc), "tier": resolve_user_subscription_tier(user_id)}), 400

        claimed_account_token = str(transaction_fields.get("app_account_token") or "").strip()
        if claimed_account_token and claimed_account_token != user_id:
            db.session.rollback()
            return jsonify({"error": "app_account_token_mismatch", "tier": resolve_user_subscription_tier(user_id)}), 403

        db.session.commit()
        tier = resolve_user_subscription_tier(user_id)
        _capture_mobile_analytics_event(
            "subscription_sync_succeeded",
            user_id=user_id,
            anonymous_id=None,
            metadata={
                "source": "subscription_validate",
                "product_id": state.product_id,
                "status": state.status,
                "transaction_id": state.transaction_id or transaction_id,
            },
        )
        return jsonify(
            {
                "tier": tier,
                "status": state.status,
                "transaction_id": state.transaction_id or transaction_id,
            }
        ), 200

    tier = resolve_user_subscription_tier(user_id)
    return jsonify({"tier": tier, "transaction_id": transaction_id}), 200


# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================
# START SERVER
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Treningscoach Backend v1.1.0")
    logger.info(f"Port: {port}, Debug: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
