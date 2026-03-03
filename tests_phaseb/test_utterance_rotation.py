from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utterance_rotation import select_rotated_utterance


def test_single_id_always_selected(tmp_path: Path):
    state_path = tmp_path / "rotation_state.json"
    chosen = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="no",
        persona="personal_trainer",
        available_ids=["welcome.standard.1"],
        state_path=state_path,
    )
    assert chosen == "welcome.standard.1"


def test_rotation_avoids_immediate_repeat(tmp_path: Path):
    state_path = tmp_path / "rotation_state.json"
    ids = ["welcome.standard.1", "welcome.standard.2", "welcome.standard.3"]
    now = datetime(2026, 3, 3, 8, 0, tzinfo=timezone.utc)

    first = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="en",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now,
    )
    second = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="en",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now + timedelta(minutes=1),
    )

    assert first != second


def test_recent_k_guard_blocks_last_two(tmp_path: Path):
    state_path = tmp_path / "rotation_state.json"
    ids = ["welcome.standard.1", "welcome.standard.2", "welcome.standard.3"]
    now = datetime(2026, 3, 3, 8, 0, tzinfo=timezone.utc)

    # Seed three picks
    pick1 = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="no",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now,
    )
    pick2 = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="no",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now + timedelta(minutes=1),
    )
    pick3 = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="no",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now + timedelta(minutes=2),
    )

    assert len({pick1, pick2, pick3}) == 3

    # Next pick should avoid previous 2 where possible
    pick4 = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="no",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=now + timedelta(minutes=3),
        recent_k=2,
    )
    assert pick4 not in {pick2, pick3}


def test_avoid_hours_guard_prefers_older_variant(tmp_path: Path):
    state_path = tmp_path / "rotation_state.json"
    ids = ["welcome.standard.1", "welcome.standard.2"]
    start = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)

    first = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="en",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=start,
    )
    second = select_rotated_utterance(
        category_prefix="welcome.standard",
        language="en",
        persona="personal_trainer",
        available_ids=ids,
        state_path=state_path,
        now_utc=start + timedelta(hours=23),
        recent_k=0,
        avoid_hours=24,
    )

    assert first != second
