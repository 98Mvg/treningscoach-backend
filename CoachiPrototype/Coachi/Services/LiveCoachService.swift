import Foundation

final class LiveCoachService: CoachServiceProtocol, @unchecked Sendable {

    private let baseURL: String
    private let session: URLSession

    init(baseURL: String = AppConfig.productionURL) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        self.session = URLSession(configuration: config)
    }

    // MARK: - GET /welcome
    func getWelcomeMessage(language: String, persona: String) async throws -> WelcomeMessage {
        var components = URLComponents(string: "\(baseURL)/welcome")!
        components.queryItems = [
            URLQueryItem(name: "language", value: language),
            URLQueryItem(name: "persona", value: persona)
        ]

        let (data, _) = try await session.data(from: components.url!)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]

        return WelcomeMessage(
            text: json["text"] as? String ?? "Let's go!",
            audioURL: json["audio_url"] as? String
        )
    }

    // MARK: - POST /coach/continuous
    func getContinuousCoachFeedback(sessionId: String, phase: WorkoutPhase, elapsedSeconds: Int) async throws -> CoachFeedback {
        let url = URL(string: "\(baseURL)/coach/continuous")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        // Build multipart form data (matching backend expectation)
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        let fields: [String: String] = [
            "session_id": sessionId,
            "phase": phase.rawValue,
            "elapsed_seconds": String(elapsedSeconds),
            "language": "en"
        ]

        for (key, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, _) = try await session.data(for: request)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]

        let intensityStr = (json["breath_analysis"] as? [String: Any])?["intensity"] as? String ?? "moderate"
        let intensity = IntensityLevel(rawValue: intensityStr) ?? .moderate

        let phaseStr = json["phase"] as? String ?? phase.rawValue
        let responsePhase = WorkoutPhase(rawValue: phaseStr) ?? phase

        return CoachFeedback(
            text: json["text"] as? String ?? "",
            shouldSpeak: json["should_speak"] as? Bool ?? true,
            intensity: intensity,
            phase: responsePhase,
            waitSeconds: json["wait_seconds"] as? Double ?? 8.0
        )
    }

    // MARK: - POST /coach/talk
    func talkToCoach(message: String, sessionId: String, context: String) async throws -> CoachReply {
        let url = URL(string: "\(baseURL)/coach/talk")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "message": message,
            "session_id": sessionId,
            "context": context
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, _) = try await session.data(for: request)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]

        return CoachReply(
            text: json["text"] as? String ?? "",
            audioURL: json["audio_url"] as? String,
            personality: json["personality"] as? String ?? "personal_trainer"
        )
    }

    // MARK: - POST /workouts
    func saveWorkout(_ record: WorkoutRecord) async throws {
        let url = URL(string: "\(baseURL)/workouts")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "duration_seconds": record.durationSeconds,
            "final_phase": record.finalPhase,
            "avg_intensity": record.avgIntensity,
            "persona_used": record.personaUsed,
            "language": "en"
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }
    }

    // MARK: - GET /workouts
    func getWorkoutHistory() async throws -> [WorkoutRecord] {
        let url = URL(string: "\(baseURL)/workouts?limit=20")!
        let (data, _) = try await session.data(from: url)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]

        guard let workoutsArray = json["workouts"] as? [[String: Any]] else {
            return []
        }

        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        return workoutsArray.compactMap { item in
            guard let durationSeconds = item["duration_seconds"] as? Int else { return nil }

            let dateString = item["created_at"] as? String ?? ""
            let date = dateFormatter.date(from: dateString) ?? Date()

            return WorkoutRecord(
                id: UUID(),
                date: date,
                durationSeconds: durationSeconds,
                finalPhase: item["final_phase"] as? String ?? "unknown",
                avgIntensity: item["avg_intensity"] as? String ?? "moderate",
                personaUsed: item["persona_used"] as? String ?? "personal_trainer"
            )
        }
    }

    // MARK: - GET /brain/health
    func checkHealth() async throws -> ServiceHealth {
        let url = URL(string: "\(baseURL)/brain/health")!
        let (data, _) = try await session.data(from: url)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]

        return ServiceHealth(
            isHealthy: json["healthy"] as? Bool ?? false,
            activeBrain: json["active_brain"] as? String ?? "unknown",
            version: AppConfig.appVersion
        )
    }
}
