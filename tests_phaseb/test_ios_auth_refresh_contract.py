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
    assert 'case profileName = "profile_name"' in text
    assert "var resolvedDisplayName: String?" in text
    assert "var resolvedAccessToken: String {" in text


def test_auth_manager_persists_and_clears_full_token_bundle() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "import OSLog" in text
    assert "Logger(" in text
    assert "print(" not in text
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
    assert 'AUTH_SIGN_OUT action=guest_mode' in text
    assert 'AUTH_SUCCESS session_established=true' in text
    assert "applyAuthenticatedProfile(response.user)" in text
    assert "applyAuthenticatedProfile(profileResponse.user)" in text
    assert "private func applyAuthenticatedProfile(_ user: UserProfile)" in text
    assert "private func persistIdentityDefaults(from user: UserProfile)" in text
    assert "private func persistResolvedName(_ fullName: String, defaults: UserDefaults = .standard)" in text
    assert 'defaults.set(trimmed, forKey: "user_display_name")' in text
    assert 'defaults.set(first, forKey: "user_first_name")' in text
    assert 'defaults.set(parts.dropFirst().joined(separator: " "), forKey: "user_last_name")' in text
    assert "signOut()" in text
    assert 'UserDefaults.standard.removeObject(forKey: "has_completed_onboarding")' not in text


def test_backend_api_service_refreshes_and_retries_on_unauthorized() -> None:
    text = API.read_text(encoding="utf-8")
    assert "import OSLog" in text
    assert "Logger(" in text
    assert "print(" not in text
    assert "func refreshAuthTokenIfNeeded() async -> Bool" in text
    assert "func deleteCurrentAccount() async throws" in text
    assert '"\\(baseURL)/auth/me"' in text
    assert 'request.httpMethod = "DELETE"' in text
    assert '"\\(baseURL)/auth/refresh"' in text
    assert "private func dataWithAuthRetry(for request: URLRequest)" in text
    assert "let refreshed = await refreshAuthTokenIfNeeded()" in text
    assert "return try await session.data(for: retryRequest)" in text
    assert "private let backendAvailabilityQueue = DispatchQueue(label: \"BackendAPIService.availability\")" in text
    assert "private let backendUnavailableCooldownSeconds: TimeInterval = 20" in text
    assert "private func ensureBackendAvailable(path: String) throws" in text
    assert "private func markBackendUnavailableIfNeeded(error: Error, path: String)" in text
    assert "private func clearBackendUnavailableIfNeeded(path: String)" in text
    assert "private func isTransientBackendNetworkError(_ error: Error) -> Bool" in text
    assert "private func performRequestWithBackendAvailability(" in text
    assert "func fetchAuthenticatedProfile(token: String) async throws -> (Data, URLResponse)" in text
    assert "func updateAuthenticatedProfile(token: String, payload: Data) async throws -> (Data, URLResponse)" in text


def test_backend_api_service_guards_best_effort_and_primary_requests_during_backend_cooldown() -> None:
    text = API.read_text(encoding="utf-8")
    assert 'guard !shouldSkipBestEffortRequest(path: "/health") else { return }' in text
    assert 'performRequestWithBackendAvailability(request, path: "/health")' in text
    assert 'performRequestWithBackendAvailability(request, path: "/app/runtime")' in text
    assert 'path: "/coach/continuous"' in text
    assert 'path: "/coach/talk"' in text
    assert 'path: "/voice/session"' in text
    assert 'path: "/analytics/mobile"' in text
    assert 'path: "/voice/telemetry"' in text
    assert 'path: "/subscription/validate"' in text
    assert 'catch is BackendAvailabilityError {' in text


def test_backend_api_service_uses_matching_paths_for_analyze_and_continuous_requests() -> None:
    text = API.read_text(encoding="utf-8")
    analyze_block = text.split("func analyzeAudio(_ audioURL: URL) async throws -> BreathAnalysis {", 1)[1]
    analyze_block = analyze_block.split("func downloadVoiceAudio(", 1)[0]
    assert 'path: "/analyze"' in analyze_block

    continuous_block = text.split("func getContinuousCoachFeedback(", 1)[1]
    continuous_block = continuous_block.split("func talkToCoach(", 1)[0]
    assert 'path: "/coach/continuous"' in continuous_block
    assert 'path: "/coach/talk"' not in continuous_block


