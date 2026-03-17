import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from session_manager import SessionManager


def test_workout_state_initializes_latency_strategy_defaults():
    manager = SessionManager()
    session_id = manager.create_session(user_id="user1", persona="personal_trainer")

    manager.init_workout_state(session_id, phase="warmup", training_level="intermediate")
    state = manager.get_workout_state(session_id)
    latency = state.get("latency_strategy", {})

    assert latency.get("pending_rich_followup") is False
    assert latency.get("last_fast_fallback_elapsed") == -10_000
    assert latency.get("last_rich_followup_elapsed") == -10_000
    assert latency.get("last_latency_provider") is None


def test_database_backed_session_manager_round_trips_sessions_across_instances():
    with main.app.app_context():
        writer = SessionManager(storage_backend="database")
        session_id = writer.create_session(user_id="db_roundtrip_user", persona="personal_trainer")
        try:
            writer.init_workout_state(session_id, phase="warmup", training_level="intermediate")
            writer.add_message(session_id, "user", "Keep me steady.")
            session = writer.get_session(session_id)
            session.setdefault("metadata", {})["recent_zone_events"] = [
                {"event_type": "in_zone", "text": "Smooth and easy.", "timestamp": "2026-03-18T10:00:00Z"}
            ]
            writer.save_session(session_id, session)
            writer.sessions.clear()

            reader = SessionManager(storage_backend="database")
            assert reader.session_exists(session_id) is True
            assert reader.get_persona(session_id) == "personal_trainer"
            assert reader.get_messages(session_id) == [{"role": "user", "content": "Keep me steady."}]
            workout_state = reader.get_workout_state(session_id)
            assert workout_state is not None
            assert workout_state.get("current_phase") == "warmup"
            reloaded = reader.get_session(session_id, refresh=True)
            assert reloaded["metadata"]["recent_zone_events"][0]["text"] == "Smooth and easy."
        finally:
            writer.delete_session(session_id)
