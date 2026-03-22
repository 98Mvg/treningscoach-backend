from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "HomeView.swift"
)
PROFILE_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ProfileView.swift"
)
MONITORS_VIEW = PROFILE_VIEW
SETTINGS_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Settings" / "SettingsView.swift"
)
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
    assert "@State private var selectedDay: Date?" in text
    assert "selectedDay = slot.date" in text
    assert "displayedCoachScore" in text
    assert "ForEach(weekSlots)" in text
    assert "slot.isSelected" in text
    assert "Text(L10n.coachScore)" in text
    assert "L10n.connectHeartRateMonitorTitle" in text
    assert "ConnectMonitorNoticeCard" not in text
    assert "WeeklyProgressRing" not in text


def test_profile_manage_monitors_row_uses_manage_monitors_view() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "title: L10n.manageHeartRateMonitors" in text
    assert "NavigationLink {\n                HeartRateMonitorsView()" in text


def test_settings_hides_audio_maintenance_actions_behind_expandable_toggle() -> None:
    text = SETTINGS_VIEW.read_text(encoding="utf-8")
    assert "@State private var showAdvancedVoiceOptions = false" in text
    assert "showAdvancedVoiceOptions.toggle()" in text
    assert 'Image(systemName: "chevron.down")' in text
    assert "if showAdvancedVoiceOptions {" in text
    assert "Task { await syncManager.resetAndResync() }" in text
    assert "syncManager.purgeStaleFiles()" in text
    assert ".buttonStyle(.plain)" in text


def test_profile_hides_placeholder_settings_sections_in_launch_runtime() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "accountSection" not in text
    assert "legalSection" not in text
    assert "PlaceholderSettingsView" not in text
    assert "private var premiumSection: some View" not in text
    assert "sectionHeader(L10n.account)" in text
    assert "sectionHeader(L10n.coaching)" in text
    assert "sectionHeader(L10n.helpAndSupport)" in text
    assert "FAQView()" not in text
    assert "NavigationLink {\n                FAQGuideView()" in text
    assert "NavigationLink {\n                ContactSupportView()" in text
    assert 'private let coachiPrivacyURL = "https://coachi.no/privacy"' in text
    assert 'private let coachiTermsURL = "https://coachi.no/terms"' in text
    assert "guard let url = URL(string: coachiPrivacyURL) else { return }" in text
    assert "guard let url = URL(string: coachiTermsURL) else { return }" in text
    assert "openURL(url)" in text
    assert "title: L10n.contactSupport" in text
    assert "title: L10n.faqTitle" in text
    assert "title: L10n.privacyPolicy" in text
    assert "title: L10n.termsOfUse" in text
    assert "SupportCenterView()" not in text
    assert "title: L10n.howCoachiWorks" in text
    assert "CoachingSettingsView()" in text
    assert "title: L10n.historyAndData" in text
    assert "HistoryAndDataView()" in text
    assert "PersonalProfileSettingsView()" in text
    assert "HealthProfileView()" in text
    assert "ManageSubscriptionView(isManageSubscriptionPresented: $isManageSubscriptionPresented)" in text
    assert "AboutCoachiView()" in text
    assert text.count("DeleteAccountInfoView()") == 1
    assert 'title: "\\(L10n.aboutCoachi) · v\\(AppConfig.version)"' not in text
    assert "confirmationDialog(" in text
    assert 'Text("\\(L10n.appVersionLabel) \\(AppConfig.version)")' in text
    assert "private var isGuestMode: Bool" in text
    assert "if authManager.isAuthenticated || isGuestMode" in text
    assert "appViewModel.resetOnboarding()" in text
    assert '.frame(maxWidth: .infinity, alignment: .leading)' in text


