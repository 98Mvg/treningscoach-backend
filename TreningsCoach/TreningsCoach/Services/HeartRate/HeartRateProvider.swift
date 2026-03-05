import Foundation

enum HRSource: String {
    case wc
    case ble
    case hk
    case none
}

enum HRQuality: String {
    case good
    case degraded
    case none
}

enum ProviderStatus: Equatable {
    case disconnected
    case connecting
    case ready
    case degraded
    case error(reason: String)
}

struct HeartRateSample: Equatable {
    let bpm: Int
    let ts: Date
    let source: HRSource
    let quality: HRQuality
}

protocol HeartRateProvider: AnyObject {
    var source: HRSource { get }
    var onSample: ((HeartRateSample) -> Void)? { get set }
    var onStatus: ((ProviderStatus) -> Void)? { get set }

    func start()
    func stop()
}
