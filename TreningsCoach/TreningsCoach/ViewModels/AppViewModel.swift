//
//  AppViewModel.swift
//  TreningsCoach
//
//  App-level state: onboarding, user profile, language
//

import Foundation
import SwiftUI
import UIKit
import UserNotifications
import Combine

struct LocalProfile {
    var name: String
    var trainingLevel: String
    var language: String
    var weeklyGoal: Int
}

enum AppDeepLinkDestination: Equatable {
    case home
    case workout
    case profile
    case paywall(context: String)
    case manageSubscription
    case restorePurchases

    var analyticsContext: String {
        switch self {
        case .home:
            return "home"
        case .workout:
            return "workout"
        case .profile:
            return "profile"
        case let .paywall(context):
            return "paywall:\(context)"
        case .manageSubscription:
            return "subscription_manage"
        case .restorePurchases:
            return "subscription_restore"
        }
    }
}

final class PushNotificationManager: NSObject, ObservableObject, UNUserNotificationCenterDelegate {
    static let shared = PushNotificationManager()

    private let notificationCenter = UNUserNotificationCenter.current()
    private let backendAPI = BackendAPIService.shared
    private let onboardingReminderRequestIdentifier = "coachi.onboarding.reminder.v1"
    private let workoutReminderRequestIdentifier = "coachi.workout.reminder.v1"
    private let deviceTokenDefaultsKey = "apns_device_token_hex"
    private let notificationDeepLinkKey = "deep_link"
    private let notificationSourceKey = "source"
    private let workoutReminderDeepLink = "coachi://tab/workout"

    @Published private(set) var authorizationStatus: UNAuthorizationStatus = .notDetermined
    @Published private(set) var apnsDeviceToken: String = UserDefaults.standard.string(forKey: "apns_device_token_hex") ?? ""
    @Published private(set) var lastRegistrationError: String?

    var hasAuthorizedNotifications: Bool {
        switch authorizationStatus {
        case .authorized, .provisional, .ephemeral:
            return true
        case .notDetermined, .denied:
            return false
        @unknown default:
            return false
        }
    }

    func configure() {
        notificationCenter.delegate = self
        Task {
            await refreshAuthorizationStatus()
        }
    }

    func refreshAuthorizationStatus() async {
        let settings = await notificationCenter.notificationSettings()
        await MainActor.run {
            authorizationStatus = settings.authorizationStatus
        }
    }

    func requestAuthorizationAndRegister() async -> Bool {
        let granted = (try? await notificationCenter.requestAuthorization(options: [.alert, .badge, .sound])) ?? false
        await refreshAuthorizationStatus()

        _ = await backendAPI.trackAnalyticsEvent(
            event: granted ? "push_permission_granted" : "push_permission_denied",
            metadata: [
                "source": "onboarding",
                "authorization_status": authorizationStatus.analyticsName,
            ]
        )

        guard granted else { return false }
        await registerForRemoteNotifications()
        return true
    }

    func registerForRemoteNotificationsIfAuthorized() async {
        await refreshAuthorizationStatus()
        guard hasAuthorizedNotifications else { return }
        await registerForRemoteNotifications()
    }

    func scheduleOnboardingReminderIfNeeded() async {
        await refreshAuthorizationStatus()
        guard hasAuthorizedNotifications else { return }
        await scheduleReminder(
            identifier: onboardingReminderRequestIdentifier,
            titleNo: "Coachi er klar",
            bodyNo: "Ta en ny økt når du er klar. Coachi coacher deg live underveis.",
            titleEn: "Coachi is ready",
            bodyEn: "Start another workout when you're ready. Coachi will guide you live.",
            source: "onboarding"
        )
    }

