//
//  AppViewModel.swift
//  TreningsCoach
//
//  App-level state: onboarding, user profile, language
//

import Foundation
import SwiftUI

struct LocalProfile {
    var name: String
    var trainingLevel: String
    var language: String
    var weeklyGoal: Int
}

extension AppViewModel {
    struct OnboardingProfileDraft {
        var firstName: String
        var lastName: String
        var birthDate: Date
        var gender: String
        var heightCm: Int
        var weightKg: Int
        var hrMax: Int
        var restingHR: Int
        var doesEnduranceTraining: Bool
        var hardestIntensity: String
        var moderateSessionsPerWeek: String
        var moderateDuration: String
        var notificationsOptIn: Bool
        var languageCode: String
        var trainingLevel: String

        var displayName: String {
            let first = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
            let last = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
            let joined = [first, last].filter { !$0.isEmpty }.joined(separator: " ")
            return joined.isEmpty ? L10n.athlete : joined
        }

        var age: Int {
            let years = Calendar.current.dateComponents([.year], from: birthDate, to: Date()).year ?? 0
            return max(14, min(95, years))
        }
    }
}

@MainActor
class AppViewModel: ObservableObject {
    @AppStorage("has_completed_onboarding") var hasCompletedOnboarding: Bool = false
    @AppStorage("user_display_name") var userName: String = ""
    @AppStorage("training_level") var trainingLevelRaw: String = "beginner"
    @AppStorage("good_coach_workout_count") var goodCoachWorkoutCount: Int = 0
    @AppStorage("app_language") var languageCode: String = "en"
    @AppStorage("spotify_prompt_pending") private var spotifyPromptPending: Bool = false
    @AppStorage("spotify_prompt_seen") private var spotifyPromptSeen: Bool = false

    var userProfile: LocalProfile {
        LocalProfile(
            name: userName.isEmpty ? L10n.athlete : userName,
            trainingLevel: trainingLevelRaw,
            language: languageCode,
            weeklyGoal: 4
        )
    }

    let authManager = AuthManager.shared
    private let backendAPI = BackendAPIService.shared

    var trainingLevelDisplayName: String {
        switch trainingLevelRaw {
        case "advanced":
            return L10n.current == .no ? "Avansert" : "Advanced"
        case "intermediate":
            return L10n.current == .no ? "Middels" : "Intermediate"
        default:
            return L10n.current == .no ? "Nybegynner" : "Beginner"
        }
    }

    var levelProgressFraction: Double {
        guard let target = nextLevelTargetCount else { return 1.0 }
        let start = currentLevelStartCount
        let span = max(1, target - start)
        let progress = max(0, min(span, goodCoachWorkoutCount - start))
        return Double(progress) / Double(span)
    }

    var levelProgressLine: String {
        guard let target = nextLevelTargetCount else {
            return L10n.current == .no
                ? "Maksnivå nådd • \(goodCoachWorkoutCount) gode økter"
                : "Max level reached • \(goodCoachWorkoutCount) good workouts"
        }

        let start = currentLevelStartCount
        let needed = max(1, target - start)
        let progress = max(0, min(needed, goodCoachWorkoutCount - start))
        if L10n.current == .no {
            return "\(progress)/\(needed) gode økter til neste nivå"
        }
        return "\(progress)/\(needed) good workouts to next level"
    }

    var levelBadgeLine: String {
        if L10n.current == .no {
            return "Nivå \(trainingLevelDisplayName)"
        }
        return "Level \(trainingLevelDisplayName)"
    }

    private var currentLevelStartCount: Int {
        switch trainingLevelRaw {
        case "advanced":
            return AppConfig.Progression.advancedAtGoodWorkouts
        case "intermediate":
            return AppConfig.Progression.intermediateAtGoodWorkouts
        default:
            return 0
        }
    }

    private var nextLevelTargetCount: Int? {
        switch trainingLevelRaw {
        case "advanced":
            return nil
        case "intermediate":
            return AppConfig.Progression.advancedAtGoodWorkouts
        default:
            return AppConfig.Progression.intermediateAtGoodWorkouts
        }
    }

    func completeOnboarding(profile: OnboardingProfileDraft) {
        let defaults = UserDefaults.standard
        userName = profile.displayName
        trainingLevelRaw = profile.trainingLevel
        languageCode = profile.languageCode
        goodCoachWorkoutCount = 0

        defaults.set(profile.displayName, forKey: "user_display_name")
        defaults.set(profile.trainingLevel, forKey: "training_level")
        defaults.set(profile.languageCode, forKey: "app_language")

        defaults.set(profile.firstName, forKey: "user_first_name")
        defaults.set(profile.lastName, forKey: "user_last_name")
        defaults.set(profile.birthDate.timeIntervalSince1970, forKey: "user_birthdate_ts")
        defaults.set(profile.age, forKey: "user_age")
        defaults.set(profile.gender, forKey: "user_gender")
        defaults.set(profile.heightCm, forKey: "user_height_cm")
        defaults.set(profile.weightKg, forKey: "user_weight_kg")

        defaults.set(profile.hrMax, forKey: "hr_max")
        defaults.set(profile.restingHR, forKey: "resting_hr")

        defaults.set(profile.doesEnduranceTraining, forKey: "user_endurance_training")
        defaults.set(profile.hardestIntensity, forKey: "user_hardest_intensity")
        defaults.set(profile.moderateSessionsPerWeek, forKey: "user_moderate_sessions_per_week")
        defaults.set(profile.moderateDuration, forKey: "user_moderate_duration")
        defaults.set(profile.notificationsOptIn, forKey: "notifications_opt_in")

        hasCompletedOnboarding = true
        if !spotifyPromptSeen {
            spotifyPromptPending = true
        }

        Task {
            await syncProfileToBackend(reason: "onboarding")
        }
    }

    func resetOnboarding() {
        let defaults = UserDefaults.standard
        let keysToClear = [
            "user_display_name",
            "training_level",
            "user_first_name",
            "user_last_name",
            "user_birthdate_ts",
            "user_age",
            "user_gender",
            "user_height_cm",
            "user_weight_kg",
            "hr_max",
            "resting_hr",
            "user_endurance_training",
            "user_hardest_intensity",
            "user_moderate_sessions_per_week",
            "user_moderate_duration",
            "notifications_opt_in",
        ]
        keysToClear.forEach { defaults.removeObject(forKey: $0) }

        userName = ""
        trainingLevelRaw = "beginner"
        hasCompletedOnboarding = false
    }

    func syncProfileToBackend(reason: String) async {
        guard authManager.hasUsableSession() else { return }
        let defaults = UserDefaults.standard
        let payload = BackendUserProfilePayload(
            name: defaults.string(forKey: "user_display_name"),
            sex: defaults.string(forKey: "user_gender"),
            age: defaults.object(forKey: "user_age") as? Int,
            heightCm: defaults.object(forKey: "user_height_cm") as? Int,
            weightKg: defaults.object(forKey: "user_weight_kg") as? Int,
            maxHrBpm: defaults.object(forKey: "hr_max") as? Int,
            restingHrBpm: defaults.object(forKey: "resting_hr") as? Int,
            profileUpdatedAt: ISO8601DateFormatter().string(from: Date())
        )
        do {
            try await backendAPI.upsertUserProfile(payload)
            print("📤 Profile upsert reason=\(reason)")
        } catch {
            print("⚠️ Profile upsert failed reason=\(reason) error=\(error.localizedDescription)")
        }
    }
}
