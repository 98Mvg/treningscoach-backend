import Foundation
import HealthKit
import WatchConnectivity

@MainActor
final class PhoneWCManager: NSObject, ObservableObject {
    static let shared = PhoneWCManager()
    enum StartRequestOutcome {
        case liveRequestSent
        case deferredAwaitingReachability
        case failed(String)
    }

    enum WatchLaunchOutcome: Equatable {
        case launched
        case skipped(String)
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
    private let healthStore = HKHealthStore()

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
    var onDistance: ((Double) -> Void)?
    private var lastCapabilitySnapshot: String?
    private var hasActivatedSession = false

    private override init() {
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

    func sendStartRequest(
        workoutType: String,
        timestamp: TimeInterval,
        requestID: String,
        context: [String: Any] = [:]
    ) -> StartRequestOutcome {
        guard WCSession.isSupported() else {
            return .failed("watch_unavailable")
        }

        let session = WCSession.default
        refreshState(from: session)

        guard canUseWatchTransport else {
            return .failed("watch_unavailable")
        }

        var payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.requestStartWorkout,
            WCKeys.requestId: requestID,
            WCKeys.workoutType: WCKeys.WorkoutType.normalized(workoutType),
            WCKeys.timestamp: timestamp,
        ]
        context.forEach { payload[$0.key] = $0.value }

        switch watchCapabilityState {
        case .watchReady:
            do {
                try session.updateApplicationContext(payload)
            } catch {
                return .failed(error.localizedDescription)
            }
            session.sendMessage(payload, replyHandler: nil) { error in
                Task { @MainActor in
                    print(
                        "WATCH_START_TRANSPORT_DEGRADED request_id=\(requestID) transport=message error=\(error.localizedDescription)"
                    )
                }
            }
            return .liveRequestSent
        case .watchInstalledNotReachable:
            do {
                try session.updateApplicationContext(payload)
                return .deferredAwaitingReachability
            } catch {
                return .failed(error.localizedDescription)
            }
        case .noWatchSupport, .watchNotInstalled:
            return .failed("watch_unavailable")
        }
    }

    func retryDeferredStartRequest(
        workoutType: String,
        timestamp: TimeInterval,
        requestID: String,
        context: [String: Any] = [:]
    ) -> Bool {
        guard WCSession.isSupported() else { return false }

        let session = WCSession.default
        refreshState(from: session)

        guard watchCapabilityState == .watchReady else { return false }

        var payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.requestStartWorkout,
            WCKeys.requestId: requestID,
            WCKeys.workoutType: WCKeys.WorkoutType.normalized(workoutType),
            WCKeys.timestamp: timestamp,
        ]
        context.forEach { payload[$0.key] = $0.value }

        print("WATCH_START_RETRY_TRANSPORT request_id=\(requestID) transport=message")
        session.sendMessage(payload, replyHandler: nil) { error in
            Task { @MainActor in
                print("WATCH_START_RETRY_FAILED request_id=\(requestID) error=\(error.localizedDescription)")
            }
        }
        return true
    }

    func launchWatchAppForWorkout(workoutType: String) async -> WatchLaunchOutcome {
        refreshState(from: .default)

        guard canUseWatchTransport else {
            return .skipped("watch_unavailable")
        }
        guard HKHealthStore.isHealthDataAvailable() else {
            return .failed("healthkit_unavailable")
        }

        let normalizedWorkoutType = WCKeys.WorkoutType.normalized(workoutType)
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = normalizedWorkoutType == WCKeys.WorkoutType.intervals
            ? .highIntensityIntervalTraining
            : .running
        configuration.locationType = .outdoor

        do {
            try await healthStore.startWatchApp(toHandle: configuration)
            return .launched
        } catch {
            let reason = error.localizedDescription.trimmingCharacters(in: .whitespacesAndNewlines)
            return .failed(reason.isEmpty ? "watch_launch_failed" : reason)
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

    func refreshStateManually() {
        guard WCSession.isSupported() else { return }
        refreshState(from: WCSession.default)
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

    private func handleIncomingPayload(_ payload: [String: Any], transport: String) {
        if let hr = payload[WCKeys.heartRate] as? Double {
            print("WATCH_HR_RECEIVED transport=\(transport) bpm=\(Int(round(hr)))")
            onHeartRate?(hr, parseTimestamp(payload[WCKeys.timestamp]))
            return
        }
        if let hrInt = payload[WCKeys.heartRate] as? Int {
            print("WATCH_HR_RECEIVED transport=\(transport) bpm=\(hrInt)")
            onHeartRate?(Double(hrInt), parseTimestamp(payload[WCKeys.timestamp]))
            return
        }

        if let dist = payload[WCKeys.distanceMeters] as? Double {
            print("WATCH_DIST_RECEIVED transport=\(transport) meters=\(Int(dist))")
            onDistance?(dist)
            return
        }

        guard let cmd = payload[WCKeys.cmd] as? String else { return }
        print("WATCH_CMD_RECEIVED transport=\(transport) cmd=\(cmd)")
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
            self.handleIncomingPayload(message, transport: "message")
        }
    }

    nonisolated func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        Task { @MainActor in
            self.handleIncomingPayload(applicationContext, transport: "applicationContext")
        }
    }

    nonisolated func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any]) {
        Task { @MainActor in
            self.handleIncomingPayload(userInfo, transport: "userInfo")
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

    nonisolated func sessionWatchStateDidChange(_ session: WCSession) {
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