    func scheduleWorkoutReminderIfNeeded() async {
        await refreshAuthorizationStatus()
        guard hasAuthorizedNotifications else { return }
        await scheduleReminder(
            identifier: workoutReminderRequestIdentifier,
            titleNo: "Hold streaken i gang",
            bodyNo: "Ta en ny økt i morgen. Coachi er klar til å guide deg live.",
            titleEn: "Keep your streak going",
            bodyEn: "Start another workout tomorrow. Coachi is ready to guide you live.",
            source: "workout"
        )
    }

    func clearPendingCoachReminders() {
        notificationCenter.removePendingNotificationRequests(
            withIdentifiers: [
                onboardingReminderRequestIdentifier,
                workoutReminderRequestIdentifier,
            ]
        )
    }

    func handleDidRegisterForRemoteNotifications(deviceToken: Data) {
        let hexToken = deviceToken.map { String(format: "%02x", $0) }.joined()
        UserDefaults.standard.set(hexToken, forKey: deviceTokenDefaultsKey)

        Task { @MainActor in
            apnsDeviceToken = hexToken
            lastRegistrationError = nil
        }

        Task {
            _ = await backendAPI.trackAnalyticsEvent(
                event: "push_token_registered",
                metadata: [
                    "token_prefix": String(hexToken.prefix(12)),
                    "source": "apns",
                ]
            )
        }
    }

    func handleDidFailToRegisterForRemoteNotifications(error: Error) {
        let message = error.localizedDescription
        Task { @MainActor in
            lastRegistrationError = message
        }
        Task {
            _ = await backendAPI.trackAnalyticsEvent(
                event: "push_registration_failed",
                metadata: [
                    "source": "apns",
                    "error": message,
                ]
            )
        }
    }

