//
//  BackendAPIService.swift
//  TreningsCoach
//
//  Handles communication with the Flask backend
//

import Foundation
import OSLog

private let backendLogger = Logger(
    subsystem: Bundle.main.bundleIdentifier ?? "com.coachi.app",
    category: "BackendAPIService"
)

private enum BackendAvailabilityError: LocalizedError {
    case cooldownActive(path: String, remainingSeconds: Int)

    var errorDescription: String? {
        switch self {
        case .cooldownActive:
            return "Backend temporarily unavailable."
        }
    }
}

struct WorkoutTalkContext {
    let phase: String?
    let heartRate: Int?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let zoneState: String?
    let timeLeftS: Int?
    let repIndex: Int?
    let repsTotal: Int?
    let repRemainingS: Int?
    let repsRemainingIncludingCurrent: Int?
}

struct BackendUserProfilePayload: Encodable {
    let name: String?
    let sex: String?
    let age: Int?
    let heightCm: Int?
    let weightKg: Int?
    let maxHrBpm: Int?
    let restingHrBpm: Int?
    let profileUpdatedAt: String?

    enum CodingKeys: String, CodingKey {
        case name
        case sex
        case age
        case heightCm = "height_cm"
        case weightKg = "weight_kg"
        case maxHrBpm = "max_hr_bpm"
        case restingHrBpm = "resting_hr_bpm"
        case profileUpdatedAt = "profile_updated_at"
    }
}

private struct TokenRefreshResponse: Codable {
    let token: String?
    let accessToken: String?
    let refreshToken: String?
    let expiresIn: Int?
    let refreshExpiresIn: Int?

    enum CodingKeys: String, CodingKey {
        case token
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case refreshExpiresIn = "refresh_expires_in"
    }

