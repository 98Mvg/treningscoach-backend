import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import locale_config


def test_voice_config_derives_from_locale_single_source_of_truth():
    for language in locale_config.get_supported_languages():
        assert config.VOICE_CONFIG[language]["voice_id"] == locale_config.get_voice_id(language, "personal_trainer")


def test_persona_voice_config_derives_from_locale_single_source_of_truth():
    for persona in ("personal_trainer", "toxic_mode"):
        for language in locale_config.get_supported_languages():
            expected = locale_config.get_voice_id(language, persona)
            assert config.PERSONA_VOICE_CONFIG[persona]["voice_ids"][language] == expected
