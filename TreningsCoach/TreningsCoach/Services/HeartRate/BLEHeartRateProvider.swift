import CoreBluetooth
import Foundation

final class BLEHeartRateProvider: NSObject, HeartRateProvider {
    let source: HRSource = .ble

    var onSample: ((HeartRateSample) -> Void)?
    var onStatus: ((ProviderStatus) -> Void)?

    private let hrServiceUUID = CBUUID(string: "180D")
    private let hrMeasurementUUID = CBUUID(string: "2A37")

    private let favoriteDeviceUUIDKey = "ble_favorite_device_uuid"
    private let favoriteDeviceNameKey = "ble_favorite_device_name"
    private let scanTimeoutSeconds: TimeInterval = 12.0
    private let reconnectBaseDelaySeconds: TimeInterval = 1.5
    private let maxReconnectBackoffSeconds: TimeInterval = 12.0

    private var central: CBCentralManager?
    private var connectedPeripheral: CBPeripheral?
    private var hrMeasurementCharacteristic: CBCharacteristic?
    private var shouldReconnect = false
    private var isStarted = false
    private var reconnectAttempt = 0
    private var reconnectWorkItem: DispatchWorkItem?
    private var scanTimeoutWorkItem: DispatchWorkItem?
    private var isScanningForHeartRate = false

    func start() {
        isStarted = true
        shouldReconnect = true
        reconnectAttempt = 0
        cancelReconnectWorkItem()
        ensureCentralManager()
        onStatus?(.connecting)

        if central?.state == .poweredOn {
            connectFavoriteOrScan()
        }
    }

    func stop() {
        isStarted = false
        shouldReconnect = false
        reconnectAttempt = 0
        cancelReconnectWorkItem()
        cancelScanTimeoutWorkItem()

        if let peripheral = connectedPeripheral {
            central?.cancelPeripheralConnection(peripheral)
        }

        if central?.isScanning == true {
            central?.stopScan()
        }
        isScanningForHeartRate = false

        connectedPeripheral = nil
        hrMeasurementCharacteristic = nil
        onStatus?(.disconnected)
    }

    private func ensureCentralManager() {
        guard central == nil else { return }
        central = CBCentralManager(delegate: self, queue: nil)
    }

    private func connectFavoriteOrScan() {
        guard isStarted, let central else { return }

        if let favorite = favoritePeripheralUUID(),
           let peripheral = central.retrievePeripherals(withIdentifiers: [favorite]).first {
            onStatus?(.connecting)
            central.connect(peripheral, options: nil)
            return
        }

        startScanning()
    }

    private func startScanning() {
        guard isStarted, let central, central.state == .poweredOn else { return }
        if central.isScanning {
            central.stopScan()
        }
        isScanningForHeartRate = true
        onStatus?(.connecting)
        central.scanForPeripherals(withServices: [hrServiceUUID], options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
        scheduleScanTimeout()
    }

    private func favoritePeripheralUUID() -> UUID? {
        guard let raw = UserDefaults.standard.string(forKey: favoriteDeviceUUIDKey) else {
            return nil
        }
        return UUID(uuidString: raw)
    }

    private func persistFavorite(peripheral: CBPeripheral) {
        UserDefaults.standard.set(peripheral.identifier.uuidString, forKey: favoriteDeviceUUIDKey)
        UserDefaults.standard.set(peripheral.name ?? "BLE HR Sensor", forKey: favoriteDeviceNameKey)
    }

    private func reconnectWithBackoff() {
        guard shouldReconnect, isStarted else { return }
        cancelReconnectWorkItem()
        reconnectAttempt += 1
        let delay = min(
            maxReconnectBackoffSeconds,
            reconnectBaseDelaySeconds * pow(2.0, Double(max(0, reconnectAttempt - 1)))
        )

        let workItem = DispatchWorkItem { [weak self] in
            guard let self, self.shouldReconnect, self.isStarted else { return }
            self.connectFavoriteOrScan()
        }
        reconnectWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + delay, execute: workItem)
    }

    private func scheduleScanTimeout() {
        cancelScanTimeoutWorkItem()
        let workItem = DispatchWorkItem { [weak self] in
            guard let self,
                  self.isStarted,
                  self.connectedPeripheral == nil,
                  self.isScanningForHeartRate else {
                return
            }

            self.central?.stopScan()
            self.isScanningForHeartRate = false
            self.onStatus?(.degraded)
            self.reconnectWithBackoff()
        }
        scanTimeoutWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + scanTimeoutSeconds, execute: workItem)
    }

    private func cancelReconnectWorkItem() {
        reconnectWorkItem?.cancel()
        reconnectWorkItem = nil
    }

    private func cancelScanTimeoutWorkItem() {
        scanTimeoutWorkItem?.cancel()
        scanTimeoutWorkItem = nil
    }

    private func parseHeartRateBPM(from data: Data) -> Int? {
        guard data.count >= 2 else { return nil }
        let flags = data[data.startIndex]
        let isUInt16 = (flags & 0x01) != 0

        if isUInt16 {
            guard data.count >= 3 else { return nil }
            let lsb = UInt16(data[data.startIndex.advanced(by: 1)])
            let msb = UInt16(data[data.startIndex.advanced(by: 2)])
            let bpm = Int((msb << 8) | lsb)
            return bpm > 0 ? bpm : nil
        }

        let bpm = Int(data[data.startIndex.advanced(by: 1)])
        return bpm > 0 ? bpm : nil
    }
}

