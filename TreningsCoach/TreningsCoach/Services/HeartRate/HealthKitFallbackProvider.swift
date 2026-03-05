import Foundation
import HealthKit

final class HealthKitFallbackProvider: HeartRateProvider {
    let source: HRSource = .hk

    var onSample: ((HeartRateSample) -> Void)?
    var onStatus: ((ProviderStatus) -> Void)?

    private let healthStore = HKHealthStore()
    private var observerQuery: HKObserverQuery?
    private var anchoredQuery: HKAnchoredObjectQuery?
    private var queryAnchor: HKQueryAnchor?
    private var isStarted = false

    private var heartRateType: HKQuantityType? {
        HKObjectType.quantityType(forIdentifier: .heartRate)
    }

    private var restingHeartRateType: HKQuantityType? {
        HKObjectType.quantityType(forIdentifier: .restingHeartRate)
    }

    func requestAuthorization() async -> Bool {
        guard HKHealthStore.isHealthDataAvailable(),
              let heartRateType,
              let restingHeartRateType else {
            return false
        }

        let readTypes: Set<HKObjectType> = [heartRateType, restingHeartRateType]
        return await withCheckedContinuation { continuation in
            healthStore.requestAuthorization(toShare: nil, read: readTypes) { success, _ in
                continuation.resume(returning: success)
            }
        }
    }

    func fetchLatestHeartRateSnapshot() async -> HeartRateSample? {
        guard let heartRateType else { return nil }
        return await withCheckedContinuation { continuation in
            let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
            let query = HKSampleQuery(
                sampleType: heartRateType,
                predicate: nil,
                limit: 1,
                sortDescriptors: [sort]
            ) { _, samples, _ in
                guard let sample = (samples as? [HKQuantitySample])?.first,
                      let mapped = Self.makeSample(from: sample) else {
                    continuation.resume(returning: nil)
                    return
                }
                continuation.resume(returning: mapped)
            }
            self.healthStore.execute(query)
        }
    }

    func fetchLatestRestingHeartRate() async -> Int? {
        guard let restingHeartRateType else { return nil }
        return await withCheckedContinuation { continuation in
            let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
            let query = HKSampleQuery(
                sampleType: restingHeartRateType,
                predicate: nil,
                limit: 1,
                sortDescriptors: [sort]
            ) { _, samples, _ in
                guard let sample = (samples as? [HKQuantitySample])?.first else {
                    continuation.resume(returning: nil)
                    return
                }
                let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
                let bpm = Int(round(sample.quantity.doubleValue(for: unit)))
                continuation.resume(returning: bpm > 0 ? bpm : nil)
            }
            self.healthStore.execute(query)
        }
    }

    func start() {
        guard !isStarted else { return }
        isStarted = true

        Task { [weak self] in
            guard let self else { return }
            self.onStatus?(.connecting)

            let authorized = await self.requestAuthorization()
            guard authorized else {
                self.onStatus?(.error(reason: "healthkit_auth_denied"))
                return
            }

            self.startQueries()
        }
    }

    func stop() {
        isStarted = false
        if let observerQuery {
            healthStore.stop(observerQuery)
        }
        if let anchoredQuery {
            healthStore.stop(anchoredQuery)
        }
        observerQuery = nil
        anchoredQuery = nil
        queryAnchor = nil
        onStatus?(.disconnected)
    }

    private func startQueries() {
        guard let heartRateType else {
            onStatus?(.error(reason: "healthkit_hr_type_missing"))
            return
        }

        observerQuery = HKObserverQuery(sampleType: heartRateType, predicate: nil) { [weak self] _, completionHandler, _ in
            self?.runAnchoredHeartRateQuery()
            completionHandler()
        }

        if let observerQuery {
            healthStore.execute(observerQuery)
        }

        runAnchoredHeartRateQuery()
        onStatus?(.ready)
    }

    private func runAnchoredHeartRateQuery() {
        guard let heartRateType else { return }

        anchoredQuery = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: nil,
            anchor: queryAnchor,
            limit: HKObjectQueryNoLimit
        ) { [weak self] _, addedSamples, _, newAnchor, _ in
            guard let self else { return }
            self.queryAnchor = newAnchor
            self.emit(samples: addedSamples)
        }

        anchoredQuery?.updateHandler = { [weak self] _, addedSamples, _, newAnchor, _ in
            guard let self else { return }
            self.queryAnchor = newAnchor
            self.emit(samples: addedSamples)
        }

        if let anchoredQuery {
            healthStore.execute(anchoredQuery)
        }
    }

    private func emit(samples: [HKSample]?) {
        let quantitySamples = (samples as? [HKQuantitySample] ?? []).sorted { $0.endDate < $1.endDate }
        if quantitySamples.isEmpty {
            return
        }

        for sample in quantitySamples {
            if let mapped = Self.makeSample(from: sample) {
                onSample?(mapped)
            }
        }
        onStatus?(.ready)
    }

    private static func makeSample(from sample: HKQuantitySample) -> HeartRateSample? {
        let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
        let bpm = Int(round(sample.quantity.doubleValue(for: unit)))
        guard bpm > 0 else { return nil }

        return HeartRateSample(
            bpm: bpm,
            ts: sample.endDate,
            source: .hk,
            quality: .degraded
        )
    }
}
