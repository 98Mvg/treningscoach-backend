import Foundation

enum TrainingLevel: String, CaseIterable, Identifiable, Codable {
    case beginner
    case intermediate
    case advanced

    var id: String { rawValue }

    var displayName: String { rawValue.capitalized }

    var icon: String {
        switch self {
        case .beginner: return "figure.walk"
        case .intermediate: return "figure.run"
        case .advanced: return "figure.highintensity.intervaltraining"
        }
    }

    var description: String {
        switch self {
        case .beginner: return "New to working out"
        case .intermediate: return "Regular training"
        case .advanced: return "Competitive level"
        }
    }
}

struct UserProfile: Codable {
    var name: String
    var trainingLevel: TrainingLevel
    var language: String
    var weeklyGoal: Int

    static let `default` = UserProfile(
        name: "Athlete",
        trainingLevel: .intermediate,
        language: "en",
        weeklyGoal: 5
    )
}

struct UserStats {
    var totalWorkouts: Int
    var totalMinutes: Int
    var currentStreak: Int
    var workoutsThisWeek: Int
    var weeklyGoal: Int
}
