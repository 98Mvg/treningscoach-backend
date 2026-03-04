//
//  AuthManager.swift
//  TreningsCoach
//
//  Manages authentication state with Apple, Google, Facebook, and Vipps
//  Stores JWT token in Keychain, communicates with backend /auth/* endpoints
//

import Foundation
import SwiftUI
import AuthenticationServices
import UIKit

@MainActor
class AuthManager: ObservableObject {
    // MARK: - Published State

    @Published var isAuthenticated = false
    @Published var currentUser: UserProfile?
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Token

    var authToken: String? {
        KeychainHelper.readString(key: KeychainHelper.tokenKey)
    }

    // MARK: - Init

    init() {
        // Check if we have a stored token on launch
        if let token = authToken, !token.isEmpty {
            isAuthenticated = true
            // Fetch profile in background
            Task {
                await fetchProfile()
            }
        }
    }

    // MARK: - Google Sign-In

    func signInWithGoogle() async {
        isLoading = true
        errorMessage = nil

        // TODO: Integrate Google Sign-In SDK
        // 1. GoogleSignIn.sharedInstance.signIn(withPresenting: rootVC)
        // 2. Get idToken from result.user.idToken?.tokenString
        // 3. Send to backend

        // Placeholder: simulate getting a Google ID token
        // Replace with actual Google Sign-In SDK integration
        let placeholderToken = "google_id_token_placeholder"

        do {
            let authResponse = try await sendAuthRequest(
                provider: "google",
                body: ["id_token": placeholderToken]
            )
            handleAuthSuccess(authResponse)
        } catch {
            errorMessage = "Google sign-in failed: \(error.localizedDescription)"
        }

        isLoading = false
    }

    // MARK: - Apple Sign-In

    func signInWithApple() async -> Bool {
        isLoading = true
        errorMessage = nil

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
        isLoading = true
        errorMessage = nil

        // TODO: Integrate Facebook Login SDK
        // 1. LoginManager().logIn(permissions: ["email", "public_profile"])
        // 2. Get AccessToken.current?.tokenString
        // 3. Send to backend

        let placeholderToken = "facebook_access_token_placeholder"

        do {
            let authResponse = try await sendAuthRequest(
                provider: "facebook",
                body: ["access_token": placeholderToken]
            )
            handleAuthSuccess(authResponse)
        } catch {
            errorMessage = "Facebook sign-in failed: \(error.localizedDescription)"
        }

        isLoading = false
    }

    // MARK: - Vipps Sign-In

    func signInWithVipps() async {
        isLoading = true
        errorMessage = nil

        // TODO: Integrate Vipps Login SDK
        // 1. VippsLogin.startLogin()
        // 2. Get access token from callback
        // 3. Send to backend

        let placeholderToken = "vipps_access_token_placeholder"

        do {
            let authResponse = try await sendAuthRequest(
                provider: "vipps",
                body: ["access_token": placeholderToken]
            )
            handleAuthSuccess(authResponse)
        } catch {
            errorMessage = "Vipps sign-in failed: \(error.localizedDescription)"
        }

        isLoading = false
    }

    // MARK: - Sign Out

    func signOut() {
        KeychainHelper.delete(key: KeychainHelper.tokenKey)
        isAuthenticated = false
        currentUser = nil
        UserDefaults.standard.removeObject(forKey: "has_completed_onboarding")
        print("Signed out")
    }

    // MARK: - Profile

    func fetchProfile() async {
        guard let token = authToken else { return }

        do {
            let url = URL(string: "\(AppConfig.backendURL)/auth/me")!
            var request = URLRequest(url: url)
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                // Token may be expired
                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 401 {
                    signOut()
                }
                return
            }

            let profileResponse = try JSONDecoder().decode(ProfileResponse.self, from: data)
            currentUser = profileResponse.user

            // Sync language preference
            L10n.set(profileResponse.user.language)

        } catch {
            print("Failed to fetch profile: \(error.localizedDescription)")
        }
    }

    func updateProfile(language: AppLanguage? = nil, trainingLevel: TrainingLevel? = nil, persona: String? = nil) async {
        guard let token = authToken else { return }

        var body: [String: String] = [:]
        if let lang = language { body["language"] = lang.rawValue }
        if let level = trainingLevel { body["training_level"] = level.rawValue }
        if let p = persona { body["preferred_persona"] = p }

        do {
            let url = URL(string: "\(AppConfig.backendURL)/auth/me")!
            var request = URLRequest(url: url)
            request.httpMethod = "PUT"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            request.httpBody = try JSONEncoder().encode(body)

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else { return }

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
            print("📤 Profile upsert reason=profile_edit")

        } catch {
            print("Failed to update profile: \(error.localizedDescription)")
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

    private func handleAuthSuccess(_ response: AuthResponse) {
        // Save token to Keychain
        KeychainHelper.save(key: KeychainHelper.tokenKey, string: response.token)

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

        print("Authenticated: \(response.user.email)")
    }
}

private struct AppleAuthorizationPayload {
    let identityToken: String
    let authorizationCode: String?
    let email: String?
    let fullName: String?
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
