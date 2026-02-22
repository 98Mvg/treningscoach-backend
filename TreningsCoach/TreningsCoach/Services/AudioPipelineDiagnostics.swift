//
//  AudioPipelineDiagnostics.swift
//  TreningsCoach
//
//  Real-time diagnostic monitor for the voice pipeline.
//  Tracks: mic input levels, VAD state, wake-word detection,
//  speech recognition events, and the full signal path.
//
//  Usage: AudioPipelineDiagnostics.shared is fed from
//  ContinuousRecordingManager (audio buffers) and
//  WakeWordManager (recognition events).
//

import Foundation
import Combine
import AVFoundation
import Speech

/// Diagnostic panel tab selection
enum DiagnosticTab: String {
    case voice
    case breath
    case pulse
}

/// Pipeline stage for tracking signal flow
enum PipelineStage: String {
    case micInit = "MIC_INIT"
    case micActive = "MIC_ACTIVE"
    case audioFrame = "AUDIO_FRAME"
    case vadSilence = "VAD_SILENCE"
    case vadVoice = "VAD_VOICE"
    case wakeWordListening = "WAKEWORD_LISTEN"
    case wakeWordDetected = "WAKEWORD_DETECTED"
    case utteranceCapture = "UTTERANCE_CAPTURE"
    case utteranceFinalized = "UTTERANCE_DONE"
    case speechRecogError = "SPEECH_ERROR"
    case backendSend = "BACKEND_SEND"
    case backendResponse = "BACKEND_RESP"
    case ttsPlayback = "TTS_PLAY"
}

/// A single pipeline event for the log
struct PipelineEvent: Identifiable {
    let id = UUID()
    let timestamp: Date
    let stage: PipelineStage
    let detail: String

    var timeString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter.string(from: timestamp)
    }
}

@MainActor
class AudioPipelineDiagnostics: ObservableObject {

    static let shared = AudioPipelineDiagnostics()

    // MARK: - Published State

    /// Current RMS audio level (0.0 - 1.0), updated per buffer
    @Published var audioLevel: Float = 0.0

    /// Peak audio level (decays slowly for visual feedback)
    @Published var peakLevel: Float = 0.0

    /// Audio level in decibels (-160 to 0)
    @Published var decibelLevel: Float = -160.0

    /// Simple VAD: is voice detected (above threshold)?
    @Published var isVoiceDetected: Bool = false

    /// Is the microphone initialized and receiving frames?
    @Published var isMicActive: Bool = false

    /// Total audio frames received since start
    @Published var framesReceived: Int = 0

    /// Frames per second (computed over last second)
    @Published var framesPerSecond: Int = 0

    /// Sample rate detected from audio format
    @Published var sampleRate: Double = 0.0

    /// Wake word manager state
    @Published var isWakeWordListening: Bool = false
    @Published var wakeWordDetected: Bool = false
    @Published var lastWakeWordTime: Date? = nil
    @Published var speechRecognizerAvailable: Bool = false

    /// Last captured utterance
    @Published var lastUtterance: String? = nil

    /// Speech recognition restart diagnostics
    @Published var speechRestartAttempts: Int = 0
    @Published var speechDegradedEvents: Int = 0

    /// Pipeline event log (most recent first, capped at 50)
    @Published var events: [PipelineEvent] = []

    /// Whether the diagnostic overlay is visible
    @Published var isOverlayVisible: Bool = false

    /// Active diagnostic tab (voice pipeline vs breath analysis)
    @Published var diagnosticTab: DiagnosticTab = .voice

    // MARK: - Breath Analysis Diagnostics

    /// Latest breath analysis from backend
    @Published var lastBreathAnalysis: BreathAnalysis?

    /// Total number of breath analyses received
    @Published var breathAnalysisCount: Int = 0

    /// Total number of breath analysis errors
    @Published var breathAnalysisErrors: Int = 0

    /// Last error message for breath analysis
    @Published var lastBreathError: String?

    /// Last backend reason (should_speak / silence reason)
    @Published var lastBreathReason: String?

    /// Timestamp of last breath analysis
    @Published var lastBreathAnalysisTime: Date?

    /// Backend round-trip time in seconds
    @Published var backendResponseTime: TimeInterval?

    /// Size of last audio chunk sent to backend
    @Published var chunkSizeBytes: Int?

    /// Duration of last audio chunk
    @Published var chunkDuration: TimeInterval?

    // MARK: - Coach Decision Diagnostics

    /// Whether coach spoke on last tick
    @Published var lastShouldSpeak: Bool = false

    /// Last coach text (even if not displayed in UI — voice only)
    @Published var lastCoachText: String?

