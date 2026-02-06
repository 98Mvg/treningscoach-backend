"""
ElevenLabs TTS Integration for Treningscoach
Fast, cloud-based voice with multilingual support (EN + NO)
Configurable voice IDs per language
"""

import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging
import config

logger = logging.getLogger(__name__)

class ElevenLabsTTS:
    def __init__(self, api_key: str, voice_id: str):
        """
        Initialize ElevenLabs TTS client

        Args:
            api_key: Your ElevenLabs API key (from dashboard)
            voice_id: Default voice ID (fallback if no per-language ID configured)
        """
        self.client = ElevenLabs(api_key=api_key)
        self.default_voice_id = voice_id

        # Cache directory for generated audio
        self.cache_dir = os.path.join(os.path.dirname(__file__), "output", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        logger.info(f"ElevenLabs initialized with default voice ID: {voice_id[:8]}...")

    def get_voice_id(self, language: str = None) -> str:
        """
        Get the appropriate voice ID for the given language.

        Args:
            language: "en" or "no" (None uses default)

        Returns:
            Voice ID string
        """
        if language and language in config.VOICE_CONFIG:
            voice_id = config.VOICE_CONFIG[language].get("voice_id", "")
            if voice_id:
                return voice_id
        return self.default_voice_id

    def generate_audio(
        self,
        text: str,
        output_path: str = None,
        language: str = None,
        voice_pacing: dict = None
    ) -> str:
        """
        Generate speech from text using the appropriate language voice.

        Args:
            text: The text to synthesize
            output_path: Where to save the audio file
            language: "en" or "no" for language-specific voice (optional)
            voice_pacing: Optional pacing settings for emotional progression:
                - stability: 0.0-1.0 (higher = more consistent)
                - speed: Not directly supported, but affects style
                - pause_before/pause_after: Handled by caller

        Returns:
            Path to the generated audio file
        """
        if not output_path:
            import time
            output_path = os.path.join(
                self.cache_dir,
                f"coach_{int(time.time() * 1000)}.mp3"
            )

        # Select voice ID based on language
        voice_id = self.get_voice_id(language)

        # Apply emotional voice settings if provided
        stability = 0.5
        similarity_boost = 0.75
        style = 0.0

        if voice_pacing:
            stability = voice_pacing.get("stability", 0.5)
            # Note: ElevenLabs doesn't have a direct "speed" parameter
            # but lower stability + higher style can create more energetic delivery
            # For Calm Coach (high stability) vs Drill Sergeant (low stability)
            logger.info(f"Emotional pacing: stability={stability}")

        lang_label = f" [{language}]" if language else ""
        logger.info(f"Generating with ElevenLabs{lang_label}: '{text}' (voice: {voice_id[:8]}...)")

        # Generate audio using text_to_speech method
        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",  # Supports Norwegian + English
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=True
            )
        )

        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.info(f"Audio saved: {output_path}")
        return output_path

    def generate_audio_bytes(
        self,
        text: str,
        language: str = None,
        voice_pacing: dict = None
    ) -> bytes:
        """
        Generate speech and return as bytes (no file save).

        This is more efficient for streaming responses.

        Args:
            text: The text to synthesize
            language: "en" or "no" for language-specific voice
            voice_pacing: Optional pacing settings for emotional progression

        Returns:
            Audio bytes (MP3 format)
        """
        voice_id = self.get_voice_id(language)

        # Apply emotional voice settings
        stability = voice_pacing.get("stability", 0.5) if voice_pacing else 0.5

        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Collect all chunks into bytes
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk

        return audio_bytes


# Example usage
if __name__ == "__main__":
    # Test the integration
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        print("Set environment variables:")
        print("   export ELEVENLABS_API_KEY='your_key'")
        print("   export ELEVENLABS_VOICE_ID='your_voice_id'")
    else:
        tts = ElevenLabsTTS(api_key, voice_id)

        # Test English
        audio_file = tts.generate_audio("Perfect! Keep going!", language="en")
        print(f"English: {audio_file}")

        # Test Norwegian
        audio_file = tts.generate_audio("Perfekt! Fortsett!", language="no")
        print(f"Norwegian: {audio_file}")