    private func registerForRemoteNotifications() async {
        await MainActor.run {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        _ = center
        _ = notification
        return [.banner, .sound]
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        _ = center
        let request = response.notification.request
        let userInfo = request.content.userInfo
        let deepLink = userInfo[notificationDeepLinkKey] as? String
        let source = (userInfo[notificationSourceKey] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        _ = await backendAPI.trackAnalyticsEvent(
            event: "push_notification_opened",
            metadata: [
                "request_id": request.identifier,
                "source": source ?? "unknown",
                "deep_link": deepLink ?? "",
            ]
        )
        guard let deepLink, let url = URL(string: deepLink) else { return }
        await MainActor.run {
            UIApplication.shared.open(url)
        }
    }

    private func scheduleReminder(
        identifier: String,
        titleNo: String,
        bodyNo: String,
        titleEn: String,
        bodyEn: String,
        source: String
    ) async {
        notificationCenter.removePendingNotificationRequests(withIdentifiers: [identifier])

        let content = UNMutableNotificationContent()
        if L10n.current == .no {
            content.title = titleNo
            content.body = bodyNo
        } else {
            content.title = titleEn
            content.body = bodyEn
        }
        content.sound = .default
        content.userInfo = [
            notificationDeepLinkKey: workoutReminderDeepLink,
            notificationSourceKey: source,
        ]

        let request = UNNotificationRequest(
            identifier: identifier,
            content: content,
            trigger: UNCalendarNotificationTrigger(
                dateMatching: nextReminderComponents(after: Date()),
                repeats: false
            )
        )

        do {
            try await notificationCenter.add(request)
            _ = await backendAPI.trackAnalyticsEvent(
                event: "push_local_reminder_scheduled",
                metadata: [
                    "source": source,
                    "request_id": identifier,
                    "deep_link": workoutReminderDeepLink,
                ]
            )
        } catch {
            await MainActor.run {
                lastRegistrationError = error.localizedDescription
            }
        }
    }

    private func nextReminderComponents(after date: Date) -> DateComponents {
        let calendar = Calendar.autoupdatingCurrent
        let nextDay = calendar.date(byAdding: .day, value: 1, to: date) ?? date
        var components = calendar.dateComponents([.year, .month, .day], from: nextDay)
        components.hour = 18
        components.minute = 0
        return components
    }
}

private extension UNAuthorizationStatus {
    var analyticsName: String {
        switch self {
        case .notDetermined:
            return "not_determined"
        case .denied:
            return "denied"
        case .authorized:
            return "authorized"
        case .provisional:
            return "provisional"
        case .ephemeral:
            return "ephemeral"
        @unknown default:
            return "unknown"
        }
    }
}

extension AppViewModel {
    struct OnboardingProfileDraft {
        var firstName: String
        var lastName: String
        var birthDate: Date
        var gender: String
        var heightCm: Int
        var weightKg: Int
        var hrMax: Int
        var restingHR: Int
        var doesEnduranceTraining: Bool
        var hardestIntensity: String
        var moderateSessionsPerWeek: String
        var moderateDuration: String
        var notificationsOptIn: Bool
        var languageCode: String
        var trainingLevel: String

        var displayName: String {
            let first = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
            let last = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
            let joined = [first, last].filter { !$0.isEmpty }.joined(separator: " ")
            return joined.isEmpty ? L10n.athlete : joined
        }

        var age: Int {
            let years = Calendar.current.dateComponents([.year], from: birthDate, to: Date()).year ?? 0
            return max(14, min(95, years))
        }
    }
}

@MainActor
class AppViewModel: ObservableObject {
    @AppStorage("has_completed_onboarding") var hasCompletedOnboarding: Bool = false
    @AppStorage("user_display_name") var userName: String = ""
    @AppStorage("training_level") var trainingLevelRaw: String = "beginner"
    @AppStorage("app_language") var languageCode: String = "en"
    @AppStorage("spotify_prompt_pending") private var spotifyPromptPending: Bool = false
    @AppStorage("spotify_prompt_seen") private var spotifyPromptSeen: Bool = false
    @Published var pendingDeepLink: AppDeepLinkDestination?
    @Published private(set) var coachiProgressState = CoachiProgressState()
    let pushNotificationManager = PushNotificationManager.shared
    private var cancellables: Set<AnyCancellable> = []

    var userProfile: LocalProfile {
        LocalProfile(
            name: userName.isEmpty ? L10n.athlete : userName,
            trainingLevel: trainingLevelRaw,
            language: languageCode,
            weeklyGoal: 4
        )
    }

    let authManager = AuthManager.shared
    private let backendAPI = BackendAPIService.shared

    init() {
        refreshCoachiProgress()

        authManager.$currentUser
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                self?.refreshCoachiProgress()
            }
            .store(in: &cancellables)

        NotificationCenter.default.publisher(for: .coachiProgressDidChange)
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                self?.refreshCoachiProgress()
            }
            .store(in: &cancellables)
    }

    var trainingLevelDisplayName: String {
        switch trainingLevelRaw {
        case "advanced":
            return L10n.current == .no ? "Avansert" : "Advanced"
        case "intermediate":
            return L10n.current == .no ? "Middels" : "Intermediate"
        default:
            return L10n.current == .no ? "Nybegynner" : "Beginner"
        }
    }

    var coachiLevelLabel: String {
        if L10n.current == .no {
            return "Nivå \(coachiProgressState.level)"
        }
        return "Level \(coachiProgressState.level)"
    }

    var coachiXPProgressFraction: Double {
        coachiProgressState.xpFraction
    }

    var coachiXPLine: String {
        if coachiProgressState.isMaxLevel {
            return L10n.maxLevelReached
        }
        return "\(coachiProgressState.xpToNextLevel) \(L10n.xpToNextLevel)"
    }

    var coachiXPValueLine: String {
        if coachiProgressState.isMaxLevel {
            return "\(CoachiProgressState.xpPerLevel)/\(CoachiProgressState.xpPerLevel) \(L10n.xp)"
        }
        return "\(coachiProgressState.xpInCurrentLevel)/\(CoachiProgressState.xpPerLevel) \(L10n.xp)"
    }

    func refreshCoachiProgress() {
        coachiProgressState = CoachiProgressStore.load(for: currentProgressUserID)
    }