extension BLEHeartRateProvider: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        guard isStarted else { return }

        switch central.state {
        case .poweredOn:
            connectFavoriteOrScan()
        case .poweredOff:
            cancelScanTimeoutWorkItem()
            cancelReconnectWorkItem()
            isScanningForHeartRate = false
            onStatus?(.degraded)
        case .unauthorized:
            onStatus?(.error(reason: "bluetooth_unauthorized"))
        case .unsupported:
            onStatus?(.error(reason: "bluetooth_unsupported"))
        case .resetting, .unknown:
            onStatus?(.connecting)
        @unknown default:
            onStatus?(.error(reason: "bluetooth_unknown_state"))
        }
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData _: [String: Any],
        rssi _: NSNumber
    ) {
        guard isStarted else { return }

        if let connectedPeripheral, connectedPeripheral.identifier == peripheral.identifier {
            return
        }

        central.stopScan()
        isScanningForHeartRate = false
        cancelScanTimeoutWorkItem()
        onStatus?(.connecting)
        central.connect(peripheral, options: nil)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        guard isStarted else { return }

        connectedPeripheral = peripheral
        hrMeasurementCharacteristic = nil
        reconnectAttempt = 0
        cancelReconnectWorkItem()
        cancelScanTimeoutWorkItem()
        isScanningForHeartRate = false

        persistFavorite(peripheral: peripheral)
        onStatus?(.connecting)

        peripheral.delegate = self
        peripheral.discoverServices([hrServiceUUID])

        if central.isScanning {
            central.stopScan()
        }
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        _ = (central, peripheral)
        cancelScanTimeoutWorkItem()
        isScanningForHeartRate = false
        onStatus?(.error(reason: error?.localizedDescription ?? "ble_connect_failed"))
        reconnectWithBackoff()
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        _ = central
        guard isStarted else { return }

        if connectedPeripheral?.identifier == peripheral.identifier {
            connectedPeripheral = nil
            hrMeasurementCharacteristic = nil
        }
        cancelScanTimeoutWorkItem()
        isScanningForHeartRate = false

        if let error {
            onStatus?(.error(reason: error.localizedDescription))
        } else {
            onStatus?(.degraded)
        }

        reconnectWithBackoff()
    }
}

extension BLEHeartRateProvider: CBPeripheralDelegate {
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard error == nil else {
            onStatus?(.error(reason: error?.localizedDescription ?? "ble_discover_services_failed"))
            reconnectWithBackoff()
            return
        }

        guard let services = peripheral.services else {
            onStatus?(.degraded)
            reconnectWithBackoff()
            return
        }

        for service in services where service.uuid == hrServiceUUID {
            peripheral.discoverCharacteristics([hrMeasurementUUID], for: service)
        }
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        guard error == nil else {
            onStatus?(.error(reason: error?.localizedDescription ?? "ble_discover_characteristics_failed"))
            reconnectWithBackoff()
            return
        }

        guard let characteristics = service.characteristics else {
            onStatus?(.degraded)
            reconnectWithBackoff()
            return
        }

        for characteristic in characteristics where characteristic.uuid == hrMeasurementUUID {
            hrMeasurementCharacteristic = characteristic
            peripheral.setNotifyValue(true, for: characteristic)
        }
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didUpdateNotificationStateFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        _ = peripheral
        guard characteristic.uuid == hrMeasurementUUID else { return }

        if let error {
            onStatus?(.error(reason: error.localizedDescription))
            reconnectWithBackoff()
            return
        }

        onStatus?(.ready)
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        _ = peripheral
        guard characteristic.uuid == hrMeasurementUUID else { return }

        if let error {
            onStatus?(.error(reason: error.localizedDescription))
            reconnectWithBackoff()
            return
        }

        guard let data = characteristic.value,
              let bpm = parseHeartRateBPM(from: data) else {
            return
        }

        let sample = HeartRateSample(
            bpm: bpm,
            ts: Date(),
            source: .ble,
            quality: .good
        )
        onSample?(sample)
        onStatus?(.ready)
    }
}
