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
APP_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "AppViewModel.swift"
)


def _onboarding_text() -> str:
    return ONBOARDING_VIEW.read_text(encoding="utf-8")


def _app_viewmodel_text() -> str:
    return APP_VIEW_MODEL.read_text(encoding="utf-8")


def test_onboarding_includes_full_profile_and_hr_steps() -> None:
    text = _onboarding_text()
    assert "case birthAndGender" in text
    assert "case dataPurpose" in text
    assert "case bodyMetrics" in text
    assert "case maxHeartRate" in text
    assert "case restingHeartRate" in text
    assert "case enduranceHabits" in text
    assert "case frequencyAndDuration" in text
    assert "case summary" in text
    assert "case result" in text
    assert "case noSensorFallback" in text
    assert "case notificationPermission" in text
    assert "OnboardingFlowProgressView(" in text
    assert "Step \\(current) of \\(total)" in text


def test_data_purpose_step_becomes_personalized_hello_page() -> None:
    text = _onboarding_text()
    assert 'return "Hello! \\(displayName)"' in text
    assert '"Let me first explain what we can do for you."' in text
    assert 'Image("OnboardingBgOutdoor")' in text
    assert 'let textWidth = max(0.0, min(contentWidth, layoutWidth < 390 ? 288.0 : 328.0))' in text
    assert 'let controlsHeight = 74.0 + bottomInset + 24.0' in text
    assert '.frame(width: textWidth, alignment: .leading)' in text
    assert '.padding(.bottom, controlsHeight)' in text
    assert 'VStack {' in text
    assert 'Button(action: onContinue)' in text
    assert '.padding(.bottom, bottomInset)' in text
    assert 'Text(L10n.current == .no ? "Neste" : "Next")' in text
    assert 'mode: .postAuthExplainer(displayName: formState.displayName)' in text


def test_onboarding_routes_to_profile_completion_path() -> None:
    text = _onboarding_text()
    assert "primaryTitle: L10n.register" in text
    assert 'secondaryTitle: L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account"' in text
    assert "move(to: .identity)" in text
    assert "} onContinueWithoutAccount: {" in text
    assert "onBack: { move(to: .auth) }" in text
    assert "onContinue: { move(to: .dataPurpose) }" in text
    assert "onContinue: { move(to: .features) }" in text
    assert "onPrimary: { move(to: .birthAndGender) }" in text
    assert "onBack: { move(to: .features) }" in text
    assert "onContinue: { move(to: .sensorConnect) }" in text
    assert "move(to: .notificationPermission)" in text
    assert "let profileDraft = formState.toDraft(" in text
    assert "appViewModel.completeOnboarding(profile: profileDraft)" in text


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
