import SwiftUI
import Combine

@MainActor
class WorkoutViewModel: ObservableObject {
    // MARK: - State
    @Published var workoutState: WorkoutState = .idle
    @Published var currentPhase: WorkoutPhase = .warmup
    @Published var orbState: OrbState = .idle
    @Published var elapsedTime: TimeInterval = 0
    @Published var activePersonality: CoachPersonality = .personalTrainer
    @Published var currentIntensity: IntensityLevel = .calm
    @Published var coachMessage: String = ""
    @Published var showComplete = false

    private var timer: AnyCancellable?
    private let service: CoachServiceProtocol
    private let sessionId = UUID().uuidString

    init(service: CoachServiceProtocol = LiveCoachService()) {
        self.service = service
    }

    // MARK: - Computed

    var elapsedFormatted: String {
        let minutes = Int(elapsedTime) / 60
        let seconds = Int(elapsedTime) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    var phaseProgress: Double {
        elapsedTime / currentPhase.duration
    }

    var totalProgress: Double {
        let warmup = AppConfig.warmupDuration
        let intense = AppConfig.intenseDuration
        let total = warmup + intense + 180 // cooldown 3 min

        switch currentPhase {
        case .warmup:
            return elapsedTime / total
        case .intense:
            return (warmup + elapsedTime) / total
        case .cooldown:
            return (warmup + intense + elapsedTime) / total
        }
    }

    // MARK: - Actions

    func startWorkout() {
        workoutState = .active
        currentPhase = .warmup
        elapsedTime = 0
        orbState = .listening
        coachMessage = ""
        startTimer()
        fetchCoaching()
    }

    func pauseWorkout() {
        workoutState = .paused
        orbState = .paused
        timer?.cancel()
    }

    func resumeWorkout() {
        workoutState = .active
        orbState = .listening
        startTimer()
    }

    func stopWorkout() {
        timer?.cancel()
        workoutState = .complete
        orbState = .idle
        showComplete = true

        Task {
            let record = WorkoutRecord(
                id: UUID(),
                date: Date(),
                durationSeconds: Int(elapsedTime),
                finalPhase: currentPhase.rawValue,
                avgIntensity: currentIntensity.rawValue,
                personaUsed: activePersonality.rawValue
            )
            try? await service.saveWorkout(record)
        }
    }

    func resetWorkout() {
        workoutState = .idle
        currentPhase = .warmup
        elapsedTime = 0
        orbState = .idle
        coachMessage = ""
        showComplete = false
    }

    func selectPersonality(_ persona: CoachPersonality) {
        activePersonality = persona
    }

    // MARK: - Private

    private func startTimer() {
        timer = Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self else { return }
                self.elapsedTime += 1
                self.checkPhaseTransition()
            }
    }

    private func checkPhaseTransition() {
        switch currentPhase {
        case .warmup:
            if elapsedTime >= AppConfig.warmupDuration {
                currentPhase = .intense
                elapsedTime = 0
                currentIntensity = .moderate
            }
        case .intense:
            if elapsedTime >= AppConfig.intenseDuration {
                currentPhase = .cooldown
                elapsedTime = 0
                currentIntensity = .calm
            }
            if elapsedTime > 300 { currentIntensity = .intense }
        case .cooldown:
            if elapsedTime >= 180 {
                stopWorkout()
            }
        }
    }

    private func fetchCoaching() {
        Task {
            while workoutState == .active {
                orbState = .listening
                do {
                    let feedback = try await service.getContinuousCoachFeedback(
                        sessionId: sessionId,
                        phase: currentPhase,
                        elapsedSeconds: Int(elapsedTime)
                    )
                    if workoutState == .active {
                        orbState = .speaking
                        withAnimation(.easeInOut(duration: 0.3)) {
                            coachMessage = feedback.text
                            currentIntensity = feedback.intensity
                        }
                        try await Task.sleep(nanoseconds: 2_000_000_000) // Show message for 2s
                        orbState = .listening
                        withAnimation(.easeInOut(duration: 0.5)) {
                            coachMessage = ""
                        }
                        try await Task.sleep(nanoseconds: UInt64(feedback.waitSeconds * 1_000_000_000))
                    }
                } catch {
                    try? await Task.sleep(nanoseconds: 5_000_000_000) // retry after 5s
                }
            }
        }
    }
}
