import Foundation
import HealthKit
import WatchConnectivity

@MainActor
final class WatchWorkoutManager: NSObject, ObservableObject {
    private let healthStore = HKHealthStore()
    private var workoutSession: HKWorkoutSession?
    private var workoutBuilder: HKLiveWorkoutBuilder?
    private var requestTimestamp: TimeInterval?
    private var requestID: String?
    private var didSendStopForCurrentSession = false

    @Published private(set) var isRunning: Bool = false
    @Published private(set) var currentHR: Double?

    func requestHealthAuthorization() async throws {
        guard HKHealthStore.isHealthDataAvailable(),
              let hrType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return
        }
        try await healthStore.requestAuthorization(toShare: [], read: [hrType])
    }

    func startWorkout(workoutType: String, requestTimestamp: TimeInterval, requestID: String) async {
        self.requestTimestamp = requestTimestamp
        self.requestID = requestID
        didSendStopForCurrentSession = false
        let normalized = WCKeys.WorkoutType.normalized(workoutType)
        let activityType: HKWorkoutActivityType = normalized == WCKeys.WorkoutType.intervals
            ? .highIntensityIntervalTraining
            : .running

        do {
            try await requestHealthAuthorization()
            startWorkoutSession(activityType: activityType, workoutType: normalized)
        } catch {
            sendStartFailed(error: error.localizedDescription)
        }
    }

    func stopWorkout(sendRemoteSignal: Bool = true) {
        workoutSession?.end()
        if sendRemoteSignal {
            sendWorkoutStoppedSignal()
        }
    }

    private func startWorkoutSession(activityType: HKWorkoutActivityType, workoutType: String) {
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = activityType
        configuration.locationType = .outdoor

        do {
            let session = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
            let builder = session.associatedWorkoutBuilder()

            workoutSession = session
            workoutBuilder = builder

            session.delegate = self
            builder.delegate = self
            builder.dataSource = HKLiveWorkoutDataSource(healthStore: healthStore, workoutConfiguration: configuration)

            let startDate = Date()
            session.startActivity(with: startDate)
            builder.beginCollection(withStart: startDate) { [weak self] success, error in
                Task { @MainActor in
                    guard let self else { return }
                    if success {
                        self.isRunning = true
                        self.sendStartedAck(workoutType: workoutType)
                    } else {
                        self.sendStartFailed(error: error?.localizedDescription ?? "begin_collection_failed")
                    }
                }
            }
        } catch {
            sendStartFailed(error: error.localizedDescription)
        }
    }

    private func sendStartedAck(workoutType: String) {
        let ts = requestTimestamp ?? Date().timeIntervalSince1970
        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.workoutStarted,
            WCKeys.requestId: requestID ?? "",
            WCKeys.workoutType: workoutType,
            WCKeys.timestamp: ts,
        ]
        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }
        try? WCSession.default.updateApplicationContext(payload)
    }

    private func sendStartFailed(error: String) {
        let sanitized = error.trimmingCharacters(in: .whitespacesAndNewlines)
        let ts = requestTimestamp ?? Date().timeIntervalSince1970
        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.workoutStartFailed,
            WCKeys.requestId: requestID ?? "",
            WCKeys.error: sanitized.isEmpty ? "workout_start_failed" : sanitized,
            WCKeys.timestamp: ts,
        ]

        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }
        try? WCSession.default.updateApplicationContext(payload)
    }

    private func sendWorkoutStoppedSignal() {
        guard !didSendStopForCurrentSession else { return }
        didSendStopForCurrentSession = true
        let payload: [String: Any] = [
            WCKeys.cmd: WCKeys.Command.workoutStopped,
            WCKeys.requestId: requestID ?? "",
            WCKeys.timestamp: Date().timeIntervalSince1970,
        ]

        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }
        try? WCSession.default.updateApplicationContext(payload)
    }
}

extension WatchWorkoutManager: HKWorkoutSessionDelegate {
    nonisolated func workoutSession(
        _ workoutSession: HKWorkoutSession,
        didChangeTo toState: HKWorkoutSessionState,
        from fromState: HKWorkoutSessionState,
        date: Date
    ) {
        _ = (workoutSession, fromState, date)
        Task { @MainActor in
            self.isRunning = toState == .running
            if toState == .ended {
                self.sendWorkoutStoppedSignal()
            }
        }
    }

    nonisolated func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        _ = workoutSession
        Task { @MainActor in
            self.sendStartFailed(error: error.localizedDescription)
        }
    }
}

extension WatchWorkoutManager: HKLiveWorkoutBuilderDelegate {
    nonisolated func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        guard let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate),
              collectedTypes.contains(hrType),
              let statistics = workoutBuilder.statistics(for: hrType),
              let quantity = statistics.mostRecentQuantity() else {
            return
        }

        let bpm = quantity.doubleValue(for: HKUnit.count().unitDivided(by: HKUnit.minute()))
        Task { @MainActor in
            self.currentHR = bpm
        }

        let payload: [String: Any] = [
            WCKeys.heartRate: bpm,
            WCKeys.timestamp: Date().timeIntervalSince1970,
        ]

        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }
    }

    nonisolated func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {
        _ = workoutBuilder
    }
}
