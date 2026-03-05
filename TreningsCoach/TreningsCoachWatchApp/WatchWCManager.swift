import Foundation
import WatchConnectivity

@MainActor
final class WatchWCManager: NSObject, ObservableObject {
    @Published var pendingWorkoutType: String?
    @Published var pendingRequestTimestamp: TimeInterval?
    @Published var showStartScreen: Bool = false

    private var lastHandledStartRequestTs: TimeInterval = 0
    private let requestTTLSeconds: TimeInterval = 120

    var onRemoteStopRequest: (() -> Void)?

    override init() {
        super.init()
        activate()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
    }

    private func parseTimestamp(_ value: Any?) -> TimeInterval {
        if let doubleValue = value as? Double { return doubleValue }
        if let numberValue = value as? NSNumber { return numberValue.doubleValue }
        if let stringValue = value as? String, let parsed = Double(stringValue) { return parsed }
        return Date().timeIntervalSince1970
    }

    private func handleStartRequest(_ payload: [String: Any]) {
        let timestamp = parseTimestamp(payload[WCKeys.timestamp])
        let age = Date().timeIntervalSince1970 - timestamp
        guard age <= requestTTLSeconds else { return }
        guard timestamp > lastHandledStartRequestTs else { return }

        lastHandledStartRequestTs = timestamp
        pendingRequestTimestamp = timestamp
        pendingWorkoutType = WCKeys.WorkoutType.normalized(payload[WCKeys.workoutType] as? String)
        showStartScreen = true
    }

    private func handlePayload(_ payload: [String: Any]) {
        guard let cmd = payload[WCKeys.cmd] as? String else { return }

        switch cmd {
        case WCKeys.Command.requestStartWorkout:
            handleStartRequest(payload)
        case WCKeys.Command.workoutStopped:
            onRemoteStopRequest?()
        default:
            break
        }
    }
}

extension WatchWCManager: WCSessionDelegate {
    nonisolated func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        Task { @MainActor in
            self.handlePayload(message)
        }
    }

    nonisolated func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        Task { @MainActor in
            self.handlePayload(applicationContext)
        }
    }

    nonisolated func session(
        _ session: WCSession,
        activationDidCompleteWith activationState: WCSessionActivationState,
        error: Error?
    ) {
        _ = (session, activationState, error)
    }
}
