//
//  AuthManager.swift
//  TreningsCoach
//
//  Manages authentication state with Apple and passwordless email sign-in
//  Stores JWT token in Keychain, communicates with backend /auth/* endpoints
//

import Foundation
import SwiftUI
import AuthenticationServices
import UIKit
import CryptoKit
import OSLog

private let authLogger = Logger(
    subsystem: Bundle.main.bundleIdentifier ?? "com.coachi.app",
    category: "AuthManager"
)

@MainActor
class AuthManager: ObservableObject {
    static let shared = AuthManager()

    // MARK: - Published State

    @Published var isAuthenticated = false
    @Published var currentUser: UserProfile?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var productFlags: ProductFlags = .launchDefaults

    // MARK: - Token

    var authToken: String? {
        currentAccessToken()
    }

    func currentAccessToken() -> String? {
        if let access = KeychainHelper.readString(key: KeychainHelper.accessTokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !access.isEmpty {
            return access
        }
        return KeychainHelper.readString(key: KeychainHelper.tokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    func currentRefreshToken() -> String? {
        guard let refresh = KeychainHelper.readString(key: KeychainHelper.refreshTokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !refresh.isEmpty else {
            return nil
        }
        return refresh
    }

    func hasUsableSession() -> Bool {
        if let token = currentAccessToken(), !token.isEmpty {
            if let expiresAt = expiryTimestamp(for: KeychainHelper.accessTokenExpiresAtKey) {
                if !isExpired(expiresAt) {
                    return true
                }
            } else {
                return true
            }
        }

        if let refresh = currentRefreshToken(), !refresh.isEmpty {
            if let expiresAt = expiryTimestamp(for: KeychainHelper.refreshTokenExpiresAtKey) {
                return !isExpired(expiresAt)
            }
            return true
        }

        return false
    }

    // MARK: - Init

    init() {
        Task {
            await fetchRuntimeFlags()
        }

        // Check if we have a stored token on launch
        if hasUsableSession() {
            isAuthenticated = true
            // Fetch profile in background
            Task {
                await fetchProfile()
            }
        }
    }

    // MARK: - Google Sign-In

    func signInWithGoogle() async -> Bool {
        guard AppConfig.Auth.googleSignInFeatureEnabled else {
            markUnsupportedProvider(label: L10n.registerWithGoogle)
            return false
        }
        guard let clientID = AppConfig.Auth.googleClientID, !clientID.isEmpty else {
            errorMessage = "Google Sign-In is not configured."
            return false
        }
        guard AppConfig.Auth.googleRedirectScheme != nil else {
            errorMessage = "Google Sign-In callback URL is not configured."
            return false
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let idToken = try await performGoogleWebAuth(clientID: clientID)
            let response = try await sendAuthRequest(provider: "google", body: ["id_token": idToken])
            handleAuthSuccess(response)
            return true
        } catch {
            if !(error is CancellationError) {
                errorMessage = localizedAuthError(provider: "google", error: error)
            }
            return false
        }
    }

    /// Opens a Google OAuth consent screen via ASWebAuthenticationSession,
    /// exchanges the auth code for tokens, and returns the id_token.
    private func performGoogleWebAuth(clientID: String) async throws -> String {
        guard let callbackScheme = AppConfig.Auth.googleRedirectScheme else {
            throw APIError.serverError(message: "Google redirect scheme is not configured.")
        }

        let redirectURI = "\(callbackScheme):/oauthredirect"
        let nonce = UUID().uuidString
        let state = UUID().uuidString
        let codeVerifier = randomURLSafeString(length: 64)
        let codeChallenge = pkceCodeChallenge(for: codeVerifier)

        var components = URLComponents(string: "https://accounts.google.com/o/oauth2/v2/auth")!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: clientID),
            URLQueryItem(name: "redirect_uri", value: redirectURI),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "scope", value: "openid email profile"),
            URLQueryItem(name: "nonce", value: nonce),
            URLQueryItem(name: "state", value: state),
            URLQueryItem(name: "code_challenge", value: codeChallenge),
            URLQueryItem(name: "code_challenge_method", value: "S256"),
        ]

        guard let authURL = components.url else {
            throw APIError.invalidURL
        }

        let callbackURL: URL = try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(url: authURL, callbackURLScheme: callbackScheme) { url, error in
                if let error { continuation.resume(throwing: error); return }
                guard let url else { continuation.resume(throwing: APIError.invalidResponse); return }
                continuation.resume(returning: url)
            }
            session.prefersEphemeralWebBrowserSession = false
            session.presentationContextProvider = GoogleAuthPresentationContext.shared
            DispatchQueue.main.async { session.start() }
        }

        let callbackComponents = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false)
        if let callbackError = callbackComponents?
            .queryItems?.first(where: { $0.name == "error" })?.value {
            throw APIError.serverError(message: "Google sign-in failed: \(callbackError)")
        }

