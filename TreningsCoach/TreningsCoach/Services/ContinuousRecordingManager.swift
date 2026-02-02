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
    private var recordingStartTime: Date?

    // Circular buffer for storing recent audio (15 seconds)
    private var audioBuffer: [[Float]] = []
    private let bufferCapacity: TimeInterval = 15.0
    private var currentFormat: AVAudioFormat?

    // Audio settings
    private let sampleRate: Double = 44100.0
    private let channels: AVAudioChannelCount = 1

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
        try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetoothA2DP])
        try audioSession.setActive(true)

        // Get input node
        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        currentFormat = format

        print("📱 Audio format: \(format.sampleRate)Hz, \(format.channelCount) channels")

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
        recordingStartTime = nil

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

        // Calculate how many samples we need
        let samplesToExtract = Int(duration * format.sampleRate)
        let totalSamplesInBuffer = audioBuffer.reduce(0) { $0 + $1.count }

        guard totalSamplesInBuffer > 0 else {
            print("⚠️ Cannot get chunk: buffer empty")
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

    /// Get current recording duration
    func getRecordingDuration() -> TimeInterval {
        guard let startTime = recordingStartTime else { return 0 }
        return Date().timeIntervalSince(startTime)
    }

    /// Check if currently recording
    func isCurrentlyRecording() -> Bool {
        return isRecording
    }

    // MARK: - Private Methods

    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData else { return }

        let channelCount = Int(buffer.format.channelCount)
        let frameLength = Int(buffer.frameLength)

        // Convert to Float array (mono - take first channel)
        var samples: [Float] = []
        samples.reserveCapacity(frameLength)

        for frame in 0..<frameLength {
            samples.append(channelData[0][frame])
        }

        // Add to circular buffer
        audioBuffer.append(samples)

        // Maintain buffer capacity (keep only last 15 seconds)
        if let format = currentFormat {
            let maxSamples = Int(bufferCapacity * format.sampleRate)
            let currentSamples = audioBuffer.reduce(0) { $0 + $1.count }

            // Remove old chunks if exceeding capacity
            while currentSamples > maxSamples && !audioBuffer.isEmpty {
                audioBuffer.removeFirst()
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
            let sample = max(-1.0, min(1.0, samples[i]))
            channelData[0][i] = Int16(sample * 32767.0)
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
