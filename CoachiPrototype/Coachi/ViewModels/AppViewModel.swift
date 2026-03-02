import SwiftUI

@MainActor
class AppViewModel: ObservableObject {
    @AppStorage("has_completed_onboarding") var hasCompletedOnboarding = false
    @AppStorage("user_name") var userName = ""
    @AppStorage("training_level") var trainingLevelRaw = TrainingLevel.intermediate.rawValue

    var trainingLevel: TrainingLevel {
        get { TrainingLevel(rawValue: trainingLevelRaw) ?? .intermediate }
        set { trainingLevelRaw = newValue.rawValue }
    }

    var userProfile: UserProfile {
        UserProfile(
            name: userName.isEmpty ? "Athlete" : userName,
            trainingLevel: trainingLevel,
            language: "en",
            weeklyGoal: 5
        )
    }

    func completeOnboarding(name: String, level: TrainingLevel) {
        userName = name.isEmpty ? "Athlete" : name
        trainingLevel = level
        withAnimation(AppConfig.Anim.transitionSpring) {
            hasCompletedOnboarding = true
        }
    }

    func resetOnboarding() {
        withAnimation(AppConfig.Anim.transitionSpring) {
            hasCompletedOnboarding = false
        }
    }
}
