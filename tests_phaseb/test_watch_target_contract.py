from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PBXPROJ = REPO_ROOT / "TreningsCoach" / "TreningsCoach.xcodeproj" / "project.pbxproj"
WATCH_ROOT = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp"
WATCH_PLIST = WATCH_ROOT / "Info.plist"
WATCH_ENTITLEMENTS = WATCH_ROOT / "TreningsCoachWatchApp.entitlements"


def test_project_contains_watch_target_markers() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "WDTARGET /* TreningsCoachWatchApp */" in text
    assert 'productType = "com.apple.product-type.application";' in text
    assert "WDWATCHAPP /* TreningsCoachWatch.app */" in text


def test_watch_target_contains_healthkit_usage_key_in_build_settings() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "INFOPLIST_KEY_NSHealthShareUsageDescription" in text
    assert "TreningsCoachWatchApp/Info.plist" in text
    assert "INFOPLIST_KEY_NSBluetoothAlwaysUsageDescription" in text


def test_watch_support_files_exist() -> None:
    for required in (
        WATCH_ROOT / "TreningsCoachWatchApp.swift",
        WATCH_ROOT / "WatchRootView.swift",
        WATCH_ROOT / "WatchStartWorkoutView.swift",
        WATCH_ROOT / "WatchWCManager.swift",
        WATCH_ROOT / "WatchWorkoutManager.swift",
        WATCH_ROOT / "WCKeys.swift",
        WATCH_PLIST,
        WATCH_ENTITLEMENTS,
    ):
        assert required.exists(), f"Missing required watch file: {required}"


def test_watch_entitlements_include_healthkit_workout_access() -> None:
    text = WATCH_ENTITLEMENTS.read_text(encoding="utf-8")
    assert "com.apple.developer.healthkit" in text
    assert "com.apple.developer.healthkit.access" in text
    assert "workout" in text


def test_watch_plist_enables_workout_processing_background_mode() -> None:
    text = WATCH_PLIST.read_text(encoding="utf-8")
    assert "WKBackgroundModes" in text
    assert "workout-processing" in text