    private var currentProgressUserID: String? {
        authManager.currentUser?.id
    }

    func completeOnboarding(profile: OnboardingProfileDraft) {
        let defaults = UserDefaults.standard
        userName = profile.displayName
        trainingLevelRaw = profile.trainingLevel
        languageCode = profile.languageCode

        defaults.set(profile.displayName, forKey: "user_display_name")
        defaults.set(profile.trainingLevel, forKey: "training_level")
        defaults.set(profile.languageCode, forKey: "app_language")
        defaults.removeObject(forKey: "good_coach_workout_count")

        defaults.set(profile.firstName, forKey: "user_first_name")
        defaults.set(profile.lastName, forKey: "user_last_name")
        defaults.set(profile.birthDate.timeIntervalSince1970, forKey: "user_birthdate_ts")
        defaults.set(profile.age, forKey: "user_age")
        defaults.set(profile.gender, forKey: "user_gender")
        defaults.set(profile.heightCm, forKey: "user_height_cm")
        defaults.set(profile.weightKg, forKey: "user_weight_kg")

        defaults.set(profile.hrMax, forKey: "hr_max")
        defaults.set(profile.restingHR, forKey: "resting_hr")

        defaults.set(profile.doesEnduranceTraining, forKey: "user_endurance_training")
        defaults.set(profile.hardestIntensity, forKey: "user_hardest_intensity")
        defaults.set(profile.moderateSessionsPerWeek, forKey: "user_moderate_sessions_per_week")
        defaults.set(profile.moderateDuration, forKey: "user_moderate_duration")
        defaults.set(profile.notificationsOptIn, forKey: "notifications_opt_in")

        hasCompletedOnboarding = true
        if !spotifyPromptSeen {
            spotifyPromptPending = true
        }

        Task {
            await syncProfileToBackend(reason: "onboarding")
            if profile.notificationsOptIn {
                await pushNotificationManager.scheduleOnboardingReminderIfNeeded()
            }
            _ = await backendAPI.trackAnalyticsEvent(
                event: "onboarding_completed",
                metadata: [
                    "language": profile.languageCode,
                    "training_level": profile.trainingLevel,
                    "notifications_opt_in": profile.notificationsOptIn,
                    "signed_in": authManager.hasUsableSession(),
                ]
            )
        }
    }

    /// Called after a successful login for a user who already completed onboarding on a previous
    /// install or device. Skips the full profile setup flow and lands the user in the main app.
    /// Any existing backend profile data is re-synced in the background after the transition.
    func completeOnboardingForReturningUser(displayName: String, languageCode: String) {
        let defaults = UserDefaults.standard
        let incomingDisplayName = displayName.trimmingCharacters(in: .whitespacesAndNewlines)
        let preferredDisplayName = authoritativeStoredDisplayName(defaults: defaults) ?? incomingDisplayName

        if !preferredDisplayName.isEmpty {
            userName = preferredDisplayName
            defaults.set(preferredDisplayName, forKey: "user_display_name")
            if defaults.string(forKey: "user_first_name")?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ?? true {
                let parts = preferredDisplayName
                    .split(separator: " ", omittingEmptySubsequences: true)
                    .map(String.init)
                if let first = parts.first {
                    defaults.set(first, forKey: "user_first_name")
                    defaults.set(parts.dropFirst().joined(separator: " "), forKey: "user_last_name")
                }
            }
        }
        if !languageCode.isEmpty {
            self.languageCode = languageCode
            defaults.set(languageCode, forKey: "app_language")
        }
        hasCompletedOnboarding = true
        Task {
            await syncProfileToBackend(reason: "returning_user_login")
            _ = await backendAPI.trackAnalyticsEvent(
                event: "onboarding_skipped_returning_user",
                metadata: ["language": languageCode]
            )
        }
    }