def test_personal_profile_static_rows_do_not_show_misleading_chevrons() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    personal_slice = text[text.index("private struct PersonalProfileSettingsView: View"):text.index("private struct AboutCoachiView: View")]
    assert "import PhotosUI" not in text
    assert "private struct CoachiProfileAvatarView: View" in text
    assert "AsyncImage(url: resolvedURL)" in text
    assert "PhotosPicker(selection: $selectedPhotoItem, matching: .images)" not in text
    assert 'Text(L10n.current == .no ? "Profilbilde" : "Profile photo")' in text
    assert "private func profilePhotoStatusLine(isAuthenticated: Bool, currentAvatarURL: String?) -> String {" in personal_slice
    assert "authManager.updateProfileAvatar(imageData: jpegData)" not in text
    assert 'title: L10n.current == .no ? "Navn" : "Name",' in text
    assert 'title: L10n.current == .no ? "E-post" : "Email",' in text
    assert 'Text(L10n.current == .no ? "Slett brukerkontoen din" : "Delete your account")' in personal_slice
    assert 'Text(L10n.current == .no ? "Slett konto" : "Delete account")' not in personal_slice
    assert personal_slice.index('title: L10n.current == .no ? "E-post" : "Email",') < personal_slice.index('Text(L10n.current == .no ? "Slett brukerkontoen din" : "Delete your account")')
    assert personal_slice.index('Text(L10n.current == .no ? "Slett brukerkontoen din" : "Delete your account")') < personal_slice.index('sectionHeader(L10n.current == .no ? "App" : "App")')
    assert 'title: L10n.current == .no ? "Navn: \\(appViewModel.userProfile.name)" : "Name: \\(appViewModel.userProfile.name)"' not in text
    assert '"\\(L10n.experienceLevel): \\(appViewModel.trainingLevelDisplayName)"' not in text
    assert "sectionHeader(L10n.account)" not in personal_slice
    assert 'Text(L10n.signOut)' not in personal_slice
    assert "showingSignOutConfirmation" not in personal_slice

def test_profile_faq_guide_covers_launch_help_topics() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "private struct FAQGuideView: View" in text
    assert "private struct FAQGuideSection: Identifiable" in text
    assert 'title: "Hvordan Coachi fungerer"' in text
    assert 'title: "Klokke og synkronisering"' in text
    assert 'title: "Brukerprofil"' in text
    assert 'title: "Abonnement"' in text
    assert 'title: "Puls og pulsmåler"' in text
    assert 'title: "How Coachi works"' in text
    assert 'title: "Watch and sync"' in text
    assert 'title: "User profile"' in text
    assert 'title: "Subscription"' in text
    assert 'title: "Heart rate and sensors"' in text
    assert "SupportGuideCard(section: section)" in text
    assert "Velg Administrer abonnement for å se hva som er inkludert i Gratis og Premium." in text
    assert "Use Manage subscription to compare what is included in Free and Premium." in text


