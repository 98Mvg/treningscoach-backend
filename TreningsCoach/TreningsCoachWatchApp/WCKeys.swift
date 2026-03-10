import Foundation

enum WCKeys {
    static let cmd = "cmd"
    static let requestId = "request_id"
    static let workoutType = "workout_type"
    static let timestamp = "ts"
    static let heartRate = "hr"
    static let error = "error"
    static let warmupSeconds = "warmup_seconds"
    static let mainSeconds = "main_seconds"
    static let cooldownSeconds = "cooldown_seconds"
    static let intervalRepeats = "interval_repeats"
    static let intervalWorkSeconds = "interval_work_seconds"
    static let intervalRecoverySeconds = "interval_recovery_seconds"
    static let easyRunSessionMode = "easy_run_session_mode"

    enum Command {
        static let requestStartWorkout = "request_start_workout"
        static let workoutStarted = "workout_started"
        static let workoutStartFailed = "workout_start_failed"
        static let workoutStopped = "workout_stopped"
    }

    enum WorkoutType {
        static let easyRun = "easy_run"
        static let intervals = "intervals"

        static func normalized(_ raw: String?) -> String {
            let value = (raw ?? "").trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            switch value {
            case intervals, "interval", "hiit":
                return intervals
            default:
                return easyRun
            }
        }
    }
}
