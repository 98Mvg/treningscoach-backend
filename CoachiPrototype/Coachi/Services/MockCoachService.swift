import Foundation

final class MockCoachService: CoachServiceProtocol, @unchecked Sendable {

    // MARK: - Mock Message Banks

    private let welcomeMessages: [String: [String]] = [
        "personal_trainer": [
            "Let's make this count. Ready when you are.",
            "Time to build something great. Let's go.",
            "Good to see you. Let's get moving.",
            "Another day, another chance to get stronger.",
            "I'm here with you. Let's crush it."
        ],
        "toxic_mode": [
            "Oh, you actually showed up. Color me shocked.",
            "Finally. I was about to give up on you.",
            "Let's see if you last longer than five minutes today.",
            "No excuses today. We go hard or go home.",
            "Think you're tough? Prove it."
        ]
    ]

    private let coachingMessages: [String: [String]] = [
        "warmup": [
            "Nice and easy. Let your body wake up.",
            "Good pace. Keep it steady.",
            "Loosen up those muscles.",
            "Find your rhythm.",
            "Breathe deep, warm it up.",
            "Easy does it. Building momentum.",
            "Smooth and controlled.",
            "That's it. Nice warm-up flow."
        ],
        "intense": [
            "Push through this. You've got it.",
            "Strong work. Don't stop now.",
            "Keep that intensity up!",
            "Dig deep. This is where it counts.",
            "You're stronger than you think.",
            "Stay focused. Power through.",
            "That's the fire I want to see!",
            "No letting up. Keep going."
        ],
        "cooldown": [
            "Bring it down slowly. Great session.",
            "Deep breaths. You earned this.",
            "Nice and easy now. Recovery time.",
            "Let your heart rate come down.",
            "Great work today. Be proud.",
            "Slow it down. Stretch it out.",
            "You showed up and delivered.",
            "Breathe. Relax. Well done."
        ]
    ]

    // MARK: - Mock Workout History

    private var workoutHistory: [WorkoutRecord] = {
        let calendar = Calendar.current
        let now = Date()
        return [
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -1, to: now)!, durationSeconds: 1935, finalPhase: "cooldown", avgIntensity: "moderate", personaUsed: "personal_trainer"),
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -2, to: now)!, durationSeconds: 2580, finalPhase: "cooldown", avgIntensity: "intense", personaUsed: "toxic_mode"),
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -4, to: now)!, durationSeconds: 1200, finalPhase: "intense", avgIntensity: "moderate", personaUsed: "personal_trainer"),
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -5, to: now)!, durationSeconds: 2100, finalPhase: "cooldown", avgIntensity: "moderate", personaUsed: "personal_trainer"),
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -7, to: now)!, durationSeconds: 900, finalPhase: "warmup", avgIntensity: "calm", personaUsed: "personal_trainer"),
            WorkoutRecord(id: UUID(), date: calendar.date(byAdding: .day, value: -9, to: now)!, durationSeconds: 1800, finalPhase: "cooldown", avgIntensity: "moderate", personaUsed: "toxic_mode"),
        ]
    }()

    // MARK: - Protocol Methods

    func getWelcomeMessage(language: String, persona: String) async throws -> WelcomeMessage {
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5s
        let messages = welcomeMessages[persona] ?? welcomeMessages["personal_trainer"]!
        let text = messages.randomElement()!
        return WelcomeMessage(text: text, audioURL: nil)
    }

    func getContinuousCoachFeedback(sessionId: String, phase: WorkoutPhase, elapsedSeconds: Int) async throws -> CoachFeedback {
        let delay = UInt64.random(in: 800_000_000...1_500_000_000) // 0.8-1.5s
        try await Task.sleep(nanoseconds: delay)

        let messages = coachingMessages[phase.rawValue] ?? coachingMessages["intense"]!
        let text = messages.randomElement()!

        let intensity: IntensityLevel
        switch phase {
        case .warmup: intensity = .calm
        case .intense: intensity = elapsedSeconds > 600 ? .intense : .moderate
        case .cooldown: intensity = .calm
        }

        return CoachFeedback(
            text: text,
            shouldSpeak: true,
            intensity: intensity,
            phase: phase,
            waitSeconds: Double.random(in: 6...12)
        )
    }

    func talkToCoach(message: String, sessionId: String, context: String) async throws -> CoachReply {
        let delay = UInt64.random(in: 1_000_000_000...2_000_000_000) // 1-2s
        try await Task.sleep(nanoseconds: delay)

        let replies = [
            "I hear you. Keep pushing, you're doing great.",
            "Focus on your breathing. In through the nose, out through the mouth.",
            "You've got this. Stay in the zone.",
            "That's the spirit. Channel that energy.",
            "Good question. Just trust the process and keep moving."
        ]

        return CoachReply(
            text: replies.randomElement()!,
            audioURL: nil,
            personality: "personal_trainer"
        )
    }

    func saveWorkout(_ record: WorkoutRecord) async throws {
        try await Task.sleep(nanoseconds: 300_000_000) // 0.3s
        workoutHistory.insert(record, at: 0)
    }

    func getWorkoutHistory() async throws -> [WorkoutRecord] {
        try await Task.sleep(nanoseconds: 200_000_000) // 0.2s
        return workoutHistory
    }

    func checkHealth() async throws -> ServiceHealth {
        ServiceHealth(isHealthy: true, activeBrain: "mock", version: AppConfig.appVersion)
    }
}