        let returnedState = callbackComponents?
            .queryItems?.first(where: { $0.name == "state" })?.value
        guard returnedState == state else {
            throw APIError.serverError(message: "Google sign-in state mismatch.")
        }

        guard let code = callbackComponents?
            .queryItems?.first(where: { $0.name == "code" })?.value else {
            throw APIError.serverError(message: "No authorization code received from Google.")
        }

        // Exchange code for tokens via Google token endpoint
        var tokenRequest = URLRequest(url: URL(string: "https://oauth2.googleapis.com/token")!)
        tokenRequest.httpMethod = "POST"
        tokenRequest.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        tokenRequest.httpBody = formEncodedData([
            URLQueryItem(name: "code", value: code),
            URLQueryItem(name: "client_id", value: clientID),
            URLQueryItem(name: "redirect_uri", value: redirectURI),
            URLQueryItem(name: "grant_type", value: "authorization_code"),
            URLQueryItem(name: "code_verifier", value: codeVerifier),
        ])

        let (data, _) = try await URLSession.shared.data(for: tokenRequest)
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let idToken = json["id_token"] as? String else {
            throw APIError.serverError(message: "Failed to exchange Google auth code for id_token.")
        }

        return idToken
    }

    private func formEncodedData(_ items: [URLQueryItem]) -> Data? {
        var components = URLComponents()
        components.queryItems = items
        let encoded = components.percentEncodedQuery ?? ""
        return encoded.data(using: .utf8)
    }

    private func randomURLSafeString(length: Int) -> String {
        let raw = UUID().uuidString.replacingOccurrences(of: "-", with: "") + UUID().uuidString.replacingOccurrences(of: "-", with: "")
        return String(raw.prefix(max(43, length)))
    }

    private func pkceCodeChallenge(for verifier: String) -> String {
        let challenge = SHA256.hash(data: Data(verifier.utf8))
        let encoded = Data(challenge).base64EncodedString()
        return encoded
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }

    // MARK: - Email Sign-In

    func requestEmailSignInCode(email rawEmail: String) async -> Bool {
        guard AppConfig.Auth.emailSignInEnabled else {
            errorMessage = L10n.emailDeliveryUnavailable
            return false
        }

        let email = normalizedEmail(rawEmail)
        guard isValidEmail(email) else {
            errorMessage = L10n.emailAddressInvalid
            return false
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            _ = try await sendEmailCodeRequest(email: email)
            return true
        } catch {
            errorMessage = localizedEmailRequestError(error)
            return false
        }
    }

    func signInWithEmail(email rawEmail: String, code rawCode: String) async -> Bool {
        guard AppConfig.Auth.emailSignInEnabled else {
            errorMessage = L10n.emailDeliveryUnavailable
            return false
        }

        let email = normalizedEmail(rawEmail)
        let code = rawCode.trimmingCharacters(in: .whitespacesAndNewlines)
        guard isValidEmail(email) else {
            errorMessage = L10n.emailAddressInvalid
            return false
        }
        guard code.count == 6 else {
            errorMessage = L10n.emailCodeInvalid
            return false
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response = try await sendEmailVerifyRequest(email: email, code: code)
            handleAuthSuccess(response)
            return true
        } catch {
            errorMessage = localizedEmailVerifyError(error)
            return false
        }
    }

    // MARK: - Apple Sign-In

    func signInWithApple() async -> Bool {
        guard AppConfig.Auth.appleSignInEnabled else {
            errorMessage = L10n.appleSignInFailedTryAgain
            return false
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let credential = try await requestAppleCredential()
            var body: [String: String] = [
                "identity_token": credential.identityToken
            ]
            if let authorizationCode = credential.authorizationCode, !authorizationCode.isEmpty {
                body["authorization_code"] = authorizationCode
            }
            if let email = credential.email, !email.isEmpty {
                body["email"] = email
            }
            if let fullName = credential.fullName, !fullName.isEmpty {
                body["full_name"] = fullName
            }

            let authResponse = try await sendAuthRequest(
                provider: "apple",
                body: body
            )
            handleAuthSuccess(authResponse)
            return true
        } catch let appleError as ASAuthorizationError {
            if appleError.code != .canceled {
                errorMessage = L10n.appleSignInFailedTryAgain
            }
            return false
        } catch {
            errorMessage = localizedAuthError(provider: "apple", error: error)
            return false
        }
    }

    // MARK: - Facebook Sign-In

    func signInWithFacebook() async {
        markUnsupportedProvider(label: L10n.signInWithFacebook)
    }

    // MARK: - Vipps Sign-In

    func signInWithVipps() async {
        markUnsupportedProvider(label: L10n.signInWithVipps)
    }

    // MARK: - Sign Out

    func signOut() {
        let refreshToken = currentRefreshToken()
        transitionToGuestMode()
        authLogger.notice("AUTH_SIGN_OUT action=guest_mode")

        guard let refreshToken, !refreshToken.isEmpty else { return }
        Task {
            await BackendAPIService.shared.logout(refreshToken: refreshToken)
        }
    }

    func deleteAccount() async -> String? {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            try await BackendAPIService.shared.deleteCurrentAccount()
            transitionToGuestMode()
            authLogger.notice("AUTH_DELETE success=true action=guest_mode")
            return nil
        } catch {
            let message: String
            if let apiError = error as? APIError,
               case .serverError(let backendMessage) = apiError {
                message = backendMessage
            } else {
                message = "Could not delete account. Please try again."
            }
            errorMessage = message
            authLogger.error("AUTH_DELETE success=false")
            return message
        }
    }

    // MARK: - Profile

    func fetchProfile() async {
        guard let token = authToken, !token.isEmpty else { return }

        do {
            let (data, response) = try await performProfileRequest(token: token)
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                let refreshed = await BackendAPIService.shared.refreshAuthTokenIfNeeded()
                guard refreshed,
                      let refreshedToken = authToken,
                      !refreshedToken.isEmpty
                else {
                    // Only sign out if tokens were explicitly rejected (cleared by refresh).
                    // Network failures leave tokens in Keychain — keep session alive
                    // so the next app launch can retry when backend is reachable.
                    if currentRefreshToken() == nil {
                        signOut()
                    } else {
                        authLogger.notice("AUTH_PROFILE refresh_failed=network keeping_session=true")
                    }
                    return
                }

                let (retryData, retryResponse) = try await performProfileRequest(token: refreshedToken)
                guard let retryHTTP = retryResponse as? HTTPURLResponse,
                      retryHTTP.statusCode == 200 else {
                    // Only sign out on definitive auth rejection, not transient server errors
                    if let retryHTTP = retryResponse as? HTTPURLResponse,
                       [401, 403, 404].contains(retryHTTP.statusCode) {
                        signOut()
                    }
                    return
                }
                try updateProfileFromResponseData(retryData)
                return
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 404 {
                    authLogger.notice("AUTH_PROFILE stale_session=true status=404 action=sign_out")
                    signOut()
                }
                return
            }

            try updateProfileFromResponseData(data)
        } catch {
            // Network timeout / connectivity — keep tokens, don't sign out
            authLogger.error("AUTH_PROFILE network_error=true")
        }
    }

    func updateProfile(language: AppLanguage? = nil, trainingLevel: TrainingLevel? = nil, persona: String? = nil) async {
        guard let token = authToken, !token.isEmpty else { return }

        var body: [String: String] = [:]
        if let lang = language { body["language"] = lang.rawValue }
        if let level = trainingLevel { body["training_level"] = level.rawValue }
        if let p = persona { body["preferred_persona"] = p }

        do {
            let payload = try JSONEncoder().encode(body)
            var (data, response) = try await performProfileUpdateRequest(token: token, payload: payload)
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                let refreshed = await BackendAPIService.shared.refreshAuthTokenIfNeeded()
                guard refreshed,
                      let refreshedToken = authToken,
                      !refreshedToken.isEmpty
                else {
                    if currentRefreshToken() == nil {
                        signOut()
                    } else {
                        authLogger.notice("AUTH_PROFILE_UPDATE refresh_failed=network keeping_session=true")
                    }
                    return
                }
                (data, response) = try await performProfileUpdateRequest(token: refreshedToken, payload: payload)
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 404 {
                    authLogger.notice("AUTH_PROFILE_UPDATE stale_session=true status=404 action=sign_out")
                    signOut()
                }
                return
            }

            let profileResponse = try JSONDecoder().decode(ProfileResponse.self, from: data)
            currentUser = profileResponse.user

            // Keep backend profile snapshot fresh for coaching runtime.
            let defaults = UserDefaults.standard
            let snapshot = BackendUserProfilePayload(
                name: defaults.string(forKey: "user_display_name"),
                sex: defaults.string(forKey: "user_gender"),
                age: defaults.object(forKey: "user_age") as? Int,
                heightCm: defaults.object(forKey: "user_height_cm") as? Int,
                weightKg: defaults.object(forKey: "user_weight_kg") as? Int,
                maxHrBpm: defaults.object(forKey: "hr_max") as? Int,
                restingHrBpm: defaults.object(forKey: "resting_hr") as? Int,
                profileUpdatedAt: ISO8601DateFormatter().string(from: Date())
            )
            try? await BackendAPIService.shared.upsertUserProfile(snapshot)
            authLogger.debug("PROFILE_UPSERT reason=profile_edit")

        } catch {
            authLogger.error("PROFILE_UPDATE success=false")
        }
    }

    func fetchRuntimeFlags() async {
        do {
            let runtime = try await BackendAPIService.shared.fetchAppRuntime()
            productFlags = runtime.productFlags
        } catch {
            authLogger.error("RUNTIME_FLAGS fetch_failed=true")
        }
    }

    // MARK: - Private

    private func sendAuthRequest(provider: String, body: [String: String]) async throws -> AuthResponse {
        let url = URL(string: "\(AppConfig.backendURL)/auth/\(provider)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            let errorResp = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            let backendMessage = errorResp?.error ?? "Auth failed"
            if provider == "apple" {
                throw APIError.serverError(message: localizedAppleBackendError(errorResponse: errorResp, fallback: backendMessage))
            }
            throw APIError.serverError(message: backendMessage)
        }

        return try JSONDecoder().decode(AuthResponse.self, from: data)
    }

    private func requestAppleCredential() async throws -> AppleAuthorizationPayload {
        let provider = ASAuthorizationAppleIDProvider()
        let request = provider.createRequest()
        request.requestedScopes = [.fullName, .email]

        let controller = ASAuthorizationController(authorizationRequests: [request])
        let coordinator = AppleSignInCoordinator()
        controller.delegate = coordinator
        controller.presentationContextProvider = coordinator
        return try await coordinator.perform(controller: controller)
    }

    private func sendEmailCodeRequest(email: String) async throws -> EmailCodeRequestResponse {
        let url = URL(string: "\(AppConfig.backendURL)/auth/email/request-code")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode([
            "email": email,
            "language": L10n.current.rawValue,
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard httpResponse.statusCode == 200 else {
            let errorResp = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw APIError.serverError(message: localizedEmailBackendError(errorResponse: errorResp))
        }

        return try JSONDecoder().decode(EmailCodeRequestResponse.self, from: data)
    }

    private func sendEmailVerifyRequest(email: String, code: String) async throws -> AuthResponse {
        let url = URL(string: "\(AppConfig.backendURL)/auth/email/verify")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode([
            "email": email,
            "code": code,
        ])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard httpResponse.statusCode == 200 else {
            let errorResp = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw APIError.serverError(message: localizedEmailBackendError(errorResponse: errorResp))
        }

        return try JSONDecoder().decode(AuthResponse.self, from: data)
    }

    private func localizedAuthError(provider: String, error: Error) -> String {
        if provider == "apple" {
            if let apiError = error as? APIError {
                switch apiError {
                case .serverError(let message):
                    return message
                default:
                    return L10n.appleSignInFailedTryAgain
                }
            }
            return L10n.appleSignInFailedTryAgain
        }
        return error.localizedDescription
    }

    private func localizedAppleBackendError(errorResponse: ErrorResponse?, fallback: String) -> String {
        switch errorResponse?.errorCode {
        case "apple_token_expired":
            return L10n.appleTokenExpired
        case "apple_audience_mismatch", "apple_identity_unverified":
            return L10n.appleIdentityVerifyFailed
        case "apple_token_invalid", "apple_missing_identity_token", "apple_auth_internal_error":
            return L10n.appleSignInFailedTryAgain
        default:
            break
        }

        if errorResponse?.error.localizedCaseInsensitiveContains("verify Apple identity") == true {
            return L10n.appleIdentityVerifyFailed
        }
        if errorResponse?.error.localizedCaseInsensitiveContains("expired") == true {
            return L10n.appleTokenExpired
        }
        return fallback.isEmpty ? L10n.appleSignInFailedTryAgain : fallback
    }

    private func localizedEmailBackendError(errorResponse: ErrorResponse?) -> String {
        switch errorResponse?.errorCode {
        case "email_invalid":
            return L10n.emailAddressInvalid
        case "email_code_invalid":
            return L10n.emailCodeInvalid
        case "email_code_expired":
            return L10n.emailCodeExpired
        case "email_code_mismatch":
            return L10n.emailCodeMismatch
        case "email_delivery_unavailable":
            return L10n.emailDeliveryUnavailable
        default:
            return errorResponse?.error ?? L10n.emailCodeVerifyFailed
        }
    }

    private func localizedEmailRequestError(_ error: Error) -> String {
        if let apiError = error as? APIError,
           case .serverError(let message) = apiError {
            return message
        }
        return L10n.emailCodeRequestFailed
    }

    private func localizedEmailVerifyError(_ error: Error) -> String {
        if let apiError = error as? APIError,
           case .serverError(let message) = apiError {
            return message
        }
        return L10n.emailCodeVerifyFailed
    }

    private func markUnsupportedProvider(label: String) {
        isLoading = false
        errorMessage = "\(label): \(L10n.comingSoon)"
    }

    private func handleAuthSuccess(_ response: AuthResponse) {
        saveTokenBundle(response)

        // Update state
        currentUser = response.user
        isAuthenticated = true

        // Sync language
        L10n.set(response.user.language)

        // First-time Spotify prompt after account creation/sign-in (one-time per install)
        let defaults = UserDefaults.standard
        if !defaults.bool(forKey: "spotify_prompt_seen") {
            defaults.set(true, forKey: "spotify_prompt_pending")
        }

        Task {
            await fetchRuntimeFlags()
        }

        authLogger.notice("AUTH_SUCCESS session_established=true")
    }

    private func performProfileRequest(token: String) async throws -> (Data, URLResponse) {
        let url = URL(string: "\(AppConfig.backendURL)/auth/me")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return try await URLSession.shared.data(for: request)
    }

    private func performProfileUpdateRequest(token: String, payload: Data) async throws -> (Data, URLResponse) {
        let url = URL(string: "\(AppConfig.backendURL)/auth/me")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = payload
        return try await URLSession.shared.data(for: request)
    }

    private func updateProfileFromResponseData(_ data: Data) throws {
        let profileResponse = try JSONDecoder().decode(ProfileResponse.self, from: data)
        currentUser = profileResponse.user
        isAuthenticated = hasUsableSession()
        L10n.set(profileResponse.user.language)
    }

    private func saveTokenBundle(_ response: AuthResponse) {
        let access = response.resolvedAccessToken
        guard !access.isEmpty else { return }

        _ = KeychainHelper.save(key: KeychainHelper.tokenKey, string: access)
        _ = KeychainHelper.save(key: KeychainHelper.accessTokenKey, string: access)

        if let refresh = response.refreshToken?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !refresh.isEmpty {
            _ = KeychainHelper.save(key: KeychainHelper.refreshTokenKey, string: refresh)
        }

        if let expiresIn = response.expiresIn {
            let expiresAt = Date().addingTimeInterval(TimeInterval(max(0, expiresIn))).timeIntervalSince1970
            _ = KeychainHelper.save(key: KeychainHelper.accessTokenExpiresAtKey, string: String(format: "%.3f", expiresAt))
        }

        if let refreshExpiresIn = response.refreshExpiresIn {
            let refreshExpiresAt = Date().addingTimeInterval(TimeInterval(max(0, refreshExpiresIn))).timeIntervalSince1970
            _ = KeychainHelper.save(key: KeychainHelper.refreshTokenExpiresAtKey, string: String(format: "%.3f", refreshExpiresAt))
        }
    }

    private func clearStoredTokens() {
        KeychainHelper.delete(key: KeychainHelper.tokenKey)
        KeychainHelper.delete(key: KeychainHelper.accessTokenKey)
        KeychainHelper.delete(key: KeychainHelper.refreshTokenKey)
        KeychainHelper.delete(key: KeychainHelper.accessTokenExpiresAtKey)
        KeychainHelper.delete(key: KeychainHelper.refreshTokenExpiresAtKey)
    }

    private func transitionToGuestMode() {
        clearStoredTokens()
        isAuthenticated = false
        currentUser = nil
        errorMessage = nil
    }

    private func expiryTimestamp(for key: String) -> TimeInterval? {
        guard let raw = KeychainHelper.readString(key: key)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            let expiresAt = Double(raw) else {
            return nil
        }
        return expiresAt
    }

    private func isExpired(_ expiresAt: TimeInterval) -> Bool {
        Date().timeIntervalSince1970 >= expiresAt
    }

    private func normalizedEmail(_ rawEmail: String) -> String {
        rawEmail.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private func isValidEmail(_ email: String) -> Bool {
        let trimmed = normalizedEmail(email)
        guard let atIndex = trimmed.firstIndex(of: "@") else { return false }
        let local = trimmed[..<atIndex]
        let domain = trimmed[trimmed.index(after: atIndex)...]
        return !local.isEmpty && domain.contains(".")
    }
}

private struct AppleAuthorizationPayload {
    let identityToken: String
    let authorizationCode: String?
    let email: String?
    let fullName: String?
}

private struct EmailCodeRequestResponse: Codable {
    let success: Bool
    let codeSent: Bool
    let expiresIn: Int?

    enum CodingKeys: String, CodingKey {
        case success
        case codeSent = "code_sent"
        case expiresIn = "expires_in"
    }
}

private final class AppleSignInCoordinator: NSObject, ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
    private var continuation: CheckedContinuation<AppleAuthorizationPayload, Error>?

    func perform(controller: ASAuthorizationController) async throws -> AppleAuthorizationPayload {
        try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            controller.performRequests()
        }
    }

    func presentationAnchor(for _: ASAuthorizationController) -> ASPresentationAnchor {
        guard let scene = UIApplication.shared.connectedScenes
            .compactMap({ $0 as? UIWindowScene })
            .first,
            let window = scene.windows.first(where: { $0.isKeyWindow })
        else {
            return ASPresentationAnchor(frame: .zero)
        }
        return window
    }

    func authorizationController(
        controller _: ASAuthorizationController,
        didCompleteWithAuthorization authorization: ASAuthorization
    ) {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            continuation?.resume(throwing: NSError(domain: "AuthManager", code: 9001, userInfo: [NSLocalizedDescriptionKey: "Invalid Apple credential"]))
            continuation = nil
            return
        }

        guard let identityTokenData = credential.identityToken,
              let identityToken = String(data: identityTokenData, encoding: .utf8),
              !identityToken.isEmpty
        else {
            continuation?.resume(throwing: NSError(domain: "AuthManager", code: 9002, userInfo: [NSLocalizedDescriptionKey: "Missing Apple identity token"]))
            continuation = nil
            return
        }

        let authorizationCode: String?
        if let codeData = credential.authorizationCode,
           let value = String(data: codeData, encoding: .utf8),
           !value.isEmpty {
            authorizationCode = value
        } else {
            authorizationCode = nil
        }

        let formatter = PersonNameComponentsFormatter()
        let fullNameString: String?
        if let components = credential.fullName {
            let formatted = formatter.string(from: components).trimmingCharacters(in: .whitespacesAndNewlines)
            fullNameString = formatted.isEmpty ? nil : formatted
        } else {
            fullNameString = nil
        }

        let payload = AppleAuthorizationPayload(
            identityToken: identityToken,
            authorizationCode: authorizationCode,
            email: credential.email,
            fullName: fullNameString
        )
        continuation?.resume(returning: payload)
        continuation = nil
    }

    func authorizationController(
        controller _: ASAuthorizationController,
        didCompleteWithError error: Error
    ) {
        continuation?.resume(throwing: error)
        continuation = nil
    }
}

// MARK: - Google Auth Presentation Context

private final class GoogleAuthPresentationContext: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let shared = GoogleAuthPresentationContext()

    func presentationAnchor(for _: ASWebAuthenticationSession) -> ASPresentationAnchor {
        guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let window = scene.windows.first(where: \.isKeyWindow) ?? scene.windows.first else {
            return ASPresentationAnchor()
        }
        return window
    }
}
