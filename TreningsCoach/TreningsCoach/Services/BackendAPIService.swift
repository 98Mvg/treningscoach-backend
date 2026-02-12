//
//  BackendAPIService.swift
//  TreningsCoach
//
//  Handles communication with the Flask backend
//

import Foundation

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

    // MARK: - Auth Header

    /// Adds JWT auth token to request if available
    private func addAuthHeader(to request: inout URLRequest) {
        if let token = KeychainHelper.readString(key: KeychainHelper.tokenKey) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
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
        let request = try createMultipartRequest(url: url, audioURL: audioURL, phase: nil)

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
        let request = try createMultipartRequest(url: url, audioURL: audioURL, phase: phase)

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
        trainingLevel: String = "intermediate",
        persona: String = "personal_trainer",
        userName: String = ""
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
            userName: userName
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

    /// Talk to the coach (conversational, Sundby personality)
    func talkToCoach(message: String) async throws -> CoachTalkResponse {
        let url = URL(string: "\(baseURL)/coach/talk")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["message": message]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(CoachTalkResponse.self, from: data)
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
            "context": "workout"  // Tells backend this is mid-workout, not casual chat
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
        let url = URL(string: "\(baseURL)/workouts")!
        let request = authenticatedRequest(url: url)

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        let json = try JSONSerialization.jsonObject(with: data)
        guard let dict = json as? [String: Any],
              let workouts = dict["workouts"] as? [[String: Any]] else {
            throw APIError.invalidResponse
        }
        return workouts
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
        trainingLevel: String = "intermediate",
        persona: String = "personal_trainer",
        userName: String = ""
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        addAuthHeader(to: &request)

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
        appendField(name: "session_id", value: sessionId)
        appendField(name: "phase", value: phase.rawValue)
        appendField(name: "last_coaching", value: lastCoaching)
        appendField(name: "elapsed_seconds", value: "\(elapsedSeconds)")
        appendField(name: "language", value: language)
        appendField(name: "training_level", value: trainingLevel)
        appendField(name: "persona", value: persona)
        if !userName.isEmpty {
            appendField(name: "user_name", value: userName)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        return request
    }
}

// MARK: - Error Types

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case serverError(message: String)
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
        case .downloadFailed:
            return "Failed to download audio"
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
}
