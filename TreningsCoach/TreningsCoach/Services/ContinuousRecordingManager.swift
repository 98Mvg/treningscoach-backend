//
//  ContinuousRecordingManager.swift
//  TreningsCoach
//
//  Manages continuous audio recording with non-destructive chunk sampling
//  for real-time breath analysis during workouts.
//

import Foundation
import AVFoundation

class ContinuousRecordingManager: NSObject {

    // MARK: - Properties

    private let audioEngine = AVAudioEngine()
    private var audioFile: AVAudioFile?
    private var isRecording = false
    private var isPaused = false
    private var recordingStartTime: Date?
    private var pausedDuration: TimeInterval = 0
    private var pauseStartTime: Date?

    // Circular buffer for storing recent audio (15 seconds)
    private var audioBuffer: [[Float]] = []
    private let bufferCapacity: TimeInterval = 15.0
    private var currentFormat: AVAudioFormat?

    // Wake word: callback to feed audio buffers to speech recognizer
    var onAudioBuffer: ((AVAudioPCMBuffer) -> Void)?

    /// Expose audio engine for wake word manager
    var engine: AVAudioEngine { audioEngine }

    // MARK: - Public Methods

    /// Start continuous recording session
    func startContinuousRecording() throws {
        guard !isRecording else {
            print("⚠️ Already recording")
            return
        }

        // Configure audio session for BOTH recording AND playback
        // .playAndRecord allows coach voice to play while mic stays active
        let audioSession = AVAudioSession.sharedInstance()

        // Ensure microphone permission is granted
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
        let format = inputNode.outputFormat(forBus: 0)
        if format.channelCount == 0 || format.sampleRate == 0 {
            throw RecordingError.recordingFailed
        }
        currentFormat = format

        print("📱 Audio format: \(format.sampleRate)Hz, \(format.channelCount) channels, interleaved=\(format.isInterleaved)")

        // Feed sample rate to diagnostics
        Task { @MainActor in
            AudioPipelineDiagnostics.shared.sampleRate = format.sampleRate
            AudioPipelineDiagnostics.shared.log(.micInit, detail: "\(format.sampleRate)Hz, \(format.channelCount)ch, interleaved=\(format.isInterleaved)")
        }

        // Install tap to capture audio continuously
        // Buffers are used for both breath analysis (circular buffer) and wake word detection
        inputNode.installTap(onBus: 0, bufferSize: 4096, format: format) { [weak self] buffer, time in
            self?.processAudioBuffer(buffer)
            // Forward to wake word speech recognizer
            self?.onAudioBuffer?(buffer)
        }

        // Start engine
        try audioEngine.start()

        isRecording = true
        recordingStartTime = Date()

        print("✅ Continuous recording started")
    }

    /// Pause continuous recording
    func pauseRecording() {
        guard isRecording && !isPaused else { return }

        isPaused = true
        pauseStartTime = Date()

        // Stop the engine but keep the buffer
        audioEngine.stop()

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

        // Remove tap
        audioEngine.inputNode.removeTap(onBus: 0)

        // Stop engine
        audioEngine.stop()

        // Clear buffer
        audioBuffer.removeAll()

        isRecording = false
        isPaused = false
        recordingStartTime = nil
        pausedDuration = 0
        pauseStartTime = nil

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
            print("⚠️ Cannot get chunk: no audio format")
            return nil
        }

        let totalSamplesInBuffer = audioBuffer.reduce(0) { $0 + $1.count }
        let denom = format.sampleRate > 1.0 ? format.sampleRate : 1.0
        let bufferedSeconds = Double(totalSamplesInBuffer) / denom

        guard totalSamplesInBuffer > 0 else {
            print("⚠️ Cannot get chunk: buffer empty")
            return nil
        }

        // Avoid exporting tiny files if we don't have enough audio yet
        if bufferedSeconds < 1.0 {
            print("⚠️ Cannot get chunk: only \(String(format: "%.2f", bufferedSeconds))s buffered")
            return nil
        }

        // Extract last N seconds from buffer
        let chunk = extractLastSeconds(duration: duration, format: format)

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

        let format = buffer.format
        let channelCount = Int(format.channelCount)

        if format.isInterleaved {
            let abl = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: buffer.audioBufferList))
            guard let mData = abl.first?.mData else { return }

            switch format.commonFormat {
            case .pcmFormatFloat32:
                let ptr = mData.assumingMemoryBound(to: Float.self)
                for i in 0..<frameLength {
                    let sample = ptr[i * max(channelCount, 1)]
                    samples.append(sample)
                    sumSquares += sample * sample
                }
            case .pcmFormatInt16:
                let ptr = mData.assumingMemoryBound(to: Int16.self)
                let scale = 1.0 / Float(Int16.max)
                for i in 0..<frameLength {
                    let sample = Float(ptr[i * max(channelCount, 1)]) * scale
                    samples.append(sample)
                    sumSquares += sample * sample
                }
            default:
                return
            }
        } else if let channelData = buffer.floatChannelData {
            for i in 0..<frameLength {
                let sample = channelData[0][i]
                samples.append(sample)
                sumSquares += sample * sample
            }
        } else if let int16Data = buffer.int16ChannelData {
            let scale = 1.0 / Float(Int16.max)
            for i in 0..<frameLength {
                let sample = Float(int16Data[0][i]) * scale
                samples.append(sample)
                sumSquares += sample * sample
            }
        } else {
            return
        }

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

        // Add to circular buffer
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

    private func extractLastSeconds(duration: TimeInterval, format: AVAudioFormat) -> [Float] {
        let samplesToExtract = Int(duration * format.sampleRate)
        let totalSamples = audioBuffer.reduce(0) { $0 + $1.count }

        // If we have less than requested, return everything
        let actualSamples = min(samplesToExtract, totalSamples)

        // Flatten buffer and take last N samples
        let flatBuffer = audioBuffer.flatMap { $0 }

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

        // Create audio file
        guard let audioFile = try? AVAudioFile(
            forWriting: fileURL,
            settings: [
                AVFormatIDKey: kAudioFormatLinearPCM,
                AVSampleRateKey: sampleRate,
                AVNumberOfChannelsKey: channels,
                AVLinearPCMBitDepthKey: 16,
                AVLinearPCMIsFloatKey: false,
                AVLinearPCMIsBigEndianKey: false
            ]
        ) else {
            print("⚠️ Could not create audio file")
            return nil
        }

        // Create buffer for writing
        let frameCount = AVAudioFrameCount(samples.count)
        guard let buffer = AVAudioPCMBuffer(pcmFormat: audioFile.processingFormat, frameCapacity: frameCount) else {
            print("⚠️ Could not create PCM buffer")
            return nil
        }

        buffer.frameLength = frameCount

        // Copy samples to buffer (convert Float to Int16)
        guard let channelData = buffer.int16ChannelData else {
            print("⚠️ Could not access channel data")
            return nil
        }

        for i in 0..<samples.count {
            // Convert Float (-1.0 to 1.0) to Int16 (-32768 to 32767)
            let sample = Swift.max(Float(-1.0), Swift.min(Float(1.0), samples[i]))
            channelData[0][i] = Int16(sample * Float(32767.0))
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
}
