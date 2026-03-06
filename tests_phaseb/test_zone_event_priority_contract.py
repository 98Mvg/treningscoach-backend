from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_ios_event_router_prefers_backend_primary_event() -> None:
    content = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func selectEventToSpeak(from response: ContinuousCoachResponse)" in content
    assert "response.zonePrimaryEvent" in content
    assert '"backend_primary"' in content
    assert '"backend_order"' in content
    assert '"local_priority_fallback"' in content
