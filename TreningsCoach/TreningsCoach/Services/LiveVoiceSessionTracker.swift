//
//  LiveVoiceSessionTracker.swift
//  TreningsCoach
//
//  Tracks free-tier Live Voice session usage.
//  - Daily limit:   AppConfig.LiveVoice.freeSessionsPerDay (3)
//  - Premium users: no limits enforced and are not counted locally
//
//  State is UserDefaults-backed. Daily counter resets automatically on a new calendar day.
//

import Foundation

@MainActor
final class LiveVoiceSessionTracker: ObservableObject {

    static let shared = LiveVoiceSessionTracker()

    // MARK: - Published State

    @Published private(set) var sessionsUsedToday: Int = 0

    // MARK: - Private

    private let defaults = UserDefaults.standard
    private let countKey = "live_voice_daily_count"
    private let dateKey  = "live_voice_daily_date"

    private init() {
        refreshDailyCount()
    }

    // MARK: - Query

    /// Whether a free-tier user can start another live voice session today.
    func canStart(isPremium: Bool) -> Bool {
        if isPremium { return true }
        refreshDailyCount()
        return sessionsUsedToday < AppConfig.LiveVoice.freeSessionsPerDay
    }

    /// Remaining sessions today for free-tier users. Returns nil for premium.
    func remainingToday(isPremium: Bool) -> Int? {
        if isPremium { return nil }
        refreshDailyCount()
        return max(0, AppConfig.LiveVoice.freeSessionsPerDay - sessionsUsedToday)
    }

    // MARK: - Mutation

    /// Call when a live voice session is successfully started.
    func recordSession(isPremium: Bool) {
        if isPremium { return }
        refreshDailyCount()
        let updated = sessionsUsedToday + 1
        defaults.set(updated, forKey: countKey)
        sessionsUsedToday = updated
    }

    // MARK: - Private Helpers

    private func refreshDailyCount() {
        let today = currentDateString()
        if defaults.string(forKey: dateKey) == today {
            sessionsUsedToday = defaults.integer(forKey: countKey)
        } else {
            // New day — reset counter
            defaults.set(today, forKey: dateKey)
            defaults.set(0,     forKey: countKey)
            sessionsUsedToday = 0
        }
    }

    private func currentDateString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }
}
