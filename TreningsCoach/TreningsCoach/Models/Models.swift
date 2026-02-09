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
    let analysisVersion: Int?
    let silence: Double
    let volume: Double
    let tempo: Double
    let intensity: String
    let duration: Double

    // Advanced breath metrics (from BreathAnalyzer DSP pipeline)
    let breathPhases: [BreathPhaseEvent]?
    let respiratoryRate: Double?
    let breathRegularity: Double?
    let inhaleExhaleRatio: Double?
    let signalQuality: Double?
    let dominantFrequency: Double?
    let intensityScore: Double?
    let intensityConfidence: Double?
    let intervalState: String?
    let intervalStateConfidence: Double?
    let intervalZone: String?

    enum CodingKeys: String, CodingKey {
        case analysisVersion = "analysis_version"
        case silence, volume, tempo, intensity, duration
        case breathPhases = "breath_phases"
        case respiratoryRate = "respiratory_rate"
        case breathRegularity = "breath_regularity"
        case inhaleExhaleRatio = "inhale_exhale_ratio"
        case signalQuality = "signal_quality"
        case dominantFrequency = "dominant_frequency"
        case intensityScore = "intensity_score"
        case intensityConfidence = "intensity_confidence"
        case intervalState = "interval_state"
        case intervalStateConfidence = "interval_state_confidence"
        case intervalZone = "interval_zone"
    }

    var intensityLevel: IntensityLevel {
        IntensityLevel(rawValue: intensity.lowercased()) ?? .moderate
    }

    /// Latest detected breath phase (inhale/exhale/pause)
    var latestBreathPhase: BreathPhaseEvent? {
        breathPhases?.last(where: { $0.type != "pause" })
    }

    /// Real respiratory rate in BPM (falls back to tempo)
    var effectiveRespiratoryRate: Double {
        respiratoryRate ?? tempo
    }
}

// MARK: - Breath Phase Event

struct BreathPhaseEvent: Codable, Identifiable {
    var id: String { "\(type)-\(start)" }
    let type: String       // "inhale", "exhale", "pause"
    let start: Double
    let end: Double
    let confidence: Double

    enum CodingKeys: String, CodingKey {
        case type, start, end, confidence
    }

    var duration: Double { end - start }

    var displayName: String {
        switch type {
        case "inhale": return "Inhale"
        case "exhale": return "Exhale"
        case "pause": return "Pause"
        default: return type.capitalized
        }
    }

    var icon: String {
        switch type {
        case "inhale": return "arrow.down.circle"
        case "exhale": return "arrow.up.circle"
        case "pause": return "pause.circle"
        default: return "circle"
        }
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

// MARK: - Welcome Response

struct WelcomeResponse: Codable {
    let text: String
    let audioURL: String
    let category: String

    enum CodingKeys: String, CodingKey {
        case text
        case audioURL = "audio_url"
        case category
    }
}

// MARK: - Workout Record (for Dashboard History)

struct WorkoutRecord: Identifiable, Codable {
    let id: UUID
    let date: Date
    let durationSeconds: Int
    let phase: WorkoutPhase
    let intensity: String

    init(id: UUID = UUID(), date: Date = Date(), durationSeconds: Int, phase: WorkoutPhase, intensity: String) {
        self.id = id
        self.date = date
        self.durationSeconds = durationSeconds
        self.phase = phase
        self.intensity = intensity
    }

    var formattedDuration: String {
        let mins = durationSeconds / 60
        let secs = durationSeconds % 60
        return String(format: "%d:%02d", mins, secs)
    }
}

// MARK: - User Stats (for Profile)

struct UserStats {
    var totalWorkouts: Int = 0
    var totalMinutes: Int = 0
    var currentStreak: Int = 0
    var workoutsThisWeek: Int = 0
    var weeklyGoal: Int = 4
}

// MARK: - Coach Talk Response

struct CoachTalkResponse: Codable {
    let text: String
    let audioURL: String
    let personality: String

    enum CodingKeys: String, CodingKey {
        case text
        case audioURL = "audio_url"
        case personality
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
