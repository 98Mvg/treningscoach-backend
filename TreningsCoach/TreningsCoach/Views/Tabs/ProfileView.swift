//
//  ProfileView.swift
//  TreningsCoach
//
//  Settings-first profile tab styled after the native list layout
//

import SwiftUI

private let coachiSupportEmail = "AI.Coachi@hotmail.com"
private let coachiWebsiteURL = "https://coachi.no"
private let coachiPrivacyUpdatedNo = "10. mars 2026"
private let coachiPrivacyUpdatedEn = "March 10, 2026"

private let coachiPrivacyURL = "https://coachi.no/privacy"
private let coachiTermsURL = "https://coachi.no/terms"
private let coachiSupportURL = "https://coachi.no/support"
private let coachiDownloadURL = "https://coachi.no/download"

struct ProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var subscriptionManager: SubscriptionManager
    @Environment(\.openURL) private var openURL
    @Binding var selectedTab: TabItem
    @State private var showingSignOutConfirmation = false
    @State private var showManageSubscription = false
    @State private var showAppUpdatePrompt = false
    @State private var availableAppVersion: String?
    @State private var hasCheckedForAppUpdate = false
    @AppStorage("dismissed_app_update_version") private var dismissedAppUpdateVersion = ""

    private var isGuestMode: Bool {
        appViewModel.hasCompletedOnboarding && !authManager.isAuthenticated
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    profileSection
                    signOutSection
                }
                .padding(.top, 12)
                .padding(.bottom, 120)
            }
            .background(CoachiTheme.bg.ignoresSafeArea())
            .safeAreaInset(edge: .top) {
                topBar
                    .background(CoachiTheme.bg)
            }
            .navigationBarHidden(true)
            .navigationDestination(isPresented: $showManageSubscription) {
                ManageSubscriptionView()
                    .environmentObject(subscriptionManager)
            }
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .task {
            guard !hasCheckedForAppUpdate else { return }
            hasCheckedForAppUpdate = true
            await checkForAppUpdateIfNeeded()
        }
        .confirmationDialog(
            L10n.signOut,
            isPresented: $showingSignOutConfirmation,
            titleVisibility: .visible
        ) {
            Button(L10n.signOut, role: .destructive) {
                exitCurrentMode()
            }
            Button(L10n.current == .no ? "Avbryt" : "Cancel", role: .cancel) {}
        } message: {
            Text(
                isGuestMode
                    ? (L10n.current == .no
                        ? "Du går tilbake til registrering eller innlogging."
                        : "You will return to registration or sign-in.")
                    : (L10n.current == .no
                        ? "Du kan logge inn igjen senere."
                        : "You can sign in again later.")
            )
        }
        .overlay {
            if showAppUpdatePrompt, let availableAppVersion {
                ZStack {
                    Color.black.opacity(0.42)
                        .ignoresSafeArea()

                    AppUpdatePromptView(
                        latestVersion: availableAppVersion,
                        onUpdate: {
                            if let url = URL(string: coachiDownloadURL) {
                                openURL(url)
                            }
                        },
                        onSkip: {
                            dismissedAppUpdateVersion = availableAppVersion
                            showAppUpdatePrompt = false
                        }
                    )
                    .padding(.horizontal, 24)
                }
            }
        }
    }

    private var topBar: some View {
        HStack(spacing: 10) {
            Button {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                    selectedTab = .home
                }
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .frame(width: 32, height: 32)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            Text(L10n.settings)
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.75)

            Spacer(minLength: 0)
        }
        .padding(.horizontal, 20)
        .padding(.top, 6)
        .padding(.bottom, 8)
    }

    private var profileSection: some View {
        VStack(spacing: 0) {
            sectionHeader(L10n.account)

            NavigationLink {
                PersonalProfileSettingsView()
                    .environmentObject(appViewModel)
                    .environmentObject(authManager)
            } label: {
                HStack(spacing: 16) {
                    Image(systemName: "face.smiling")
                        .font(.system(size: 28))
                        .foregroundColor(CoachiTheme.textTertiary)
                        .frame(width: 76, height: 76)
                        .background(CoachiTheme.surfaceElevated)
                        .clipShape(Circle())

                    VStack(alignment: .leading, spacing: 4) {
                        Text(appViewModel.userProfile.name)
                            .font(.system(size: 19, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)

                        Text(L10n.personalProfile)
                            .font(.system(size: 14, weight: .regular))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .lineLimit(2)
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(CoachiTheme.textTertiary)
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                HealthProfileView()
                    .environmentObject(appViewModel)
            } label: {
                SettingsListRow(
                    icon: "heart",
                    title: L10n.healthProfile
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                HeartRateMonitorsView()
            } label: {
                SettingsListRow(
                    icon: "applewatch",
                    title: L10n.manageHeartRateMonitors
                )
            }
            .buttonStyle(.plain)

            sectionHeader(L10n.coaching)

            settingsDivider

            NavigationLink {
                CoachingSettingsView()
            } label: {
                SettingsListRow(
                    icon: "figure.run",
                    title: L10n.howCoachiWorks
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                HistoryAndDataView()
            } label: {
                SettingsListRow(
                    icon: "clock.arrow.circlepath",
                    title: L10n.historyAndData
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            Button {
                showManageSubscription = true
            } label: {
                SettingsListRow(
                    icon: "bookmark",
                    title: L10n.manageSubscription
                )
            }
            .buttonStyle(.plain)

            sectionHeader(L10n.helpAndSupport)

            settingsDivider

            NavigationLink {
                FAQGuideView()
            } label: {
                SettingsListRow(
                    icon: "questionmark.circle",
                    title: L10n.faqTitle
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                ContactSupportView()
            } label: {
                SettingsListRow(
                    icon: "headphones",
                    title: L10n.contactSupport
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            // Privacy Policy — opens website
            Button {
                if let url = URL(string: coachiPrivacyURL) { openURL(url) }
            } label: {
                SettingsListRow(
                    icon: "hand.raised",
                    title: L10n.privacyPolicy,
                    trailingIcon: "arrow.up.right.square"
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            // Terms of Use — opens website
            Button {
                if let url = URL(string: coachiTermsURL) { openURL(url) }
            } label: {
                SettingsListRow(
                    icon: "doc.text",
                    title: L10n.termsOfUse,
                    trailingIcon: "arrow.up.right.square"
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            Button {
                Task {
                    await checkForAppUpdateIfNeeded(forcePromptWhenAvailable: true)
                }
            } label: {
                SettingsListRow(
                    icon: "arrow.down.circle",
                    title: L10n.current == .no ? "Appoppdateringer" : "App updates",
                    subtitle: appUpdateStatusText,
                    trailingIcon: availableAppVersion == nil ? "arrow.clockwise" : "chevron.right"
                )
            }
            .buttonStyle(.plain)

        }
    }

    private var signOutSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            if authManager.isAuthenticated || isGuestMode {
                Button {
                    showingSignOutConfirmation = true
                } label: {
                    HStack(spacing: 14) {
                        Image(systemName: "arrow.right.circle")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(Color(hex: "5B4FD1"))
                            .frame(width: 30)

                        Text(L10n.signOut)
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(Color(hex: "5B4FD1"))

                        Spacer()
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 18)
                    .padding(.bottom, 8)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }

            Text("\(L10n.appVersionLabel) \(AppConfig.version)")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.horizontal, 24)
        }
        .padding(.top, 28)
    }

    private func exitCurrentMode() {
        let shouldResetOnboarding = isGuestMode
        authManager.signOut()
        if shouldResetOnboarding {
            appViewModel.resetOnboarding()
        }
    }

    private var appUpdateStatusText: String {
        if let availableAppVersion {
            return L10n.current == .no
                ? "Ny versjon \(availableAppVersion) er tilgjengelig"
                : "Version \(availableAppVersion) is available"
        }
        return L10n.current == .no
            ? "Installert versjon: \(AppConfig.version)"
            : "Installed version: \(AppConfig.version)"
    }

    private func checkForAppUpdateIfNeeded(forcePromptWhenAvailable: Bool = false) async {
        do {
            let runtime = try await BackendAPIService.shared.fetchAppRuntime()
            guard let latestVersion = normalizedVersion(runtime.version),
                  isVersion(latestVersion, newerThan: AppConfig.version) else {
                return
            }

            await MainActor.run {
                availableAppVersion = latestVersion
                if forcePromptWhenAvailable || dismissedAppUpdateVersion != latestVersion {
                    showAppUpdatePrompt = true
                }
            }
        } catch {
            // Quiet failure — this is a convenience check, not a critical path.
        }
    }

    private func normalizedVersion(_ rawValue: String?) -> String? {
        guard let rawValue else { return nil }
        let trimmed = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }

    private func isVersion(_ candidate: String, newerThan current: String) -> Bool {
        let candidateParts = candidate.split(separator: ".").compactMap { Int($0) }
        let currentParts = current.split(separator: ".").compactMap { Int($0) }
        let maxCount = max(candidateParts.count, currentParts.count)

        for index in 0..<maxCount {
            let candidateValue = index < candidateParts.count ? candidateParts[index] : 0
            let currentValue = index < currentParts.count ? currentParts[index] : 0
            if candidateValue != currentValue {
                return candidateValue > currentValue
            }
        }
        return false
    }

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 17, weight: .bold))
            .foregroundColor(CoachiTheme.textPrimary)
            .lineLimit(2)
            .minimumScaleFactor(0.75)
            .padding(.horizontal, 24)
            .padding(.top, 32)
            .padding(.bottom, 8)
    }

    private var settingsDivider: some View {
        Rectangle()
            .fill(CoachiTheme.borderSubtle.opacity(0.8))
            .frame(height: 1)
    }
}

private struct SettingsListRow: View {
    let icon: String
    let title: String
    var subtitle: String? = nil
    var trailingIcon: String? = "chevron.right"

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(CoachiTheme.textTertiary)
                .frame(width: 30)

            VStack(alignment: .leading, spacing: subtitle == nil ? 0 : 3) {
                Text(title)
                    .font(.system(size: 17, weight: .regular))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .lineLimit(2)

                if let subtitle {
                    Text(subtitle)
                        .font(.system(size: 13, weight: .regular))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .lineLimit(2)
                }
            }

            Spacer(minLength: 8)

            if let trailingIcon {
                Image(systemName: trailingIcon)
                    .font(
                        trailingIcon == "arrow.up.right.square"
                            ? .system(size: 18, weight: .regular)
                            : .system(size: 14, weight: .semibold)
                    )
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 15)
        .contentShape(Rectangle())
    }
}

private struct AppUpdatePromptView: View {
    let latestVersion: String
    let onUpdate: () -> Void
    let onSkip: () -> Void

    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        VStack(spacing: 20) {
            Text(isNorwegian ? "Oppdater appen" : "Update the app")
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .multilineTextAlignment(.center)

            Text(
                isNorwegian
                    ? "En ny versjon (\(latestVersion)) er tilgjengelig. Oppdater for å få de nyeste forbedringene i Coachi."
                    : "A new version (\(latestVersion)) is available. Update to get the latest Coachi improvements."
            )
            .font(.system(size: 18, weight: .medium))
            .foregroundColor(CoachiTheme.textSecondary)
            .multilineTextAlignment(.center)
            .fixedSize(horizontal: false, vertical: true)

            Button(action: onUpdate) {
                Text(isNorwegian ? "Oppdater nå" : "Update now")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 17)
                    .background(
                        Capsule(style: .continuous)
                            .fill(
                                LinearGradient(
                                    colors: [Color(hex: "7C3AED"), Color(hex: "4F46E5")],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                    )
            }
            .buttonStyle(.plain)

            Button(action: onSkip) {
                Text(isNorwegian ? "Hopp over" : "Skip")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 28)
        .padding(.vertical, 30)
        .background(
            RoundedRectangle(cornerRadius: 30, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0.95),
                            Color(hex: "DDD6FE").opacity(0.96),
                            Color(hex: "A7F3D0").opacity(0.92),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 30, style: .continuous)
                .stroke(Color.white.opacity(0.55), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.18), radius: 28, x: 0, y: 18)
    }
}

private struct ProfileValueRow: View {
    let title: String
    let value: String
    var trailingIcon: String? = nil
    var valueColor: Color = CoachiTheme.textPrimary

    var body: some View {
        HStack(spacing: 14) {
            Text(title)
                .font(.system(size: 17, weight: .regular))
                .foregroundColor(CoachiTheme.textSecondary)

            Spacer(minLength: 12)

            Text(value)
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(valueColor)
                .multilineTextAlignment(.trailing)

            if let trailingIcon {
                Image(systemName: trailingIcon)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
        .contentShape(Rectangle())
    }
}

private struct ManageSubscriptionView: View {
    @EnvironmentObject private var subscriptionManager: SubscriptionManager
    @Environment(\.openURL) private var openURL
    @State private var showPaywall = false

    private var isNorwegian: Bool { L10n.current == .no }
    private var hasPremiumAccess: Bool { subscriptionManager.hasPremiumAccess }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 20) {
                subscriptionStatusCard
                includedItemsCard

                Button {
                    if hasPremiumAccess {
                        subscriptionManager.manageSubscription()
                    } else {
                        showPaywall = true
                    }
                } label: {
                    Text(hasPremiumAccess
                        ? (isNorwegian ? "Administrer i App Store" : "Manage in App Store")
                        : (isNorwegian ? "Se alle tilbudene" : "See all offers"))
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 17)
                        .background(
                            Capsule(style: .continuous)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "7C3AED"), Color(hex: "4F46E5")],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                        )
                }
                .buttonStyle(.plain)

                Button(isNorwegian ? "Gjenopprett kjøp" : "Restore purchases") {
                    Task { await subscriptionManager.restorePurchases() }
                }
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(Color(hex: "5B4FD1"))
                .frame(maxWidth: .infinity)

                HStack(spacing: 8) {
                    Button(isNorwegian ? "Brukervilkår" : "Terms") {
                        if let url = URL(string: coachiTermsURL) { openURL(url) }
                    }
                    .buttonStyle(.plain)

                    Text(isNorwegian ? "og" : "and")
                        .foregroundColor(CoachiTheme.textSecondary)

                    Button(isNorwegian ? "personvernerklæring" : "privacy policy") {
                        if let url = URL(string: coachiPrivacyURL) { openURL(url) }
                    }
                    .buttonStyle(.plain)
                }
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(maxWidth: .infinity)
            }
            .padding(.horizontal, 20)
            .padding(.top, 20)
            .padding(.bottom, 36)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(isNorwegian ? "Administrer abonnement" : "Manage subscription")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showPaywall) {
            PaywallView(context: .general)
        }
    }

    private var subscriptionStatusCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(isNorwegian ? "Dine inkluderte elementer" : "Your included items")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Text(
                hasPremiumAccess
                    ? (isNorwegian ? "Premium er aktivt. Du har tilgang til alle Coachi-funksjonene som er inkludert i planen din." : "Premium is active. You have access to the full Coachi set included in your plan.")
                    : (isNorwegian ? "Gratisversjonen er aktiv. Her ser du hva som er inkludert i Gratis og hva Premium legger til." : "Free is active. Here is what is included in Free and what Premium adds.")
            )
            .font(.system(size: 15, weight: .medium))
            .foregroundColor(CoachiTheme.textSecondary)

            HStack(spacing: 10) {
                planBadge(
                    title: isNorwegian ? "Gratis" : "Free",
                    isCurrent: !hasPremiumAccess,
                    tint: Color(hex: "64748B")
                )
                planBadge(
                    title: "Premium",
                    isCurrent: hasPremiumAccess,
                    tint: Color(hex: "5B4FD1")
                )
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 20)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(CoachiTheme.surface)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.28), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.05), radius: 18, x: 0, y: 10)
    }

    private var includedItemsCard: some View {
        VStack(spacing: 0) {
            HStack(spacing: 0) {
                Text(isNorwegian ? "Inkludert i abonnementet" : "Included in your plan")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Text(isNorwegian ? "Gratis" : "Free")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .frame(width: 82)

                Text("Premium")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(Color(hex: "5B4FD1"))
                    .frame(width: 98)
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .background(CoachiTheme.surfaceElevated)

            ForEach(featureRows) { row in
                ManageSubscriptionFeatureRow(row: row)
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(CoachiTheme.surface)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.28), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
    }

    private var featureRows: [ManageSubscriptionFeatureRowData] {
        [
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Guidede økter" : "Guided workouts",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Coachi Score" : "Coachi Score",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Pulssone-coaching" : "HR zone coaching",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Talk to Coach Live" : "Talk to Coach Live",
                freeValue: isNorwegian ? "3/dag" : "3/day",
                premiumValue: isNorwegian ? "Ubegrenset" : "Unlimited"
            ),
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Økthistorikk" : "Workout history",
                freeValue: isNorwegian ? "10 økter" : "10 workouts",
                premiumValue: isNorwegian ? "Alle" : "All"
            ),
            ManageSubscriptionFeatureRowData(
                title: isNorwegian ? "Dype øktoppsummeringer" : "Deep workout insights",
                freeValue: "—",
                premiumValue: "✓"
            ),
        ]
    }

    private func planBadge(title: String, isCurrent: Bool, tint: Color) -> some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isCurrent ? tint : tint.opacity(0.18))
                .frame(width: 8, height: 8)
            Text(isCurrent ? "\(title) · \(isNorwegian ? "Din plan" : "Current")" : title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(isCurrent ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            Capsule(style: .continuous)
                .fill(isCurrent ? tint.opacity(0.12) : CoachiTheme.surfaceElevated)
        )
    }

    private var localizedPlanStatus: String {
        switch subscriptionManager.resolvedPlanLabel {
        case "Checking":
            return isNorwegian ? "Sjekker status" : "Checking status"
        case "Free":
            return isNorwegian ? "Gratis" : "Free"
        case "Free Trial":
            return isNorwegian ? "Gratis prøveperiode" : "Free trial"
        case "Expired":
            return isNorwegian ? "Utløpt" : "Expired"
        default:
            return subscriptionManager.resolvedPlanLabel
        }
    }
}

