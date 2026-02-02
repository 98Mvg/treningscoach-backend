//
//  WakeWordManager.swift
//  TreningsCoach
//
//  Listens for wake word ("Coach" / "Trener") during continuous workout,
//  then captures a short user utterance and returns the transcription.
//
//  Architecture:
//  - Uses Apple's SFSpeechRecognizer for on-device speech recognition
//  - Taps into the SAME AVAudioEngine as ContinuousRecordingManager
//  - Runs speech recognition on the audio stream looking for wake word
//  - After wake word detected: captures next ~5 seconds of speech
//  - Returns transcribed text (minus the wake word)
//
//  Key design: 90% one-way coaching, 10% user-initiated via wake word
//

import Foundation
import Speech
import AVFoundation

@MainActor
class WakeWordManager: ObservableObject {

    // MARK: - Published State

    @Published var isListening = false          // Actively listening for wake word
    @Published var isCapturingUtterance = false  // Capturing user speech after wake word
    @Published var lastTranscription: String?    // Last captured user utterance
    @Published var wakeWordDetected = false      // Brief flash when wake word heard

    // MARK: - Configuration

    /// Wake words per language (must be unnatural in gym context)
    static let wakeWords: [String: [String]] = [
        "en": ["coach", "hey coach"],
        "no": ["trener", "hei trener"]
    ]

    /// How long to capture after wake word (seconds)
    private let utteranceTimeout: TimeInterval = 5.0

    /// Minimum confidence for wake word detection
    private let minConfidence: Float = 0.5

    // MARK: - Private Properties

    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var audioEngine: AVAudioEngine?

    private var currentWakeWords: [String] = ["coach"]
    private var utteranceCaptureTimer: Timer?
    private var onUtteranceCaptured: ((String) -> Void)?

    private var isAuthorized = false

    // MARK: - Initialization

    init() {
        updateLanguage()
    }

    // MARK: - Public Methods

