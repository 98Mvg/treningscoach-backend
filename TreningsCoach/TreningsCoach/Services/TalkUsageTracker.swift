//
//  TalkUsageTracker.swift
//  TreningsCoach
//
//  Tracks free-tier Talk-to-Coach usage.
//  - Per-session limit:  AppConfig.Subscription.freeTalkQuestionsPerWorkout (1)
//  - Daily limit:        AppConfig.Subscription.freeTalkQuestionsPerDay (3)
//  - Premium users:      no limits enforced here, caller skips tracking
//
//  State is UserDefaults-backed. Daily counter resets automatically on a new calendar day.
//

import Foundation

@MainActor
final class TalkUsageTracker: ObservableObject {

    static let shared = TalkUsageTracker()

    // MARK: - Published State

    @Published private(set) var talksUsedToday: Int = 0

    // MARK: - Private

    private let defaults = UserDefaults.standard
    private let dailyCountKey = "talk_usage_daily_count"
    private let dailyDateKey  = "talk_usage_daily_date"

    private init() {
        refreshDailyCount()
    }

    // MARK: - Query

    /// Whether a free-tier user can send another question in this session and today.
    func canAsk(sessionUsed: Int, isPremium: Bool) -> Bool {
        if isPremium { return true }
        refreshDailyCount()
        let bySession = sessionUsed < AppConfig.Subscription.freeTalkQuestionsPerWorkout
        let byDay     = talksUsedToday < AppConfig.Subscription.freeTalkQuestionsPerDay
        return bySession && byDay
    }

    /// Remaining questions the user can ask today (free tier). Returns nil for premium.
    func remainingToday(isPremium: Bool) -> Int? {
        if isPremium { return nil }
        refreshDailyCount()
        return max(0, AppConfig.Subscription.freeTalkQuestionsPerDay - talksUsedToday)
    }

    // MARK: - Mutation

    /// Call after successfully sending a question and receiving a reply.
    func recordQuestion() {
        refreshDailyCount()
        let updated = talksUsedToday + 1
        defaults.set(updated, forKey: dailyCountKey)
        talksUsedToday = updated
    }

    // MARK: - Private Helpers

    private func refreshDailyCount() {
        let today = currentDateString()
        if defaults.string(forKey: dailyDateKey) == today {
            talksUsedToday = defaults.integer(forKey: dailyCountKey)
        } else {
            // New day — reset counter
            defaults.set(today, forKey: dailyDateKey)
            defaults.set(0,     forKey: dailyCountKey)
            talksUsedToday = 0
        }
    }

    private func currentDateString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }
}