private struct ManageSubscriptionFeatureRowData: Identifiable {
    let id = UUID()
    let title: String
    let freeValue: String
    let premiumValue: String
}

private struct ManageSubscriptionFeatureRow: View {
    let row: ManageSubscriptionFeatureRowData

    var body: some View {
        HStack(spacing: 0) {
            Text(row.title)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(maxWidth: .infinity, alignment: .leading)

            Text(row.freeValue)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(CoachiTheme.textSecondary)
                .frame(width: 82)

            Text(row.premiumValue)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(Color(hex: "5B4FD1"))
                .frame(width: 98)
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
        .background(Color.white.opacity(0.0001))
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(CoachiTheme.borderSubtle.opacity(0.55))
                .frame(height: 1)
                .padding(.horizontal, 18)
        }
    }
}

private struct HealthProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @AppStorage("user_birthdate_ts") private var birthdateTimestamp: Double = 0
    @AppStorage("user_gender") private var storedGender: String = ""
    @AppStorage("user_height_cm") private var storedHeightCm: Int = 0
    @AppStorage("user_weight_kg") private var storedWeightKg: Int = 0
    @AppStorage("hr_max") private var storedMaxHeartRate: Int = 0
    @AppStorage("resting_hr") private var storedRestingHeartRate: Int = 0
    @State private var showingBirthDateEditor = false
    @State private var draftBirthDate: Date = Calendar.current.date(byAdding: .year, value: -28, to: Date()) ?? Date()

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 12) {
                VStack(spacing: 0) {
                    Button {
                        draftBirthDate = storedBirthDate
                        showingBirthDateEditor = true
                    } label: {
                        ProfileValueRow(
                            title: L10n.dateOfBirth,
                            value: birthDateDisplayLine,
                            trailingIcon: "chevron.right"
                        )
                    }
                    .buttonStyle(.plain)

                    divider

                    ProfileValueRow(
                        title: L10n.current == .no ? "Kjønn" : "Gender",
                        value: genderDisplay,
                        trailingIcon: nil,
                        valueColor: metricValueColor(for: genderDisplay)
                    )

                    divider

                    ProfileValueRow(
                        title: L10n.current == .no ? "Høyde" : "Height",
                        value: heightDisplay,
                        trailingIcon: nil,
                        valueColor: metricValueColor(for: heightDisplay)
                    )

                    divider

                    ProfileValueRow(
                        title: L10n.current == .no ? "Vekt" : "Weight",
                        value: weightDisplay,
                        trailingIcon: nil,
                        valueColor: metricValueColor(for: weightDisplay)
                    )

                    divider

                    ProfileValueRow(
                        title: L10n.current == .no ? "Makspuls" : "Max heart rate",
                        value: maxHeartRateDisplay,
                        trailingIcon: nil,
                        valueColor: metricValueColor(for: maxHeartRateDisplay)
                    )

                    divider

                    ProfileValueRow(
                        title: L10n.current == .no ? "Hvilepuls" : "Resting heart rate",
                        value: restingHeartRateDisplay,
                        trailingIcon: nil,
                        valueColor: metricValueColor(for: restingHeartRateDisplay)
                    )

                    divider

                    ProfileValueRow(
                        title: L10n.experienceLevel,
                        value: appViewModel.trainingLevelDisplayName,
                        trailingIcon: nil
                    )
                }
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.4), lineWidth: 1)
                )
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.healthProfile)
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingBirthDateEditor) {
            BirthDateEditorSheet(
                selectedDate: draftBirthDate,
                minDate: minimumBirthDate,
                maxDate: Date(),
                onSave: persistBirthDate
            )
        }
    }

    private var divider: some View {
        Rectangle()
            .fill(CoachiTheme.borderSubtle.opacity(0.8))
            .frame(height: 1)
    }

    private var minimumBirthDate: Date {
        Calendar.current.date(byAdding: .year, value: -95, to: Date()) ?? Date()
    }

    private var fallbackBirthDate: Date {
        Calendar.current.date(byAdding: .year, value: -28, to: Date()) ?? Date()
    }

    private var storedBirthDate: Date {
        guard birthdateTimestamp > 0 else { return fallbackBirthDate }
        return Date(timeIntervalSince1970: birthdateTimestamp)
    }

    private var birthDateDisplayLine: String {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateStyle = .medium
        return formatter.string(from: storedBirthDate)
    }

    private var notSetText: String {
        L10n.current == .no ? "Ikke satt" : "Not set"
    }

    private var genderDisplay: String {
        switch storedGender.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
        case "male", "mann", "man":
            return L10n.current == .no ? "Mann" : "Male"
        case "female", "kvinne", "woman":
            return L10n.current == .no ? "Kvinne" : "Female"
        case "other", "annet", "nonbinary", "non-binary":
            return L10n.current == .no ? "Annet" : "Other"
        default:
            return notSetText
        }
    }

    private var heightDisplay: String {
        storedHeightCm > 0 ? "\(storedHeightCm) cm" : notSetText
    }

    private var weightDisplay: String {
        storedWeightKg > 0 ? "\(storedWeightKg) kg" : notSetText
    }

    private var maxHeartRateDisplay: String {
        storedMaxHeartRate > 0
            ? "\(storedMaxHeartRate) \(L10n.current == .no ? "slag/min" : "bpm")"
            : notSetText
    }

    private var restingHeartRateDisplay: String {
        storedRestingHeartRate > 0
            ? "\(storedRestingHeartRate) \(L10n.current == .no ? "slag/min" : "bpm")"
            : notSetText
    }

    private func metricValueColor(for value: String) -> Color {
        value == notSetText ? CoachiTheme.textSecondary : CoachiTheme.textPrimary
    }

    private func persistBirthDate(_ value: Date) {
        let bounded = min(max(value, minimumBirthDate), Date())
        birthdateTimestamp = bounded.timeIntervalSince1970
        let years = Calendar.current.dateComponents([.year], from: bounded, to: Date()).year ?? 0
        let age = max(14, min(95, years))
        UserDefaults.standard.set(age, forKey: "user_age")
    }
}

