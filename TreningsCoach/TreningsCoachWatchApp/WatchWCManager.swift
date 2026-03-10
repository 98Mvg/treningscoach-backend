import Foundation
import HealthKit
import WatchConnectivity

struct WatchSessionPlanSnapshot: Equatable {
    let warmupSeconds: Int
    let mainSeconds: Int
    let cooldownSeconds: Int
    let intervalRepeats: Int?
    let intervalWorkSeconds: Int?
    let intervalRecoverySeconds: Int?
    let easyRunSessionMode: String

    init?(payload: [String: Any]) {
        let warmupSeconds = max(0, Self.parseInt(payload[WCKeys.warmupSeconds]) ?? 0)
        let mainSeconds = max(0, Self.parseInt(payload[WCKeys.mainSeconds]) ?? 0)
        let cooldownSeconds = max(0, Self.parseInt(payload[WCKeys.cooldownSeconds]) ?? 0)
        let easyRunSessionMode = (payload[WCKeys.easyRunSessionMode] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased() ?? ""

        let hasTimingData = warmupSeconds > 0 || mainSeconds > 0 || cooldownSeconds > 0 || easyRunSessionMode == "free_run"
        guard hasTimingData else { return nil }

        self.warmupSeconds = warmupSeconds
        self.mainSeconds = mainSeconds
        self.cooldownSeconds = cooldownSeconds
        self.intervalRepeats = Self.parseInt(payload[WCKeys.intervalRepeats])
        self.intervalWorkSeconds = Self.parseInt(payload[WCKeys.intervalWorkSeconds])
        self.intervalRecoverySeconds = Self.parseInt(payload[WCKeys.intervalRecoverySeconds])
        self.easyRunSessionMode = easyRunSessionMode
    }

    var isFreeRun: Bool {
        easyRunSessionMode == "free_run"
    }

    var totalDurationSeconds: Int? {
        guard !isFreeRun else { return nil }
        let total = warmupSeconds + mainSeconds + cooldownSeconds
        return total > 0 ? total : nil
    }

    private static func parseInt(_ value: Any?) -> Int? {
        if let intValue = value as? Int { return intValue }
        if let numberValue = value as? NSNumber { return numberValue.intValue }
        if let stringValue = value as? String, let parsed = Int(stringValue) { return parsed }
        return nil
    }
}

@MainActor
final class WatchWCManager: NSObject, ObservableObject {
    static let shared = WatchWCManager()

    @Published var pendingWorkoutType: String?
    @Published var pendingRequestId: String?
    @Published var pendingRequestTimestamp: TimeInterval?
    @Published var pendingSessionPlan: WatchSessionPlanSnapshot?
    @Published var showStartScreen: Bool = false

    private var handledRequestIDs: [String: TimeInterval] = [:]
    private let requestTTLSeconds: TimeInterval = 120

    var onRemoteStopRequest: ((String) -> Void)?

    override init() {
        super.init()
        activate()
    }

    func activate() {
        guard WCSession.isSupported() else { return }
        let session = WCSession.default
        session.delegate = self
        session.activate()
        applyPendingApplicationContextIfNeeded(from: session)
    }

    func primePendingStartFromSystemLaunch(workoutConfiguration: HKWorkoutConfiguration) {
        pendingWorkoutType = Self.normalizedWorkoutType(from: workoutConfiguration)
        showStartScreen = true
    }

    private func parseTimestamp(_ value: Any?) -> TimeInterval {
        if let doubleValue = value as? Double { return doubleValue }
        if let numberValue = value as? NSNumber { return numberValue.doubleValue }
        if let stringValue = value as? String, let parsed = Double(stringValue) { return parsed }
        return Date().timeIntervalSince1970
    }

    private func handleStartRequest(_ payload: [String: Any]) {
        let requestID = (payload[WCKeys.requestId] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !requestID.isEmpty else { return }

        let timestamp = parseTimestamp(payload[WCKeys.timestamp])
        let age = Date().timeIntervalSince1970 - timestamp
        guard age <= requestTTLSeconds else { return }
        if let previousTimestamp = handledRequestIDs[requestID], timestamp <= previousTimestamp {
            return
        }

        handledRequestIDs = handledRequestIDs.filter { Date().timeIntervalSince1970 - $0.value <= requestTTLSeconds }
        handledRequestIDs[requestID] = timestamp
        pendingRequestId = requestID
        pendingRequestTimestamp = timestamp
        pendingWorkoutType = WCKeys.WorkoutType.normalized(payload[WCKeys.workoutType] as? String)
        pendingSessionPlan = WatchSessionPlanSnapshot(payload: payload)
        showStartScreen = true
    }

    private func handlePayload(_ payload: [String: Any]) {
        guard let cmd = payload[WCKeys.cmd] as? String else { return }

        switch cmd {
        case WCKeys.Command.requestStartWorkout:
            handleStartRequest(payload)
        case WCKeys.Command.workoutStopped:
            let requestID = (payload[WCKeys.requestId] as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            if !requestID.isEmpty, requestID == pendingRequestId {
                pendingRequestId = nil
                pendingRequestTimestamp = nil
                pendingWorkoutType = nil
                pendingSessionPlan = nil
                showStartScreen = false
            }
            onRemoteStopRequest?(requestID)
        default:
            break
        }
    }

    private func applyPendingApplicationContextIfNeeded(from session: WCSession) {
        let applicationContext = session.receivedApplicationContext
        guard !applicationContext.isEmpty else { return }
        handlePayload(applicationContext)
    }

    private static func normalizedWorkoutType(from workoutConfiguration: HKWorkoutConfiguration) -> String {
        switch workoutConfiguration.activityType {
        case .highIntensityIntervalTraining:
            return WCKeys.WorkoutType.intervals
        default:
            return WCKeys.WorkoutType.easyRun
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
        _ = (activationState, error)
        Task { @MainActor in
            self.applyPendingApplicationContextIfNeeded(from: session)
        }
    }
}