    var resolvedAccessToken: String {
        (accessToken ?? token ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

private struct VoiceSessionRequest: Encodable {
    let language: String
    let userName: String?
    let summaryContext: PostWorkoutSummaryContext

    enum CodingKeys: String, CodingKey {
        case language
        case userName = "user_name"
        case summaryContext = "summary_context"
    }
}

class BackendAPIService {
    // MARK: - Configuration

    static let shared = BackendAPIService()
    private static let mobileAnalyticsAnonymousIDKey = "mobile_analytics_anonymous_id"

    private let baseURL = AppConfig.backendURL
    private let talkRequestTimeout: TimeInterval = 12
    private let session: URLSession
    private let jsonDecoder = JSONDecoder()
    private let jsonEncoder = JSONEncoder()
    private let backendAvailabilityQueue = DispatchQueue(label: "BackendAPIService.availability")
    private let backendUnavailableCooldownSeconds: TimeInterval = 20
    private var backendUnavailableUntil: Date?

    private init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 90
        configuration.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: configuration)
    }

    // MARK: - Backend Wake-Up

    /// Fire-and-forget ping to /health to wake Render from cold start.
    /// Call early (app launch) so the backend is warm by the time real requests arrive.
    func wakeBackend() {
        guard let url = URL(string: "\(baseURL)/health") else { return }
        guard !shouldSkipBestEffortRequest(path: "/health") else { return }
        let request = URLRequest(url: url, timeoutInterval: 30)
        session.dataTask(with: request) { [weak self] _, _, error in
            if let error {
                self?.markBackendUnavailableIfNeeded(error: error, path: "/health")
            } else {
                self?.clearBackendUnavailableIfNeeded(path: "/health")
            }
        }.resume()
    }

    // MARK: - Auth Header

    private func currentAuthToken() -> String? {
        if let accessToken = KeychainHelper.readString(key: KeychainHelper.accessTokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !accessToken.isEmpty {
            return accessToken
        }
        if let token = KeychainHelper.readString(key: KeychainHelper.tokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !token.isEmpty {
            return token
        }
        return nil
    }

    private func mobileAnalyticsAnonymousID() -> String {
        let defaults = UserDefaults.standard
        if let existing = defaults.string(forKey: Self.mobileAnalyticsAnonymousIDKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
           !existing.isEmpty {
            return existing
        }
        let generated = UUID().uuidString.lowercased()
        defaults.set(generated, forKey: Self.mobileAnalyticsAnonymousIDKey)
        return generated
    }

    private func currentRefreshToken() -> String? {
        guard let token = KeychainHelper.readString(key: KeychainHelper.refreshTokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !token.isEmpty else {
            return nil
        }
        return token
    }

    private func hasAuthMaterial() -> Bool {
        currentAuthToken() != nil || currentRefreshToken() != nil
    }

    private func isExpired(expiresAtKey: String) -> Bool {
        guard let raw = KeychainHelper.readString(key: expiresAtKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            let expiresAt = Double(raw) else {
            return false
        }
        return Date().timeIntervalSince1970 >= expiresAt
    }

    /// Adds JWT auth token to request if available.
    @discardableResult
    private func addAuthHeader(to request: inout URLRequest) -> Bool {
        guard let token = currentAuthToken() else { return false }
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return true
    }

    /// Creates an authenticated GET request
    private func authenticatedRequest(url: URL) -> URLRequest {
        var request = URLRequest(url: url, timeoutInterval: talkRequestTimeout)
        addAuthHeader(to: &request)
        return request
    }

    private func persistTokenBundle(accessToken: String, refreshToken: String?, expiresIn: Int?, refreshExpiresIn: Int?) {
        _ = KeychainHelper.save(key: KeychainHelper.tokenKey, string: accessToken)
        _ = KeychainHelper.save(key: KeychainHelper.accessTokenKey, string: accessToken)

        if let refreshToken, !refreshToken.isEmpty {
            _ = KeychainHelper.save(key: KeychainHelper.refreshTokenKey, string: refreshToken)
        }

        if let expiresIn {
            let expiresAt = Date().addingTimeInterval(TimeInterval(max(0, expiresIn))).timeIntervalSince1970
            _ = KeychainHelper.save(key: KeychainHelper.accessTokenExpiresAtKey, string: String(format: "%.3f", expiresAt))
        }

        if let refreshExpiresIn {
            let expiresAt = Date().addingTimeInterval(TimeInterval(max(0, refreshExpiresIn))).timeIntervalSince1970
            _ = KeychainHelper.save(key: KeychainHelper.refreshTokenExpiresAtKey, string: String(format: "%.3f", expiresAt))
        }
    }

    private func clearTokenBundle() {
        KeychainHelper.delete(key: KeychainHelper.tokenKey)
        KeychainHelper.delete(key: KeychainHelper.accessTokenKey)
        KeychainHelper.delete(key: KeychainHelper.refreshTokenKey)
        KeychainHelper.delete(key: KeychainHelper.accessTokenExpiresAtKey)
        KeychainHelper.delete(key: KeychainHelper.refreshTokenExpiresAtKey)
    }

    func refreshAuthTokenIfNeeded() async -> Bool {
        guard let refreshToken = currentRefreshToken(), !refreshToken.isEmpty else {
            backendLogger.notice("AUTH_REFRESH skipped reason=missing_refresh_token")
            return false
        }
        if isExpired(expiresAtKey: KeychainHelper.refreshTokenExpiresAtKey) {
            backendLogger.notice("AUTH_REFRESH skipped reason=refresh_token_expired")
            clearTokenBundle()
            return false
        }

        guard let url = URL(string: "\(baseURL)/auth/refresh") else {
            return false
        }

        do {
            backendLogger.debug("AUTH_REFRESH attempt=true")
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try jsonEncoder.encode(["refresh_token": refreshToken])

            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                return false
            }

            guard httpResponse.statusCode == 200 else {
                backendLogger.notice("AUTH_REFRESH success=false status=\(httpResponse.statusCode)")
                if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                    clearTokenBundle()
                }
                return false
            }

            let payload = try jsonDecoder.decode(TokenRefreshResponse.self, from: data)
            let accessToken = payload.resolvedAccessToken
            guard !accessToken.isEmpty else {
                return false
            }

            let normalizedRefresh = payload.refreshToken?.trimmingCharacters(in: .whitespacesAndNewlines)
            persistTokenBundle(
                accessToken: accessToken,
                refreshToken: normalizedRefresh?.isEmpty == false ? normalizedRefresh : nil,
                expiresIn: payload.expiresIn,
                refreshExpiresIn: payload.refreshExpiresIn
            )
            backendLogger.notice("AUTH_REFRESH success=true")
            return true
        } catch {
            backendLogger.error("AUTH_REFRESH success=false")
            return false
        }
    }

    @discardableResult
    func logout(refreshToken: String) async -> Bool {
        let normalizedToken = refreshToken.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalizedToken.isEmpty,
              let url = URL(string: "\(baseURL)/auth/logout") else {
            return false
        }

        do {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try jsonEncoder.encode(["refresh_token": normalizedToken])
            let (_, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                return false
            }
            return httpResponse.statusCode == 200
        } catch {
            backendLogger.error("AUTH_LOGOUT success=false")
            return false
        }
    }

    func deleteCurrentAccount() async throws {
        let url = URL(string: "\(baseURL)/auth/me")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        addAuthHeader(to: &request)

        let (data, response) = try await dataWithAuthRetry(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            let errorResponse = try? jsonDecoder.decode(ErrorResponse.self, from: data)
            throw APIError.serverError(message: errorResponse?.error ?? "Failed to delete account.")
        }
    }

    private func dataWithAuthRetry(for request: URLRequest) async throws -> (Data, URLResponse) {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            return (data, response)
        }
        guard httpResponse.statusCode == 401 || httpResponse.statusCode == 403 else {
            return (data, response)
        }

        backendLogger.notice("AUTH_RETRY status=\(httpResponse.statusCode) path=\(request.url?.path ?? "unknown")")
        let refreshed = await refreshAuthTokenIfNeeded()
        guard refreshed else {
            return (data, response)
        }

        var retryRequest = request
        guard addAuthHeader(to: &retryRequest) else {
            return (data, response)
        }

        return try await session.data(for: retryRequest)
    }

    private func backendUnavailableRemainingSeconds() -> Int? {
        backendAvailabilityQueue.sync {
            guard let unavailableUntil = backendUnavailableUntil else {
                return nil
            }
            let remaining = unavailableUntil.timeIntervalSinceNow
            if remaining <= 0 {
                backendUnavailableUntil = nil
                return nil
            }
            return Int(ceil(remaining))
        }
    }

    private func ensureBackendAvailable(path: String) throws {
        if let remaining = backendUnavailableRemainingSeconds() {
            backendLogger.notice("BACKEND_COOLDOWN skip path=\(path, privacy: .public) remaining_s=\(remaining)")
            throw BackendAvailabilityError.cooldownActive(path: path, remainingSeconds: remaining)
        }
    }

    private func shouldSkipBestEffortRequest(path: String) -> Bool {
        do {
            try ensureBackendAvailable(path: path)
            return false
        } catch {
            return true
        }
    }

    private func clearBackendUnavailableIfNeeded(path: String) {
        let restored = backendAvailabilityQueue.sync { () -> Bool in
            guard backendUnavailableUntil != nil else {
                return false
            }
            backendUnavailableUntil = nil
            return true
        }
        if restored {
            backendLogger.notice("BACKEND_RESTORED path=\(path, privacy: .public)")
        }
    }

    private func markBackendUnavailableIfNeeded(error: Error, path: String) {
        guard isTransientBackendNetworkError(error) else {
            return
        }

        let existingRemaining = backendUnavailableRemainingSeconds()
        backendAvailabilityQueue.sync {
            backendUnavailableUntil = Date().addingTimeInterval(backendUnavailableCooldownSeconds)
        }

        if existingRemaining == nil {
            backendLogger.notice(
                "BACKEND_UNAVAILABLE path=\(path, privacy: .public) cooldown_s=\(Int(self.backendUnavailableCooldownSeconds))"
            )
        }
    }

    private func isTransientBackendNetworkError(_ error: Error) -> Bool {
        if error is BackendAvailabilityError {
            return false
        }
        if let apiError = error as? APIError,
           case .networkError(let wrapped) = apiError {
            return isTransientBackendNetworkError(wrapped)
        }
        let nsError = error as NSError
        guard nsError.domain == NSURLErrorDomain else {
            return false
        }
        let code = URLError.Code(rawValue: nsError.code)
        switch code {
        case .timedOut,
             .cannotFindHost,
             .cannotConnectToHost,
             .dnsLookupFailed,
             .networkConnectionLost,
             .notConnectedToInternet,
             .cannotLoadFromNetwork,
             .resourceUnavailable:
            return true
        default:
            return false
        }
    }

    private func performRequestWithBackendAvailability(
        _ request: URLRequest,
        path: String,
        useAuthRetry: Bool = false
    ) async throws -> (Data, URLResponse) {
        try ensureBackendAvailable(path: path)
        do {
            let result: (Data, URLResponse)
            if useAuthRetry {
                result = try await dataWithAuthRetry(for: request)
            } else {
                result = try await session.data(for: request)
            }
            clearBackendUnavailableIfNeeded(path: path)
            return result
        } catch {
            markBackendUnavailableIfNeeded(error: error, path: path)
            throw error
        }
    }

    func fetchAuthenticatedProfile(token: String) async throws -> (Data, URLResponse) {
        let url = URL(string: "\(baseURL)/auth/me")!
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return try await performRequestWithBackendAvailability(request, path: "/auth/me")
    }

    func updateAuthenticatedProfile(token: String, payload: Data) async throws -> (Data, URLResponse) {
        let url = URL(string: "\(baseURL)/auth/me")!
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = payload
        return try await performRequestWithBackendAvailability(request, path: "/auth/me")
    }

    func updateAuthenticatedProfileAvatar(
        token: String,
        imageData: Data,
        filename: String,
        mimeType: String
    ) async throws -> (Data, URLResponse) {
        let url = URL(string: "\(baseURL)/auth/me")!
        var request = URLRequest(url: url, timeoutInterval: 30)
        request.httpMethod = "PUT"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"avatar\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        return try await performRequestWithBackendAvailability(request, path: "/auth/me")
    }

    // MARK: - API Methods

    /// Check backend health
    func checkHealth() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/health")!
        var request = URLRequest(url: url, timeoutInterval: 15)
        request.httpMethod = "GET"
        let (data, _) = try await performRequestWithBackendAvailability(request, path: "/health")
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    func fetchAppRuntime() async throws -> AppRuntimeResponse {
        let url = URL(string: "\(baseURL)/app/runtime")!
        let request = URLRequest(url: url, timeoutInterval: 15)
        let (data, response) = try await performRequestWithBackendAvailability(request, path: "/app/runtime")
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
        return try jsonDecoder.decode(AppRuntimeResponse.self, from: data)
    }

    /// Send audio for analysis only
    func analyzeAudio(_ audioURL: URL) async throws -> BreathAnalysis {
        let url = URL(string: "\(baseURL)/analyze")!
        var request = try createMultipartRequest(url: url, audioURL: audioURL, phase: nil)
        addAuthHeader(to: &request)

        let (data, response) = try await performRequestWithBackendAvailability(
            request,
            path: "/analyze",
            useAuthRetry: true
        )

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }

        return try JSONDecoder().decode(BreathAnalysis.self, from: data)
    }

    /// Download voice audio file
    func downloadVoiceAudio(from path: String) async throws -> Data {
        let urlString = path.hasPrefix("http") ? path : "\(baseURL)\(path)"
        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.downloadFailed
        }

        return data
    }

    /// Send audio chunk for continuous coaching feedback
    func getContinuousCoachFeedback(
        _ audioURL: URL,
        sessionId: String,
        phase: WorkoutPhase,
        lastCoaching: String,
        elapsedSeconds: Int,
        language: String = "en",
        trainingLevel: String = "beginner",
        persona: String = "personal_trainer",
        userName: String = "",
        workoutMode: WorkoutMode = .standard,
        easyRunFreeMode: Bool = false,
        coachingStyle: CoachingStyle = .medium,
        intervalTemplate: IntervalTemplate = .fourByFour,
        warmupSeconds: Int? = nil,
        mainSeconds: Int? = nil,
        cooldownSeconds: Int? = nil,
        intervalRepeats: Int? = nil,
        intervalWorkSeconds: Int? = nil,
        intervalRecoverySeconds: Int? = nil,
        userProfileId: String? = nil,
        heartRate: Int? = nil,
        hrSampleAgeSeconds: Double? = nil,
        hrQuality: String? = nil,
        hrConfidence: Double? = nil,
        watchConnected: Bool? = nil,
        watchStatus: String? = nil,
        movementScore: Double? = nil,
        cadenceSPM: Double? = nil,
        movementSource: String? = nil,
        hrMax: Int? = nil,
        restingHR: Int? = nil,
        age: Int? = nil,
        allowGuestPreview: Bool = false,
        breathAnalysisEnabled: Bool = true,
        micPermissionGranted: Bool = true,
        clientSpokenCue: ClientSpokenCue? = nil
    ) async throws -> ContinuousCoachResponse {
        let url = URL(string: "\(baseURL)/coach/continuous")!
        let request = try createContinuousMultipartRequest(
            url: url,
            audioURL: audioURL,
            sessionId: sessionId,
            phase: phase,
            lastCoaching: lastCoaching,
            elapsedSeconds: elapsedSeconds,
            language: language,
            trainingLevel: trainingLevel,
            persona: persona,
            userName: userName,
            workoutMode: workoutMode,
            easyRunFreeMode: easyRunFreeMode,
            coachingStyle: coachingStyle,
            intervalTemplate: intervalTemplate,
            warmupSeconds: warmupSeconds,
            mainSeconds: mainSeconds,
            cooldownSeconds: cooldownSeconds,
            intervalRepeats: intervalRepeats,
            intervalWorkSeconds: intervalWorkSeconds,
            intervalRecoverySeconds: intervalRecoverySeconds,
            userProfileId: userProfileId,
            heartRate: heartRate,
            hrSampleAgeSeconds: hrSampleAgeSeconds,
            hrQuality: hrQuality,
            hrConfidence: hrConfidence,
            watchConnected: watchConnected,
            watchStatus: watchStatus,
            movementScore: movementScore,
            cadenceSPM: cadenceSPM,
            movementSource: movementSource,
            hrMax: hrMax,
            restingHR: restingHR,
            age: age,
            allowGuestPreview: allowGuestPreview,
            breathAnalysisEnabled: breathAnalysisEnabled,
            micPermissionGranted: micPermissionGranted,
            clientSpokenCue: clientSpokenCue
        )

        let (data, response) = try await performRequestWithBackendAvailability(
            request,
            path: "/coach/continuous",
            useAuthRetry: true
        )

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            let errorMessage = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw APIError.serverError(message: errorMessage?.error ?? "Unknown error")
        }

        return try JSONDecoder().decode(ContinuousCoachResponse.self, from: data)
    }

