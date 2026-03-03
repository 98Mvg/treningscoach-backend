//
//  WakeWordManager.swift
//  TreningsCoach
//
//  Listens for wake phrase ("coach" / "coachi") during continuous workout.
//
//  Architecture:
//  - Uses Apple's SFSpeechRecognizer for on-device speech recognition
//  - Taps into the SAME AVAudioEngine as ContinuousRecordingManager
//  - Runs on-device phrase spotting with constrained wake words
//  - Emits wake events only (no transcript command parsing in workout path)
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
    @Published var isDegradedMode = false        // Speech recognizer temporarily degraded

    // MARK: - Configuration

    /// Wake phrases per language (locked runtime set)
    /// NOTE: v1 allows only "coach" and "coachi".
    static let wakeWords: [String: [String]] = [
        "en": ["coach", "coachi"],
        "no": ["coach", "coachi"]
    ]

    /// Retrigger cooldown to avoid duplicate wake detections.
    private let wakeCooldownSeconds: TimeInterval = 10.0

    // MARK: - Private Properties

    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var audioEngine: AVAudioEngine?

    private var currentWakeWords: [String] = ["coach"]
    private var utteranceCaptureTimer: Timer?
    private var onUtteranceCaptured: ((String) -> Void)?
    private var lastWakeDetectionAt: Date?

    private var isAuthorized = false

    // Button-capture state
    private var capturedText = ""
    private var captureOnResult: ((String) -> Void)?
    private var captureWasListening = false
    private var isButtonCaptureSession = false

    // Restart/backoff control (prevents infinite speech error loops)
    private var restartAttemptCount = 0
    private var restartWindowStart: Date = .distantPast
    private var pendingRestartTask: Task<Void, Never>?
    private var degradedRecoveryTask: Task<Void, Never>?
    private let restartWindowSeconds: TimeInterval = 20.0
    private let maxRestartAttemptsPerWindow = 6
    private let maxRestartBackoffSeconds: TimeInterval = 5.0
    private let degradedRecoveryDelaySeconds: TimeInterval = 8.0
    private let idleNoSpeechRestartDelaySeconds: TimeInterval = 1.5

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

    /// Start listening for wake phrase on the given audio engine
    /// Shares the audio engine with ContinuousRecordingManager
    func startListening(audioEngine: AVAudioEngine, onUtterance: @escaping (String) -> Void) {
        let diag = AudioPipelineDiagnostics.shared

        guard isAuthorized else {
            print("⚠️ Speech recognition not authorized, cannot listen for wake word")
            diag.log(.speechRecogError, detail: "Not authorized")
            return
        }

        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            print("⚠️ Speech recognizer not available")
            diag.log(.speechRecogError, detail: "Recognizer unavailable")
            diag.speechRecognizerAvailable = false
            return
        }
        diag.speechRecognizerAvailable = true

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

        resetErrorRetryState()

        // Use the input node directly — we'll feed buffers manually
        // Instead of a second tap (which conflicts), we'll use a different approach:
        // Install tap on the input node with a custom format via a mixer
        startRecognitionTask(recognizer: recognizer, request: request)

        // Feed audio buffers from the input node
        // We tap into the input node's output — sharing with ContinuousRecordingManager
        // Note: ContinuousRecordingManager already has a tap on bus 0.
        // We can't install a second tap on the same bus.
        // Instead, we'll periodically feed audio from the circular buffer.
        // Alternative: use a splitter node. For simplicity, we install on bus 0
        // and let ContinuousRecordingManager handle it — we just need the buffers.

        isListening = true
        diag.isWakeWordListening = true
        diag.log(.wakeWordListening, detail: "Words: \(currentWakeWords.joined(separator: ", "))")
        print("👂 Wake word listening started (kws phrases: \(currentWakeWords))")
    }

    /// Feed an audio buffer to the speech recognizer
    /// Called by ContinuousRecordingManager when it processes buffers
    func feedAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        guard isListening || isCapturingUtterance else { return }
        recognitionRequest?.append(buffer)
    }

    /// Start a short speech capture session (button-triggered, no wake word needed).
    /// Captures whatever the user says for up to `duration` seconds, then calls `onResult`.
    func captureUtterance(duration: TimeInterval = 5.0, onResult: @escaping (String) -> Void) {
        let diag = AudioPipelineDiagnostics.shared

        guard isAuthorized else {
            print("⚠️ Speech recognition not authorized for capture")
            diag.log(.speechRecogError, detail: "Not authorized (capture)")
            onResult("")
            return
        }

        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            print("⚠️ Speech recognizer not available for capture")
            diag.log(.speechRecogError, detail: "Recognizer unavailable (capture)")
            onResult("")
            return
        }

        guard !isCapturingUtterance else {
            print("⚠️ Capture already active — ignoring duplicate capture request")
            onResult("")
            return
        }

        // Store state for the capture session
        captureWasListening = isListening
        captureOnResult = onResult
        capturedText = ""
        isButtonCaptureSession = true

        // Prevent in-flight wake-word restarts from colliding with button capture.
        isListening = false
        pendingRestartTask?.cancel()
        pendingRestartTask = nil

        // Stop any existing wake-word listening (we'll restart after capture)
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest?.endAudio()

        // Create a new recognition request for capture
        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        if #available(iOS 13, *) {
            request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
        }
        recognitionRequest = request

        isCapturingUtterance = true

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self = self else { return }
            guard self.isCapturingUtterance else { return }

            if let error = error {
                let canceled = self.isCancellationLikeError(error)
                if canceled {
                    return
                }
                if self.isNoSpeechError(error) {
                    print("⚠️ Capture speech recognition error: No speech detected")
                } else {
                    print("⚠️ Capture speech recognition error: \(error.localizedDescription)")
                    Task { @MainActor in
                        AudioPipelineDiagnostics.shared.log(.speechRecogError, detail: "Capture: \(error.localizedDescription)")
                    }
                }
                return
            }

            guard let result = result else { return }

            Task { @MainActor in
                self.capturedText = result.bestTranscription.formattedString

                // If final result arrives early, deliver immediately
                if result.isFinal && !self.capturedText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    self.utteranceCaptureTimer?.invalidate()
                    self.utteranceCaptureTimer = nil
                    self.finishCapture()
                }
            }
        }

        // Timeout: deliver whatever we have after `duration` seconds
        utteranceCaptureTimer = Timer.scheduledTimer(withTimeInterval: duration, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.finishCapture()
            }
        }

        print("🎤 Capture session started (\(duration)s timeout)")
        diag.log(.wakeWordListening, detail: "Button capture started")
    }

    /// Finish a button-triggered capture session
    private func finishCapture() {
        guard isCapturingUtterance else { return }  // Already finished
        isCapturingUtterance = false
        isButtonCaptureSession = false
        utteranceCaptureTimer?.invalidate()
        utteranceCaptureTimer = nil

        // Cancel the capture task
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest?.endAudio()
        recognitionRequest = nil

        let trimmed = capturedText.trimmingCharacters(in: .whitespacesAndNewlines)
        print("💬 Capture result: '\(trimmed)'")
        AudioPipelineDiagnostics.shared.log(.utteranceFinalized, detail: "Button capture: '\(trimmed)'")

        // Deliver result
        captureOnResult?(trimmed)
        captureOnResult = nil

        // Restart wake-word listening if it was active before
        let wasListening = captureWasListening
        if wasListening, let recognizer = self.speechRecognizer {
            Task {
                try? await Task.sleep(nanoseconds: 300_000_000) // 0.3s
                let request = SFSpeechAudioBufferRecognitionRequest()
                request.shouldReportPartialResults = true
                if #available(iOS 13, *) {
                    request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
                }
                await MainActor.run {
                    self.recognitionRequest = request
                    self.resetErrorRetryState()
                    self.startRecognitionTask(recognizer: recognizer, request: request)
                    self.isListening = true
                }
            }
        }
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
        isButtonCaptureSession = false
        wakeWordDetected = false
        isDegradedMode = false
        restartAttemptCount = 0
        restartWindowStart = .distantPast
        pendingRestartTask?.cancel()
        pendingRestartTask = nil
        degradedRecoveryTask?.cancel()
        degradedRecoveryTask = nil

        AudioPipelineDiagnostics.shared.isWakeWordListening = false
        AudioPipelineDiagnostics.shared.wakeWordDetected = false
        print("🔇 Wake word listening stopped")
    }

    // MARK: - Private Methods

    private func startRecognitionTask(recognizer: SFSpeechRecognizer, request: SFSpeechAudioBufferRecognitionRequest) {
        request.contextualStrings = currentWakeWords

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self = self else { return }

            if let error = error {
                let canceled = self.isCancellationLikeError(error)
                let detail = error.localizedDescription
                let noSpeech = self.isNoSpeechError(error)

                // Transitional cancellation/no-speech can happen when switching between
                // wake-word listening and manual button capture; keep logs clean.
                if canceled || (!self.isListening && (self.isButtonCaptureSession || noSpeech)) {
                    return
                }

                // "No speech detected" is common in idle wake-word listening and should not trigger
                // aggressive exponential backoff/degraded mode.
                if noSpeech {
                    print("⚠️ Speech recognition error: No speech detected")
                    Task { @MainActor in
                        AudioPipelineDiagnostics.shared.log(.speechRecogError, detail: "No speech detected")
                    }
                } else {
                    print("⚠️ Speech recognition error: \(detail)")
                    Task { @MainActor in
                        AudioPipelineDiagnostics.shared.log(.speechRecogError, detail: detail)
                    }
                }

                // Restart listening only when wake-word listener is active (not during button capture).
                if self.isListening && !self.isButtonCaptureSession {
                    Task { @MainActor in
                        if noSpeech {
                            self.restartRecognition(
                                reason: "idle_no_speech",
                                isErrorRetry: false,
                                delayOverride: self.idleNoSpeechRestartDelaySeconds
                            )
                        } else {
                            self.restartRecognition(reason: detail, isErrorRetry: true)
                        }
                    }
                }
                return
            }

            guard let result = result else { return }

            let transcription = result.bestTranscription.formattedString.lowercased()

            Task { @MainActor in
                self.resetErrorRetryState()
                for wakeWord in self.currentWakeWords where self.matchesWakePhrase(wakeWord, in: transcription) {
                    let now = Date()
                    if let previous = self.lastWakeDetectionAt,
                       now.timeIntervalSince(previous) < self.wakeCooldownSeconds {
                        AudioPipelineDiagnostics.shared.log(
                            .wakeWordDetected,
                            detail: "Suppressed by cooldown (\(Int(self.wakeCooldownSeconds))s)"
                        )
                        return
                    }

                    self.lastWakeDetectionAt = now
                    self.wakeWordDetected = true
                    self.isCapturingUtterance = true
                    AudioPipelineDiagnostics.shared.wakeWordDetected = true
                    AudioPipelineDiagnostics.shared.lastWakeWordTime = now
                    AudioPipelineDiagnostics.shared.log(.wakeWordDetected, detail: "'\(wakeWord)'")
                    print("🎯 Wake phrase detected: '\(wakeWord)'")

                    self.onUtteranceCaptured?(wakeWord)
                    self.utteranceCaptureTimer?.invalidate()
                    self.utteranceCaptureTimer = Timer.scheduledTimer(withTimeInterval: 0.6, repeats: false) { [weak self] _ in
                        Task { @MainActor in
                            self?.wakeWordDetected = false
                            self?.isCapturingUtterance = false
                            AudioPipelineDiagnostics.shared.wakeWordDetected = false
                        }
                    }
                    return
                }
            }
        }
    }

    private func matchesWakePhrase(_ phrase: String, in transcription: String) -> Bool {
        let escaped = NSRegularExpression.escapedPattern(for: phrase)
        let pattern = "(^|[^a-zA-ZæøåÆØÅ])\(escaped)([^a-zA-ZæøåÆØÅ]|$)"
        return transcription.range(of: pattern, options: .regularExpression) != nil
    }

    private func resetErrorRetryState() {
        restartAttemptCount = 0
        restartWindowStart = .distantPast
        isDegradedMode = false
        degradedRecoveryTask?.cancel()
        degradedRecoveryTask = nil
    }

    private func scheduleDegradedRecovery() {
        degradedRecoveryTask?.cancel()
        degradedRecoveryTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: UInt64(degradedRecoveryDelaySeconds * 1_000_000_000))
            guard !Task.isCancelled else { return }
            guard self.audioEngine != nil, self.speechRecognizer != nil else { return }
            self.resetErrorRetryState()
            self.restartRecognition(reason: "degraded_recovery")
        }
    }

    private func restartRecognition(
        reason: String = "manual",
        isErrorRetry: Bool = false,
        delayOverride: TimeInterval? = nil
    ) {
        guard self.audioEngine != nil, let recognizer = self.speechRecognizer else { return }

        var delaySeconds: TimeInterval = 0.3
        if isErrorRetry {
            let now = Date()
            if now.timeIntervalSince(restartWindowStart) > restartWindowSeconds {
                restartWindowStart = now
                restartAttemptCount = 0
            }
            restartAttemptCount += 1

            if restartAttemptCount > maxRestartAttemptsPerWindow {
                isDegradedMode = true
                isListening = false
                isCapturingUtterance = false
                AudioPipelineDiagnostics.shared.recordSpeechRestart(
                    detail: "Exceeded retry limit (\(maxRestartAttemptsPerWindow)) in \(Int(restartWindowSeconds))s window",
                    degraded: true
                )
                scheduleDegradedRecovery()
                return
            }

            delaySeconds = min(0.5 * pow(2.0, Double(max(0, restartAttemptCount - 1))), maxRestartBackoffSeconds)
            AudioPipelineDiagnostics.shared.recordSpeechRestart(
                detail: "reason='\(reason)' attempt=\(restartAttemptCount) delay=\(String(format: "%.2f", delaySeconds))s"
            )
        }
        if let override = delayOverride {
            delaySeconds = max(0, override)
        }

        pendingRestartTask?.cancel()
        pendingRestartTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: UInt64(delaySeconds * 1_000_000_000))
            guard !Task.isCancelled else { return }
            guard self.audioEngine != nil else { return }

            // Cancel old task
            self.recognitionTask?.cancel()
            self.recognitionTask = nil
            self.recognitionRequest?.endAudio()

            // Create new request
            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            if #available(iOS 13, *) {
                request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
            }
            self.recognitionRequest = request

            self.startRecognitionTask(recognizer: recognizer, request: request)
            self.isListening = true
        }
    }

    private func isNoSpeechError(_ error: Error) -> Bool {
        let text = error.localizedDescription.lowercased()
        return text.contains("no speech")
    }

    private func isCancellationLikeError(_ error: Error) -> Bool {
        let nsError = error as NSError
        let text = nsError.localizedDescription.lowercased()

        if text.contains("canceled") || text.contains("cancelled") {
            return true
        }
        if nsError.domain == NSURLErrorDomain && nsError.code == NSURLErrorCancelled {
            return true
        }
        if nsError.domain == "kAFAssistantErrorDomain" && (nsError.code == 1101 || nsError.code == 1107 || nsError.code == 1110) {
            return true
        }
        if nsError.domain == "kAFAssistantErrorDomain" && text.contains("recognition request was canceled") {
            return true
        }
        return false
    }
}
