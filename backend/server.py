"""
server.py - FastAPI server with Qwen3-TTS integration

Full pipeline:
iOS/Web → FastAPI → Claude → Qwen3-TTS → Audio WAV
"""

import io
import os
import wave
import math
import torch
import soundfile as sf
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic
from qwen_tts import Qwen3TTSModel

from coach_personality import get_coach_prompt
from session_manager import SessionManager
from coaching_intelligence import should_coach_speak, calculate_next_interval
from response_cache import get_cache
import config

# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Treningscoach API", version="1.2.0")

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

# Initialize Qwen3-TTS (loaded once at startup)
print("🎤 Loading Qwen3-TTS model...")
device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map="auto",
    dtype=torch.float16 if device == "cuda" else torch.float32
)
print(f"✅ Qwen3-TTS loaded on {device}")

# Load reference voice ONCE at startup
reference_audio_path = "voices/coach_voice.wav"
if not os.path.exists(reference_audio_path):
    raise FileNotFoundError(f"Reference audio not found: {reference_audio_path}")

reference_audio, sr = sf.read(reference_audio_path)
print(f"✅ Reference audio loaded: {reference_audio_path}")


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
    system_prompt = get_coach_prompt(mode=mode)
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


def synthesize_voice(text: str) -> bytes:
    """
    Synthesize speech using Qwen3-TTS with custom voice.

    Args:
        text: Coaching text to synthesize

    Returns:
        WAV audio bytes
    """
    try:
        # Generate speech with cloned voice
        wavs, sample_rate = model.generate_custom_voice(
            text=text,
            speaker="custom",
            reference_audio=reference_audio
        )

        # Convert to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, wavs[0], sample_rate, format="WAV")
        buffer.seek(0)

        return buffer.read()

    except Exception as e:
        print(f"❌ TTS synthesis error: {e}")
        # Return silent audio as fallback
        return create_silent_wav(2.0)


def create_silent_wav(duration_seconds: float) -> bytes:
    """Create silent WAV audio as fallback."""
    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)
    silent_audio = torch.zeros(num_samples)

    buffer = io.BytesIO()
    sf.write(buffer, silent_audio.numpy(), sample_rate, format="WAV")
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
        "version": "1.2.0",
        "service": "Treningscoach API",
        "tts": "Qwen3-TTS",
        "brain": "Claude 3.5 Haiku (fast + cheap)"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    cache_stats = response_cache.get_stats()

    return {
        "status": "healthy",
        "version": "1.2.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
            "qwen3_tts": True,
            "reference_audio": os.path.exists(reference_audio_path)
        },
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
            media_type="audio/wav",
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
    last_coaching: str = Form("")
):
    """
    Continuous coaching endpoint with intelligent frequency.

    Flow:
    1. Analyze breath chunk
    2. Decide if coach should speak (using coaching_intelligence)
    3. If yes: Get Claude text + synthesize voice
    4. Return audio + metadata + wait_seconds
    """
    try:
        # Read audio data
        audio_data = await audio.read()

        # 1. Analyze breath
        breath_analysis = analyze_breath(audio_data)

        # 2. Get session context
        workout_state = session_manager.get_workout_state(session_id)
        if not workout_state:
            # Initialize new session
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

        # 3. Decide if coach should speak
        should_speak, reason = should_coach_speak(
            current_analysis=breath_analysis,
            last_analysis=last_breath,
            coaching_history=coaching_history,
            phase=phase
        )

        print(f"📊 Analysis: {breath_analysis['intensity']}, should_speak: {should_speak}, reason: {reason}")

        # 4. Generate coaching if needed
        audio_bytes = None
        coach_text = last_coaching or ""

        if should_speak:
            coach_text = get_claude_coaching(breath_analysis, phase, mode="realtime_coach")
            audio_bytes = synthesize_voice(coach_text)
            print(f"🗣️ Coach speaking: '{coach_text}'")
        else:
            print(f"🤐 Coach silent: {reason}")

        # 5. Update session state
        session_manager.update_workout_state(
            session_id=session_id,
            breath_analysis=breath_analysis,
            coaching_output=coach_text if should_speak else None,
            phase=phase,
            elapsed_seconds=elapsed_seconds
        )

        # 6. Calculate next interval
        wait_seconds = calculate_next_interval(
            phase=phase,
            intensity=breath_analysis["intensity"],
            coaching_frequency=len(coaching_history)
        )

        # 7. Return response
        if should_speak and audio_bytes:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/wav",
                headers={
                    "X-Coach-Text": coach_text,
                    "X-Should-Speak": "true",
                    "X-Reason": reason,
                    "X-Wait-Seconds": str(wait_seconds),
                    "X-Breath-Intensity": breath_analysis["intensity"]
                }
            )
        else:
            # Coach silent - return JSON metadata only
            return JSONResponse({
                "should_speak": False,
                "reason": reason,
                "wait_seconds": wait_seconds,
                "breath_analysis": breath_analysis,
                "text": coach_text
            })

    except Exception as e:
        print(f"❌ Continuous coach error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("=" * 50)
    print("🎯 Treningscoach Backend v1.2.0")
    print("=" * 50)
    print(f"✅ FastAPI server ready")
    print(f"✅ Claude API configured")
    print(f"✅ Qwen3-TTS loaded on {device}")
    print(f"✅ Reference audio: {reference_audio_path}")
    print(f"✅ Coach personality: Nordic Endurance Coach")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