    /// Count of consecutive silent ticks
    @Published var consecutiveSilentTicks: Int = 0

    /// Count of times coach spoke
    @Published var speakCount: Int = 0

    // MARK: - VAD Configuration

    /// RMS threshold for voice activity detection
    /// Target: ~-30dB for soft breathing, ~-15dB for speech
    /// RMS 0.03 ≈ -30dB (breathing/soft), RMS 0.18 ≈ -15dB (normal speech)
    /// Using 0.025 to catch breathing at the low end
    var vadThreshold: Float = 0.025

    // MARK: - Private

    private var frameCountThisSecond: Int = 0
    private var fpsTimer: Timer?

    // MARK: - Init

    private init() {
        // Start FPS counter
        fpsTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self = self else { return }
                self.framesPerSecond = self.frameCountThisSecond
                self.frameCountThisSecond = 0

                // Decay peak level
                self.peakLevel *= 0.85
            }
        }
    }

    // MARK: - Audio Level Feed

    /// Update diagnostics from pre-computed audio stats.
    /// Call this on the main actor.
    func updateFromAudio(rms: Float, db: Float, voiceDetected: Bool, frameCount: Int) {
        let safeRms = sanitizeRms(rms)
        let safeDb = sanitizeDb(db)
        let normalizedLevel = clamp01(safeRms * 5.0) // Scale for visual (0-1)

        self.audioLevel = normalizedLevel
        self.decibelLevel = safeDb
        self.isVoiceDetected = voiceDetected && safeRms.isFinite && safeRms > 0
        self.framesReceived += 1
        self.frameCountThisSecond += 1

        if !self.peakLevel.isFinite {
            self.peakLevel = 0
        }
        if normalizedLevel > self.peakLevel {
            self.peakLevel = normalizedLevel
        }

        if !self.isMicActive {
            self.isMicActive = true
            self.log(.micActive, detail: "First audio frame received")
        }
    }

    private func sanitizeRms(_ value: Float) -> Float {
        guard value.isFinite else { return 0 }
        return max(0, value)
    }

    private func sanitizeDb(_ value: Float) -> Float {
        guard value.isFinite else { return -160.0 }
        return min(0.0, max(-160.0, value))
    }

    private func clamp01(_ value: Float) -> Float {
        guard value.isFinite else { return 0 }
        return max(0, min(1, value))
    }

    // MARK: - Pipeline Event Logging

    func log(_ stage: PipelineStage, detail: String = "") {
        let event = PipelineEvent(timestamp: Date(), stage: stage, detail: detail)
        events.insert(event, at: 0)
        if events.count > 50 {
            events.removeLast()
        }

        // Also print for Xcode console debugging
        print("🔬 [\(stage.rawValue)] \(detail)")
    }

    /// Track speech recognizer restart activity to detect error thrash.
    func recordSpeechRestart(detail: String, degraded: Bool = false) {
        speechRestartAttempts += 1
        if degraded {
            speechDegradedEvents += 1
        }
        let status = degraded ? "DEGRADED" : "RESTART"
        log(.speechRecogError, detail: "[\(status)] \(detail)")
    }

    // MARK: - Standalone Mic Test (with Wake Word)

    /// Standalone audio engine for testing mic independently of workout
    private var testAudioEngine: AVAudioEngine?
    @Published var isMicTestRunning: Bool = false

    /// Speech recognizer for standalone wake word testing
    private var testSpeechRecognizer: SFSpeechRecognizer?
    private var testRecognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var testRecognitionTask: SFSpeechRecognitionTask?
    private var testWakeWords: [String] = ["coach", "hey coach"]

    /// Start a standalone mic test — captures audio from the Mac/device mic
    /// without starting a full workout. Tests the FULL pipeline: mic → frames → VAD → wake word → command.
    func startMicTest() {
        guard !isMicTestRunning else { return }

        log(.micInit, detail: "Starting standalone mic test (with wake word)...")

        let engine = AVAudioEngine()
        let inputNode = engine.inputNode

        // Configure audio session
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setActive(false)
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetoothA2DP, .mixWithOthers])
            try session.setActive(true)
            log(.micInit, detail: "Audio session active: \(session.category.rawValue)")
        } catch {
            log(.speechRecogError, detail: "Audio session error: \(error.localizedDescription)")
            return
        }

        // Get the native format from the input node
        let format = inputNode.outputFormat(forBus: 0)
        sampleRate = format.sampleRate
        log(.micInit, detail: "Format: \(format.sampleRate)Hz, \(format.channelCount)ch")

        // Validate format — simulator may return 0 channels when no mic is available
        guard format.channelCount > 0 && format.sampleRate > 0 else {
            log(.speechRecogError, detail: "Invalid audio format: \(format.sampleRate)Hz, \(format.channelCount)ch — no microphone available?")
            return
        }

        // Setup wake word speech recognizer
        let lang = UserDefaults.standard.string(forKey: "app_language") ?? "en"
        let locale = lang == "no" ? Locale(identifier: "nb-NO") : Locale(identifier: "en-US")
        testSpeechRecognizer = SFSpeechRecognizer(locale: locale)
        testWakeWords = WakeWordManager.wakeWords[lang] ?? WakeWordManager.wakeWords["en"]!

        // Create recognition request
        let recognitionReq = SFSpeechAudioBufferRecognitionRequest()
        recognitionReq.shouldReportPartialResults = true
        if let recognizer = testSpeechRecognizer {
            if #available(iOS 13, *) {
                recognitionReq.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
            }
        }
        testRecognitionRequest = recognitionReq

        // Start speech recognition task for wake word detection
        if let recognizer = testSpeechRecognizer, recognizer.isAvailable {
            speechRecognizerAvailable = true
            isWakeWordListening = true
            log(.wakeWordListening, detail: "Test mode — words: \(testWakeWords.joined(separator: ", "))")
            startTestRecognitionTask(recognizer: recognizer, request: recognitionReq)
        } else {
            speechRecognizerAvailable = false
            log(.speechRecogError, detail: "Speech recognizer unavailable for locale: \(locale.identifier)")
        }

        // Install tap to capture audio buffers
        // Pass nil for format to use the node's native format (avoids format mismatch crashes)
        inputNode.installTap(onBus: 0, bufferSize: 4096, format: nil) { [weak self] buffer, time in
            guard let channelData = buffer.floatChannelData else { return }
            let frameLength = Int(buffer.frameLength)
            guard frameLength > 0 else { return }

            // Compute RMS + dB on the audio thread
            var sumSquares: Float = 0.0
            for i in 0..<frameLength {
                let sample = channelData[0][i]
                sumSquares += sample * sample
            }
            let rms = sqrtf(sumSquares / Float(frameLength))
            let db = 20.0 * log10f(max(rms, 1e-10))
            let voiceDetected = rms > 0.025

            Task { @MainActor in
                self?.updateFromAudio(rms: rms, db: db, voiceDetected: voiceDetected, frameCount: frameLength)
            }

            // Feed audio to wake word speech recognizer
            self?.testRecognitionRequest?.append(buffer)
        }

        do {
            try engine.start()
            testAudioEngine = engine
            isMicTestRunning = true
            log(.micActive, detail: "Mic test running — say 'Coach' to test wake word!")
        } catch {
            // Clean up tap if engine fails to start
            inputNode.removeTap(onBus: 0)
            log(.speechRecogError, detail: "Engine start failed: \(error.localizedDescription)")
        }
    }

    /// Stop the standalone mic test
    func stopMicTest() {
        guard isMicTestRunning else { return }

        // Stop speech recognition
        testRecognitionTask?.cancel()
        testRecognitionTask = nil
        testRecognitionRequest?.endAudio()
        testRecognitionRequest = nil
        testSpeechRecognizer = nil

        testAudioEngine?.inputNode.removeTap(onBus: 0)
        testAudioEngine?.stop()
        testAudioEngine = nil
        isMicTestRunning = false
        isMicActive = false
        isWakeWordListening = false
        wakeWordDetected = false
        log(.micInit, detail: "Mic test stopped")
    }

    // MARK: - Test Wake Word Recognition

    private func startTestRecognitionTask(recognizer: SFSpeechRecognizer, request: SFSpeechAudioBufferRecognitionRequest) {
        var wakeWordFound = false
        var capturedText = ""

        testRecognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self = self else { return }

            if let error = error {
                print("⚠️ Test speech recognition error: \(error.localizedDescription)")
                Task { @MainActor in
                    self.log(.speechRecogError, detail: "Test: \(error.localizedDescription)")
                    // Restart recognition if still in test mode
                    if self.isMicTestRunning {
                        self.restartTestRecognition()
                    }
                }
                return
            }

            guard let result = result else { return }

            let transcription = result.bestTranscription.formattedString.lowercased()

            Task { @MainActor in
                if !wakeWordFound {
                    // Looking for wake word
                    for wakeWord in self.testWakeWords {
                        if transcription.contains(wakeWord) {
                            wakeWordFound = true
                            self.wakeWordDetected = true
                            self.lastWakeWordTime = Date()
                            self.log(.wakeWordDetected, detail: "TEST: '\(wakeWord)' in '\(transcription)'")

                            // Extract text after wake word
                            capturedText = transcription
                            for w in self.testWakeWords {
                                capturedText = capturedText.replacingOccurrences(of: w, with: "").trimmingCharacters(in: .whitespaces)
                            }

                            // Wait 3 seconds for follow-up utterance, then finalize
                            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) { [weak self] in
                                guard let self = self else { return }
                                if !capturedText.isEmpty {
                                    self.lastUtterance = capturedText
                                    self.log(.utteranceFinalized, detail: "TEST: '\(capturedText)'")
                                } else {
                                    self.log(.utteranceFinalized, detail: "TEST: Wake word only, no follow-up")
                                }
                                self.wakeWordDetected = false
                                // Restart for next detection
                                self.restartTestRecognition()
                            }
                            break
                        }
                    }
                } else {
                    // Capturing utterance after wake word
                    capturedText = transcription
                    for w in self.testWakeWords {
                        capturedText = capturedText.replacingOccurrences(of: w, with: "").trimmingCharacters(in: .whitespaces)
                    }

                    if result.isFinal && !capturedText.isEmpty {
                        self.lastUtterance = capturedText
                        self.log(.utteranceFinalized, detail: "TEST: '\(capturedText)'")
                        self.wakeWordDetected = false
                        self.restartTestRecognition()
                    }
                }
            }
        }
    }

    private func restartTestRecognition() {
        guard isMicTestRunning, let recognizer = testSpeechRecognizer else { return }

        // Cancel old task
        testRecognitionTask?.cancel()
        testRecognitionTask = nil
        testRecognitionRequest?.endAudio()

        // Brief delay before restarting
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            guard let self = self, self.isMicTestRunning else { return }

            // Create new request
            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            if #available(iOS 13, *) {
                request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
            }
            self.testRecognitionRequest = request
            self.isWakeWordListening = true
            self.log(.wakeWordListening, detail: "Test: restarted — say 'Coach'")
            self.startTestRecognitionTask(recognizer: recognizer, request: request)
        }
    }

    // MARK: - Breath Analysis Update

    /// Called from WorkoutViewModel after each coaching tick
    func updateBreathAnalysis(
        _ analysis: BreathAnalysis,
        responseTime: TimeInterval,
        chunkBytes: Int?,
        chunkDur: TimeInterval?,
        reason: String?,
        shouldSpeak: Bool = false,
        coachText: String? = nil
    ) {
        lastBreathAnalysis = analysis
        breathAnalysisCount += 1
        lastBreathAnalysisTime = Date()
        backendResponseTime = responseTime
        chunkSizeBytes = chunkBytes
        chunkDuration = chunkDur
        lastBreathReason = reason
        lastShouldSpeak = shouldSpeak
        lastCoachText = coachText

        if shouldSpeak {
            speakCount += 1
            consecutiveSilentTicks = 0
        } else {
            consecutiveSilentTicks += 1
        }

        let speakStr = shouldSpeak ? "SPEAK" : "SILENT"
        log(.backendResponse, detail: "[\(speakStr)] \(analysis.intensity), SQ:\(String(format: "%.2f", analysis.signalQuality ?? 0)), RTT:\(Int(responseTime * 1000))ms, reason:\(reason ?? "?")")
    }

    func recordBreathAnalysisError(_ message: String = "Unknown error") {
        breathAnalysisErrors += 1
        lastBreathError = message
        lastBreathReason = nil
        log(.backendResponse, detail: "ERROR: \(message)")
    }

    /// Time since last breath analysis (for display)
    var timeSinceLastBreathAnalysis: String {
        guard let lastTime = lastBreathAnalysisTime else { return "—" }
        let seconds = Int(Date().timeIntervalSince(lastTime))
        if seconds < 60 { return "\(seconds)s ago" }
        return "\(seconds / 60)m ago"
    }

    // MARK: - Reset

    func reset() {
        stopMicTest()
        audioLevel = 0
        peakLevel = 0
        decibelLevel = -160
        isVoiceDetected = false
        isMicActive = false
        framesReceived = 0
        framesPerSecond = 0
        isWakeWordListening = false
        wakeWordDetected = false
        lastUtterance = nil
        events.removeAll()
        // Reset breath diagnostics
        lastBreathAnalysis = nil
        breathAnalysisCount = 0
        breathAnalysisErrors = 0
        lastBreathError = nil
        lastBreathReason = nil
        lastBreathAnalysisTime = nil
        backendResponseTime = nil
        chunkSizeBytes = nil
        chunkDuration = nil
        diagnosticTab = .voice
    }
}
