import SwiftUI

struct HomeView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @StateObject private var viewModel = HomeViewModel()
    @State private var appeared = false

    let onStartWorkout: () -> Void

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                // Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(viewModel.greeting + ",")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                        Text(appViewModel.userProfile.name)
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24)
                .padding(.top, 16)
                .opacity(appeared ? 1 : 0)

                // Weekly progress
                VStack(spacing: 12) {
                    WeeklyProgressRing(
                        completed: viewModel.stats.workoutsThisWeek,
                        goal: viewModel.stats.weeklyGoal,
                        size: 140
                    )

                    Text("\(viewModel.stats.workoutsThisWeek) of \(viewModel.stats.weeklyGoal) workouts this week")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                }
                .padding(.top, 32)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 20)

                // Start button
                PulseButtonView(title: "Start\nworkout", icon: "play.fill", size: 140) {
                    onStartWorkout()
                }
                .padding(.top, 36)
                .opacity(appeared ? 1 : 0)

                // Waveform
                WaveformView(isActive: false, barCount: 14, height: 40)
                    .padding(.horizontal, 60)
                    .padding(.top, 16)
                    .opacity(appeared ? 1 : 0)

                // Stats row
                HStack(spacing: 12) {
                    StatCardView(icon: "flame.fill", value: "\(viewModel.stats.totalWorkouts)", label: "Workouts")
                    StatCardView(icon: "clock.fill", value: "\(viewModel.stats.totalMinutes)", label: "Minutes", color: CoachiTheme.secondary)
                    StatCardView(icon: "bolt.fill", value: "\(viewModel.stats.currentStreak)", label: "Streak", color: CoachiTheme.accent)
                }
                .padding(.horizontal, 20)
                .padding(.top, 36)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 15)

                // Recent workouts
                if !viewModel.recentWorkouts.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Recent Workouts")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .padding(.horizontal, 24)

                        ForEach(viewModel.recentWorkouts.prefix(4)) { workout in
                            RecentWorkoutRow(workout: workout)
                                .padding(.horizontal, 20)
                        }
                    }
                    .padding(.top, 32)
                    .opacity(appeared ? 1 : 0)
                }

                // Bottom padding for tab bar
                Spacer()
                    .frame(height: 100)
            }
        }
        .task {
            await viewModel.loadData()
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) {
                appeared = true
            }
        }
    }
}

#Preview {
    ZStack {
        CoachiTheme.backgroundGradient.ignoresSafeArea()
        HomeView { }
            .environmentObject(AppViewModel())
    }
}