private struct PersonalProfileSettingsView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @AppStorage("app_language") private var appLanguageCode: String = "en"
    @AppStorage("app_dark_mode_enabled") private var darkModeEnabled: Bool = true

    private var isGuestMode: Bool {
        appViewModel.hasCompletedOnboarding && !authManager.isAuthenticated
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                sectionHeader(L10n.personalProfile)

                HStack(spacing: 16) {
                    Image(systemName: "face.smiling")
                        .font(.system(size: 28))
                        .foregroundColor(CoachiTheme.textTertiary)
                        .frame(width: 76, height: 76)
                        .background(CoachiTheme.surfaceElevated)
                        .clipShape(Circle())

                    Text(L10n.current == .no ? "Legg til profilbilde" : "Add profile photo")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color(hex: "8B5CF6"))

                    Spacer()
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 18)

                settingsDivider

                ProfileValueRow(
                    title: L10n.current == .no ? "Navn" : "Name",
                    value: appViewModel.userProfile.name,
                    trailingIcon: nil
                )

                settingsDivider

                ProfileValueRow(
                    title: L10n.current == .no ? "E-post" : "Email",
                    value: emailDisplayLine,
                    trailingIcon: nil,
                    valueColor: emailDisplayLine == unavailableEmailText ? CoachiTheme.textSecondary : CoachiTheme.textPrimary
                )

                sectionHeader(L10n.current == .no ? "App" : "App")

                settingsDivider

                NavigationLink {
                    LanguageSettingsView().environmentObject(authManager)
                } label: {
                    SettingsListRow(
                        icon: "globe",
                        title: "\(L10n.language): \((AppLanguage(rawValue: appLanguageCode) ?? .en).displayName)"
                    )
                }
                .buttonStyle(.plain)

                settingsDivider

                HStack(spacing: 14) {
                    Image(systemName: darkModeEnabled ? "moon.fill" : "sun.max.fill")
                        .font(.system(size: 16))
                        .foregroundColor(CoachiTheme.textTertiary)
                        .frame(width: 30)

                    Text(L10n.darkMode)
                        .font(.system(size: 17, weight: .medium))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Spacer()

                    Toggle("", isOn: $darkModeEnabled)
                        .labelsHidden()
                        .tint(CoachiTheme.primary)
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 15)

                settingsDivider

                NavigationLink {
                    AboutCoachiView()
                        .environmentObject(appViewModel)
                } label: {
                    SettingsListRow(
                        icon: "info.circle",
                        title: "\(L10n.about): v\(AppConfig.version)"
                    )
                }
                .buttonStyle(.plain)

                if authManager.isAuthenticated {
                    settingsDivider

                    NavigationLink {
                        DeleteAccountInfoView()
                    } label: {
                        HStack(spacing: 14) {
                            Image(systemName: "trash")
                                .font(.system(size: 16))
                                .foregroundColor(CoachiTheme.danger)
                                .frame(width: 30)

                            Text(L10n.current == .no ? "Slett konto" : "Delete account")
                                .font(.system(size: 17, weight: .semibold))
                                .foregroundColor(CoachiTheme.danger)

                            Spacer()

                            Image(systemName: "chevron.right")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(CoachiTheme.textTertiary)
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 16)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.top, 8)
            .padding(.bottom, 80)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.personalProfile)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var emailDisplayLine: String {
        if let email = authManager.currentUser?.email, !email.isEmpty {
            return email
        }
        return unavailableEmailText
    }

    private var unavailableEmailText: String {
        isGuestMode
            ? (L10n.current == .no ? "Ingen konto tilkoblet" : "No account connected")
            : (L10n.current == .no ? "Ikke tilgjengelig" : "Not available")
    }

    private var settingsDivider: some View {
        Rectangle()
            .fill(CoachiTheme.borderSubtle.opacity(0.8))
            .frame(height: 1)
    }

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 15, weight: .bold))
            .foregroundColor(CoachiTheme.textSecondary)
            .padding(.horizontal, 24)
            .padding(.top, 24)
            .padding(.bottom, 10)
    }
}

