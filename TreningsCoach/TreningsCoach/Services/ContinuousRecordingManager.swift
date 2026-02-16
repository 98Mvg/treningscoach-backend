//
//  ContinuousRecordingManager.swift
//  TreningsCoach
//
//  Manages continuous audio recording with non-destructive chunk sampling
//  for real-time breath analysis during workouts.
//

import Foundation
import AVFoundation
import AVFAudio

class ContinuousRecordingManager: NSObject {

    // MARK: - Properties

    private let audioEngine = AVAudioEngine()
    private var audioFile: AVAudioFile?
    private var isRecording = false
    private var isPaused = false
    private var recordingStartTime: Date?
    private var pausedDuration: TimeInterval = 0
    private var pauseStartTime: Date?

    // Thread-safe access to the circular buffer
    private let bufferQueue = DispatchQueue(label: "com.treningscoach.audiobuffer", qos: .userInteractive)
    private var audioBuffer: [[Float]] = []
    private let bufferCapacity: TimeInterval = 15.0
    private var currentFormat: AVAudioFormat?

    // Diagnostics: count tap callbacks to verify the tap is firing
    private var tapCallbackCount: Int = 0
    private var hasInstalledTap = false

    // Wake word: callback to feed audio buffers to speech recognizer
    var onAudioBuffer: ((AVAudioPCMBuffer) -> Void)?

    /// Expose audio engine for wake word manager
    var engine: AVAudioEngine { audioEngine }

    // MARK: - Public Methods

    /// Start continuous recording session
    func startContinuousRecording() throws {
        try startContinuousRecording(retryCount: 1)
    }

    // MARK: - Internal Start Logic

    /// Internal start helper with bounded retry for transient CoreAudio startup failures.
    private func startContinuousRecording(retryCount: Int) throws {
        guard !isRecording else {
            print("⚠️ Already recording")
            return
        }

        // Defensive cleanup in case a previous start attempt failed mid-way.
        teardownAudioPipeline()

        // Configure audio session for BOTH recording AND playback
        // .playAndRecord allows coach voice to play while mic stays active
        let audioSession = AVAudioSession.sharedInstance()

        // Ensure microphone permission is granted
        if #available(iOS 17.0, *) {
            switch AVAudioApplication.shared.recordPermission {
            case .granted:
                break
            case .denied:
                throw RecordingError.noPermission
            case .undetermined:
                AVAudioApplication.requestRecordPermission { _ in }
                throw RecordingError.noPermission
            @unknown default:
                throw RecordingError.noPermission
            }
        } else {
            switch audioSession.recordPermission {
            case .granted:
                break
            case .denied:
                throw RecordingError.noPermission
            case .undetermined:
                audioSession.requestRecordPermission { _ in }
                throw RecordingError.noPermission
            @unknown default:
                throw RecordingError.noPermission
            }
        }

        // IMPORTANT: Deactivate first to allow category change
        // This prevents error -10875 (kAudioSessionIncompatibleCategory)
        do {
            try audioSession.setActive(false)
        } catch {
            print("⚠️ Could not deactivate audio session (may already be inactive): \(error)")
        }

