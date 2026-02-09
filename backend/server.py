"""
server.py - FastAPI server with ElevenLabs TTS integration

Full pipeline:
iOS/Web → FastAPI → Claude → ElevenLabs → Audio MP3
"""

import io
import os
import numpy as np
import soundfile as sf
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic

from coach_personality import get_coach_prompt
from session_manager import SessionManager, EmotionalState
from coaching_intelligence import (
    should_coach_speak,
    calculate_next_interval,
    check_safety_override,
    apply_safety_to_coaching
)
from persona_manager import PersonaManager
from voice_intelligence import VoiceIntelligence
from elevenlabs_tts import ElevenLabsTTS
from response_cache import get_cache
import config

# Initialize voice intelligence for emotional pacing
voice_intelligence = VoiceIntelligence()

# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Treningscoach API", version="2.0.0")

# CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize session manager and cache
session_manager = SessionManager()
response_cache = get_cache()

# Initialize ElevenLabs TTS (cloud-based, no local GPU needed)
print("🎤 Initializing ElevenLabs TTS...")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

if not elevenlabs_api_key:
    print("⚠️ WARNING: ELEVENLABS_API_KEY not set - TTS will fail")
    tts = None
else:
    tts = ElevenLabsTTS(
        api_key=elevenlabs_api_key,
        voice_id=elevenlabs_voice_id or "default"
    )
    print(f"✅ ElevenLabs TTS initialized")


# ============================================
# HELPER FUNCTIONS
# ============================================

def analyze_breath(audio_data: bytes) -> dict:
    """
    Analyzes breath audio and returns intensity metrics.

    Returns:
    - silence: How much silence (0-100%)
    - volume: How loud (0-100)
    - tempo: Breaths per minute
    - intensity: "calm", "moderate", "intense", or "critical"
    """
    try:
        # Read audio from bytes
        audio, sample_rate = sf.read(io.BytesIO(audio_data))

        # Calculate duration
        duration = len(audio) / sample_rate

        # Calculate volume (simplified)
        avg_volume = abs(audio).mean()
        max_possible = 1.0  # Normalized audio
        volume_percent = min(100, (avg_volume / max_possible) * 100 * 10)

        # Calculate silence
        silence_threshold = 0.01
        silent_samples = sum(1 for s in audio if abs(s) < silence_threshold)
        silence_percent = (silent_samples / len(audio)) * 100

        # Calculate tempo (simplified - based on volume changes)
        changes = 0
        threshold = 0.05
        for i in range(1, len(audio)):
            if abs(audio[i] - audio[i-1]) > threshold:
                changes += 1

        tempo = min(60, (changes / duration) * 60 / 10)

        # Determine intensity
        if volume_percent < 20 and silence_percent > 50:
            intensity = "calm"
        elif volume_percent < 40 and tempo < 20:
            intensity = "moderate"
        elif volume_percent < 70 and tempo < 35:
            intensity = "intense"
        else:
            intensity = "critical"

        return {
            "silence": round(silence_percent, 1),
            "volume": round(volume_percent, 1),
            "tempo": round(tempo, 1),
            "intensity": intensity,
            "duration": round(duration, 2)
        }

    except Exception as e:
        print(f"❌ Breath analysis error: {e}")
        return {
            "silence": 50.0,
            "volume": 30.0,
            "tempo": 15.0,
            "intensity": "moderate",
            "duration": 2.0
        }


