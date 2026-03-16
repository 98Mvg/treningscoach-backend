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
    assert "coachScore: workoutViewModel.homeCoachScore" in text
    assert "Text(L10n.coachScore)" in text
    assert "L10n.connectHeartRateMonitorTitle" in text
    assert "ConnectMonitorNoticeCard" not in text
    assert "WeeklyProgressRing" not in text


def test_profile_manage_monitors_row_uses_manage_monitors_view() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "title: L10n.manageHeartRateMonitors" in text
    assert "NavigationLink {\n                HeartRateMonitorsView()" in text


def test_profile_hides_placeholder_settings_sections_in_launch_runtime() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "accountSection" not in text
    assert "legalSection" not in text
    assert "PlaceholderSettingsView" not in text
    assert "sectionHeader(L10n.account)" in text
    assert "sectionHeader(L10n.coaching)" in text
    assert "sectionHeader(L10n.helpAndSupport)" in text
    assert "title: L10n.faqTitle" in text
    assert "title: L10n.contactSupport" in text
    assert "title: L10n.privacyPolicy" in text
    assert "title: L10n.termsOfUse" in text
    assert "SupportCenterView()" not in text
    assert "title: L10n.howCoachiWorks" in text
    assert "CoachingSettingsView()" in text
    assert "title: L10n.historyAndData" in text
    assert "HistoryAndDataView()" in text
    assert "PersonalProfileSettingsView()" in text
    assert "HealthProfileView()" in text
    assert "ManageSubscriptionView()" in text
    assert "AboutCoachiView()" in text
    assert "confirmationDialog(" in text
    assert 'Text("\\(L10n.appVersionLabel) \\(AppConfig.version)")' in text
    assert "private var isGuestMode: Bool" in text
    assert "if authManager.isAuthenticated || isGuestMode" in text
    assert "appViewModel.resetOnboarding()" in text


def test_personal_profile_static_rows_do_not_show_misleading_chevrons() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert 'title: L10n.current == .no ? "Navn: \\(appViewModel.userProfile.name)" : "Name: \\(appViewModel.userProfile.name)",\n                    trailingIcon: nil' in text
    assert '"\\(L10n.experienceLevel): \\(appViewModel.trainingLevelDisplayName)",\n                    trailingIcon: nil' in text


def test_profile_faq_covers_launch_critical_questions() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert 'question: "Hvordan fungerer Coachi?"' in text
    assert 'question: "Trenger jeg Apple Watch eller pulsklokke?"' in text
    assert 'question: "Hva skjer hvis puls mangler?"' in text
    assert 'question: "Hva er inkludert i gratisversjonen?"' in text
    assert 'question: "Hva er inkludert i Premium?"' in text
    assert 'question: "Hvordan avslutter jeg abonnementet?"' in text
    assert 'question: "Hvordan sletter jeg kontoen min?"' in text
    assert 'question: "Hvordan kontakter jeg support?"' in text
    assert 'question: "How does Coachi work?"' in text
    assert 'question: "Do I need Apple Watch or a heart-rate sensor?"' in text
    assert 'question: "What happens if heart rate is missing?"' in text


