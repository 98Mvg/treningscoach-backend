//
//  ProfileView.swift
//  TreningsCoach
//
//  Profile and stats screen
//  Shows workout statistics and settings
//

import SwiftUI

struct ProfileView: View {
    @ObservedObject var viewModel: WorkoutViewModel

    var body: some View {
        ZStack {
            // Dark background
            AppTheme.backgroundGradient.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 24) {

                    // MARK: - Profile Header
                    VStack(spacing: 12) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 72))
                            .foregroundStyle(AppTheme.primaryAccent)

                        Text("Marius")
                            .font(.title.bold())
                            .foregroundStyle(AppTheme.textPrimary)

                        Text("Athlete")
                            .font(.subheadline)
                            .foregroundStyle(AppTheme.textSecondary)
                    }
                    .padding(.top, 20)

                    // MARK: - Stats Grid
                    VStack(alignment: .leading, spacing: 12) {
                        Text("My Statistics")
                            .font(.headline)
                            .foregroundStyle(AppTheme.textPrimary)

                        HStack(spacing: 12) {
                            StatCardView(
                                title: "Workouts",
                                value: "\(viewModel.userStats.totalWorkouts)",
                                icon: "figure.run",
                                color: AppTheme.primaryAccent
                            )

                            StatCardView(
                                title: "Minutes",
                                value: "\(viewModel.userStats.totalMinutes)",
                                icon: "clock.fill",
                                color: AppTheme.secondaryAccent
                            )

                            StatCardView(
                                title: "Streak",
                                value: "\(viewModel.userStats.currentStreak)",
                                icon: "flame.fill",
                                color: AppTheme.warning
                            )
                        }
                    }
                    .padding(.horizontal, 20)

                    // MARK: - Settings Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Settings")
                            .font(.headline)
                            .foregroundStyle(AppTheme.textPrimary)

                        // Backend connection status
                        settingsRow(
                            icon: "server.rack",
                            title: "Backend",
                            subtitle: AppConfig.backendURL,
                            color: AppTheme.secondaryAccent
                        )

                        // Experience level
                        settingsRow(
                            icon: "chart.bar.fill",
                            title: "Experience Level",
                            subtitle: "Advanced",
                            color: AppTheme.primaryAccent
                        )

                        // Audio settings
                        settingsRow(
                            icon: "speaker.wave.3.fill",
                            title: "Coach Voice",
                            subtitle: "ElevenLabs",
                            color: AppTheme.success
                        )
                    }
                    .padding(.horizontal, 20)

                    // MARK: - App Info
                    VStack(spacing: 4) {
                        Text(AppConfig.appName)
                            .font(.caption.weight(.medium))
                            .foregroundStyle(AppTheme.textSecondary)

                        Text("v\(AppConfig.version)")
                            .font(.caption)
                            .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
                    }
                    .padding(.top, 20)
                }
                .padding(.bottom, 100) // Space for tab bar
            }
        }
    }

    // MARK: - Settings Row

    private func settingsRow(icon: String, title: String, subtitle: String, color: Color) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.body)
                .foregroundStyle(color)
                .frame(width: 36, height: 36)
                .background(color.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(AppTheme.textPrimary)

                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(AppTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
        }
        .padding(12)
        .cardStyle()
    }
}
