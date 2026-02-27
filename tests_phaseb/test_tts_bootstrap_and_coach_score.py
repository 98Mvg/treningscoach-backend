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


def test_resolve_default_voice_id_uses_locale_when_env_missing(monkeypatch):
    _clear_voice_env(monkeypatch)
    monkeypatch.setattr(
        main,
        "locale_voice_id",
        lambda lang, persona="personal_trainer": (
            "voice_from_locale_personal_en"
            if (lang == "en" and persona == "personal_trainer")
            else ("voice_from_locale_personal_no" if (lang == "no" and persona == "personal_trainer") else "")
        ),
        raising=False,
    )

    voice_id, source = main._resolve_default_elevenlabs_voice_id()

    assert voice_id == "voice_from_locale_personal_en"
    assert source == "locale_config.personal_trainer.en"


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

    assert line_no.startswith("Coach score: 100")
    assert "Solid jobb" in line_no
    assert line_en.startswith("Coach score: 0")
    assert "Solid work" in line_en


def test_layered_coach_score_allows_high_score_with_breath_plus_duration_when_hr_missing():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=7200,
        breath_data={
            "intensity": "intense",
            "signal_quality": 0.95,
            "breath_regularity": 0.90,
            "intensity_confidence": 0.90,
        },
        zone_tick={
            "heart_rate": None,
            "hr_quality": "poor",
            "main_set_seconds": 7200,
            "hr_valid_main_set_seconds": 0,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
        },
        watch_connected=False,
        heart_rate=None,
        hr_quality="poor",
        breath_enabled_by_user=True,
        mic_permission_granted=True,
        breath_quality_samples=[0.8, 0.9, 0.9, 0.88, 0.87, 0.9],
    )

    assert payload["raw_score"] >= 90
    assert payload["cap_applied"] == 100
    assert payload["score"] >= 90
    assert payload["hr_zone_compliance_ok"] is False


def test_layered_coach_score_records_breath_missing_without_blocking_hr_plus_duration():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=3600,
        breath_data={
            "intensity": "intense",
            "signal_quality": 0.30,
            "breath_regularity": 0.95,
            "intensity_confidence": 0.95,
        },
        zone_tick={
            "heart_rate": 156,
            "hr_quality": "good",
            "main_set_seconds": 3600,
            "hr_valid_main_set_seconds": 3500,
            "zone_valid_main_set_seconds": 3400,
            "target_enforced_main_set_seconds": 3400,
            "zone_compliance": 0.82,
        },
        watch_connected=True,
        heart_rate=156,
        hr_quality="good",
        breath_enabled_by_user=True,
        mic_permission_granted=True,
        breath_quality_samples=[0.2, 0.25, 0.3, 0.21, 0.24],
    )

    assert payload["raw_score"] >= 70
    assert payload["cap_applied"] == 100
    assert payload["cap_applied_reason"] == "BREATH_MISSING"
    assert payload["score"] >= 70
    assert payload["breath_quality_ok"] is True


def test_layered_coach_score_allows_100_without_breath_when_hr_is_strong():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=7200,
        breath_data={
            "intensity": "moderate",
            "signal_quality": 0.05,
            "breath_regularity": 0.05,
            "intensity_confidence": 0.05,
        },
        zone_tick={
            "heart_rate": 154,
            "hr_quality": "good",
            "main_set_seconds": 7200,
            "hr_valid_main_set_seconds": 7000,
            "zone_valid_main_set_seconds": 6900,
            "target_enforced_main_set_seconds": 6900,
            "zone_compliance": 0.82,
        },
        watch_connected=True,
        heart_rate=154,
        hr_quality="good",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )

    assert payload["cap_applied"] == 100
    assert payload["score"] >= 95
    assert payload["hr_zone_compliance_ok"] is True
    assert payload["breath_in_play"] is False


