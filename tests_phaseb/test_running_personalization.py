import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from running_personalization import RunningPersonalizationStore


def test_record_session_builds_recovery_baseline_and_tip(tmp_path):
    store_path = tmp_path / "personalization.json"
    store = RunningPersonalizationStore(storage_path=str(store_path), max_recovery_samples=10, max_session_history=10)

    first = store.record_session(
        user_id="runner_1",
        language="en",
        score=82,
        time_in_target_pct=76.0,
        overshoots=2,
        recovery_avg_seconds=34.0,
    )
    second = store.record_session(
        user_id="runner_1",
        language="en",
        score=86,
        time_in_target_pct=84.0,
        overshoots=1,
        recovery_avg_seconds=28.0,
    )

    assert first["profile"]["sessions_completed"] == 1
    assert second["profile"]["sessions_completed"] == 2
    assert second["profile"]["recovery_baseline_seconds"] == 31.0
    assert isinstance(second["next_time_tip"], str)
    assert second["next_time_tip"] != ""


def test_high_overshoots_sets_conservative_aggressiveness(tmp_path):
    store_path = tmp_path / "personalization.json"
    store = RunningPersonalizationStore(storage_path=str(store_path))

    for overshoots in (4, 3, 5):
        store.record_session(
            user_id="runner_2",
            language="no",
            score=70,
            time_in_target_pct=62.0,
            overshoots=overshoots,
            recovery_avg_seconds=38.0,
        )

    profile = store.get_profile("runner_2")
    assert profile["aggressiveness"] == "conservative"
    assert profile["sessions_completed"] == 3


def test_empty_user_id_returns_default_without_writing(tmp_path):
    store_path = tmp_path / "personalization.json"
    store = RunningPersonalizationStore(storage_path=str(store_path))
    result = store.record_session(
        user_id="",
        language="en",
        score=80,
        time_in_target_pct=75.0,
        overshoots=2,
        recovery_avg_seconds=30.0,
    )

    assert result["profile"]["sessions_completed"] == 0
    assert result["next_time_tip"] == ""
