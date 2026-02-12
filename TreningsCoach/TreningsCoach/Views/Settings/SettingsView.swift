//
//  SettingsView.swift
//  TreningsCoach
//
//  Settings / About screen
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var appViewModel: AppViewModel

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 16) {
                    // About
                    VStack(spacing: 12) {
                        CoachiLogoView(size: 80)
                        Text(AppConfig.appName).font(.system(size: 24, weight: .bold)).foregroundColor(CoachiTheme.textPrimary)
                        Text(AppConfig.appTagline).font(.system(size: 14)).foregroundColor(CoachiTheme.textSecondary)
                        Text("v\(AppConfig.version)").font(.system(size: 12)).foregroundColor(CoachiTheme.textTertiary)
                    }
                    .padding(.top, 32).padding(.bottom, 24)

                    settingsRow(icon: "globe", title: L10n.language, subtitle: (AppLanguage(rawValue: appViewModel.languageCode) ?? .en).displayName)
                    settingsRow(icon: "chart.bar.fill", title: L10n.experienceLevel, subtitle: appViewModel.trainingLevelRaw.capitalized)
                    settingsRow(icon: "speaker.wave.3.fill", title: L10n.coachVoice, subtitle: "ElevenLabs")
                    settingsRow(icon: "server.rack", title: "Backend", subtitle: AppConfig.backendURL)
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle(L10n.settings)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func settingsRow(icon: String, title: String, subtitle: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.body).foregroundColor(CoachiTheme.primary)
                .frame(width: 36, height: 36).background(CoachiTheme.primary.opacity(0.15)).clipShape(RoundedRectangle(cornerRadius: 8))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 15, weight: .medium)).foregroundColor(CoachiTheme.textPrimary)
                Text(subtitle).font(.system(size: 12)).foregroundColor(CoachiTheme.textSecondary).lineLimit(1)
            }
            Spacer()
        }
        .padding(12).cardStyle()
    }
}
