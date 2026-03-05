import Foundation

final class HeartRateArbiter {
    struct Output {
        let currentBPM: Int?
        let hrSource: HRSource
        let hrSignalQuality: HRQuality
        let watchConnected: Bool
        let bleConnected: Bool
        let liveHRAvailable: Bool
        let watchStatus: String
        let lastSampleAt: Date?
    }

    var onOutput: ((Output) -> Void)?
    var onLog: ((String) -> Void)?

    private var latestSamples: [HRSource: HeartRateSample] = [:]
    private var providerStates: [HRSource: ProviderStatus] = [
        .wc: .disconnected,
        .ble: .disconnected,
        .hk: .disconnected,
    ]

    private var currentSource: HRSource = .none
    private var lastOutput: Output?
    private var lastNoLiveEventAt: Date?

    private let liveFreshnessSeconds: TimeInterval = 10.0
    private let hkFreshnessSeconds: TimeInterval = 120.0

    private(set) var lastWCHRSampleAt: Date?
    private(set) var lastBLEHRSampleAt: Date?
    private(set) var lastHKSampleAt: Date?

    func ingest(sample: HeartRateSample) {
        latestSamples[sample.source] = sample
        switch sample.source {
        case .wc:
            lastWCHRSampleAt = sample.ts
        case .ble:
            lastBLEHRSampleAt = sample.ts
        case .hk:
            lastHKSampleAt = sample.ts
        case .none:
            break
        }

        if sample.source != .none {
            providerStates[sample.source] = .ready
        }

        evaluate(reason: "sample_\(sample.source.rawValue)")
    }

    func updateStatus(source: HRSource, status: ProviderStatus) {
        guard source != .none else { return }
        providerStates[source] = status

        let stateText = providerStateText(status)
        let reasonText: String
        if case .error(let reason) = status {
            reasonText = reason
        } else {
            reasonText = "state_update"
        }
        onLog?("PROVIDER_STATE provider=\(source.rawValue) state=\(stateText) reason=\(reasonText)")

        evaluate(reason: "status_\(source.rawValue)_\(stateText)")
    }

    func refreshLiveness() {
        evaluate(reason: "liveness_tick")
    }

    private func evaluate(reason: String) {
        let now = Date()

        let wcFresh = isFresh(.wc, at: now)
        let bleFresh = isFresh(.ble, at: now)
        let hkFresh = isFresh(.hk, at: now)

        let selectedSource: HRSource
        if wcFresh {
            selectedSource = .wc
        } else if bleFresh {
            selectedSource = .ble
        } else if hkFresh {
            selectedSource = .hk
        } else {
            selectedSource = .none
        }

        if selectedSource != currentSource {
            let from = currentSource.rawValue
            let to = selectedSource.rawValue
            onLog?("ARBITER_SWITCH from=\(from) to=\(to) reason=\(reason)")
            currentSource = selectedSource
        }

        if selectedSource == .none,
           let lastNoLiveEventAt,
           now.timeIntervalSince(lastNoLiveEventAt) > liveFreshnessSeconds {
            onLog?("HR_STALE source=all age_s=>\(Int(liveFreshnessSeconds))")
            self.lastNoLiveEventAt = now
        } else if selectedSource == .none,
                  lastNoLiveEventAt == nil {
            onLog?("HR_STALE source=all age_s=>\(Int(liveFreshnessSeconds))")
            self.lastNoLiveEventAt = now
        }

        let sample = latestSamples[selectedSource]
        let quality: HRQuality
        switch selectedSource {
        case .wc, .ble:
            quality = .good
        case .hk:
            quality = .degraded
        case .none:
            quality = .none
        }

        let bleState = providerStates[.ble] ?? .disconnected
        let wcState = providerStates[.wc] ?? .disconnected
        let bleConnected = isProviderReady(bleState)
        let watchConnected = isProviderReady(wcState)

        let output = Output(
            currentBPM: sample?.bpm,
            hrSource: selectedSource,
            hrSignalQuality: quality,
            watchConnected: watchConnected,
            bleConnected: bleConnected,
            liveHRAvailable: selectedSource == .wc || selectedSource == .ble,
            watchStatus: watchStatus(for: selectedSource),
            lastSampleAt: sample?.ts
        )

        if shouldEmit(newOutput: output) {
            lastOutput = output
            onOutput?(output)
        }
    }

    private func shouldEmit(newOutput: Output) -> Bool {
        guard let lastOutput else { return true }
        return lastOutput.currentBPM != newOutput.currentBPM ||
            lastOutput.hrSource != newOutput.hrSource ||
            lastOutput.hrSignalQuality != newOutput.hrSignalQuality ||
            lastOutput.watchConnected != newOutput.watchConnected ||
            lastOutput.bleConnected != newOutput.bleConnected ||
            lastOutput.liveHRAvailable != newOutput.liveHRAvailable ||
            lastOutput.watchStatus != newOutput.watchStatus
    }

    private func isFresh(_ source: HRSource, at now: Date) -> Bool {
        guard let sample = latestSamples[source] else { return false }
        let age = max(0, now.timeIntervalSince(sample.ts))
        switch source {
        case .wc, .ble:
            return age < liveFreshnessSeconds
        case .hk:
            return age < hkFreshnessSeconds
        case .none:
            return false
        }
    }

    private func watchStatus(for source: HRSource) -> String {
        switch source {
        case .wc:
            return "wc_connected"
        case .ble:
            return "ble_connected"
        case .hk:
            return "hk_fallback"
        case .none:
            return "no_live_hr"
        }
    }

    private func providerStateText(_ status: ProviderStatus) -> String {
        switch status {
        case .disconnected:
            return "disconnected"
        case .connecting:
            return "connecting"
        case .ready:
            return "ready"
        case .degraded:
            return "degraded"
        case .error:
            return "error"
        }
    }

    private func isProviderReady(_ status: ProviderStatus) -> Bool {
        switch status {
        case .ready:
            return true
        case .connecting, .degraded, .disconnected, .error:
            return false
        }
    }
}
