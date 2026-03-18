from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "RootView.swift"
ONBOARDING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "OnboardingContainerView.swift"
)
THEME_FILE = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Theme"
    / "AppTheme.swift"
)
INTRO_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "FeaturesPageView.swift"
)
AUTH_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "AuthView.swift"
)
PROFILE_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ProfileView.swift"
)
CUSTOM_TAB_BAR = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Components"
    / "CustomTabBar.swift"
)
SETTINGS_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Settings"
    / "SettingsView.swift"
)
LANGUAGE_SELECTION_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "LanguageSelectionView.swift"
)
L10N_FILE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Localization" / "L10n.swift"
)
ASSETS_ROOT = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Resources" / "Assets.xcassets"
)


def test_root_view_is_not_forced_to_dark_mode() -> None:
    text = ROOT_VIEW.read_text(encoding="utf-8")
    assert ".preferredColorScheme(.dark)" not in text


def test_root_view_expands_to_full_window_size() -> None:
    text = ROOT_VIEW.read_text(encoding="utf-8")
    assert ".frame(maxWidth: .infinity, maxHeight: .infinity)" in text


def test_onboarding_uses_step_based_atmosphere_background() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "OnboardingAtmosphereView(step: currentStep)" in text
    assert ".frame(maxWidth: .infinity, maxHeight: .infinity)" in text
    assert 'return "OnboardingBgOutdoor"' in text
    assert 'return "OnboardingBgRun"' in text
    assert 'return "OnboardingBgCalm"' in text


def test_onboarding_hides_status_bar_on_all_steps() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "private var hidesStatusBar: Bool {" in text
    assert "currentStep == .welcome || currentStep == .features" not in text
    status_bar_block = text.split("private var hidesStatusBar: Bool {", 1)[1].split("}", 1)[0]
    assert "true" in status_bar_block
    assert ".statusBar(hidden: hidesStatusBar)" in text


def test_onboarding_scaffold_clamps_layout_width_and_vertical_scroll_only() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "let layoutWidth = min(min(renderWidth, deviceWidth), 500)" in text
    assert "let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))" in text
    assert "let bottomInset = min(42.0, max(20.0, geo.safeAreaInsets.bottom + 8.0))" in text
    assert "let contentTopInset = contentTopInsetOverride ?? max(renderHeight * 0.08, 24.0)" in text
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert ".safeAreaInset(edge: .bottom, spacing: 0)" in text
    assert ".scrollBounceBehavior(.basedOnSize, axes: .vertical)" in text
    assert ".scrollDismissesKeyboard(.interactively)" in text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in text
    assert ".clipped()" in text


def test_theme_defines_adaptive_light_dark_palette() -> None:
    text = THEME_FILE.read_text(encoding="utf-8")
    assert "private static func adaptive(light: String, dark: String) -> Color" in text
    assert "Color(uiColor: UIColor { traits in" in text
    assert "static let borderSubtle" in text


