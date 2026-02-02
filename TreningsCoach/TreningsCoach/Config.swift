//
//  Config.swift
//  TreningsCoach
//
//  Central configuration for easy customization
//

import Foundation
import SwiftUI

// MARK: - App Configuration

struct AppConfig {
    // MARK: - App Info
    static let appName = "Treningscoach"
    static let version = "2.0.0"

    // MARK: - Backend
    static let productionURL = "https://treningscoach-backend.onrender.com"
    static let localURL = "http://localhost:10000"

    // Use LOCAL for voice cloning testing
    static let backendURL = localURL

    // MARK: - Phase Timings (seconds)
    static let warmupDuration: TimeInterval = 120  // 2 minutes
    static let intenseDuration: TimeInterval = 900  // 15 minutes
    // After intenseDuration = cooldown

    // MARK: - UI Colors (Dark Purple/Blue Theme)
    struct Colors {
        static let idle = AppTheme.primaryAccent
        static let listening = AppTheme.success
        static let speaking = AppTheme.danger

        static let idleGradient = [
            Color(hex: "7C3AED"),
            Color(hex: "6D28D9")
        ]

        static let listeningGradient = [
            Color(hex: "10B981"),
            Color(hex: "059669")
        ]

        static let speakingGradient = [
            Color(hex: "EF4444"),
            Color(hex: "DC2626")
        ]

        static let backgroundGradient = [AppTheme.background, AppTheme.backgroundDeep]
    }

    // MARK: - UI Text
    struct Text {
        static let phaseWarmup = "Warm-up"
        static let phaseIntense = "Hard Coach"
        static let phaseCooldown = "Cool-down"
    }

    // MARK: - Animation Durations
    struct Animation {
        static let pulseDuration: Double = 1.5
        static let waveDuration: Double = 0.8
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

    // MARK: - Continuous Coaching Settings
    struct ContinuousCoaching {
        static let defaultInterval: TimeInterval = 8.0
        static let minInterval: TimeInterval = 5.0  // STEP 2: kritisk = 5s (urgent)
        static let maxInterval: TimeInterval = 15.0
        static let chunkDuration: TimeInterval = 8.0  // Audio sample window (6-10s)
        static let maxWorkoutDuration: TimeInterval = 45 * 60  // 45 min auto-timeout
        static let autoTimeoutMessage = "Great workout! Remember to tap Stop when done."
    }
}
