from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONBOARDING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "OnboardingContainerView.swift"
)
INTRO_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "FeaturesPageView.swift"
)
APP_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "AppViewModel.swift"
)


def _onboarding_text() -> str:
    return ONBOARDING_VIEW.read_text(encoding="utf-8")


def _intro_text() -> str:
    return INTRO_VIEW.read_text(encoding="utf-8")


def _app_viewmodel_text() -> str:
    return APP_VIEW_MODEL.read_text(encoding="utf-8")


def test_onboarding_includes_full_profile_and_hr_steps() -> None:
    text = _onboarding_text()
    guided_block = text.split("private var guidedOnboardingSteps: [OnboardingStep] {", 1)[1].split("private var showsGuidedProgress", 1)[0]
    assert "case birthAndGender" in text
    assert "case bodyMetrics" in text
    assert "case maxHeartRate" in text
    assert "case restingHeartRate" in text
    assert "case enduranceHabits" in text
    assert "case frequencyAndDuration" in text
    assert "case summary" in text
    assert "case result" in text
    assert "case noSensorFallback" in text
    assert "case watchConnectedOffer" in text
    assert "case notificationPermission" in text
    assert "OnboardingFlowProgressView(" in text
    assert "Step \\(current) of \\(total)" in text
    assert ".identity," not in guided_block
    assert ".features," not in guided_block
    assert ".birthAndGender," in guided_block
    assert ".notificationPermission," in guided_block
    assert ".dataPurpose," not in guided_block
    assert "steps.insert(.frequencyAndDuration, at: 5)" in guided_block
    assert "steps.insert(.watchConnectedOffer, at: steps.count - 1)" in guided_block
    assert "if formState.doesEnduranceTraining" in guided_block


def test_post_auth_explainer_starts_with_personalized_hello_page() -> None:
    text = _intro_text()
    post_auth_block = text.split("private func postAuthPages(displayName: String) -> [IntroStoryPage] {", 1)[1].split("private var showcasePrimaryTitle", 1)[0]
    assert "let greeting = displayName.isEmpty" in text
    assert 'titleNo: greeting' in post_auth_block
    assert 'bodyNo: "La meg først forklare hvordan vi kan hjelpe deg."' in post_auth_block
    assert post_auth_block.count('bodyNo: ""') == 4
    assert 'imageName: "IntroStory1"' in post_auth_block
    assert post_auth_block.count("IntroStoryPage(") == 5
    assert 'titleNo: "Jeg guider deg live med pulssoner"' in post_auth_block
    assert 'titleNo: "Jeg motiverer og tilpasser økten dynamisk"' in post_auth_block
    assert 'titleNo: "Du får en CoachScore etter hver økt"' in post_auth_block
    assert 'titleNo: "Etter økten kan vi snakke live"' in post_auth_block
    # Welcome uses .intro (bg-image carousel, 6s auto-advance)
    welcome_block = _onboarding_text().split("case .welcome:", 1)[1].split("case .language:", 1)[0]
    assert "mode: .intro" in welcome_block
    # Features uses .postAuthExplainer after identity
    assert 'case postAuthExplainer(displayName: String)' in text


def test_onboarding_routes_to_profile_completion_path() -> None:
    text = _onboarding_text()
    assert "@State private var authMode: AuthFlowMode = .register" in text
    assert "primaryTitle: L10n.register" in text
    assert 'secondaryTitle: L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account"' in text
    assert "authMode = .register" in text
    assert "authMode = .login" in text
    assert "AuthView(mode: authMode)" in text
    assert "move(to: .identity)" in text
    assert "} onContinueWithoutAccount: {" in text
    assert "onBack: { move(to: .auth) }" in text
    assert "onContinue: { move(to: .features) }" in text
    assert "onSecondary: { move(to: .identity) }" in text
    assert "onPrimary: { move(to: .birthAndGender) }" in text
    assert "onBack: { move(to: .features) }" in text
    assert "onContinue: { move(to: nextStepAfterEnduranceHabits) }" in text
    assert "private var nextStepAfterEnduranceHabits: OnboardingStep" in text
    assert "private var summaryBackStep: OnboardingStep" in text
    assert "onContinue: { move(to: .sensorConnect) }" in text
    assert "onBack: { move(to: summaryBackStep) }" in text
    assert "onContinue: { watchConnected in" in text
    assert "if !subscriptionManager.hasPremiumAccess {" in text
    assert "notificationBackStep = .watchConnectedOffer" in text
    assert "move(to: .watchConnectedOffer)" in text
    assert "notificationBackStep = .sensorConnect" in text
    assert "move(to: .notificationPermission)" in text
    assert "case .dataPurpose:" not in text
    assert "let profileDraft = formState.toDraft(" in text
    assert "appViewModel.completeOnboarding(profile: profileDraft)" in text


