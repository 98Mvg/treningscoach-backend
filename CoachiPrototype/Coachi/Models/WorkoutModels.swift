import Foundation

enum WorkoutPhase: String, CaseIterable, Identifiable {
    case warmup
    case intense
    case cooldown

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .warmup: return "Warm-up"
        case .intense: return "Intense"
        case .cooldown: return "Cool-down"
        }
    }

    var duration: TimeInterval {
        switch self {
        case .warmup: return AppConfig.warmupDuration
        case .intense: return AppConfig.intenseDuration
        case .cooldown: return 180
        }
    }
}

enum WorkoutState {
    case idle
    case active
    case paused
    case complete
}

struct WorkoutRecord: Identifiable, Codable {
    let id: UUID
    let date: Date
    let durationSeconds: Int
    let finalPhase: String
    let avgIntensity: String
    let personaUsed: String

    var durationFormatted: String {
        let minutes = durationSeconds / 60
        let seconds = durationSeconds % 60
        return String(format: "%d:%02d", minutes, seconds)
    }

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
}

struct WorkoutSummary {
    let duration: TimeInterval
    let avgIntensity: IntensityLevel
    let phases: [WorkoutPhase]
    let coachMessages: Int
}

enum IntensityLevel: String, CaseIterable {
    case calm
    case moderate
    case intense
    case critical

    var displayName: String { rawValue.capitalized }

    var color: String {
        switch self {
        case .calm: return "4ECDC4"
        case .moderate: return "FF6B35"
        case .intense: return "FFD93D"
        case .critical: return "FF4757"
        }
    }
}
