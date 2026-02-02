//
//  AuthManager.swift
//  TreningsCoach
//
//  Manages authentication state with Google, Facebook, and Vipps
//  Stores JWT token in Keychain, communicates with backend /auth/* endpoints
//

import Foundation
import SwiftUI

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
            throw APIError.serverError(message: errorResp?.error ?? "Auth failed")
        }

        return try JSONDecoder().decode(AuthResponse.self, from: data)
    }

    private func handleAuthSuccess(_ response: AuthResponse) {
        // Save token to Keychain
        KeychainHelper.save(key: KeychainHelper.tokenKey, string: response.token)

        // Update state
        currentUser = response.user
        isAuthenticated = true

        // Sync language
        L10n.set(response.user.language)

        print("Authenticated: \(response.user.email)")
    }
}