    /// Talk to the coach (short Q&A by default for user-initiated asks)
    func talkToCoach(
        message: String,
        language: String? = nil,
        persona: String? = nil,
        userName: String = "",
        responseMode: String? = nil,
        context: String? = nil,
        triggerSource: String = "button"
    ) async throws -> CoachTalkResponse {
        let url = URL(string: "\(baseURL)/coach/talk")!
        var request = URLRequest(url: url, timeoutInterval: talkRequestTimeout)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)

        var body: [String: String] = ["message": message]
        if let language = language?.trimmingCharacters(in: .whitespacesAndNewlines), !language.isEmpty {
            body["language"] = language
        }
        if let persona = persona?.trimmingCharacters(in: .whitespacesAndNewlines), !persona.isEmpty {
            body["persona"] = persona
        }
        if !userName.isEmpty {
            body["user_name"] = userName
        }
        if let responseMode = responseMode?.trimmingCharacters(in: .whitespacesAndNewlines), !responseMode.isEmpty {
            body["response_mode"] = responseMode
        }
        if let context = context?.trimmingCharacters(in: .whitespacesAndNewlines), !context.isEmpty {
            body["context"] = context
        }
        body["trigger_source"] = triggerSource
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await dataWithAuthRetry(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(CoachTalkResponse.self, from: data)
    }

