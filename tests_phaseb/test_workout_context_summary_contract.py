import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import main
from zone_event_motor import evaluate_zone_tick


def _base_tick(**overrides):
    payload = {
        "workout_state": {},
        "workout_mode": "interval",
        "phase": "intense",
        "elapsed_seconds": 0,
        "language": "en",
        "persona": "personal_trainer",
        "coaching_style": "normal",
        "interval_template": "4x4",
        "heart_rate": 145,
        "hr_quality": "good",
        "hr_confidence": 0.9,
        "hr_sample_age_seconds": 0.2,
        "hr_sample_gap_seconds": 1.0,
        "movement_score": 0.6,
        "cadence_spm": 160.0,
        "movement_source": "cadence",
        "watch_connected": True,
        "watch_status": "connected",
        "hr_max": 190,
        "resting_hr": 55,
        "age": 35,
        "config_module": config,
        "breath_intensity": "moderate",
        "breath_signal_quality": 0.8,
        "breath_summary": None,
        "session_id": "summary_test_session",
        "paused": False,
    }
    payload.update(overrides)
    return payload


def test_interval_summary_reports_rep_and_time_left_including_current():
    state = {}
    # Warmup is 600s in 4x4 template; at 1450s we're in rep 3 work.
    tick = evaluate_zone_tick(**_base_tick(workout_state=state, elapsed_seconds=1450))
    summary = tick.get("workout_context_summary") or {}

    assert summary["elapsed_source"] == "server_authoritative"
    assert summary["phase"] in {"work", "recovery", "warmup", "cooldown", "main"}
    assert summary["elapsed_s"] == 1450
    assert summary["reps_total"] == 4
    assert summary["rep_index"] == 3
    assert summary["reps_remaining_including_current"] == 2
    assert isinstance(summary["time_left_s"], int)
    assert summary["time_left_s"] >= 0


def test_easy_run_summary_is_present_without_hr():
    state = {"warmup_remaining_s": 15}
    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="warmup",
            elapsed_seconds=105,
            heart_rate=None,
            hr_quality="poor",
            watch_connected=False,
            watch_status="disconnected",
        )
    )
    summary = tick.get("workout_context_summary") or {}
    assert summary["elapsed_source"] == "server_authoritative"
    assert summary["phase"] == "warmup"
    assert summary["elapsed_s"] == 105
    assert summary["time_left_s"] == 15
    assert summary["reps_total"] is None
    assert summary["rep_index"] == 0
    assert summary["reps_remaining_including_current"] is None


def test_interval_summary_respects_runtime_plan_overrides():
    state = {
        "plan_warmup_s": 120,
        "plan_interval_repeats": 5,
        "plan_interval_work_s": 60,
        "plan_interval_recovery_s": 30,
        "plan_cooldown_s": 120,
    }
    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="interval",
            phase="intense",
            elapsed_seconds=150,
            heart_rate=145,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    summary = tick.get("workout_context_summary") or {}
    assert summary["reps_total"] == 5
    assert summary["rep_index"] == 1
    assert summary["rep_remaining_s"] == 30
    assert summary["reps_remaining_including_current"] == 5


def test_easy_run_timed_summary_uses_plan_time_left():
    state = {
        "plan_warmup_s": 120,
        "plan_main_s": 1800,
        "plan_cooldown_s": 300,
        "plan_free_run": False,
    }
    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="intense",
            elapsed_seconds=300,
            heart_rate=140,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    summary = tick.get("workout_context_summary") or {}
    assert summary["phase"] == "main"
    assert summary["rep_remaining_s"] == 1620
    assert summary["time_left_s"] == 1920


def test_easy_run_free_run_summary_omits_fixed_time_left():
    state = {
        "plan_warmup_s": 0,
        "plan_main_s": 0,
        "plan_cooldown_s": 300,
        "plan_free_run": True,
    }
    tick = evaluate_zone_tick(
        **_base_tick(
            workout_state=state,
            workout_mode="easy_run",
            phase="intense",
            elapsed_seconds=600,
            heart_rate=138,
            hr_quality="good",
            watch_connected=True,
            watch_status="connected",
        )
    )
    summary = tick.get("workout_context_summary") or {}
    assert summary["phase"] == "main"
    assert summary["time_left_s"] is None


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


def test_continuous_response_includes_workout_context_summary(monkeypatch):
    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_ENABLED", False, raising=False)

    session_id = main.session_manager.create_session(user_id="summary_contract_user", persona="personal_trainer")
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
            "elapsed_seconds": "900",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "interval",
            "coaching_style": "normal",
            "interval_template": "4x4",
            "heart_rate": "145",
            "watch_connected": "true",
            "watch_status": "connected",
            "hr_quality": "good",
            "hr_confidence": "0.9",
            "hr_max": "190",
            "resting_hr": "55",
            "age": "35",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    summary = payload.get("workout_context_summary")
    assert isinstance(summary, dict)
    assert summary.get("elapsed_source") == "server_authoritative"
    assert "time_left_s" in summary
    assert "rep_index" in summary
    assert "reps_remaining_including_current" in summary