def get_claude_coaching(breath_data: dict, phase: str, mode: str = "realtime_coach") -> str:
    """
    Get coaching text from Claude with endurance coach personality.
    Uses caching to avoid repeated API calls for similar inputs.

    Args:
        breath_data: Breath analysis metrics
        phase: "warmup", "intense", or "cooldown"
        mode: "chat" or "realtime_coach"

    Returns:
        Coaching text
    """
    # Critical override: use config message for speed
    if breath_data["intensity"] == "critical":
        import random
        return random.choice(config.COACH_MESSAGES.get("critical", ["Stop. Breathe slow."]))

    # Check cache first
    cached = response_cache.get(
        intensity=breath_data["intensity"],
        phase=phase,
        tempo=breath_data["tempo"],
        volume=breath_data["volume"],
        mode=mode
    )

    if cached:
        print(f"💾 Cache hit: {breath_data['intensity']}_{phase} (hit #{cached.hit_count})")
        return cached.text

    # Build system prompt with personality
    language = breath_data.get("language", "en")
    system_prompt = get_coach_prompt(mode=mode, language=language)
    system_prompt += f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {breath_data['intensity']}"

    # Build user message
    if mode == "realtime_coach":
        user_message = f"{breath_data['intensity']} breathing, {phase} phase. One action:"
        max_tokens = 30
    else:
        user_message = f"""Breath analysis:
- Intensity: {breath_data['intensity']}
- Volume: {breath_data['volume']}
- Tempo: {breath_data['tempo']} breaths/min
- Phase: {phase}

Give ONE short coaching message (max 7 words):"""
        max_tokens = 50

    try:
        # Call Claude API (Haiku for speed + cost)
        response = claude.messages.create(
            model="claude-3-5-haiku-20241022",  # Haiku: faster + cheaper
            max_tokens=max_tokens,
            temperature=0.9,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        text = response.content[0].text.strip()

        # Truncate to first sentence if needed
        if '.' in text:
            text = text.split('.')[0] + '.'

        # Cache the response
        response_cache.set(
            intensity=breath_data["intensity"],
            phase=phase,
            tempo=breath_data["tempo"],
            volume=breath_data["volume"],
            text=text,
            mode=mode
        )
        print(f"💾 Cached new response: {breath_data['intensity']}_{phase}")

        return text

    except Exception as e:
        print(f"❌ Claude API error: {e}")
        # Fallback to config message
        import random
        if phase == "intense":
            intense_msgs = config.COACH_MESSAGES.get("intense", {})
            return random.choice(intense_msgs.get(breath_data["intensity"], ["Keep going!"]))
        return random.choice(config.COACH_MESSAGES.get(phase, ["Good work!"]))


def synthesize_voice(text: str, voice_pacing: Dict = None, language: str = "en") -> bytes:
    """
    Synthesize speech using ElevenLabs with emotional voice pacing.

    Args:
        text: Coaching text to synthesize
        voice_pacing: Optional dict with stability, speed settings for emotional progression
        language: "en" or "no" for language-specific voice

    Returns:
        Audio bytes (MP3 format)
    """
    if not tts:
        print("❌ TTS not initialized - returning silent audio")
        return create_silent_audio(2.0)

    try:
        # Generate speech with ElevenLabs
        audio_bytes = tts.generate_audio_bytes(
            text=text,
            language=language,
            voice_pacing=voice_pacing
        )

        print(f"✅ Audio synthesized: {len(audio_bytes)} bytes")
        return audio_bytes

    except Exception as e:
        print(f"❌ TTS synthesis error: {e}")
        # Return silent audio as fallback
        return create_silent_audio(2.0)


def create_silent_audio(duration_seconds: float) -> bytes:
    """Create silent audio as fallback (WAV format)."""
    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)
    silent_audio = np.zeros(num_samples, dtype=np.float32)

    buffer = io.BytesIO()
    sf.write(buffer, silent_audio, sample_rate, format="WAV")
    buffer.seek(0)

    return buffer.read()


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "Treningscoach API",
        "tts": "ElevenLabs",
        "brain": "Claude 3.5 Haiku (fast + cheap)",
        "features": ["emotional_progression", "persona_drift", "safety_overrides"]
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    cache_stats = response_cache.get_stats()

    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "welcome": "/welcome",
            "download": "/download/<filename>",
            "coach": "/api/coach",
            "continuous_coach": "/api/continuous-coach",
            "analyze": "/analyze"
        },
        "services": {
            "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
            "elevenlabs_tts": tts is not None,
            "emotional_progression": True
        },
        "personas": PersonaManager.list_personas(),
        "cache": cache_stats
    }


