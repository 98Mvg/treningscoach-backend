from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KEYCHAIN = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "KeychainHelper.swift"
USER_PROFILE = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Models" / "UserProfile.swift"
AUTH_MANAGER = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "AuthManager.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"
CONFIG_SWIFT = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Config.swift"
AUTH_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "AuthView.swift"
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
ACTIVE_WORKOUT_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ActiveWorkoutView.swift"


def test_keychain_exposes_access_and_refresh_token_keys() -> None:
    text = KEYCHAIN.read_text(encoding="utf-8")
    assert 'static let accessTokenKey = "auth_access_token"' in text
    assert 'static let refreshTokenKey = "auth_refresh_token"' in text
    assert 'static let accessTokenExpiresAtKey = "auth_access_expires_at"' in text
    assert 'static let refreshTokenExpiresAtKey = "auth_refresh_expires_at"' in text


def test_auth_response_supports_refresh_token_bundle_fields() -> None:
    text = USER_PROFILE.read_text(encoding="utf-8")
    assert 'case accessToken = "access_token"' in text
    assert 'case refreshToken = "refresh_token"' in text
    assert 'case expiresIn = "expires_in"' in text
    assert 'case refreshExpiresIn = "refresh_expires_in"' in text
    assert "var resolvedAccessToken: String {" in text


def test_auth_manager_persists_and_clears_full_token_bundle() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "static let shared = AuthManager()" in text
    assert "func hasUsableSession() -> Bool {" in text
    assert "func currentRefreshToken() -> String? {" in text
    assert "private func saveTokenBundle(_ response: AuthResponse)" in text
    assert "private func clearStoredTokens()" in text
    assert "KeychainHelper.save(key: KeychainHelper.accessTokenKey" in text
    assert "KeychainHelper.save(key: KeychainHelper.refreshTokenKey" in text
    assert "KeychainHelper.delete(key: KeychainHelper.refreshTokenKey)" in text
    assert "let refreshed = await BackendAPIService.shared.refreshAuthTokenIfNeeded()" in text
    assert "await BackendAPIService.shared.logout(refreshToken: refreshToken)" in text
    assert "func deleteAccount() async -> String?" in text
    assert "transitionToGuestMode()" in text
    assert 'httpResponse.statusCode == 404' in text
    assert 'AUTH_PROFILE stale_session=true status=404 action=sign_out' in text
    assert 'AUTH_PROFILE_UPDATE stale_session=true status=404 action=sign_out' in text
    assert "signOut()" in text
    assert 'UserDefaults.standard.removeObject(forKey: "has_completed_onboarding")' not in text


def test_backend_api_service_refreshes_and_retries_on_unauthorized() -> None:
    text = API.read_text(encoding="utf-8")
    assert "func refreshAuthTokenIfNeeded() async -> Bool" in text
    assert "func deleteCurrentAccount() async throws" in text
    assert '"\\(baseURL)/auth/me"' in text
    assert 'request.httpMethod = "DELETE"' in text
    assert '"\\(baseURL)/auth/refresh"' in text
    assert "private func dataWithAuthRetry(for request: URLRequest)" in text
    assert "let refreshed = await refreshAuthTokenIfNeeded()" in text
    assert "return try await session.data(for: retryRequest)" in text


def test_auth_view_gates_google_sign_in_when_provider_disabled() -> None:
    config_text = CONFIG_SWIFT.read_text(encoding="utf-8")
    view_text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "static var googleSignInEnabled: Bool" in config_text
    # Google sign-in flag now reads from build config (googleSignInFeatureEnabled)
    assert "googleSignInFeatureEnabled" in config_text.split("static var googleSignInEnabled: Bool", 1)[1].split("}", 1)[0]
    assert "static var emailSignInEnabled: Bool" in config_text
    # AuthView now gates Google button behind the feature flag
    assert "if AppConfig.Auth.googleSignInEnabled {" in view_text
    assert "secondaryActionButton(" in view_text
    assert "title: L10n.continueWithoutAccount" in view_text
    assert "Text(L10n.signInLaterHint)" in view_text
    assert "Text(L10n.accountRequiredHint)" in view_text
    assert "authBenefitRow(icon: \"chart.line.uptrend.xyaxis\", text: L10n.authBenefitSaveHistory)" in view_text
    assert "authBenefitRow(icon: \"person.crop.circle.badge.checkmark\", text: L10n.authBenefitSyncProfile)" in view_text
    assert "authBenefitRow(icon: \"envelope.badge\", text: L10n.authBenefitAppleOrEmail)" in view_text
    assert "onContinueWithoutAccount()" in view_text
    assert "title: L10n.emailAddress" in view_text
    assert "title: L10n.emailCodeLabel" in view_text
    assert "await authManager.requestEmailSignInCode(email: normalizedEmail)" in view_text
    assert "await authManager.signInWithEmail(" in view_text


def test_auth_manager_supports_passwordless_email_sign_in() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "func requestEmailSignInCode(email rawEmail: String) async -> Bool" in text
    assert "func signInWithEmail(email rawEmail: String, code rawCode: String) async -> Bool" in text
    assert '"\\(AppConfig.backendURL)/auth/email/request-code"' in text
    assert '"\\(AppConfig.backendURL)/auth/email/verify"' in text
    assert "private func localizedEmailBackendError(errorResponse: ErrorResponse?) -> String" in text


def test_workout_view_model_surfaces_backend_backoff_status_line() -> None:
    view_model_text = WORKOUT_VM.read_text(encoding="utf-8")
    active_view_text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert "@Published var coachingStatusLine: String?" in view_model_text
    assert "private func applyCoachingFailureBackoff()" in view_model_text
    assert "private func isRetriableCoachingError(_ error: Error) -> Bool" in view_model_text
    assert "authManager.hasUsableSession()" in view_model_text
    assert "if let statusLine = viewModel.coachingStatusLine {" in active_view_text
