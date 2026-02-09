#
#  tts_service.py
#  TTS Utilities (Qwen3 disabled; ElevenLabs preferred)
#
#  Local Qwen3-TTS is disabled by default due to CPU slowness.
#  This module now defaults to mock audio unless re-enabled.
#

import os
import logging
import math
import wave
import struct
import hashlib
import shutil
from datetime import datetime
from typing import Optional
from pathlib import Path
import config

logger = logging.getLogger(__name__)
ENABLE_QWEN_TTS = getattr(config, "ENABLE_QWEN_TTS", False)

# Cache directory for pre-generated phrases
CACHE_DIR = os.path.join(os.path.dirname(__file__), "output", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Configuration
REFERENCE_AUDIO_PATH = os.path.join(os.path.dirname(__file__), "voices", "coach_voice.wav")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "output")

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global model instance (loaded once at startup)
_TTS_MODEL = None
_REFERENCE_AUDIO_PATH = None


class TTSError(Exception):
    """Custom exception for TTS-related errors"""
    pass


def initialize_tts():
    """
    Initializes Qwen3-TTS model and loads reference audio (if enabled).
    Call this when Flask app starts.
    """
    global _TTS_MODEL, _REFERENCE_AUDIO_PATH

    try:
        if not ENABLE_QWEN_TTS:
            logger.info("Qwen3-TTS disabled; skipping local model initialization")
            _TTS_MODEL = None
            _REFERENCE_AUDIO_PATH = None
            return

        logger.info("Initializing Qwen3-TTS...")

        # Check if reference audio exists
        if not os.path.exists(REFERENCE_AUDIO_PATH):
            logger.warning(f"Reference audio not found at {REFERENCE_AUDIO_PATH}")
            logger.warning("TTS will use mock mode until reference audio is provided")
            return

        logger.info(f"Reference audio found: {REFERENCE_AUDIO_PATH}")
        _REFERENCE_AUDIO_PATH = REFERENCE_AUDIO_PATH

        # Try to load Qwen3-TTS model using qwen_tts library
        try:
            from qwen_tts import Qwen3TTSModel
            import torch

            model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

            logger.info(f"Loading Qwen3-TTS model from {model_name}...")

            # Determine device (use CPU for stability on limited RAM)
            # Note: MPS would require 7+ GB VRAM, so we use CPU with optimizations
            device = "cpu"
            dtype = torch.float32
            logger.info("💻 Using CPU (optimized for stability)")

            # Load model using from_pretrained (HuggingFace-style)
            # Use low_cpu_mem_usage to reduce peak memory consumption
            _TTS_MODEL = Qwen3TTSModel.from_pretrained(
                model_name,
                device_map=device,
                torch_dtype=dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            logger.info(f"✅ Qwen3-TTS model loaded on {device}")
            logger.info("✅ TTS service initialized successfully with voice cloning")

            # Log supported languages
            try:
                languages = _TTS_MODEL.model.get_supported_languages()
                logger.info(f"Supported languages: {languages}")
            except:
                logger.debug("Could not retrieve supported languages")

        except ImportError as e:
            logger.warning(f"Qwen3-TTS library not available: {e}")
            logger.warning("TTS will use mock mode")
            logger.warning("Install with: pip install qwen-tts torch soundfile")
            _TTS_MODEL = None
        except Exception as e:
            logger.error(f"Failed to load Qwen3-TTS model: {e}")
            logger.warning("TTS will use mock mode")
            _TTS_MODEL = None

    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        logger.warning("TTS will use mock mode")
        _TTS_MODEL = None


def get_cached_audio(text: str) -> Optional[str]:
    """Check if audio for this text is already cached."""
    text_hash = hashlib.md5(text.lower().strip().encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"cached_{text_hash}.wav")

    if os.path.exists(cache_path):
        logger.info(f"✅ Using cached audio for: '{text}'")
        return cache_path

    return None


def cache_audio(text: str, audio_path: str) -> str:
    """Copy generated audio to cache for future instant use."""
    text_hash = hashlib.md5(text.lower().strip().encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"cached_{text_hash}.wav")

    shutil.copy(audio_path, cache_path)
    logger.info(f"💾 Cached audio for future use: '{text}'")
    return cache_path


def synthesize_speech(text: str, language: str = "english") -> str:
    """
    Synthesizes speech from text using Qwen3-TTS with custom voice cloning (if enabled).
    Uses cached audio if available for instant playback!

    Args:
        text: The coaching message to synthesize
        language: Language for speech synthesis (default: "english")

    Returns:
        Path to generated WAV file (12kHz, 16-bit, mono)
    """
    global _TTS_MODEL, _REFERENCE_AUDIO_PATH

    if not ENABLE_QWEN_TTS:
        logger.debug("Qwen3-TTS disabled, using mock audio")
        return synthesize_speech_mock(text)

    # Check cache first for instant response!
    cached = get_cached_audio(text)
    if cached:
        return cached

    # Fallback to mock if model not loaded
    if _TTS_MODEL is None or _REFERENCE_AUDIO_PATH is None:
        logger.debug("TTS model not available, using mock")
        return synthesize_speech_mock(text)

    logger.info(f"Synthesizing speech with voice cloning: '{text}' (language: {language})")

    try:
        import soundfile as sf

        # Generate speech using custom voice from reference audio
        # speaker parameter is required - use one from the model's supported speakers
        # Available: serena, vivian, uncle_fu, ryan, aiden, ono_anna, sohee, eric, dylan
        wavs, sample_rate = _TTS_MODEL.generate_custom_voice(
            text=text,
            ref_audio=_REFERENCE_AUDIO_PATH,  # Path to your 20s voice sample
            speaker="ryan",  # Base speaker to clone from (male voice)
            language=language,  # "english", "chinese", etc.
            ref_text=None,  # Optional: transcript of reference audio
        )

        # Save to output folder
        timestamp = datetime.now().timestamp()
        output_path = os.path.join(OUTPUT_FOLDER, f"coach_{timestamp}.wav")

        # wavs is a list of numpy arrays, take the first one
        audio_data = wavs[0]

        # Save using soundfile
        sf.write(output_path, audio_data, sample_rate)

        logger.info(f"✅ Speech synthesized: {output_path} ({sample_rate}Hz, {len(audio_data)/sample_rate:.2f}s)")

        # Cache for future instant use
        cache_audio(text, output_path)

        return output_path

    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        logger.warning("Falling back to mock audio")
        return synthesize_speech_mock(text)


def synthesize_speech_mock(text: str) -> str:
    """
    Creates a placeholder audio file for testing without real TTS.
    Generates a short audible beep so you can confirm audio playback works.
    """
    timestamp = datetime.now().timestamp()
    output_path = os.path.join(OUTPUT_FOLDER, f"coach_mock_{timestamp}.wav")

    sample_rate = 44100
    # Two short beeps: beep-pause-beep (confirms audio pipeline is working)
    beep_duration = 0.15  # seconds per beep
    pause_duration = 0.1
    frequency = 880  # Hz (A5 note, clearly audible but not harsh)
    amplitude = 8000  # ~25% volume (gentle, not startling)

    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        # First beep
        for i in range(int(beep_duration * sample_rate)):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', sample))

        # Pause
        for _ in range(int(pause_duration * sample_rate)):
            wav_file.writeframes(struct.pack('<h', 0))

        # Second beep
        for i in range(int(beep_duration * sample_rate)):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', sample))

    logger.warning(f"⚠️ Using MOCK audio (beep) for: '{text}' - configure TTS for real voice")
    return output_path
