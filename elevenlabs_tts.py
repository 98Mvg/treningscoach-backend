"""
ElevenLabs TTS Integration for Coachi
Fast, cloud-based voice with multilingual support (EN + NO + DA)
Configurable voice IDs per language and persona

Model: eleven_flash_v2_5 (proper Norwegian support, 75ms latency, 0.5 credits/char)
Note: eleven_multilingual_v2 does NOT support Norwegian properly (sounds Danish)
"""

import os
import hashlib
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging
import config

logger = logging.getLogger(__name__)

# TTS model selection — flash_v2_5 is fastest + cheapest + supports Norwegian
TTS_MODEL = "eleven_flash_v2_5"

# Language codes for ElevenLabs (helps with short/ambiguous text)
# ElevenLabs uses ISO 639-1 codes for language_code parameter
# See: https://elevenlabs.io/docs/api-reference/text-to-speech
LANGUAGE_CODES = {
    "en": None,     # Auto-detect works well for English
    "no": "no",     # Norwegian — ISO 639-1 (NOT "nor" which returns 400)
    "da": "da",     # Danish — ISO 639-1
}

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
        persona: str = None,
        voice_pacing: dict = None
    ) -> str:
        """
        Generate speech from text using the appropriate voice.

        Voice selection priority:
        1. Persona-specific voice (from PERSONA_VOICE_CONFIG)
        2. Language-specific voice (from VOICE_CONFIG)
        3. Default voice ID

        Args:
            text: The text to synthesize
            output_path: Where to save the audio file
            language: "en" or "no" for language-specific voice (optional)
            persona: Persona identifier for persona-specific voice/settings (optional)
            voice_pacing: Optional pacing settings override (overrides persona defaults)

        Returns:
            Path to the generated audio file
        """
        if not output_path:
            import time
            output_path = os.path.join(
                self.cache_dir,
                f"coach_{int(time.time() * 1000)}.mp3"
            )

        # Start with defaults
        voice_id = self.get_voice_id(language)
        stability = 0.5
        similarity_boost = 0.75
        style = 0.0

        # Apply persona-specific voice settings
        if persona and persona in config.PERSONA_VOICE_CONFIG:
            persona_config = config.PERSONA_VOICE_CONFIG[persona]
            # Use persona voice ID for the requested language, fallback to "en"
            voice_ids = persona_config.get("voice_ids", {})
            persona_voice = voice_ids.get(language) or voice_ids.get("en")
            if persona_voice:
                voice_id = persona_voice
            stability = persona_config.get("stability", stability)
            style = persona_config.get("style", style)
            logger.info(f"Persona '{persona}': stability={stability}, style={style}")

        # Manual pacing overrides persona defaults
        if voice_pacing:
            stability = voice_pacing.get("stability", stability)
            style = voice_pacing.get("style", style)
            logger.info(f"Voice pacing override: stability={stability}, style={style}")

        lang_label = f" [{language}]" if language else ""
        persona_label = f" ({persona})" if persona else ""
        language_code = LANGUAGE_CODES.get(language) if language else None
        logger.info(f"Generating with ElevenLabs{lang_label}{persona_label}: '{text}' (voice: {voice_id[:8]}..., model: {TTS_MODEL}, lang_code: {language_code})")

        # Build API kwargs — language_code is optional, only add when set
        convert_kwargs = dict(
            voice_id=voice_id,
            text=text,
            model_id=TTS_MODEL,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=True
            )
        )
        if language_code:
            convert_kwargs["language_code"] = language_code

        # Generate audio using text_to_speech method
        audio = self.client.text_to_speech.convert(**convert_kwargs)

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
        persona: str = None,
        voice_pacing: dict = None
    ) -> bytes:
        """
        Generate speech and return as bytes (no file save).

        This is more efficient for streaming responses.

        Args:
            text: The text to synthesize
            language: "en" or "no" for language-specific voice
            persona: Persona identifier for persona-specific voice/settings
            voice_pacing: Optional pacing settings override

        Returns:
            Audio bytes (MP3 format)
        """
        voice_id = self.get_voice_id(language)
        stability = 0.5
        style = 0.0

        # Apply persona-specific settings
        if persona and persona in config.PERSONA_VOICE_CONFIG:
            persona_config = config.PERSONA_VOICE_CONFIG[persona]
            voice_ids = persona_config.get("voice_ids", {})
            persona_voice = voice_ids.get(language) or voice_ids.get("en")
            if persona_voice:
                voice_id = persona_voice
            stability = persona_config.get("stability", stability)
            style = persona_config.get("style", style)

        # Manual pacing overrides
        if voice_pacing:
            stability = voice_pacing.get("stability", stability)
            style = voice_pacing.get("style", style)

        language_code = LANGUAGE_CODES.get(language) if language else None

        # Build API kwargs — language_code is optional, only add when set
        convert_kwargs = dict(
            voice_id=voice_id,
            text=text,
            model_id=TTS_MODEL,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=0.75,
                style=style,
                use_speaker_boost=True
            )
        )
        if language_code:
            convert_kwargs["language_code"] = language_code

        audio = self.client.text_to_speech.convert(**convert_kwargs)

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