def test_profile_support_center_exposes_launch_critical_support_and_legal_surfaces() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "private struct SupportCenterView: View" not in text
    assert "private struct ManageSubscriptionView: View" in text
    assert "private struct AppUpdatePromptView: View" in text
    assert "private struct AboutCoachiView: View" in text
    assert "private struct CoachingSettingsView: View" in text
    assert "private struct AudioAndVoicesView: View" in text
    assert "private struct HistoryAndDataView: View" in text
    assert "private struct FAQView: View" not in text
    assert "private struct ContactSupportView: View" in text
    assert "private struct SupportRequestFormView: View" in text
    assert "private struct SupportGuideCard: View" in text
    assert "SupportFAQItem" not in text
    assert "supportFAQItems(isNorwegian: isNorwegian)" not in text
    assert 'icon: "headphones"' in text
    assert 'icon: "questionmark.circle"' in text
    assert 'icon: "hand.raised"' in text
    assert 'icon: "doc.text"' in text
    assert "DeleteAccountInfoView()" in text
    assert "coachiSupportURL" in text
    assert "coachiDownloadURL" in text
    assert "AI.Coachi@hotmail.com" in text
    assert "Selskapsdetaljer fylles inn senere." not in text
    assert "showManageSubscription = true" in text
    assert 'title: L10n.manageSubscription' in text
    assert 'title: isNorwegian ? "Slett konto nå" : "Delete account now"' in text
    assert "await authManager.deleteAccount()" in text
    assert 'Text(isNorwegian ? "Kontakt support" : "Contact support")' in text
    assert 'title: L10n.current == .no ? "Appoppdateringer" : "App updates"' in text
    assert "checkForAppUpdateIfNeeded(" in text
    assert ".navigationTitle(L10n.faqTitle)" in text
    assert 'NavigationLink {\n                    SupportRequestFormView()' in text
    assert 'components.scheme = "mailto"' in text
    assert 'URLQueryItem(name: "subject", value: subject)' in text
    assert 'URLQueryItem(name: "body", value: body)' in text
    assert "[SUPPORT_EMAIL]" not in text
    assert "[COMPANY_NAME]" not in text
    assert "[SUBSCRIPTION_DETAILS]" not in text
    assert "[PRIVACY_EMAIL]" not in text
    assert "[VERIFY PROCESSOR]" not in text
    assert "Coachi\\nE-post: \\(coachiSupportEmail)\\nNettside: \\(coachiWebsiteURL)" in text
    assert "Historikk og data" in text
    assert "Hosting og drift: Render" in text
    assert "Tekst-til-tale: ElevenLabs" in text
    assert "Audio storage and sync: Cloudflare R2" in text
    assert "Text to speech: ElevenLabs" in text
    assert "Coachi is free to download and includes a free version." in text
    assert "Last updated: \\(coachiPrivacyUpdatedEn)" in text
    assert 'Text(L10n.signOut)' in text
    assert 'Text(L10n.current == .no ? "Se alle tilbudene" : "See all offers")' not in text
    assert '.foregroundColor(CoachiTheme.textPrimary)' in text
    assert '.foregroundColor(CoachiTheme.textSecondary)' in text
    assert 'private let coachiTermsURL = "https://coachi.no/terms"' in text
    assert "@State private var accountStatus: String" in text
    assert "@State private var category: String" in text
    assert "_accountStatus = State(initialValue: Self.defaultAccountStatus(isNorwegian: isNorwegian))" in text
    assert "_category = State(initialValue: Self.defaultCategory(isNorwegian: isNorwegian))" in text
    assert "@State private var countryDialCode: SupportDialCodeOption = .norway" in text
    assert "@State private var phoneNumber = \"\"" in text
    assert "if accountStatus.isEmpty || !accountStatusOptions.contains(accountStatus)" in text
    assert "if category.isEmpty || !categoryOptions.contains(category)" in text
    assert "authManager.currentUser?.resolvedDisplayName ?? appViewModel.userProfile.name" in text
    assert "SupportPhoneField(" in text
    assert "SupportDialCodeOption" in text
    assert 'case norway = "+47"' in text
    assert "Telefonnummer" in text
    assert "Phone number" in text
    assert "ForEach(SupportDialCodeOption.allCases)" in text
    assert "countryDialCode.dialCode" in text


