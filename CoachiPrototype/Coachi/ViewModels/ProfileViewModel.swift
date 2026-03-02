import SwiftUI

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var stats = UserStats(
        totalWorkouts: 12,
        totalMinutes: 340,
        currentStreak: 5,
        workoutsThisWeek: 3,
        weeklyGoal: 5
    )
}
