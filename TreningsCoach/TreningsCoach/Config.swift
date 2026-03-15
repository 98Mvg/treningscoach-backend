//
//  Config.swift
//  TreningsCoach
//
//  Central configuration — production URLs, timings, animation & layout constants
//

import Foundation
import SwiftUI

// MARK: - App Configuration

struct AppConfig {
    // MARK: - App Info
    static let appName = "Coachi"
    static let appTagline = "Real-time running coach that keeps you in the right HR zone and uses breathing to help you get there."
    static let version = "3.0.0"

    // MARK: - Backend
    static let productionURL = "https://treningscoach-backend.onrender.com"
    static let localURL = "http://localhost:5001"
    static let backendURL = productionURL

    // MARK: - Phase Timings (seconds)
    static let warmupDuration: TimeInterval = 120   // 2 minutes
    static let intenseDuration: TimeInterval = 900   // 15 minutes

    // MARK: - Animation Constants
    enum Anim {
        static let orbIdlePulse: Double = 1.8
        static let orbListeningPulse: Double = 1.2
        static let orbSpeakingWave: Double = 0.6
        static let transitionSpring: SwiftUI.Animation = .spring(response: 0.5, dampingFraction: 0.8)
        static let buttonSpring: SwiftUI.Animation = .spring(response: 0.35, dampingFraction: 0.7)
        static let cardAppear: SwiftUI.Animation = .easeOut(duration: 0.4)
    }

    // MARK: - Layout Constants
    enum Layout {
        static let orbSize: CGFloat = 120
        static let ctaButtonSize: CGFloat = 160
        static let timerRingSize: CGFloat = 200
        static let tabBarHeight: CGFloat = 70
        static let cardCornerRadius: CGFloat = 16
    }

    // MARK: - Audio Settings
    struct Audio {
        static let sampleRate: Double = 44100.0
        static let channels = 1
        static let bitDepth = 16
    }

    // MARK: - Network Settings
    struct Network {
        static let requestTimeout: TimeInterval = 60
        static let resourceTimeout: TimeInterval = 120
    }

    // MARK: - Auth Feature Flags
    struct Auth {
        private static func boolInfoValue(_ key: String, default defaultValue: Bool = false) -> Bool {
            guard let raw = Bundle.main.object(forInfoDictionaryKey: key) else {
                return defaultValue
            }
            if let boolValue = raw as? Bool {
                return boolValue
            }
            if let stringValue = raw as? String {
                switch stringValue.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
                case "1", "true", "yes", "on":
                    return true
                case "0", "false", "no", "off":
                    return false
                default:
                    return defaultValue
                }
            }
            return defaultValue
        }

        private static func stringInfoValue(_ key: String) -> String? {
            guard let raw = Bundle.main.object(forInfoDictionaryKey: key) else {
                return nil
            }
            if let stringValue = raw as? String {
                return normalizedConfigString(stringValue)
            }
            return nil
        }

        private static func normalizedConfigString(_ rawValue: String?) -> String? {
            guard let rawValue else {
                return nil
            }

            let candidate = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !candidate.isEmpty else {
                return nil
            }

            let uppercase = candidate.uppercased()
            if candidate.hasPrefix("$(") && candidate.hasSuffix(")") {
                return nil
            }
            if uppercase.hasPrefix("YOUR_") || uppercase.contains("PLACEHOLDER") {
                return nil
            }

            return candidate
        }

        static let appleSignInFeatureEnabled: Bool = boolInfoValue("APPLE_SIGN_IN_ENABLED", default: false)
        static let emailSignInFeatureEnabled: Bool = boolInfoValue("EMAIL_SIGN_IN_ENABLED", default: true)
        static let googleSignInFeatureEnabled: Bool = boolInfoValue("GOOGLE_SIGN_IN_ENABLED", default: true)
        static let facebookSignInFeatureEnabled: Bool = boolInfoValue("FACEBOOK_SIGN_IN_ENABLED", default: false)
        static let vippsSignInFeatureEnabled: Bool = boolInfoValue("VIPPS_SIGN_IN_ENABLED", default: false)
        static let requireSignInForWorkoutStart: Bool = boolInfoValue("REQUIRE_SIGN_IN_FOR_WORKOUT_START", default: false)

        // Show Apple auth only when explicitly enabled in build config.
        // Personal Team default is disabled to avoid capability/signing friction.
        static var appleSignInEnabled: Bool {
            appleSignInFeatureEnabled
        }

        static var emailSignInEnabled: Bool {
            emailSignInFeatureEnabled
        }

        static var googleSignInEnabled: Bool {
            googleSignInFeatureEnabled
                && googleClientID != nil
                && googleRedirectScheme != nil
        }

        /// Google OAuth client ID — supports either GOOGLE_CLIENT_ID or GIDClientID in Info.plist.
        static var googleClientID: String? {
            stringInfoValue("GOOGLE_CLIENT_ID") ?? stringInfoValue("GIDClientID")
        }

        /// Redirect scheme for ASWebAuthenticationSession callback.
        /// Supports GOOGLE_REVERSED_CLIENT_ID or derives from the client ID.
        static var googleRedirectScheme: String? {
            if let explicit = stringInfoValue("GOOGLE_REVERSED_CLIENT_ID") {
                return explicit
            }
            guard let clientID = googleClientID else {
                return nil
            }
            let prefix = clientID.components(separatedBy: ".").first ?? clientID
            return normalizedConfigString("com.googleusercontent.apps.\(prefix)")
        }

        static var facebookSignInEnabled: Bool {
            false
        }

