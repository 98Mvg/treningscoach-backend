//
//  Models.swift
//  TreningsCoach
//
//  Data models for the app
//

import Foundation

// MARK: - Voice State

enum VoiceState {
    case idle
    case listening
    case speaking
}

// MARK: - Workout State

enum WorkoutState: String {
    case idle
    case active
    case paused
    case complete
}

// MARK: - Orb State

enum OrbState: String {
    case idle
    case listening
    case speaking
    case paused
}

// MARK: - Workout Phase

enum WorkoutPhase: String, CaseIterable, Identifiable, Codable {
    case warmup = "warmup"
    case intense = "intense"
    case cooldown = "cooldown"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .warmup: return "Warm-up"
        case .intense: return "Intense"
        case .cooldown: return "Cool-down"
        }
    }

    var description: String {
        switch self {
        case .warmup: return "Gentle coaching for warming up"
        case .intense: return "Motivational coaching for intense workout"
        case .cooldown: return "Calming coaching for cooling down"
        }
    }

    var duration: TimeInterval {
        switch self {
        case .warmup: return AppConfig.warmupDuration
        case .intense: return AppConfig.intenseDuration
        case .cooldown: return 180  // 3 minutes
        }
    }
}

enum WorkoutMode: String, CaseIterable, Identifiable, Codable {
    case easyRun = "easy_run"
    case intervals = "interval"
    case standard = "standard"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .easyRun:
            return "Easy Run"
        case .intervals:
            return "Intervals"
        case .standard:
            return "Standard"
        }
    }
}

enum IntervalTemplate: String, CaseIterable, Identifiable, Codable {
    case fourByFour = "4x4"
    case eightByOne = "8x1"
    case tenByThirtyThirty = "10x30/30"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .fourByFour:
            return "4×4"
        case .eightByOne:
            return "8×1"
        case .tenByThirtyThirty:
            return "10×30/30"
        }
    }
}

enum CoachingStyle: String, CaseIterable, Identifiable, Codable {
    case minimal = "minimal"
    case normal = "normal"
    case motivational = "motivational"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .minimal:
            return "Minimal"
        case .normal:
            return "Normal"
        case .motivational:
            return "Motivational"
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

    var latestBreathPhase: BreathPhaseEvent? {
        breathPhases?.last(where: { $0.type != "pause" })
    }

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

// MARK: - Intensity Level

enum IntensityLevel: String, CaseIterable {
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

    var color: String {
        switch self {
        case .calm:     return "4ECDC4"
        case .moderate: return "FF6B35"
        case .intense:  return "FFD93D"
        case .critical: return "FF4757"
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
    let reason: String?
    let coachScore: Int?
    let coachScoreLine: String?
    let brainProvider: String?
    let brainSource: String?
    let brainStatus: String?
    let brainMode: String?
    let coachingStyle: String?
    let intervalTemplate: String?
    let zoneStatus: String?
    let zoneEvent: String?
    let heartRate: Int?
    let targetZoneLabel: String?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let targetSource: String?
    let targetHREnforced: Bool?
    let hrQuality: String?
    let hrQualityReasons: [String]?
    let movementScore: Double?
    let cadenceSPM: Double?
    let movementSource: String?
    let movementState: String?
    let zoneScoreConfidence: String?
    let zoneTimeInTargetPct: Double?
    let zoneOvershoots: Int?
    let recoverySeconds: Double?
    let recoveryAvgSeconds: Double?
    let personalizationTip: String?
    let recoveryLine: String?
    let recoveryBaselineSeconds: Double?

    enum CodingKeys: String, CodingKey {
        case text
        case shouldSpeak = "should_speak"
        case breathAnalysis = "breath_analysis"
        case audioURL = "audio_url"
        case waitSeconds = "wait_seconds"
        case phase
        case reason
        case coachScore = "coach_score"
        case coachScoreLine = "coach_score_line"
        case brainProvider = "brain_provider"
        case brainSource = "brain_source"
        case brainStatus = "brain_status"
        case brainMode = "brain_mode"
        case coachingStyle = "coaching_style"
        case intervalTemplate = "interval_template"
        case zoneStatus = "zone_status"
        case zoneEvent = "zone_event"
        case heartRate = "heart_rate"
        case targetZoneLabel = "target_zone_label"
        case targetHRLow = "target_hr_low"
        case targetHRHigh = "target_hr_high"
        case targetSource = "target_source"
        case targetHREnforced = "target_hr_enforced"
        case hrQuality = "hr_quality"
        case hrQualityReasons = "hr_quality_reasons"
        case movementScore = "movement_score"
        case cadenceSPM = "cadence_spm"
        case movementSource = "movement_source"
        case movementState = "movement_state"
        case zoneScoreConfidence = "zone_score_confidence"
        case zoneTimeInTargetPct = "zone_time_in_target_pct"
        case zoneOvershoots = "zone_overshoots"
        case recoverySeconds = "recovery_seconds"
        case recoveryAvgSeconds = "recovery_avg_seconds"
        case personalizationTip = "personalization_tip"
        case recoveryLine = "recovery_line"
        case recoveryBaselineSeconds = "recovery_baseline_seconds"
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

// MARK: - Workout Record

struct WorkoutRecord: Identifiable, Codable {
    let id: UUID
    let date: Date
    let durationSeconds: Int
    let finalPhase: String
    let avgIntensity: String
    let personaUsed: String

    init(id: UUID = UUID(), date: Date = Date(), durationSeconds: Int, finalPhase: String = "cooldown", avgIntensity: String = "moderate", personaUsed: String = "personal_trainer") {
        self.id = id
        self.date = date
        self.durationSeconds = durationSeconds
        self.finalPhase = finalPhase
        self.avgIntensity = avgIntensity
        self.personaUsed = personaUsed
    }

    // Backward compat: init from old WorkoutPhase + intensity String
    init(id: UUID = UUID(), date: Date = Date(), durationSeconds: Int, phase: WorkoutPhase, intensity: String) {
        self.id = id
        self.date = date
        self.durationSeconds = durationSeconds
        self.finalPhase = phase.rawValue
        self.avgIntensity = intensity
        self.personaUsed = "personal_trainer"
    }

    var durationFormatted: String {
        let mins = durationSeconds / 60
        let secs = durationSeconds % 60
        if mins > 0 {
            return "\(mins)m \(secs)s"
        }
        return "\(secs)s"
    }

    var formattedDuration: String { durationFormatted }

    var dateFormatted: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: date)
    }

    var dayOfWeek: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE"
        return formatter.string(from: date)
    }

    // Legacy compatibility
    var phase: WorkoutPhase {
        WorkoutPhase(rawValue: finalPhase) ?? .cooldown
    }

    var intensity: String { avgIntensity }
}

// MARK: - User Stats

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
