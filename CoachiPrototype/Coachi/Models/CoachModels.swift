import Foundation

enum CoachPersonality: String, CaseIterable, Identifiable {
    case personalTrainer = "personal_trainer"
    case toxicMode = "toxic_mode"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .personalTrainer: return "Coach"
        case .toxicMode: return "Drill Sergeant"
        }
    }

    var icon: String {
        switch self {
        case .personalTrainer: return "figure.run"
        case .toxicMode: return "bolt.heart.fill"
        }
    }

    var description: String {
        switch self {
        case .personalTrainer: return "Supportive and encouraging"
        case .toxicMode: return "Tough love, no excuses"
        }
    }

    var colorHex: String {
        switch self {
        case .personalTrainer: return "FF6B35"
        case .toxicMode: return "FF4757"
        }
    }
}

enum OrbState {
    case idle
    case listening
    case speaking
    case paused
}

struct CoachFeedback {
    let text: String
    let shouldSpeak: Bool
    let intensity: IntensityLevel
    let phase: WorkoutPhase
    let waitSeconds: Double
}

struct WelcomeMessage {
    let text: String
    let audioURL: String?
}

struct CoachReply {
    let text: String
    let audioURL: String?
    let personality: String
}

struct BreathAnalysis {
    let intensity: Double
    let volume: Double
    let tempo: Double
    let respiratoryRate: Double
    let breathRegularity: Double
    let signalQuality: Double
}

struct ServiceHealth {
    let isHealthy: Bool
    let activeBrain: String
    let version: String
}
