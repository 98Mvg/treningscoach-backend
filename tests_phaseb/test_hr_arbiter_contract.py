from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARBITER_FILE = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "HeartRate"
    / "HeartRateArbiter.swift"
)
WORKOUT_VM = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)


def test_arbiter_freshness_windows_match_product_rules() -> None:
    text = ARBITER_FILE.read_text(encoding="utf-8")
    assert "private let liveFreshnessSeconds: TimeInterval = 10.0" in text
    assert "private let hkFreshnessSeconds: TimeInterval = 120.0" in text


def test_arbiter_uses_single_source_priority_wc_ble_hk_none() -> None:
    text = ARBITER_FILE.read_text(encoding="utf-8")
    assert "if wcFresh {" in text
    assert "} else if bleFresh {" in text
    assert "} else if hkFresh {" in text
    assert "selectedSource = .none" in text


def test_arbiter_exposes_watch_and_ble_connectivity_flags() -> None:
    text = ARBITER_FILE.read_text(encoding="utf-8")
    assert "let bleConnected = isProviderConnected(bleState)" in text
    assert "let watchConnected = isProviderConnected(wcState)" in text
    assert "watchStatus: watchStatus(for: selectedSource)" in text
    assert "case .ble:" in text
    assert 'return "ble_connected"' in text


def test_view_model_uses_arbiter_outputs_for_request_payload_inputs() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "let liveHRConnected = hrSource == .wc || hrSource == .ble" in text
    assert "watchConnected: liveHRConnected" in text
    assert "watchStatus: latestWatchStatusForBackend" in text
    assert "if let hr = response.heartRate {" not in text
    assert "if let quality = response.hrQuality {" not in text

