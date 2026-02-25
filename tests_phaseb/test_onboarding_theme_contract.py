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
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert ".scrollBounceBehavior(.basedOnSize, axes: .vertical)" in text
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
    assert 'imageName: "IntroStory1"' in text
    assert 'imageName: "IntroStory2"' in text
    assert 'imageName: "IntroStory3"' in text
    assert 'imageName: "IntroStory4"' in text
    assert 'Text(L10n.current == .no ? "Registrer deg" : "Register")' in text
    assert 'Text(L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account")' in text
    assert "Circle()" in text
    assert ".scaledToFill()" in text
    assert "showsCoachScoreCard" in text
    assert "activePage" in text
    assert "DragGesture(minimumDistance: 24)" in text
    assert "if horizontal < 0 {" in text
    assert "currentPage += 1" in text
    assert "currentPage -= 1" in text
    assert "@State private var autoAdvanceTask: Task<Void, Never>?" in text
    assert "Task.sleep(nanoseconds: 7_000_000_000)" in text
    assert "La coachen hjelpe deg holde riktig puls" in text
    assert "score: 100" in text


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
    assert ".frame(width: layoutWidth, height: renderHeight)" in text
    assert ".frame(maxWidth: .infinity, alignment: .top)" in text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in text
    assert ".frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)" in text


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


def test_intro_only_ignores_vertical_safe_areas() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    assert ".ignoresSafeArea(edges: [.top, .bottom])" in text
    assert ".ignoresSafeArea()" not in text


def test_intro_layout_places_indicator_above_register_cta() -> None:
    text = INTRO_VIEW.read_text(encoding="utf-8")
    dots_idx = text.index("HStack(spacing: 10) {")
    register_idx = text.index("Button(action: onRegister)")
    assert dots_idx < register_idx
    assert ".padding(.top, max(14, geo.safeAreaInsets.top + 8))" not in text


def test_auth_layout_clamps_width_for_all_iphone_sizes() -> None:
    text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "let layoutWidth = min(min(renderWidth, deviceWidth), 500)" in text
    assert "let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))" in text
    assert "let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))" in text
    assert "Spacer().frame(height: bottomInset)" in text
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert ".scrollBounceBehavior(.basedOnSize, axes: .vertical)" in text
    assert ".frame(width: layoutWidth, height: renderHeight, alignment: .top)" in text
    assert ".clipped()" in text


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


def test_profile_and_settings_do_not_expose_technical_provider_details() -> None:
    profile_text = PROFILE_VIEW.read_text(encoding="utf-8")
    settings_text = SETTINGS_VIEW.read_text(encoding="utf-8")

    assert "ElevenLabs" not in profile_text
    assert "L10n.coachVoice" not in profile_text
    assert "ElevenLabs" not in settings_text
    assert 'title: "Backend"' not in settings_text
    assert "AppConfig.backendURL" not in settings_text


def test_norwegian_language_strings_use_sprak() -> None:
    l10n_text = L10N_FILE.read_text(encoding="utf-8")
    language_selection_text = LANGUAGE_SELECTION_VIEW.read_text(encoding="utf-8")

    assert '"Språk"' in l10n_text
    assert '"Velg språk"' in l10n_text
    assert '"Spraak"' not in l10n_text
    assert '"Velg spraak"' not in l10n_text
    assert "Norsk språk & coach" in language_selection_text
    assert "Norsk spraak & coach" not in language_selection_text
