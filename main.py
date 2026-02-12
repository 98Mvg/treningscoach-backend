# main.py - MAIN FILE FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify, Response, stream_with_context, render_template
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
from datetime import datetime
import config  # Import central configuration
from brain_router import BrainRouter  # Import Brain Router
from session_manager import SessionManager  # Import Session Manager
from persona_manager import PersonaManager  # Import Persona Manager
from coaching_intelligence import should_coach_speak, calculate_next_interval  # Import coaching intelligence
from user_memory import UserMemory  # STEP 5: Import user memory
from voice_intelligence import VoiceIntelligence  # STEP 6: Import voice intelligence
from tts_service import synthesize_speech_mock  # Import mock TTS (Qwen disabled)
from elevenlabs_tts import ElevenLabsTTS  # Import ElevenLabs TTS
from strategic_brain import get_strategic_brain  # Import Strategic Brain for high-level coaching
from coach_personality import get_coach_prompt, ENDURANCE_COACH_PERSONALITY  # Import coach personality
from database import init_db  # Import database initialization
from breath_analyzer import BreathAnalyzer  # Import advanced breath analysis
from auth_routes import auth_bp  # Import auth blueprint

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
strategic_brain = get_strategic_brain()  # Initialize Strategic Brain (Claude-powered)
logger.info(f"Initialized with brain: {brain_router.get_active_brain()}")
if strategic_brain.is_available():
    logger.info("✅ Strategic Brain (Claude) is available")
else:
    logger.info("⚠️ Strategic Brain disabled (no ANTHROPIC_API_KEY)")

# Initialize TTS service (ElevenLabs for production)
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

if elevenlabs_api_key and elevenlabs_voice_id:
    logger.info("🎙️ Initializing ElevenLabs TTS...")
    elevenlabs_tts = ElevenLabsTTS(api_key=elevenlabs_api_key, voice_id=elevenlabs_voice_id)
    USE_ELEVENLABS = True
    logger.info("✅ ElevenLabs TTS ready")
else:
    logger.warning("⚠️ ElevenLabs credentials not found, using mock TTS")
    USE_ELEVENLABS = False
logger.info("TTS service initialized")

# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def generate_voice(text, language=None, persona=None):
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
        if USE_ELEVENLABS:
            # Use ElevenLabs with persona-specific voice settings
            result = elevenlabs_tts.generate_audio(text, language=language, persona=persona)
            print(f"[TTS] OK lang={language} persona={persona} file={os.path.basename(result)}")
            return result
        else:
            # Fallback to mock (Qwen disabled)
            print(f"[TTS] MOCK (ElevenLabs disabled) lang={language}")
            return synthesize_speech_mock(text)
    except Exception as e:
        logger.error(f"TTS failed, using mock: {e}")
        print(f"[TTS] FAILED lang={language} persona={persona} error={type(e).__name__}: {e}")
        # Fallback to mock for development/testing
        return synthesize_speech_mock(text)

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """Homepage - Workout UI with player controls"""
    return render_template('index.html')

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
        language = request.args.get('language', 'en')
        persona = request.args.get('persona', 'personal_trainer')

        # Select message category based on experience
        if experience == 'beginner':
            message_category = 'beginner_friendly'
        elif experience in ['breath_aware', 'advanced']:
            message_category = 'breath_aware'
        else:
            message_category = 'standard'

        # Get random welcome message from config (language-aware)
        if language == "no":
            welcome_bank = getattr(config, 'WELCOME_MESSAGES_NO', config.WELCOME_MESSAGES)
        else:
            welcome_bank = config.WELCOME_MESSAGES
        messages = welcome_bank.get(message_category, welcome_bank.get('standard', ["Welcome."]))
        welcome_text = random.choice(messages)

        logger.info(f"Welcome message requested: experience={experience}, language={language}, message='{welcome_text}'")

        # Generate or use cached audio (language + persona-aware voice)
        voice_file = generate_voice(welcome_text, language=language, persona=persona)

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
        voice_file = generate_voice(coach_text, persona=persona)

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
        if 'audio' not in request.files:
            logger.warning("Continuous coach request missing audio file")
            return jsonify({"error": "No audio file received"}), 400

        audio_file = request.files['audio']
        session_id = request.form.get('session_id')
        phase = request.form.get('phase', 'intense')
        last_coaching = request.form.get('last_coaching', '')
        elapsed_seconds = int(request.form.get('elapsed_seconds', 0))
        language = request.form.get('language', 'en')
        training_level = request.form.get('training_level', 'intermediate')
        persona = request.form.get('persona', 'personal_trainer')
        workout_mode = request.form.get('workout_mode', config.DEFAULT_WORKOUT_MODE)

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

        logger.info(f"Continuous coaching tick: session={session_id}, phase={phase}, mode={workout_mode}, elapsed={elapsed_seconds}s, lang={language}, level={training_level}, persona={persona}")

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
                "metadata": {"workout_mode": workout_mode}
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

            return jsonify({
                "text": "",
                "should_speak": False,
                "breath_analysis": breath_data,
                "audio_url": None,
                "wait_seconds": wait_seconds,
                "phase": phase,
                "workout_mode": workout_mode,
                "reason": "audio_too_small"
            })

        # Analyze breath
        breath_data = breath_analyzer.analyze(filepath)

        # Get coaching context and workout state
        coaching_context = session_manager.get_coaching_context(session_id)
        last_breath = session_manager.get_last_breath_analysis(session_id)
        workout_state = session_manager.get_workout_state(session_id)
        if workout_state is not None:
            workout_state["workout_mode"] = workout_mode

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
                elapsed_seconds=elapsed_seconds
            )

            if should_be_silent:
                # Cap silence so coach doesn't disappear
                max_silence = getattr(config, "MAX_SILENCE_SECONDS", 60)
                min_quality = getattr(config, "MIN_SIGNAL_QUALITY_TO_FORCE", 0.2)
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
                    training_level=training_level
                )

            logger.info(f"Coaching decision: should_speak={speak_decision}, reason={reason}")

        # STEP 4: Check if we should use pattern-based insight (hybrid mode)
        pattern_insight = None
        last_pattern_time = workout_state.get("last_pattern_time") if workout_state else None

        if brain_router.use_hybrid and brain_router.should_use_pattern_insight(elapsed_seconds, last_pattern_time):
            pattern_insight = brain_router.detect_pattern(
                breath_history=coaching_context["breath_history"],
                coaching_history=coaching_context["coaching_history"],
                phase=phase
            )

            if pattern_insight:
                logger.info(f"Pattern detected: {pattern_insight}")
                # Update last pattern time
                if workout_state:
                    workout_state["last_pattern_time"] = elapsed_seconds

        # Strategic Brain: High-level coaching guidance (every 2-3 minutes)
        strategic_guidance = None
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
                # Update last strategic time
                if workout_state:
                    workout_state["last_strategic_time"] = elapsed_seconds

        # Get coaching message (priority: strategic > pattern > config)
        use_welcome = workout_state.get("use_welcome_phrase", False)
        if use_welcome:
            # Use a specific cached phrase for instant welcome
            coach_text = "Perfect."  # This phrase is cached (from pregenerate list)
            workout_state["use_welcome_phrase"] = False  # Clear flag
            logger.info(f"Using cached welcome phrase: {coach_text}")
        elif strategic_guidance and speak_decision:
            # Strategic Brain guidance (highest priority for strategic moments)
            # System decides: use suggested phrase or pick from config based on guidance
            if "suggested_phrase" in strategic_guidance and strategic_guidance["suggested_phrase"]:
                coach_text = strategic_guidance["suggested_phrase"]
                logger.info(f"🧠 Using Strategic Brain phrase: {coach_text}")
            else:
                # Use config phrase that matches strategic intent
                coach_text = get_coach_response_continuous(breath_data, phase, language=language, persona=persona)
                logger.info(f"🧠 Strategic guidance applied, using config phrase: {coach_text}")
        elif pattern_insight and speak_decision:
            coach_text = pattern_insight  # STEP 4: Use Claude's pattern insight
            logger.info(f"Using pattern insight instead of config message")
        else:
            coach_text = get_coach_response_continuous(breath_data, phase, language=language, persona=persona)

        # STEP 6: Add human variation to avoid robotic repetition (skip for welcome)
        if speak_decision and not use_welcome:
            coach_text = voice_intelligence.add_human_variation(coach_text)

        # Generate voice only if should speak (language-aware)
        audio_url = None
        if speak_decision:
            voice_file = generate_voice(coach_text, language=language, persona=persona)
            # Convert absolute path to relative path from OUTPUT_FOLDER
            relative_path = os.path.relpath(voice_file, OUTPUT_FOLDER)
            audio_url = f"/download/{relative_path}"

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
            user_memory.mark_safety_event(user_id)
            logger.info(f"Memory: marked critical breathing event for user {user_id}")

        # Clean up temp file
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        # Response
        response_data = {
            "text": coach_text,
            "should_speak": speak_decision,
            "breath_analysis": breath_data,
            "audio_url": audio_url,
            "wait_seconds": wait_seconds,
            "phase": phase,
            "workout_mode": workout_mode,
            "reason": reason  # For debugging
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in continuous coaching endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def get_coach_response_continuous(breath_data, phase, language="en", persona=None):
    """
    STEP 3: Get coaching message using REALTIME_COACH brain mode.

    Uses BrainRouter with mode="realtime_coach" for fast, actionable cues.
    Falls back to config messages if brain is disabled.
    Supports language and persona selection.
    """
    # STEP 3: Use realtime_coach brain mode (not chat mode)
    return brain_router.get_coaching_response(
        breath_data=breath_data,
        phase=phase,
        mode="realtime_coach",  # Product-defining: fast, actionable, no explanations
        language=language,
        persona=persona
    )


@app.route('/download/<path:filename>')
def download(filename):
    """Download generated voice file"""
    try:
        # Security: Prevent directory traversal (but allow cache/ subdirectory)
        if '..' in filename:
            logger.warning(f"Attempted directory traversal: {filename}")
            return jsonify({"error": "Invalid filename"}), 400

        # Support both direct files and cache/ subdirectory
        filepath = os.path.join(OUTPUT_FOLDER, filename)

        if os.path.exists(filepath):
            logger.info(f"Serving file: {filename}")
            # Determine mimetype based on file extension
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
        from auth import optional_auth
        from database import db, WorkoutHistory

        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        # Try to get user from auth token (optional)
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from auth import decode_jwt
                token = auth_header.split("Bearer ")[1]
                payload = decode_jwt(token)
                user_id = payload.get("user_id")
            except:
                pass

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
    - limit: Max number of records (default: 20)
    """
    try:
        from database import WorkoutHistory

        # Try to get user from auth token
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from auth import decode_jwt
                token = auth_header.split("Bearer ")[1]
                payload = decode_jwt(token)
                user_id = payload.get("user_id")
            except:
                pass

        limit = int(request.args.get("limit", 20))

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
        intensity = data.get('intensity', 'moderate')
        persona = data.get('persona', 'personal_trainer')
        language = data.get('language', 'en')

        logger.info(f"Coach talk: '{user_message}' (context={context}, phase={phase}, persona={persona})")

        # Build system prompt based on context
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
            )
            if language == "no":
                system_prompt += "\n- RESPOND IN NORWEGIAN."
            max_tokens = 60

        # Use strategic brain (Claude Haiku for cost efficiency)
        coach_text = None
        if strategic_brain.is_available():
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

        # Generate voice audio with persona-specific voice
        voice_file = generate_voice(coach_text, language=language, persona=persona)
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
