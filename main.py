# main.py - MAIN FILE FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
import wave
import math
import random
import logging
import time
from datetime import datetime
import config  # Import central configuration
from brain_router import BrainRouter  # Import Brain Router
from session_manager import SessionManager  # Import Session Manager
from persona_manager import PersonaManager  # Import Persona Manager
from coaching_intelligence import should_coach_speak, calculate_next_interval, apply_max_silence_override  # Import coaching intelligence
from user_memory import UserMemory  # STEP 5: Import user memory
from voice_intelligence import VoiceIntelligence  # STEP 6: Import voice intelligence
from elevenlabs_tts import ElevenLabsTTS, synthesize_speech_mock  # Import ElevenLabs TTS + fallback mock
from strategic_brain import get_strategic_brain  # Import Strategic Brain for high-level coaching
from database import init_db, db, WaitlistSignup  # Import database initialization + models
from breath_analyzer import BreathAnalyzer  # Import advanced breath analysis
from auth_routes import auth_bp  # Import auth blueprint
from norwegian_phrase_quality import rewrite_norwegian_phrase
from coaching_engine import validate_coaching_text, get_template_message
from breathing_timeline import BreathingTimeline
from running_personalization import RunningPersonalizationStore
from zone_event_motor import (
    evaluate_zone_tick,
    is_zone_mode,
    normalize_coaching_style,
    normalize_interval_template,
)
from coaching_pipeline import run as run_coaching_pipeline
from web_routes import create_web_blueprint
from chat_routes import create_chat_blueprint
from locale_config import get_voice_id as locale_voice_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for iOS app

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
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'output')  # Match tts_service.py
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Brain Router and Managers
brain_router = BrainRouter()
session_manager = SessionManager()
user_memory = UserMemory()  # STEP 5: Initialize user memory
voice_intelligence = VoiceIntelligence()  # STEP 6: Initialize voice intelligence
breath_analyzer = BreathAnalyzer(
    sample_rate=getattr(config, "BREATH_ANALYSIS_SAMPLE_RATE", 44100)
)  # Advanced breath analysis with DSP + spectral features
running_personalization = RunningPersonalizationStore(
    storage_path=getattr(config, "ZONE_PERSONALIZATION_STORAGE_PATH", "zone_personalization.json"),
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

# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    samples = []
    if isinstance(breath_quality_samples, (list, tuple)):
        for value in breath_quality_samples:
            parsed = _coerce_float(value)
            if parsed is not None:
                samples.append(max(0.0, min(1.0, parsed)))
    signal_quality = _coerce_float((breath_data or {}).get("signal_quality"))
    if signal_quality is not None:
        samples.append(max(0.0, min(1.0, signal_quality)))
    return samples


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
    quality_samples = _derive_breath_quality_samples(breath_data, breath_quality_samples)
    breath_sample_count = len(quality_samples)
    breath_median_quality = _median(quality_samples)

    breath_available_reliable = (
        breath_in_play
        and breath_sample_count >= int(getattr(config, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
        and breath_median_quality is not None
        and breath_median_quality >= float(getattr(config, "CS_BREATH_MIN_RELIABLE_QUALITY", 0.35))
    )
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
            return seed, {
                "provider": "system",
                "source": "zone_event_motor",
                "status": "rewrite_word_limit_fallback",
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
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "language": normalize_language_code(language or "en"),
        "persona": persona or "personal_trainer",
        "filename": os.path.basename(file_path or ""),
    }


def _record_tts_error(stage: str, language: str, persona: str, error_type: str, status_code, message: str):
    TTS_RUNTIME_DIAGNOSTICS["last_error"] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
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
    samples = _derive_breath_quality_samples(breath_data, recent_samples)
    median_quality = _median(samples)
    sample_count = len(samples)
    reliable_min_samples = int(getattr(config, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
    reliable_min_quality = float(getattr(config, "CS_BREATH_MIN_RELIABLE_QUALITY", 0.35))
    degraded_floor = max(0.05, min(0.30, reliable_min_quality - 0.15))

    if (
        sample_count >= reliable_min_samples
        and median_quality is not None
        and median_quality >= reliable_min_quality
    ):
        return "reliable"

    current_quality = _coerce_float((breath_data or {}).get("signal_quality"))
    if (median_quality is not None and median_quality >= degraded_floor) or (
        current_quality is not None and current_quality >= degraded_floor
    ):
        return "degraded"
    return "unavailable"


def _phase_fallback_interval_seconds(phase: str) -> float:
    normalized_phase = (phase or "").strip().lower()
    if normalized_phase == "warmup":
        return float(getattr(config, "SPEECH_PHASE_FALLBACK_WARMUP_SECONDS", 30.0))
    if normalized_phase == "cooldown":
        return float(getattr(config, "SPEECH_PHASE_FALLBACK_COOLDOWN_SECONDS", 40.0))
    return float(getattr(config, "SPEECH_PHASE_FALLBACK_INTENSE_SECONDS", 35.0))


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
                print(f"[TTS] OK lang={normalized_language} persona={selected_persona} mode={selected_mode} file={os.path.basename(result)}")
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
                    print(f"[TTS] RETRY_OK lang={normalized_language} persona=base mode={selected_mode} file={os.path.basename(result)}")
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
                            print(f"[TTS] RETRY_OK lang=en persona=base mode={selected_mode} file={os.path.basename(result)}")
                            return result
                        except Exception as english_error:
                            logger.warning("English base voice TTS retry failed: %s", english_error)

                    raise base_error
        else:
            # Fallback to mock (Qwen disabled)
            print(f"[TTS] MOCK (ElevenLabs disabled) lang={normalized_language}")
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
        print(f"[TTS] FAILED lang={language} persona={persona} type={type(e).__name__} status={status_code} error={e}")
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
    """
    Get welcome message for workout start (Gym Companion style).

    Query params:
        experience: "beginner", "intermediate", "advanced" (default: "standard")

    Returns:
        JSON with welcome message text and audio URL
    """
    try:
        experience = request.args.get('experience', 'standard')
        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(request.args.get('language', default_language))
        persona = request.args.get('persona', 'personal_trainer')
        user_name = request.args.get('user_name', '').strip()

        # Keep welcome personality consistent across experience levels
        # (experience is retained for API compatibility and analytics/logging)
        message_category = 'standard'

        # Get random welcome message from config (language-aware)
        if language == "no":
            welcome_bank = getattr(config, 'WELCOME_MESSAGES_NO', config.WELCOME_MESSAGES)
        else:
            welcome_bank = config.WELCOME_MESSAGES
        messages = welcome_bank.get(message_category, welcome_bank.get('standard', ["Welcome."]))
        welcome_text = random.choice(messages)

        # Personalize welcome with user name (first message of session uses name)
        if user_name:
            if language == "no":
                welcome_text = f"Hei {user_name}! {welcome_text}"
            else:
                welcome_text = f"Hey {user_name}! {welcome_text}"
        welcome_text = enforce_language_consistency(welcome_text, language, phase="warmup")

        logger.info(f"Welcome message requested: experience={experience}, language={language}, user={user_name or 'anon'}, message='{welcome_text}'")

        # Generate or use cached audio (language + persona-aware voice)
        voice_file = generate_voice(welcome_text, language=language, persona=persona, emotional_mode="supportive")

        # Return relative path for download
        relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
        audio_url = f"/download/{relative_path}"

        return jsonify({
            "text": welcome_text,
            "audio_url": audio_url,
            "category": message_category
        })

    except Exception as e:
        logger.error(f"Welcome endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
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

        # Analyze breathing
        breath_data = breath_analyzer.analyze(filepath)

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

@app.route('/coach', methods=['POST'])
def coach():
    """
    Main endpoint: Receives audio, analyzes, returns coach voice

    App sends:
    - audio: Audio file
    - phase: "warmup", "intense", or "cooldown"
    - mode: "chat" or "realtime_coach" (optional, default: "chat")

    Backend returns:
    - Coach voice as MP3

    STEP 3: Supports switching between chat brain and realtime_coach brain
    """
    try:
        if 'audio' not in request.files:
            logger.warning("Coach request missing audio file")
            return jsonify({"error": "No audio file received"}), 400

        audio_file = request.files['audio']
        phase = request.form.get('phase', 'intense')
        mode = request.form.get('mode', 'chat')  # STEP 3: Default to chat for legacy endpoint
        persona = request.form.get('persona', 'personal_trainer')
        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(request.form.get('language', default_language))

        if audio_file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        # Validate phase
        valid_phases = ['warmup', 'intense', 'cooldown']
        if phase not in valid_phases:
            return jsonify({"error": f"Invalid phase. Must be one of: {', '.join(valid_phases)}"}), 400

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

        logger.info(f"Coach request: {filename} ({file_size} bytes), phase={phase}, mode={mode}")

        # Analyze breathing
        breath_data = breath_analyzer.analyze(filepath)

        # Get coach response (text) - STEP 3: Pass mode to brain router
        coach_text = get_coach_response(breath_data, phase, mode=mode)

        # Generate voice with persona-specific settings
        voice_file = generate_voice(
            coach_text,
            language=language,
            persona=persona,
            emotional_mode=_infer_emotional_mode(breath_data.get("intensity", "moderate")),
        )

        # Delete temporary input file
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        # Send back voice file + metadata
        # Convert absolute path to relative path from OUTPUT_FOLDER
        relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
        response_data = {
            "text": coach_text,
            "breath_analysis": breath_data,
            "audio_url": f"/download/{relative_path}",
            "phase": phase
        }

        logger.info(f"Coach response: '{coach_text}' (intensity: {breath_data['intensity']})")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in coach endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/coach/continuous', methods=['POST'])
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
        session_id = request.form.get('session_id')
        phase = request.form.get('phase', 'intense')
        last_coaching = request.form.get('last_coaching', '')
        elapsed_seconds = int(request.form.get('elapsed_seconds', 0))
        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(request.form.get('language', default_language))
        training_level = request.form.get('training_level', 'intermediate')
        persona = request.form.get('persona', 'personal_trainer')
        workout_mode = request.form.get('workout_mode', config.DEFAULT_WORKOUT_MODE)
        coaching_style = normalize_coaching_style(
            request.form.get('coaching_style', getattr(config, "DEFAULT_COACHING_STYLE", "normal")),
            config,
        )
        interval_template = normalize_interval_template(
            request.form.get('interval_template', getattr(config, "DEFAULT_INTERVAL_TEMPLATE", "4x4")),
            config,
        )
        user_name = request.form.get('user_name', '').strip()
        user_profile_id = request.form.get('user_profile_id', '').strip()
        heart_rate_raw = request.form.get("heart_rate")
        hr_quality_raw = request.form.get("hr_quality")
        watch_connected_raw = request.form.get("watch_connected")
        breath_analysis_enabled_raw = request.form.get("breath_analysis_enabled", "true")
        mic_permission_granted_raw = request.form.get("mic_permission_granted", "true")
        breath_enabled_by_user = _coerce_bool(breath_analysis_enabled_raw)
        mic_permission_granted = _coerce_bool(mic_permission_granted_raw)

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400

        if audio_file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

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
        audio_file.save(filepath)

        logger.info(
            "Continuous coaching tick: session=%s phase=%s mode=%s elapsed=%ss lang=%s level=%s persona=%s style=%s template=%s user=%s",
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
            })

        # Analyze breath
        analyze_started = time.perf_counter()
        breath_data = breath_analyzer.analyze(filepath)
        analyze_ms = (time.perf_counter() - analyze_started) * 1000.0

        # Get coaching context and workout state
        coaching_context = session_manager.get_coaching_context_with_emotion(session_id)
        last_breath = session_manager.get_last_breath_analysis(session_id)
        workout_state = session_manager.get_workout_state(session_id)
        if workout_state is not None:
            workout_state["workout_mode"] = workout_mode
            workout_state["coaching_style"] = coaching_style
            workout_state["interval_template"] = interval_template
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

        zone_mode_active = is_zone_mode(workout_mode, config)
        zone_tick = None
        zone_forced_text = None
        zone_mode_speaks = False
        if zone_mode_active and workout_state is not None:
            zone_tick = evaluate_zone_tick(
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
                hr_max=request.form.get("hr_max"),
                resting_hr=request.form.get("resting_hr"),
                age=request.form.get("age"),
                config_module=config,
                breath_intensity=breath_data.get("intensity"),
                breath_signal_quality=breath_data.get("signal_quality"),
                session_id=session_id,
                paused=request.form.get("paused"),
            )
            zone_mode_speaks = bool(zone_tick.get("should_speak"))
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

        # Check if this is the very first breath (welcome message)
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
        speech_decision_owner_v2 = bool(getattr(config, "SPEECH_DECISION_OWNER_V2", True))
        recent_breath_quality_samples = [
            item.get("signal_quality")
            for item in (coaching_context.get("breath_history", [])[-12:] if isinstance(coaching_context, dict) else [])
            if isinstance(item, dict) and item.get("signal_quality") is not None
        ]
        breath_quality_state = _resolve_breath_quality_state(
            breath_data=breath_data,
            recent_samples=recent_breath_quality_samples,
        )
        unified_event_router_enabled = bool(getattr(config, "UNIFIED_EVENT_ROUTER_ENABLED", True))
        unified_event_router_shadow = bool(getattr(config, "UNIFIED_EVENT_ROUTER_SHADOW", False))
        unified_zone_router_active = (
            unified_event_router_enabled
            and zone_mode_active
            and zone_tick is not None
            and workout_mode in {"easy_run", "interval"}
        )
        if unified_event_router_shadow and zone_mode_active and zone_tick is not None:
            logger.info(
                "UNIFIED_EVENT_SHADOW session=%s mode=%s events=%s legacy_reason=%s legacy_should_speak=%s",
                session_id,
                workout_mode,
                [item.get("event_type") for item in (zone_tick.get("events") or []) if isinstance(item, dict)],
                zone_tick.get("reason"),
                zone_tick.get("should_speak"),
            )
        decision = run_coaching_pipeline(
            is_first_breath=bool(is_first_breath),
            zone_mode_active=bool(zone_mode_active),
            zone_tick=zone_tick,
            breath_quality_state=breath_quality_state,
            speech_decision_owner_v2=bool(speech_decision_owner_v2),
            unified_zone_router_active=bool(unified_zone_router_active),
            voice_intelligence=voice_intelligence,
            should_coach_speak_fn=should_coach_speak,
            apply_max_silence_override_fn=apply_max_silence_override,
            phase_fallback_interval_seconds_fn=_phase_fallback_interval_seconds,
            breath_data=breath_data,
            phase=phase,
            last_coaching=last_coaching,
            elapsed_seconds=elapsed_seconds,
            last_breath=last_breath,
            coaching_history=coaching_context["coaching_history"],
            training_level=training_level,
            session_id=session_id,
            elapsed_since_last=elapsed_since_last,
            max_silence_seconds=float(getattr(config, "MAX_SILENCE_SECONDS", 60)),
        )
        speak_decision = bool(decision.speak)
        reason = decision.reason
        decision_owner = decision.owner
        decision_owner_base = decision.owner_base
        zone_forced_text = decision.zone_forced_text
        max_silence_override_used = bool(decision.max_silence_override_used)

        if decision.mark_first_breath_consumed:
            workout_state["is_first_breath"] = False
        if decision.mark_use_welcome_phrase:
            workout_state["use_welcome_phrase"] = True
            logger.info("First breath detected - will provide welcome message")

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

        # Latency strategy (legacy path only): if previous tick used fast fallback,
        # force one richer follow-up cue.
        if (not speech_decision_owner_v2) and (not is_first_breath) and latency_state.get("pending_rich_followup") and not zone_mode_active:
            rich_followup_forced = True
            if not speak_decision:
                speak_decision = True
                reason = "latency_rich_followup"
                logger.info(
                    "Latency strategy: forcing rich follow-up cue (provider=%s)",
                    latency_state.get("last_latency_provider"),
                )
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
        use_welcome = workout_state.get("use_welcome_phrase", False)
        recent_cues = _extract_recent_spoken_cues(
            coaching_context.get("coaching_history", []),
            limit=getattr(config, "BRAIN_RECENT_CUE_WINDOW", 4),
        )
        timeline_cue = None
        timeline_shadow = bool(getattr(config, "BREATHING_TIMELINE_SHADOW_MODE", True))
        timeline_enforce = bool(getattr(config, "BREATHING_TIMELINE_ENFORCE", False))
        if timeline_shadow or timeline_enforce:
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
            # Low-latency path: skip AI generation when coach will stay silent.
            coach_text = _get_silent_debug_text(reason, language)
            brain_meta = {
                "provider": "system",
                "source": "silent_policy",
                "status": "skipped_generation",
                "mode": "realtime_coach",
            }
        elif use_welcome:
            # Use a specific cached phrase for instant welcome
            coach_text = "Perfect."  # This phrase is cached (from pregenerate list)
            workout_state["use_welcome_phrase"] = False  # Clear flag
            brain_meta = {
                "provider": "system",
                "source": "welcome_cache",
                "status": "cached_phrase",
                "mode": "realtime_coach",
            }
            logger.info(f"Using cached welcome phrase: {coach_text}")
        elif speech_decision_owner_v2 and decision_owner_base == "phase_fallback":
            coach_text = _phase_fallback_text(
                language=language,
                phase=phase,
                elapsed_seconds=elapsed_seconds,
            )
            brain_meta = {
                "provider": "system",
                "source": "phase_fallback",
                "status": "deterministic_template",
                "mode": "realtime_coach",
            }
        elif speech_decision_owner_v2 and decision_owner_base == "zone_event":
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
                # Keep v2 single-owner deterministic even if zone motor text is missing.
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
                    "Zone decision owner selected but no zone text supplied; using deterministic fallback (session=%s reason=%s event=%s)",
                    session_id,
                    reason,
                    zone_event_type,
                )
        elif zone_mode_active and zone_forced_text:
            zone_event_type = (
                (zone_tick or {}).get("primary_event_type")
                or (zone_tick or {}).get("event_type")
                or reason
            )
            coach_text, brain_meta = _maybe_rephrase_zone_event_text(
                base_text=zone_forced_text,
                language=language,
                persona=persona,
                coaching_style=coaching_style,
                event_type=zone_event_type,
            )
        else:
            # Only run expensive brain paths when we already decided to speak.
            use_fast_fallback = False
            if not rich_followup_forced:
                latency_signal = brain_router.get_latency_fallback_signal(mode="realtime_coach")
                if latency_signal.get("should_fallback") and _latency_fast_fallback_allowed(latency_state, elapsed_seconds):
                    use_fast_fallback = True

            if use_fast_fallback:
                coach_text = brain_router.get_fast_fallback_response(
                    breath_data=breath_data,
                    phase=phase,
                    language=language,
                    persona=persona,
                )
                brain_meta = brain_router.get_last_route_meta()
                fast_fallback_used = True
                latency_state["pending_rich_followup"] = True
                latency_state["last_fast_fallback_elapsed"] = float(elapsed_seconds)
                latency_state["last_latency_provider"] = latency_signal.get("provider")
                logger.info(
                    "Latency strategy: fast fallback used (provider=%s avg=%.3fs threshold=%.3fs calls=%s)",
                    latency_signal.get("provider"),
                    float(latency_signal.get("avg_latency", 0.0)),
                    float(latency_signal.get("threshold", 0.0)),
                    latency_signal.get("calls"),
                )
            else:
                last_pattern_time = workout_state.get("last_pattern_time") if workout_state else None
                if brain_router.use_hybrid and brain_router.should_use_pattern_insight(elapsed_seconds, last_pattern_time):
                    pattern_insight = brain_router.detect_pattern(
                        breath_history=coaching_context["breath_history"],
                        coaching_history=coaching_context["coaching_history"],
                        phase=phase
                    )

                    if pattern_insight:
                        logger.info(f"Pattern detected: {pattern_insight}")
                        if workout_state:
                            workout_state["last_pattern_time"] = elapsed_seconds

                if strategic_brain is not None:
                    last_strategic_time = workout_state.get("last_strategic_time", 0) if workout_state else 0

                    if strategic_brain.should_provide_insight(elapsed_seconds, last_strategic_time, phase):
                        strategic_guidance = strategic_brain.get_strategic_insight(
                            breath_history=coaching_context["breath_history"],
                            coaching_history=coaching_context["coaching_history"],
                            phase=phase,
                            elapsed_seconds=elapsed_seconds,
                            session_context=session_manager.sessions.get(session_id, {}).get("metadata", {}),
                            language=language
                        )

                        if strategic_guidance:
                            logger.info(f"🧠 Strategic guidance received: {strategic_guidance}")
                            if workout_state:
                                workout_state["last_strategic_time"] = elapsed_seconds

                generation_breath_data = dict(breath_data)
                generation_breath_data["session_id"] = session_id
                generation_breath_data["persona"] = persona
                generation_breath_data["training_level"] = training_level
                generation_breath_data["persona_mode"] = coaching_context.get("persona_mode")
                generation_breath_data["emotional_intensity"] = coaching_context.get("emotional_intensity")
                generation_breath_data["emotional_trend"] = coaching_context.get("emotional_trend")
                generation_breath_data["safety_override"] = coaching_context.get("safety_override")
                generation_breath_data["time_in_struggle"] = coaching_context.get("time_in_struggle")
                generation_breath_data["coaching_reason"] = reason
                generation_breath_data["recent_coach_cues"] = recent_cues

                if strategic_guidance:
                # Strategic Brain guidance (highest priority for strategic moments)
                # System decides: use suggested phrase or pick from config based on guidance
                    if "suggested_phrase" in strategic_guidance and strategic_guidance["suggested_phrase"]:
                        coach_text = strategic_guidance["suggested_phrase"]
                        brain_meta = {
                            "provider": "strategic",
                            "source": "strategic_brain",
                            "status": "suggested_phrase",
                            "mode": "strategic",
                        }
                        logger.info(f"🧠 Using Strategic Brain phrase: {coach_text}")
                    else:
                        coach_text = get_coach_response_continuous(
                            generation_breath_data,
                            phase,
                            language=language,
                            persona=persona,
                            user_name=user_name,
                        )
                        brain_meta = brain_router.get_last_route_meta()
                        logger.info(f"🧠 Strategic guidance applied, using config phrase: {coach_text}")
                elif pattern_insight:
                    coach_text = pattern_insight  # STEP 4: Use Claude's pattern insight
                    brain_meta = {
                        "provider": "claude",
                        "source": "pattern_insight",
                        "status": "pattern_override",
                        "mode": "strategic",
                    }
                    logger.info(f"Using pattern insight instead of config message")
                else:
                    coach_text = get_coach_response_continuous(
                        generation_breath_data,
                        phase,
                        language=language,
                        persona=persona,
                        user_name=user_name,
                    )
                    brain_meta = brain_router.get_last_route_meta()

                if rich_followup_forced:
                    latency_state["pending_rich_followup"] = False
                    latency_state["last_rich_followup_elapsed"] = float(elapsed_seconds)
                    logger.info(
                        "Latency strategy: rich follow-up completed (provider=%s source=%s)",
                        brain_meta.get("provider"),
                        brain_meta.get("source"),
                    )

        if (not speech_decision_owner_v2) and speak_decision and timeline_cue and timeline_enforce and not use_welcome and not fast_fallback_used:
            zone_priority_active = zone_mode_active and (
                bool(zone_forced_text) or str(brain_meta.get("source", "")).startswith("zone_event_")
            )
            if zone_priority_active:
                _increment_quality_metric("timeline_zone_priority_skips")
                logger.info("Breathing timeline override skipped: deterministic zone cue has priority")
            else:
                coach_text = timeline_cue
                brain_meta = {
                    "provider": "system",
                    "source": "breathing_timeline",
                    "status": "timeline_override",
                    "mode": "realtime_coach",
                }
                _increment_quality_metric("timeline_overrides")

        validation_shadow = bool(getattr(config, "COACHING_VALIDATION_SHADOW_MODE", True))
        validation_enforce = bool(getattr(config, "COACHING_VALIDATION_ENFORCE", False))
        if speak_decision and not use_welcome and (validation_shadow or validation_enforce):
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

        # STEP 6: Add human variation to avoid robotic repetition (skip for welcome)
        if (
            speak_decision
            and not use_welcome
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
            breath_quality_samples=[
                item.get("signal_quality")
                for item in (coaching_context.get("breath_history", [])[-12:] if isinstance(coaching_context, dict) else [])
                if isinstance(item, dict) and item.get("signal_quality") is not None
            ],
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
        }
        if zone_mode_active and zone_tick is not None:
            response_data.update(
                {
                    "zone_status": zone_tick.get("zone_status"),
                    "zone_event": zone_tick.get("event_type"),
                    "zone_primary_event": zone_tick.get("primary_event_type"),
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
        return jsonify({"error": "Internal server error"}), 500


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

def _extract_optional_user_id() -> str:
    """
    Extract user_id from optional Bearer JWT in Authorization header.

    Returns user_id string or None. Logs decode failures at warning level
    instead of silently swallowing them.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    try:
        from auth import decode_jwt
        import jwt as pyjwt
        token = auth_header.split("Bearer ", 1)[1]
        payload = decode_jwt(token)
        return payload.get("user_id")
    except Exception as e:
        # Log a sanitized warning (no token content) so failures are visible
        logger.warning(f"Optional JWT decode failed: {type(e).__name__}")
        return None


@app.route('/workouts', methods=['POST'])
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

        user_id = _extract_optional_user_id()

        workout = WorkoutHistory(
            user_id=user_id or "anonymous",
            duration_seconds=data.get("duration_seconds", 0),
            final_phase=data.get("final_phase"),
            avg_intensity=data.get("avg_intensity"),
            persona_used=data.get("persona_used"),
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
def get_workouts():
    """
    Get workout history for a user.

    Query params:
    - limit: Max number of records (default: 20, max: 100)
    """
    try:
        from database import WorkoutHistory

        user_id = _extract_optional_user_id()

        # Bounds-check limit to prevent abuse
        try:
            limit = max(1, min(100, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            limit = 20

        if user_id:
            workouts = WorkoutHistory.query.filter_by(user_id=user_id)\
                .order_by(WorkoutHistory.date.desc())\
                .limit(limit).all()
        else:
            workouts = WorkoutHistory.query\
                .order_by(WorkoutHistory.date.desc())\
                .limit(limit).all()

        return jsonify({
            "workouts": [w.to_dict() for w in workouts]
        }), 200

    except Exception as e:
        logger.error(f"Get workouts error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================
# TALK TO COACH (Conversational + Voice)
# ============================================

@app.route('/coach/talk', methods=['POST'])
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
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' parameter"}), 400

        user_message = data['message']
        session_id = data.get('session_id')
        context = data.get('context', 'chat')  # "workout" or "chat"
        phase = data.get('phase', 'intense')
        intensity = normalize_intensity_value(data.get('intensity', 'moderate'))
        persona = data.get('persona', 'personal_trainer')
        default_language = getattr(config, "DEFAULT_LANGUAGE", "en")
        language = normalize_language_code(data.get('language', default_language))
        user_name = data.get('user_name', '').strip()
        response_mode = (data.get("response_mode", "") or "").strip().lower()

        logger.info(f"Coach talk: '{user_message}' (context={context}, phase={phase}, persona={persona}, user={user_name or 'anon'})")

        is_question = response_mode in {"qa", "qna", "question"} or is_question_request(user_message)

        # User questions should use fast Grok-first Q&A with max 3 sentences.
        if is_question:
            coach_text = brain_router.get_question_response(
                user_message,
                language=language,
                persona=persona,
                context=context,
                user_name=user_name or None,
            )
        else:
            # Build system prompt based on context
            name_context = f"\n- The athlete's name is {user_name}. Use it at most once in this response, and only if it feels natural." if user_name else ""

            if context == 'workout':
                # Mid-workout: user spoke via wake word — keep response VERY SHORT
                persona_prompt = PersonaManager.get_system_prompt(persona, language=language)
                system_prompt = (
                    f"{persona_prompt}\n\n"
                    f"IMPORTANT: The user is IN THE MIDDLE of a workout right now.\n"
                    f"- Current phase: {phase}\n"
                    f"- Breathing intensity: {intensity}\n"
                    f"- They used the wake word to speak to you.\n"
                    f"- Keep your response to 1 sentence MAX. Be direct and actionable.\n"
                    f"- Don't ask questions — they can't easily respond.\n"
                    f"- If unclear, give a short motivational response."
                    f"{name_context}"
                )
                if language == "no":
                    system_prompt += "\n- RESPOND IN NORWEGIAN."
                max_tokens = 40  # Very short for mid-workout
            else:
                # Casual chat: outside workout, slightly longer allowed
                persona_prompt = PersonaManager.get_system_prompt(persona, language=language)
                system_prompt = (
                    f"{persona_prompt}\n"
                    f"Max 2 sentences. You speak out loud to an athlete. Be concise and direct."
                    f"{name_context}"
                )
                if language == "no":
                    system_prompt += "\n- RESPOND IN NORWEGIAN."
                max_tokens = 60

            # Use strategic brain (Claude Haiku for cost efficiency) if enabled
            coach_text = None
            if strategic_brain is not None and strategic_brain.is_available():
                try:
                    response = strategic_brain.client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_message}]
                    )
                    coach_text = response.content[0].text
                    logger.info(f"Claude Haiku response: '{coach_text}'")
                except Exception as e:
                    logger.error(f"Claude API error: {e}")

            # Fallback to config-based response
            if not coach_text:
                coach_text = brain_router.get_coaching_response(
                    {"intensity": intensity, "volume": 50, "tempo": 20},
                    phase,
                    mode="chat",
                    language=language,
                    persona=persona
                )
        coach_text = enforce_language_consistency(
            coach_text,
            language,
            phase=phase if context == "workout" else None
        )

        # Generate voice audio with persona-specific voice
        voice_file = generate_voice(
            coach_text,
            language=language,
            persona=persona,
            emotional_mode=_infer_emotional_mode(intensity),
        )
        relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
        audio_url = f"/download/{relative_path}"

        return jsonify({
            "text": coach_text,
            "audio_url": audio_url,
            "personality": persona
        })

    except Exception as e:
        logger.error(f"Coach talk error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================
# ERROR HANDLERS
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
