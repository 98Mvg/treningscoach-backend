//
//  RootView.swift
//  TreningsCoach
//
//  Root view — shows onboarding or main app based on AppViewModel state
//

import SwiftUI

struct RootView: View {
    @EnvironmentObject var appViewModel: AppViewModel

    var body: some View {
        Group {
            if appViewModel.hasCompletedOnboarding {
                MainTabView()
                    .transition(.opacity)
            } else {
                OnboardingContainerView()
                    .transition(.opacity)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .animation(AppConfig.Anim.transitionSpring, value: appViewModel.hasCompletedOnboarding)
    }
}
