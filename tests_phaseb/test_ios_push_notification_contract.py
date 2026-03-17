from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "TreningsCoachApp.swift"
APP_VIEW_MODEL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "AppViewModel.swift"
ONBOARDING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "OnboardingContainerView.swift"
)
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_app_bootstraps_push_runtime_with_app_delegate() -> None:
    text = APP.read_text(encoding="utf-8")
    assert "final class CoachiAppDelegate: NSObject, UIApplicationDelegate" in text
    assert "@UIApplicationDelegateAdaptor(CoachiAppDelegate.self) private var appDelegate" in text
    assert "PushNotificationManager.shared.configure()" in text
    assert "await PushNotificationManager.shared.registerForRemoteNotificationsIfAuthorized()" in text
    assert "didRegisterForRemoteNotificationsWithDeviceToken" in text
    assert "didFailToRegisterForRemoteNotificationsWithError" in text


def test_push_manager_tracks_permission_registration_and_local_reminder() -> None:
    text = APP_VIEW_MODEL.read_text(encoding="utf-8")
    assert "final class PushNotificationManager: NSObject, ObservableObject, UNUserNotificationCenterDelegate" in text
    assert "func requestAuthorizationAndRegister() async -> Bool" in text
    assert "UNUserNotificationCenter.current()" in text
    assert 'event: granted ? "push_permission_granted" : "push_permission_denied"' in text
    assert "UIApplication.shared.registerForRemoteNotifications()" in text
    assert "func scheduleOnboardingReminderIfNeeded() async" in text
    assert "func scheduleWorkoutReminderIfNeeded() async" in text
    assert 'private let onboardingReminderRequestIdentifier = "coachi.onboarding.reminder.v1"' in text
    assert 'private let workoutReminderRequestIdentifier = "coachi.workout.reminder.v1"' in text
    assert 'private let workoutReminderDeepLink = "coachi://tab/workout"' in text
    assert 'content.userInfo = [' in text
    assert 'notificationDeepLinkKey: workoutReminderDeepLink' in text
    assert 'event: "push_local_reminder_scheduled"' in text
    assert 'event: "push_token_registered"' in text
    assert 'event: "push_registration_failed"' in text
    assert 'event: "push_notification_opened"' in text
    assert 'UIApplication.shared.open(url)' in text


def test_onboarding_and_workout_runtime_use_single_push_manager_path() -> None:
    onboarding_text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    workout_text = WORKOUT_VM.read_text(encoding="utf-8")
    app_text = APP_VIEW_MODEL.read_text(encoding="utf-8")

    assert "let pushNotificationManager = PushNotificationManager.shared" in app_text
    assert "await appViewModel.pushNotificationManager.requestAuthorizationAndRegister()" in onboarding_text
    assert "await pushNotificationManager.scheduleOnboardingReminderIfNeeded()" in app_text
    assert "pushNotificationManager.clearPendingCoachReminders()" in app_text
    assert "PushNotificationManager.shared.clearPendingCoachReminders()" in workout_text
    assert "await PushNotificationManager.shared.scheduleWorkoutReminderIfNeeded()" in workout_text