def test_watch_connected_onboarding_offer_reuses_existing_paywall_path() -> None:
    text = _onboarding_text()
    assert "private struct WatchConnectedPremiumOfferStepView: View" in text
    assert 'title: isNorwegian ? "Klokken er klar" : "Your watch is ready"' in text
    assert 'primaryTitle: isNorwegian ? "Fortsett med Gratis" : "Continue with Free"' in text
    assert 'Text(isNorwegian ? "Gratis \\(trialDays)-dagers prøveperiode" : "Free \\(trialDays)-day trial")' in text
    assert 'Text(isNorwegian ? "Start gratis prøveperiode" : "Start free trial")' in text
    assert "PaywallView(context: .general)" in text


def test_app_viewmodel_persists_backend_relevant_profile_keys() -> None:
    text = _app_viewmodel_text()
    assert "func completeOnboarding(profile: OnboardingProfileDraft)" in text
    assert 'defaults.set(profile.hrMax, forKey: "hr_max")' in text
    assert 'defaults.set(profile.restingHR, forKey: "resting_hr")' in text
    assert 'defaults.set(profile.age, forKey: "user_age")' in text
    assert 'defaults.set(profile.trainingLevel, forKey: "training_level")' in text
    assert 'defaults.set(profile.languageCode, forKey: "app_language")' in text


def test_app_viewmodel_retains_onboarding_optional_future_keys() -> None:
    text = _app_viewmodel_text()
    assert 'defaults.set(profile.heightCm, forKey: "user_height_cm")' in text
    assert 'defaults.set(profile.weightKg, forKey: "user_weight_kg")' in text
    assert 'defaults.set(profile.gender, forKey: "user_gender")' in text
    assert 'defaults.set(profile.notificationsOptIn, forKey: "notifications_opt_in")' in text


def test_reset_onboarding_clears_profile_and_hr_defaults() -> None:
    text = _app_viewmodel_text()
    assert 'keysToClear = [' in text
    assert '"hr_max"' in text
    assert '"resting_hr"' in text
    assert '"user_age"' in text
    assert 'keysToClear.forEach { defaults.removeObject(forKey: $0) }' in text


def test_onboarding_explains_hr_endurance_and_intensity_in_coachi_copy() -> None:
    text = _onboarding_text()
    assert "Makspuls er det høyeste antallet hjerteslag per minutt du kan nå under hard trening." in text
    assert "Max HR is the highest number of heart beats per minute your heart can reach during intense exercise." in text
    assert "Hvilepuls er hvor mange ganger hjertet ditt slår per minutt når du er avslappet og ikke trener." in text
    assert "Resting HR is how many times your heart beats per minute when you are relaxed and not exercising." in text
    assert "Hva er utholdenhetstrening?" in text
    assert "✅ 🏃 Løping" in text
    assert "✅ 🚶 Gåturer" in text
    assert "✅ 🚴 Sykling" in text
    assert "✅ 🏊 Svømming" in text
    assert "✅ 💃 Dansing" in text
    assert "✅ 🤸 Aerobic" in text
    assert "❌ 🧘 Yoga" in text
    assert "❌ 🏋️ Styrketrening" in text
    assert "❌ 🙆 Pilates" in text
    assert "Du blir bare lett andpusten og kan holde samme tempo lenge uten problemer." in text
    assert "Du puster raskere og kjenner at du jobber, men du har fortsatt kontroll og kan holde på en god stund." in text
    assert "Du blir tydelig andpusten, må jobbe hardt og klarer bare å holde intensiteten i korte drag." in text
    assert "Tap any value if you want to update it before continuing." in text
    assert "onEditField: { field in" in text
    assert "move(to: field.targetStep(doesEnduranceTraining: formState.doesEnduranceTraining))" in text
