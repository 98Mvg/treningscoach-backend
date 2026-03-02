import SwiftUI

struct MainTabView: View {
    @StateObject private var workoutViewModel = WorkoutViewModel()
    @State private var selectedTab: TabItem = .home

    var body: some View {
        ZStack(alignment: .bottom) {
            // Background
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            // Content
            Group {
                switch selectedTab {
                case .home:
                    HomeView {
                        selectedTab = .workout
                    }

                case .workout:
                    workoutContent

                case .profile:
                    ProfileView()
                }
            }

            // Tab bar (hidden during active workout)
            if workoutViewModel.workoutState == .idle && !workoutViewModel.showComplete {
                CustomTabBar(selectedTab: $selectedTab)
                    .padding(.bottom, 16)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.workoutState)
        .animation(AppConfig.Anim.transitionSpring, value: workoutViewModel.showComplete)
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

#Preview {
    MainTabView()
        .environmentObject(AppViewModel())
}
