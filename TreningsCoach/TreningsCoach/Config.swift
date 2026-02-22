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

    // MARK: - Continuous Coaching Settings
    struct ContinuousCoaching {
        static let defaultInterval: TimeInterval = 8.0
        static let minInterval: TimeInterval = 5.0
        static let maxInterval: TimeInterval = 15.0
        static let chunkDuration: TimeInterval = 8.0
        static let minChunkBytes: Int = 8000
        static let maxWorkoutDuration: TimeInterval = 45 * 60
        static let autoTimeoutMessage = "Great workout! Remember to tap Stop when done."
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

    // MARK: - Experience Progression
    struct Progression {
        // A workout counts as "good quality" only if both duration and CoachScore pass.
        static let minWorkoutSecondsForProgression: Int = 12 * 60
        static let goodCoachScoreThreshold: Int = 80

        // Level-up thresholds based on good-quality workouts.
        static let intermediateAtGoodWorkouts: Int = 4
        static let advancedAtGoodWorkouts: Int = 12
    }
}