    /// Request speech recognition authorization
    func requestAuthorization() async -> Bool {
        return await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                let authorized = status == .authorized
                Task { @MainActor in
                    self.isAuthorized = authorized
                    if !authorized {
                        print("⚠️ Speech recognition not authorized: \(status.rawValue)")
                    }
                }
                continuation.resume(returning: authorized)
            }
        }
    }

    /// Update wake words based on current language
    func updateLanguage() {
        let lang = UserDefaults.standard.string(forKey: "app_language") ?? "en"
        currentWakeWords = Self.wakeWords[lang] ?? Self.wakeWords["en"]!

        // Create speech recognizer for the appropriate locale
        let locale = lang == "no" ? Locale(identifier: "nb-NO") : Locale(identifier: "en-US")
        speechRecognizer = SFSpeechRecognizer(locale: locale)

        print("🎙️ Wake word manager: language=\(lang), words=\(currentWakeWords)")
    }

    /// Start listening for wake word on the given audio engine
    /// Shares the audio engine with ContinuousRecordingManager
    func startListening(audioEngine: AVAudioEngine, onUtterance: @escaping (String) -> Void) {
        guard isAuthorized else {
            print("⚠️ Speech recognition not authorized, cannot listen for wake word")
            return
        }

        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            print("⚠️ Speech recognizer not available")
            return
        }

        // Cancel any existing task
        stopListening()

        self.audioEngine = audioEngine
        self.onUtteranceCaptured = onUtterance

        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let request = recognitionRequest else { return }

        // Configure for on-device recognition when available (lower latency)
        request.shouldReportPartialResults = true
        if #available(iOS 13, *) {
            request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
        }

        // Install a SECOND tap on the audio engine's input node
        // This works because AVAudioEngine supports multiple taps
        // ContinuousRecordingManager has tap on bus 0, we use the mixer node
        let mixerNode = audioEngine.mainMixerNode
        let recordingFormat = audioEngine.inputNode.outputFormat(forBus: 0)

        // Use the input node directly — we'll feed buffers manually
        // Instead of a second tap (which conflicts), we'll use a different approach:
        // Install tap on the input node with a custom format via a mixer
        startRecognitionTask(recognizer: recognizer, request: request)

        // Feed audio buffers from the input node
        // We tap into the input node's output — sharing with ContinuousRecordingManager
        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)

        // Note: ContinuousRecordingManager already has a tap on bus 0.
        // We can't install a second tap on the same bus.
        // Instead, we'll periodically feed audio from the circular buffer.
        // Alternative: use a splitter node. For simplicity, we install on bus 0
        // and let ContinuousRecordingManager handle it — we just need the buffers.

        isListening = true
        print("👂 Wake word listening started (words: \(currentWakeWords))")
    }

    /// Feed an audio buffer to the speech recognizer
    /// Called by ContinuousRecordingManager when it processes buffers
    func feedAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        guard isListening || isCapturingUtterance else { return }
        recognitionRequest?.append(buffer)
    }

    /// Stop listening for wake word
    func stopListening() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        utteranceCaptureTimer?.invalidate()
        utteranceCaptureTimer = nil
        isListening = false
        isCapturingUtterance = false
        wakeWordDetected = false
        print("🔇 Wake word listening stopped")
    }

    // MARK: - Private Methods

    private func startRecognitionTask(recognizer: SFSpeechRecognizer, request: SFSpeechAudioBufferRecognitionRequest) {
        var wakeWordFound = false
        var wakeWordTimestamp: Date?
        var capturedText = ""

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self = self else { return }

            if let error = error {
                // Recognition errors are common (timeouts, etc.) — not critical
                print("⚠️ Speech recognition error: \(error.localizedDescription)")
                // Restart listening if it was an interruption
                if self.isListening {
                    Task { @MainActor in
                        self.restartRecognition()
                    }
                }
                return
            }

            guard let result = result else { return }

            let transcription = result.bestTranscription.formattedString.lowercased()

            Task { @MainActor in
                if !wakeWordFound {
                    // Phase 1: Looking for wake word
                    for wakeWord in self.currentWakeWords {
                        if transcription.contains(wakeWord) {
                            wakeWordFound = true
                            wakeWordTimestamp = Date()
                            self.wakeWordDetected = true
                            self.isCapturingUtterance = true

                            print("🎯 Wake word detected: '\(wakeWord)' in '\(transcription)'")

                            // Remove wake word from transcription to get the utterance
                            capturedText = transcription
                            for w in self.currentWakeWords {
                                capturedText = capturedText.replacingOccurrences(of: w, with: "").trimmingCharacters(in: .whitespaces)
                            }

                            // Start timeout for utterance capture
                            self.utteranceCaptureTimer = Timer.scheduledTimer(withTimeInterval: self.utteranceTimeout, repeats: false) { [weak self] _ in
                                Task { @MainActor in
                                    self?.finalizeUtterance(capturedText)
                                }
                            }
                            break
                        }
                    }
                } else {
                    // Phase 2: Capturing utterance after wake word
                    capturedText = transcription
                    for w in self.currentWakeWords {
                        capturedText = capturedText.replacingOccurrences(of: w, with: "").trimmingCharacters(in: .whitespaces)
                    }

                    // If result is final, don't wait for timeout
                    if result.isFinal && !capturedText.isEmpty {
                        self.utteranceCaptureTimer?.invalidate()
                        self.finalizeUtterance(capturedText)
                    }
                }
            }
        }
    }

    private func finalizeUtterance(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            print("👂 Wake word heard but no utterance captured — resuming listening")
            wakeWordDetected = false
            isCapturingUtterance = false
            restartRecognition()
            return
        }

        print("💬 User utterance captured: '\(trimmed)'")
        lastTranscription = trimmed
        wakeWordDetected = false
        isCapturingUtterance = false

        // Notify callback
        onUtteranceCaptured?(trimmed)

        // Restart listening for next wake word
        restartRecognition()
    }

    private func restartRecognition() {
        // Brief delay before restarting to avoid rapid cycles
        Task {
            try? await Task.sleep(nanoseconds: 500_000_000) // 0.5s

            guard let engine = self.audioEngine, let recognizer = self.speechRecognizer else { return }

            // Cancel old task
            recognitionTask?.cancel()
            recognitionTask = nil
            recognitionRequest?.endAudio()

            // Create new request
            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            if #available(iOS 13, *) {
                request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
            }
            recognitionRequest = request

            startRecognitionTask(recognizer: recognizer, request: request)
            isListening = true
        }
    }
}
