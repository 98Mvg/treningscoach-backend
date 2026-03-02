import Foundation

protocol CoachServiceProtocol: Sendable {
    func getWelcomeMessage(language: String, persona: String) async throws -> WelcomeMessage
    func getContinuousCoachFeedback(sessionId: String, phase: WorkoutPhase, elapsedSeconds: Int) async throws -> CoachFeedback
    func talkToCoach(message: String, sessionId: String, context: String) async throws -> CoachReply
    func saveWorkout(_ record: WorkoutRecord) async throws
    func getWorkoutHistory() async throws -> [WorkoutRecord]
    func checkHealth() async throws -> ServiceHealth
}
