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

    let authManager = AuthManager()

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

    func completeOnboarding(name: String, level _: String) {
        userName = name
        trainingLevelRaw = "beginner"
        goodCoachWorkoutCount = 0
        hasCompletedOnboarding = true
        if !spotifyPromptSeen {
            spotifyPromptPending = true
        }
    }

    func resetOnboarding() {
        hasCompletedOnboarding = false
    }
}