@app.get("/api/cache/stats")
async def cache_stats():
    """Get detailed cache statistics."""
    return response_cache.get_stats()


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear response cache."""
    response_cache.clear()
    return {"status": "cleared", "message": "Cache cleared successfully"}


# ============================================
# WELCOME & DOWNLOAD ENDPOINTS
# ============================================

# In-memory storage for generated audio files (for simplicity)
# In production, consider using cloud storage (S3, GCS, etc.)
import tempfile
import uuid

# Create a temp directory for audio files
AUDIO_DIR = tempfile.mkdtemp(prefix="treningscoach_audio_")
print(f"📁 Audio files directory: {AUDIO_DIR}")


@app.get("/welcome")
async def welcome(language: str = "en"):
    """
    Return welcome message with audio for workout start.

    Called by iOS app when user taps "Start Workout".
    Generates a motivational welcome message with TTS.
    """
    welcome_messages = {
        "en": "Let's go! I'm your coach today. Focus on your breathing and give it everything you've got.",
        "no": "La oss kjøre! Jeg er treneren din i dag. Fokuser på pusten og gi alt du har."
    }

    text = welcome_messages.get(language, welcome_messages["en"])
    print(f"👋 Welcome message requested (language: {language})")

    try:
        # Generate audio with ElevenLabs
        audio_bytes = synthesize_voice(text, language=language)

        # Save to file
        filename = f"welcome_{language}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        print(f"✅ Welcome audio generated: {filename} ({len(audio_bytes)} bytes)")

        return {
            "text": text,
            "audio_url": f"/download/{filename}",
            "language": language
        }

    except Exception as e:
        print(f"❌ Welcome message error: {e}")
        # Return text-only response if TTS fails
        return {
            "text": text,
            "audio_url": None,
            "language": language,
            "error": str(e)
        }


@app.get("/download/{filename}")
async def download_audio(filename: str):
    """
    Download a generated audio file.

    Used by iOS app to fetch coach voice audio.
    """
    # Security: prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(AUDIO_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Determine media type based on extension
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"

    return FileResponse(
        filepath,
        media_type=media_type,
        filename=filename
    )


@app.post("/api/coach")
async def coach(
    audio: UploadFile = File(...),
    phase: str = Form("intense"),
    mode: str = Form("realtime_coach")
):
    """
    Main coaching endpoint.

    Flow:
    1. Receive breath audio from iOS
    2. Analyze breathing intensity
    3. Get coaching text from Claude
    4. Synthesize speech with Qwen3-TTS
    5. Return audio + metadata
    """
    try:
        # Read audio data
        audio_data = await audio.read()

        # 1. Analyze breath
        breath_analysis = analyze_breath(audio_data)
        print(f"📊 Breath analysis: {breath_analysis['intensity']} (phase: {phase})")

        # 2. Get coaching text from Claude
        coach_text = get_claude_coaching(breath_analysis, phase, mode)
        print(f"🗣️ Coach says: '{coach_text}'")

        # 3. Synthesize speech
        audio_bytes = synthesize_voice(coach_text)
        print(f"✅ Audio synthesized: {len(audio_bytes)} bytes")

        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",  # ElevenLabs returns MP3
            headers={
                "X-Coach-Text": coach_text,
                "X-Breath-Intensity": breath_analysis["intensity"],
                "X-Breath-Volume": str(breath_analysis["volume"]),
                "X-Breath-Tempo": str(breath_analysis["tempo"])
            }
        )

    except Exception as e:
        print(f"❌ Coach endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/continuous-coach")
async def continuous_coach(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    phase: str = Form("intense"),
    elapsed_seconds: int = Form(0),
    last_coaching: str = Form(""),
    persona: str = Form("personal_trainer"),
    language: str = Form("en"),
    training_level: str = Form("intermediate")
):
    """
    Continuous coaching endpoint with intelligent frequency and emotional progression.

    Flow:
    1. Analyze breath chunk
    2. Get emotional state from session
    3. Check safety overrides
    4. Decide if coach should speak (using coaching_intelligence)
    5. If yes: Get Claude text with emotional mode + synthesize voice with pacing
    6. Update emotional state
    7. Return audio + metadata + wait_seconds

    Emotional progression:
    - Personas escalate/de-escalate based on accumulated struggle
    - Safety overrides force supportive mode when needed
    - Voice pacing changes with emotional intensity
    """
    try:
        # Read audio data
        audio_data = await audio.read()

        # 1. Analyze breath
        breath_analysis = analyze_breath(audio_data)

        # 2. Get session context with emotional state
        workout_state = session_manager.get_workout_state(session_id)
        if not workout_state:
            # Initialize new session with training level
            session_manager.init_workout_state(
                session_id=session_id,
                phase=phase,
                training_level=training_level
            )
            session_manager.update_workout_state(
                session_id=session_id,
                breath_analysis=breath_analysis,
                coaching_output=None,
                phase=phase,
                elapsed_seconds=elapsed_seconds
            )
            workout_state = session_manager.get_workout_state(session_id)

        coaching_history = workout_state.get("coaching_history", [])
        breath_history = workout_state.get("breath_history", [])
        last_breath = breath_history[-1] if breath_history else None

        # Get emotional state
        emotional_state = session_manager.get_emotional_state(session_id)
        emotional_mode = emotional_state.get_persona_mode()
        emotional_intensity = emotional_state.intensity

        # 3. Check safety overrides (NON-NEGOTIABLE)
        safety_override, safety_reason = check_safety_override(
            breath_analysis=breath_analysis,
            emotional_intensity=emotional_intensity
        )

        if safety_override:
            print(f"⚠️ SAFETY OVERRIDE: {safety_reason} (intensity: {emotional_intensity:.2f})")
            emotional_mode = "supportive"  # Force supportive mode

        # 4. Decide if coach should speak
        should_speak, reason = should_coach_speak(
            current_analysis=breath_analysis,
            last_analysis=last_breath,
            coaching_history=coaching_history,
            phase=phase,
            training_level=training_level
        )

        print(f"📊 Analysis: {breath_analysis['intensity']}, emotional: {emotional_mode} ({emotional_intensity:.2f}), speak: {should_speak}")

        # 5. Generate coaching if needed
        audio_bytes = None
        coach_text = last_coaching or ""

        if should_speak:
            if safety_override:
                # Use safety message instead of Claude
                coach_text = apply_safety_to_coaching(
                    message="",
                    persona=persona,
                    safety_reason=safety_reason,
                    language=language
                )
            else:
                # Get Claude coaching with emotional mode
                coach_text = get_claude_coaching_with_emotion(
                    breath_data=breath_analysis,
                    phase=phase,
                    persona=persona,
                    emotional_mode=emotional_mode,
                    language=language,
                    training_level=training_level
                )

            # Get voice pacing for this persona + emotional mode
            voice_pacing = voice_intelligence.get_voice_pacing(
                persona=persona,
                emotional_mode=emotional_mode,
                message=coach_text
            )

            # Synthesize with emotional pacing and language
            audio_bytes = synthesize_voice(coach_text, voice_pacing, language)
            print(f"🗣️ Coach ({persona}/{emotional_mode}) [{language}]: '{coach_text}'")
        else:
            print(f"🤐 Coach silent: {reason}")

        # 6. Update session state (this also updates emotional state)
        session_manager.update_workout_state(
            session_id=session_id,
            breath_analysis=breath_analysis,
            coaching_output=coach_text if should_speak else None,
            phase=phase,
            elapsed_seconds=elapsed_seconds
        )

        # 7. Calculate next interval
        wait_seconds = calculate_next_interval(
            phase=phase,
            intensity=breath_analysis["intensity"],
            coaching_frequency=len(coaching_history)
        )

        # 8. Return response
        if should_speak and audio_bytes:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/mpeg",  # ElevenLabs returns MP3
                headers={
                    "X-Coach-Text": coach_text,
                    "X-Should-Speak": "true",
                    "X-Reason": reason,
                    "X-Wait-Seconds": str(wait_seconds),
                    "X-Breath-Intensity": breath_analysis["intensity"],
                    "X-Emotional-Mode": emotional_mode,
                    "X-Emotional-Intensity": f"{emotional_intensity:.2f}",
                    "X-Safety-Override": str(safety_override).lower()
                }
            )
        else:
            # Coach silent - return JSON metadata only
            return JSONResponse({
                "should_speak": False,
                "reason": reason,
                "wait_seconds": wait_seconds,
                "breath_analysis": breath_analysis,
                "text": coach_text,
                "emotional_state": {
                    "mode": emotional_mode,
                    "intensity": round(emotional_intensity, 2),
                    "trend": emotional_state.trend
                }
            })

    except Exception as e:
        print(f"❌ Continuous coach error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_claude_coaching_with_emotion(
    breath_data: dict,
    phase: str,
    persona: str,
    emotional_mode: str,
    language: str = "en",
    training_level: str = "intermediate"
) -> str:
    """
    Get coaching text from Claude with persona + emotional mode.

    This is the emotional progression-aware version of get_claude_coaching.
    The persona's expression changes based on emotional_mode.

    Args:
        breath_data: Breath analysis metrics
        phase: "warmup", "intense", or "cooldown"
        persona: The coach persona
        emotional_mode: "supportive", "pressing", "intense", or "peak"
        language: "en" or "no"
        training_level: User's training level

    Returns:
        Coaching text adapted to emotional state
    """
    import random

    # Critical override: use config message for speed
    if breath_data["intensity"] == "critical":
        messages = config.COACH_MESSAGES.get("critical", ["Stop. Breathe slow."])
        if language == "no":
            messages = config.COACH_MESSAGES_NO.get("critical", messages)
        return random.choice(messages)

    # Get system prompt with emotional mode
    system_prompt = PersonaManager.get_system_prompt(
        persona=persona,
        language=language,
        training_level=training_level,
        emotional_mode=emotional_mode,
        safety_override=False
    )

    # Add context
    system_prompt += f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing: {breath_data['intensity']}"

    # Build user message (concise for real-time)
    user_message = f"{breath_data['intensity']} breathing, {phase} phase. One action:"

    try:
        response = claude.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=30,
            temperature=0.9,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        text = response.content[0].text.strip()

        # Truncate to first sentence if needed
        if '.' in text:
            text = text.split('.')[0] + '.'

        # Add human variation
        text = voice_intelligence.add_human_variation(text)

        return text

    except Exception as e:
        print(f"❌ Claude API error: {e}")
        # Fallback to config message
        if phase == "intense":
            intense_msgs = config.COACH_MESSAGES.get("intense", {})
            return random.choice(intense_msgs.get(breath_data["intensity"], ["Keep going!"]))
        return random.choice(config.COACH_MESSAGES.get(phase, ["Good work!"]))


# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("=" * 50)
    print("🎯 Treningscoach Backend v2.0.0")
    print("=" * 50)
    print(f"✅ FastAPI server ready")
    print(f"✅ Claude API configured")
    print(f"✅ ElevenLabs TTS: {'ready' if tts else 'NOT CONFIGURED'}")
    print(f"✅ Emotional progression: enabled")
    print(f"✅ Coach personas: {len(PersonaManager.list_personas())} available")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
