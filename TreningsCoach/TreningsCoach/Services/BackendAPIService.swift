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
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: configuration)
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
        elapsedSeconds: Int
    ) async throws -> ContinuousCoachResponse {
        let url = URL(string: "\(baseURL)/coach/continuous")!
        let request = try createContinuousMultipartRequest(
            url: url,
            audioURL: audioURL,
            sessionId: sessionId,
            phase: phase,
            lastCoaching: lastCoaching,
            elapsedSeconds: elapsedSeconds
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
        elapsedSeconds: Int
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add audio file
        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"chunk.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        // Add session_id
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"session_id\"\r\n\r\n".data(using: .utf8)!)
        body.append(sessionId.data(using: .utf8)!)
        body.append("\r\n".data(using: .utf8)!)

        // Add phase
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"phase\"\r\n\r\n".data(using: .utf8)!)
        body.append(phase.rawValue.data(using: .utf8)!)
        body.append("\r\n".data(using: .utf8)!)

        // Add last_coaching
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"last_coaching\"\r\n\r\n".data(using: .utf8)!)
        body.append(lastCoaching.data(using: .utf8)!)
        body.append("\r\n".data(using: .utf8)!)

        // Add elapsed_seconds
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"elapsed_seconds\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(elapsedSeconds)".data(using: .utf8)!)
        body.append("\r\n".data(using: .utf8)!)

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
