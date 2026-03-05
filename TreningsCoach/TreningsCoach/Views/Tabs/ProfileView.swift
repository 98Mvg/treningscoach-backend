//
//  ProfileView.swift
//  TreningsCoach
//
//  Settings-first profile tab styled after the native list layout
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @Binding var selectedTab: TabItem

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    profileSection
                    accountSection
                    helpSection
                    legalSection
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
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(CoachiTheme.textPrimary)
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 15, weight: .semibold))
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
                    .environmentObject(authManager)
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
        }
    }

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            sectionHeader(L10n.accountSettings)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.notifications)
            } label: {
                SettingsListRow(
                    icon: "bell.badge",
                    title: L10n.notifications
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.privacySettings)
            } label: {
                SettingsListRow(
                    icon: "shield",
                    title: L10n.privacySettings
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.sharingSettings)
            } label: {
                SettingsListRow(
                    icon: "square.and.arrow.up",
                    title: L10n.sharingSettings
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.manageSubscription)
            } label: {
                SettingsListRow(
                    icon: "bookmark",
                    title: L10n.manageSubscription
                )
            }
            .buttonStyle(.plain)
        }
    }

    private var helpSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            sectionHeader(L10n.helpAndSupport)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.faqTitle)
            } label: {
                SettingsListRow(
                    icon: "questionmark.bubble",
                    title: L10n.faqTitle,
                    trailingIcon: "arrow.up.right.square"
                )
            }
            .buttonStyle(.plain)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.contactSupport)
            } label: {
                SettingsListRow(
                    icon: "headphones",
                    title: L10n.contactSupport
                )
            }
            .buttonStyle(.plain)
        }
    }

    private var legalSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            sectionHeader(L10n.legal)

            settingsDivider

            NavigationLink {
                PlaceholderSettingsView(title: L10n.termsOfUse)
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
                PlaceholderSettingsView(title: L10n.privacyPolicy)
            } label: {
                SettingsListRow(
                    icon: "lock",
                    title: L10n.privacyPolicy,
                    trailingIcon: "arrow.up.right.square"
                )
            }
            .buttonStyle(.plain)
        }
    }

    private var signOutSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Button {
                authManager.signOut()
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

            Text("\(L10n.appVersionLabel) \(AppConfig.version)")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.horizontal, 24)
        }
        .padding(.top, 28)
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
    var trailingIcon: String = "chevron.right"

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(CoachiTheme.textTertiary)
                .frame(width: 30)

            Text(title)
                .font(.system(size: 17, weight: .regular))
                .foregroundColor(CoachiTheme.textPrimary)
                .lineLimit(2)

            Spacer(minLength: 8)

            Image(systemName: trailingIcon)
                .font(
                    trailingIcon == "arrow.up.right.square"
                        ? .system(size: 18, weight: .regular)
                        : .system(size: 14, weight: .semibold)
                )
                .foregroundColor(CoachiTheme.textTertiary)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 15)
        .contentShape(Rectangle())
    }
}

private struct HealthProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        PersonalProfileSettingsView()
            .environmentObject(appViewModel)
            .environmentObject(authManager)
            .navigationTitle(L10n.healthProfile)
            .navigationBarTitleDisplayMode(.inline)
    }
}

private struct PlaceholderSettingsView: View {
    let title: String

    var body: some View {
        ZStack {
            CoachiTheme.bg.ignoresSafeArea()
            VStack(spacing: 16) {
                Image(systemName: "clock")
                    .font(.system(size: 34, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                Text(title)
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .multilineTextAlignment(.center)
                Text(L10n.comingSoon)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
            }
            .padding(.horizontal, 24)
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct PersonalProfileSettingsView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @AppStorage("app_language") private var appLanguageCode: String = "en"
    @AppStorage("app_dark_mode_enabled") private var darkModeEnabled: Bool = true
    @AppStorage("user_birthdate_ts") private var birthdateTimestamp: Double = 0
    @State private var showingBirthDateEditor = false
    @State private var draftBirthDate: Date = Calendar.current.date(byAdding: .year, value: -28, to: Date()) ?? Date()

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                SettingsListRow(icon: "person.text.rectangle", title: L10n.current == .no ? "Navn: \(appViewModel.userProfile.name)" : "Name: \(appViewModel.userProfile.name)", trailingIcon: "chevron.right")

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

                Button {
                    draftBirthDate = storedBirthDate
                    showingBirthDateEditor = true
                } label: {
                    SettingsListRow(
                        icon: "calendar",
                        title: "\(L10n.dateOfBirth): \(birthDateDisplayLine)"
                    )
                }
                .buttonStyle(.plain)

                settingsDivider

                SettingsListRow(
                    icon: "chart.bar.fill",
                    title: "\(L10n.experienceLevel): \(appViewModel.trainingLevelDisplayName)"
                )

                settingsDivider

                NavigationLink {
                    SettingsView().environmentObject(appViewModel)
                } label: {
                    SettingsListRow(
                        icon: "info.circle",
                        title: "\(L10n.about): v\(AppConfig.version)"
                    )
                }
                .buttonStyle(.plain)

                settingsDivider

                Button {
                    authManager.signOut()
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
            .padding(.top, 8)
            .padding(.bottom, 80)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
        .navigationTitle(L10n.personalProfile)
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingBirthDateEditor) {
            BirthDateEditorSheet(
                selectedDate: draftBirthDate,
                minDate: minimumBirthDate,
                maxDate: Date(),
                onSave: { value in
                    persistBirthDate(value)
                }
            )
        }
    }

    private var settingsDivider: some View {
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

    private func persistBirthDate(_ value: Date) {
        let bounded = min(max(value, minimumBirthDate), Date())
        birthdateTimestamp = bounded.timeIntervalSince1970
        let years = Calendar.current.dateComponents([.year], from: bounded, to: Date()).year ?? 0
        let age = max(14, min(95, years))
        UserDefaults.standard.set(age, forKey: "user_age")
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
                Button {
                    if brand == .appleWatch || brand == .bluetoothSensor {
                        workoutViewModel.refreshHealthSensors()
                    }
                } label: {
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

                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(CoachiTheme.textTertiary)
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)

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
