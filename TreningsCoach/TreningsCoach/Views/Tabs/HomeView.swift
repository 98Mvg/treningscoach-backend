//
//  HomeView.swift
//  TreningsCoach
//
//  Coachi home screen with greeting, weekly ring, stats, recent workouts
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var workoutViewModel: WorkoutViewModel
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
                            .font(.system(size: 16, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
                        Text(appViewModel.userProfile.name)
                            .font(.system(size: 28, weight: .bold)).foregroundColor(CoachiTheme.textPrimary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24).padding(.top, 16).opacity(appeared ? 1 : 0)

                // Weekly progress
                VStack(spacing: 12) {
                    WeeklyProgressRing(completed: viewModel.stats.workoutsThisWeek, goal: viewModel.stats.weeklyGoal, size: 140)
                    Text("\(viewModel.stats.workoutsThisWeek) \(L10n.of) \(viewModel.stats.weeklyGoal) \(L10n.workoutsCompleted)")
                        .font(.system(size: 14, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
                }
                .padding(.top, 32).opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

                // Experience level progression (gameified via good CoachScore workouts)
                VStack(alignment: .leading, spacing: 10) {
                    Text(appViewModel.levelBadgeLine)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(CoachiTheme.surface.opacity(0.8))
                            Capsule()
                                .fill(CoachiTheme.success)
                                .frame(width: max(8, geo.size.width * appViewModel.levelProgressFraction))
                        }
                    }
                    .frame(height: 10)

                    Text(appViewModel.levelProgressLine)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                }
                .padding(14)
                .cardStyle()
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .opacity(appeared ? 1 : 0)

                // Start button
                PulseButtonView(title: L10n.startWorkout, icon: "play.fill", size: 140) { onStartWorkout() }
                    .padding(.top, 36).opacity(appeared ? 1 : 0)

                // Spotify quick access + status
                Button {
                    workoutViewModel.handleSpotifyButtonTapped()
                } label: {
                    HStack(spacing: 12) {
                        SpotifyLogoBadge(size: 34)

                        VStack(alignment: .leading, spacing: 3) {
                            Text("Spotify")
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(CoachiTheme.textPrimary)

                            HStack(spacing: 6) {
                                Circle()
                                    .fill(workoutViewModel.isSpotifyConnected ? CoachiTheme.success : CoachiTheme.textTertiary)
                                    .frame(width: 8, height: 8)
                                Text(
                                    workoutViewModel.isSpotifyConnected
                                        ? (L10n.current == .no ? "Tilkoblet" : "Connected")
                                        : (L10n.current == .no ? "Ikke tilkoblet" : "Not connected")
                                )
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                            }
                        }

                        Spacer()

                        Text(
                            workoutViewModel.isSpotifyConnected
                                ? (L10n.current == .no ? "Åpne" : "Open")
                                : (L10n.current == .no ? "Koble til" : "Connect")
                        )
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(CoachiTheme.primary)
                    }
                    .padding(14)
                    .cardStyle()
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 20)
                .padding(.top, 22)
                .opacity(appeared ? 1 : 0)

                // Waveform
                WaveformView(isActive: false, barCount: 14, height: 40)
                    .padding(.horizontal, 60).padding(.top, 16).opacity(appeared ? 1 : 0)

                // Stats row
                HStack(spacing: 12) {
                    StatCardView(icon: "flame.fill", value: "\(viewModel.stats.totalWorkouts)", label: L10n.workouts)
                    StatCardView(icon: "clock.fill", value: "\(viewModel.stats.totalMinutes)", label: L10n.minutes, color: CoachiTheme.secondary)
                    StatCardView(icon: "bolt.fill", value: "\(viewModel.stats.currentStreak)", label: L10n.streak, color: CoachiTheme.accent)
                }
                .padding(.horizontal, 20).padding(.top, 36).opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 15)

                // Recent workouts
                if !viewModel.recentWorkouts.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.recentWorkouts).font(.system(size: 18, weight: .bold)).foregroundColor(CoachiTheme.textPrimary).padding(.horizontal, 24)
                        ForEach(viewModel.recentWorkouts.prefix(4)) { workout in
                            RecentWorkoutRow(workout: workout).padding(.horizontal, 20)
                        }
                    }
                    .padding(.top, 32).opacity(appeared ? 1 : 0)
                }

                // Empty state
                if viewModel.recentWorkouts.isEmpty && !viewModel.isLoading {
                    VStack(spacing: 12) {
                        Image(systemName: "figure.cooldown")
                            .font(.system(size: 40))
                            .foregroundColor(CoachiTheme.textTertiary)
                        Text(L10n.noWorkoutsYet)
                            .font(.system(size: 16, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
                        Text(L10n.tapStartWorkout)
                            .font(.system(size: 14)).foregroundColor(CoachiTheme.textTertiary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 32).opacity(appeared ? 1 : 0)
                }

                Spacer().frame(height: 100)
            }
        }
        .task {
            await viewModel.loadData()
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }
}