private struct AboutCoachiView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @Environment(\.openURL) private var openURL

    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Om Coachi" : "About Coachi",
                    copyText: isNorwegian
                        ? "Coachi er en løpecoach-app som guider deg gjennom økter med korte lydsignaler, tydelige overganger og en rolig coachingstil."
                        : "Coachi is a running coach app that guides you through workouts with short audio cues, clear transitions, and a calm coaching style."
                )

                SupportCard(
                    title: isNorwegian ? "Versjon" : "Version",
                    copyText: "Coachi v\(AppConfig.version)"
                )

                SupportCard(
                    title: isNorwegian ? "Kontakt" : "Contact",
                    copyText: coachiSupportEmail
                )

                Button {
                    openSupportEmail()
                } label: {
                    SettingsActionRow(
                        icon: "envelope",
                        title: isNorwegian ? "Kontakt support" : "Contact support",
                        tint: CoachiTheme.primary
                    )
                }
                .buttonStyle(.plain)

                NavigationLink {
                    SettingsView().environmentObject(appViewModel)
                } label: {
                    SettingsCardRow(
                        icon: "slider.horizontal.3",
                        title: L10n.advancedSettings,
                        subtitle: L10n.audioMaintenance
                    )
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.aboutCoachi)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func openSupportEmail() {
        guard let url = URL(string: "mailto:\(coachiSupportEmail)") else { return }
        openURL(url)
    }
}

private struct CoachingSettingsView: View {
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: L10n.howCoachiWorks,
                    copyText: isNorwegian
                        ? "Coachi guider deg gjennom økten med korte lydsignaler, tydelige overganger og rolige påminnelser når det trengs."
                        : "Coachi guides your workout with short audio cues, clear transitions, and calm reminders when they matter."
                )

                SupportCard(
                    title: isNorwegian ? "Når puls er tilgjengelig" : "When heart rate is available",
                    copyText: isNorwegian
                        ? "Når Coachi får live puls fra Apple Watch eller Bluetooth-sensor, kan coachingen bli mer presis og hjelpe deg å holde riktig intensitet."
                        : "When Coachi receives live heart rate from Apple Watch or a Bluetooth sensor, coaching becomes more precise and can help you stay in the right intensity."
                )

                SupportCard(
                    title: L10n.ifHeartRateMissing,
                    copyText: isNorwegian
                        ? "Hvis puls mangler, fortsetter Coachi med struktur og timing. Du får fortsatt tydelig veiledning gjennom økten."
                        : "If heart rate is missing, Coachi continues with structure and timing cues. You still get clear guidance through the workout."
                )

                SupportCard(
                    title: isNorwegian ? "Talk to Coach" : "Talk to Coach",
                    copyText: isNorwegian
                        ? "Du kan stille korte spørsmål under økten når funksjonen er tilgjengelig. Opplevelsen kan være begrenset av nettverk eller produktnivå."
                        : "You can ask short questions during a workout when the feature is available. The experience may be limited by network conditions or product tier."
                )
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.coaching)
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct AudioAndVoicesView: View {
    @EnvironmentObject var authManager: AuthManager
    @AppStorage("app_dark_mode_enabled") private var darkModeEnabled: Bool = true
    @ObservedObject private var syncManager = AudioPackSyncManager.shared

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                NavigationLink {
                    LanguageSettingsView().environmentObject(authManager)
                } label: {
                    SettingsCardRow(
                        icon: "globe",
                        title: L10n.language,
                        subtitle: (AppLanguage(rawValue: UserDefaults.standard.string(forKey: "app_language") ?? "en") ?? .en).displayName
                    )
                }
                .buttonStyle(.plain)

                SettingsCardRow(
                    icon: "person.wave.2",
                    title: L10n.activeVoice,
                    subtitle: L10n.current == .no ? "Standard coach-stemme" : "Standard coach voice",
                    showsChevron: false
                )

                VStack(alignment: .leading, spacing: 6) {
                    Text(L10n.advancedSettings)
                        .font(.system(size: 15, weight: .bold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Text(L10n.audioMaintenance)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 4)

                VStack(spacing: 8) {
                    SettingsCardRow(
                        icon: "speaker.wave.3.fill",
                        title: L10n.voicePackStatus,
                        subtitle: voicePackSubtitle,
                        showsChevron: false
                    )

                    Button {
                        Task { await syncManager.resetAndResync() }
                    } label: {
                        SettingsActionRow(
                            icon: "arrow.clockwise",
                            title: L10n.current == .no ? "Oppdater lydinnhold" : "Refresh audio content",
                            tint: .red
                        )
                    }
                    .buttonStyle(.plain)
                    .disabled(syncManager.syncState == .downloading)

                    Button {
                        syncManager.purgeStaleFiles()
                    } label: {
                        SettingsActionRow(
                            icon: "trash",
                            title: L10n.current == .no ? "Rydd lokale lydfiler" : "Clean local audio files",
                            tint: CoachiTheme.textSecondary
                        )
                    }
                    .buttonStyle(.plain)
                }

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
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.audioAndVoices)
        .navigationBarTitleDisplayMode(.inline)
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

private struct HistoryAndDataView: View {
    @EnvironmentObject var authManager: AuthManager
    private var isNorwegian: Bool { L10n.current == .no }
    @State private var workouts: [WorkoutRecord] = []
    @State private var isLoading = false

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                workoutHistorySection

                SupportCard(
                    title: L10n.dataAndPrivacy,
                    copyText: isNorwegian
                        ? "Coachi bruker data for å levere coaching, lagre økter, holde tjenesten stabil og gi deg innsikt i treningen. Selskapsdetaljer fylles inn senere."
                        : "Coachi uses data to deliver coaching, store workouts, keep the service stable, and give you insight into your training. Company details will be filled in later."
                )

                SupportCard(
                    title: isNorwegian ? "Juridisk og personvern" : "Legal and privacy",
                    copyText: isNorwegian
                        ? "Personvern og vilkår er tilgjengelig direkte fra hovedinnstillingene, slik at du slipper ekstra trykk her."
                        : "Privacy policy and terms are available directly from the main settings screen, so you do not need extra taps here."
                )
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.historyAndData)
        .navigationBarTitleDisplayMode(.inline)
        .task { await loadWorkouts() }
    }

    @ViewBuilder
    private var workoutHistorySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(L10n.trainingHistory)
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(CoachiTheme.textPrimary)

            if isLoading {
                HStack {
                    Spacer()
                    ProgressView()
                        .tint(CoachiTheme.textSecondary)
                    Spacer()
                }
                .padding(.vertical, 24)
            } else if workouts.isEmpty {
                Text(isNorwegian
                    ? "Ingen lagrede økter ennå. Fullfør en økt for å se den her."
                    : "No saved workouts yet. Complete a workout to see it here.")
                    .font(.system(size: 14))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .padding(.vertical, 12)
            } else {
                VStack(spacing: 0) {
                    ForEach(workouts) { record in
                        NavigationLink {
                            WorkoutSessionDetailView(record: record)
                        } label: {
                            WorkoutHistoryRow(record: record)
                        }
                        .buttonStyle(.plain)

                        if record.id != workouts.last?.id {
                            Divider()
                                .background(CoachiTheme.borderSubtle.opacity(0.4))
                                .padding(.horizontal, 16)
                        }
                    }
                }
                .background(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(CoachiTheme.surface)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.28), lineWidth: 1)
                )
            }
        }
    }

    private func loadWorkouts() async {
        guard authManager.hasUsableSession() else { return }
        isLoading = true
        defer { isLoading = false }
        workouts = (try? await BackendAPIService.shared.getWorkoutHistory(limit: 20)) ?? []
    }
}

