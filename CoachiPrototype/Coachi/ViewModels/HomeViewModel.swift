import SwiftUI

@MainActor
class HomeViewModel: ObservableObject {
    @Published var recentWorkouts: [WorkoutRecord] = []
    @Published var stats = UserStats(totalWorkouts: 12, totalMinutes: 340, currentStreak: 5, workoutsThisWeek: 3, weeklyGoal: 5)
    @Published var isLoading = false

    private let service: CoachServiceProtocol

    init(service: CoachServiceProtocol = LiveCoachService()) {
        self.service = service
    }

    var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        case 17..<21: return "Good evening"
        default: return "Good night"
        }
    }

    var weeklyProgress: Double {
        Double(stats.workoutsThisWeek) / Double(max(stats.weeklyGoal, 1))
    }

    func loadData() async {
        isLoading = true
        defer { isLoading = false }

        do {
            recentWorkouts = try await service.getWorkoutHistory()
        } catch {
            // Fallback to empty — mock shouldn't fail
            recentWorkouts = []
        }
    }
}
