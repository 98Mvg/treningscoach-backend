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
    @ObservedObject private var watchManager = PhoneWCManager.shared

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
                    darkModeRow

                    // Apple Watch
                    watchSection

                    // Voice Pack
                    voicePackSection
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle(L10n.advancedSettings)
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

    // MARK: - Apple Watch Section

    private var watchStatusSubtitle: String {
        switch watchManager.watchCapabilityState {
        case .watchReady:
            return L10n.current == .no ? "Tilkoblet" : "Connected"
        case .watchInstalledNotReachable:
            return L10n.current == .no ? "Ikke tilgjengelig" : "Not reachable"
        case .watchNotInstalled:
            return L10n.current == .no ? "Klokkappen ikke installert" : "Watch app not installed"
        case .noWatchSupport:
            return L10n.current == .no ? "Ingen klokke paret" : "No watch paired"
        }
    }

    private var watchStatusColor: Color {
        switch watchManager.watchCapabilityState {
        case .watchReady: return CoachiTheme.success
        case .watchInstalledNotReachable: return Color.yellow
        default: return CoachiTheme.textSecondary.opacity(0.4)
        }
    }

    @State private var showWatchConnect = false

    private var watchSection: some View {
        NavigationLink(destination: WatchSettingsDestination(watchManager: watchManager)) {
            HStack(spacing: 12) {
                Image(systemName: "applewatch")
                    .font(.body)
                    .foregroundColor(CoachiTheme.primary)
                    .frame(width: 36, height: 36)
                    .background(CoachiTheme.primary.opacity(0.15))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Apple Watch")
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(CoachiTheme.textPrimary)
                    HStack(spacing: 5) {
                        Circle()
                            .fill(watchStatusColor)
                            .frame(width: 6, height: 6)
                        Text(watchStatusSubtitle)
                            .font(.system(size: 12))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .lineLimit(1)
                    }
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
            .padding(12)
            .cardStyle()
        }
        .buttonStyle(.plain)
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
                    Text(L10n.current == .no ? "Oppdater lydinnhold" : "Refresh audio content")
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
                    Text(L10n.current == .no ? "Rydd lokale lydfiler" : "Clean local audio files")
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

// MARK: - Watch Settings Destination

/// Wraps the onboarding SensorConnectOnboardingView for use inside Settings navigation.
private struct WatchSettingsDestination: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var watchManager: PhoneWCManager

    var body: some View {
        SensorConnectOnboardingView(
            watchManager: watchManager,
            onBack: { dismiss() },
            onContinue: { _ in dismiss() }
        )
        .navigationBarBackButtonHidden(true)
    }
}
