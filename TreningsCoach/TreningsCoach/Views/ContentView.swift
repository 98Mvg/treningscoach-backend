//
//  ContentView.swift
//  TreningsCoach
//
//  Tab container — hosts Home, Workout, and Profile tabs
//  WorkoutViewModel is created here and shared to all child views
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = WorkoutViewModel()
    @State private var selectedTab = 1  // Default to Workout tab (center)

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView(viewModel: viewModel, selectedTab: $selectedTab)
                .tabItem {
                    Label(L10n.current == .no ? "Hjem" : "Home", systemImage: "house.fill")
                }
                .tag(0)

            WorkoutView(viewModel: viewModel)
                .tabItem {
                    Label(L10n.current == .no ? "Trening" : "Workout", systemImage: "waveform")
                }
                .tag(1)

            ProfileView(viewModel: viewModel)
                .environmentObject(authManager)
                .tabItem {
                    Label(L10n.current == .no ? "Profil" : "Profile", systemImage: "person.fill")
                }
                .tag(2)
        }
        .tint(AppTheme.primaryAccent)
        .onAppear {
            // Style the tab bar for dark theme
            let appearance = UITabBarAppearance()
            appearance.configureWithOpaqueBackground()
            appearance.backgroundColor = UIColor(AppTheme.cardSurface)

            // Unselected tab items
            appearance.stackedLayoutAppearance.normal.iconColor = UIColor(AppTheme.textSecondary)
            appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
                .foregroundColor: UIColor(AppTheme.textSecondary)
            ]

            // Selected tab items
            appearance.stackedLayoutAppearance.selected.iconColor = UIColor(AppTheme.primaryAccent)
            appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
                .foregroundColor: UIColor(AppTheme.primaryAccent)
            ]

            UITabBar.appearance().standardAppearance = appearance
            UITabBar.appearance().scrollEdgeAppearance = appearance
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - Preview

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(AuthManager())
    }
}
