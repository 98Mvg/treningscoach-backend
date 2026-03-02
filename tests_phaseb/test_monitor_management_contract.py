from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "HomeView.swift"
)
PROFILE_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ProfileView.swift"
)
MONITORS_VIEW = PROFILE_VIEW
L10N_FILE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Localization" / "L10n.swift"
)


def test_home_connect_watch_routes_to_manage_monitors_and_shows_coach_score() -> None:
    text = HOME_VIEW.read_text(encoding="utf-8")
    assert "@State private var showManageMonitors = false" in text
    assert ".navigationDestination(isPresented: $showManageMonitors)" in text
    assert "HeartRateMonitorsView()" in text
    assert "CoachScoreSection(" in text
    assert "records: viewModel.recentWorkouts" in text
    assert "coachScore: workoutViewModel.coachScore" in text
    assert "Text(L10n.coachScore)" in text
    assert "L10n.connectHeartRateMonitorTitle" in text
    assert "ConnectMonitorNoticeCard" not in text
    assert "WeeklyProgressRing" not in text


def test_profile_manage_monitors_row_uses_manage_monitors_view() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "title: L10n.manageHeartRateMonitors" in text
    assert "NavigationLink {\n                HeartRateMonitorsView()" in text


def test_profile_settings_continuation_matches_reference_sections() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "sectionHeader(L10n.helpAndSupport)" in text
    assert "title: L10n.faqTitle" in text
    assert 'trailingIcon: "arrow.up.right.square"' in text
    assert "title: L10n.contactSupport" in text
    assert "sectionHeader(L10n.legal)" in text
    assert "title: L10n.termsOfUse" in text
    assert "title: L10n.privacyPolicy" in text
    assert 'Text("\\(L10n.appVersionLabel) \\(AppConfig.version)")' in text


def test_manage_monitors_screen_matches_provider_list_contract() -> None:
    text = MONITORS_VIEW.read_text(encoding="utf-8")
    assert 'case garmin = "Garmin"' in text
    assert 'case polar = "Polar"' in text
    assert 'case fitbit = "Fitbit"' in text
    assert 'case appleWatch = "Apple Watch"' in text
    assert 'case suunto = "Suunto"' in text
    assert 'case withings = "Withings"' in text
    assert "navigationTitle(L10n.manageHeartRateMonitors)" in text
    assert "L10n.notConnected" in text
    assert "if brand == .appleWatch" in text


def test_localization_contains_monitor_and_coach_score_strings() -> None:
    text = L10N_FILE.read_text(encoding="utf-8")
    assert 'static var coachScore: String { "Coach score" }' in text
    assert "static var connectHeartRateMonitorTitle: String" in text
    assert "static var connectHeartRateMonitorBody: String" in text
    assert "static var goToManageMonitors: String" in text
    assert "static var notConnected: String" in text
    assert "static var legal: String" in text
    assert "static var termsOfUse: String" in text
    assert "static var privacyPolicy: String" in text
    assert "static var appVersionLabel: String" in text
    assert "Treningsnivaa" not in text
    assert " for aa " not in text
