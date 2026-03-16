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
        sessionsUsedToday = currentStoredCount(resetIfNeeded: true)
    }

    // MARK: - Query

    /// Whether a free-tier user can start another live voice session today.
    func canStart(isPremium: Bool) -> Bool {
        if isPremium { return true }
        return currentStoredCount(resetIfNeeded: false) < AppConfig.LiveVoice.freeSessionsPerDay
    }

    /// Remaining sessions today for free-tier users. Returns nil for premium.
    func remainingToday(isPremium: Bool) -> Int? {
        if isPremium { return nil }
        let used = currentStoredCount(resetIfNeeded: false)
        return max(0, AppConfig.LiveVoice.freeSessionsPerDay - used)
    }

    func synchronize() {
        publishSessionsUsedToday(currentStoredCount(resetIfNeeded: true))
    }

    // MARK: - Mutation

    /// Call when a live voice session is successfully started.
    func recordSession(isPremium: Bool) {
        if isPremium { return }
        let updated = currentStoredCount(resetIfNeeded: true) + 1
        defaults.set(updated, forKey: countKey)
        publishSessionsUsedToday(updated)
    }

    // MARK: - Private Helpers

    private func currentStoredCount(resetIfNeeded: Bool) -> Int {
        let today = currentDateString()
        if defaults.string(forKey: dateKey) == today {
            return defaults.integer(forKey: countKey)
        }

        if resetIfNeeded {
            defaults.set(today, forKey: dateKey)
            defaults.set(0, forKey: countKey)
        }

        return 0
    }

    private func currentDateString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }

    private func publishSessionsUsedToday(_ value: Int) {
        guard sessionsUsedToday != value else { return }
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            guard self.sessionsUsedToday != value else { return }
            self.sessionsUsedToday = value
        }
    }
}
