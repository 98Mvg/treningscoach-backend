//
//  ContentView.swift → MainTabView
//  TreningsCoach
//
//  Main tab container with floating tab bar — Coachi design
//

import SwiftUI

struct MainTabView: View {
    @EnvironmentObject private var appViewModel: AppViewModel
    @EnvironmentObject private var subscriptionManager: SubscriptionManager
    @StateObject private var workoutViewModel = WorkoutViewModel()
    @State private var selectedTab: TabItem = .home
    @State private var didTrackAppOpen = false
    @State private var deepLinkPaywallContext: PaywallContext?
    @State private var isManageSubscriptionPresented = false

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

            ProfileView(
                selectedTab: $selectedTab,
                isManageSubscriptionPresented: $isManageSubscriptionPresented
            )
                .opacity(selectedTab == .profile ? 1 : 0)
                .allowsHitTesting(selectedTab == .profile)

            if workoutViewModel.workoutState == .idle
                && !workoutViewModel.showComplete
                && !isManageSubscriptionPresented {
                CustomTabBar(selectedTab: $selectedTab)
                    .padding(.bottom, 8)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .environmentObject(workoutViewModel)
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.workoutState)
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.showComplete)
        .onAppear {
            if !didTrackAppOpen {
                didTrackAppOpen = true
                Task {
                    _ = await BackendAPIService.shared.trackAnalyticsEvent(event: "app_opened")
                }
            }
            if let pendingDeepLink = appViewModel.pendingDeepLink {
                handleDeepLink(pendingDeepLink)
            }
            workoutViewModel.presentSpotifyPromptIfNeeded()
            workoutViewModel.triggerAudioPackSync()
        }
        .onChange(of: appViewModel.pendingDeepLink) { _, deepLink in
            guard let deepLink else { return }
            handleDeepLink(deepLink)
        }
        .fullScreenCover(isPresented: $workoutViewModel.showSpotifyConnectSheet) {
            SpotifyConnectView(viewModel: workoutViewModel)
        }
        .sheet(item: $deepLinkPaywallContext) { context in
            PaywallView(context: context)
                .environmentObject(subscriptionManager)
        }
    }

    @ViewBuilder
    private var workoutContent: some View {
        switch workoutViewModel.workoutState {
        case .idle:
            WorkoutLaunchView(
                viewModel: workoutViewModel,
                showsAnimatedBackground: selectedTab == .workout
            )
        case .active, .paused:
            ActiveWorkoutView(viewModel: workoutViewModel)
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
        case .complete:
            WorkoutCompleteView(viewModel: workoutViewModel)
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
        }
    }

    private func handleDeepLink(_ deepLink: AppDeepLinkDestination) {
        switch deepLink {
        case .home:
            selectedTab = .home
        case .workout:
            selectedTab = .workout
        case .profile:
            selectedTab = .profile
        case let .paywall(context):
            deepLinkPaywallContext = PaywallContext.fromDeepLinkValue(context)
        case .manageSubscription:
            subscriptionManager.manageSubscription()
        case .restorePurchases:
            Task { await subscriptionManager.restorePurchases() }
        }

        Task {
            _ = await BackendAPIService.shared.trackAnalyticsEvent(
                event: "deep_link_opened",
                metadata: ["destination": deepLink.analyticsContext]
            )
        }
        appViewModel.consumePendingDeepLink()
    }
}