def test_manage_subscription_embeds_inline_offer_swiper_without_onboarding_header() -> None:
    profile_text = PROFILE_VIEW.read_text(encoding="utf-8")
    content_text = (
        REPO_ROOT
        / "TreningsCoach"
        / "TreningsCoach"
        / "Views"
        / "ContentView.swift"
    ).read_text(encoding="utf-8")
    onboarding_text = (
        REPO_ROOT
        / "TreningsCoach"
        / "TreningsCoach"
        / "Views"
        / "Onboarding"
        / "OnboardingContainerView.swift"
    ).read_text(encoding="utf-8")

    assert "presentationMode: .manageSubscriptionInline" in profile_text
    assert "WatchConnectedPremiumOfferStepView(" in profile_text
    assert "Continue to your Premium Dashboard" not in profile_text
    assert "struct ManageSubscriptionFeatureRowData: Identifiable" not in profile_text
    assert "enum SubscriptionComparisonCatalog {" not in profile_text
    assert "OnboardingAtmosphereView(step: .premiumOffer)" not in profile_text
    assert ".fullScreenCover(isPresented: $showPlanOffers)" not in profile_text
    assert 'Text(isNorwegian ? "Mine inkluderte elementer" : "My included items")' not in profile_text
    assert 'Text(isNorwegian ? "Inkludert i abonnementet" : "Included in your plan")' not in profile_text
    assert "private var subscriptionStatusCard: some View" not in profile_text
    assert "private var includedItemsCard: some View" not in profile_text
    assert '(isNorwegian ? "Administrer i App Store" : "Manage in App Store")' in profile_text
    assert '(isNorwegian ? "Gjenopprett kjøp" : "Restore purchases")' in profile_text
    assert '.frame(maxWidth: 320)' in profile_text
    assert '.background(Color(hex: "22C55E"))' in profile_text
    assert "min(max(UIScreen.main.bounds.height * 0.86, 760), 920)" in profile_text
    assert 'guard let url = URL(string: coachiTermsURL) else { return }' in profile_text
    assert 'guard let url = URL(string: coachiPrivacyURL) else { return }' in profile_text
    assert "openURL(url)" in profile_text
    assert "@Binding var isManageSubscriptionPresented: Bool" in profile_text
    assert "ManageSubscriptionView(isManageSubscriptionPresented: $isManageSubscriptionPresented)" in profile_text
    assert "isManageSubscriptionPresented = true" in profile_text
    assert "isManageSubscriptionPresented = false" in profile_text
    assert "ProfileView(" in content_text
    assert "isManageSubscriptionPresented: $isManageSubscriptionPresented" in content_text
    assert "&& !isManageSubscriptionPresented" in content_text
    assert "struct ManageSubscriptionFeatureRowData: Identifiable" in onboarding_text
    assert "enum SubscriptionComparisonCatalog {" in onboarding_text
    assert "private var onboardingOfferBody: some View {" in onboarding_text
    assert "private var inlineManageSubscriptionBody: some View {" in onboarding_text
    assert "private var isInlineManageSubscription: Bool { presentationMode == .manageSubscriptionInline }" in onboarding_text
    assert "private var autoAdvanceIntervalSeconds: UInt64?" in onboarding_text
    assert "12" in onboarding_text
    assert '.fullScreenCover(item: $purchaseSuccessState)' in onboarding_text
    assert 'premiumSuccessScreen(for: state)' in onboarding_text
    assert 'Color(hex: "2F7BFF")' in onboarding_text


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
    assert 'title: L10n.current == .no ? "Gi Coachi tilgang til pulsdata" : "Give Coachi access to your heart-rate data"' not in text
    assert 'title: L10n.current == .no ? "Den er grei!" : "Sounds good!"' not in text
    assert "L10n.liveCoachingSourceHint" not in text
    assert "if isActionableMonitor(brand)" in text
    assert "monitorRowContent(for: brand, showsChevron: false)" in text
    assert "private let floatingTabBarContentClearance: CGFloat = 96" in text
    assert text.count("Color.clear.frame(height: floatingTabBarContentClearance)") == 1
    assert "contentTopInsetOverride: 16" in text
    assert "bottomActionClearance: floatingTabBarContentClearance" in text


def test_health_profile_is_a_dedicated_surface_not_a_wrapper() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "private struct HealthProfileView: View" in text
    assert "PersonalProfileSettingsView()" not in text[text.index("private struct HealthProfileView: View"):text.index("private struct PersonalProfileSettingsView: View")]
    assert '@AppStorage("user_gender") private var storedGender: String = ""' in text
    assert '@AppStorage("user_height_cm") private var storedHeightCm: Int = 0' in text
    assert '@AppStorage("user_weight_kg") private var storedWeightKg: Int = 0' in text
    assert '@AppStorage("hr_max") private var storedMaxHeartRate: Int = 0' in text
    assert '@AppStorage("resting_hr") private var storedRestingHeartRate: Int = 0' in text
    assert 'title: L10n.dateOfBirth,' in text
    assert 'title: L10n.current == .no ? "Kjønn" : "Gender",' in text
    assert 'title: L10n.current == .no ? "Høyde" : "Height",' in text
    assert 'title: L10n.current == .no ? "Vekt" : "Weight",' in text
    assert 'title: L10n.current == .no ? "Makspuls" : "Max heart rate",' in text
    assert 'title: L10n.current == .no ? "Hvilepuls" : "Resting heart rate",' in text


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
