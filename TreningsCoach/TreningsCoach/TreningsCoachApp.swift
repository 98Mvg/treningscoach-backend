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

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appViewModel)
                .environmentObject(appViewModel.authManager)
        }
    }
}
