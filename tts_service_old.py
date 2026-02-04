#
#  tts_service.py
#  Local Qwen3-TTS Integration for Voice Cloning
#
#  Runs Qwen3-TTS locally on backend server
#

import os
import logging
from datetime import datetime
from typing import Optional
import torch
import torchaudio
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
REFERENCE_AUDIO_PATH = os.path.join(os.path.dirname(__file__), "voices", "coach_voice.wav")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "output")

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global model instance (loaded once at startup)
_TTS_MODEL = None
_REFERENCE_AUDIO = None


class TTSError(Exception):
    """Custom exception for TTS-related errors"""
    pass


def initialize_tts():
    """
    Initializes Qwen3-TTS model and loads reference audio.
    Call this when Flask app starts.
    """
    global _TTS_MODEL, _REFERENCE_AUDIO

    try:
        logger.info("Initializing Qwen3-TTS...")

        # Check if reference audio exists
        if not os.path.exists(REFERENCE_AUDIO_PATH):
            logger.warning(f"Reference audio not found at {REFERENCE_AUDIO_PATH}")
            logger.warning("TTS will use mock mode until reference audio is provided")
            return

        # Load reference audio using wave module to avoid torchcodec dependency
        logger.info(f"Loading reference audio from {REFERENCE_AUDIO_PATH}")
        import wave
        import numpy as np

        with wave.open(REFERENCE_AUDIO_PATH, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            audio_data = wav_file.readframes(n_frames)

            # Convert to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Convert to torch tensor
            _REFERENCE_AUDIO = torch.from_numpy(audio_np).unsqueeze(0)

        # Resample to 16kHz if needed (Qwen3-TTS expects 16kHz reference audio)
        if sample_rate != 16000:
            logger.info(f"Resampling reference audio from {sample_rate}Hz to 16000Hz")
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            _REFERENCE_AUDIO = resampler(_REFERENCE_AUDIO)

        # Convert stereo to mono if needed
        if _REFERENCE_AUDIO.shape[0] > 1:
            logger.info("Converting reference audio from stereo to mono")
            _REFERENCE_AUDIO = torch.mean(_REFERENCE_AUDIO, dim=0, keepdim=True)

        logger.info(f"Reference audio loaded: shape={_REFERENCE_AUDIO.shape}")

        # Load Qwen3-TTS model
        # NOTE: This assumes you have Qwen3-TTS installed and available
        # You may need to adjust the import and model loading based on the actual Qwen3-TTS API
        try:
            from qwen_tts import QwenTTS  # Placeholder import - adjust based on actual library

            _TTS_MODEL = QwenTTS(
                device="cuda" if torch.cuda.is_available() else "cpu",
                sample_rate=44100  # Output at 44.1kHz for iOS compatibility
            )

            logger.info(f"Qwen3-TTS model loaded on {_TTS_MODEL.device}")
            logger.info("TTS service initialized successfully")

        except ImportError:
            logger.warning("Qwen3-TTS library not found - using mock mode")
            logger.warning("Install with: pip install qwen-tts")
            _TTS_MODEL = None

    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        logger.warning("TTS will use mock mode")
        _TTS_MODEL = None


def synthesize_speech(text: str) -> str:
    """
    Synthesizes speech from text using the cloned voice.

    Args:
        text: The coaching message to synthesize

    Returns:
        Path to generated WAV file (44.1kHz, 16-bit, mono)
    """
    global _TTS_MODEL, _REFERENCE_AUDIO

    # Fallback to mock if model not loaded
    if _TTS_MODEL is None or _REFERENCE_AUDIO is None:
        logger.debug("TTS model not available, using mock")
        return synthesize_speech_mock(text)

    logger.info(f"Synthesizing speech: '{text}'")

    try:
        # Generate speech with voice cloning
        # NOTE: Adjust this based on actual Qwen3-TTS API
        with torch.no_grad():
            audio_output = _TTS_MODEL.synthesize(
                text=text,
                reference_audio=_REFERENCE_AUDIO,
                reference_sample_rate=16000,
                output_sample_rate=44100
            )

        # Save to output folder
        timestamp = datetime.now().timestamp()
        output_path = os.path.join(OUTPUT_FOLDER, f"coach_{timestamp}.wav")

        # Convert tensor to numpy and save using wave module
        import wave
        import struct
        import numpy as np

        audio_np = audio_output.cpu().numpy()
        if audio_np.ndim > 1:
            audio_np = audio_np[0]  # Take first channel if stereo

        # Normalize and convert to 16-bit PCM
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_int16 = (audio_np * 32767).astype(np.int16)

        # Save as WAV (44.1kHz, 16-bit, mono)
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(audio_int16.tobytes())

        logger.info(f"Speech synthesized: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        raise TTSError(f"Speech synthesis failed: {str(e)}")


def synthesize_speech_mock(text: str) -> str:
    """
    Creates a placeholder audio file for testing without real TTS.
    Returns path to silent WAV file.
    """
    import wave
    import struct

    timestamp = datetime.now().timestamp()
    output_path = os.path.join(OUTPUT_FOLDER, f"coach_mock_{timestamp}.wav")

    # Create 2 seconds of silence at 44.1kHz, 16-bit, mono
    duration_seconds = 2.0
    sample_rate = 44100
    num_samples = int(duration_seconds * sample_rate)

    # Create WAV file using wave module (no torchcodec needed)
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write silent samples
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))

    logger.info(f"Created mock audio: {output_path} (text: '{text}')")
    return output_path