private struct WorkoutHistoryRow: View {
    let record: WorkoutRecord
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(record.dateFormatted)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                Text(record.durationFormatted)
                    .font(.system(size: 13))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            Spacer()

            if let score = record.coachScore, score > 0 {
                VStack(spacing: 2) {
                    Text("\(score)")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                    Text("CS")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                }
            }

            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(CoachiTheme.textSecondary.opacity(0.5))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .contentShape(Rectangle())
    }
}

private struct WorkoutSessionDetailView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var subscriptionManager: SubscriptionManager
    @StateObject private var liveVoiceTracker = LiveVoiceSessionTracker.shared
    @State private var showLiveCoachVoice = false
    @State private var showLiveVoicePaywall = false
    let record: WorkoutRecord

    private var isNorwegian: Bool { L10n.current == .no }
    private var hasPremiumAccess: Bool { subscriptionManager.hasPremiumAccess }
    private var hasLiveVoiceAccountAccess: Bool { authManager.hasUsableSession() }
    private var liveVoiceIsAvailable: Bool {
        AppConfig.LiveVoice.isEnabled &&
        hasLiveVoiceAccountAccess &&
        (hasPremiumAccess || liveVoiceTracker.sessionsUsedToday < AppConfig.LiveVoice.freeSessionsPerDay)
    }
    private var remainingLiveSessions: Int? {
        guard hasLiveVoiceAccountAccess else { return nil }
        return liveVoiceTracker.remainingToday(isPremium: hasPremiumAccess)
    }
    private var liveVoiceStatusText: String {
        if liveVoiceIsAvailable {
            if let remaining = remainingLiveSessions {
                let unit = isNorwegian
                    ? (remaining == 1 ? "økt igjen i dag" : "økter igjen i dag")
                    : (remaining == 1 ? "session left today" : "sessions left today")
                return isNorwegian ? "Gratis: \(remaining) \(unit)" : "Free: \(remaining) \(unit)"
            }
            return "Premium"
        }
        if !hasLiveVoiceAccountAccess {
            return isNorwegian ? "Logg inn for å bruke live" : "Sign in to use live"
        }
        return isNorwegian ? "Ingen økter igjen i dag" : "No sessions left today"
    }
    private var languageCode: String {
        authManager.currentUser?.language.rawValue ?? L10n.current.rawValue
    }
    private var userName: String {
        authManager.currentUser?.displayName ?? ""
    }
    private var summaryContext: PostWorkoutSummaryContext {
        let label = isNorwegian ? "\(record.durationFormatted) økt" : "\(record.durationFormatted) workout"
        return PostWorkoutSummaryContext(
            workoutMode: record.finalPhase,
            workoutLabel: label,
            durationText: record.durationFormatted,
            finalHeartRateText: "—",
            coachScore: record.coachScore ?? 0,
            coachScoreSummaryLine: "",
            zoneTimeInTargetPct: nil,
            zoneOvershoots: 0,
            phase: record.finalPhase,
            elapsedS: record.durationSeconds,
            timeLeftS: nil,
            repIndex: nil,
            repsTotal: nil,
            repRemainingS: nil,
            repsRemainingIncludingCurrent: nil,
            elapsedSource: nil
        )
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 20) {
                // Stats grid
                statsGrid

                if AppConfig.LiveVoice.isEnabled {
                    Divider()
                        .background(CoachiTheme.borderSubtle.opacity(0.4))

                    liveCoachSection
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 16)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(record.dateFormatted)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { liveVoiceTracker.synchronize() }
        .sheet(isPresented: $showLiveCoachVoice) {
            LiveCoachConversationView(
                summaryContext: summaryContext,
                languageCode: languageCode,
                userName: userName,
                isPremium: hasPremiumAccess
            )
            .presentationDetents([.medium, .large])
            .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $showLiveVoicePaywall) {
            PaywallView(context: .liveVoice)
                .environmentObject(subscriptionManager)
        }
    }

    private var statsGrid: some View {
        VStack(spacing: 0) {
            HStack(spacing: 0) {
                statCell(
                    title: isNorwegian ? "Varighet" : "Duration",
                    value: record.durationFormatted
                )
                Divider().frame(width: 1)
                statCell(
                    title: isNorwegian ? "Coachi Score" : "Coachi Score",
                    value: record.coachScore.map { $0 > 0 ? "\($0)" : "—" } ?? "—"
                )
            }
            Divider()
            HStack(spacing: 0) {
                statCell(
                    title: isNorwegian ? "Intensitet" : "Intensity",
                    value: localizedIntensity(record.avgIntensity)
                )
                Divider().frame(width: 1)
                statCell(
                    title: isNorwegian ? "Fase" : "Phase",
                    value: localizedPhase(record.finalPhase)
                )
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(CoachiTheme.surface)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.28), lineWidth: 1)
        )
    }

    private func statCell(title: String, value: String) -> some View {
        VStack(spacing: 6) {
            Text(value)
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
    }

    private var liveCoachSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(isNorwegian ? "Snakk med Coach Live" : "Talk to Coach Live")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                Text(isNorwegian
                    ? "Få tilbakemelding på denne økten fra AI-coachen din."
                    : "Get feedback on this workout from your AI coach.")
                    .font(.system(size: 14))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            Button {
                if liveVoiceIsAvailable {
                    showLiveCoachVoice = true
                } else {
                    showLiveVoicePaywall = true
                }
            } label: {
                Text(isNorwegian ? "Start coaching" : "Start coaching")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(liveVoiceIsAvailable ? .white : CoachiTheme.textSecondary)
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .fill(liveVoiceIsAvailable
                                ? CoachiTheme.accent
                                : CoachiTheme.surfaceElevated)
                    )
            }
            .buttonStyle(.plain)

            HStack(spacing: 6) {
                Circle()
                    .fill(liveVoiceIsAvailable ? CoachiTheme.success : CoachiTheme.textSecondary.opacity(0.4))
                    .frame(width: 6, height: 6)
                Text(liveVoiceStatusText)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
            }
        }
    }

    private func localizedIntensity(_ intensity: String) -> String {
        switch intensity {
        case "calm":    return isNorwegian ? "Rolig" : "Calm"
        case "moderate": return isNorwegian ? "Moderat" : "Moderate"
        case "intense":  return isNorwegian ? "Intens" : "Intense"
        case "critical": return isNorwegian ? "Kritisk" : "Critical"
        default:         return intensity.capitalized
        }
    }

    private func localizedPhase(_ phase: String) -> String {
        switch phase {
        case "prep":     return isNorwegian ? "Forberedelse" : "Prep"
        case "warmup":   return isNorwegian ? "Oppvarming" : "Warm-up"
        case "intense":  return isNorwegian ? "Intensiv" : "Main set"
        case "recovery": return isNorwegian ? "Restitusjon" : "Recovery"
        case "cooldown": return isNorwegian ? "Nedtrapping" : "Cool-down"
        default:         return phase.capitalized
        }
    }
}

private struct FAQGuideSection: Identifiable {
    let id: String
    let title: String
    let body: String
    let tips: [String]
}