def test_profile_support_center_exposes_launch_critical_support_and_legal_surfaces() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "private struct SupportCenterView: View" not in text
    assert "private struct ManageSubscriptionView: View" in text
    assert "private struct AboutCoachiView: View" in text
    assert "private struct CoachingSettingsView: View" in text
    assert "private struct AudioAndVoicesView: View" in text
    assert "private struct HistoryAndDataView: View" in text
    assert 'icon: "questionmark.circle"' in text
    assert 'icon: "headphones"' in text
    assert 'icon: "hand.raised"' in text
    assert 'icon: "doc.text"' in text
    assert "DeleteAccountInfoView()" in text
    assert '"https://coachi.no/support"' in text
    assert '"https://coachi.no/privacy"' in text
    assert '"https://coachi.no/terms"' in text
    assert "AI.Coachi@hotmail.com" in text
    assert '@Environment(\\.openURL) private var openURL' in text
    assert "showManageSubscription = true" in text
    assert 'title: L10n.manageSubscription' in text
    assert 'title: isNorwegian ? "Slett konto nå" : "Delete account now"' in text
    assert "await authManager.deleteAccount()" in text
    assert "[SUPPORT_EMAIL]" not in text
    assert "[COMPANY_NAME]" not in text
    assert "[SUBSCRIPTION_DETAILS]" not in text
    assert "[PRIVACY_EMAIL]" not in text
    assert "[VERIFY PROCESSOR]" not in text
    assert "Coachi\\nE-post: \\(coachiSupportEmail)\\nNettside: \\(coachiWebsiteURL)" in text
    assert "Hosting og drift: Render" in text
    assert "Audio storage and sync: Cloudflare R2" in text
    assert "Coachi is free to download and includes a free version." in text
    assert "Last updated: \\(coachiPrivacyUpdatedEn)" in text
    assert 'Text(L10n.signOut)' in text
    assert 'Text(L10n.current == .no ? "Se alle tilbudene" : "See all offers")' in text
    assert '.foregroundColor(CoachiTheme.textPrimary)' in text
    assert '.foregroundColor(CoachiTheme.textSecondary)' in text
    assert '.fill(CoachiTheme.surfaceElevated)' in text
    assert 'private let coachiTermsURL = "https://coachi.no/terms"' in text


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
    assert 'title: L10n.current == .no ? "Gi Coachi tilgang til pulsdata" : "Give Coachi access to your heart-rate data"' in text
    assert 'title: L10n.current == .no ? "Den er grei!" : "Sounds good!"' in text
    assert "if isActionableMonitor(brand)" in text
    assert "monitorRowContent(for: brand, showsChevron: false)" in text


def test_health_profile_is_a_dedicated_surface_not_a_wrapper() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "private struct HealthProfileView: View" in text
    assert "PersonalProfileSettingsView()" not in text[text.index("private struct HealthProfileView: View"):text.index("private struct PersonalProfileSettingsView: View")]
    assert 'title: L10n.healthProfile' in text
    assert 'title: "\\(L10n.dateOfBirth): \\(birthDateDisplayLine)"' in text


def test_localization_contains_monitor_and_coach_score_strings() -> None:
    text = L10N_FILE.read_text(encoding="utf-8")
    assert "static var coachScore: String" in text
    assert "static var connectHeartRateMonitorTitle: String" in text
    assert "static var connectHeartRateMonitorBody: String" in text
    assert "static var account: String" in text
    assert "static var accountStatus: String" in text
    assert "static var signedInAs: String" in text
    assert "static var usingWithoutAccount: String" in text
    assert "static var connectAccountLaterHint: String" in text
    assert "static var coaching: String" in text
    assert "static var helpAndSupport: String" in text
    assert "static var audioAndVoices: String" in text
    assert "static var historyAndData: String" in text
    assert "static var howCoachiWorks: String" in text
    assert "static var ifHeartRateMissing: String" in text
    assert "static var trainingHistory: String" in text
    assert "static var dataAndPrivacy: String" in text
    assert "static var voicePackStatus: String" in text
    assert "static var activeVoice: String" in text
    assert "static var aboutCoachi: String" in text
    assert "static var advancedSettings: String" in text
    assert "static var audioMaintenance: String" in text
    assert "static var liveCapability: String" in text
    assert "static var historyCapability: String" in text
    assert "static var liveCoachingSourceHint: String" in text
    assert "static var historySyncOnlyHint: String" in text
    assert "static var goToManageMonitors: String" in text
    assert "static var manageSubscription: String" in text
    assert "static var notConnected: String" in text
    assert "static var legal: String" in text
    assert "static var termsOfUse: String" in text
    assert "static var privacyPolicy: String" in text
    assert "static var appVersionLabel: String" in text
