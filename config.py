# config.py - Central configuration for Coachi AI Coach
# Voice/locale config lives in locale_config.py (single source of truth)

import json
import os
from pathlib import Path
from locale_config import SUPPORTED_LOCALES, get_voice_id as locale_get_voice_id


PROJECT_ROOT = Path(__file__).resolve().parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_csv_list(name: str, default: list) -> list:
    raw = os.getenv(name)
    if not raw:
        return default
    values = [item.strip() for item in raw.split(",")]
    values = [item for item in values if item]
    return values or default


def _env_json_dict(name: str, default: dict) -> dict:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        return default
    except json.JSONDecodeError:
        return default


def _env_csv_set(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return list(default)
    values = []
    for item in raw.split(","):
        candidate = item.strip()
        if candidate:
            values.append(candidate)
    return values or list(default)


def _resolve_repo_path(raw_value: str | None, default_relative: str) -> str:
    raw = (raw_value or default_relative).strip() or default_relative
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return str(path.resolve())


def _resolve_child_runtime_path(base_dir: str, raw_value: str | None, default_relative: str) -> str:
    base_path = Path(base_dir)
    default_path = (base_path / default_relative).resolve()
    path = Path(_resolve_repo_path(raw_value, str(default_path)))
    if not path.is_relative_to(base_path):
        path = default_path
    return str(path.resolve())

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "Coachi"
APP_VERSION = "3.0.0"
WEB_UI_VARIANT = (os.getenv("WEB_UI_VARIANT", "codex") or "codex").strip().lower()

# Runtime storage directories
INSTANCE_DIR = _resolve_repo_path(os.getenv("INSTANCE_DIR"), "instance")
UPLOAD_DIR = _resolve_repo_path(os.getenv("UPLOAD_DIR"), "uploads")
OUTPUT_DIR = _resolve_repo_path(os.getenv("OUTPUT_DIR"), "output")
TTS_AUDIO_CACHE_DIR = _resolve_child_runtime_path(OUTPUT_DIR, os.getenv("TTS_AUDIO_CACHE_DIR"), "cache")

# Monetization runtime policy:
# - Keep app fully free while APP_FREE_MODE=true.
# - Billing flags can be prepared now and activated later by flipping APP_FREE_MODE=false.
APP_FREE_MODE = _env_bool("APP_FREE_MODE", True)
BILLING_ENABLED = _env_bool("BILLING_ENABLED", False)
PREMIUM_SURFACES_ENABLED = _env_bool("PREMIUM_SURFACES_ENABLED", False)
if APP_FREE_MODE:
    BILLING_ENABLED = False
    PREMIUM_SURFACES_ENABLED = False

# Launch integrations
POSTHOG_ENABLED = _env_bool("POSTHOG_ENABLED", False)
POSTHOG_API_KEY = (os.getenv("POSTHOG_API_KEY", "") or "").strip()
POSTHOG_HOST = (os.getenv("POSTHOG_HOST", "https://us.i.posthog.com") or "https://us.i.posthog.com").strip()
SENTRY_ENABLED = _env_bool("SENTRY_ENABLED", False)
SENTRY_DSN = (os.getenv("SENTRY_DSN", "") or "").strip()
SENTRY_ENVIRONMENT = (
    os.getenv("SENTRY_ENVIRONMENT")
    or os.getenv("ENVIRONMENT")
    or os.getenv("APP_ENV")
    or os.getenv("FLASK_ENV")
    or "development"
).strip()
SENTRY_RELEASE = (os.getenv("SENTRY_RELEASE", APP_VERSION) or APP_VERSION).strip()
SENTRY_TRACES_SAMPLE_RATE = _env_float("SENTRY_TRACES_SAMPLE_RATE", 0.0)
XAI_VOICE_AGENT_ENABLED = _env_bool("XAI_VOICE_AGENT_ENABLED", True)
XAI_VOICE_AGENT_MODEL = (os.getenv("XAI_VOICE_AGENT_MODEL", "grok-3-mini") or "grok-3-mini").strip()
XAI_VOICE_AGENT_REGION = (os.getenv("XAI_VOICE_AGENT_REGION", "us-east-1") or "us-east-1").strip()
XAI_VOICE_AGENT_VOICE = (os.getenv("XAI_VOICE_AGENT_VOICE", "Rex") or "Rex").strip()
XAI_VOICE_AGENT_MAX_SESSION_SECONDS = _env_int("XAI_VOICE_AGENT_MAX_SESSION_SECONDS", 300)
XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS = _env_int("XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", 120)
XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS = _env_int("XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS", 300)
XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY = _env_int("XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", 2)
XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY = _env_int("XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY", 10)
XAI_VOICE_AGENT_CLIENT_SECRET_URL = (
    os.getenv("XAI_VOICE_AGENT_CLIENT_SECRET_URL", "https://api.x.ai/v1/realtime/client_secrets")
    or "https://api.x.ai/v1/realtime/client_secrets"
).strip()
XAI_VOICE_AGENT_WEBSOCKET_URL = (
    os.getenv("XAI_VOICE_AGENT_WEBSOCKET_URL", "wss://api.x.ai/v1/realtime")
    or "wss://api.x.ai/v1/realtime"
).strip()
XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT = _env_int("XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT", 12)

# Security posture
JWT_ACCESS_TOKEN_MAX_DAYS = _env_int("JWT_ACCESS_TOKEN_MAX_DAYS", 7)
JWT_REFRESH_TOKEN_MAX_DAYS = _env_int("JWT_REFRESH_TOKEN_MAX_DAYS", 7)
JWT_SECRET_MAX_AGE_DAYS = _env_int("JWT_SECRET_MAX_AGE_DAYS", 90)
APPLE_AUTH_ENABLED = _env_bool("APPLE_AUTH_ENABLED", True)
EMAIL_AUTH_ENABLED = _env_bool("EMAIL_AUTH_ENABLED", True)
GOOGLE_AUTH_ENABLED = _env_bool("GOOGLE_AUTH_ENABLED", False)
FACEBOOK_AUTH_ENABLED = _env_bool("FACEBOOK_AUTH_ENABLED", False)
VIPPS_AUTH_ENABLED = _env_bool("VIPPS_AUTH_ENABLED", False)
EMAIL_AUTH_CODE_TTL_MINUTES = _env_int("EMAIL_AUTH_CODE_TTL_MINUTES", 10)

# Enforce auth for mobile API runtime routes (/coach/*, /analyze, chat control).
# Default is guest-friendly for the current pre-launch phase; set env true to re-enable strict auth.
MOBILE_API_AUTH_REQUIRED = _env_bool("MOBILE_API_AUTH_REQUIRED", False)
# Test-only bypass for new mobile auth/rate-limit guards to preserve deterministic tests.
AUTH_BYPASS_FOR_TESTS = _env_bool("AUTH_BYPASS_FOR_TESTS", True)
RATE_LIMIT_BYPASS_FOR_TESTS = _env_bool("RATE_LIMIT_BYPASS_FOR_TESTS", True)
# Test-only bypass for synthetic audio fixtures that do not carry real file signatures.
AUDIO_SIGNATURE_BYPASS_FOR_TESTS = _env_bool("AUDIO_SIGNATURE_BYPASS_FOR_TESTS", True)

# Database-backed API rate limits (fixed windows, shared across workers).
RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
RATE_LIMIT_STORAGE_BACKEND = (os.getenv("RATE_LIMIT_STORAGE_BACKEND", "database") or "database").strip().lower()
RATE_LIMIT_RETENTION_SECONDS = _env_int("RATE_LIMIT_RETENTION_SECONDS", 7 * 24 * 3600)
API_RATE_LIMIT_PER_HOUR = _env_int("API_RATE_LIMIT_PER_HOUR", 100)
AUTH_RATE_LIMIT_PER_HOUR = _env_int("AUTH_RATE_LIMIT_PER_HOUR", 40)
REFRESH_RATE_LIMIT_PER_HOUR = _env_int("REFRESH_RATE_LIMIT_PER_HOUR", 60)
PASSWORD_RESET_RATE_LIMIT_PER_HOUR = _env_int("PASSWORD_RESET_RATE_LIMIT_PER_HOUR", 3)
CONTINUOUS_RATE_LIMIT_PER_HOUR = _env_int("CONTINUOUS_RATE_LIMIT_PER_HOUR", 1200)
AUTH_LOGIN_RATE_LIMIT_PER_MINUTE = _env_int("AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", 5)
AUTH_LOGIN_RATE_LIMIT_PER_HOUR = _env_int("AUTH_LOGIN_RATE_LIMIT_PER_HOUR", 20)
AUTH_REGISTER_RATE_LIMIT_PER_10_MINUTES = _env_int("AUTH_REGISTER_RATE_LIMIT_PER_10_MINUTES", 3)
AUTH_REGISTER_RATE_LIMIT_PER_DAY = _env_int("AUTH_REGISTER_RATE_LIMIT_PER_DAY", 10)
AUTH_REFRESH_RATE_LIMIT_PER_MINUTE = _env_int("AUTH_REFRESH_RATE_LIMIT_PER_MINUTE", 30)
AUTH_ME_RATE_LIMIT_PER_MINUTE = _env_int("AUTH_ME_RATE_LIMIT_PER_MINUTE", 60)
PROFILE_UPSERT_RATE_LIMIT_PER_MINUTE = _env_int("PROFILE_UPSERT_RATE_LIMIT_PER_MINUTE", 20)
WORKOUTS_RATE_LIMIT_PER_MINUTE = _env_int("WORKOUTS_RATE_LIMIT_PER_MINUTE", 60)
CONTINUOUS_RATE_LIMIT_PER_MINUTE = _env_int("CONTINUOUS_RATE_LIMIT_PER_MINUTE", 30)
CONTINUOUS_RATE_LIMIT_PER_HOUR = _env_int("CONTINUOUS_RATE_LIMIT_PER_HOUR", 500)
COACH_TALK_PREMIUM_RATE_LIMIT_PER_MINUTE = _env_int("COACH_TALK_PREMIUM_RATE_LIMIT_PER_MINUTE", 15)
COACH_TALK_PREMIUM_RATE_LIMIT_PER_HOUR = _env_int("COACH_TALK_PREMIUM_RATE_LIMIT_PER_HOUR", 25)
COACH_TALK_PREMIUM_RATE_LIMIT_PER_DAY = _env_int("COACH_TALK_PREMIUM_RATE_LIMIT_PER_DAY", 25)
COACH_TALK_FREE_RATE_LIMIT_PER_SESSION = _env_int("COACH_TALK_FREE_RATE_LIMIT_PER_SESSION", 3)
COACH_TALK_FREE_RATE_LIMIT_PER_DAY = _env_int("COACH_TALK_FREE_RATE_LIMIT_PER_DAY", 6)

# Never use wildcard CORS in production.
CORS_ALLOWED_ORIGINS = _env_csv_set(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)

# ============================================
# LANGUAGE SETTINGS
# ============================================
SUPPORTED_LANGUAGES = ["en", "no", "da"]
_DEFAULT_LANGUAGE_RAW = (os.getenv("DEFAULT_LANGUAGE", "no") or "no").strip().lower()
DEFAULT_LANGUAGE = _DEFAULT_LANGUAGE_RAW if _DEFAULT_LANGUAGE_RAW in SUPPORTED_LANGUAGES else "no"

# ============================================
# VOICE CONFIGURATION (locale_config SSoT)
# ============================================
def _build_voice_config_from_locales() -> dict:
    voice_config = {}
    for language, locale in SUPPORTED_LOCALES.items():
        display_name = (locale.get("display_name") or {}).get("en", language.upper())
        voice_id = locale_get_voice_id(language, "personal_trainer")
        voice_config[language] = {
            "voice_id": voice_id,
            "name": f"{display_name} Coach",
        }
    return voice_config


def _build_persona_voice_config_from_locales() -> dict:
    persona_voice_config = {}
    for persona in ("personal_trainer", "toxic_mode"):
        voice_ids = {}
        for language, locale in SUPPORTED_LOCALES.items():
            _ = locale  # Keep loop shape explicit for readability.
            voice_ids[language] = locale_get_voice_id(language, persona)
        persona_voice_config[persona] = {
            "voice_ids": voice_ids,
            "name": "Personal Trainer" if persona == "personal_trainer" else "Toxic Mode",
            "stability": 0.7 if persona == "personal_trainer" else 0.25,
            "similarity_boost": 0.9 if persona == "personal_trainer" else 0.85,
            "style": 0.25 if persona == "personal_trainer" else 0.9,
        }
    return persona_voice_config


VOICE_CONFIG = _build_voice_config_from_locales()

# ============================================
# TTS SETTINGS
# ============================================
# Local Qwen3-TTS is disabled (too slow on CPU). Use ElevenLabs instead.
ENABLE_QWEN_TTS = False
# Voice delivery quality (premium speech pacing)
VOICE_TTS_PACING_ENABLED = _env_bool("VOICE_TTS_PACING_ENABLED", True)
VOICE_TEXT_PACING_ENABLED = _env_bool("VOICE_TEXT_PACING_ENABLED", True)
# Optional persistent audio cache for ElevenLabs output.
# Default OFF so current behavior/cost profile remains unchanged until enabled.
TTS_AUDIO_CACHE_ENABLED = _env_bool("TTS_AUDIO_CACHE_ENABLED", False)
TTS_AUDIO_CACHE_READ_ENABLED = _env_bool("TTS_AUDIO_CACHE_READ_ENABLED", True)
TTS_AUDIO_CACHE_WRITE_ENABLED = _env_bool("TTS_AUDIO_CACHE_WRITE_ENABLED", True)
# Bump cache version (for example v1 -> v2) to invalidate old voice files.
TTS_AUDIO_CACHE_VERSION = (os.getenv("TTS_AUDIO_CACHE_VERSION", "v1") or "v1").strip()
# Cache retention controls (applied only when cache write is enabled).
TTS_AUDIO_CACHE_MAX_FILES = _env_int("TTS_AUDIO_CACHE_MAX_FILES", 1000)
TTS_AUDIO_CACHE_MAX_AGE_SECONDS = _env_int("TTS_AUDIO_CACHE_MAX_AGE_SECONDS", 14 * 24 * 3600)
TTS_AUDIO_CACHE_CLEANUP_INTERVAL_WRITES = _env_int("TTS_AUDIO_CACHE_CLEANUP_INTERVAL_WRITES", 25)

# ============================================
# R2 AUDIO PACK CONFIGURATION
# ============================================
R2_BUCKET_NAME = (os.getenv("R2_BUCKET_NAME", "coachi-audio") or "coachi-audio").strip()
R2_ACCOUNT_ID = (os.getenv("R2_ACCOUNT_ID", "") or "").strip()
R2_ACCESS_KEY_ID = (os.getenv("R2_ACCESS_KEY_ID", "") or "").strip()
R2_SECRET_ACCESS_KEY = (os.getenv("R2_SECRET_ACCESS_KEY", "") or "").strip()
R2_PUBLIC_URL = (os.getenv("R2_PUBLIC_URL", "") or "").strip()
AUDIO_PACK_VERSION = (os.getenv("AUDIO_PACK_VERSION", "v1") or "v1").strip()

# ============================================
# BREATH ANALYSIS SETTINGS
# ============================================
# Downsample to reduce CPU and improve stability
BREATH_ANALYSIS_SAMPLE_RATE = 16000
# MFCC extraction is disabled by default in runtime because current coaching
# decisions do not consume MFCC vectors.
BREATH_ANALYSIS_ENABLE_MFCC = _env_bool("BREATH_ANALYSIS_ENABLE_MFCC", False)
# Minimum upload size (bytes) to treat as valid audio
BREATH_MIN_AUDIO_BYTES = 8000
# Hard timeout for runtime breath analysis so a bad chunk cannot stall a worker.
BREATH_ANALYSIS_TIMEOUT_SECONDS = _env_float("BREATH_ANALYSIS_TIMEOUT_SECONDS", 2.5)
# Cooldown after a timeout to avoid piling work onto a still-running analyzer task.
BREATH_ANALYSIS_TIMEOUT_COOLDOWN_SECONDS = _env_float("BREATH_ANALYSIS_TIMEOUT_COOLDOWN_SECONDS", 20.0)
# Cooldown after STT quota/rate-limit failures so workout talk degrades fast instead of retrying every request.
TALK_STT_QUOTA_COOLDOWN_SECONDS = _env_float("TALK_STT_QUOTA_COOLDOWN_SECONDS", 300.0)
# Smoothing for breath metrics (EMA over recent history)
BREATH_SMOOTHING_ALPHA = 0.5
BREATH_SMOOTHING_WINDOW = 4
# Maximum silence before forcing a coach cue (seconds)
# 30s ensures coach doesn't disappear — users expect active coaching
MAX_SILENCE_SECONDS = 30
# Context-aware max-silence tuning (zone-event runtime path)
# Keep MAX_SILENCE_SECONDS for legacy/non-event compatibility.
CONTEXT_AWARE_MAX_SILENCE_ENABLED = _env_bool("CONTEXT_AWARE_MAX_SILENCE_ENABLED", True)
CONTINUOUS_CONTRACT_V2_ENABLED = _env_bool("CONTINUOUS_CONTRACT_V2_ENABLED", True)
PROFILE_DB_ENABLED = _env_bool("PROFILE_DB_ENABLED", True)
# Server-authoritative workout clock for /coach/continuous canonical elapsed/time-left.
SERVER_CLOCK_ENABLED = _env_bool("SERVER_CLOCK_ENABLED", True)
SERVER_CLOCK_DRIFT_LOG_THRESHOLD_SECONDS = _env_int("SERVER_CLOCK_DRIFT_LOG_THRESHOLD_SECONDS", 5)
SERVER_CLOCK_RESYNC_AHEAD_SECONDS = _env_int("SERVER_CLOCK_RESYNC_AHEAD_SECONDS", 20)
SENSOR_MODE_TABLE_V2_ENABLED = _env_bool("SENSOR_MODE_TABLE_V2_ENABLED", True)
COUNTDOWN_ENGINE_ONLY_ENABLED = _env_bool("COUNTDOWN_ENGINE_ONLY_ENABLED", True)
CONTINUOUS_FAILSAFE_ENABLED = _env_bool("CONTINUOUS_FAILSAFE_ENABLED", True)
AUDIO_PREFETCH_ENABLED = _env_bool("AUDIO_PREFETCH_ENABLED", True)
MAX_SILENCE_EASY_RUN_BASE = _env_int("MAX_SILENCE_EASY_RUN_BASE", 60)
MAX_SILENCE_INTERVALS_WORK = _env_int("MAX_SILENCE_INTERVALS_WORK", 30)
MAX_SILENCE_INTERVALS_RECOVERY = _env_int("MAX_SILENCE_INTERVALS_RECOVERY", 45)
NO_HR_STRUCTURE_FINAL_EFFORT_SECONDS = _env_int("NO_HR_STRUCTURE_FINAL_EFFORT_SECONDS", 60)
MAX_SILENCE_RAMP_PER_10MIN = _env_int("MAX_SILENCE_RAMP_PER_10MIN", 15)
MAX_SILENCE_HR_MISSING_MULTIPLIER = _env_float("MAX_SILENCE_HR_MISSING_MULTIPLIER", 1.5)
MAX_SILENCE_BUDGET_EASY_RUN_SECONDS = _env_int("MAX_SILENCE_BUDGET_EASY_RUN_SECONDS", 90)
MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING = _env_int("MAX_SILENCE_INTERVAL_SUPPRESS_REMAINING", 35)
MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS = _env_int("MAX_SILENCE_INTERVAL_WORK_RAMP_SECONDS", 12)

# Keep interval countdown cues reliable by tightening /coach/continuous polling
# during interval phases. This prevents skipping 30/15/5-second windows.
INTERVAL_WORK_MAX_WAIT_SECONDS = _env_int("INTERVAL_WORK_MAX_WAIT_SECONDS", 8)
INTERVAL_RECOVERY_MAX_WAIT_SECONDS = _env_int("INTERVAL_RECOVERY_MAX_WAIT_SECONDS", 5)
INTERVAL_RECOVERY_FINAL_WINDOW_SECONDS = _env_int("INTERVAL_RECOVERY_FINAL_WINDOW_SECONDS", 35)
INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS = _env_int("INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3)
INTERVAL_TRANSITION_MAX_WAIT_SECONDS = _env_int("INTERVAL_TRANSITION_MAX_WAIT_SECONDS", 12)

# Motivation cooldown barrier (Tier D anti-spam)
MOTIVATION_BARRIER_SECONDS_INTERVALS = _env_int("MOTIVATION_BARRIER_SECONDS_INTERVALS", 25)
MOTIVATION_BARRIER_SECONDS_EASY_RUN = _env_int("MOTIVATION_BARRIER_SECONDS_EASY_RUN", 45)
MOTIVATION_MIN_SPACING_INTERVALS = _env_int("MOTIVATION_MIN_SPACING_INTERVALS", 60)
MOTIVATION_MIN_SPACING_EASY_RUN = _env_int("MOTIVATION_MIN_SPACING_EASY_RUN", 120)

# Stage-based motivation (interval_in_target_sustained / easy_run_in_target_sustained)
MOTIVATION_SUSTAIN_SEC_EASY = _env_int("MOTIVATION_SUSTAIN_SEC_EASY", 45)
MOTIVATION_WORK_MIN_ELAPSED = _env_int("MOTIVATION_WORK_MIN_ELAPSED", 10)
MOTIVATION_BARRIER_SEC = _env_int("MOTIVATION_BARRIER_SEC", 20)
EASY_RUN_MOTIVATION_COOLDOWN = _env_int("EASY_RUN_MOTIVATION_COOLDOWN", 120)

# Easy-run stage thresholds (minutes into main phase)
EASY_RUN_STAGE_THRESHOLDS = [20, 40, 60]  # stage 1: 0-20, stage 2: 20-40, stage 3: 40-60, stage 4: 60+

EARLY_WORKOUT_GRACE_SECONDS = 30  # Force coaching output during early workout
# Minimum signal quality required to force a cue after max silence
# Set to 0.0 so the override ALWAYS fires — phone mics are noisy during workouts
# and we never want the coach to go permanently silent
MIN_SIGNAL_QUALITY_TO_FORCE = _env_float("MIN_SIGNAL_QUALITY_TO_FORCE", 0.0)

# Persona-specific voices
# voice_ids now derive from locale_config SUPPORTED_LOCALES (single source of truth).
PERSONA_VOICE_CONFIG = _build_persona_voice_config_from_locales()

# ============================================
# TRAINING LEVEL CONFIGURATION
# ============================================
TRAINING_LEVEL_CONFIG = {
    "beginner": {
        "coaching_frequency_multiplier": 1.5,   # Talk more often
        "intensity_threshold_offset": -10,       # Lower threshold to trigger "intense"
        "tone": "supportive",
        "max_push_intensity": "moderate",        # Never push beginners to extreme
        "prompt_modifier": "Speak to a beginner. Be encouraging and patient. Explain what to do. Never assume fitness knowledge. Use simple language."
    },
    "intermediate": {
        "coaching_frequency_multiplier": 1.0,
        "intensity_threshold_offset": 0,
        "tone": "balanced",
        "max_push_intensity": "intense",
        "prompt_modifier": "Speak to an experienced exerciser. Be direct and motivating. Challenge appropriately."
    },
    "advanced": {
        "coaching_frequency_multiplier": 0.7,    # Talk less (they know what they're doing)
        "intensity_threshold_offset": 10,
        "tone": "direct",
        "max_push_intensity": "critical",
        "prompt_modifier": "Speak to an elite athlete. Be minimal. Only speak when it matters. Push hard."
    }
}

# ============================================
# UI CUSTOMIZATION
# ============================================
# Colors (CSS format)
COLOR_PRIMARY = "#007AFF"  # Blue
COLOR_LISTENING = "#34C759"  # Green
COLOR_SPEAKING = "#FF3B30"  # Red
COLOR_TEXT_PRIMARY = "#1d1d1f"
COLOR_TEXT_SECONDARY = "#86868b"
COLOR_BACKGROUND_START = "#ffffff"
COLOR_BACKGROUND_END = "#f5f5f7"

# Text
STATUS_TEXT_IDLE = "Ready"
STATUS_TEXT_LISTENING = "Listening"
STATUS_TEXT_SPEAKING = "Speaking"
INFO_TEXT_IDLE = "Click to start"
INFO_TEXT_LISTENING = "Analyzing your breath..."
INFO_TEXT_SPEAKING = "Coach is responding..."

# ============================================
# PHASE TIMINGS (seconds)
# ============================================
WARMUP_DURATION = 120  # First 2 minutes
INTENSE_DURATION = 900  # 2-15 minutes
# After INTENSE_DURATION = cooldown

# ============================================
# WELCOME MESSAGES (Gym Companion - Martin Sundby Style)
# ============================================
# Welcome utterance-id rotation tuning
WELCOME_ROTATION_RECENT_K = _env_int("WELCOME_ROTATION_RECENT_K", 2)
WELCOME_ROTATION_AVOID_HOURS = _env_int("WELCOME_ROTATION_AVOID_HOURS", 24)
WELCOME_ROTATION_HISTORY_MAX = _env_int("WELCOME_ROTATION_HISTORY_MAX", 50)
WELCOME_ROTATION_STATE_PATH = (
    _resolve_child_runtime_path(
        INSTANCE_DIR,
        os.getenv("WELCOME_ROTATION_STATE_PATH"),
        "cache/utterance_rotation_state.json",
    )
)

# Spoken once at workout start (before first breath)
# Purpose: Acknowledge start, set expectations, establish rhythm
# Tone: Calm, authoritative, friendly
WELCOME_MESSAGES = {
    "standard": [
        "Good to see you. Let's start with some easy movement and build from there.",
        "Ready when you are. Take a breath, settle in, and we'll ease into it.",
        "Nice timing. Let's warm up properly and set the tone for a good session.",
        "Let's get moving. Controlled pace to start, then we'll find your rhythm.",
        "Welcome back. Focus on how your body feels and we'll build from there.",
        "Alright, let's begin. Smooth and steady, no rush.",
        "Good call showing up. Start easy, the intensity will come naturally."
    ],

    "beginner_friendly": [
        "Great that you're here. We'll start slow and keep it simple.",
        "Welcome. Just focus on breathing and moving at your own pace.",
        "Let's begin easy. No pressure, just getting your body warmed up.",
        "Nice to have you. Take it one step at a time, I'll guide you through.",
        "You're here, that's the hardest part. Now let's ease into it together."
    ],

    "breath_aware": [
        "Take a moment. Deep breath in, slow breath out. Now let's begin.",
        "Start by finding your breath. Shoulders down, chest open, easy pace.",
        "Let's connect with your breathing first. Everything else follows from there.",
        "Settle your breath, relax your body. We'll build the intensity gradually."
    ]
}

# ============================================
# COACH MESSAGES (English for live conversations)
# ============================================
COACH_MESSAGES = {
    "critical": ["STOP! Breathe slowly. You're safe."],

    "warmup": [
        "Welcome. Let's start slow. Find your rhythm.",
        "Good. Breathe in, and out. Settle your shoulders.",
        "Steady now. Don't rush. Warmup first, intensity later.",
        "Easy does it. Focus on breathing, not speed."
    ],

    "cooldown": [
        "Well done. Let the breath settle. You earned it.",
        "Relax. Slow it down. Shoulder and chest relaxed.",
        "Good session. Keep calm and controlled.",
        "Steady breathing. That's how we finish strong.",
        "Nice work. You controlled your effort well."
    ],

    "intense": {
        "calm": [
            "Maintain control. Pace yourself. Don't overdo it.",
            "Good. Keep that rhythm. Slightly faster, not frantic.",
            "PUSH! Harder!",
            "You got more!"
        ],
        "moderate": [
            "Good. Keep that rhythm. Slightly faster, not frantic.",
            "Steady arms, steady breath. That's it.",
            "Keep going! Don't stop!",
            "Good! Hold the pace!"
        ],
        "intense": [
            "Breathing quickened. Slow down a touch.",
            "Maintain control. Pace yourself. Don't overdo it.",
            "One more interval like this and you're done. Focus.",
            "YES! Hold on! Ten more!"
        ]
    }
}

# ============================================
# API SETTINGS
# ============================================
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

# ============================================
# ANALYSIS THRESHOLDS
# ============================================
# Adjust these to tune the breath analysis sensitivity
SILENCE_THRESHOLD = 0.01  # 1% of max amplitude
VOLUME_AMPLIFICATION = 10  # How much to amplify volume readings

# Intensity classification thresholds
INTENSITY_THRESHOLDS = {
    "calm": {"max_volume": 20, "min_silence": 50},
    "moderate": {"max_volume": 40, "max_tempo": 20},
    "intense": {"max_volume": 70, "max_tempo": 35},
    # Above these = critical
}

# ============================================
# BRAIN ROUTER CONFIGURATION
# ============================================
# Choose which AI brain to use: "claude", "openai", "grok", "gemini", "config"
# - "claude": Uses Claude AI (requires ANTHROPIC_API_KEY)
# - "openai": Uses OpenAI GPT (requires OPENAI_API_KEY)
# - "grok":   Uses xAI Grok (requires XAI_API_KEY, OpenAI-compatible API)
# - "gemini": Uses Google Gemini (requires GEMINI_API_KEY)
# - "config": Uses simple config-based messages (no AI, no API key needed)
ACTIVE_BRAIN = os.getenv("ACTIVE_BRAIN", "grok").strip().lower() or "grok"

# Priority routing (try brains in order with timeout + fallback)
USE_PRIORITY_ROUTING = _env_bool("USE_PRIORITY_ROUTING", True)
# Default: Grok first, then immediate config fallback (no Gemini/OpenAI/Claude calls).
BRAIN_PRIORITY = _env_csv_list("BRAIN_PRIORITY", ["grok", "config"])
BRAIN_TIMEOUT = _env_float("BRAIN_TIMEOUT", 1.2)  # global default timeout (seconds) for brains without overrides
# Per-brain timeout overrides. Grok typically needs ~4-5s in production.
BRAIN_TIMEOUTS = _env_json_dict("BRAIN_TIMEOUTS_JSON", {"grok": 6.0})
# Optional per-mode overrides (realtime_coach/chat). Falls back to BRAIN_TIMEOUTS/BRAIN_TIMEOUT.
BRAIN_MODE_TIMEOUTS = _env_json_dict("BRAIN_MODE_TIMEOUTS_JSON", {})
COACH_QA_TIMEOUT_SECONDS = _env_float("COACH_QA_TIMEOUT_SECONDS", 5.0)
COACH_TALK_WAKE_TIMEOUT_SECONDS = _env_float("COACH_TALK_WAKE_TIMEOUT_SECONDS", 1.2)
COACH_TALK_BUTTON_TIMEOUT_SECONDS = _env_float("COACH_TALK_BUTTON_TIMEOUT_SECONDS", 2.0)
TALK_STT_ENABLED = _env_bool("TALK_STT_ENABLED", False)
TALK_CONTEXT_SUMMARY_ENABLED = _env_bool("TALK_CONTEXT_SUMMARY_ENABLED", True)
COACH_QA_MAX_TOKENS = _env_int("COACH_QA_MAX_TOKENS", 80)
COACH_QA_MAX_SENTENCES = _env_int("COACH_QA_MAX_SENTENCES", 3)
COACH_TALK_ALLOWED_TRIGGER_SOURCES = ("wake_word", "button")
COACH_TALK_STRICT_SAFETY_ENABLED = _env_bool("COACH_TALK_STRICT_SAFETY_ENABLED", True)
COACH_TALK_POLICY_ROTATE_ENABLED = _env_bool("COACH_TALK_POLICY_ROTATE_ENABLED", True)
COACH_TALK_POLICY_REFUSAL_BANK = {
    "en": [
        "Lets talk about your workout instead",
        "I am Your Coach and will only speak about related subjects",
        "Lets not talk about that",
    ],
    "no": [
        "La oss snakke om din treningsøkt isteden",
        "Jeg er din Coach og holder meg til relevante temaer.",
        "La oss ikke snakke om det nå",
    ],
}
COACH_TALK_WORKOUT_FALLBACKS = {
    "en": {
        "above_zone": "Check in: ease off a touch and lengthen your exhale.",
        "below_zone": "Build gradually now. Shorter steps and calm breathing.",
        "in_zone": "You're on target. Keep this rhythm and relaxed shoulders.",
        "unknown": "Stay smooth and controlled. Keep your breathing steady.",
    },
    "no": {
        "above_zone": "Sjekk inn: ro litt ned og forleng utpusten.",
        "below_zone": "Bygg gradvis nå. Kortere steg og rolig pust.",
        "in_zone": "Du er i målsonen. Hold rytmen og lave skuldre.",
        "unknown": "Hold det jevnt og kontrollert. Stabil pust hele veien.",
    },
}
#
# Provider client timeout strategy:
# Keep provider HTTP timeout slightly below router timeout so timed-out work
# does not continue running in background threads.
BRAIN_CLIENT_TIMEOUT_MARGIN_SECONDS = _env_float("BRAIN_CLIENT_TIMEOUT_MARGIN_SECONDS", 0.25)
GROK_CLIENT_TIMEOUT_SECONDS = _env_float(
    "GROK_CLIENT_TIMEOUT_SECONDS",
    max(1.0, float(BRAIN_TIMEOUTS.get("grok", BRAIN_TIMEOUT)) - BRAIN_CLIENT_TIMEOUT_MARGIN_SECONDS),
)
USAGE_LIMIT = _env_float("USAGE_LIMIT", 0.9)  # skip brain if usage >= this (optional BRAIN_USAGE map)
BRAIN_COOLDOWN_SECONDS = _env_float("BRAIN_COOLDOWN_SECONDS", 60)
BRAIN_TIMEOUT_COOLDOWN_SECONDS = _env_float("BRAIN_TIMEOUT_COOLDOWN_SECONDS", 30)
BRAIN_INIT_RETRY_SECONDS = _env_float("BRAIN_INIT_RETRY_SECONDS", 5)  # Short cooldown for init failures (API key missing, import error)
BRAIN_QUOTA_COOLDOWN_SECONDS = _env_float("BRAIN_QUOTA_COOLDOWN_SECONDS", 300)  # Longer cooldown for provider quota failures
BRAIN_SLOW_THRESHOLD = _env_float("BRAIN_SLOW_THRESHOLD", 3.0)  # seconds avg latency before skipping (must be > BRAIN_TIMEOUT)
# Per-brain slow-threshold overrides. Grok should not be marked slow at 4-5s.
BRAIN_SLOW_THRESHOLDS = _env_json_dict("BRAIN_SLOW_THRESHOLDS_JSON", {"grok": 6.5})
BRAIN_LATENCY_DECAY_FACTOR = _env_float("BRAIN_LATENCY_DECAY_FACTOR", 0.9)  # Decay old avg_latency toward recent readings
BRAIN_RECENT_CUE_WINDOW = _env_int("BRAIN_RECENT_CUE_WINDOW", 4)  # Anti-repetition memory per session
# Latency-aware response strategy:
# - If expected brain latency is high, return fast config fallback cue immediately.
# - Force one richer AI follow-up cue on the next tick.
LATENCY_FAST_FALLBACK_ENABLED = _env_bool("LATENCY_FAST_FALLBACK_ENABLED", True)
LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS = _env_float("LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", 2.8)
LATENCY_FAST_FALLBACK_MIN_CALLS = _env_int("LATENCY_FAST_FALLBACK_MIN_CALLS", 2)
LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS = _env_float("LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS", 20.0)
# Optional live usage map (0.0-1.0). Example: {"grok": 0.92}
BRAIN_USAGE = _env_json_dict("BRAIN_USAGE_JSON", {})

# STEP 4: Hybrid Brain Strategy
# Use Claude for pattern detection, config for speed
USE_HYBRID_BRAIN = _env_bool("USE_HYBRID_BRAIN", False)  # Disabled by default: pattern insights not wanted during workouts
HYBRID_CLAUDE_FOR_PATTERNS = _env_bool("HYBRID_CLAUDE_FOR_PATTERNS", False)
HYBRID_CONFIG_FOR_SPEED = _env_bool("HYBRID_CONFIG_FOR_SPEED", True)
USE_STRATEGIC_BRAIN = _env_bool("USE_STRATEGIC_BRAIN", False)

# ============================================
# CONTINUOUS COACHING SETTINGS
# ============================================
CONTINUOUS_COACHING_ENABLED = True
DEFAULT_COACHING_INTERVAL = 8  # seconds between coaching ticks
MIN_COACHING_INTERVAL = 6      # fastest interval
MAX_COACHING_INTERVAL = 15     # slowest interval
MIN_TIME_BETWEEN_COACHING = 20  # minimum seconds between spoken messages (prevent over-coaching)

# Optional quality systems (defaulted for behavior parity)
# - Shadow mode logs/observes only.
# - Enforce mode can alter spoken output (on by default for launch quality floor).
COACHING_VALIDATION_SHADOW_MODE = _env_bool("COACHING_VALIDATION_SHADOW_MODE", True)
# Day 3 quality floor: validated fallback templates should protect every spoken cue.
COACHING_VALIDATION_ENFORCE = _env_bool("COACHING_VALIDATION_ENFORCE", True)
BREATHING_TIMELINE_SHADOW_MODE = _env_bool("BREATHING_TIMELINE_SHADOW_MODE", True)
# Timeline enforcement is enabled by default, but runtime only applies it when
# no deterministic zone-event text is active.
BREATHING_TIMELINE_ENFORCE = _env_bool("BREATHING_TIMELINE_ENFORCE", True)

# ============================================
# WORKOUT MODES (BACKEND-ONLY FOR NOW)
# ============================================
SUPPORTED_WORKOUT_MODES = ["standard", "interval", "easy_run"]
DEFAULT_WORKOUT_MODE = "standard"
ZONE_COACHING_WORKOUT_MODES = ["standard", "easy_run", "interval"]

# Coach score rollout switch:
# - cs_v2: new layered score (default)
# - cs_v1: legacy score
# - shadow: compute both, return v1 as primary while logging v2 diagnostics
COACH_SCORE_VERSION = (os.getenv("COACH_SCORE_VERSION", "cs_v2") or "cs_v2").strip().lower()
if COACH_SCORE_VERSION not in {"cs_v1", "cs_v2", "shadow"}:
    COACH_SCORE_VERSION = "cs_v2"
COACH_SCORE_DEBUG_LOGS = _env_bool("COACH_SCORE_DEBUG_LOGS", True)
COACH_TRANSCRIPT_DEBUG_LOGS = _env_bool("COACH_TRANSCRIPT_DEBUG_LOGS", True)
UNIFIED_EVENT_ROUTER_ENABLED = _env_bool("UNIFIED_EVENT_ROUTER_ENABLED", True)
UNIFIED_EVENT_ROUTER_SHADOW = _env_bool("UNIFIED_EVENT_ROUTER_SHADOW", False)
IOS_EVENT_SPEECH_ENABLED = _env_bool("IOS_EVENT_SPEECH_ENABLED", True)
SPEECH_DECISION_OWNER_V2 = _env_bool("SPEECH_DECISION_OWNER_V2", True)
SPEECH_PHASE_FALLBACK_WARMUP_SECONDS = _env_float("SPEECH_PHASE_FALLBACK_WARMUP_SECONDS", 30.0)
SPEECH_PHASE_FALLBACK_INTENSE_SECONDS = _env_float("SPEECH_PHASE_FALLBACK_INTENSE_SECONDS", 35.0)
SPEECH_PHASE_FALLBACK_COOLDOWN_SECONDS = _env_float("SPEECH_PHASE_FALLBACK_COOLDOWN_SECONDS", 40.0)

# CS v2 thresholds
CS_ZONE_PASS_THRESHOLD = _env_float("CS_ZONE_PASS_THRESHOLD", 0.50)
CS_BREATH_MIN_RELIABLE_QUALITY = _env_float("CS_BREATH_MIN_RELIABLE_QUALITY", 0.35)
CS_BREATH_MIN_RELIABLE_SAMPLES = _env_int("CS_BREATH_MIN_RELIABLE_SAMPLES", 6)
CS_BREATH_PASS_MIN_CONFIDENCE = _env_float("CS_BREATH_PASS_MIN_CONFIDENCE", 0.60)
CS_BREATH_PASS_MIN_SCORE = _env_float("CS_BREATH_PASS_MIN_SCORE", 50.0)
CS_STRONG_HR_FOR_MAX_ZONE_COMPLIANCE = _env_float("CS_STRONG_HR_FOR_MAX_ZONE_COMPLIANCE", 0.75)
CS_STRONG_HR_FOR_MAX_SECONDS = _env_float("CS_STRONG_HR_FOR_MAX_SECONDS", 600.0)
CS_MIN_HR_VALID_SECONDS_FOR_PILLAR = _env_float("CS_MIN_HR_VALID_SECONDS_FOR_PILLAR", 120.0)
CS_MIN_ZONE_VALID_SECONDS_FOR_CAP = _env_float("CS_MIN_ZONE_VALID_SECONDS_FOR_CAP", 120.0)
CS_MIN_ZONE_VALID_SECONDS_FOR_SCORE = _env_float("CS_MIN_ZONE_VALID_SECONDS_FOR_SCORE", 30.0)
CS_MIN_PHASE_VALID_SECONDS = _env_float("CS_MIN_PHASE_VALID_SECONDS", 30.0)

# Target generation safety
TARGET_MIN_HALF_WIDTH_BPM = _env_int("TARGET_MIN_HALF_WIDTH_BPM", 8)  # +/- 8 bpm
TARGET_HR_UPPER_ABSOLUTE_CAP = _env_int("TARGET_HR_UPPER_ABSOLUTE_CAP", 195)

# Auto target bands (primary HRR, fallback %HRmax)
STEADY_HRR_BANDS = {
    "easy": (0.55, 0.68),
    "medium": (0.68, 0.80),
    "hard": (0.80, 0.90),
}
STEADY_HRMAX_BANDS = {
    "easy": (0.65, 0.75),
    "medium": (0.75, 0.85),
    "hard": (0.85, 0.92),
}
INTERVAL_WORK_HRR_BANDS = {
    "easy": (0.70, 0.82),
    "medium": (0.80, 0.90),
    "hard": (0.88, 0.95),
}
INTERVAL_RECOVERY_HRR_BANDS = {
    "easy": (0.55, 0.65),
    "medium": (0.58, 0.68),
    "hard": (0.60, 0.72),
}
INTERVAL_WORK_HRMAX_BANDS = {
    "easy": (0.75, 0.85),
    "medium": (0.85, 0.92),
    "hard": (0.88, 0.94),
}

# Running session templates (v1)
SUPPORTED_INTERVAL_TEMPLATES = ["4x4", "8x1", "10x30/30"]
DEFAULT_INTERVAL_TEMPLATE = (os.getenv("DEFAULT_INTERVAL_TEMPLATE", "4x4") or "4x4").strip()

INTERVAL_TEMPLATES = {
    "4x4": {
        "warmup_seconds": 600,
        "work_seconds": 240,
        "rest_seconds": 180,
        "reps": 4,
        "cooldown_seconds": 480,
        "work_target": "Z4",
        "rest_target": "Z1-2",
        "work_hr_enforced": True,
    },
    "8x1": {
        "warmup_seconds": 600,
        "work_seconds": 60,
        "rest_seconds": 60,
        "reps": 8,
        "cooldown_seconds": 480,
        "work_target": "Z4-5",
        "rest_target": "Z1-2",
        # HR lags on short reps; timing cues are primary.
        "work_hr_enforced": False,
    },
    "10x30/30": {
        "warmup_seconds": 600,
        "work_seconds": 30,
        "rest_seconds": 30,
        "reps": 10,
        "cooldown_seconds": 360,
        "work_target": "hard",
        "rest_target": "easy",
        # HR lags on very short reps; timing cues are primary.
        "work_hr_enforced": False,
    },
}

# Zone 2 definition
# Primary: HRR (Karvonen) when resting HR exists
ZONE2_HRR_LOW = _env_float("ZONE2_HRR_LOW", 0.60)
ZONE2_HRR_HIGH = _env_float("ZONE2_HRR_HIGH", 0.70)
# Fallback: HRmax percentages when resting HR is missing
ZONE2_HRMAX_LOW = _env_float("ZONE2_HRMAX_LOW", 0.70)
ZONE2_HRMAX_HIGH = _env_float("ZONE2_HRMAX_HIGH", 0.80)

# HR quality policy
HR_QUALITY_STALE_SECONDS = _env_float("HR_QUALITY_STALE_SECONDS", 8.0)
HR_QUALITY_SPIKE_DELTA_BPM = _env_float("HR_QUALITY_SPIKE_DELTA_BPM", 20.0)
HR_QUALITY_SPIKE_WINDOW_SECONDS = _env_float("HR_QUALITY_SPIKE_WINDOW_SECONDS", 2.0)
HR_QUALITY_MIN_CONFIDENCE = _env_float("HR_QUALITY_MIN_CONFIDENCE", 0.5)

# Event stability
HR_ZONE_HYSTERESIS_BPM = _env_float("HR_ZONE_HYSTERESIS_BPM", 3.0)
HR_ZONE_DWELL_SECONDS = _env_float("HR_ZONE_DWELL_SECONDS", 8.0)

# Movement/cadence fallback (sensor layer B/C)
MOVEMENT_SCORE_PAUSE_THRESHOLD = _env_float("MOVEMENT_SCORE_PAUSE_THRESHOLD", 0.12)
MOVEMENT_SCORE_ACTIVE_THRESHOLD = _env_float("MOVEMENT_SCORE_ACTIVE_THRESHOLD", 0.25)
MOVEMENT_PAUSE_DWELL_SECONDS = _env_float("MOVEMENT_PAUSE_DWELL_SECONDS", 8.0)
MOVEMENT_PAUSE_MIN_HR_DROP_BPM = _env_float("MOVEMENT_PAUSE_MIN_HR_DROP_BPM", 1.0)
MOVEMENT_PAUSE_HR_DROP_MAX_GAP_SECONDS = _env_float("MOVEMENT_PAUSE_HR_DROP_MAX_GAP_SECONDS", 10.0)
HR_PAUSE_RAPID_DROP_BPM = _env_float("HR_PAUSE_RAPID_DROP_BPM", 6.0)
HR_PAUSE_RAPID_DROP_MAX_GAP_SECONDS = _env_float("HR_PAUSE_RAPID_DROP_MAX_GAP_SECONDS", 8.0)

# Phase 3: sustained push/ease rules
ZONE_BELOW_PUSH_SUSTAIN_SECONDS = _env_float("ZONE_BELOW_PUSH_SUSTAIN_SECONDS", 25.0)
ZONE_BELOW_PUSH_MIN_MOVEMENT_SCORE = _env_float("ZONE_BELOW_PUSH_MIN_MOVEMENT_SCORE", 0.30)
ZONE_ABOVE_EASE_SUSTAIN_SECONDS = _env_float("ZONE_ABOVE_EASE_SUSTAIN_SECONDS", 20.0)
ZONE_ABOVE_EASE_MIN_HR_RISE_BPM = _env_float("ZONE_ABOVE_EASE_MIN_HR_RISE_BPM", 1.5)
ZONE_ABOVE_EASE_RISE_MAX_GAP_SECONDS = _env_float("ZONE_ABOVE_EASE_RISE_MAX_GAP_SECONDS", 10.0)
ZONE_SUSTAINED_EVENT_REPEAT_SECONDS = _env_float("ZONE_SUSTAINED_EVENT_REPEAT_SECONDS", 45.0)

# Coaching style controls frequency/tone only - never core decision logic.
SUPPORTED_COACHING_STYLES = ["minimal", "normal", "motivational"]
DEFAULT_COACHING_STYLE = (
    os.getenv("DEFAULT_COACHING_STYLE", "normal") or "normal"
).strip().lower()
COACHING_STYLE_COOLDOWNS = {
    "minimal": {
        "min_seconds_between_any_speech": 30,
        "min_seconds_between_same_cue_type": 90,
        "max_cues_per_10min": 10,
        "praise_min_seconds": 360,
    },
    "normal": {
        "min_seconds_between_any_speech": 25,
        "min_seconds_between_same_cue_type": 60,
        "max_cues_per_10min": 16,
        "praise_min_seconds": 240,
    },
    "motivational": {
        "min_seconds_between_any_speech": 20,
        "min_seconds_between_same_cue_type": 45,
        "max_cues_per_10min": 22,
        "praise_min_seconds": 150,
    },
}

# Phase 4: LLM is allowed to rewrite deterministic zone cues for wording only.
# Event decisions, cooldowns, and scoring remain owned by the event motor.
ZONE_EVENT_LLM_REWRITE_ENABLED = _env_bool("ZONE_EVENT_LLM_REWRITE_ENABLED", False)
ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS = _env_float("ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS", 0.9)
ZONE_EVENT_LLM_REWRITE_MAX_WORDS = _env_int("ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 16)
ZONE_EVENT_LLM_REWRITE_MAX_CHARS = _env_int("ZONE_EVENT_LLM_REWRITE_MAX_CHARS", 120)
ZONE_EVENT_LLM_REWRITE_ALLOWED_EVENTS = _env_csv_list(
    "ZONE_EVENT_LLM_REWRITE_ALLOWED_EVENTS",
    [
        "above_zone",
        "above_zone_ease",
        "below_zone",
        "below_zone_push",
        "in_zone_recovered",
        "phase_change_work",
        "phase_change_rest",
        "phase_change_warmup",
        "phase_change_cooldown",
        "pause_detected",
        "pause_resumed",
        "max_silence_override",
    ],
)

# Phase 5: personalization is analytics/insight only in v1 (no decision mutation).
ZONE_PERSONALIZATION_ENABLED = _env_bool("ZONE_PERSONALIZATION_ENABLED", True)
ZONE_PERSONALIZATION_STORAGE_PATH = (
    _resolve_child_runtime_path(
        INSTANCE_DIR,
        os.getenv("ZONE_PERSONALIZATION_STORAGE_PATH"),
        "zone_personalization.json",
    )
)
ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES = _env_int("ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES", 24)
ZONE_PERSONALIZATION_MAX_SESSION_HISTORY = _env_int("ZONE_PERSONALIZATION_MAX_SESSION_HISTORY", 20)

# STEP 2: Intensity-driven message bank with personality
# Message characteristics:
#   critical → FIRM, SAFETY-FIRST: 1-3 words, urgent tone
#   calm → REASSURING, CALM: 3-5 words, gentle encouragement
#   moderate → GUIDING, ENCOURAGING: 2-4 words, supportive
#   intense → ASSERTIVE, FOCUSED: 2-3 words, direct motivation
CONTINUOUS_COACH_MESSAGES = {
    # CRITICAL - Firm, safety-first (1-3 words, URGENT)
    "critical": [
        "STOP!",
        "Breathe slow!",
        "Easy now!",
        "Slow down!",
        "Too hard!"
    ],

    # WARMUP - Reassuring, calm (3-5 words)
    "warmup": [
        "Easy pace, nice start.",
        "Steady, good warmup.",
        "Gentle, keep warming up.",
        "Nice and easy.",
        "Perfect warmup pace."
    ],

    # COOLDOWN - Reassuring, calm (3-5 words)
    "cooldown": [
        "Bring it down, easy now.",
        "Slow breaths, good cooldown.",
        "Ease off, nice work.",
        "Almost done, slow it.",
        "Perfect, keep slowing down."
    ],

    # INTENSE PHASE - Personality by intensity level
    "intense": {
        # CALM during intense - Reassuring but encouraging (3-5 words)
        "calm": [
            "You can push harder!",
            "More effort, you got this!",
            "Speed up a bit!",
            "Give me more power!",
            "Let's pick up the pace!"
        ],

        # MODERATE during intense - Guiding, encouraging (2-4 words)
        "moderate": [
            "Keep going, good pace!",
            "Stay with it!",
            "Nice rhythm, maintain!",
            "You got this!",
            "Good work, keep steady!"
        ],

        # INTENSE during intense - Assertive, focused (2-3 words)
        "intense": [
            "Perfect! Hold it!",
            "Yes! Strong!",
            "Keep this!",
            "Excellent work!",
            "Ten more seconds!"
        ]
    }
}

# ============================================
# NORWEGIAN WELCOME MESSAGES
# ============================================
WELCOME_MESSAGES_NO = {
    "standard": [
        "Fint at du er her. Vi starter rolig og bygger derfra.",
        "Klar når du er. Ta et pust, finn roen, så setter vi i gang.",
        "Bra timing. La oss varme opp ordentlig og legge grunnlaget.",
        "La oss komme i gang. Kontrollert tempo til å begynne med.",
        "Velkommen tilbake. Kjenn på kroppen så bygger vi derfra.",
        "Ok, la oss begynne. Rolig og jevnt, uten stress.",
        "Bra at du dukket opp. Start rolig, intensiteten kommer naturlig."
    ],
    "beginner_friendly": [
        "Fint at du er her. Vi starter sakte og holder det enkelt.",
        "Velkommen. Bare fokuser på pusten og beveg deg i ditt tempo.",
        "La oss starte rolig. Ingen press, bare få kroppen varm.",
        "Godt å ha deg her. Ett steg om gangen, jeg guider deg.",
        "Du er her, det er det vanskeligste. Nå tar vi det rolig sammen."
    ],
    "breath_aware": [
        "Ta et øyeblikk. Dyp innpust, rolig utpust. Nå begynner vi.",
        "Start med å finne pusten. Skuldrene ned, brystet åpent, rolig tempo.",
        "La oss koble på pusten først. Alt annet følger derfra.",
        "Finn roen i pusten, slapp av kroppen. Vi bygger intensiteten gradvis."
    ]
}

# ============================================
# NORWEGIAN COACH MESSAGES
# ============================================
COACH_MESSAGES_NO = {
    "critical": ["STOPP! Pust sakte. Du er trygg."],

    "warmup": [
        "Velkommen. La oss starte rolig. Finn rytmen din.",
        "Bra. Pust inn, og ut. Slapp av skuldrene.",
        "Rolig nå. Ikke stress. Oppvarming først.",
        "Ta det med ro. Fokuser på pusten."
    ],

    "cooldown": [
        "Bra jobbet. La pusten roe seg. Du fortjener det.",
        "Slapp av. Senk tempoet. Skuldre og bryst avslappet.",
        "God økt. Hold deg rolig og kontrollert.",
        "Jevn pust. Slik avslutter vi sterkt.",
        "Bra jobbet. Du kontrollerte innsatsen godt."
    ],

    "intense": {
        "calm": [
            "Behold kontrollen. Hold tempoet. Ikke overdrive.",
            "Bra. Hold rytmen. Litt raskere, ikke hektisk.",
            "TRYKK! Hardere!",
            "Du har mer!"
        ],
        "moderate": [
            "Bra. Hold rytmen. Litt raskere, ikke hektisk.",
            "Sterke armer, stø pust. Der ja.",
            "Fortsett! Ikke stopp!",
            "Bra! Hold tempoet!"
        ],
        "intense": [
            "Pusten øker. Senk litt.",
            "Behold kontrollen. Hold tempoet.",
            "En runde til slik, så er du ferdig. Fokus.",
            "JA! Hold ut! Ti til!"
        ]
    }
}

# ============================================
# NORWEGIAN CONTINUOUS COACH MESSAGES
# ============================================
CONTINUOUS_COACH_MESSAGES_NO = {
    "critical": [
        "STOPP!",
        "Pust rolig!",
        "Ta det rolig!",
        "Senk farten!",
        "For hardt!"
    ],

    "warmup": [
        "Rolig tempo, fin start.",
        "Jevnt, god oppvarming.",
        "Rolig, fortsett oppvarmingen.",
        "Fint og rolig.",
        "Perfekt oppvarmingstempo."
    ],

    "cooldown": [
        "Senk tempoet, ta det rolig nå.",
        "Rolige pust, god nedkjøling.",
        "Slipp av, bra jobbet.",
        "Nesten ferdig, senk farten.",
        "Perfekt, fortsett å roe ned."
    ],

    "intense": {
        "calm": [
            "Du kan presse hardere!",
            "Mer innsats, du klarer det!",
            "Øk tempoet.",
            "Mer press nå!",
            "La oss øke farten!"
        ],
        "moderate": [
            "Fortsett, godt tempo!",
            "Hold deg fokusert!",
            "Bra tempo!",
            "Du klarer det!",
            "Bra jobba! Hold jevnt tempo."
        ],
        "intense": [
            "Perfekt! Hold tempoet!",
            "Ja! Sterkt!",
            "Behold dette!",
            "Utmerket jobbet!",
            "Ti sekunder til!"
        ]
    }
}

# ============================================
# TOXIC MODE MESSAGES (EN + NO)
# ============================================
TOXIC_MODE_MESSAGES = {
    "en": {
        "warmup": [
            "Warming up?! We're WASTING TIME!",
            "Move FASTER or go home!",
            "My GRANDMOTHER warms up faster!",
            "This is PATHETIC! Let's GO!",
            "You call this a warmup? I call it a NAP!"
        ],
        "intense": {
            "calm": [
                "PATHETIC! My grandma pushes harder!",
                "Are you even TRYING?! MOVE!",
                "I've seen SNAILS with more intensity!",
                "Is that ALL you got?! EMBARRASSING!",
                "WAKE UP! This isn't a spa day!"
            ],
            "moderate": [
                "Barely acceptable. Give me MORE!",
                "You can do better than THAT!",
                "I'm NOT impressed yet. HARDER!",
                "Keep going or I'll double it!",
                "That's it?! Push HARDER!"
            ],
            "intense": [
                "FINALLY! Was that so hard?!",
                "NOW we're talking! Don't you DARE slow down!",
                "THERE it is! About TIME!",
                "YES! That's what I want! MORE!",
                "Not bad. But I want BETTER!"
            ]
        },
        "cooldown": [
            "Done already?! Fine. You EARNED this break.",
            "Okay, okay. You survived. Barely.",
            "Not the worst I've seen. Rest up.",
            "Acceptable performance. BARELY acceptable.",
            "Alright, breathe. You'll need it for next time."
        ],
        "critical": [
            "Alright, real talk. Breathe. Safety first.",
            "Okay, stop. I'm tough, not stupid. Rest.",
            "Hey. Real break. Breathe slow. I mean it."
        ]
    },
    "no": {
        "warmup": [
            "Oppvarming?! Vi KASTER BORT TID!",
            "Beveg deg RASKERE eller gå hjem!",
            "BESTEMORA mi varmer opp raskere!",
            "Dette er PATETISK! La oss KJØRE!",
            "Kaller du dette oppvarming? Jeg kaller det en LITEN BLUND!"
        ],
        "intense": {
            "calm": [
                "PATETISK! Bestemora mi presser hardere!",
                "PRØVER du i det hele tatt?! BEVEG DEG!",
                "Jeg har sett SNEGLER med mer intensitet!",
                "Er det ALT du har?! PINLIG!",
                "VÅKN OPP! Dette er ikke en spa-dag!"
            ],
            "moderate": [
                "Så vidt godkjent. Gi meg MER!",
                "Du kan bedre enn DET!",
                "Jeg er IKKE imponert ennå. HARDERE!",
                "Fortsett ellers dobler jeg det!",
                "Er det alt?! TRYKK HARDERE!"
            ],
            "intense": [
                "ENDELIG! Var det så vanskelig?!",
                "NÅ snakker vi! Ikke VÅG å senke farten!",
                "DER er det! På TIDE!",
                "JA! Det er det jeg vil ha! MER!",
                "Ikke verst. Men jeg vil ha BEDRE!"
            ]
        },
        "cooldown": [
            "Ferdig allerede?! Greit. Du FORTJENTE denne pausen.",
            "Ok, ok. Du overlevde. Så vidt.",
            "Ikke det verste jeg har sett. Hvil deg.",
            "Godkjent prestasjon. Så vidt godkjent.",
            "Greit, pust. Du trenger det til neste gang."
        ],
        "critical": [
            "Ok, alvor nå. Pust. Sikkerhet først.",
            "Ok, stopp. Jeg er toff, ikke dum. Hvil.",
            "Hei. Ordentlig pause. Pust rolig. Jeg mener det."
        ]
    }
}

# ============================================
# DEPLOYMENT
# ============================================
GITHUB_REPO = "https://github.com/98Mvg/treningscoach-backend"
PRODUCTION_URL = "https://treningscoach-backend.onrender.com"
