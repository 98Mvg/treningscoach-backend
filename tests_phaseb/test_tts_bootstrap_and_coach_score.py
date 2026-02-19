import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def _clear_voice_env(monkeypatch):
    keys = [
        "ELEVENLABS_VOICE_ID",
        "ELEVENLABS_VOICE_ID_EN",
        "ELEVENLABS_VOICE_ID_NO",
        "ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN",
        "ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_resolve_default_voice_id_prefers_explicit_env(monkeypatch):
    _clear_voice_env(monkeypatch)
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice_env_primary")

    voice_id, source = main._resolve_default_elevenlabs_voice_id()

    assert voice_id == "voice_env_primary"
    assert source == "ELEVENLABS_VOICE_ID"


def test_resolve_default_voice_id_uses_config_when_env_missing(monkeypatch):
    _clear_voice_env(monkeypatch)
    monkeypatch.setattr(
        main.config,
        "PERSONA_VOICE_CONFIG",
        {
            "personal_trainer": {"voice_ids": {"en": "voice_from_persona_config", "no": ""}},
            "toxic_mode": {"voice_ids": {"en": "", "no": ""}},
        },
        raising=False,
    )
    monkeypatch.setattr(
        main.config,
        "VOICE_CONFIG",
        {"en": {"voice_id": ""}, "no": {"voice_id": ""}},
        raising=False,
    )

    voice_id, source = main._resolve_default_elevenlabs_voice_id()

    assert voice_id == "voice_from_persona_config"
    assert source == "config.PERSONA_VOICE_CONFIG.personal_trainer.en"


def test_coach_score_mapping_covers_localized_inputs():
    assert main._coach_score_from_intensity("calm") == 74
    assert main._coach_score_from_intensity("rolig") == 74
    assert main._coach_score_from_intensity("moderate") == 82
    assert main._coach_score_from_intensity("intense") == 88
    assert main._coach_score_from_intensity("hard") == 88
    assert main._coach_score_from_intensity("critical") == 68
    assert main._coach_score_from_intensity("kritisk") == 68


def test_coach_score_line_is_localized_and_clamped():
    line_no = main._coach_score_line(112, "no")
    line_en = main._coach_score_line(-4, "en")

    assert line_no.startswith("CoachScore: 100")
    assert "Solid jobb" in line_no
    assert line_en.startswith("CoachScore: 0")
    assert "Solid work" in line_en
