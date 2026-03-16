from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BLE_PROVIDER = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "HeartRate"
    / "BLEHeartRateProvider.swift"
)
HR_ARBITER = (
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
CONFIG = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Config.swift"
)


def test_ble_provider_has_scan_timeout_and_backoff_guards() -> None:
    text = BLE_PROVIDER.read_text(encoding="utf-8")
    assert "private let scanTimeoutSeconds: TimeInterval = 12.0" in text
    assert "private let reconnectBaseDelaySeconds: TimeInterval = 1.5" in text
    assert "private let maxReconnectBackoffSeconds: TimeInterval = 12.0" in text
    assert "private var reconnectAttempt = 0" in text
    assert "private func scheduleScanTimeout()" in text
    assert "private func cancelReconnectWorkItem()" in text
    assert "private func cancelScanTimeoutWorkItem()" in text
    assert "self.onStatus?(.degraded)" in text


def test_ble_provider_cleans_up_scan_and_reconnect_state_on_stop() -> None:
    text = BLE_PROVIDER.read_text(encoding="utf-8")
    assert "cancelReconnectWorkItem()" in text
    assert "cancelScanTimeoutWorkItem()" in text
    assert "isScanningForHeartRate = false" in text


def test_arbiter_exposes_deterministic_time_hook_for_edge_case_testing() -> None:
    text = HR_ARBITER.read_text(encoding="utf-8")
    assert "private let nowProvider: () -> Date" in text
    assert "init(nowProvider: @escaping () -> Date = { Date() })" in text
    assert "func evaluateForTesting(at now: Date)" in text
    assert "private func evaluate(reason: String, now overrideNow: Date? = nil)" in text
    assert "let now = overrideNow ?? nowProvider()" in text


def test_workout_view_model_filters_old_hk_startup_snapshots() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    assert "static let hkStartupSnapshotMaxAgeSeconds: TimeInterval = 15.0" in config_text
    assert "HK_STARTUP_SNAPSHOT_ACCEPTED" in text
    assert "HK_STARTUP_SNAPSHOT_IGNORED" in text
    assert "if age <= AppConfig.Health.hkStartupSnapshotMaxAgeSeconds {" in text