    private func authoritativeStoredDisplayName(defaults: UserDefaults = .standard) -> String? {
        let storedFirst = defaults.string(forKey: "user_first_name")?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let storedLast = defaults.string(forKey: "user_last_name")?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let storedCombinedName = [storedFirst, storedLast]
            .filter { !$0.isEmpty }
            .joined(separator: " ")
        if !storedCombinedName.isEmpty {
            return storedCombinedName
        }

        let storedDisplayName = defaults.string(forKey: "user_display_name")?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return storedDisplayName.isEmpty ? nil : storedDisplayName
    }

    func resetOnboarding() {
        let defaults = UserDefaults.standard
        let keysToClear = [
            "user_display_name",
            "training_level",
            "user_first_name",
            "user_last_name",
            "user_birthdate_ts",
            "user_age",
            "user_gender",
            "user_height_cm",
            "user_weight_kg",
            "hr_max",
            "resting_hr",
            "user_endurance_training",
            "user_hardest_intensity",
            "user_moderate_sessions_per_week",
            "user_moderate_duration",
            "notifications_opt_in",
            "good_coach_workout_count",
        ]
        keysToClear.forEach { defaults.removeObject(forKey: $0) }

        userName = ""
        trainingLevelRaw = "beginner"
        hasCompletedOnboarding = false
        CoachiProgressStore.clearGuestProgress()
        refreshCoachiProgress()
        pushNotificationManager.clearPendingCoachReminders()
    }

    func syncProfileToBackend(reason: String) async {
        guard authManager.hasUsableSession() else { return }
        let defaults = UserDefaults.standard
        let payload = BackendUserProfilePayload(
            name: defaults.string(forKey: "user_display_name"),
            sex: defaults.string(forKey: "user_gender"),
            age: defaults.object(forKey: "user_age") as? Int,
            heightCm: defaults.object(forKey: "user_height_cm") as? Int,
            weightKg: defaults.object(forKey: "user_weight_kg") as? Int,
            maxHrBpm: defaults.object(forKey: "hr_max") as? Int,
            restingHrBpm: defaults.object(forKey: "resting_hr") as? Int,
            profileUpdatedAt: ISO8601DateFormatter().string(from: Date())
        )
        do {
            try await backendAPI.upsertUserProfile(payload)
            print("📤 Profile upsert reason=\(reason)")
        } catch {
            print("⚠️ Profile upsert failed reason=\(reason) error=\(error.localizedDescription)")
        }
    }

    func handleIncomingURL(_ url: URL) {
        guard let scheme = url.scheme?.lowercased() else { return }
        let normalizedHost = (url.host ?? "").lowercased()
        let acceptsScheme = scheme == "coachi"
        let acceptsUniversalLink = scheme == "https" && ["coachi.app", "www.coachi.app"].contains(normalizedHost)
        guard acceptsScheme || acceptsUniversalLink else { return }

        let host = acceptsUniversalLink ? url.pathComponents.dropFirst().first?.lowercased() ?? "" : normalizedHost
        let pathComponents = url.pathComponents.filter { $0 != "/" }
        let routeComponents = acceptsUniversalLink ? Array(pathComponents.dropFirst()) : pathComponents
        let queryItems = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
        let queryValue: (String) -> String? = { name in
            queryItems.first(where: { $0.name == name })?.value?.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        switch host {
        case "tab":
            switch routeComponents.first?.lowercased() {
            case "home":
                pendingDeepLink = .home
            case "workout":
                pendingDeepLink = .workout
            case "profile":
                pendingDeepLink = .profile
            default:
                pendingDeepLink = nil
            }
        case "paywall":
            pendingDeepLink = .paywall(context: queryValue("context") ?? "general")
        case "subscription":
            switch routeComponents.first?.lowercased() {
            case "manage":
                pendingDeepLink = .manageSubscription
            case "restore":
                pendingDeepLink = .restorePurchases
            default:
                pendingDeepLink = nil
            }
        default:
            pendingDeepLink = nil
        }
    }

    func consumePendingDeepLink() {
        pendingDeepLink = nil
    }
}
