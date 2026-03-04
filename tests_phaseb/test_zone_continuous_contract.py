import io
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def _mock_breath_analysis(_path: str):
    return {
        "intensity": "moderate",
        "tempo": 16.0,
        "volume": 35.0,
        "breath_regularity": 0.55,
        "inhale_exhale_ratio": 0.7,
        "signal_quality": 0.8,
        "respiratory_rate": 16.0,
    }


def _mock_breath_analysis_low_quality(_path: str):
    return {
        "intensity": "moderate",
        "tempo": 16.0,
        "volume": 35.0,
        "breath_regularity": 0.20,
        "inhale_exhale_ratio": 0.7,
        "signal_quality": 0.05,
        "respiratory_rate": 16.0,
    }


def _legacy_evaluate_zone_tick_without_warmup_seconds(
    *,
    workout_state,
    workout_mode,
    phase,
    elapsed_seconds,
    language,
    persona,
    coaching_style,
    interval_template,
    heart_rate,
    hr_quality,
    hr_confidence,
    hr_sample_age_seconds,
    hr_sample_gap_seconds,
    movement_score,
    cadence_spm,
    movement_source,
    watch_connected,
    watch_status,
    hr_max,
    resting_hr,
    age,
    config_module,
    breath_intensity=None,
    breath_signal_quality=None,
    breath_summary=None,
    session_id=None,
    paused=None,
):
    _ = (
        workout_state,
        workout_mode,
        phase,
        elapsed_seconds,
        language,
        persona,
        coaching_style,
        interval_template,
        heart_rate,
        hr_quality,
        hr_confidence,
        hr_sample_age_seconds,
        hr_sample_gap_seconds,
        movement_score,
        cadence_spm,
        movement_source,
        watch_connected,
        watch_status,
        hr_max,
        resting_hr,
        age,
        config_module,
        breath_intensity,
        breath_signal_quality,
        breath_summary,
        session_id,
        paused,
    )
    return {
        "should_speak": False,
        "reason": "zone_no_change",
        "events": [],
        "zone_status": "timing_control",
        "heart_rate": 0,
        "target_zone_label": "Easy",
        "target_hr_low": None,
        "target_hr_high": None,
        "target_source": "none",
        "target_hr_enforced": False,
        "hr_quality": "poor",
    }


def _raising_evaluate_zone_tick(**kwargs):
    _ = kwargs
    raise RuntimeError("forced zone tick failure")


