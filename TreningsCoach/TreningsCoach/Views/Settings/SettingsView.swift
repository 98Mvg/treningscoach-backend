//
//  SettingsView.swift
//  TreningsCoach
//
//  Settings / About screen
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @AppStorage("app_dark_mode_enabled") private var darkModeEnabled: Bool = true
    @ObservedObject private var syncManager = AudioPackSyncManager.shared

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
                    darkModeRow

                    // Voice Pack
                    voicePackSection
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle(L10n.settings)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func settingsRow(icon: String, title: String, subtitle: String, trailingIcon: String? = nil) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.body).foregroundColor(CoachiTheme.primary)
                .frame(width: 36, height: 36).background(CoachiTheme.primary.opacity(0.15)).clipShape(RoundedRectangle(cornerRadius: 8))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 15, weight: .medium)).foregroundColor(CoachiTheme.textPrimary)
                Text(subtitle).font(.system(size: 12)).foregroundColor(CoachiTheme.textSecondary).lineLimit(1)
            }
            Spacer()
            if let trailingIcon {
                Image(systemName: trailingIcon)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .padding(12).cardStyle()
    }

    private var darkModeRow: some View {
        HStack(spacing: 12) {
            Image(systemName: darkModeEnabled ? "moon.fill" : "sun.max.fill")
                .font(.body)
                .foregroundColor(CoachiTheme.primary)
                .frame(width: 36, height: 36)
                .background(CoachiTheme.primary.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 2) {
                Text(L10n.darkMode)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(CoachiTheme.textPrimary)
                Text(L10n.darkModeSubtitle)
                    .font(.system(size: 12))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .lineLimit(2)
            }

            Spacer()

            Toggle("", isOn: $darkModeEnabled)
                .labelsHidden()
                .tint(CoachiTheme.primary)
        }
        .padding(12)
        .cardStyle()
    }

    // MARK: - Voice Pack Section

    private var voicePackSection: some View {
        VStack(spacing: 8) {
            // Status row
            HStack(spacing: 12) {
                Image(systemName: "speaker.wave.3.fill")
                    .font(.body)
                    .foregroundColor(CoachiTheme.primary)
                    .frame(width: 36, height: 36)
                    .background(CoachiTheme.primary.opacity(0.15))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                VStack(alignment: .leading, spacing: 2) {
                    Text(L10n.voicePackTitle)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(CoachiTheme.textPrimary)
                    Text(voicePackSubtitle)
                        .font(.system(size: 12))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .lineLimit(2)
                }
                Spacer()
                if syncManager.syncState == .downloading || syncManager.syncState == .checking {
                    ProgressView()
                        .scaleEffect(0.7)
                }
            }
            .padding(12)
            .cardStyle()

            // Reset Voice Pack
            Button {
                Task { await syncManager.resetAndResync() }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text(L10n.resetVoicePack)
                }
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.red)
                .frame(maxWidth: .infinity)
                .padding(10)
            }
            .cardStyle()
            .disabled(syncManager.syncState == .downloading)

            // Purge Stale Files
            Button {
                syncManager.purgeStaleFiles()
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "trash")
                    Text(L10n.purgeStaleFiles)
                }
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .frame(maxWidth: .infinity)
                .padding(10)
            }
            .cardStyle()
        }
    }

    private var voicePackSubtitle: String {
        let version = syncManager.currentPackVersion ?? "none"

        switch syncManager.syncState {
        case .idle:
            return packInfoLine(version: version)
        case .checking:
            return L10n.current == .no ? "Sjekker oppdateringer..." : "Checking for updates..."
        case .downloading:
            let (done, total) = syncManager.downloadProgress
            return L10n.current == .no ? "Laster ned \(done)/\(total)..." : "Downloading \(done)/\(total)..."
        case .cleaning:
            return L10n.current == .no ? "Rydder opp..." : "Cleaning up..."
        case .complete:
            return packInfoLine(version: version)
        case .failed:
            return syncManager.lastError ?? "Sync failed"
        }
    }

    private func packInfoLine(version: String) -> String {
        let files = syncManager.localFileCount()
        let sizeMB = String(format: "%.1f", Double(syncManager.localPackSizeBytes()) / 1_048_576.0)
        var line = "\(version) | \(files) files | \(sizeMB) MB"
        if let lastSync = syncManager.lastSyncAt {
            let formatter = RelativeDateTimeFormatter()
            formatter.unitsStyle = .short
            let ago = formatter.localizedString(for: lastSync, relativeTo: Date())
            line += " | \(ago)"
        }
        return line
    }
}
