from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
ARBiter = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "HeartRate" / "HeartRateArbiter.swift"
PROVIDER = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "HeartRate" / "HeartRateProvider.swift"


def test_provider_contract_defines_sources_and_quality() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    assert "enum HRSource: String" in text
    assert "case wc" in text
    assert "case ble" in text
    assert "case hk" in text
    assert "case none" in text
    assert "enum HRQuality: String" in text
    assert "protocol HeartRateProvider: AnyObject" in text


def test_arbiter_has_freshness_windows_and_priority_order() -> None:
    text = ARBiter.read_text(encoding="utf-8")
    assert "private let liveFreshnessSeconds: TimeInterval = 10.0" in text
    assert "private let hkFreshnessSeconds: TimeInterval = 120.0" in text
    assert "if wcFresh {" in text
    assert "} else if bleFresh {" in text
    assert "} else if hkFresh {" in text
    assert "selectedSource = .none" in text


def test_arbiter_tracks_wc_ble_hk_sample_timestamps() -> None:
    text = ARBiter.read_text(encoding="utf-8")
    assert "private(set) var lastWCHRSampleAt: Date?" in text
    assert "private(set) var lastBLEHRSampleAt: Date?" in text
    assert "private(set) var lastHKSampleAt: Date?" in text
    assert "case .wc:" in text
    assert "case .ble:" in text
    assert "case .hk:" in text


def test_workout_view_model_uses_arbiter_as_single_hr_output_path() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private let heartRateArbiter = HeartRateArbiter()" in text
    assert "heartRateArbiter.onOutput = { [weak self] output in" in text
    assert "self.heartRate = output.currentBPM" in text
    assert "self.hrSource = output.hrSource" in text
    assert "self.hrSignalQuality = output.hrSignalQuality.rawValue" in text
    assert "private func handleWCHRUpdate(bpm: Double, timestamp: TimeInterval)" in text
    assert "watchHRProvider.ingestHeartRate(bpm: bpm, timestamp: timestamp)" in text


def test_workout_view_model_marshals_hr_pipeline_updates_to_main_actor() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "watchHRProvider.onSample = { [weak self] sample in\n            Task { @MainActor [weak self] in" in text
    assert "bleHeartRateProvider.onStatus = { [weak self] status in\n            Task { @MainActor [weak self] in" in text
    assert "hkFallbackProvider.onStatus = { [weak self] status in\n            Task { @MainActor [weak self] in" in text
    assert "heartRateArbiter.onOutput = { [weak self] output in\n            Task { @MainActor [weak self] in" in text


def test_watch_hr_startup_grace_is_explicit_and_clears_on_first_live_sample() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var watchHRStartupGraceDeadline: Date?" in text
    assert "private func beginWatchHRStartupGrace(reason: String)" in text
    assert "private func clearWatchHRStartupGrace(reason: String)" in text
    assert "private func resolvedWatchStatusForBackend(now: Date = Date()) -> String" in text
    assert 'return "watch_starting"' in text
    assert 'clearWatchHRStartupGrace(reason: "first_live_watch_hr")' in text
