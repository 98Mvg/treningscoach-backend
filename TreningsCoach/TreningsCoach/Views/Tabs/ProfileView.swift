//
//  ProfileView.swift
//  TreningsCoach
//
//  Coachi profile screen with stats, settings, sign-out
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = ProfileViewModel()
    @AppStorage("app_language") private var appLanguageCode: String = "en"

    var body: some View {
        NavigationStack {
            ZStack {
                CoachiTheme.backgroundGradient.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 24) {
                        // Profile Header
                        VStack(spacing: 12) {
                            Image(systemName: "person.circle.fill")
                                .font(.system(size: 72))
                                .foregroundColor(CoachiTheme.primary)

                            Text(appViewModel.userProfile.name)
                                .font(.system(size: 24, weight: .bold)).foregroundColor(CoachiTheme.textPrimary)

                            Text(appViewModel.trainingLevelRaw.capitalized)
                                .font(.system(size: 13, weight: .bold)).foregroundColor(CoachiTheme.primary)
                                .padding(.horizontal, 14).padding(.vertical, 6)
                                .background(Capsule().fill(CoachiTheme.primary.opacity(0.15)))
                        }
                        .padding(.top, 20)

                        // Stats Grid
                        HStack(spacing: 12) {
                            StatCardView(icon: "flame.fill", value: "\(viewModel.stats.totalWorkouts)", label: L10n.workouts)
                            StatCardView(icon: "clock.fill", value: "\(viewModel.stats.totalMinutes)", label: L10n.minutes, color: CoachiTheme.secondary)
                            StatCardView(icon: "bolt.fill", value: "\(viewModel.stats.currentStreak)", label: L10n.streak, color: CoachiTheme.accent)
                        }
                        .padding(.horizontal, 20)

                        // Settings
                        VStack(alignment: .leading, spacing: 12) {
                            Text(L10n.settings).font(.system(size: 18, weight: .bold)).foregroundColor(CoachiTheme.textPrimary)

                            NavigationLink {
                                LanguageSettingsView().environmentObject(authManager)
                            } label: {
                                settingsRow(icon: "globe", title: L10n.language, subtitle: (AppLanguage(rawValue: appLanguageCode) ?? .en).displayName, color: CoachiTheme.primary)
                            }
                            .buttonStyle(.plain)

                            settingsRow(icon: "chart.bar.fill", title: L10n.experienceLevel, subtitle: appViewModel.trainingLevelRaw.capitalized, color: CoachiTheme.primary)
                            settingsRow(icon: "speaker.wave.3.fill", title: L10n.coachVoice, subtitle: "ElevenLabs", color: CoachiTheme.success)

                            NavigationLink {
                                SettingsView()
                            } label: {
                                settingsRow(icon: "gearshape.fill", title: L10n.current == .no ? "Om" : "About", subtitle: "v\(AppConfig.version)", color: CoachiTheme.textSecondary)
                            }
                            .buttonStyle(.plain)
                        }
                        .padding(.horizontal, 20)

                        // Sign Out
                        Button {
                            authManager.signOut()
                        } label: {
                            HStack {
                                Image(systemName: "rectangle.portrait.and.arrow.right")
                                Text(L10n.signOut)
                            }
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(CoachiTheme.danger)
                            .padding(.vertical, 12)
                            .frame(maxWidth: .infinity)
                            .background(CoachiTheme.danger.opacity(0.12))
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        .padding(.horizontal, 20)

                        // Version
                        VStack(spacing: 4) {
                            Text(AppConfig.appName).font(.system(size: 12, weight: .medium)).foregroundColor(CoachiTheme.textTertiary)
                            Text("v\(AppConfig.version)").font(.system(size: 11)).foregroundColor(CoachiTheme.textTertiary.opacity(0.5))
                        }
                        .padding(.top, 20)
                    }
                    .padding(.bottom, 100)
                }
            }
        }
        .task { await viewModel.loadStats() }
    }

    private func settingsRow(icon: String, title: String, subtitle: String, color: Color) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.body).foregroundColor(color)
                .frame(width: 36, height: 36).background(color.opacity(0.15)).clipShape(RoundedRectangle(cornerRadius: 8))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 15, weight: .medium)).foregroundColor(CoachiTheme.textPrimary)
                Text(subtitle).font(.system(size: 12)).foregroundColor(CoachiTheme.textSecondary).lineLimit(1)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.caption).foregroundColor(CoachiTheme.textTertiary)
        }
        .padding(12).cardStyle()
    }
}
