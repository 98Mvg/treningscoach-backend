import Foundation

final class AppleWatchWCProvider: HeartRateProvider {
    let source: HRSource = .wc

    var onSample: ((HeartRateSample) -> Void)?
    var onStatus: ((ProviderStatus) -> Void)?

    private var isStarted = false
    private var isReachable = false
    private var isPaired = false
    private var isInstalled = false

    func start() {
        isStarted = true
        emitConnectivityStatus()
    }

    func stop() {
        isStarted = false
        onStatus?(.disconnected)
    }

    func updateSessionState(reachable: Bool, paired: Bool, installed: Bool) {
        isReachable = reachable
        isPaired = paired
        isInstalled = installed
        emitConnectivityStatus()
    }

    func ingestHeartRate(bpm: Double, timestamp: TimeInterval) {
        guard isStarted else { return }
        let rounded = Int(round(bpm))
        guard rounded > 0 else { return }

        let sample = HeartRateSample(
            bpm: rounded,
            ts: Date(timeIntervalSince1970: timestamp),
            source: .wc,
            quality: .good
        )
        onSample?(sample)
    }

    private func emitConnectivityStatus() {
        guard isStarted else { return }
        guard isPaired, isInstalled else {
            onStatus?(.disconnected)
            return
        }
        onStatus?(isReachable ? .ready : .degraded)
    }
}
