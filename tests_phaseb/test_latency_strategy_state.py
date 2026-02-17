import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
