#
#  tts_service.py
#  Local Qwen3-TTS Integration for Voice Cloning
#
#  Runs Qwen3-TTS locally on backend server using qwen_tts library
#

import os
import logging
import wave
import struct
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

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
    Initializes Qwen3-TTS model and loads reference audio.
    Call this when Flask app starts.
    """
    global _TTS_MODEL, _REFERENCE_AUDIO_PATH

    try:
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

            # Determine device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if device == "cuda" else torch.float32

            # Load model using from_pretrained (HuggingFace-style)
            _TTS_MODEL = Qwen3TTSModel.from_pretrained(
                model_name,
                device_map=device,
                torch_dtype=dtype,
                trust_remote_code=True
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


def synthesize_speech(text: str, language: str = "english") -> str:
    """
    Synthesizes speech from text using Qwen3-TTS with custom voice cloning.

    Args:
        text: The coaching message to synthesize
        language: Language for speech synthesis (default: "english")

    Returns:
        Path to generated WAV file (12kHz, 16-bit, mono)
    """
    global _TTS_MODEL, _REFERENCE_AUDIO_PATH

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
        return output_path

    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        logger.warning("Falling back to mock audio")
        return synthesize_speech_mock(text)


def synthesize_speech_mock(text: str) -> str:
    """
    Creates a placeholder audio file for testing without real TTS.
    Returns path to silent WAV file.
    """
    timestamp = datetime.now().timestamp()
    output_path = os.path.join(OUTPUT_FOLDER, f"coach_mock_{timestamp}.wav")

    # Create 2 seconds of silence at 44.1kHz, 16-bit, mono
    duration_seconds = 2.0
    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)

    # Create WAV file using wave module
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write silent samples
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))

    logger.debug(f"Created mock audio: {output_path} (text: '{text}')")
    return output_path
