from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_hr_source_and_wc_freshness_state_exists() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "enum HRSource: String" in text
    assert "case wc = \"wc\"" in text
    assert "case hk = \"hk\"" in text
    assert "case none = \"none\"" in text
    assert "@Published private(set) var hrSource: HRSource = .none" in text
    assert "private var lastWCHRSampleAt: Date?" in text
    assert "private let wcFreshnessThresholdSeconds: TimeInterval = 10.0" in text


def test_hk_updates_are_ignored_while_wc_is_fresh() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if let lastWCSampleAt = lastWCHRSampleAt," in text
    assert "Date().timeIntervalSince(lastWCSampleAt) < wcFreshnessThresholdSeconds" in text
    assert "// WC remains primary while fresh to prevent source conflicts." in text


def test_wc_stall_demotes_to_hk_or_none_until_wc_resumes() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func refreshWCLiveness()" in text
    assert "if age <= wcFreshnessThresholdSeconds" in text
    assert "if let latest = latestHeartRateSampleDate, latest > lastSampleAt" in text
    assert "hrSource = .hk" in text
    assert "hrSource = .none" in text
    assert "watchConnected = false" in text


def test_wc_updates_promote_source_to_wc() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func handleWCHRUpdate(bpm: Double, timestamp: TimeInterval)" in text
    assert "lastWCHRSampleAt = sampleDate" in text
    assert "hrSource = .wc" in text
    assert "hrSignalQuality = \"good\"" in text
