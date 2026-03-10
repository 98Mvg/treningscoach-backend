from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PBXPROJ = REPO_ROOT / "TreningsCoach" / "TreningsCoach.xcodeproj" / "project.pbxproj"
WATCH_ROOT = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp"
WATCH_PLIST = WATCH_ROOT / "Info.plist"
WATCH_ENTITLEMENTS = WATCH_ROOT / "TreningsCoachWatchApp.entitlements"
WATCH_ROOT_VIEW = WATCH_ROOT / "WatchRootView.swift"
WATCH_START_VIEW = WATCH_ROOT / "WatchStartWorkoutView.swift"
WATCH_WORKOUT_MANAGER = WATCH_ROOT / "WatchWorkoutManager.swift"
APP_ICON_SET = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Resources"
    / "Assets.xcassets"
    / "AppIcon.appiconset"
    / "Contents.json"
)


def test_project_contains_watch_target_markers() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "WDTARGET /* TreningsCoachWatchApp */" in text
    assert 'productType = "com.apple.product-type.application";' in text
    assert "WDWATCHAPP /* TreningsCoachWatch.app */" in text


def test_phone_target_embeds_watch_app_and_depends_on_watch_target() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert 'name = "Embed Watch Content";' in text
    assert 'dstPath = "$(CONTENTS_FOLDER_PATH)/Watch";' in text
    assert "TreningsCoachWatch.app in Embed Watch Content" in text
    assert "WD3004 /* PBXTargetDependency */" in text


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


def test_watch_entitlements_include_healthkit_capability() -> None:
    text = WATCH_ENTITLEMENTS.read_text(encoding="utf-8")
    assert "com.apple.developer.healthkit" in text
    assert "com.apple.developer.healthkit.access" not in text


def test_watch_plist_enables_workout_processing_background_mode() -> None:
    text = WATCH_PLIST.read_text(encoding="utf-8")
    assert "WKBackgroundModes" in text
    assert "workout-processing" in text


def test_watch_root_uses_modern_navigation_destination_api() -> None:
    text = WATCH_ROOT_VIEW.read_text(encoding="utf-8")
    assert ".navigationDestination(isPresented: $wcManager.showStartScreen)" in text
    assert "NavigationLink(" not in text
    assert '@StateObject private var wcManager = WatchWCManager.shared' in text
    assert 'Text("Coachi opens from iPhone workout start. If it does not, open the app here and allow workout access if prompted.")' in text


def test_watch_app_installs_application_delegate_for_workout_launches() -> None:
    text = (WATCH_ROOT / "TreningsCoachWatchApp.swift").read_text(encoding="utf-8")
    assert "final class WatchWorkoutLaunchDelegate: NSObject, WKApplicationDelegate" in text
    assert "@WKApplicationDelegateAdaptor(WatchWorkoutLaunchDelegate.self)" in text
    assert "func handle(_ workoutConfiguration: HKWorkoutConfiguration)" in text
    assert "WatchWCManager.shared.primePendingStartFromSystemLaunch(workoutConfiguration: workoutConfiguration)" in text


def test_watch_icon_asset_catalog_includes_watch_roles() -> None:
    text = APP_ICON_SET.read_text(encoding="utf-8")
    assert '"idiom" : "watch"' in text
    assert '"idiom" : "watch-marketing"' in text
    assert '"role" : "notificationCenter"' in text
    assert '"role" : "appLauncher"' in text
    assert '"role" : "quickLook"' in text
    assert '"filename" : "AppIcon-watch-notification-45mm@2x.png"' in text
    assert "ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;" in PBXPROJ.read_text(encoding="utf-8")


def test_watch_start_view_has_running_dashboard_with_bpm_and_time() -> None:
    text = WATCH_START_VIEW.read_text(encoding="utf-8")
    assert "TimelineView(.periodic(from: .now, by: 1))" in text
    assert 'Text(isWaitingForPhoneRequestDetails ? "Syncing with iPhone..." : "Start workout?")' in text
    assert 'Text("BPM")' in text
    assert 'Text("Live Heart Rate")' in text
    assert "sessionPlan: wcManager.pendingSessionPlan" in text
    assert "workoutManager.dashboardTimeLabel(at: date)" in text
    assert "workoutManager.dashboardTimeValue(at: date)" in text
    assert ".disabled(isWaitingForPhoneRequestDetails)" in text


def test_watch_workout_manager_uses_elapsed_for_free_run_and_remaining_for_timed_modes() -> None:
    text = WATCH_WORKOUT_MANAGER.read_text(encoding="utf-8")
    assert 'sessionPlanSnapshot?.isFreeRun == true ? "Elapsed" : "Time Remaining"' in text
    assert "if sessionPlanSnapshot?.isFreeRun == true" in text
    assert "return \"--:--\"" in text
