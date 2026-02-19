"""
ElevenLabs TTS Integration for Coachi
Fast, cloud-based voice with multilingual support (EN + NO + DA)
Configurable voice IDs per language and persona

Model: eleven_flash_v2_5 (proper Norwegian support, 75ms latency, 0.5 credits/char)
Note: eleven_multilingual_v2 does NOT support Norwegian properly (sounds Danish)
"""

import os
import hashlib
import json
import shutil
import time
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
        self._cache_hits = 0
        self._cache_misses = 0
        self._writes_since_cleanup = 0

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
        # Start with defaults
        voice_id = self.get_voice_id(language)
        stability = 0.5
        similarity_boost = 0.75
        style = 0.0
        speed = 1.0

        # Apply persona-specific voice settings
        if persona and persona in config.PERSONA_VOICE_CONFIG:
            persona_config = config.PERSONA_VOICE_CONFIG[persona]
            # Use persona voice ID for the requested language, fallback to "en"
            voice_ids = persona_config.get("voice_ids", {})
            persona_voice = voice_ids.get(language) or voice_ids.get("en")
            if persona_voice:
                voice_id = persona_voice
            stability = persona_config.get("stability", stability)
            similarity_boost = persona_config.get("similarity_boost", similarity_boost)
            style = persona_config.get("style", style)
            speed = persona_config.get("speed", speed)
            logger.info(f"Persona '{persona}': stability={stability}, similarity={similarity_boost}, style={style}, speed={speed}")

        # Manual pacing overrides persona defaults
        if voice_pacing:
            stability = voice_pacing.get("stability", stability)
            similarity_boost = voice_pacing.get("similarity_boost", similarity_boost)
            style = voice_pacing.get("style", style)
            speed = voice_pacing.get("speed", speed)
            logger.info(f"Voice pacing override: stability={stability}, similarity={similarity_boost}, style={style}, speed={speed}")

        stability = max(0.0, min(1.0, float(stability)))
        similarity_boost = max(0.0, min(1.0, float(similarity_boost)))
        style = max(0.0, min(1.0, float(style)))
        speed = max(0.7, min(1.2, float(speed)))

        lang_label = f" [{language}]" if language else ""
        persona_label = f" ({persona})" if persona else ""
        language_code = LANGUAGE_CODES.get(language) if language else None

        cache_enabled = bool(getattr(config, "TTS_AUDIO_CACHE_ENABLED", False))
        cache_read_enabled = bool(getattr(config, "TTS_AUDIO_CACHE_READ_ENABLED", True))
        cache_write_enabled = bool(getattr(config, "TTS_AUDIO_CACHE_WRITE_ENABLED", True))
        cache_version = str(getattr(config, "TTS_AUDIO_CACHE_VERSION", "v1") or "v1")

        cache_path = None
        if cache_enabled and (cache_read_enabled or cache_write_enabled):
            cache_path = self._cache_path_for_request(
                text=text,
                language=language,
                persona=persona,
                voice_id=voice_id,
                language_code=language_code,
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                speed=speed,
                cache_version=cache_version,
            )

        if cache_enabled and cache_read_enabled and cache_path and os.path.exists(cache_path):
            self._cache_hits += 1
            logger.info("TTS cache hit [%s%s] path=%s", language or "auto", persona_label, os.path.basename(cache_path))
            if output_path and os.path.abspath(output_path) != os.path.abspath(cache_path):
                shutil.copyfile(cache_path, output_path)
                return output_path
            return cache_path
        elif cache_enabled and cache_read_enabled and cache_path:
            self._cache_misses += 1

        if not output_path:
            if cache_enabled and cache_write_enabled and cache_path:
                output_path = cache_path
            else:
                output_path = os.path.join(
                    self.cache_dir,
                    f"coach_{int(time.time() * 1000)}.mp3"
                )

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
                speed=speed,
                use_speaker_boost=True
            )
        )
        if language_code:
            convert_kwargs["language_code"] = language_code

        # Generate audio using text_to_speech method
        try:
            audio = self.client.text_to_speech.convert(**convert_kwargs)
        except Exception as e:
            status_code = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
            logger.error(
                "ElevenLabs convert failed (lang=%s persona=%s voice=%s status=%s model=%s): %s",
                language or "auto",
                persona or "none",
                (voice_id[:8] + "...") if voice_id else "missing",
                status_code,
                TTS_MODEL,
                e,
                exc_info=True,
            )
            raise

        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        if (
            cache_enabled
            and cache_write_enabled
            and cache_path
            and os.path.abspath(output_path) != os.path.abspath(cache_path)
        ):
            shutil.copyfile(output_path, cache_path)
        if cache_enabled and cache_write_enabled:
            self._maybe_cleanup_cache()

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
        similarity_boost = 0.75
        style = 0.0
        speed = 1.0

        # Apply persona-specific settings
        if persona and persona in config.PERSONA_VOICE_CONFIG:
            persona_config = config.PERSONA_VOICE_CONFIG[persona]
            voice_ids = persona_config.get("voice_ids", {})
            persona_voice = voice_ids.get(language) or voice_ids.get("en")
            if persona_voice:
                voice_id = persona_voice
            stability = persona_config.get("stability", stability)
            similarity_boost = persona_config.get("similarity_boost", similarity_boost)
            style = persona_config.get("style", style)
            speed = persona_config.get("speed", speed)

        # Manual pacing overrides
        if voice_pacing:
            stability = voice_pacing.get("stability", stability)
            similarity_boost = voice_pacing.get("similarity_boost", similarity_boost)
            style = voice_pacing.get("style", style)
            speed = voice_pacing.get("speed", speed)

        stability = max(0.0, min(1.0, float(stability)))
        similarity_boost = max(0.0, min(1.0, float(similarity_boost)))
        style = max(0.0, min(1.0, float(style)))
        speed = max(0.7, min(1.2, float(speed)))

        language_code = LANGUAGE_CODES.get(language) if language else None

        # Build API kwargs — language_code is optional, only add when set
        convert_kwargs = dict(
            voice_id=voice_id,
            text=text,
            model_id=TTS_MODEL,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                speed=speed,
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

    def _cache_path_for_request(
        self,
        text: str,
        language: str,
        persona: str,
        voice_id: str,
        language_code: str,
        stability: float,
        similarity_boost: float,
        style: float,
        speed: float,
        cache_version: str,
    ) -> str:
        payload = {
            "cache_version": cache_version,
            "model": TTS_MODEL,
            "text": (text or "").strip(),
            "language": language or "",
            "persona": persona or "",
            "voice_id": voice_id or "",
            "language_code": language_code or "",
            "stability": round(float(stability), 4),
            "similarity_boost": round(float(similarity_boost), 4),
            "style": round(float(style), 4),
            "speed": round(float(speed), 4),
        }
        cache_key = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"tts_{cache_key}.mp3")

    def _cache_files(self):
        files = []
        if not os.path.isdir(self.cache_dir):
            return files
        for name in os.listdir(self.cache_dir):
            if not (name.startswith("tts_") and name.endswith(".mp3")):
                continue
            path = os.path.join(self.cache_dir, name)
            if os.path.isfile(path):
                files.append(path)
        return files

    def _maybe_cleanup_cache(self):
        interval = max(1, int(getattr(config, "TTS_AUDIO_CACHE_CLEANUP_INTERVAL_WRITES", 25)))
        self._writes_since_cleanup += 1
        if self._writes_since_cleanup < interval:
            return
        self._writes_since_cleanup = 0
        self.cleanup_cache()

    def cleanup_cache(self):
        files = self._cache_files()
        if not files:
            return 0

        now = time.time()
        max_age = max(0, int(getattr(config, "TTS_AUDIO_CACHE_MAX_AGE_SECONDS", 14 * 24 * 3600)))
        max_files = max(1, int(getattr(config, "TTS_AUDIO_CACHE_MAX_FILES", 1000)))

        removed = 0
        if max_age > 0:
            for path in files:
                try:
                    if (now - os.path.getmtime(path)) > max_age:
                        os.remove(path)
                        removed += 1
                except OSError:
                    continue

        remaining = self._cache_files()
        if len(remaining) > max_files:
            remaining.sort(key=lambda p: os.path.getmtime(p))
            for path in remaining[: len(remaining) - max_files]:
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    continue

        if removed:
            logger.info("TTS cache cleanup removed %s file(s)", removed)
        return removed

    def get_cache_stats(self):
        files = self._cache_files()
        total_bytes = 0
        for path in files:
            try:
                total_bytes += os.path.getsize(path)
            except OSError:
                continue

        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_lookups) if total_lookups else 0.0
        return {
            "enabled": bool(getattr(config, "TTS_AUDIO_CACHE_ENABLED", False)),
            "files": len(files),
            "total_bytes": total_bytes,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate, 3),
            "version": str(getattr(config, "TTS_AUDIO_CACHE_VERSION", "v1") or "v1"),
            "max_files": int(getattr(config, "TTS_AUDIO_CACHE_MAX_FILES", 1000)),
            "max_age_seconds": int(getattr(config, "TTS_AUDIO_CACHE_MAX_AGE_SECONDS", 14 * 24 * 3600)),
        }


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
