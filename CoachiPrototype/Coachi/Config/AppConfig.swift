import SwiftUI

enum AppConfig {
    static let appName = "Coachi"
    static let appTagline = "Your AI Workout Coach"
    static let appVersion = "1.0.0"

    // MARK: - Backend (for future integration)
    static let productionURL = "https://treningscoach-backend.onrender.com"
    static let devURL = "http://localhost:5001"

    // MARK: - Workout Timings
    static let warmupDuration: TimeInterval = 120
    static let intenseDuration: TimeInterval = 900
    static let autoTimeoutDuration: TimeInterval = 2700
    static let coachingInterval: TimeInterval = 8
    static let minCoachingInterval: TimeInterval = 5
    static let maxCoachingInterval: TimeInterval = 15

    // MARK: - Animation Durations
    enum Anim {
        static let orbIdlePulse: Double = 1.8
        static let orbListeningPulse: Double = 1.2
        static let orbSpeakingWave: Double = 0.6
        static let waveformIdle: Double = 2.0
        static let waveformActive: Double = 0.4
        static let particleCycle: Double = 8.0

        static let transitionSpring = Animation.spring(response: 0.5, dampingFraction: 0.8)
        static let buttonSpring = Animation.spring(response: 0.3, dampingFraction: 0.7)
        static let cardAppear = Animation.spring(response: 0.6, dampingFraction: 0.75)
    }

    // MARK: - Layout
    enum Layout {
        static let orbSize: CGFloat = 120
        static let ctaButtonSize: CGFloat = 160
        static let timerRingSize: CGFloat = 200
        static let tabBarHeight: CGFloat = 70
        static let cardCornerRadius: CGFloat = 16
    }
}
