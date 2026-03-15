//
//  TreningsCoachApp.swift
//  TreningsCoach
//
//  Created by Marius Gaarder
//  iOS Workout Coaching App with Real-time Voice Feedback
//

import SwiftUI
import UIKit

final class CoachiAppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil
    ) -> Bool {
        _ = application
        _ = launchOptions
        PushNotificationManager.shared.configure()
        Task {
            await PushNotificationManager.shared.registerForRemoteNotificationsIfAuthorized()
        }
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        _ = application
        PushNotificationManager.shared.handleDidRegisterForRemoteNotifications(deviceToken: deviceToken)
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        _ = application
        PushNotificationManager.shared.handleDidFailToRegisterForRemoteNotifications(error: error)
    }
}

@main
struct TreningsCoachApp: App {
    @UIApplicationDelegateAdaptor(CoachiAppDelegate.self) private var appDelegate
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
