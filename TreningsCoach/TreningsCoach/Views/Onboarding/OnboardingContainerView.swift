//
//  OnboardingContainerView.swift
//  TreningsCoach
//
//  5-step onboarding: Welcome → Language → Features → Account → Setup
//

import SwiftUI

enum OnboardingStep: Int {
    case welcome = 0
    case language = 1
    case features = 2
    case auth = 3
    case setup = 4
}

struct OnboardingContainerView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @State private var currentStep: OnboardingStep = .welcome

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            Group {
                switch currentStep {
                case .welcome:
                    WelcomePageView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .language }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .language:
                    LanguageSelectionView { language in
                        L10n.set(language)
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .features }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .features:
                    FeaturesPageView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .auth }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .auth:
                    AuthView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .setup }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .setup:
                    SetupPageView { name, level in
                        appViewModel.completeOnboarding(name: name, level: level)
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))
                }
            }
        }
        .animation(AppConfig.Anim.transitionSpring, value: currentStep.rawValue)
    }
}
