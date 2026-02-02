//
//  ProfileView.swift
//  TreningsCoach
//
//  Profile and stats screen
//  Shows workout statistics, settings, and sign-out
//

import SwiftUI

struct ProfileView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @EnvironmentObject var authManager: AuthManager

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

                        Text(authManager.currentUser?.displayName ?? L10n.athlete)
                            .font(.title.bold())
                            .foregroundStyle(AppTheme.textPrimary)

                        Text(authManager.currentUser?.trainingLevel.displayName ?? L10n.athlete)
                            .font(.subheadline)
                            .foregroundStyle(AppTheme.textSecondary)
                    }
                    .padding(.top, 20)

                    // MARK: - Stats Grid
                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.myStatistics)
                            .font(.headline)
                            .foregroundStyle(AppTheme.textPrimary)

                        HStack(spacing: 12) {
                            StatCardView(
                                title: L10n.workouts,
                                value: "\(viewModel.userStats.totalWorkouts)",
                                icon: "figure.run",
                                color: AppTheme.primaryAccent
                            )

                            StatCardView(
                                title: L10n.minutes,
                                value: "\(viewModel.userStats.totalMinutes)",
                                icon: "clock.fill",
                                color: AppTheme.secondaryAccent
                            )

                            StatCardView(
                                title: L10n.streak,
                                value: "\(viewModel.userStats.currentStreak)",
                                icon: "flame.fill",
                                color: AppTheme.warning
                            )
                        }
                    }
                    .padding(.horizontal, 20)

                    // MARK: - Settings Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.settings)
                            .font(.headline)
                            .foregroundStyle(AppTheme.textPrimary)

                        // Language
                        settingsRow(
                            icon: "globe",
                            title: L10n.language,
                            subtitle: L10n.current.displayName,
                            color: AppTheme.primaryAccent
                        )

                        // Experience level
                        settingsRow(
                            icon: "chart.bar.fill",
                            title: L10n.experienceLevel,
                            subtitle: authManager.currentUser?.trainingLevel.displayName ?? "Intermediate",
                            color: AppTheme.primaryAccent
                        )

                        // Coach voice
                        settingsRow(
                            icon: "speaker.wave.3.fill",
                            title: L10n.coachVoice,
                            subtitle: "ElevenLabs",
                            color: AppTheme.success
                        )

                        // Backend connection status
                        settingsRow(
                            icon: "server.rack",
                            title: "Backend",
                            subtitle: AppConfig.backendURL,
                            color: AppTheme.secondaryAccent
                        )
                    }
                    .padding(.horizontal, 20)

                    // MARK: - Sign Out Button
                    Button {
                        authManager.signOut()
                    } label: {
                        HStack {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                            Text(L10n.signOut)
                        }
                        .font(.body.weight(.medium))
                        .foregroundStyle(AppTheme.danger)
                        .padding(.vertical, 12)
                        .frame(maxWidth: .infinity)
                        .background(AppTheme.danger.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
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
