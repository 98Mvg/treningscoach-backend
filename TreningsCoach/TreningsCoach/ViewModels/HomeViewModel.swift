//
//  HomeViewModel.swift
//  TreningsCoach
//
//  Drives the home screen: greeting, stats, recent workouts
//

import Foundation

@MainActor
class HomeViewModel: ObservableObject {
    @Published var recentWorkouts: [WorkoutRecord] = []
    @Published var stats: UserStats = UserStats()
    @Published var isLoading = false

    private let apiService = BackendAPIService.shared

    var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return L10n.goodMorning
        case 12..<17: return L10n.goodAfternoon
        case 17..<22: return L10n.goodEvening
        default: return L10n.goodNight
        }
    }

    func loadData() async {
        isLoading = true
        do {
            let history = try await apiService.getWorkoutHistory(limit: 10)
            recentWorkouts = history

            // Compute stats from history
            stats.totalWorkouts = history.count
            stats.totalMinutes = history.reduce(0) { $0 + $1.durationSeconds } / 60

            // Count workouts this week
            let calendar = Calendar.current
            let weekStart = calendar.date(from: calendar.dateComponents([.yearForWeekOfYear, .weekOfYear], from: Date())) ?? Date()
            stats.workoutsThisWeek = history.filter { $0.date >= weekStart }.count

            // Simple streak: consecutive days with workouts
            stats.currentStreak = computeStreak(from: history)
        } catch {
            print("⚠️ Failed to load workout history: \(error.localizedDescription)")
        }
        isLoading = false
    }

    private func computeStreak(from records: [WorkoutRecord]) -> Int {
        guard !records.isEmpty else { return 0 }
        let calendar = Calendar.current
        let sortedDates = Set(records.map { calendar.startOfDay(for: $0.date) }).sorted(by: >)

        var streak = 0
        var expectedDate = calendar.startOfDay(for: Date())

        for date in sortedDates {
            if date == expectedDate {
                streak += 1
                expectedDate = calendar.date(byAdding: .day, value: -1, to: expectedDate)!
            } else if date < expectedDate {
                break
            }
        }
        return streak
    }
}
