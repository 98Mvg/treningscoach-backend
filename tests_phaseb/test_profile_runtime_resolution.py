import io
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import auth
from database import User, UserProfile, db
from workout_contracts import UserProfilePayload


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
            "phase": kwargs.get("phase") or "intense",
            "elapsed_s": int(kwargs.get("elapsed_seconds") or 0),
            "time_left_s": None,
            "rep_index": 0,
            "reps_total": None,
            "rep_remaining_s": None,
            "reps_remaining_including_current": None,
            "elapsed_source": "server_authoritative",
        },
    }


def _ensure_user(user_id: str) -> None:
    with main.app.app_context():
        existing = User.query.filter_by(id=user_id).first()
        if existing is None:
            user = User(
                id=user_id,
                email=f"{user_id}@example.com",
                display_name=user_id,
                auth_provider="apple",
                auth_provider_id=f"apple_{user_id}",
                language="en",
                training_level="intermediate",
                preferred_persona="personal_trainer",
            )
            db.session.add(user)
            db.session.commit()


def test_resolve_runtime_profile_prefers_newer_snapshot_and_updates_db():
    user_id = "runtime_profile_snapshot_user"
    _ensure_user(user_id)
    with main.app.app_context():
        old_ts = datetime.now(timezone.utc) - timedelta(days=2)
        record = UserProfile.query.filter_by(user_id=user_id).first()
        if record is None:
            record = UserProfile(user_id=user_id)
            db.session.add(record)
        record.max_hr_bpm = 180
        record.resting_hr_bpm = 60
        record.age = 41
        record.profile_updated_at = old_ts
        db.session.commit()

        snapshot = UserProfilePayload(
            age=35,
            max_hr_bpm=190,
            resting_hr_bpm=55,
            profile_updated_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        )
        resolved, source = main._resolve_runtime_profile(user_id=user_id, snapshot_profile=snapshot)
        assert source == "snapshot_newer"
        assert resolved is not None
        assert resolved.max_hr_bpm == 190

        reloaded = UserProfile.query.filter_by(user_id=user_id).first()
        assert reloaded is not None
        assert reloaded.max_hr_bpm == 190
        assert reloaded.resting_hr_bpm == 55
        assert reloaded.age == 35


def test_continuous_uses_db_profile_when_request_fields_missing(monkeypatch, tmp_path):
    user_id = "runtime_profile_continuous_user"
    _ensure_user(user_id)

    with main.app.app_context():
        record = UserProfile.query.filter_by(user_id=user_id).first()
        if record is None:
            record = UserProfile(user_id=user_id)
            db.session.add(record)
        record.max_hr_bpm = 188
        record.resting_hr_bpm = 54
        record.age = 34
        record.profile_updated_at = datetime.now(timezone.utc)
        db.session.commit()

    captured = {}

    def _capturing_zone_tick(**kwargs):
        captured["hr_max"] = kwargs.get("hr_max")
        captured["resting_hr"] = kwargs.get("resting_hr")
        captured["age"] = kwargs.get("age")
        return _zone_tick_stub(**kwargs)

    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _capturing_zone_tick)
    monkeypatch.setattr(main, "_validate_audio_upload_signature", lambda _file: True)
    monkeypatch.setattr(main.config, "PROFILE_DB_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_ENABLED", False, raising=False)

    session_id = main.session_manager.create_session(user_id=user_id, persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False
    token = auth.create_jwt(user_id, f"{user_id}@example.com")

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "42",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "user_profile_id": user_id,
        },
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert captured["hr_max"] == 188
    assert captured["resting_hr"] == 54
    assert captured["age"] == 34


def test_resolve_runtime_profile_does_not_persist_local_personalization_ids():
    local_profile_id = "profile_008ef136-9114-44ed-bd40-52494d445363"

    with main.app.app_context():
        snapshot = UserProfilePayload(
            age=32,
            max_hr_bpm=189,
            resting_hr_bpm=57,
            profile_updated_at=datetime.now(timezone.utc).isoformat(),
        )

        resolved, source = main._resolve_runtime_profile(
            user_id=local_profile_id,
            snapshot_profile=snapshot,
        )

        assert source == "snapshot"
        assert resolved is not None
        assert resolved.max_hr_bpm == 189
        assert UserProfile.query.filter_by(user_id=local_profile_id).first() is None


