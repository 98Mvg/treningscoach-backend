from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
PHONE_WC = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "PhoneWCManager.swift"


def test_start_workout_routes_by_watch_capability_state() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "switch watchCapabilityState {" in text
    assert "case .watchReady, .watchInstalledNotReachable:" in text
    assert "requestWatchStartOrFallback()" in text
    assert "case .watchNotInstalled, .noWatchSupport:" in text
    assert "startContinuousWorkoutInternal()" in text


def test_stop_workout_skips_watch_notify_when_watch_transport_unavailable() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if !phoneWCManager.canUseWatchTransport {" in text
    assert "WATCH_NOTIFY_SKIPPED reason=watch_unavailable" in text
    assert "else if let requestID = activeWatchRequestId ?? pendingWatchRequestId, !requestID.isEmpty {" in text


def test_phone_wc_manager_guards_transport_before_watch_sync_calls() -> None:
    text = PHONE_WC.read_text(encoding="utf-8")
    assert "var canUseWatchTransport: Bool" in text
    assert "guard canUseWatchTransport else {" in text
    assert 'return .failed("watch_unavailable")' in text
    assert "WATCH_NOTIFY_SKIPPED reason=watch_unavailable" in text