private func faqGuideSections(isNorwegian: Bool) -> [FAQGuideSection] {
    if isNorwegian {
        return [
            FAQGuideSection(
                id: "watch_sync",
                title: "Klokke og synkronisering",
                body: "Slik kobler du til pulsmåleren din og holder dataene oppdatert i Coachi.",
                tips: [
                    "Koble til Apple Watch eller annen støttet pulsmåler i profilen.",
                    "Start en kort testøkt for å sjekke at puls kommer inn live.",
                    "Hvis data ikke oppdateres, åpne Administrer pulsmålere og koble til på nytt.",
                ]
            ),
            FAQGuideSection(
                id: "profile",
                title: "Brukerprofil",
                body: "Finn ut hvor du endrer navn, e-post, språk og andre profilinnstillinger.",
                tips: [
                    "Åpne Personlig profil for å se og oppdatere kontodetaljene dine.",
                    "Logg ut og inn igjen hvis profilinformasjon ikke ser riktig ut.",
                    "Du kan slette kontoen din direkte fra profilfanen når du trenger det.",
                ]
            ),
            FAQGuideSection(
                id: "subscription",
                title: "Abonnement",
                body: "Her finner du veien til aktivering, gjenoppretting og håndtering av Premium.",
                tips: [
                    "Velg Administrer abonnement for å se hva som er inkludert i Gratis og Premium.",
                    "Bruk Gjenopprett kjøp hvis App Store-kjøp ikke dukker opp.",
                    "Aktive abonnement håndteres videre i App Store på iPhone.",
                ]
            ),
            FAQGuideSection(
                id: "heart_rate",
                title: "Puls og pulsmåler",
                body: "Gode råd for å få stabile pulsmålinger og riktige Coachi-økter.",
                tips: [
                    "Bruk hvilepuls og makspuls i Helseprofil for mer presis coaching.",
                    "Sjekk at klokken sitter tett nok under intervaller og kalde økter.",
                    "Hvis puls mangler, fortsetter Coachi med timing og struktur som normalt.",
                ]
            ),
        ]
    }

    return [
        FAQGuideSection(
            id: "watch_sync",
            title: "Watch and sync",
            body: "Learn how to connect your heart-rate source and keep data flowing into Coachi.",
            tips: [
                "Connect Apple Watch or another supported heart-rate source from your profile.",
                "Run a short test workout to confirm live heart rate is arriving.",
                "If sync looks stale, reconnect from Manage heart-rate monitors.",
            ]
        ),
        FAQGuideSection(
            id: "profile",
            title: "User profile",
            body: "Find the essentials for updating your account details and profile settings.",
            tips: [
                "Open Personal profile to review name, email, and account details.",
                "Sign out and back in if your profile information looks outdated.",
                "You can delete your account directly from the profile tab when needed.",
            ]
        ),
        FAQGuideSection(
            id: "subscription",
            title: "Subscription",
            body: "Get the basics for starting, restoring, and managing Premium inside Coachi.",
            tips: [
                "Use Manage subscription to compare what is included in Free and Premium.",
                "Tap Restore Purchases if an App Store purchase does not appear.",
                "Active subscriptions are managed further in the App Store on iPhone.",
            ]
        ),
        FAQGuideSection(
            id: "heart_rate",
            title: "Heart rate and sensors",
            body: "Practical advice for cleaner heart-rate capture and more reliable workout guidance.",
            tips: [
                "Set resting and max heart rate in Health profile for better guidance.",
                "Wear your watch snugly during intervals and colder workouts.",
                "If heart rate drops out, Coachi continues with timing and workout structure.",
            ]
        ),
    ]
}

private struct FAQGuideView: View {
    private var isNorwegian: Bool { L10n.current == .no }
    private var guideSections: [FAQGuideSection] { faqGuideSections(isNorwegian: isNorwegian) }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: L10n.faqTitle,
                    copyText: isNorwegian
                        ? "Her finner du korte forklaringer på det folk oftest trenger hjelp til i Coachi."
                        : "Here you will find short explanations for the things people most often need help with in Coachi."
                )

                ForEach(guideSections) { section in
                    SupportGuideCard(section: section)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.faqTitle)
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct ContactSupportView: View {
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Kontakt support" : "Contact support",
                    copyText: isNorwegian
                        ? "Har du støtt på et problem du ikke finner svaret på i FAQ-seksjonen? Kontakt vårt support-team, som kan hjelpe deg."
                        : "Have you run into an issue you cannot solve from the FAQ section? Contact our support team and we will help you."
                )

                NavigationLink {
                    SupportRequestFormView()
                } label: {
                    Text(isNorwegian ? "Kontakt support" : "Contact support")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 17)
                        .background(
                            Capsule(style: .continuous)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "7C3AED"), Color(hex: "4F46E5")],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                        )
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.contactSupport)
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct SupportRequestFormView: View {
    @EnvironmentObject private var appViewModel: AppViewModel
    @EnvironmentObject private var authManager: AuthManager
    @Environment(\.openURL) private var openURL

    @State private var subject = ""
    @State private var email = ""
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var accountStatus = ""
    @State private var category = ""
    @State private var watchType = ""
    @State private var phoneType = ""
    @State private var description = ""

    private var isNorwegian: Bool { L10n.current == .no }
    private var accountStatusOptions: [String] {
        isNorwegian
            ? ["Velg", "Jeg har et Premium-abonnement", "Jeg bruker gratisversjonen", "Jeg er ikke sikker"]
            : ["Select", "I have Premium", "I use the free version", "I am not sure"]
    }
    private var categoryOptions: [String] {
        isNorwegian
            ? ["Velg", "Klokke og synkronisering", "Brukerprofil", "Abonnement", "Puls og pulsmåler", "Annet"]
            : ["Select", "Watch and sync", "User profile", "Subscription", "Heart rate and sensors", "Other"]
    }
    private var isFormValid: Bool {
        !subject.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !email.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !firstName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !lastName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !description.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 18) {
                SupportCard(
                    title: isNorwegian ? "Kontakt support" : "Contact support",
                    copyText: isNorwegian
                        ? "Fortell oss kort hva du trenger hjelp med, så åpner vi en ferdig utfylt henvendelse til support."
                        : "Tell us briefly what you need help with and we will open a pre-filled support request."
                )

                SupportFormField(
                    title: isNorwegian ? "Overskrift / emne" : "Title / subject",
                    text: $subject,
                    keyboardType: .default
                )

                SupportFormField(
                    title: isNorwegian ? "E-post" : "Email",
                    text: $email,
                    keyboardType: .emailAddress
                )

                SupportFormField(
                    title: isNorwegian ? "Fornavn" : "First name",
                    text: $firstName,
                    keyboardType: .default
                )

                SupportFormField(
                    title: isNorwegian ? "Etternavn" : "Last name",
                    text: $lastName,
                    keyboardType: .default
                )

                SupportPickerField(
                    title: isNorwegian ? "Kontostatus" : "Account status",
                    selection: $accountStatus,
                    options: accountStatusOptions
                )

                SupportPickerField(
                    title: isNorwegian ? "Kategori" : "Category",
                    selection: $category,
                    options: categoryOptions
                )

                SupportFormField(
                    title: isNorwegian ? "Klokkemerke/type" : "Watch brand / type",
                    text: $watchType,
                    keyboardType: .default
                )

                SupportFormField(
                    title: isNorwegian ? "Telefontype" : "Phone type",
                    text: $phoneType,
                    keyboardType: .default
                )

                SupportTextEditorField(
                    title: isNorwegian ? "Beskrivelse" : "Description",
                    text: $description
                )

                Button {
                    openSupportDraft()
                } label: {
                    Text(isNorwegian ? "Send" : "Send")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 17)
                        .background(
                            Capsule(style: .continuous)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "7C3AED"), Color(hex: "4F46E5")],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                        )
                }
                .buttonStyle(.plain)
                .disabled(!isFormValid)
                .opacity(isFormValid ? 1 : 0.5)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.contactSupport)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            prefillFromCurrentUser()
        }
    }

    private func prefillFromCurrentUser() {
        if email.isEmpty {
            email = authManager.currentUser?.email ?? ""
        }
        if firstName.isEmpty && lastName.isEmpty {
            let displayName = authManager.currentUser?.displayName ?? appViewModel.userProfile.name
            let parts = displayName
                .split(separator: " ", omittingEmptySubsequences: true)
                .map(String.init)
            if let first = parts.first {
                firstName = first
                lastName = parts.dropFirst().joined(separator: " ")
            }
        }
        if accountStatus.isEmpty {
            accountStatus = accountStatusOptions.first ?? ""
        }
        if category.isEmpty {
            category = categoryOptions.first ?? ""
        }
    }

    private func openSupportDraft() {
        let accountLine = normalizedChoice(accountStatus)
        let categoryLine = normalizedChoice(category)
        let body = [
            "\(isNorwegian ? "Navn" : "Name"): \(firstName) \(lastName)",
            "\(isNorwegian ? "E-post" : "Email"): \(email)",
            "\(isNorwegian ? "Kontostatus" : "Account status"): \(accountLine)",
            "\(isNorwegian ? "Kategori" : "Category"): \(categoryLine)",
            "\(isNorwegian ? "Klokkemerke/type" : "Watch brand / type"): \(watchType)",
            "\(isNorwegian ? "Telefontype" : "Phone type"): \(phoneType)",
            "",
            "\(isNorwegian ? "Beskrivelse" : "Description"):",
            description,
        ]
        .joined(separator: "\n")

        var components = URLComponents()
        components.scheme = "mailto"
        components.path = coachiSupportEmail
        components.queryItems = [
            URLQueryItem(name: "subject", value: subject),
            URLQueryItem(name: "body", value: body),
        ]

        guard let url = components.url else { return }
        openURL(url)
    }

    private func normalizedChoice(_ value: String) -> String {
        let defaultValue = isNorwegian ? "Velg" : "Select"
        return value == defaultValue ? (isNorwegian ? "Ikke valgt" : "Not selected") : value
    }
}

