//
//  ProfileViewModel.swift
//  TreningsCoach
//
//  User stats wrapper for profile screen
//

import Foundation

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var stats: UserStats = UserStats()

    private let apiService = BackendAPIService.shared

    func loadStats() async {
        do {
            let history = try await apiService.getWorkoutHistory(limit: 50)
            stats.totalWorkouts = history.count
            stats.totalMinutes = history.reduce(0) { $0 + $1.durationSeconds } / 60

            let calendar = Calendar.current
            let weekStart = calendar.date(from: calendar.dateComponents([.yearForWeekOfYear, .weekOfYear], from: Date())) ?? Date()
            stats.workoutsThisWeek = history.filter { $0.date >= weekStart }.count
        } catch {
            print("⚠️ Failed to load stats: \(error.localizedDescription)")
        }
    }
}
