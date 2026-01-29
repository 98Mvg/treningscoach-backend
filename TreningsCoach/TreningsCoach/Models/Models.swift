//
//  Models.swift
//  TreningsCoach
//
//  Data models for the app
//

import Foundation

// MARK: - Workout Phase

enum WorkoutPhase: String, CaseIterable, Identifiable, Codable {
    case warmup = "warmup"
    case intense = "intense"
    case cooldown = "cooldown"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .warmup: return "🔥 Warm-up"
        case .intense: return "💪 Intense"
        case .cooldown: return "😌 Cool-down"
        }
    }

    var description: String {
        switch self {
        case .warmup: return "Gentle coaching for warming up"
        case .intense: return "Motivational coaching for intense workout"
        case .cooldown: return "Calming coaching for cooling down"
        }
    }
}

// MARK: - Breath Analysis

struct BreathAnalysis: Codable {
    let silence: Double
    let volume: Double
    let tempo: Double
    let intensity: String
    let duration: Double

    enum CodingKeys: String, CodingKey {
        case silence, volume, tempo, intensity, duration
    }

    var intensityLevel: IntensityLevel {
        IntensityLevel(rawValue: intensity.lowercased()) ?? .moderate
    }
}

enum IntensityLevel: String {
    case calm = "calm"
    case moderate = "moderate"
    case intense = "intense"
    case critical = "critical"

    var displayName: String {
        switch self {
        case .calm: return "Calm"
        case .moderate: return "Moderate"
        case .intense: return "Intense"
        case .critical: return "Critical"
        }
    }

    var emoji: String {
        switch self {
        case .calm: return "😌"
        case .moderate: return "💪"
        case .intense: return "🔥"
        case .critical: return "⚠️"
        }
    }
}

// MARK: - Coach Response

struct CoachResponse: Codable {
    let text: String
    let breathAnalysis: BreathAnalysis
    let audioURL: String
    let phase: String

    enum CodingKeys: String, CodingKey {
        case text
        case breathAnalysis = "breath_analysis"
        case audioURL = "audio_url"
        case phase
    }
}

// MARK: - Continuous Coach Response

struct ContinuousCoachResponse: Codable {
    let text: String
    let shouldSpeak: Bool
    let breathAnalysis: BreathAnalysis
    let audioURL: String?
    let waitSeconds: Double
    let phase: String
    let reason: String?  // For debugging

    enum CodingKeys: String, CodingKey {
        case text
        case shouldSpeak = "should_speak"
        case breathAnalysis = "breath_analysis"
        case audioURL = "audio_url"
        case waitSeconds = "wait_seconds"
        case phase
        case reason
    }
}

// MARK: - Workout Session

struct WorkoutSession: Identifiable, Codable {
    let id: UUID
    let date: Date
    let phase: WorkoutPhase
    let analysis: BreathAnalysis
    let coachMessage: String

    init(id: UUID = UUID(), date: Date = Date(), phase: WorkoutPhase, analysis: BreathAnalysis, coachMessage: String) {
        self.id = id
        self.date = date
        self.phase = phase
        self.analysis = analysis
        self.coachMessage = coachMessage
    }
}