def test_layered_coach_score_hard_clamps_under_20_minutes_proportionally():
    payload = main._compute_layered_coach_score(
        language="no",
        elapsed_seconds=600,
        breath_data={
            "intensity": "intense",
            "signal_quality": 0.95,
            "breath_regularity": 0.92,
            "intensity_confidence": 0.90,
        },
        zone_tick={
            "heart_rate": 155,
            "hr_quality": "good",
            "main_set_seconds": 600,
            "hr_valid_main_set_seconds": 600,
            "zone_valid_main_set_seconds": 600,
            "target_enforced_main_set_seconds": 600,
            "zone_compliance": 0.86,
        },
        watch_connected=True,
        heart_rate=155,
        hr_quality="good",
        breath_enabled_by_user=True,
        mic_permission_granted=True,
        breath_quality_samples=[0.8, 0.9, 0.85, 0.9, 0.87, 0.88],
    )

    assert payload["raw_score"] > 10
    assert payload["cap_applied"] == 10
    assert payload["cap_applied_reason"] == "SHORT_DURATION"
    assert payload["score"] == 10


def test_zone_score_formula_uses_070_softness_explicitly():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=2400,
        breath_data={"signal_quality": 0.8, "breath_regularity": 0.8, "intensity_confidence": 0.8},
        zone_tick={
            "heart_rate": 150,
            "hr_quality": "good",
            "main_set_seconds": 2400,
            "hr_valid_main_set_seconds": 2200,
            "zone_valid_main_set_seconds": 2200,
            "target_enforced_main_set_seconds": 2200,
            "zone_compliance": 0.56,
        },
        watch_connected=True,
        heart_rate=150,
        hr_quality="good",
        breath_enabled_by_user=True,
        mic_permission_granted=True,
        breath_quality_samples=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    )

    assert payload["zone_score"] == 80


def test_denominator_split_keeps_hr_present_when_targets_unenforced():
    payload = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=2400,
        breath_data={"signal_quality": 0.9, "breath_regularity": 0.9, "intensity_confidence": 0.9},
        zone_tick={
            "heart_rate": 152,
            "hr_quality": "good",
            "main_set_seconds": 2400,
            "hr_valid_main_set_seconds": 2000,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
            "zone_compliance": None,
        },
        watch_connected=True,
        heart_rate=152,
        hr_quality="good",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )

    assert "HR_MISSING" not in payload["cap_reason_codes"]
    assert "ZONE_MISSING_OR_UNENFORCED" in payload["cap_reason_codes"]
    assert "DURATION_ONLY_CAP" in payload["cap_reason_codes"]
    assert payload["cap_applied_reason"] == "DURATION_ONLY_CAP"


def test_duration_only_cap_guardrail_reaches_40_60_100_thresholds():
    payload_40 = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=2400,
        breath_data={"signal_quality": 0.2, "breath_regularity": 0.2, "intensity_confidence": 0.2},
        zone_tick={
            "heart_rate": None,
            "hr_quality": "poor",
            "main_set_seconds": 2400,
            "hr_valid_main_set_seconds": 0,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
        },
        watch_connected=False,
        heart_rate=None,
        hr_quality="poor",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )
    payload_60 = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=3600,
        breath_data={"signal_quality": 0.2, "breath_regularity": 0.2, "intensity_confidence": 0.2},
        zone_tick={
            "heart_rate": None,
            "hr_quality": "poor",
            "main_set_seconds": 3600,
            "hr_valid_main_set_seconds": 0,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
        },
        watch_connected=False,
        heart_rate=None,
        hr_quality="poor",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )
    payload_120 = main._compute_layered_coach_score(
        language="en",
        elapsed_seconds=7200,
        breath_data={"signal_quality": 0.2, "breath_regularity": 0.2, "intensity_confidence": 0.2},
        zone_tick={
            "heart_rate": None,
            "hr_quality": "poor",
            "main_set_seconds": 7200,
            "hr_valid_main_set_seconds": 0,
            "zone_valid_main_set_seconds": 0,
            "target_enforced_main_set_seconds": 0,
        },
        watch_connected=False,
        heart_rate=None,
        hr_quality="poor",
        breath_enabled_by_user=False,
        mic_permission_granted=False,
        breath_quality_samples=[],
    )

    assert payload_40["cap_applied"] == 40
    assert payload_40["cap_applied_reason"] == "DURATION_ONLY_CAP"
    assert payload_60["cap_applied"] == 60
    assert payload_120["cap_applied"] == 100
