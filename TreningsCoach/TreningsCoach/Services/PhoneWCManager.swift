import Foundation
import WatchConnectivity

@MainActor
final class PhoneWCManager: NSObject, ObservableObject {
    enum StartRequestOutcome {
        case liveRequestSent
        case deferredAndFallback
        case failed(String)
    }

    @Published private(set) var isReachable: Bool = false
    @Published private(set) var isPaired: Bool = false
    @Published private(set) var isWatchAppInstalled: Bool = false

    var onReachabilityChanged: ((Bool) -> Void)?
    var onWorkoutStartedAck: ((String, TimeInterval) -> Void)?
    var onWorkoutStartFailed: ((String, TimeInterval) -> Void)?
    var onWorkoutStopped: ((TimeInterval) -> Void)?
    var onHeartRate: ((Double, TimeInterval) -> Void)?

    override init() {
        super.init()
        activate()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
        refreshState(from: session)
    }

    func sendStartRequest(workoutType: String, timestamp: TimeInterval) -> StartRequestOutcome {
        guard WCSession.isSupported() else {
            return .failed("watch_connectivity_unsupported")
        }

        let session = WCSession.default
        refreshState(from: session)

        guard session.isPaired, session.isWatchAppInstalled else {
            return .failed("watch_unavailable")
        }

        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.requestStartWorkout,
            WCKeys.workoutType: WCKeys.WorkoutType.normalized(workoutType),
            WCKeys.timestamp: timestamp,
        ]

        if session.isReachable {
            session.sendMessage(payload, replyHandler: nil) { error in
                Task { @MainActor in
                    self.onWorkoutStartFailed?(error.localizedDescription, timestamp)
                }
            }
            return .liveRequestSent
        }

        do {
            try session.updateApplicationContext(payload)
            return .deferredAndFallback
        } catch {
            return .failed(error.localizedDescription)
        }
    }

    func sendWorkoutStopped(timestamp: TimeInterval) {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default

        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.workoutStopped,
            WCKeys.timestamp: timestamp,
        ]

        if session.isReachable {
            session.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }

        try? session.updateApplicationContext(payload)
    }

    private func refreshState(from session: WCSession = .default) {
        isReachable = session.isReachable
        isPaired = session.isPaired
        isWatchAppInstalled = session.isWatchAppInstalled
        onReachabilityChanged?(isReachable)
    }

    private func parseTimestamp(_ value: Any?) -> TimeInterval {
        if let doubleValue = value as? Double { return doubleValue }
        if let numberValue = value as? NSNumber { return numberValue.doubleValue }
        if let stringValue = value as? String, let parsed = Double(stringValue) { return parsed }
        return Date().timeIntervalSince1970
    }

    private func handleIncomingPayload(_ payload: [String: Any]) {
        if let hr = payload[WCKeys.heartRate] as? Double {
            onHeartRate?(hr, parseTimestamp(payload[WCKeys.timestamp]))
            return
        }
        if let hrInt = payload[WCKeys.heartRate] as? Int {
            onHeartRate?(Double(hrInt), parseTimestamp(payload[WCKeys.timestamp]))
            return
        }

        guard let cmd = payload[WCKeys.cmd] as? String else { return }
        let timestamp = parseTimestamp(payload[WCKeys.timestamp])

        switch cmd {
        case WCKeys.Command.workoutStarted:
            let type = WCKeys.WorkoutType.normalized(payload[WCKeys.workoutType] as? String)
            onWorkoutStartedAck?(type, timestamp)
        case WCKeys.Command.workoutStartFailed:
            let reason = (payload[WCKeys.error] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
            onWorkoutStartFailed?(reason?.isEmpty == false ? reason! : "workout_start_failed", timestamp)
        case WCKeys.Command.workoutStopped:
            onWorkoutStopped?(timestamp)
        default:
            break
        }
    }
}

extension PhoneWCManager: WCSessionDelegate {
    nonisolated func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        Task { @MainActor in
            self.handleIncomingPayload(message)
        }
    }

    nonisolated func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        Task { @MainActor in
            self.handleIncomingPayload(applicationContext)
        }
    }

    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        Task { @MainActor in
            self.refreshState(from: session)
        }
    }

    nonisolated func session(
        _ session: WCSession,
        activationDidCompleteWith activationState: WCSessionActivationState,
        error: Error?
    ) {
        Task { @MainActor in
            self.refreshState(from: session)
        }
    }

    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {
        Task { @MainActor in
            self.refreshState(from: session)
        }
    }

    nonisolated func sessionDidDeactivate(_ session: WCSession) {
        Task { @MainActor in
            WCSession.default.activate()
            self.refreshState(from: WCSession.default)
        }
    }
}
