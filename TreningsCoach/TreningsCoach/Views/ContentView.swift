//
//  ContentView.swift → MainTabView
//  TreningsCoach
//
//  Main tab container with floating tab bar — Coachi design
//

import SwiftUI

struct MainTabView: View {
    @StateObject private var workoutViewModel = WorkoutViewModel()
    @State private var selectedTab: TabItem = .home

    var body: some View {
        ZStack(alignment: .bottom) {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            // Keep all tab views alive to prevent .task cancellation on tab switch
            HomeView { selectedTab = .workout }
                .opacity(selectedTab == .home ? 1 : 0)
                .allowsHitTesting(selectedTab == .home)

            workoutContent
                .opacity(selectedTab == .workout ? 1 : 0)
                .allowsHitTesting(selectedTab == .workout)

            ProfileView()
                .opacity(selectedTab == .profile ? 1 : 0)
                .allowsHitTesting(selectedTab == .profile)

            if workoutViewModel.workoutState == .idle && !workoutViewModel.showComplete {
                CustomTabBar(selectedTab: $selectedTab)
                    .padding(.bottom, 16)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .environmentObject(workoutViewModel)
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.workoutState)
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.showComplete)
        .onAppear {
            workoutViewModel.presentSpotifyPromptIfNeeded()
        }
        .fullScreenCover(isPresented: $workoutViewModel.showSpotifyConnectSheet) {
            SpotifyConnectView(viewModel: workoutViewModel)
        }
    }

    @ViewBuilder
    private var workoutContent: some View {
        switch workoutViewModel.workoutState {
        case .idle:
            WorkoutLaunchView(viewModel: workoutViewModel)
        case .active, .paused:
            ActiveWorkoutView(viewModel: workoutViewModel)
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
        case .complete:
            WorkoutCompleteView(viewModel: workoutViewModel)
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
        }
    }
}
