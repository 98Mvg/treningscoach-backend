//
//  BackendAPIService.swift
//  TreningsCoach
//
//  Handles communication with the Flask backend
//

import Foundation

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

class BackendAPIService {
    // MARK: - Configuration

    static let shared = BackendAPIService()

    private let baseURL = AppConfig.backendURL
    private let session: URLSession

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
        let request = URLRequest(url: url, timeoutInterval: 10)
        session.dataTask(with: request) { _, _, _ in }.resume()
    }

    // MARK: - Auth Header

    private func currentAuthToken() -> String? {
        guard let token = KeychainHelper.readString(key: KeychainHelper.tokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !token.isEmpty else {
            return nil
        }
        return token
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
        var request = URLRequest(url: url)
        addAuthHeader(to: &request)
        return request
    }

    // MARK: - API Methods

    /// Check backend health
    func checkHealth() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/health")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    /// Send audio for analysis only
    func analyzeAudio(_ audioURL: URL) async throws -> BreathAnalysis {
        let url = URL(string: "\(baseURL)/analyze")!
        var request = try createMultipartRequest(url: url, audioURL: audioURL, phase: nil)
        addAuthHeader(to: &request)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }

        return try JSONDecoder().decode(BreathAnalysis.self, from: data)
    }

    /// Send audio to coach endpoint and get feedback
    func getCoachFeedback(_ audioURL: URL, phase: WorkoutPhase) async throws -> CoachResponse {
        let url = URL(string: "\(baseURL)/coach")!
        var request = try createMultipartRequest(url: url, audioURL: audioURL, phase: phase)
        addAuthHeader(to: &request)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            let errorMessage = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw APIError.serverError(message: errorMessage?.error ?? "Unknown error")
        }

        return try JSONDecoder().decode(CoachResponse.self, from: data)
    }

    /// Get welcome message for workout start
    func getWelcomeMessage(language: String = "en", persona: String = "personal_trainer", userName: String = "") async throws -> WelcomeResponse {
        var urlString = "\(baseURL)/welcome?language=\(language)&persona=\(persona)"
        if !userName.isEmpty, let encoded = userName.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) {
            urlString += "&user_name=\(encoded)"
        }
        let url = URL(string: urlString)!
        let request = authenticatedRequest(url: url)
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(WelcomeResponse.self, from: data)
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
        breathAnalysisEnabled: Bool = true,
        micPermissionGranted: Bool = true
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
            breathAnalysisEnabled: breathAnalysisEnabled,
            micPermissionGranted: micPermissionGranted
        )

        let (data, response) = try await session.data(for: request)

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
        var request = URLRequest(url: url)
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

        let (data, response) = try await session.data(for: request)

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

            let (data, response) = try await session.data(for: request)
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

    /// Talk to coach during active workout (wake word triggered)
    /// Includes workout context so coach can give relevant answers
    func talkToCoachDuringWorkout(
        message: String,
        sessionId: String,
        phase: String,
        intensity: String,
        persona: String,
        language: String,
        userName: String = ""
    ) async throws -> CoachTalkResponse {
        let url = URL(string: "\(baseURL)/coach/talk")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)

        var body: [String: String] = [
            "message": message,
            "session_id": sessionId,
            "phase": phase,
            "intensity": intensity,
            "persona": persona,
            "language": language,
            "context": "workout",  // Tells backend this is mid-workout, not casual chat
            "response_mode": "qa",
            "trigger_source": "button"
        ]
        if !userName.isEmpty {
            body["user_name"] = userName
        }
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(CoachTalkResponse.self, from: data)
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

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }
    }

    /// Save workout record to backend
    func saveWorkout(durationSeconds: Int, phase: String, intensity: String, persona: String? = nil) async throws {
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

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.invalidResponse
        }
    }

    /// Get workout history from backend (raw)
    func getWorkouts() async throws -> [[String: Any]] {
        // Home/profile can load before auth is complete; treat as empty history.
        guard let token = KeychainHelper.readString(key: KeychainHelper.tokenKey), !token.isEmpty else {
            return []
        }

        let url = URL(string: "\(baseURL)/workouts")!
        let request = authenticatedRequest(url: url)

        let (data, response) = try await session.data(for: request)
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
            return WorkoutRecord(
                date: date,
                durationSeconds: durationSeconds,
                finalPhase: dict["final_phase"] as? String ?? "cooldown",
                avgIntensity: dict["avg_intensity"] as? String ?? "moderate",
                personaUsed: dict["persona_used"] as? String ?? "personal_trainer"
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

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200 ... 299).contains(httpResponse.statusCode)
        else {
            throw APIError.invalidResponse
        }
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
        breathAnalysisEnabled: Bool = true,
        micPermissionGranted: Bool = true
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        guard addAuthHeader(to: &request) else {
            throw APIError.authenticationRequired
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
