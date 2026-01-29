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
    static let version = "1.0.0"

    // MARK: - Backend
    static let productionURL = "https://treningscoach-backend.onrender.com"
    static let localURL = "http://localhost:5001"

    // Use production by default, change to localURL for local testing
    static let backendURL = productionURL

    // MARK: - Phase Timings (seconds)
    static let warmupDuration: TimeInterval = 120  // 2 minutes
    static let intenseDuration: TimeInterval = 900  // 15 minutes
    // After intenseDuration = cooldown

    // MARK: - UI Colors
    struct Colors {
        static let idle = Color.blue
        static let listening = Color.green
        static let speaking = Color.red

        static let idleGradient = [
            Color(red: 0.0, green: 0.48, blue: 1.0),
            Color(red: 0.0, green: 0.32, blue: 0.84)
        ]

        static let listeningGradient = [
            Color(red: 0.20, green: 0.78, blue: 0.35),
            Color(red: 0.14, green: 0.54, blue: 0.24)
        ]

        static let speakingGradient = [
            Color(red: 1.0, green: 0.23, blue: 0.19),
            Color(red: 0.78, green: 0.17, blue: 0.14)
        ]

        static let backgroundGradient = [Color.white, Color(.systemGray6)]
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
