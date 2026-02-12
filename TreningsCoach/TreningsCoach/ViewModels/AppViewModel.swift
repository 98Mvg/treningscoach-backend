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
    @AppStorage("training_level") var trainingLevelRaw: String = "intermediate"
    @AppStorage("app_language") var languageCode: String = "en"

    var userProfile: LocalProfile {
        LocalProfile(
            name: userName.isEmpty ? L10n.athlete : userName,
            trainingLevel: trainingLevelRaw,
            language: languageCode,
            weeklyGoal: 4
        )
    }

    let authManager = AuthManager()

    func completeOnboarding(name: String, level: String) {
        userName = name
        trainingLevelRaw = level
        hasCompletedOnboarding = true
    }

    func resetOnboarding() {
        hasCompletedOnboarding = false
    }
}