def test_continuous_zone_tick_signature_drift_does_not_500(monkeypatch, tmp_path, caplog):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _legacy_evaluate_zone_tick_without_warmup_seconds)

    session_id = main.session_manager.create_session(user_id="zone_sig_drift_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="warmup")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False

    caplog.set_level("WARNING", logger=main.logger.name)
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "warmup",
            "elapsed_seconds": "42",
            "language": "no",
            "persona": "personal_trainer",
            "workout_mode": "interval",
            "coaching_style": "motivational",
            "interval_template": "4x4",
            "warmup_seconds": "120",
            "heart_rate": "0",
            "watch_connected": "false",
            "watch_status": "disconnected",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["reason"] == "zone_no_change"
    warning_messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "Zone tick compat fallback: dropping unsupported kwargs" not in warning_messages


def test_continuous_internal_exception_returns_failsafe_200(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _raising_evaluate_zone_tick)
    monkeypatch.setattr(main.config, "CONTINUOUS_FAILSAFE_ENABLED", True, raising=False)

    session_id = main.session_manager.create_session(user_id="failsafe_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "42",
            "language": "no",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["reason"] == "continuous_failsafe"
    assert payload["should_speak"] is False
    assert payload["events"] == []
    assert isinstance(payload.get("debug_trace_id"), str)
    assert payload["debug_trace_id"]


def test_continuous_zone_contract_exposes_zone_fields(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_contract_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["workout_mode"] == "easy_run"
    assert payload["coaching_style"] == "normal"
    assert payload["zone_status"] in {"in_zone", "above_zone", "below_zone", "timing_control", "hr_unstable"}
    assert "target_zone_label" in payload
    assert "target_hr_low" in payload
    assert "target_hr_high" in payload
    assert "hr_quality" in payload
    assert "hr_delta_bpm" in payload
    assert "zone_duration_seconds" in payload
    assert "movement_score" in payload
    assert "cadence_spm" in payload
    assert "movement_source" in payload
    assert "movement_state" in payload
    assert "zone_score_confidence" in payload
    assert "zone_overshoots" in payload
    assert "coach_score_v2" in payload
    assert "coach_score_components" in payload
    assert "cap_reason_codes" in payload
    assert "cap_applied" in payload
    assert "cap_applied_reason" in payload
    assert "hr_valid_main_set_seconds" in payload
    assert "zone_valid_main_set_seconds" in payload
    assert "zone_compliance" in payload
    assert "breath_available_reliable" in payload
    assert "decision_owner" in payload
    assert "decision_reason" in payload
    assert "breath_quality_state" in payload


def test_continuous_logs_transcript_and_score_summary(monkeypatch, tmp_path, caplog):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_logs_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    caplog.set_level("INFO", logger=main.logger.name)
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "600",
            "language": "no",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "COACH_TRANSCRIPT" in messages
    assert "lang=no" in messages
    assert "CS_DEBUG_SUMMARY" in messages
    assert "cap_applied=" in messages
    assert "final_cs=" in messages
    assert "DECISION_DEBUG" in messages


def test_zone_mode_owner_remains_zone_event_when_breath_quality_is_poor(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis_low_quality)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_owner_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=10)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["breath_quality_state"] in {"degraded", "unavailable"}


def test_standard_mode_uses_zone_event_owner_when_breath_not_reliable(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis_low_quality)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="phase_fallback_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=5)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "standard",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["decision_reason"] in {
        "main_started",
        "zone_no_change",
        "max_silence_override",
        "hr_signal_lost",
    }


def test_standard_mode_uses_zone_event_owner_when_breath_is_reliable(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="breath_owner_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=5)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded
    state["breath_history"] = [{"signal_quality": 0.8} for _ in range(8)]

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "standard",
            "coaching_style": "normal",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["breath_quality_state"] == "reliable"


def test_standard_mode_emits_max_silence_event_with_zone_owner(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    session_id = main.session_manager.create_session(user_id="override_owner_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded
    state["breath_history"] = [{"signal_quality": 0.8} for _ in range(8)]

    client = main.app.test_client()
    first_response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "300",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "standard",
            "coaching_style": "normal",
            "heart_rate": "150",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
        },
        content_type="multipart/form-data",
    )
    assert first_response.status_code == 200

    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
                "phase": "intense",
                "elapsed_seconds": "370",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "standard",
            "coaching_style": "normal",
            "heart_rate": "151",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert str(payload["decision_reason"]).startswith("max_silence_")
    event_names = [item.get("event_type") for item in payload.get("events", []) if isinstance(item, dict)]
    assert any(str(name).startswith("max_silence_") for name in event_names)
    assert payload.get("zone_primary_event") in event_names
    # Regression guard: max-silence speech must come from canonical events[], not legacy-only fields.
    max_silence_event = next(
        (
            item
            for item in (payload.get("events") or [])
            if isinstance(item, dict) and str(item.get("event_type", "")).startswith("max_silence_")
        ),
        None,
    )
    assert max_silence_event is not None
    assert max_silence_event.get("phrase_id")
    assert isinstance(max_silence_event.get("priority"), int)


def test_zone_owner_v2_does_not_fall_back_to_ai_when_zone_text_missing(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis_low_quality)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(
        main,
        "evaluate_zone_tick",
        lambda **kwargs: {
            "should_speak": True,
            "reason": "zone_hold",
            "coach_text": None,
            "event_type": "hold_zone",
            "zone_status": "in_zone",
            "heart_rate": 144,
            "hr_quality": "good",
            "coaching_style": kwargs.get("coaching_style", "normal"),
        },
    )
    monkeypatch.setattr(
        main,
        "get_coach_response_continuous",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("AI generation should not be called")),
    )

    session_id = main.session_manager.create_session(user_id="zone_no_text_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=8)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "144",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "121.0",
            "movement_source": "cadence",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["brain_source"] == "zone_event_fallback"


def test_zone_mode_emits_max_silence_event_instead_of_event_router_empty(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="zone_silence_guard_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=10)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    client = main.app.test_client()

    # First tick establishes zone-engine speech baseline (main_started).
    first_response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "300",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "150",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )
    assert first_response.status_code == 200

    # Next tick has no zone transition; max silence should now emit canonical event.
    second_response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
                "phase": "intense",
                "elapsed_seconds": "370",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "151",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )
    assert second_response.status_code == 200
    payload = second_response.get_json()
    assert payload["decision_owner"] == "zone_event"
    # Motivation events (priority 55) can fire before max_silence when
    # user is in-zone during easy_run. Both are valid silence breakers.
    _silence_breakers = {"max_silence_override", "easy_run_in_target_sustained"}
    assert payload["decision_reason"] in _silence_breakers
    assert payload["should_speak"] is True
    event_names = [item.get("event_type") for item in payload.get("events", []) if isinstance(item, dict)]
    assert any(e in _silence_breakers for e in event_names)


def test_zone_tick_missing_returns_silent_safe_without_legacy_fallback(monkeypatch, tmp_path, caplog):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", lambda **kwargs: None)

    session_id = main.session_manager.create_session(user_id="zone_tick_missing_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=120)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    caplog.set_level("INFO", logger=main.logger.name)
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "360",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "123.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_owner"] == "zone_event"
    assert payload["decision_reason"] == "zone_tick_missing_silent_safe"
    assert payload["zone_tick_guard_silent_safe"] is True
    assert payload["should_speak"] is False
    assert payload["events"] == []
    assert payload["audio_url"] is None
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "ZONE_GUARD silent-safe: zone_tick missing; legacy fallback disabled" in messages


def test_interval_recovery_uses_short_tick_budget_for_countdowns(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="interval_countdown_tick_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=60)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    # 4x4 template:
    # warmup=600, work=240, rest=180.
    # elapsed=990 -> recovery segment with 30s remaining.
    elapsed = 990

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": str(elapsed),
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "interval",
            "coaching_style": "normal",
            "interval_template": "4x4",
            "heart_rate": "148",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "122.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["workout_mode"] == "interval"
    assert payload.get("remaining_phase_seconds") == 30
    assert payload["wait_seconds"] <= int(getattr(main.config, "INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3))

    event_names = [item.get("event_type") for item in (payload.get("events") or []) if isinstance(item, dict)]
    assert "interval_countdown_30" in event_names


def test_interval_warmup_uses_short_tick_budget_for_countdowns(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="interval_warmup_tick_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="warmup")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=60)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    # 4x4 template warmup=600. elapsed=570 => 30s left in warmup.
    elapsed = 570

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "warmup",
            "elapsed_seconds": str(elapsed),
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "interval",
            "coaching_style": "normal",
            "interval_template": "4x4",
            "heart_rate": "142",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "122.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["workout_mode"] == "interval"
    assert payload.get("phase") == "warmup"
    assert payload.get("remaining_phase_seconds") == 30
    assert payload["wait_seconds"] <= int(getattr(main.config, "INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3))

    event_names = [item.get("event_type") for item in (payload.get("events") or []) if isinstance(item, dict)]
    assert "interval_countdown_30" in event_names


def test_easy_run_warmup_uses_short_tick_budget_for_countdowns(monkeypatch, tmp_path):
    fake_audio = tmp_path / "dummy.mp3"
    fake_audio.write_bytes(b"ID3")

    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)

    session_id = main.session_manager.create_session(user_id="easy_warmup_tick_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="warmup")
    state = main.session_manager.get_workout_state(session_id)
    seeded = (datetime.now() - timedelta(seconds=60)).isoformat()
    state["is_first_breath"] = False
    state["coaching_history"] = [{"timestamp": seeded, "text": "Keep steady."}]
    state["last_coaching_time"] = seeded

    # easy_run warmup configured to 120s. elapsed=90 => 30s left in warmup.
    elapsed = 90

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "warmup",
            "elapsed_seconds": str(elapsed),
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "coaching_style": "normal",
            "warmup_seconds": "120",
            "heart_rate": "138",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "movement_score": "0.62",
            "cadence_spm": "122.0",
            "movement_source": "cadence",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["workout_mode"] == "easy_run"
    assert payload.get("phase") == "warmup"
    assert payload.get("remaining_phase_seconds") == 30
    assert payload["wait_seconds"] <= int(getattr(main.config, "INTERVAL_RECOVERY_FINAL_MAX_WAIT_SECONDS", 3))

    event_names = [item.get("event_type") for item in (payload.get("events") or []) if isinstance(item, dict)]
    assert "interval_countdown_30" in event_names
