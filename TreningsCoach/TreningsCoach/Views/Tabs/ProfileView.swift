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

struct ProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var subscriptionManager: SubscriptionManager
    @Environment(\.openURL) private var openURL
    @Binding var selectedTab: TabItem
    @State private var showingSignOutConfirmation = false
    @State private var showPaywall = false
    @State private var showManageSubscription = false

    private var isGuestMode: Bool {
        appViewModel.hasCompletedOnboarding && !authManager.isAuthenticated
    }

    private var hasPremiumAccess: Bool {
        subscriptionManager.hasPremiumAccess
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    profileSection
                    premiumSection
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
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .sheet(isPresented: $showPaywall) {
            PaywallView(context: .general)
        }
        .navigationDestination(isPresented: $showManageSubscription) {
            ManageSubscriptionView()
                .environmentObject(subscriptionManager)
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

            NavigationLink {
                AboutCoachiView()
                    .environmentObject(appViewModel)
            } label: {
                SettingsListRow(
                    icon: "info.circle",
                    title: "\(L10n.aboutCoachi) · v\(AppConfig.version)"
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
    }

    private var premiumSection: some View {
        VStack(spacing: 12) {
            if !hasPremiumAccess {
                Button { showPaywall = true } label: {
                    HStack(spacing: 14) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .fill(Color(hex: "5B4FD1").opacity(0.10))
                                .frame(width: 38, height: 38)
                            Image(systemName: "star.fill")
                                .font(.system(size: 17, weight: .semibold))
                                .foregroundStyle(Color(hex: "5B4FD1"))
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(L10n.current == .no ? "Se alle tilbudene" : "See all offers")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(CoachiTheme.textPrimary)
                            Text(L10n.current == .no ? "Velg mellom måneds- eller årsabonnement." : "Choose monthly or yearly premium.")
                                .font(.system(size: 13, weight: .regular))
                                .foregroundColor(CoachiTheme.textSecondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(CoachiTheme.textTertiary)
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
                    .background(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .fill(CoachiTheme.surfaceElevated)
                    )
                    .padding(.horizontal, 16)
                }
                .buttonStyle(.plain)
            } else {
                HStack(spacing: 14) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(Color(hex: "22C55E").opacity(0.12))
                            .frame(width: 38, height: 38)
                        Image(systemName: "checkmark.seal.fill")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(Color(hex: "22C55E"))
                    }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(L10n.current == .no ? "Premium er aktivt" : "Premium is active")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(subscriptionManager.resolvedPlanLabel)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .fill(CoachiTheme.surfaceElevated)
                )
                .padding(.horizontal, 16)
            }
        }
        .padding(.top, 20)
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
    private let freeHighlights: [(String, String)] = [
        ("Kjernecoaching", "Core coaching"),
        ("Coach Score og oppsummering", "Coach Score and summary"),
        ("Nylige økter", "Recent workouts"),
    ]
    private let premiumHighlights: [(String, String)] = [
        ("Live voice med coachen", "Live voice with your coach"),
        ("Mer historikk og høyere grenser", "More history and higher limits"),
        ("Måneds- eller årsabonnement", "Monthly or yearly subscription"),
    ]

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 18) {
                Text(isNorwegian ? "Inkludert i abonnementet" : "Included in subscription")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)

                statusCard(
                    title: isNorwegian ? "Gratis" : "Free",
                    headline: isNorwegian ? "Kjernecoaching" : "Core coaching",
                    detailText: isNorwegian ? "Gratis å bruke" : "Free to use",
                    highlights: freeHighlights,
                    isSelected: !hasPremiumAccess,
                    accentColor: CoachiTheme.textSecondary
                )

                statusCard(
                    title: "Premium",
                    headline: localizedPlanStatus,
                    detailText: hasPremiumAccess
                        ? (isNorwegian ? "Aktivt i App Store" : "Active in the App Store")
                        : (isNorwegian ? "Alle Coachi-funksjoner" : "All Coachi features"),
                    highlights: premiumHighlights,
                    isSelected: hasPremiumAccess,
                    accentColor: Color(hex: "8B5CF6"),
                    ribbonTitle: isNorwegian ? "Populær" : "Popular"
                )

                Button {
                    showPaywall = true
                } label: {
                    Text(isNorwegian ? "Se alle tilbudene" : "See all offers")
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

    private func statusCard(
        title: String,
        headline: String,
        detailText: String,
        highlights: [(String, String)],
        isSelected: Bool,
        accentColor: Color,
        ribbonTitle: String? = nil
    ) -> some View {
        Button {
            if !isSelected {
                showPaywall = true
            }
        } label: {
            VStack(alignment: .leading, spacing: 0) {
                if let ribbonTitle {
                    HStack {
                        Text(ribbonTitle)
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.white)
                        Spacer()
                        if isSelected {
                            Image(systemName: "checkmark")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(Color(hex: "A78BFA"))
                }

                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(title)
                            .font(.system(size: 19, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(headline)
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(detailText)
                            .font(.system(size: 15, weight: .regular))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 6) {
                        Text(isSelected ? (isNorwegian ? "Aktiv" : "Current") : title)
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(isSelected ? accentColor : CoachiTheme.textPrimary)
                        if isSelected && ribbonTitle == nil {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(accentColor)
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 18)
                .padding(.bottom, 14)

                VStack(alignment: .leading, spacing: 8) {
                    ForEach(highlights.indices, id: \.self) { index in
                        let item = highlights[index]
                        HStack(spacing: 10) {
                            Image(systemName: "checkmark")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundColor(accentColor)
                            Text(isNorwegian ? item.0 : item.1)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 18)
            }
            .background(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(CoachiTheme.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(
                        isSelected ? accentColor : CoachiTheme.borderSubtle.opacity(0.28),
                        lineWidth: isSelected ? 3 : 1
                    )
            )
            .shadow(color: Color.black.opacity(0.06), radius: 18, x: 0, y: 10)
        }
        .buttonStyle(.plain)
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
    @State private var showingSignOutConfirmation = false

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

                if authManager.isAuthenticated {
                    settingsDivider

                    sectionHeader(L10n.account)

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

                if authManager.isAuthenticated || isGuestMode {
                    if !authManager.isAuthenticated {
                        sectionHeader(L10n.account)
                        settingsDivider
                    }

                    Button {
                        showingSignOutConfirmation = true
                    } label: {
                        HStack(spacing: 14) {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                                .font(.system(size: 16))
                                .foregroundColor(CoachiTheme.danger)
                                .frame(width: 30)

                            Text(L10n.signOut)
                                .font(.system(size: 17, weight: .semibold))
                                .foregroundColor(CoachiTheme.danger)

                            Spacer()
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

    private func exitCurrentMode() {
        let shouldResetOnboarding = isGuestMode
        authManager.signOut()
        if shouldResetOnboarding {
            appViewModel.resetOnboarding()
        }
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
    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: L10n.trainingHistory,
                    copyText: isNorwegian
                        ? "Coachi lagrer økter og oppsummeringer slik at du kan vise fremgang over tid. Hvor mye historikk du ser, kan avhenge av kontostatus og produktnivå."
                        : "Coachi stores workouts and summaries so you can review progress over time. How much history you see may depend on account status and product tier."
                )

                SupportCard(
                    title: L10n.dataAndPrivacy,
                    copyText: isNorwegian
                        ? "Coachi bruker data for å levere coaching, lagre økter, holde tjenesten stabil og gi deg innsikt i treningen. Selskapsdetaljer fylles inn senere."
                        : "Coachi uses data to deliver coaching, store workouts, keep the service stable, and give you insight into your training. Company details will be filled in later."
                )

                SupportCard(
                    title: L10n.current == .no ? "Juridisk og personvern" : "Legal and privacy",
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
    }
}

private struct SupportFAQItem: Identifiable {
    let id: String
    let question: String
    let answer: String
}

private func supportFAQItems(isNorwegian: Bool) -> [SupportFAQItem] {
    if isNorwegian {
        return [
            SupportFAQItem(
                id: "how",
                question: "Hvordan fungerer Coachi?",
                answer: "Coachi guider deg gjennom økter med korte lydsignaler, overganger og tydelige beskjeder underveis."
            ),
            SupportFAQItem(
                id: "watch",
                question: "Trenger jeg Apple Watch eller pulsklokke?",
                answer: "Nei. Du kan bruke Coachi uten puls. Hvis puls er tilgjengelig, kan coachingen bli mer presis."
            ),
            SupportFAQItem(
                id: "no_hr",
                question: "Hva skjer hvis puls mangler?",
                answer: "Coachi fortsetter med struktur og timing. Du kan fortsatt fullføre økten uten live puls."
            ),
            SupportFAQItem(
                id: "free",
                question: "Hva er inkludert i gratisversjonen?",
                answer: "Kjernecoaching, lydsignaler, nedtellinger, enkel oppsummering, coach score og nylige økter er en del av gratisopplevelsen."
            ),
            SupportFAQItem(
                id: "premium",
                question: "Hva er inkludert i Premium?",
                answer: "Premium låser opp mer av Coachi, som live voice, høyere grenser og andre abonnementsbaserte funksjoner. Når Premium er tilgjengelig i appen, kan du velge månedlig eller årlig abonnement."
            ),
            SupportFAQItem(
                id: "subscription",
                question: "Hvordan avslutter jeg abonnementet?",
                answer: "Hvis du abonnerer gjennom Apple, administrerer eller avslutter du abonnementet i App Store-abonnementene dine. Gjenoppretting av kjøp gjøres i Coachi."
            ),
            SupportFAQItem(
                id: "delete",
                question: "Hvordan sletter jeg kontoen min?",
                answer: "Åpne Slett konto i innstillinger for å slette kontoen direkte i appen. Kontakt \(coachiSupportEmail) hvis du trenger hjelp."
            ),
            SupportFAQItem(
                id: "support",
                question: "Hvordan kontakter jeg support?",
                answer: "Kontakt oss på \(coachiSupportEmail) og beskriv hva som skjedde, hvilken enhet du bruker og gjerne legg ved skjermbilder."
            ),
        ]
    }

    return [
        SupportFAQItem(
            id: "how",
            question: "How does Coachi work?",
            answer: "Coachi guides your workouts with short audio cues, transitions, and clear instructions during the session."
        ),
        SupportFAQItem(
            id: "watch",
            question: "Do I need Apple Watch or a heart-rate sensor?",
            answer: "No. You can use Coachi without heart rate. If heart rate is available, coaching can become more precise."
        ),
        SupportFAQItem(
            id: "no_hr",
            question: "What happens if heart rate is missing?",
            answer: "Coachi continues with structure and timing cues. You can still complete the workout without live heart rate."
        ),
        SupportFAQItem(
            id: "free",
            question: "What is included in the free version?",
            answer: "Core coaching, audio cues, countdowns, a simple summary, coach score, and recent workouts are part of the free experience."
        ),
        SupportFAQItem(
            id: "premium",
            question: "What is included in Premium?",
            answer: "Premium unlocks deeper Coachi features like live voice, higher limits, and other subscription-linked features. When Premium is available in the app, you can choose a monthly or yearly subscription."
        ),
        SupportFAQItem(
            id: "subscription",
            question: "How do I cancel my subscription?",
            answer: "If you subscribe through Apple, you manage or cancel your subscription in your App Store subscriptions. Restore Purchases is available inside Coachi."
        ),
        SupportFAQItem(
            id: "delete",
            question: "How do I delete my account?",
            answer: "Open Delete account in settings to delete your account directly in the app. Contact \(coachiSupportEmail) if you need help."
        ),
        SupportFAQItem(
            id: "support",
            question: "How do I contact support?",
            answer: "Contact us at \(coachiSupportEmail) and include what happened, which device you use, and screenshots if helpful."
        ),
    ]
}

private struct ContactSupportView: View {
    @Environment(\.openURL) private var openURL
    private var isNorwegian: Bool { L10n.current == .no }
    private var faqItems: [SupportFAQItem] { supportFAQItems(isNorwegian: isNorwegian) }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 16) {
                SupportCard(
                    title: isNorwegian ? "Kontakt support" : "Contact support",
                    copyText: isNorwegian
                        ? "Hvis noe ikke fungerer som det skal, eller du trenger hjelp, kan du kontakte oss direkte. Vi prioriterer klare beskrivelser og praktiske detaljer."
                        : "If something is not working as expected, or you need help, you can contact us directly. Clear descriptions and practical details help us resolve issues faster."
                )

                SupportCard(
                    title: isNorwegian ? "Support" : "Support",
                    copyText: "\(coachiSupportEmail)\n\(coachiSupportURL)"
                )

                HStack(spacing: 12) {
                    Button {
                        openSupportEmail()
                    } label: {
                        SettingsActionRow(
                            icon: "paperplane",
                            title: isNorwegian ? "Send e-post til support" : "Email support",
                            tint: CoachiTheme.primary
                        )
                    }
                    .buttonStyle(.plain)

                    Button {
                        openSupportSite()
                    } label: {
                        SettingsActionRow(
                            icon: "arrow.up.right.square",
                            title: isNorwegian ? "Åpne supportside" : "Open support page",
                            tint: CoachiTheme.textPrimary
                        )
                    }
                    .buttonStyle(.plain)
                }

                SupportCard(
                    title: isNorwegian ? "Ta gjerne med dette" : "Include this if possible",
                    copyText: isNorwegian
                        ? "Appversjon, enhetsmodell og om problemet skjedde under en økt, ved innlogging eller under synk av lydpakke. Skjermbilder er nyttige hvis du har dem."
                        : "App version, device model, and whether the issue happened during a workout, during sign-in, or during audio-pack sync. Screenshots are useful if you have them."
                )

                SupportCard(
                    title: isNorwegian ? "Hva support kan hjelpe med" : "What support can help with",
                    copyText: isNorwegian
                        ? "Feil under økter, problemer med konto, spørsmål om historikk, lydpakke, abonnement og andre tekniske problemer i Coachi."
                        : "Workout issues, account problems, questions about history, audio packs, subscriptions, and other technical issues in Coachi."
                )

                Text(L10n.faqTitle)
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 6)

                ForEach(faqItems) { item in
                    SupportCard(
                        title: item.question,
                        copyText: item.answer
                    )
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 12)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.contactSupport)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func openSupportEmail() {
        guard let url = URL(string: "mailto:\(coachiSupportEmail)") else { return }
        openURL(url)
    }

    private func openSupportSite() {
        guard let url = URL(string: coachiSupportURL) else { return }
        openURL(url)
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
