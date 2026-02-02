//
//  TreningsCoachApp.swift
//  TreningsCoach
//
//  Created by Marius Gaarder
//  iOS Workout Coaching App with Real-time Voice Feedback
//

import SwiftUI

@main
struct TreningsCoachApp: App {
    @StateObject private var authManager = AuthManager()
    @State private var hasCompletedOnboarding = UserDefaults.standard.bool(forKey: "has_completed_onboarding")

    var body: some Scene {
        WindowGroup {
            if hasCompletedOnboarding {
                ContentView()
                    .environmentObject(authManager)
            } else {
                OnboardingContainerView(authManager: authManager) {
                    withAnimation {
                        hasCompletedOnboarding = true
                    }
                }
            }
        }
    }
}
