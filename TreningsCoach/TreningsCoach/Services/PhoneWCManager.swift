import Foundation
import WatchConnectivity

@MainActor
final class PhoneWCManager: NSObject, ObservableObject {
    enum StartRequestOutcome {
        case liveRequestSent
        case deferredAndFallback
        case failed(String)
    }

    enum WatchCapabilityState: String {
        case noWatchSupport
        case watchNotInstalled
        case watchInstalledNotReachable
        case watchReady
    }

    @Published private(set) var isReachable: Bool = false
    @Published private(set) var isPaired: Bool = false
    @Published private(set) var isWatchAppInstalled: Bool = false

    var watchCapabilityState: WatchCapabilityState {
        if !WCSession.isSupported() || !isPaired {
            return .noWatchSupport
        }
        if !isWatchAppInstalled {
            return .watchNotInstalled
        }
        if isReachable {
            return .watchReady
        }
        return .watchInstalledNotReachable
    }

    var canUseWatchTransport: Bool {
        isPaired && isWatchAppInstalled
    }

    var onReachabilityChanged: ((Bool) -> Void)?
    var onSessionStateChanged: ((WatchCapabilityState) -> Void)?
    var onWorkoutStartedAck: ((String, TimeInterval, String) -> Void)?
    var onWorkoutStartFailed: ((String, TimeInterval, String) -> Void)?
    var onWorkoutStopped: ((TimeInterval, String) -> Void)?
    var onHeartRate: ((Double, TimeInterval) -> Void)?
    private var lastCapabilitySnapshot: String?
    private var hasActivatedSession = false

    override init() {
        super.init()
    }

    func activate() {
        guard WCSession.isSupported() else {
            isReachable = false
            isPaired = false
            isWatchAppInstalled = false
            emitCapabilityState(from: .noWatchSupport)
            return
        }
        guard !hasActivatedSession else { return }
        hasActivatedSession = true
        let session = WCSession.default
        session.delegate = self
        session.activate()
    }

    func sendStartRequest(workoutType: String, timestamp: TimeInterval, requestID: String) -> StartRequestOutcome {
        guard WCSession.isSupported() else {
            return .failed("watch_unavailable")
        }

        let session = WCSession.default
        refreshState(from: session)

        guard canUseWatchTransport else {
            return .failed("watch_unavailable")
        }

        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.requestStartWorkout,
            WCKeys.requestId: requestID,
            WCKeys.workoutType: WCKeys.WorkoutType.normalized(workoutType),
            WCKeys.timestamp: timestamp,
        ]

        switch watchCapabilityState {
        case .watchReady:
            session.sendMessage(payload, replyHandler: nil) { error in
                Task { @MainActor in
                    self.onWorkoutStartFailed?(error.localizedDescription, timestamp, requestID)
                }
            }
            return .liveRequestSent
        case .watchInstalledNotReachable:
            do {
                try session.updateApplicationContext(payload)
                return .deferredAndFallback
            } catch {
                return .failed(error.localizedDescription)
            }
        case .noWatchSupport, .watchNotInstalled:
            return .failed("watch_unavailable")
        }
    }

    func sendWorkoutStopped(timestamp: TimeInterval, requestID: String) {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        refreshState(from: session)

        guard canUseWatchTransport else {
            print("WATCH_NOTIFY_SKIPPED reason=watch_unavailable capability=\(watchCapabilityState.rawValue)")
            return
        }

        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.workoutStopped,
            WCKeys.requestId: requestID,
            WCKeys.timestamp: timestamp,
        ]

        if watchCapabilityState == .watchReady {
            session.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }

        try? session.updateApplicationContext(payload)
    }

    private func refreshState(from session: WCSession = .default) {
        isReachable = session.isReachable
        isPaired = session.isPaired
        isWatchAppInstalled = session.isWatchAppInstalled
        onReachabilityChanged?(isReachable)
        emitCapabilityState(from: watchCapabilityState)
    }

    private func emitCapabilityState(from state: WatchCapabilityState) {
        let snapshot = "WATCH_CAPABILITY state=\(state.rawValue) paired=\(isPaired) installed=\(isWatchAppInstalled) reachable=\(isReachable)"
        if lastCapabilitySnapshot != snapshot {
            print(snapshot)
            lastCapabilitySnapshot = snapshot
        }
        onSessionStateChanged?(state)
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
        let requestID = (payload[WCKeys.requestId] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""

        switch cmd {
        case WCKeys.Command.workoutStarted:
            let type = WCKeys.WorkoutType.normalized(payload[WCKeys.workoutType] as? String)
            onWorkoutStartedAck?(type, timestamp, requestID)
        case WCKeys.Command.workoutStartFailed:
            let reason = (payload[WCKeys.error] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
            onWorkoutStartFailed?(reason?.isEmpty == false ? reason! : "workout_start_failed", timestamp, requestID)
        case WCKeys.Command.workoutStopped:
            onWorkoutStopped?(timestamp, requestID)
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
