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
    @StateObject private var appViewModel = AppViewModel()
    @StateObject private var subscriptionManager = SubscriptionManager.shared
    @AppStorage("app_dark_mode_enabled") private var darkModeEnabled: Bool = true

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appViewModel)
                .environmentObject(appViewModel.authManager)
                .environmentObject(subscriptionManager)
                .preferredColorScheme(darkModeEnabled ? .dark : .light)
                .task {
                    await subscriptionManager.initialize()
                }
                .onOpenURL { url in
                    appViewModel.handleIncomingURL(url)
                }
        }
    }
}