        // Now set the category and reactivate
        try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetoothA2DP, .mixWithOthers])
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

        // Get input node
        let inputNode = audioEngine.inputNode

        // Read the hardware format for validation only
        let hwFormat = inputNode.outputFormat(forBus: 0)
        if hwFormat.channelCount == 0 || hwFormat.sampleRate == 0 {
            throw RecordingError.recordingFailed
        }

        print("📱 Hardware format: \(hwFormat.sampleRate)Hz, \(hwFormat.channelCount) channels, interleaved=\(hwFormat.isInterleaved), commonFormat=\(hwFormat.commonFormat.rawValue)")

        // Reset tap callback counter
        tapCallbackCount = 0

        // Install tap with nil format — lets the system use the native hardware format.
        // Passing an explicit format can crash with "format mismatch" when the audio
        // session's hardware sample rate differs from the inputNode's cached format.
        inputNode.installTap(onBus: 0, bufferSize: 4096, format: nil) { [weak self] buffer, time in
            guard let self = self else { return }

            // Capture the actual format from the first buffer callback
            self.bufferQueue.sync {
                if self.currentFormat == nil {
                    let fmt = buffer.format
                    self.currentFormat = fmt
                    print("📱 Tap format (actual): \(fmt.sampleRate)Hz, \(fmt.channelCount)ch, interleaved=\(fmt.isInterleaved), commonFormat=\(fmt.commonFormat.rawValue)")
                    Task { @MainActor in
                        AudioPipelineDiagnostics.shared.sampleRate = fmt.sampleRate
                        AudioPipelineDiagnostics.shared.log(.micInit, detail: "\(fmt.sampleRate)Hz, \(fmt.channelCount)ch, interleaved=\(fmt.isInterleaved)")
                    }
                }
            }

            self.tapCallbackCount += 1
            if self.tapCallbackCount <= 3 || self.tapCallbackCount % 500 == 0 {
                print("🎙️ Tap callback #\(self.tapCallbackCount): frames=\(buffer.frameLength), format=\(buffer.format.commonFormat.rawValue)")
            }

            self.processAudioBuffer(buffer)
            // Forward to wake word speech recognizer
            self.onAudioBuffer?(buffer)
        }
        hasInstalledTap = true

        // Start engine. If this fails, ensure tap/session are cleaned up so retry won't crash.
        do {
            try audioEngine.start()
        } catch {
            print("⚠️ Failed to start audio engine: \(error)")
            teardownAudioPipeline()
            if retryCount > 0 {
                // Small backoff helps recover from transient "AUIOClient_StartIO failed (nope)".
                Thread.sleep(forTimeInterval: 0.15)
                print("🔁 Retrying continuous recording start (\(retryCount) retries left)")
                try startContinuousRecording(retryCount: retryCount - 1)
                return
            }
            throw error
        }

        isRecording = true
        recordingStartTime = Date()

        print("✅ Continuous recording started")
    }

    /// Pause continuous recording
    func pauseRecording() {
        guard isRecording && !isPaused else { return }

        isPaused = true
        pauseStartTime = Date()

        // Stop the engine but keep tap + buffer for resume.
        if audioEngine.isRunning {
            audioEngine.stop()
        }

        print("⏸️ Recording paused")
    }

    /// Resume continuous recording
    func resumeRecording() throws {
        guard isRecording && isPaused else { return }

        // Update total paused duration
        if let pauseStart = pauseStartTime {
            pausedDuration += Date().timeIntervalSince(pauseStart)
        }
        pauseStartTime = nil
        isPaused = false

        // Restart the engine
        try audioEngine.start()

        print("▶️ Recording resumed")
    }

    /// Stop continuous recording session
    func stopContinuousRecording() {
        guard isRecording else { return }
        teardownAudioPipeline()

        isRecording = false
        isPaused = false
        recordingStartTime = nil
        pausedDuration = 0
        pauseStartTime = nil
        currentFormat = nil
        tapCallbackCount = 0
        hasInstalledTap = false

        // Deactivate audio session
        do {
            try AVAudioSession.sharedInstance().setActive(false)
        } catch {
            print("⚠️ Could not deactivate audio session: \(error)")
        }

        print("⏹️ Continuous recording stopped")
    }

    /// Get latest audio chunk (6-10 seconds) without stopping recording
    func getLatestChunk(duration: TimeInterval = 8.0) -> URL? {
        guard isRecording else {
            print("⚠️ Cannot get chunk: not recording")
            return nil
        }

        guard let format = currentFormat else {
            print("⚠️ Cannot get chunk: no audio format (tap callbacks: \(tapCallbackCount))")
            return nil
        }

        // Thread-safe read of the buffer
        var snapshot: [[Float]] = []
        bufferQueue.sync {
            snapshot = audioBuffer
        }

        let totalSamplesInBuffer = snapshot.reduce(0) { $0 + $1.count }
        let denom = format.sampleRate > 1.0 ? format.sampleRate : 1.0
        let bufferedSeconds = Double(totalSamplesInBuffer) / denom

        guard totalSamplesInBuffer > 0 else {
            print("⚠️ Cannot get chunk: buffer empty (tap callbacks: \(tapCallbackCount), chunks: \(snapshot.count))")
            return nil
        }

        // Avoid exporting tiny files if we don't have enough audio yet
        if bufferedSeconds < 1.0 {
            print("⚠️ Cannot get chunk: only \(String(format: "%.2f", bufferedSeconds))s buffered")
            return nil
        }

        // Extract last N seconds from snapshot
        let chunk = extractLastSeconds(duration: duration, from: snapshot, format: format)

        guard !chunk.isEmpty else {
            print("⚠️ Cannot get chunk: extraction failed")
            return nil
        }

        // Export as WAV file
        return exportChunkAsWAV(chunk, format: format)
    }

    /// Get current recording duration (excluding paused time)
    func getRecordingDuration() -> TimeInterval {
        guard let startTime = recordingStartTime else { return 0 }
        let totalElapsed = Date().timeIntervalSince(startTime)
        var pausedTime = pausedDuration

        // Add current pause duration if currently paused
        if isPaused, let pauseStart = pauseStartTime {
            pausedTime += Date().timeIntervalSince(pauseStart)
        }

        return totalElapsed - pausedTime
    }

    /// Check if currently recording
    func isCurrentlyRecording() -> Bool {
        return isRecording
    }

    // MARK: - Private Methods

    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        let frameLength = Int(buffer.frameLength)
        guard frameLength > 0 else { return }

        var samples: [Float] = []
        samples.reserveCapacity(frameLength)
        var sumSquares: Float = 0.0

        // Prefer floatChannelData first — this is the standard iOS mic format
        // (non-interleaved Float32). Only fall back to interleaved/int16 if needed.
        if let channelData = buffer.floatChannelData {
            let channelPtr = channelData[0]
            for i in 0..<frameLength {
                let sample = channelPtr[i]
                samples.append(sample)
                sumSquares += sample * sample
            }
        } else if let int16Data = buffer.int16ChannelData {
            let scale = 1.0 / Float(Int16.max)
            let channelPtr = int16Data[0]
            for i in 0..<frameLength {
                let sample = Float(channelPtr[i]) * scale
                samples.append(sample)
                sumSquares += sample * sample
            }
        } else {
            // Fallback: try reading from audioBufferList directly
            let format = buffer.format
            let abl = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: buffer.audioBufferList))
            guard let mData = abl.first?.mData else {
                print("⚠️ processAudioBuffer: no accessible data (format: \(format.commonFormat.rawValue), interleaved: \(format.isInterleaved))")
                return
            }

            switch format.commonFormat {
            case .pcmFormatFloat32:
                let ptr = mData.assumingMemoryBound(to: Float.self)
                let channelCount = max(Int(format.channelCount), 1)
                for i in 0..<frameLength {
                    let sample = ptr[i * channelCount]
                    samples.append(sample)
                    sumSquares += sample * sample
                }
            case .pcmFormatInt16:
                let ptr = mData.assumingMemoryBound(to: Int16.self)
                let scale = 1.0 / Float(Int16.max)
                let channelCount = max(Int(format.channelCount), 1)
                for i in 0..<frameLength {
                    let sample = Float(ptr[i * channelCount]) * scale
                    samples.append(sample)
                    sumSquares += sample * sample
                }
            default:
                print("⚠️ processAudioBuffer: unsupported format \(format.commonFormat.rawValue)")
                return
            }
        }

        guard !samples.isEmpty else { return }

        // Feed raw audio samples to pipeline diagnostics (real-time level + VAD)
        let rms = sqrtf(sumSquares / Float(frameLength))
        let db = 20.0 * log10f(Swift.max(rms, Float(1e-10)))
        let voiceDetected = rms > 0.025

        Task { @MainActor in
            AudioPipelineDiagnostics.shared.updateFromAudio(
                rms: rms,
                db: db,
                voiceDetected: voiceDetected,
                frameCount: frameLength
            )
        }

        // Add to circular buffer (thread-safe)
        bufferQueue.sync {
            audioBuffer.append(samples)

            // Maintain buffer capacity (keep only last 15 seconds)
            if let format = currentFormat {
                let maxSamples = Int(bufferCapacity * format.sampleRate)
                var currentSamples = audioBuffer.reduce(0) { $0 + $1.count }

                // Remove old chunks if exceeding capacity
                while currentSamples > maxSamples && !audioBuffer.isEmpty {
                    let removed = audioBuffer.removeFirst()
                    currentSamples -= removed.count
                }
            }
        }
    }

    private func extractLastSeconds(duration: TimeInterval, from buffer: [[Float]], format: AVAudioFormat) -> [Float] {
        let samplesToExtract = Int(duration * format.sampleRate)
        let totalSamples = buffer.reduce(0) { $0 + $1.count }

        // If we have less than requested, return everything
        let actualSamples = min(samplesToExtract, totalSamples)

        // Flatten buffer and take last N samples
        let flatBuffer = buffer.flatMap { $0 }

        guard actualSamples <= flatBuffer.count else {
            return flatBuffer
        }

        let startIndex = flatBuffer.count - actualSamples
        return Array(flatBuffer[startIndex..<flatBuffer.count])
    }

    private func exportChunkAsWAV(_ samples: [Float], format: AVAudioFormat) -> URL? {
        // Create temporary file URL
        let tempDir = FileManager.default.temporaryDirectory
        let filename = "chunk_\(Date().timeIntervalSince1970).wav"
        let fileURL = tempDir.appendingPathComponent(filename)

        let sampleRate = format.sampleRate
        let channels: AVAudioChannelCount = 1

        // Use an explicit Float32 PCM format. On some devices, AVAudioFile's
        // processingFormat does not expose int16ChannelData, which caused chunk export
        // to fail and the coaching loop to stall after welcome.
        guard let exportFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: sampleRate,
            channels: channels,
            interleaved: false
        ) else {
            print("⚠️ Could not create export format")
            return nil
        }

        guard let audioFile = try? AVAudioFile(
            forWriting: fileURL,
            settings: exportFormat.settings
        ) else {
            print("⚠️ Could not create audio file")
            return nil
        }

        // Create buffer for writing
        let frameCount = AVAudioFrameCount(samples.count)
        guard let buffer = AVAudioPCMBuffer(pcmFormat: exportFormat, frameCapacity: frameCount) else {
            print("⚠️ Could not create PCM buffer")
            return nil
        }

        buffer.frameLength = frameCount

        // Copy samples to buffer (prefer float data; fallback to int16 if needed)
        if let floatData = buffer.floatChannelData {
            for i in 0..<samples.count {
                floatData[0][i] = Swift.max(Float(-1.0), Swift.min(Float(1.0), samples[i]))
            }
        } else if let int16Data = buffer.int16ChannelData {
            for i in 0..<samples.count {
                let sample = Swift.max(Float(-1.0), Swift.min(Float(1.0), samples[i]))
                int16Data[0][i] = Int16(sample * Float(32767.0))
            }
        } else {
            print("⚠️ Could not access channel data")
            return nil
        }

        // Write to file
        do {
            try audioFile.write(from: buffer)
            print("✅ Exported chunk: \(samples.count) samples (\(Double(samples.count) / sampleRate)s)")
            return fileURL
        } catch {
            print("⚠️ Could not write audio file: \(error)")
            return nil
        }
    }

    private func teardownAudioPipeline() {
        if audioEngine.isRunning {
            audioEngine.stop()
        }

        if hasInstalledTap {
            audioEngine.inputNode.removeTap(onBus: 0)
            hasInstalledTap = false
        }

        bufferQueue.sync {
            audioBuffer.removeAll()
        }

        currentFormat = nil
        tapCallbackCount = 0

        do {
            try AVAudioSession.sharedInstance().setActive(false)
        } catch {
            print("⚠️ Could not deactivate audio session: \(error)")
        }
    }
}
