# locale_config.py - Single source of truth for language/voice/locale configuration
#
# Every language in the app is defined HERE. Adding a new language means:
# 1. Add an entry to SUPPORTED_LOCALES below
# 2. Add message banks to config.py (WELCOME_MESSAGES_XX, CONTINUOUS_COACH_MESSAGES_XX, etc.)
# 3. Add L10n entries in iOS L10n.swift
# 4. Set ElevenLabs voice ID env vars on Render
#
# Key design decisions:
# - "no" maps to nb-NO (Bokmål). If Nynorsk needed, add "nn" → nn-NO.
# - tts_language_code is separate from bcp47 (ElevenLabs uses "nb", iOS uses "nb-NO")
# - Voice IDs are per-persona per-locale with env-var overrides + hardcoded fallbacks

import os
from typing import Dict, Optional

SUPPORTED_LOCALES = {
    "en": {
        "bcp47": "en-US",
        "display_name": {"en": "English", "no": "Engelsk", "da": "Engelsk"},
        "tts_language_code": None,  # ElevenLabs auto-detects English well
        "speech_recognition_locale": "en-US",
        "voice_ids": {
            "personal_trainer": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", "1DHhvmhXw9p08Sc79vuJ"),
                "fallback": "nPczCjzI2devNBz1zQrb",
            },
            "toxic_mode": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_TOXIC_EN", "YxsfIjmqZRHBp5erMzLg"),
                "fallback": "nPczCjzI2devNBz1zQrb",
            }
        },
        "tts_model": "eleven_flash_v2_5",
        "tts_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.4},
    },
    "no": {
        "bcp47": "nb-NO",
        "display_name": {"en": "Norwegian", "no": "Norsk", "da": "Norsk"},
        "tts_language_code": "nb",  # Forces Norwegian Bokmål phonology
        "speech_recognition_locale": "nb-NO",
        "voice_ids": {
            "personal_trainer": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", "nhvaqgRyAq6BmFs3WcdX"),
                "fallback": "nhvaqgRyAq6BmFs3WcdX",
            },
            "toxic_mode": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_TOXIC_NO", "nhvaqgRyAq6BmFs3WcdX"),
                "fallback": "nhvaqgRyAq6BmFs3WcdX",
            }
        },
        "tts_model": "eleven_flash_v2_5",
        "tts_settings": {"stability": 0.65, "similarity_boost": 0.85, "style": 0.3},
    },
    "da": {
        "bcp47": "da-DK",
        "display_name": {"en": "Danish", "no": "Dansk", "da": "Dansk"},
        "tts_language_code": "da",  # Forces Danish phonology
        "speech_recognition_locale": "da-DK",
        "voice_ids": {
            "personal_trainer": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_DA", ""),
                "fallback": "nPczCjzI2devNBz1zQrb",
            },
            "toxic_mode": {
                "primary": os.getenv("ELEVENLABS_VOICE_ID_TOXIC_DA", ""),
                "fallback": "nPczCjzI2devNBz1zQrb",
            }
        },
        "tts_model": "eleven_flash_v2_5",
        "tts_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.35},
    }
}


def get_locale(lang_code: str) -> Dict:
    """
    Resolve language code to locale config.

    Args:
        lang_code: "en", "no", or "da"

    Returns:
        Locale config dict

    Raises:
        ValueError if unsupported locale
    """
    if lang_code in SUPPORTED_LOCALES:
        return SUPPORTED_LOCALES[lang_code]
    raise ValueError(f"Unsupported locale: {lang_code}. Use one of: {list(SUPPORTED_LOCALES.keys())}")


def get_voice_id(lang_code: str, persona: str = "personal_trainer") -> str:
    """
    Get the voice ID for a given language + persona.

    Returns primary voice, falls back to fallback, then to default English voice.
    """
    try:
        locale = get_locale(lang_code)
    except ValueError:
        locale = SUPPORTED_LOCALES["en"]

    voice_config = locale.get("voice_ids", {}).get(persona, {})
    primary = voice_config.get("primary", "")
    if primary:
        return primary
    fallback = voice_config.get("fallback", "")
    if fallback:
        return fallback
    # Ultimate fallback: English personal_trainer
    return SUPPORTED_LOCALES["en"]["voice_ids"]["personal_trainer"]["primary"]


def get_tts_language_code(lang_code: str) -> Optional[str]:
    """Get the ElevenLabs language_code for a locale (None for English)."""
    try:
        return get_locale(lang_code).get("tts_language_code")
    except ValueError:
        return None


def get_supported_languages() -> list:
    """List all supported language codes."""
    return list(SUPPORTED_LOCALES.keys())