def test_resolve_runtime_profile_does_not_persist_empty_snapshot_for_real_user():
    user_id = "runtime_profile_empty_user"
    _ensure_user(user_id)

    with main.app.app_context():
        UserProfile.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        snapshot = UserProfilePayload(
            profile_updated_at=datetime.now(timezone.utc).isoformat(),
        )

        resolved, source = main._resolve_runtime_profile(
            user_id=user_id,
            snapshot_profile=snapshot,
        )

        assert source == "defaults"
        assert resolved is None
        assert UserProfile.query.filter_by(user_id=user_id).first() is None


def test_continuous_prefers_authenticated_user_profile_over_local_profile_id(monkeypatch):
    user_id = "runtime_profile_auth_user"
    _ensure_user(user_id)

    with main.app.app_context():
        record = UserProfile.query.filter_by(user_id=user_id).first()
        if record is None:
            record = UserProfile(user_id=user_id)
            db.session.add(record)
        record.max_hr_bpm = 191
        record.resting_hr_bpm = 53
        record.age = 33
        record.profile_updated_at = datetime.now(timezone.utc)
        db.session.commit()

    captured = {}

    def _capturing_zone_tick(**kwargs):
        captured["hr_max"] = kwargs.get("hr_max")
        captured["resting_hr"] = kwargs.get("resting_hr")
        captured["age"] = kwargs.get("age")
        return _zone_tick_stub(**kwargs)

    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _capturing_zone_tick)
    monkeypatch.setattr(main, "_validate_audio_upload_signature", lambda _file: True)
    monkeypatch.setattr(main.config, "PROFILE_DB_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_ENABLED", False, raising=False)

    session_id = main.session_manager.create_session(user_id=user_id, persona="personal_trainer")
    main.session_manager.init_workout_state(session_id, phase="intense")
    state = main.session_manager.get_workout_state(session_id)
    state["is_first_breath"] = False

    token = auth.create_jwt(user_id, f"{user_id}@example.com")
    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": session_id,
            "phase": "intense",
            "elapsed_seconds": "42",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "user_profile_id": "profile_008ef136-9114-44ed-bd40-52494d445363",
        },
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert captured["hr_max"] == 191
    assert captured["resting_hr"] == 53
    assert captured["age"] == 33


def test_missing_continuous_session_bootstraps_from_authenticated_user_not_session_id(monkeypatch):
    auth_user_id = "runtime_session_owner_user"
    forged_user_id = "runtime_session_forged_user"
    _ensure_user(auth_user_id)
    _ensure_user(forged_user_id)

    captured = {}

    def _capturing_zone_tick(**kwargs):
        captured["session_user_id"] = kwargs.get("workout_state", {}).get("user_id")
        return _zone_tick_stub(**kwargs)

    monkeypatch.setattr(main.breath_analyzer, "analyze", _mock_breath_analysis)
    monkeypatch.setattr(main.voice_intelligence, "add_human_variation", lambda text: text)
    monkeypatch.setattr(main, "evaluate_zone_tick", _capturing_zone_tick)
    monkeypatch.setattr(main, "_validate_audio_upload_signature", lambda _file: True)
    monkeypatch.setattr(main.config, "PROFILE_DB_ENABLED", True, raising=False)
    monkeypatch.setattr(main.config, "SERVER_CLOCK_ENABLED", False, raising=False)
    monkeypatch.setattr(
        main.user_memory,
        "get_memory_summary",
        lambda user_id: captured.setdefault("memory_user_id", user_id) or "memory",
    )

    forged_session_id = f"session_{forged_user_id}_{uuid.uuid4().hex}"
    token = auth.create_jwt(auth_user_id, f"{auth_user_id}@example.com")

    client = main.app.test_client()
    response = client.post(
        "/coach/continuous",
        data={
            "audio": (io.BytesIO(b"\0" * 9000), "chunk.wav"),
            "session_id": forged_session_id,
            "phase": "intense",
            "elapsed_seconds": "42",
            "language": "en",
            "persona": "personal_trainer",
            "workout_mode": "easy_run",
            "user_profile_id": f"profile_{forged_user_id}",
        },
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert captured["memory_user_id"] == auth_user_id
    session = main.session_manager.get_session(forged_session_id, refresh=True)
    assert session is not None
    assert session["user_id"] == auth_user_id
    assert session["metadata"]["user_id"] == auth_user_id
