# main.py - MAIN FILE FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify, Response, stream_with_context, render_template, make_response
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
import json
import wave
import math
import random
import logging
import asyncio
import time
from datetime import datetime
import config  # Import central configuration
from brain_router import BrainRouter  # Import Brain Router
from session_manager import SessionManager  # Import Session Manager
from persona_manager import PersonaManager  # Import Persona Manager
from coaching_intelligence import should_coach_speak, calculate_next_interval, apply_max_silence_override  # Import coaching intelligence
from user_memory import UserMemory  # STEP 5: Import user memory
from voice_intelligence import VoiceIntelligence  # STEP 6: Import voice intelligence
from tts_service import synthesize_speech_mock  # Import mock TTS (Qwen disabled)
from elevenlabs_tts import ElevenLabsTTS  # Import ElevenLabs TTS
from strategic_brain import get_strategic_brain  # Import Strategic Brain for high-level coaching
from coach_personality import get_coach_prompt, ENDURANCE_COACH_PERSONALITY  # Import coach personality
from database import init_db  # Import database initialization
from breath_analyzer import BreathAnalyzer  # Import advanced breath analysis
from auth_routes import auth_bp  # Import auth blueprint
from norwegian_phrase_quality import rewrite_norwegian_phrase
from coaching_engine import validate_coaching_text, get_template_message
from breathing_timeline import BreathingTimeline

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
    then config-level voice maps.
    """
    persona_config = getattr(config, "PERSONA_VOICE_CONFIG", {}) or {}
    voice_config = getattr(config, "VOICE_CONFIG", {}) or {}
    personal_ids = (persona_config.get("personal_trainer", {}) or {}).get("voice_ids", {}) or {}
    toxic_ids = (persona_config.get("toxic_mode", {}) or {}).get("voice_ids", {}) or {}
    voice_config_en = (voice_config.get("en", {}) or {}).get("voice_id", "")
    voice_config_no = (voice_config.get("no", {}) or {}).get("voice_id", "")

    candidates = [
        ("ELEVENLABS_VOICE_ID", os.getenv("ELEVENLABS_VOICE_ID", "")),
        ("ELEVENLABS_VOICE_ID_EN", os.getenv("ELEVENLABS_VOICE_ID_EN", "")),
        ("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", "")),
        ("config.PERSONA_VOICE_CONFIG.personal_trainer.en", personal_ids.get("en", "")),
        ("config.VOICE_CONFIG.en", voice_config_en),
        ("ELEVENLABS_VOICE_ID_NO", os.getenv("ELEVENLABS_VOICE_ID_NO", "")),
        ("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", "")),
        ("config.PERSONA_VOICE_CONFIG.personal_trainer.no", personal_ids.get("no", "")),
        ("config.VOICE_CONFIG.no", voice_config_no),
        ("config.PERSONA_VOICE_CONFIG.toxic_mode.en", toxic_ids.get("en", "")),
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
        return f"CoachScore: {clamped} — Solid jobb. Du traff intensiteten som forbedrer helsa di."
    return f"CoachScore: {clamped} — Solid work. You hit the intensity that improves your health."

# Common English words that should never appear in Norwegian coaching output
_ENGLISH_COACHING_WORDS = {
    "keep going", "good job", "push harder", "well done", "hold on",
    "nice work", "stay focused", "you got this", "let's go", "come on",
    "great work", "push it", "almost there", "hang in there", "breathe",
    "slow down", "speed up", "perfect", "excellent", "amazing",
    "fantastic", "steady", "hold it", "more effort", "pick up",
}

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
    # No Norwegian characters AND only ASCII letters = likely English
    has_norwegian = any(c in text for c in "æøåÆØÅ")
    if not has_norwegian:
        words = text.split()
        if len(words) >= 2:
            # Common English function words that don't exist in Norwegian
            english_markers = {"the", "is", "are", "you", "your", "this", "that", "it", "do", "don't"}
            if any(w.lower().rstrip(".,!?") in english_markers for w in words):
                return True
    return False


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
        if lowered.startswith("fortsett") or "æ" in lowered or "ø" in lowered or "å" in lowered:
            logger.warning(f"Language guard corrected NO->EN drift: '{stripped}'")
            return "Keep going!"
    elif normalized_language == "no":
        if lowered in {"keep going", "keep going!"}:
            logger.warning(f"Language guard corrected EN->NO drift: '{stripped}'")
            return "Fortsett!"
        # Broader detection: English-dominant output when Norwegian expected
        if _looks_english(stripped):
            import random
            fallback_messages = getattr(config, "CONTINUOUS_COACH_MESSAGES_NO", {})
            if phase == "intense":
                intense = fallback_messages.get("intense", {})
                pool = intense.get("moderate", ["Hold trykket oppe.", "Bra flyt, fortsett."])
            elif phase == "cooldown":
                pool = fallback_messages.get("cooldown", ["Rolige pust.", "Senk tempoet rolig."])
            else:
                pool = fallback_messages.get("warmup", ["Fortsett!", "Kjør på!", "Bra jobba!"])
            replacement = random.choice(pool)
            logger.warning(f"Language guard replaced English text in NO mode: '{stripped}' -> '{replacement}'")
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
            paced_text = voice_intelligence.apply_text_rhythm(
                message=text,
                language=normalized_language,
                emotional_mode=selected_mode,
                pacing=voice_pacing,
            )
            if paced_text != text:
                logger.info("Voice text pacing applied: %r -> %r", text, paced_text)
            tts_text = paced_text

        if USE_ELEVENLABS:
            # Use ElevenLabs with persona-specific voice settings
            pacing_override = voice_pacing if getattr(config, "VOICE_TTS_PACING_ENABLED", True) else None
            result = elevenlabs_tts.generate_audio(
                tts_text,
                language=normalized_language,
                persona=selected_persona,
                voice_pacing=pacing_override,
            )
            print(f"[TTS] OK lang={normalized_language} persona={selected_persona} mode={selected_mode} file={os.path.basename(result)}")
            return result
        else:
            # Fallback to mock (Qwen disabled)
            print(f"[TTS] MOCK (ElevenLabs disabled) lang={normalized_language}")
            return synthesize_speech_mock(tts_text)
    except Exception as e:
        logger.error(f"TTS failed, using mock: {e}")
        print(f"[TTS] FAILED lang={language} persona={persona} error={type(e).__name__}: {e}")
        # Fallback to mock for development/testing
        return synthesize_speech_mock(text)

# ============================================
# API ENDPOINTS
# ============================================

WEB_VARIANT_TEMPLATES = {
    "claude": "index_claude.html",
    "codex": "index_codex.html",
}
DEFAULT_WEB_VARIANT = getattr(config, "WEB_UI_VARIANT", "codex")


def _resolve_web_variant(raw_variant: str = None):
    """Resolve requested web variant to a known template with safe fallback."""
    candidate = (raw_variant or DEFAULT_WEB_VARIANT or "codex").strip().lower()
    if candidate not in WEB_VARIANT_TEMPLATES:
        candidate = "codex"
    return candidate, WEB_VARIANT_TEMPLATES[candidate]


@app.route('/')
def home():
    """Homepage - Workout UI with player controls"""
    variant, template = _resolve_web_variant(request.args.get("variant"))
    response = make_response(render_template(template))
    response.headers["X-Web-Variant"] = variant
    return response


@app.route('/preview')
def preview_compare():
    """Side-by-side compare page for claude vs codex web variants."""
    return render_template('site_compare.html')


@app.route('/preview/<variant>')
def preview_variant(variant):
    """Preview a specific web variant without changing deploy defaults."""
    resolved_variant, template = _resolve_web_variant(variant)
    response = make_response(render_template(template))
    response.headers["X-Web-Variant"] = resolved_variant
    return response

@app.route('/health')
def health():
    """Enkel helse-sjekk for å se at serveren lever"""
    return jsonify({
        "status": "healthy",
        "version": config.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "analyze": "/analyze",
            "coach": "/coach",
            "download": "/download/<filename>",
            "welcome": "/welcome"
        }
    })

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
        language = normalize_language_code(request.args.get('language', 'en'))
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
        language = normalize_language_code(request.form.get('language', 'en'))

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
        language = normalize_language_code(request.form.get('language', 'en'))
        training_level = request.form.get('training_level', 'intermediate')
        persona = request.form.get('persona', 'personal_trainer')
        workout_mode = request.form.get('workout_mode', config.DEFAULT_WORKOUT_MODE)
        user_name = request.form.get('user_name', '').strip()

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

        logger.info(f"Continuous coaching tick: session={session_id}, phase={phase}, mode={workout_mode}, elapsed={elapsed_seconds}s, lang={language}, level={training_level}, persona={persona}, user={user_name or 'anon'}")

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
                "metadata": {"workout_mode": workout_mode, "user_name": user_name, "user_id": user_id}
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

        current_user_id = session_manager.sessions.get(session_id, {}).get("metadata", {}).get("user_id", "unknown")

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
            coach_score = _coach_score_from_intensity(breath_data.get("intensity", "moderate"))
            coach_score_line = _coach_score_line(coach_score, language)

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
        if is_first_breath:
            # Always speak on first breath to welcome the user
            speak_decision = True
            reason = "welcome_message"
            workout_state["is_first_breath"] = False  # Clear flag
            workout_state["use_welcome_phrase"] = True  # Flag to use specific cached phrase
            logger.info(f"First breath detected - will provide welcome message")
        else:
            # STEP 6: Check if coach should stay silent (optimal breathing)
            should_be_silent, silence_reason = voice_intelligence.should_stay_silent(
                breath_data=breath_data,
                phase=phase,
                last_coaching=last_coaching,
                elapsed_seconds=elapsed_seconds,
                session_id=session_id
            )

            if should_be_silent:
                # Cap silence so coach doesn't disappear
                max_silence = getattr(config, "MAX_SILENCE_SECONDS", 60)
                min_quality = getattr(config, "MIN_SIGNAL_QUALITY_TO_FORCE", 0.0)
                signal_quality = breath_data.get("signal_quality") or 0.0

                if elapsed_since_last is not None and elapsed_since_last >= max_silence and signal_quality >= min_quality:
                    speak_decision = True
                    reason = "max_silence_override"
                    logger.info(f"Voice intelligence override: speaking after {elapsed_since_last:.0f}s silence")
                else:
                    # Silence = confidence
                    logger.info(f"Voice intelligence: staying silent ({silence_reason})")
                    speak_decision = False
                    reason = silence_reason
            else:
                # Decide if coach should speak (STEP 1/2 logic)
                speak_decision, reason = should_coach_speak(
                    current_analysis=breath_data,
                    last_analysis=last_breath,
                    coaching_history=coaching_context["coaching_history"],
                    phase=phase,
                    training_level=training_level,
                    elapsed_seconds=elapsed_seconds
                )

            # Hard silence cap for guided mode: coach must re-engage at bounded intervals
            max_silence = getattr(config, "MAX_SILENCE_SECONDS", 60)
            speak_decision, reason = apply_max_silence_override(
                should_speak=speak_decision,
                reason=reason,
                elapsed_since_last=elapsed_since_last,
                max_silence_seconds=max_silence
            )

            logger.info(f"Coaching decision: should_speak={speak_decision}, reason={reason}, "
                        f"signal_quality={breath_data.get('signal_quality', 'N/A')}, "
                        f"elapsed_since_last={elapsed_since_last}, "
                        f"is_first_breath={breath_data.get('is_first_breath', False)}")

        # Latency strategy: if previous tick used fast fallback, force one richer follow-up cue.
        if not is_first_breath and latency_state.get("pending_rich_followup"):
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

        if speak_decision and timeline_cue and timeline_enforce and not use_welcome and not fast_fallback_used:
            coach_text = timeline_cue
            brain_meta = {
                "provider": "system",
                "source": "breathing_timeline",
                "status": "timeline_override",
                "mode": "realtime_coach",
            }

        validation_shadow = bool(getattr(config, "COACHING_VALIDATION_SHADOW_MODE", True))
        validation_enforce = bool(getattr(config, "COACHING_VALIDATION_ENFORCE", False))
        if speak_decision and not use_welcome and (validation_shadow or validation_enforce):
            is_valid = validate_coaching_text(
                text=coach_text,
                phase=phase,
                intensity=breath_data.get("intensity", "moderate"),
                persona=persona or "personal_trainer",
                language=language,
                mode="realtime",
            )
            if not is_valid:
                logger.warning(
                    "Coaching validation failed (phase=%s intensity=%s persona=%s enforce=%s): %r",
                    phase,
                    breath_data.get("intensity", "moderate"),
                    persona or "personal_trainer",
                    validation_enforce,
                    coach_text,
                )
                if validation_enforce:
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
        if speak_decision and not use_welcome and not fast_fallback_used:
            coach_text = voice_intelligence.add_human_variation(coach_text)

        coach_text = enforce_language_consistency(coach_text, language, phase=phase)
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

        # STEP 6: Increase wait time if coach is overtalking
        if voice_intelligence.should_reduce_frequency(breath_data, coaching_context["coaching_history"]):
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

        coach_score = _coach_score_from_intensity(breath_data.get("intensity", "moderate"))
        coach_score_line = _coach_score_line(coach_score, language)

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
            "coach_score": coach_score,
            "coach_score_line": coach_score_line,
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
        }

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

@app.route('/brain/health', methods=['GET'])
def brain_health():
    """
    Check health of active brain.

    Returns brain status and health information.
    """
    try:
        health = brain_router.health_check()
        logger.info(f"Brain health check: {health}")
        return jsonify(health), 200 if health["healthy"] else 503

    except Exception as e:
        logger.error(f"Error checking brain health: {e}", exc_info=True)
        return jsonify({
            "active_brain": "unknown",
            "healthy": False,
            "message": str(e)
        }), 500

@app.route('/brain/switch', methods=['POST'])
def switch_brain():
    """
    Switch to a different brain at runtime.

    Request body:
    {
        "brain": "claude" | "openai" | "config"
    }

    Returns success status and new active brain.
    """
    try:
        data = request.get_json()
        if not data or 'brain' not in data:
            return jsonify({"error": "Missing 'brain' parameter"}), 400

        new_brain = data['brain']
        valid_brains = ['priority', 'claude', 'openai', 'grok', 'gemini', 'config']

        if new_brain not in valid_brains:
            return jsonify({
                "error": f"Invalid brain. Must be one of: {', '.join(valid_brains)}"
            }), 400

        success = brain_router.switch_brain(new_brain)

        if success:
            return jsonify({
                "success": True,
                "active_brain": brain_router.get_active_brain(),
                "message": f"Switched to {new_brain}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "active_brain": brain_router.get_active_brain(),
                "message": f"Failed to switch to {new_brain}, stayed on current brain"
            }), 500

    except Exception as e:
        logger.error(f"Error switching brain: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ============================================
# STREAMING CHAT ENDPOINTS
# ============================================

@app.route('/chat/start', methods=['POST'])
def chat_start():
    """
    Create new conversation session.

    Request body:
    {
        "user_id": "user123",
        "persona": "fitness_coach"  (optional)
    }

    Returns:
    {
        "session_id": "session_...",
        "persona": "fitness_coach",
        "available_personas": [...]
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        persona = data.get('persona', 'personal_trainer')

        # Validate persona
        if not PersonaManager.validate_persona(persona):
            return jsonify({
                "error": f"Invalid persona. Available: {PersonaManager.list_personas()}"
            }), 400

        # Create session
        session_id = session_manager.create_session(user_id, persona)

        logger.info(f"Created chat session: {session_id}")

        return jsonify({
            "session_id": session_id,
            "persona": persona,
            "persona_description": PersonaManager.get_persona_description(persona),
            "available_personas": PersonaManager.list_personas()
        }), 200

    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        return jsonify({"error": "Failed to create session"}), 500


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming chat endpoint (SSE).

    Request body:
    {
        "session_id": "session_...",
        "message": "How are you?"
    }

    Response: Server-Sent Events (SSE) stream
    data: {"token": "Great! "}
    data: {"token": "Ready "}
    data: {"token": "to train?"}
    data: {"done": true}
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_message = data.get('message')

        if not session_id or not user_message:
            return jsonify({"error": "Missing session_id or message"}), 400

        if not session_manager.session_exists(session_id):
            return jsonify({"error": "Session not found"}), 404

        # Add user message to history
        session_manager.add_message(session_id, "user", user_message)

        # Get conversation history
        messages = session_manager.get_messages(session_id)

        # Get persona system prompt
        persona = session_manager.get_persona(session_id)
        system_prompt = PersonaManager.get_system_prompt(persona)

        logger.info(f"Streaming chat: session={session_id}, persona={persona}")

        def generate():
            """SSE generator function."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            full_response = ""

            try:
                async def stream_tokens():
                    nonlocal full_response
                    # Get streaming brain
                    if brain_router.brain and brain_router.brain.supports_streaming():
                        async for token in brain_router.brain.stream_chat(
                            messages=messages,
                            system_prompt=system_prompt
                        ):
                            full_response += token
                            yield f"data: {json.dumps({'token': token})}\n\n"
                    else:
                        # Fallback for non-streaming brains
                        response = brain_router.get_coaching_response(
                            {"intensity": "moderate", "volume": 50, "tempo": 20},
                            "intense"
                        )
                        full_response = response
                        yield f"data: {json.dumps({'token': response})}\n\n"

                # Run async generator
                async_gen = stream_tokens()
                while True:
                    try:
                        chunk = loop.run_until_complete(async_gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break

                # Send done signal
                yield f"data: {json.dumps({'done': True})}\n\n"

                # Save assistant response
                session_manager.add_message(session_id, "assistant", full_response)
                logger.info(f"Stream complete: {len(full_response)} chars")

            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                loop.close()

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        logger.error(f"Error in chat stream: {e}", exc_info=True)
        return jsonify({"error": "Streaming failed"}), 500


@app.route('/chat/message', methods=['POST'])
def chat_message():
    """
    Non-streaming chat endpoint (fallback).

    Request body:
    {
        "session_id": "session_...",
        "message": "How are you?"
    }

    Returns:
    {
        "message": "Great! Ready to train?",
        "session_id": "session_...",
        "persona": "fitness_coach"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_message = data.get('message')

        if not session_id or not user_message:
            return jsonify({"error": "Missing session_id or message"}), 400

        if not session_manager.session_exists(session_id):
            return jsonify({"error": "Session not found"}), 404

        # Add user message
        session_manager.add_message(session_id, "user", user_message)

        # Get history and persona
        messages = session_manager.get_messages(session_id)
        persona = session_manager.get_persona(session_id)
        system_prompt = PersonaManager.get_system_prompt(persona)

        # Get response
        if brain_router.brain:
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                brain_router.brain.chat(messages, system_prompt)
            )
            loop.close()
        else:
            # Fallback to config brain
            response = brain_router.get_coaching_response(
                {"intensity": "moderate", "volume": 50, "tempo": 20},
                "intense"
            )

        # Save assistant response
        session_manager.add_message(session_id, "assistant", response)

        logger.info(f"Chat message: session={session_id}, response_len={len(response)}")

        return jsonify({
            "message": response,
            "session_id": session_id,
            "persona": persona
        }), 200

    except Exception as e:
        logger.error(f"Error in chat message: {e}", exc_info=True)
        return jsonify({"error": "Chat failed"}), 500


@app.route('/chat/sessions', methods=['GET'])
def list_sessions():
    """
    List all sessions.

    Query params:
    - user_id: Filter by user (optional)

    Returns:
    {
        "sessions": [...]
    }
    """
    try:
        user_id = request.args.get('user_id')
        sessions = session_manager.list_sessions(user_id)

        return jsonify({"sessions": sessions}), 200

    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        return jsonify({"error": "Failed to list sessions"}), 500


@app.route('/chat/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session."""
    try:
        session_manager.delete_session(session_id)
        return jsonify({"success": True, "session_id": session_id}), 200

    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete session"}), 500


@app.route('/chat/personas', methods=['GET'])
def list_personas():
    """
    List all available personas.

    Returns:
    {
        "personas": [
            {"id": "fitness_coach", "description": "..."},
            ...
        ]
    }
    """
    try:
        personas = []
        for persona_id in PersonaManager.list_personas():
            personas.append({
                "id": persona_id,
                "description": PersonaManager.get_persona_description(persona_id)
            })

        return jsonify({"personas": personas}), 200

    except Exception as e:
        logger.error(f"Error listing personas: {e}", exc_info=True)
        return jsonify({"error": "Failed to list personas"}), 500

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
            language=data.get("language", "en")
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
        language = normalize_language_code(data.get('language', 'en'))
        user_name = data.get('user_name', '').strip()

        logger.info(f"Coach talk: '{user_message}' (context={context}, phase={phase}, persona={persona}, user={user_name or 'anon'})")

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
# WAITLIST + LANDING ANALYTICS
# ============================================

# In-memory waitlist storage (sufficient for pre-launch capture)
_waitlist_emails = []
_waitlist_rate_limit = {}  # ip_hash -> (count, first_request_time)
_VALID_LANDING_EVENTS = {"demo_started", "demo_mic_granted", "demo_coaching_received", "waitlist_signup"}


@app.route('/waitlist', methods=['POST'])
def waitlist_signup():
    """
    Capture landing-page waitlist emails.
    Rate limited to 5 submissions per IP hash per hour.
    """
    import re
    import hashlib

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    language = normalize_language_code(data.get("language", "en"))

    if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({"error": "Invalid email"}), 400

    remote_addr = request.remote_addr or "unknown"
    ip_hash = hashlib.sha256(remote_addr.encode()).hexdigest()[:16]
    now = datetime.now()
    limit_info = _waitlist_rate_limit.get(ip_hash)

    if limit_info:
        count, first_time = limit_info
        elapsed_hours = (now - first_time).total_seconds() / 3600
        if elapsed_hours >= 1:
            _waitlist_rate_limit[ip_hash] = (1, now)
        elif count >= 5:
            return jsonify({"error": "Rate limit exceeded"}), 429
        else:
            _waitlist_rate_limit[ip_hash] = (count + 1, first_time)
    else:
        _waitlist_rate_limit[ip_hash] = (1, now)

    _waitlist_emails.append({
        "email": email,
        "language": language,
        "timestamp": now.isoformat(),
        "ip_hash": ip_hash,
    })

    logger.info(f"Waitlist signup captured: {email} (lang={language})")
    return jsonify({"success": True}), 200


@app.route('/analytics/event', methods=['POST'])
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

    if event not in _VALID_LANDING_EVENTS:
        return jsonify({"error": "Invalid event"}), 400

    logger.info(f"Landing analytics event: {event} | {json.dumps(metadata)}")
    return jsonify({"success": True}), 200


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