struct PrivacyPolicyView: View {
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Kontakt for personvern" : "Privacy contact",
                    copyText: isNorwegian
                        ? "Coachi\nE-post: \(coachiSupportEmail)\nNettside: \(coachiWebsiteURL)"
                        : "Coachi\nEmail: \(coachiSupportEmail)\nWebsite: \(coachiWebsiteURL)"
                )

                SupportCard(
                    title: isNorwegian ? "Hva Coachi samler inn" : "What Coachi collects",
                    copyText: isNorwegian
                        ? "Coachi kan behandle kontoopplysninger, profil- og treningsdata, lyd- og interaksjonsdata, abonnementsopplysninger, tekniske logger og supporthenvendelser."
                        : "Coachi may process account details, profile and workout data, audio and interaction data, subscription information, technical logs, and support requests."
                )

                SupportCard(
                    title: isNorwegian ? "Hvorfor opplysningene brukes" : "Why data is used",
                    copyText: isNorwegian
                        ? "Opplysningene brukes for å levere coaching, lagre historikk, gi oppsummeringer, håndtere konto og abonnement, synkronisere lydpakker, yte support og forbedre kvalitet og sikkerhet."
                        : "Data is used to deliver coaching, store history, provide summaries, manage account and subscription, sync audio packs, provide support, and improve quality and security."
                )

                SupportCard(
                    title: isNorwegian ? "Behandlingsgrunnlag" : "Legal basis",
                    copyText: isNorwegian
                        ? "Vi behandler opplysninger på grunnlag av avtale, samtykke, berettiget interesse eller rettslig forpliktelse, avhengig av hva slags data og funksjon det gjelder."
                        : "We process data based on contract, consent, legitimate interests, or legal obligation, depending on the type of data and feature involved."
                )

                SupportCard(
                    title: isNorwegian ? "Lagringstid" : "Retention",
                    copyText: isNorwegian
                        ? "Opplysninger lagres så lenge det er nødvendig for å levere tjenesten, følge opp support, oppfylle lovkrav eller så lenge kontoen din er aktiv."
                        : "Data is kept as long as needed to provide the service, handle support, comply with legal requirements, or while your account remains active."
                )

                SupportCard(
                    title: isNorwegian ? "Databehandlere" : "Processors",
                    copyText: isNorwegian
                        ? "Hosting og drift: Render\nLydlagring og synk: Cloudflare R2\nTale og lydgenerering: konfigurert stemmetjeneste\nAI-funksjoner: aktiverte coach-tjenester\nAnalyse og feilovervåking: PostHog og Sentry når disse er aktivert\nE-post: Resend eller konfigurert SMTP-leverandør når e-post er aktivert\nDistribusjon og innlogging: Apple"
                        : "Hosting and operations: Render\nAudio storage and sync: Cloudflare R2\nSpeech and audio generation: configured voice service\nAI features: enabled coach services\nAnalytics and error monitoring: PostHog and Sentry when enabled\nEmail delivery: Resend or a configured SMTP provider when email is enabled\nDistribution and sign-in: Apple"
                )

                SupportCard(
                    title: isNorwegian ? "Dine rettigheter" : "Your rights",
                    copyText: isNorwegian
                        ? "Du kan be om innsyn, retting, sletting, begrensning, dataportabilitet og protestere der loven gir grunnlag. Kontakt oss på \(coachiSupportEmail)."
                        : "You can request access, correction, deletion, restriction, data portability, and object where the law allows it. Contact us at \(coachiSupportEmail)."
                )

                Text(
                    isNorwegian
                        ? "Sist oppdatert: \(coachiPrivacyUpdatedNo)"
                        : "Last updated: \(coachiPrivacyUpdatedEn)"
                )
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .padding(.horizontal, 4)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.privacyPolicy)
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct TermsOfUseView: View {
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Om tjenesten" : "About the service",
                    copyText: isNorwegian
                        ? "Coachi er en treningsapp med lydcoaching, treningshistorikk, kontofunksjoner, eventuelle Premium-funksjoner og stemmebaserte funksjoner når de er tilgjengelige."
                        : "Coachi is a training app with audio coaching, workout history, account features, possible Premium features, and voice-based features when available."
                )

                SupportCard(
                    title: isNorwegian ? "Abonnement og betaling" : "Subscriptions and payment",
                    copyText: isNorwegian
                        ? "Coachi er gratis å laste ned og bruke i en gratisversjon. Hvis Premium er tilgjengelig, kjøpes månedlig eller årlig abonnement gjennom Apple, og oppsigelse håndteres i App Store."
                        : "Coachi is free to download and includes a free version. If Premium is available, monthly or yearly subscriptions are purchased through Apple, and cancellation is handled in the App Store."
                )

                SupportCard(
                    title: isNorwegian ? "Helseforbehold" : "Health disclaimer",
                    copyText: isNorwegian
                        ? "Coachi er ikke medisinsk rådgivning. Du er selv ansvarlig for å vurdere om trening passer for deg og for å avbryte eller tilpasse aktiviteten ved smerte, svimmelhet eller ubehag."
                        : "Coachi is not medical advice. You remain responsible for deciding whether training is suitable for you and for stopping or adjusting activity if you experience pain, dizziness, or discomfort."
                )

                SupportCard(
                    title: isNorwegian ? "Brukeransvar" : "User responsibilities",
                    copyText: isNorwegian
                        ? "Du skal ikke misbruke tjenesten, omgå sikkerhetsmekanismer eller bruke Coachi på en måte som skader oss, andre brukere eller tredjepartsleverandører."
                        : "You must not misuse the service, bypass security mechanisms, or use Coachi in a way that harms us, other users, or third-party providers."
                )

                SupportCard(
                    title: isNorwegian ? "Tilgjengelighet og endringer" : "Availability and changes",
                    copyText: isNorwegian
                        ? "Vi forsøker å holde Coachi tilgjengelig og oppdatert, men vi kan ikke garantere feilfri drift. Vi kan oppdatere, endre eller fjerne funksjoner når det er nødvendig."
                        : "We try to keep Coachi available and up to date, but we cannot guarantee uninterrupted or error-free service. We may update, change, or remove features when needed."
                )

                SupportCard(
                    title: isNorwegian ? "Ansvarsbegrensning" : "Limitation of liability",
                    copyText: isNorwegian
                        ? "Så langt loven tillater det, er vi ikke ansvarlige for indirekte tap, avbrudd, sensorfeil eller tap som oppstår ved feil bruk av tjenesten."
                        : "To the extent permitted by law, we are not responsible for indirect loss, interruptions, sensor failures, or loss arising from misuse of the service."
                )

                SupportCard(
                    title: isNorwegian ? "Kontakt" : "Contact",
                    copyText: isNorwegian
                        ? "Coachi\n\(coachiSupportEmail)\n\(coachiWebsiteURL)"
                        : "Coachi\n\(coachiSupportEmail)\n\(coachiWebsiteURL)"
                )

                Text(
                    isNorwegian
                        ? "Sist oppdatert: \(coachiPrivacyUpdatedNo)"
                        : "Last updated: \(coachiPrivacyUpdatedEn)"
                )
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .padding(.horizontal, 4)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.termsOfUse)
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct DeleteAccountInfoView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    private var isNorwegian: Bool { L10n.current == .no }
    @State private var showDeleteConfirmation = false
    @State private var deleteErrorMessage: String?

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Slett konto" : "Delete account",
                    copyText: isNorwegian
                        ? "Du kan slette Coachi-kontoen din direkte i appen. Dette sletter kontoen din og fjerner tilgangen til kontoavhengige funksjoner."
                        : "You can delete your Coachi account directly in the app. This deletes your account and removes access to account-linked features."
                )

                SupportCard(
                    title: isNorwegian ? "Viktig å vite" : "Important to know",
                    copyText: isNorwegian
                        ? "Sletting av konto kan påvirke treningshistorikk, abonnementstilgang, lydinnstillinger og andre data som er knyttet til profilen din. Eventuelle Apple-abonnement må fortsatt administreres i App Store."
                        : "Deleting your account can affect workout history, subscription access, audio settings, and other data connected to your profile. Any Apple subscriptions must still be managed in the App Store."
                )

                Button {
                    showDeleteConfirmation = true
                } label: {
                    SettingsActionRow(
                        icon: "trash",
                        title: isNorwegian ? "Slett konto nå" : "Delete account now",
                        tint: CoachiTheme.danger
                    )
                }
                .buttonStyle(.plain)
                .disabled(authManager.isLoading)

                if let deleteErrorMessage, !deleteErrorMessage.isEmpty {
                    Text(deleteErrorMessage)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(CoachiTheme.danger)
                        .fixedSize(horizontal: false, vertical: true)
                }

                SupportCard(
                    title: isNorwegian ? "Trenger du hjelp?" : "Need help?",
                    copyText: coachiSupportEmail
                )

                Button {
                    openSupportEmail()
                } label: {
                    SettingsActionRow(
                        icon: "envelope.badge",
                        title: isNorwegian ? "Kontakt support" : "Contact support",
                        tint: CoachiTheme.primary
                    )
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(isNorwegian ? "Slett konto" : "Delete account")
        .navigationBarTitleDisplayMode(.inline)
        .confirmationDialog(
            isNorwegian ? "Slette kontoen din?" : "Delete your account?",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button(isNorwegian ? "Slett konto" : "Delete account", role: .destructive) {
                Task {
                    deleteErrorMessage = await authManager.deleteAccount()
                    if deleteErrorMessage == nil {
                        dismiss()
                    }
                }
            }
            Button(isNorwegian ? "Avbryt" : "Cancel", role: .cancel) {}
        } message: {
            Text(
                isNorwegian
                    ? "Dette sletter Coachi-kontoen din. Eventuelle Apple-abonnement må fortsatt avsluttes i App Store."
                    : "This deletes your Coachi account. Any Apple subscriptions must still be cancelled in the App Store."
            )
        }
    }

    private func openSupportEmail() {
        guard let url = URL(string: "mailto:\(coachiSupportEmail)") else { return }
        openURL(url)
    }
}

