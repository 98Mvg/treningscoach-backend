//
//  HomeView.swift
//  TreningsCoach
//
//  Dashboard home screen
//  Shows greeting, weekly progress, quick-start button, recent workouts
//

import SwiftUI

struct HomeView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @Binding var selectedTab: Int

    var body: some View {
        ZStack {
            // Dark background
            AppTheme.backgroundGradient.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {

                    // MARK: - Greeting Header
                    VStack(alignment: .leading, spacing: 4) {
                        Text(viewModel.greetingText + ",")
                            .font(.title2)
                            .foregroundStyle(AppTheme.textSecondary)

                        Text(UserDefaults.standard.string(forKey: "user_display_name") ?? L10n.athlete)
                            .font(.largeTitle.bold())
                            .foregroundStyle(AppTheme.textPrimary)
                    }
                    .padding(.top, 20)

                    // MARK: - Weekly Progress Card
                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.thisWeek)
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(AppTheme.textSecondary)

                        // Progress text
                        HStack {
                            Text("\(viewModel.userStats.workoutsThisWeek) \(L10n.of) \(viewModel.userStats.weeklyGoal)")
                                .font(.title3.bold())
                                .foregroundStyle(AppTheme.textPrimary)

                            Text(L10n.workoutsCompleted)
                                .font(.subheadline)
                                .foregroundStyle(AppTheme.textSecondary)

                            Spacer()
                        }

                        // Progress bar
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                // Track
                                Capsule()
                                    .fill(AppTheme.primaryAccent.opacity(0.2))
                                    .frame(height: 8)

                                // Fill
                                Capsule()
                                    .fill(
                                        LinearGradient(
                                            colors: [AppTheme.primaryAccent, AppTheme.secondaryAccent],
                                            startPoint: .leading,
                                            endPoint: .trailing
                                        )
                                    )
                                    .frame(
                                        width: geo.size.width * progressFraction,
                                        height: 8
                                    )
                                    .animation(.easeInOut(duration: 0.5), value: viewModel.userStats.workoutsThisWeek)
                            }
                        }
                        .frame(height: 8)
                    }
                    .padding(20)
                    .cardStyle()

                    // MARK: - Quick Start Button
                    Button {
                        // Switch to workout tab and start
                        selectedTab = 1
                        if !viewModel.isContinuousMode {
                            viewModel.startContinuousWorkout()
                        }
                    } label: {
                        HStack(spacing: 16) {
                            Image(systemName: "figure.run")
                                .font(.title)
                                .foregroundStyle(.white)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(L10n.startWorkout)
                                    .font(.title3.bold())
                                    .foregroundStyle(.white)

                                Text(L10n.audioCoachingStarts)
                                    .font(.caption)
                                    .foregroundStyle(.white.opacity(0.7))
                            }

                            Spacer()

                            Image(systemName: "chevron.right")
                                .font(.title3)
                                .foregroundStyle(.white.opacity(0.5))
                        }
                        .padding(20)
                        .background(AppTheme.purpleGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                    }

                    // MARK: - Recent Workouts
                    if !viewModel.workoutHistory.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text(L10n.recentWorkouts)
                                .font(.headline)
                                .foregroundStyle(AppTheme.textPrimary)

                            ForEach(viewModel.workoutHistory.prefix(5)) { record in
                                HStack(spacing: 12) {
                                    // Phase icon
                                    Image(systemName: phaseIcon(for: record.phase))
                                        .font(.title3)
                                        .foregroundStyle(AppTheme.primaryAccent)
                                        .frame(width: 40, height: 40)
                                        .background(AppTheme.primaryAccent.opacity(0.15))
                                        .clipShape(Circle())

                                    // Info
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(record.phase.displayName)
                                            .font(.subheadline.weight(.medium))
                                            .foregroundStyle(AppTheme.textPrimary)

                                        Text(record.date, style: .relative)
                                            .font(.caption)
                                            .foregroundStyle(AppTheme.textSecondary)
                                    }

                                    Spacer()

                                    // Duration
                                    Text(record.formattedDuration)
                                        .font(.subheadline.monospacedDigit().bold())
                                        .foregroundStyle(AppTheme.secondaryAccent)
                                }
                                .padding(12)
                                .cardStyle()
                            }
                        }
                    }

                    // Empty state when no history
                    if viewModel.workoutHistory.isEmpty {
                        VStack(spacing: 12) {
                            Image(systemName: "figure.cooldown")
                                .font(.system(size: 40))
                                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))

                            Text(L10n.noWorkoutsYet)
                                .font(.headline)
                                .foregroundStyle(AppTheme.textSecondary)

                            Text(L10n.tapStartWorkout)
                                .font(.subheadline)
                                .foregroundStyle(AppTheme.textSecondary.opacity(0.7))
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 40)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 100) // Space for tab bar
            }
        }
    }

    // Weekly progress as a fraction (0.0 to 1.0)
    private var progressFraction: CGFloat {
        guard viewModel.userStats.weeklyGoal > 0 else { return 0 }
        return min(CGFloat(viewModel.userStats.workoutsThisWeek) / CGFloat(viewModel.userStats.weeklyGoal), 1.0)
    }

    private func phaseIcon(for phase: WorkoutPhase) -> String {
        switch phase {
        case .warmup: return "flame.fill"
        case .intense: return "bolt.fill"
        case .cooldown: return "wind"
        }
    }
}
