import io
import os
import sys

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


def _zone_tick_stub(**kwargs):
    elapsed = int(kwargs.get("elapsed_seconds") or 0)
    phase = kwargs.get("phase") or "intense"
    return {
        "handled": True,
        "should_speak": False,
        "reason": "zone_no_change",
        "events": [],
        "phase_id": 1,
        "sensor_mode": "NO_SENSORS",
        "zone_status": "timing_control",
        "heart_rate": 0,
        "hr_quality": "poor",
        "target_zone_label": "Easy",
        "target_hr_low": None,
        "target_hr_high": None,
        "target_source": None,
        "target_hr_enforced": False,
        "workout_context_summary": {
            "phase": phase,
            "elapsed_s": elapsed,
            "time_left_s": None,
            "rep_index": 0,
            "reps_total": None,
            "rep_remaining_s": None,
            "reps_remaining_including_current": None,
            "elapsed_source": "server_authoritative",
        },
    }


def test_continuous_uses_server_authoritative_elapsed(monkeypatch):
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _zone_tick_stub)

    fake_time = {"mono": 1000.0}

    def _mono_now():
        return fake_time["mono"]

    monkeypatch.setattr(main.time, "monotonic", _mono_now)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_DRIFT_LOG_THRESHOLD_SECONDS", 1, raising=False)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_RESYNC_AHEAD_SECONDS", 10_000, raising=False)

    session_id = main.session_manager.create_session(user_id="clock_user", persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False

    client = main.app.test_client()

    first = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "100",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
        },
        content_type="multipart/form-data",
    )
    assert first.status_code == 200
    first_payload = first.get_json()
    assert first_payload["workout_context_summary"]["elapsed_s"] == 100
    assert first_payload["workout_context_summary"]["elapsed_source"] == "server_authoritative"

    # Client sends wildly wrong elapsed; backend clock should stay canonical.
    fake_time["mono"] = 1005.0
    second = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "999",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
        },
        content_type="multipart/form-data",
    )
    assert second.status_code == 200
    second_payload = second.get_json()
    assert second_payload["workout_context_summary"]["elapsed_s"] == 105
    assert second_payload["workout_context_summary"]["elapsed_source"] == "server_authoritative"