private struct SupportGuideCard: View {
    let section: FAQGuideSection

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(section.title)
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Text(section.body)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)

            VStack(alignment: .leading, spacing: 8) {
                ForEach(section.tips, id: \.self) { tip in
                    HStack(alignment: .top, spacing: 10) {
                        Circle()
                            .fill(CoachiTheme.primary)
                            .frame(width: 7, height: 7)
                            .padding(.top, 6)

                        Text(tip)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CoachiTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.4), lineWidth: 1)
        )
    }
}

private struct SupportFormField: View {
    let title: String
    @Binding var text: String
    let keyboardType: UIKeyboardType

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            TextField("", text: $text)
                .keyboardType(keyboardType)
                .textInputAutocapitalization(keyboardType == .emailAddress ? .never : .words)
                .autocorrectionDisabled(keyboardType == .emailAddress)
                .font(.system(size: 17, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 14)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                )
        }
    }
}

private struct SupportPickerField: View {
    let title: String
    @Binding var selection: String
    let options: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Picker(title, selection: $selection) {
                ForEach(options, id: \.self) { option in
                    Text(option).tag(option)
                }
            }
            .pickerStyle(.menu)
            .tint(CoachiTheme.textPrimary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
        }
    }
}

private struct SupportTextEditorField: View {
    let title: String
    @Binding var text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            TextEditor(text: $text)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(minHeight: 150)
                .padding(12)
                .scrollContentBackground(.hidden)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                )
        }
    }
}

struct SupportCard: View {
    let title: String
    let copyText: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Text(copyText)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CoachiTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.4), lineWidth: 1)
        )
    }
}

private struct SettingsCardRow: View {
    let icon: String
    let title: String
    let subtitle: String
    var showsChevron: Bool = true

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.body)
                .foregroundColor(CoachiTheme.primary)
                .frame(width: 36, height: 36)
                .background(CoachiTheme.primary.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(CoachiTheme.textPrimary)
                Text(subtitle)
                    .font(.system(size: 12))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .lineLimit(2)
            }

            Spacer()

            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .padding(12)
        .cardStyle()
    }
}

struct SettingsActionRow: View {
    let icon: String
    let title: String
    let tint: Color

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
            Text(title)
        }
        .font(.system(size: 14, weight: .medium))
        .foregroundColor(tint)
        .frame(maxWidth: .infinity)
        .padding(10)
        .cardStyle()
    }
}

private struct BirthDateEditorSheet: View {
    @Environment(\.dismiss) private var dismiss

    @State var selectedDate: Date
    let minDate: Date
    let maxDate: Date
    let onSave: (Date) -> Void

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                DatePicker(
                    "",
                    selection: $selectedDate,
                    in: minDate...maxDate,
                    displayedComponents: .date
                )
                .datePickerStyle(.wheel)
                .labelsHidden()
                .frame(maxWidth: .infinity)
                .padding(.top, 8)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, 16)
            .navigationTitle(L10n.dateOfBirth)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.current == .no ? "Avbryt" : "Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(L10n.current == .no ? "Lagre" : "Save") {
                        onSave(selectedDate)
                        dismiss()
                    }
                }
            }
        }
        .presentationDetents([.fraction(0.46), .medium])
    }
}

private enum MonitorBrand: String, CaseIterable, Identifiable {
    case appleWatch = "Apple Watch"
    case bluetoothSensor = "Bluetooth HR Sensor"
    case garmin = "Garmin"
    case polar = "Polar"
    case suunto = "Suunto"
    case fitbit = "Fitbit"
    case withings = "Withings"

    var id: String { rawValue }

    var capability: String {
        switch self {
        case .appleWatch, .bluetoothSensor:
            return L10n.liveCapability
        case .garmin, .polar, .suunto, .fitbit, .withings:
            return L10n.historyCapability
        }
    }
}

struct HeartRateMonitorsView: View {
    @EnvironmentObject var workoutViewModel: WorkoutViewModel

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 14) {
                VStack(alignment: .leading, spacing: 12) {
                    SupportCard(
                        title: L10n.current == .no ? "Gi Coachi tilgang til pulsdata" : "Give Coachi access to your heart-rate data",
                        copyText: L10n.current == .no
                            ? "Trykk én gang for å oppdatere Apple Health og sensorer. Coachi bruker dette for live coaching når puls er tilgjengelig."
                            : "Tap once to refresh Apple Health and sensor access. Coachi uses this for live coaching when heart rate is available."
                    )

                    Button {
                        workoutViewModel.refreshHealthSensors()
                    } label: {
                        SettingsActionRow(
                            icon: "heart.fill",
                            title: L10n.current == .no ? "Den er grei!" : "Sounds good!",
                            tint: CoachiTheme.primary
                        )
                    }
                    .buttonStyle(.plain)
                }

                Text(L10n.liveCoachingSourceHint)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)

                sectionHeader(label: L10n.liveCapability)
                monitorRows(for: [.appleWatch, .bluetoothSensor])

                sectionHeader(label: L10n.historyCapability)
                monitorRows(for: [.garmin, .polar, .suunto, .fitbit, .withings])

                Text(L10n.historySyncOnlyHint)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.horizontal, 20)
            .padding(.top, 8)
            .padding(.bottom, 80)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.manageHeartRateMonitors)
        .navigationBarTitleDisplayMode(.large)
        .task {
            workoutViewModel.refreshHealthSensors()
            workoutViewModel.beginSensorDiscovery()
        }
        .onDisappear {
            workoutViewModel.endSensorDiscovery()
        }
    }

    @ViewBuilder
    private func sectionHeader(label: String) -> some View {
        Text(label.uppercased())
            .font(.system(size: 11, weight: .bold))
            .foregroundColor(CoachiTheme.textSecondary)
            .tracking(1)
            .padding(.top, 6)
    }

    @ViewBuilder
    private func monitorRows(for brands: [MonitorBrand]) -> some View {
        VStack(spacing: 0) {
            ForEach(brands) { brand in
                if isActionableMonitor(brand) {
                    Button {
                        workoutViewModel.refreshHealthSensors()
                    } label: {
                        monitorRowContent(for: brand, showsChevron: true)
                    }
                    .buttonStyle(.plain)
                } else {
                    monitorRowContent(for: brand, showsChevron: false)
                }

                if brand != brands.last {
                    Rectangle()
                        .fill(CoachiTheme.borderSubtle.opacity(0.7))
                        .frame(height: 1)
                        .padding(.leading, 16)
                }
            }
        }
        .background(CoachiTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    @ViewBuilder
    private func monitorRowContent(for brand: MonitorBrand, showsChevron: Bool) -> some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(brand.rawValue)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)

                Text(brand.capability)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            Spacer()

            Text(statusText(for: brand))
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)

            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .contentShape(Rectangle())
    }

    private func isActionableMonitor(_ brand: MonitorBrand) -> Bool {
        brand == .appleWatch || brand == .bluetoothSensor
    }

    private func statusText(for brand: MonitorBrand) -> String {
        switch brand {
        case .appleWatch:
            return workoutViewModel.watchConnected ? L10n.connected : L10n.notConnected
        case .bluetoothSensor:
            return workoutViewModel.bleConnected ? L10n.connected : L10n.notConnected
        case .fitbit, .withings:
            return L10n.historyCapability
        case .garmin, .polar, .suunto:
            return L10n.historyViaBroadcastHint
        }
    }
}