def test_onboarding_background_assets_exist() -> None:
    expected = [
        ASSETS_ROOT / "OnboardingBgOutdoor.imageset" / "onboarding-bg-outdoor.png",
        ASSETS_ROOT / "OnboardingBgRun.imageset" / "onboarding-bg-run.png",
        ASSETS_ROOT / "OnboardingBgCalm.imageset" / "onboarding-bg-calm.png",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    assert not missing, f"Missing onboarding background assets: {missing}"


def test_intro_value_carousel_contract() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    intro_block = text.split("private let introPages: [IntroStoryPage] = [", 1)[1].split("private var activePage", 1)[0]
    post_auth_block = text.split("private func postAuthPages(displayName: String) -> [IntroStoryPage] {", 1)[1].split("private var showcasePrimaryTitle", 1)[0]

    assert 'imageName: "IntroStory1"' in text
    assert 'imageName: "IntroStory2"' in text
    assert 'imageName: "IntroStory3"' in text
    assert 'imageName: "IntroStory4"' in text
    assert 'Text(primaryTitle)' in text
    assert 'Mode {' in text
    assert '.intro' in text
    assert 'case postAuthExplainer(displayName: String)' in text
    assert "if let secondaryTitle, let onSecondary {" in text
    assert "Text(secondaryTitle)" in text
    assert "Circle()" in text
    assert ".frame(width: 16, height: 16)" in text
    assert ".scaledToFill()" in text
    assert "showsCoachScoreCard" in text
    assert "activePage" in text
    assert "DragGesture(minimumDistance: 24)" in text
    assert "if horizontal < 0 {" in text
    assert "currentPage += 1" in text
    assert "currentPage -= 1" in text
    assert "@State private var autoAdvanceTask: Task<Void, Never>?" in text
    assert "Task.sleep(nanoseconds: intervalSeconds * 1_000_000_000)" in text
    assert "if case .intro = mode {" in text
    assert intro_block.count("IntroStoryPage(") == 4
    assert "Få veiledning av en coach live på øret" in intro_block
    assert "Coachen holder fokus på det viktige i økten" in intro_block
    assert "Få en score av Coachen etter hver økt" in intro_block
    assert "Coachi kobles enkelt til pulsklokka di" in intro_block
    assert 'imageName: "IntroStory3"' in intro_block
    assert 'imageName: "IntroStory2"' in intro_block
    assert intro_block.count('bodyNo: ""') >= 3
    assert "Du får tydelige beskjeder når det betyr noe, og ro når du bare skal løpe." not in intro_block
    assert "CoachScore gir deg et enkelt tall på kontroll, flyt og gjennomføring." not in intro_block
    assert "Alt i orden! Du kan fortsatt bli coachet pa pustanalyse." in intro_block
    assert 'deviceTags: ["Apple Watch", "Garmin", "Fitbit", "Polar", "Withings", "Suunto"]' in intro_block
    assert "Bluetooth HR" not in intro_block
    assert "Samsung" not in intro_block
    assert "Jeg guider deg live med pulssoner" not in intro_block
    assert "Etter økten kan vi snakke live" not in intro_block
    assert post_auth_block.count("IntroStoryPage(") == 5
    assert 'bodyNo: "La meg først forklare hvordan vi kan hjelpe deg."' in post_auth_block
    assert post_auth_block.count('bodyNo: ""') == 4
    assert post_auth_block.count('bodyEn: ""') == 4
    assert 'titleNo: "Jeg guider deg live med pulssoner"' in post_auth_block
    assert 'titleNo: "Jeg motiverer og tilpasser økten dynamisk"' in post_auth_block
    assert 'titleNo: "Du får en CoachScore etter hver økt"' in post_auth_block
    assert 'titleNo: "Etter økten kan vi snakke live"' in post_auth_block
    assert "WatchBPMPreviewCard()" in text
    assert "IntensityBarPreviewCard()" in text
    assert "TalkToCoachPreviewCard()" in text
    assert "if activePage.showsCoachScoreCard {" in text
    assert "FitnessAgePromptCard" not in text
    assert "FitnessAgeExampleCard" not in text
    assert "ActivityQuotientPreviewCard" not in text
    assert "DeviceSupportPreviewCard" not in text
    assert "Din AQ" not in text
    assert "introTrustBadge(" not in text
    assert 'Logg inn med Apple eller e-post for å fortsette.' not in text
    assert "score: 100" in text
    assert "private func deviceLogoGrid(_ tags: [String]) -> some View {" in text
    assert "LazyVGrid(columns: columns, alignment: .leading, spacing: 18)" in text
    assert 'Text("WATCH")' in text
    assert 'Text("GARMIN")' in text
    assert 'Text("fitbit")' in text
    assert 'Text("POLAR")' in text
    assert 'Text("WITHINGS")' in text
    assert 'Text("SUUNTO")' in text


def test_onboarding_uses_valid_sf_symbols_for_gender_choices() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert 'return "figure.stand"' in text
    assert 'return "figure.stand.dress"' in text
    assert '"mars"' not in text
    assert '"venus"' not in text


def test_intro_layout_reserves_width_for_card_padding() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert "let renderWidth = geo.size.width" in text
    assert "let renderHeight = geo.size.height" in text
    assert "let deviceWidth = UIScreen.main.bounds.width" in text
    assert "let layoutWidth = min(min(renderWidth, deviceWidth), 500)" in text
    assert "let horizontalSafeInset = max(safeAreaInsets.leading, safeAreaInsets.trailing)" in text
    assert "let cardWidth: CGFloat = max(0, layoutWidth - (cardSideInset * 2))" in text
    assert "let textWidth: CGFloat = max(0, cardWidth - (cardContentInset * 2))" in text
    assert ".padding(.horizontal, cardSideInset)" in text
    assert ".padding(.horizontal, cardContentInset)" in text
    assert ".frame(width: cardWidth, alignment: .leading)" in text
    assert ".frame(width: textWidth, alignment: .leading)" in text
    assert ".frame(maxWidth: .infinity, alignment: .top)" in text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in text
    assert ".frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)" in text
    assert "let topSpacing: CGFloat = max(renderHeight * 0.22, safeAreaInsets.top + 28)" in text


def test_intro_layout_keeps_headline_and_body_multiline() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert text.count(".lineLimit(nil)") >= 2
    assert text.count(".fixedSize(horizontal: false, vertical: true)") >= 3
    assert ".dynamicTypeSize(.small ... .xxxLarge)" in text


def test_intro_swipe_gestures_not_blocked_by_nested_scrollview() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert "let needsVerticalScroll = renderHeight < 730 || dynamicTypeSize.isAccessibilitySize" in text
    assert "if needsVerticalScroll {" in text
    assert ".scrollBounceBehavior(.basedOnSize, axes: .vertical)" in text
    assert "DragGesture(minimumDistance: 24)" in text
    assert ".simultaneousGesture(" in text
    intro_start = text.index("private func introContent(")
    intro_slice = text[intro_start:]
    assert ".contentShape(Rectangle())" in intro_slice
    assert ".simultaneousGesture(" in intro_slice


def test_intro_pages_do_not_wrap_content_in_transparent_outer_card() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    intro_slice = text.split("private func introContent(", 1)[1].split("private func showcaseContent(", 1)[0]
    assert "RoundedRectangle(cornerRadius: 24, style: .continuous)" not in intro_slice
    assert ".background(Color.white.opacity(0.12))" not in intro_slice
    assert 'Text("Coachi")' not in intro_slice


def test_intro_only_ignores_vertical_safe_areas() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert ".ignoresSafeArea(edges: [.top, .bottom])" in text
    assert ".ignoresSafeArea()" not in text


def test_intro_layout_places_indicator_above_register_cta() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    dots_idx = text.index("HStack(spacing: 10) {")
    register_idx = text.index("Button(action: onPrimary)")
    assert dots_idx < register_idx
    assert ".padding(.top, max(14, geo.safeAreaInsets.top + 8))" not in text


def test_post_auth_explainer_uses_showcase_navigation() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    post_auth_block = text.split("private func postAuthPages(displayName: String) -> [IntroStoryPage] {", 1)[1].split("private var showcasePrimaryTitle", 1)[0]
    assert "private func showcaseContent(" in text
    assert "private var showcasePrimaryTitle: String {" in text
    assert 'return L10n.current == .no ? "Neste" : "Next"' in text
    assert "private func showcasePrimaryAction()" in text
    assert "private func showcaseSecondaryAction()" in text
    assert "if currentPage < pages.count - 1 {" in text
    assert "else if let onSecondary {" in text
    assert "let showcaseTextWidth = max(0.0, min(textWidth, isNarrow ? 288.0 : 328.0))" in text
    assert "let showcaseTopSpacing = activePage.body(for: L10n.current).isEmpty" in text
    assert "? max(renderHeight * 0.25, topSpacing + 24)" in text
    assert ".frame(width: showcaseTextWidth, alignment: .leading)" in text
    assert '.frame(width: 74, height: 74)' in text
    assert '.clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))' in text
    assert 'bodyNo: "La meg først forklare hvordan vi kan hjelpe deg."' in post_auth_block
    assert post_auth_block.count('bodyNo: ""') == 4
    assert 'previewKind: .watchBPM' in post_auth_block
    assert 'previewKind: .intensityBar' in post_auth_block
    assert 'previewKind: .talkToCoach' in post_auth_block
    assert ".shadow(color: Color.black.opacity(0.38), radius: 16, x: 0, y: 6)" in text


def test_post_auth_explainer_background_does_not_dim_top_edge() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert "private var backgroundGradientColors: [Color] {" in text
    assert "private var backgroundDimOpacity: Double {" in text
    assert "if activePage.presentationStyle == .showcase {" in text
    assert "? [Color.clear, Color.clear, Color.black.opacity(0.44)]" in text
    assert ': [Color.clear, Color.clear, Color.black.opacity(0.34)]' in text
    assert "return 0.0" in text


def test_post_auth_preview_cards_do_not_use_translucent_outer_chrome() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    preview_slice = text.split("private struct CoachScorePreviewCard: View {", 1)[1]
    assert preview_slice.count(".background(Color.white.opacity(0.13))") == 0
    assert preview_slice.count(".stroke(Color.white.opacity(0.2), lineWidth: 1)") == 0


def test_auth_layout_clamps_width_for_all_iphone_sizes() -> None:
    text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "let layoutWidth = min(min(renderWidth, deviceWidth), 500)" in text
    assert "let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))" in text
    assert "let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))" in text
    assert "Spacer().frame(height: max(renderHeight * 0.12, geo.safeAreaInsets.top + 18.0))" in text
    assert "Spacer().frame(height: bottomInset)" in text
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert ".scrollBounceBehavior(.basedOnSize, axes: .vertical)" in text
    assert ".scrollDismissesKeyboard(.interactively)" in text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in text
    assert ".clipped()" in text


def test_auth_view_supports_register_and_login_modes() -> None:
    text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "enum AuthFlowMode {" in text
    assert "case register" in text
    assert "case login" in text
    assert "let mode: AuthFlowMode" in text
    assert "L10n.registerWithApple" in text
    assert "L10n.loginWithApple" in text
    assert "L10n.registerWithGoogle" in text
    assert "L10n.loginWithGoogle" in text
    assert "L10n.loginWithEmail" in text
    assert 'badge: L10n.current == .no ? "Kommer snart" : "Coming soon"' in text
    assert "disabled: authManager.isLoading" in text
    assert "header(contentWidth: contentWidth)" not in text
    assert "authBenefitRow(" not in text
    assert "Sign in with Apple or email to save your progress and unlock Premium" not in text
    assert "Logg inn med Apple eller e-post for å lagre fremgangen din og låse opp Premium" not in text
    assert "private var requiresAcceptedTerms: Bool {" in text
    assert "mode == .register" in text
    assert "private var hasAcceptedRequiredTerms: Bool {" in text
    assert "!requiresAcceptedTerms || acceptedTerms" in text
    assert "showTermsValidationError = true" in text
    assert "emailCodeRequested" in text
    assert "requestEmailSignInCode" in text
    assert "signInWithEmail(" in text
    assert "if mode == .register {" in text
    assert "termsSection" in text
    assert "secondaryActionButton(" in text
    assert "L10n.continueWithoutAccount" in text
    assert "Text(L10n.signInLaterHint)" in text
    assert "Password" not in text
    assert "Gjenta passordet" not in text
    assert "showPrivacySheet = true" in text
    assert "showTermsSheet = true" in text
    assert "acceptedTerms.toggle()" in text
    assert ".tint(CoachiTheme.textPrimary)" in text
    assert "focusedField = .email" not in text


def test_onboarding_birth_date_picker_is_scrollable_wheel() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "displayedComponents: .date" in text
    assert ".datePickerStyle(.wheel)" in text
    assert ".datePickerStyle(.compact)" not in text


def test_profile_birth_date_editor_uses_scrollable_wheel_picker() -> None:
    text = PROFILE_VIEW.read_text(encoding="utf-8")
    assert "BirthDateEditorSheet" in text
    assert ".sheet(isPresented: $showingBirthDateEditor)" in text
    assert ".datePickerStyle(.wheel)" in text
    assert "displayedComponents: .date" in text


def test_profile_tab_label_uses_din_profil_and_your_profile() -> None:
    l10n_text = L10N_FILE.read_text(encoding="utf-8")
    tab_bar_text = CUSTOM_TAB_BAR.read_text(encoding="utf-8")

    assert 'static var profileTab: String' in l10n_text
    assert '"Din profil"' in l10n_text
    assert '"Your profile"' in l10n_text
    assert "L10n.profileTab" in tab_bar_text


def test_custom_tab_bar_uses_compact_height_layout() -> None:
    text = CUSTOM_TAB_BAR.read_text(encoding="utf-8")
    assert ".padding(.vertical, 6)" in text
    assert ".padding(.vertical, 4)" in text
    assert "RoundedRectangle(cornerRadius: 18, style: .continuous)" in text


def test_profile_and_settings_do_not_expose_technical_provider_details() -> None:
    settings_text = SETTINGS_VIEW.read_text(encoding="utf-8")

    assert "ElevenLabs" not in settings_text
    assert 'title: "Backend"' not in settings_text
    assert "AppConfig.backendURL" not in settings_text


def test_norwegian_language_strings_use_sprak() -> None:
    l10n_text = L10N_FILE.read_text(encoding="utf-8")
    language_selection_text = LANGUAGE_SELECTION_VIEW.read_text(encoding="utf-8")

    assert '"Språk"' in l10n_text
    assert '"Velg språk"' in l10n_text
    assert '"Spraak"' not in l10n_text
    assert "let layoutWidth = min(min(renderWidth, deviceWidth), 500)" in language_selection_text
    assert "let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))" in language_selection_text
    assert "let topSpacing = max(renderHeight * 0.16, geo.safeAreaInsets.top + 28.0)" in language_selection_text
    assert "let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))" in language_selection_text
    assert "ScrollView(.vertical, showsIndicators: false)" in language_selection_text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in language_selection_text
    assert ".clipped()" in language_selection_text
    assert ".frame(width: contentWidth, alignment: .center)" in language_selection_text
    assert '"Velg spraak"' not in l10n_text
    assert "Norsk språk & coach" in language_selection_text
    assert "Norsk spraak & coach" not in language_selection_text
    assert "CoachiTheme.borderSubtle.opacity(0.36)" in language_selection_text
