//
//  OnboardingContainerView.swift
//  TreningsCoach
//
//  Manages the onboarding flow: Language -> Auth -> Training Level
//

import SwiftUI

enum OnboardingStep {
    case language
    case auth
    case trainingLevel
}

struct OnboardingContainerView: View {
    @ObservedObject var authManager: AuthManager
    let onComplete: () -> Void

    @State private var currentStep: OnboardingStep = .language

    var body: some View {
        Group {
            switch currentStep {
            case .language:
                LanguageSelectionView { language in
                    L10n.set(language)
                    withAnimation {
                        currentStep = .auth
                    }
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing),
                    removal: .move(edge: .leading)
                ))

            case .auth:
                AuthView(authManager: authManager)
                    .onChange(of: authManager.isAuthenticated) { _, isAuth in
                        if isAuth {
                            withAnimation {
                                currentStep = .trainingLevel
                            }
                        }
                    }
                    .transition(.asymmetric(
                        insertion: .move(edge: .trailing),
                        removal: .move(edge: .leading)
                    ))

            case .trainingLevel:
                TrainingLevelView(authManager: authManager) {
                    onComplete()
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing),
                    removal: .move(edge: .leading)
                ))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: currentStep == .language)
        .animation(.easeInOut(duration: 0.3), value: currentStep == .auth)
        .animation(.easeInOut(duration: 0.3), value: currentStep == .trainingLevel)
    }
}