    /// Unified workout talk endpoint (wake word + button)
    /// Sends multipart audio when available, otherwise falls back to JSON prompt.
    func talkToCoachDuringWorkoutUnified(
        audioURL: URL?,
        fallbackMessage: String,
        triggerSource: String,
        sessionId: String,
        workoutContext: WorkoutTalkContext,
        persona: String,
        language: String,
        userName: String = ""
    ) async throws -> CoachTalkResponse {
        if let audioURL {
            let url = URL(string: "\(baseURL)/coach/talk")!
            let request = try createTalkMultipartRequest(
                url: url,
                audioURL: audioURL,
                triggerSource: triggerSource,
                sessionId: sessionId,
                workoutContext: workoutContext,
                persona: persona,
                language: language,
                userName: userName
            )

            let (data, response) = try await performRequestWithBackendAvailability(
                request,
                path: "/coach/talk",
                useAuthRetry: true
            )
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw APIError.invalidResponse
            }
            return try JSONDecoder().decode(CoachTalkResponse.self, from: data)
        }

        // Audio capture failed — keep behavior deterministic via JSON fallback.
        return try await talkToCoach(
            message: fallbackMessage,
            language: language,
            persona: persona,
            userName: userName,
            responseMode: "qa",
            context: "workout",
            triggerSource: triggerSource
        )
    }

    /// Switch persona mid-session
    func switchPersona(sessionId: String, persona: String) async throws {
        let url = URL(string: "\(baseURL)/coach/persona")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)

        let body: [String: String] = ["session_id": sessionId, "persona": persona]
        request.httpBody = try JSONEncoder().encode(body)

        let (_, response) = try await dataWithAuthRetry(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
    }

    func createLiveVoiceSession(
        summaryContext: PostWorkoutSummaryContext,
        language: String,
        userName: String = ""
    ) async throws -> VoiceSessionBootstrap {
        guard currentAuthToken() != nil else {
            throw APIError.authenticationRequired
        }

        let url = URL(string: "\(baseURL)/voice/session")!
        var request = URLRequest(url: url, timeoutInterval: 30)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)
        request.httpBody = try jsonEncoder.encode(
            VoiceSessionRequest(
                language: language,
                userName: userName.isEmpty ? nil : userName,
                summaryContext: summaryContext
            )
        )

        let localizedBackendUnavailableMessage = language == "no"
            ? "Serveren svarer ikke akkurat na. Prov igjen om litt."
            : "The server is not responding right now. Try again in a moment."

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await performRequestWithBackendAvailability(
                request,
                path: "/voice/session",
                useAuthRetry: true
            )
        } catch is BackendAvailabilityError {
            throw APIError.serverError(message: localizedBackendUnavailableMessage)
        } catch {
            if isTransientBackendNetworkError(error) {
                throw APIError.serverError(message: localizedBackendUnavailableMessage)
            }
            throw error
        }
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 429 {
                throw APIError.quotaExceeded
            }
            let errorMessage = try? jsonDecoder.decode(ErrorResponse.self, from: data)
            if let message = errorMessage?.error, !message.isEmpty {
                throw APIError.serverError(message: message)
            }
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }

        return try jsonDecoder.decode(VoiceSessionBootstrap.self, from: data)
    }

    @discardableResult
    func trackAnalyticsEvent(
        event: String,
        metadata: [String: Any] = [:],
        requiresAuth: Bool = false
    ) async -> Bool {
        if requiresAuth && currentAuthToken() == nil {
            return false
        }
        guard let url = URL(string: "\(baseURL)/analytics/mobile") else {
            return false
        }

        do {
            var request = URLRequest(url: url, timeoutInterval: 10)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if currentAuthToken() != nil {
                addAuthHeader(to: &request)
            }
            request.httpBody = try JSONSerialization.data(
                withJSONObject: [
                    "event": event,
                    "metadata": metadata,
                    "anonymous_id": mobileAnalyticsAnonymousID(),
                ]
            )

            let (_, response) = try await performRequestWithBackendAvailability(
                request,
                path: "/analytics/mobile",
                useAuthRetry: true
            )
            guard let httpResponse = response as? HTTPURLResponse else {
                return false
            }
            return httpResponse.statusCode == 200
        } catch is BackendAvailabilityError {
            return false
        } catch {
            markBackendUnavailableIfNeeded(error: error, path: "/analytics/mobile")
            backendLogger.error("ANALYTICS_EVENT failed event=\(event)")
            return false
        }
    }

    @discardableResult
    func trackVoiceTelemetry(
        event: String,
        metadata: [String: Any] = [:]
    ) async -> Bool {
        guard currentAuthToken() != nil,
              let url = URL(string: "\(baseURL)/voice/telemetry") else {
            return false
        }

        do {
            var request = URLRequest(url: url, timeoutInterval: 10)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            addAuthHeader(to: &request)
            request.httpBody = try JSONSerialization.data(
                withJSONObject: [
                    "event": event,
                    "metadata": metadata,
                    "anonymous_id": mobileAnalyticsAnonymousID(),
                ]
            )

            let (_, response) = try await performRequestWithBackendAvailability(
                request,
                path: "/voice/telemetry",
                useAuthRetry: true
            )
            guard let httpResponse = response as? HTTPURLResponse else {
                return false
            }
            return httpResponse.statusCode == 200
        } catch is BackendAvailabilityError {
            return false
        } catch {
            markBackendUnavailableIfNeeded(error: error, path: "/voice/telemetry")
            backendLogger.error("VOICE_TELEMETRY failed event=\(event)")
            return false
        }
    }

    /// Save workout record to backend
    func saveWorkout(
        durationSeconds: Int,
        phase: String,
        intensity: String,
        persona: String? = nil,
        language: String? = nil,
        coachScore: Int? = nil,
        hrScore: Int? = nil,
        breathScore: Int? = nil,
        durationScore: Int? = nil
    ) async throws {
        let url = URL(string: "\(baseURL)/workouts")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)

        var body: [String: Any] = [
            "duration_seconds": durationSeconds,
            "phase": phase,
            "intensity": intensity
        ]
        if let persona = persona { body["persona"] = persona }
        if let language = language, !language.isEmpty { body["language"] = language }
        if let coachScore { body["coach_score"] = coachScore }
        if let hrScore { body["hr_score"] = hrScore }
        if let breathScore { body["breath_score"] = breathScore }
        if let durationScore { body["duration_score"] = durationScore }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await dataWithAuthRetry(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.invalidResponse
        }
    }

    /// Get workout history from backend (raw)
    func getWorkouts() async throws -> [[String: Any]] {
        // Home/profile can load before auth is complete; treat as empty history.
        guard currentAuthToken() != nil else {
            return []
        }

        let url = URL(string: "\(baseURL)/workouts")!
        let request = authenticatedRequest(url: url)

        let (data, response) = try await dataWithAuthRetry(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Not signed in / expired token should not surface as noisy UI error on home.
        if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
            return []
        }

        guard httpResponse.statusCode == 200 else {
            let errorMessage = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            if let message = errorMessage?.error, !message.isEmpty {
                throw APIError.serverError(message: message)
            }
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }

        let json = try JSONSerialization.jsonObject(with: data)
        if let dict = json as? [String: Any],
           let workouts = dict["workouts"] as? [[String: Any]] {
            return workouts
        }
        // Compatibility: accept raw list response shape as well.
        if let workouts = json as? [[String: Any]] {
            return workouts
        }

        return []
    }

    /// Get workout history as WorkoutRecord array
    func getWorkoutHistory(limit: Int = 20) async throws -> [WorkoutRecord] {
        let rawWorkouts = try await getWorkouts()
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        return rawWorkouts.prefix(limit).compactMap { dict -> WorkoutRecord? in
            guard let durationSeconds = dict["duration_seconds"] as? Int else { return nil }
            let date: Date
            if let dateStr = dict["date"] as? String {
                date = dateFormatter.date(from: dateStr) ?? Date()
            } else {
                date = Date()
            }
            let coachScore: Int? = dict["coach_score"] as? Int
            return WorkoutRecord(
                date: date,
                durationSeconds: durationSeconds,
                finalPhase: dict["final_phase"] as? String ?? "cooldown",
                avgIntensity: dict["avg_intensity"] as? String ?? "moderate",
                personaUsed: dict["persona_used"] as? String ?? "personal_trainer",
                coachScore: coachScore
            )
        }
    }

    /// Persist onboarding/profile fields on backend for runtime targeting.
    func upsertUserProfile(_ profile: BackendUserProfilePayload) async throws {
        let url = URL(string: "\(baseURL)/profile/upsert")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)
        request.httpBody = try JSONEncoder().encode(profile)

        let (_, response) = try await dataWithAuthRetry(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200 ... 299).contains(httpResponse.statusCode)
        else {
            throw APIError.invalidResponse
        }
    }

    /// Server-side subscription tier check. Returns "premium" or "free". Best-effort (no throw).
    func validateSubscription(
        transactionID: String? = nil,
        signedTransactionInfo: String? = nil
    ) async -> String? {
        guard let url = URL(string: "\(baseURL)/subscription/validate") else { return nil }
        guard hasAuthMaterial() else {
            backendLogger.notice("SUB_VALIDATE skipped reason=missing_auth_material")
            return nil
        }
        do {
            var request = URLRequest(url: url, timeoutInterval: 10)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            addAuthHeader(to: &request)
            var body: [String: Any] = ["platform": "ios"]
            if let txID = transactionID, !txID.isEmpty { body["transaction_id"] = txID }
            if let signedTransactionInfo, !signedTransactionInfo.isEmpty {
                body["signed_transaction_info"] = signedTransactionInfo
            }
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            let (data, _) = try await performRequestWithBackendAvailability(
                request,
                path: "/subscription/validate",
                useAuthRetry: true
            )
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let tier = json["tier"] as? String {
                return tier
            }
        } catch is BackendAvailabilityError {
        } catch {
            // Best-effort — subscription state is StoreKit-authoritative on iOS
        }
        return nil
    }

    // MARK: - Helper Methods

    private func createMultipartRequest(url: URL, audioURL: URL, phase: WorkoutPhase?) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add audio file
        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"recording.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        // Add phase parameter if provided
        if let phase = phase {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"phase\"\r\n\r\n".data(using: .utf8)!)
            body.append(phase.rawValue.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        return request
    }

    private func createContinuousMultipartRequest(
        url: URL,
        audioURL: URL,
        sessionId: String,
        phase: WorkoutPhase,
        lastCoaching: String,
        elapsedSeconds: Int,
        language: String = "en",
        trainingLevel: String = "beginner",
        persona: String = "personal_trainer",
        userName: String = "",
        workoutMode: WorkoutMode = .standard,
        easyRunFreeMode: Bool = false,
        coachingStyle: CoachingStyle = .medium,
        intervalTemplate: IntervalTemplate = .fourByFour,
        warmupSeconds: Int? = nil,
        mainSeconds: Int? = nil,
        cooldownSeconds: Int? = nil,
        intervalRepeats: Int? = nil,
        intervalWorkSeconds: Int? = nil,
        intervalRecoverySeconds: Int? = nil,
        userProfileId: String? = nil,
        heartRate: Int? = nil,
        hrSampleAgeSeconds: Double? = nil,
        hrQuality: String? = nil,
        hrConfidence: Double? = nil,
        watchConnected: Bool? = nil,
        watchStatus: String? = nil,
        movementScore: Double? = nil,
        cadenceSPM: Double? = nil,
        movementSource: String? = nil,
        hrMax: Int? = nil,
        restingHR: Int? = nil,
        age: Int? = nil,
        allowGuestPreview: Bool = false,
        breathAnalysisEnabled: Bool = true,
        micPermissionGranted: Bool = true,
        clientSpokenCue: ClientSpokenCue? = nil
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let didAttachAuth = addAuthHeader(to: &request)
        if allowGuestPreview && !didAttachAuth {
            request.setValue("1", forHTTPHeaderField: "X-Coachi-Guest-Preview")
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Helper to append a form field
        func appendField(name: String, value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append(value.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }

        // Add audio file
        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"chunk.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        // Add form fields
        appendField(name: "contract_version", value: "2")
        appendField(name: "session_id", value: sessionId)
        appendField(name: "phase", value: phase.rawValue)
        appendField(name: "last_coaching", value: lastCoaching)
        appendField(name: "elapsed_seconds", value: "\(elapsedSeconds)")
        appendField(name: "language", value: language)
        appendField(name: "training_level", value: trainingLevel)
        appendField(name: "persona", value: persona)
        appendField(name: "workout_mode", value: workoutMode.rawValue)
        appendField(name: "easy_run_free_mode", value: easyRunFreeMode ? "true" : "false")
        appendField(name: "coaching_style", value: coachingStyle.rawValue)
        appendField(name: "interval_template", value: intervalTemplate.rawValue)
        if let warmupSeconds = warmupSeconds {
            appendField(name: "warmup_seconds", value: "\(max(0, warmupSeconds))")
        }
        if let userProfileId = userProfileId, !userProfileId.isEmpty {
            appendField(name: "user_profile_id", value: userProfileId)
        }
        if !userName.isEmpty {
            appendField(name: "user_name", value: userName)
        }
        if let heartRate = heartRate {
            appendField(name: "heart_rate", value: "\(heartRate)")
        }
        if let hrSampleAgeSeconds = hrSampleAgeSeconds {
            appendField(name: "hr_sample_age_seconds", value: String(format: "%.2f", hrSampleAgeSeconds))
        }
        if let hrQuality = hrQuality, !hrQuality.isEmpty {
            appendField(name: "hr_quality", value: hrQuality)
        }
        if let hrConfidence = hrConfidence {
            appendField(name: "hr_confidence", value: String(format: "%.3f", hrConfidence))
        }
        if let watchConnected = watchConnected {
            appendField(name: "watch_connected", value: watchConnected ? "true" : "false")
        }
        if let watchStatus = watchStatus, !watchStatus.isEmpty {
            appendField(name: "watch_status", value: watchStatus)
        }
        if let movementScore = movementScore {
            appendField(name: "movement_score", value: String(format: "%.3f", movementScore))
        }
        if let cadenceSPM = cadenceSPM {
            appendField(name: "cadence_spm", value: String(format: "%.1f", cadenceSPM))
        }
        if let movementSource = movementSource, !movementSource.isEmpty {
            appendField(name: "movement_source", value: movementSource)
        }
        if let hrMax = hrMax {
            appendField(name: "hr_max", value: "\(hrMax)")
        }
        if let restingHR = restingHR {
            appendField(name: "resting_hr", value: "\(restingHR)")
        }
        if let age = age {
            appendField(name: "age", value: "\(age)")
        }
        appendField(name: "breath_analysis_enabled", value: breathAnalysisEnabled ? "true" : "false")
        appendField(name: "mic_permission_granted", value: micPermissionGranted ? "true" : "false")

        let planWarmupSeconds = max(0, warmupSeconds ?? Int(AppConfig.warmupDuration))
        let planCooldownSeconds = max(0, cooldownSeconds ?? 0)
        var workoutPlan: [String: Any] = [
            "workout_type": workoutMode == .intervals ? "intervals" : "easy_run",
            "warmup_s": planWarmupSeconds,
            "cooldown_s": planCooldownSeconds
        ]
        if workoutMode == .easyRun && easyRunFreeMode {
            workoutPlan["main_s"] = 0
            workoutPlan["free_run"] = true
        } else if workoutMode == .easyRun, let mainSeconds {
            workoutPlan["main_s"] = max(0, mainSeconds)
        }
        if workoutMode == .intervals {
            if let intervalRepeats, let intervalWorkSeconds, let intervalRecoverySeconds,
               intervalRepeats > 0, intervalWorkSeconds > 0, intervalRecoverySeconds >= 0 {
                workoutPlan["intervals"] = [
                    "repeats": intervalRepeats,
                    "work_s": intervalWorkSeconds,
                    "recovery_s": intervalRecoverySeconds,
                ]
            } else {
                workoutPlan["intervals"] = intervalPlanFromTemplate(intervalTemplate)
            }
        }
        if let workoutPlanJSON = jsonString(workoutPlan) {
            appendField(name: "workout_plan", value: workoutPlanJSON)
        }

        var workoutState: [String: Any] = [
            "session_id": sessionId,
            "elapsed_s": elapsedSeconds,
            "phase": phase.rawValue,
            "paused": false
        ]
        if let watchConnected = watchConnected {
            workoutState["watch_connected"] = watchConnected
        }
        if let heartRate = heartRate {
            workoutState["hr_bpm"] = heartRate
        }
        if let hrQuality = hrQuality, !hrQuality.isEmpty {
            workoutState["hr_quality"] = hrQuality
        }
        if let hrConfidence = hrConfidence {
            workoutState["hr_confidence"] = hrConfidence
        }
        if let movementScore = movementScore {
            workoutState["movement_score"] = movementScore
        }
        if let cadenceSPM = cadenceSPM {
            workoutState["cadence_spm"] = cadenceSPM
        }
        if let movementSource = movementSource, !movementSource.isEmpty {
            workoutState["movement_state"] = movementSource
        }
        if let clientSpokenCue {
            workoutState["client_spoken_cue"] = [
                "cue_id": clientSpokenCue.cueID,
                "event_type": clientSpokenCue.eventType,
                "spoken_elapsed_s": clientSpokenCue.spokenElapsedSeconds,
            ]
        }
        if let workoutStateJSON = jsonString(workoutState) {
            appendField(name: "workout_state", value: workoutStateJSON)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        return request
    }

    private func createTalkMultipartRequest(
        url: URL,
        audioURL: URL,
        triggerSource: String,
        sessionId: String,
        workoutContext: WorkoutTalkContext,
        persona: String,
        language: String,
        userName: String = ""
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        addAuthHeader(to: &request)

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        func appendField(name: String, value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append(value.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }

        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"talk.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        appendField(name: "contract_version", value: "2")
        appendField(name: "trigger_source", value: triggerSource)
        appendField(name: "context", value: "workout")
        appendField(name: "response_mode", value: "qa")
        appendField(name: "session_id", value: sessionId)
        appendField(name: "persona", value: persona)
        appendField(name: "language", value: language)
        if !userName.isEmpty {
            appendField(name: "user_name", value: userName)
        }
        if let phase = workoutContext.phase, !phase.isEmpty {
            appendField(name: "phase", value: phase)
            appendField(name: "workout_phase", value: phase)
        }
        if let bpm = workoutContext.heartRate {
            appendField(name: "heart_rate", value: "\(bpm)")
            appendField(name: "workout_heart_rate", value: "\(bpm)")
        }
        if let low = workoutContext.targetHRLow {
            appendField(name: "target_hr_low", value: "\(low)")
            appendField(name: "workout_target_hr_low", value: "\(low)")
        }
        if let high = workoutContext.targetHRHigh {
            appendField(name: "target_hr_high", value: "\(high)")
            appendField(name: "workout_target_hr_high", value: "\(high)")
        }
        if let zoneState = workoutContext.zoneState, !zoneState.isEmpty {
            appendField(name: "zone_state", value: zoneState)
            appendField(name: "workout_zone_state", value: zoneState)
        }
        if let timeLeftS = workoutContext.timeLeftS {
            appendField(name: "time_left_s", value: "\(timeLeftS)")
        }
        if let repIndex = workoutContext.repIndex {
            appendField(name: "rep_index", value: "\(repIndex)")
        }
        if let repsTotal = workoutContext.repsTotal {
            appendField(name: "reps_total", value: "\(repsTotal)")
        }
        if let repRemainingS = workoutContext.repRemainingS {
            appendField(name: "rep_remaining_s", value: "\(repRemainingS)")
        }
        if let repsRemaining = workoutContext.repsRemainingIncludingCurrent {
            appendField(name: "reps_remaining_including_current", value: "\(repsRemaining)")
        }
        var workoutSummary: [String: Any] = [:]
        if let phase = workoutContext.phase, !phase.isEmpty { workoutSummary["phase"] = phase }
        if let timeLeftS = workoutContext.timeLeftS { workoutSummary["time_left_s"] = timeLeftS }
        if let repIndex = workoutContext.repIndex { workoutSummary["rep_index"] = repIndex }
        if let repsTotal = workoutContext.repsTotal { workoutSummary["reps_total"] = repsTotal }
        if let repRemainingS = workoutContext.repRemainingS { workoutSummary["rep_remaining_s"] = repRemainingS }
        if let repsRemaining = workoutContext.repsRemainingIncludingCurrent {
            workoutSummary["reps_remaining_including_current"] = repsRemaining
        }
        if let workoutSummaryJSON = jsonString(workoutSummary), !workoutSummary.isEmpty {
            appendField(name: "workout_context_summary", value: workoutSummaryJSON)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body
        return request
    }

    private func intervalPlanFromTemplate(_ template: IntervalTemplate) -> [String: Int] {
        switch template {
        case .fourByFour:
            return ["repeats": 4, "work_s": 240, "recovery_s": 180]
        case .eightByOne:
            return ["repeats": 8, "work_s": 60, "recovery_s": 60]
        case .tenByThirtyThirty:
            return ["repeats": 10, "work_s": 30, "recovery_s": 30]
        }
    }

    private func jsonString(_ value: [String: Any]) -> String? {
        guard JSONSerialization.isValidJSONObject(value),
              let data = try? JSONSerialization.data(withJSONObject: value, options: []),
              let json = String(data: data, encoding: .utf8)
        else {
            return nil
        }
        return json
    }
}

// MARK: - Error Types

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case serverError(message: String)
    case authenticationRequired
    case downloadFailed
    case networkError(Error)
    case quotaExceeded

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .authenticationRequired:
            return "Authentication required"
        case .downloadFailed:
            return "Failed to resolve audio source"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .quotaExceeded:
            return "Daily session limit reached. Try again tomorrow."
        }
    }
}

// MARK: - Response Models

struct HealthResponse: Codable {
    let status: String
    let version: String?
    let timestamp: String
}

struct ErrorResponse: Codable {
    let error: String
    let errorCode: String?

    enum CodingKeys: String, CodingKey {
        case error
        case errorCode = "error_code"
    }
}