        static var vippsSignInEnabled: Bool {
            false
        }
    }

    // MARK: - Internal Debug Access
    struct Debug {
        private static func stringListInfoValue(_ key: String, default defaultValue: [String] = []) -> [String] {
            guard let raw = Bundle.main.object(forInfoDictionaryKey: key) else {
                return defaultValue
            }
            if let arrayValue = raw as? [String] {
                return arrayValue
            }
            if let stringValue = raw as? String {
                return stringValue
                    .split(separator: ",")
                    .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                    .filter { !$0.isEmpty }
            }
            return defaultValue
        }

        // Launch-safe whitelist for the internal workout diagnostics surface.
        static var workoutDiagnosticsAllowedEmails: Set<String> {
            Set(
                stringListInfoValue(
                    "WORKOUT_DIAGNOSTICS_ALLOWED_EMAILS",
                    default: ["ai.coachi@hotmail.com"]
                )
                .map { $0.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() }
                .filter { !$0.isEmpty }
            )
        }

        static func canAccessWorkoutDiagnostics(email: String?) -> Bool {
            guard let normalizedEmail = email?
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .lowercased(),
                !normalizedEmail.isEmpty else {
                return false
            }
            return workoutDiagnosticsAllowedEmails.contains(normalizedEmail)
        }
    }

    // MARK: - Live Voice Mode
    struct LiveVoice {
        private static func boolInfoValue(_ key: String, default defaultValue: Bool = false) -> Bool {
            guard let raw = Bundle.main.object(forInfoDictionaryKey: key) else {
                return defaultValue
            }
            if let boolValue = raw as? Bool {
                return boolValue
            }
            if let stringValue = raw as? String {
                switch stringValue.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
                case "1", "true", "yes", "on":
                    return true
                case "0", "false", "no", "off":
                    return false
                default:
                    return defaultValue
                }
            }
            return defaultValue
        }

        static let isEnabled: Bool = boolInfoValue("LIVE_COACH_VOICE_ENABLED", default: true)
        static let defaultMaxDurationSeconds: Int = 300
    }

    // MARK: - Workout Talk
    struct WorkoutTalk {
        private static func boolInfoValue(_ key: String, default defaultValue: Bool = false) -> Bool {
            guard let raw = Bundle.main.object(forInfoDictionaryKey: key) else {
                return defaultValue
            }
            if let boolValue = raw as? Bool {
                return boolValue
            }
            if let stringValue = raw as? String {
                switch stringValue.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
                case "1", "true", "yes", "on":
                    return true
                case "0", "false", "no", "off":
                    return false
                default:
                    return defaultValue
                }
            }
            return defaultValue
        }

        static let wakeWordEnabled: Bool = boolInfoValue("WORKOUT_WAKE_WORD_ENABLED", default: false)
    }

    // MARK: - Sharing
    struct Share {
        static let coachiWebsiteURLString = "https://coachi.app"
        static let instagramStoriesScheme = "instagram-stories://share"
        static let snapchatScheme = "snapchat://"
    }

    // MARK: - Continuous Coaching Settings
    struct ContinuousCoaching {
        static let defaultInterval: TimeInterval = 8.0
        static let minInterval: TimeInterval = 5.0
        static let maxInterval: TimeInterval = 15.0
        static let chunkDuration: TimeInterval = 8.0
        static let minChunkBytes: Int = 8000
        static let maxWorkoutDuration: TimeInterval = 45 * 60
        static let autoTimeoutMessage = "Great workout! Remember to tap Stop when done."
        static let iosEventSpeechEnabled = true
    }

    // MARK: - Audio Pack (local-first speech)
    struct AudioPack {
        static let version = "v1"
        // Set to your Cloudflare R2 public URL to enable runtime fetch+cache.
        // Example: https://pub-xxxx.r2.dev
        static let r2PublicURL = "https://pub-b70ecae2812f46e19b80bc39deb1c9a1.r2.dev"
    }

    // MARK: - Health Signals
    struct Health {
        static let hrStaleThresholdSeconds: TimeInterval = 8.0
        static let hrPoorSpikeDeltaBPM: Int = 20
        static let hrPoorSpikeWindowSeconds: TimeInterval = 2.0
    }

    // MARK: - Motion Signals
    struct Motion {
        static let staleThresholdSeconds: TimeInterval = 8.0
    }

    // MARK: - Subscription (Phase 4 Monetization)
    struct Subscription {
        /// Monthly auto-renewing subscription product ID — set this in App Store Connect.
        static let monthlyProductID = "app.coachi.premium.monthly"
        /// Yearly auto-renewing subscription product ID — set this in App Store Connect.
        static let yearlyProductID = "app.coachi.premium.yearly"

        static let allProductIDs: [String] = [monthlyProductID, yearlyProductID]

        /// Free trial duration in days (shown in paywall UI only — StoreKit manages the actual trial).
        static let trialDurationDays = 14

        /// Monthly price shown in paywall before StoreKit price is loaded.
        static let fallbackMonthlyPrice = "$9.99"
        /// Yearly price shown in paywall before StoreKit price is loaded.
        static let fallbackYearlyPrice = "$79"

        // MARK: - Usage Limits (free tier)

        /// Max Talk-to-Coach questions per workout session for free users.
        static let freeTalkQuestionsPerWorkout = 1
        /// Max Talk-to-Coach questions per day for free users.
        static let freeTalkQuestionsPerDay = 3
        /// Max Talk-to-Coach questions per workout session for premium users.
        static let premiumTalkQuestionsPerWorkout = 10
    }

    // MARK: - Experience Progression
    struct Progression {
        static let minWorkoutSecondsForXPAward: Int = 5 * 60
        static let minCoachScoreForXPAward: Int = 50
        static let xpAwardPerQualifiedWorkout: Int = 25
        static let xpPerLevel: Int = CoachiProgressState.xpPerLevel
        static let maxCoachiLevel: Int = CoachiProgressState.maximumLevel
    }
}