def test_subscription_validation_skips_without_any_auth_material() -> None:
    text = API.read_text(encoding="utf-8")
    assert "private func hasAuthMaterial() -> Bool {" in text
    validate_block = text.split("func validateSubscription(", 1)[1].split("// MARK: - Helper Methods", 1)[0]
    assert "guard hasAuthMaterial() else {" in validate_block
    assert 'backendLogger.notice("SUB_VALIDATE skipped reason=missing_auth_material")' in validate_block


def test_auth_view_gates_google_sign_in_when_provider_disabled() -> None:
    config_text = CONFIG_SWIFT.read_text(encoding="utf-8")
    view_text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "static var googleSignInEnabled: Bool" in config_text
    google_enabled_block = config_text.split("static var googleSignInEnabled: Bool", 1)[1].split("}", 1)[0]
    assert "googleSignInFeatureEnabled" in google_enabled_block
    assert "googleClientID != nil" in google_enabled_block
    assert "googleRedirectScheme != nil" in google_enabled_block
    assert "static var googleRedirectScheme: String?" in config_text
    assert 'stringInfoValue("GOOGLE_REVERSED_CLIENT_ID")' in config_text
    assert 'stringInfoValue("GOOGLE_CLIENT_ID") ?? stringInfoValue("GIDClientID")' in config_text
    assert "static var emailSignInEnabled: Bool" in config_text
    # AuthView now surfaces Google when the build flag is on, while runtime config is validated on tap.
    assert "if AppConfig.Auth.googleSignInFeatureEnabled {" in view_text
    assert "secondaryActionButton(" in view_text
    assert "title: L10n.continueWithoutAccount" in view_text
    assert "onContinueWithoutAccount()" in view_text
    assert "let mode: AuthFlowMode" in view_text
    assert "private var requiresAcceptedTerms: Bool {" in view_text
    assert "mode == .register" in view_text
    assert "mode == .login ? L10n.loginWithApple : L10n.registerWithApple" in view_text
    assert "mode == .login ? L10n.loginWithGoogle : L10n.registerWithGoogle" in view_text
    assert "mode == .login ? L10n.loginWithEmail" in view_text
    assert "guard hasAcceptedRequiredTerms else {" in view_text.split("private var googleButton: some View {", 1)[1]
    assert "let signedIn = await authManager.signInWithGoogle()" in view_text
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


def test_auth_manager_routes_profile_reads_and_updates_through_backend_api_service() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert 'try await BackendAPIService.shared.fetchAuthenticatedProfile(token: token)' in text
    assert 'try await BackendAPIService.shared.updateAuthenticatedProfile(token: token, payload: payload)' in text
    profile_helpers = text.split("private func performProfileRequest(token: String)", 1)[1]
    assert 'URLSession.shared.data(for: request)' not in profile_helpers.split("private func updateProfileFromResponseData", 1)[0]


def test_workout_view_model_surfaces_backend_backoff_status_line() -> None:
    view_model_text = WORKOUT_VM.read_text(encoding="utf-8")
    active_view_text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert "@Published var coachingStatusLine: String?" in view_model_text
    assert "private func applyCoachingFailureBackoff()" in view_model_text
    assert "private func isRetriableCoachingError(_ error: Error) -> Bool" in view_model_text
    assert "case .invalidURL, .invalidResponse, .downloadFailed, .networkError, .quotaExceeded:" in view_model_text
    assert "case .authenticationRequired, .invalidURL, .downloadFailed, .quotaExceeded:" in view_model_text
    assert "authManager.hasUsableSession()" in view_model_text
    assert "if let statusLine = viewModel.coachingStatusLine {" in active_view_text
