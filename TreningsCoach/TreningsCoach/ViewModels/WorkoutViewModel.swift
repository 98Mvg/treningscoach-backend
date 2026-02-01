//
//  WorkoutViewModel.swift
//  TreningsCoach
//
//  Main view model for workout screen
//

import Foundation
import SwiftUI
import AVFoundation

@MainActor
class WorkoutViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var breathAnalysis: BreathAnalysis?
    @Published var coachMessage: String?
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var voiceState: VoiceState = .idle
    @Published var currentPhase: WorkoutPhase = .intense

    // MARK: - Computed Properties

    var currentPhaseDisplay: String {
        switch currentPhase {
        case .warmup:
            return "Warm-up"
        case .intense:
            return "Hard Coach"
        case .cooldown:
            return "Cool-down"
        }
    }

    // MARK: - Continuous Coaching Properties

    @Published var isContinuousMode = false
    @Published var coachingInterval: TimeInterval = AppConfig.ContinuousCoaching.defaultInterval

    // MARK: - UI Properties (for new dashboard/profile screens)

    @Published var elapsedTime: TimeInterval = 0
    @Published var workoutHistory: [WorkoutRecord] = []
    @Published var userStats: UserStats = UserStats()

    // Time-of-day greeting for the home screen
    var greetingText: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        case 17..<22: return "Good evening"
        default: return "Good night"
        }
    }

    // Formatted elapsed time string (MM:SS)
    var elapsedTimeFormatted: String {
        let mins = Int(elapsedTime) / 60
        let secs = Int(elapsedTime) % 60
        return String(format: "%02d:%02d", mins, secs)
    }

    // MARK: - Private Properties

    private let audioManager = AudioRecordingManager()
    private let continuousRecordingManager = ContinuousRecordingManager()
    private let apiService = BackendAPIService.shared
    private var audioPlayer: AVAudioPlayer?
    private var sessionStartTime: Date?
    private var workoutDuration: TimeInterval = 0
    private var coachingTimer: Timer?
    private var sessionId: String?
    private var autoTimeoutTimer: Timer?
    private var elapsedTimeTimer: Timer?

    // MARK: - Initialization

    init() {
        // Configure audio session for playback
        setupAudioSession()

        // Check backend connectivity on launch
        Task {
            await checkBackendHealth()
        }
        print("🔗 Backend URL: \(AppConfig.backendURL)")
    }

    private func setupAudioSession() {
        do {
            // Set category to playback (allows audio even when silent switch is on)
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [])
            // Activate the audio session
            try AVAudioSession.sharedInstance().setActive(true)
            print("✅ Audio session configured for playback")
        } catch {
            print("❌ Failed to setup audio session: \(error.localizedDescription)")
        }
    }

    // MARK: - Recording

    func startRecording() {
        guard !isRecording && !isProcessing else { return }

        // Auto-detect phase based on workout duration
        autoDetectPhase()

        do {
            try audioManager.startRecording()
            isRecording = true
            voiceState = .listening
            breathAnalysis = nil
            coachMessage = nil

            // Start session timer if first recording
            if sessionStartTime == nil {
                sessionStartTime = Date()
            }
        } catch {
            showErrorAlert("Failed to start recording: \(error.localizedDescription)")
        }
    }

    func stopRecording() {
        guard isRecording else { return }

        guard let audioURL = audioManager.stopRecording() else {
            showErrorAlert("Failed to stop recording")
            voiceState = .idle
            return
        }

        isRecording = false
        voiceState = .idle

        // Update workout duration
        if let startTime = sessionStartTime {
            workoutDuration = Date().timeIntervalSince(startTime)
        }

        // Send to backend
        Task {
            await sendToBackend(audioURL: audioURL, phase: currentPhase)
        }
    }

    // MARK: - Phase Auto-Detection

    private func autoDetectPhase() {
        // Auto-detect workout phase based on duration
        // First 2 minutes: warmup
        // 2-15 minutes: intense
        // After 15 minutes: cooldown

        guard let startTime = sessionStartTime else {
            currentPhase = .warmup
            return
        }

        let duration = Date().timeIntervalSince(startTime)

        if duration < 120 { // First 2 minutes
            currentPhase = .warmup
        } else if duration < 900 { // 2-15 minutes
            currentPhase = .intense
        } else { // After 15 minutes
            currentPhase = .cooldown
        }
    }

    // MARK: - API Communication

    func sendToBackend(audioURL: URL, phase: WorkoutPhase) async {
        isProcessing = true
        voiceState = .idle // Show processing state

        do {
            // Send to coach endpoint
            let response = try await apiService.getCoachFeedback(audioURL, phase: phase)

            // Update UI with response
            breathAnalysis = response.breathAnalysis
            coachMessage = response.text

            // Play voice and show speaking state
            voiceState = .speaking
            await downloadAndPlayVoice(audioURL: response.audioURL)

            // Return to idle after speaking
            voiceState = .idle

        } catch {
            showErrorAlert("Failed to analyze: \(error.localizedDescription)")
            voiceState = .idle
        }

        isProcessing = false
    }

    private func downloadAndPlayVoice(audioURL: String) async {
        do {
            let audioData = try await apiService.downloadVoiceAudio(from: audioURL)

            // Save to temporary file (WAV format from Qwen3-TTS)
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("coach_voice.wav")
            try audioData.write(to: tempURL)

            // Play audio and wait for completion
            await playAudio(from: tempURL)

        } catch {
            print("Failed to download/play voice: \(error.localizedDescription)")
            // Don't show error to user - just log it
        }
    }

    private func playAudio(from url: URL) async {
        do {
            print("🔊 Attempting to play audio from: \(url.path)")

            // Ensure audio session allows playback (may be in .playAndRecord during workout)
            let session = AVAudioSession.sharedInstance()
            if session.category != .playAndRecord && session.category != .playback {
                try session.setCategory(.playback, mode: .default, options: [])
            }
            try session.setActive(true)

            // Create audio player
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.prepareToPlay()

            // Set volume to maximum to ensure it's audible
            audioPlayer?.volume = 1.0

            guard let duration = audioPlayer?.duration, duration > 0 else {
                print("⚠️ Audio file has no duration, skipping playback")
                return
            }

            print("▶️ Playing audio (duration: \(duration)s)")
            audioPlayer?.play()

            // Wait for audio to finish (add small buffer for safety)
            try? await Task.sleep(nanoseconds: UInt64((duration + 0.1) * 1_000_000_000))
            print("✅ Audio playback completed")
        } catch {
            print("❌ Failed to play audio: \(error.localizedDescription)")
        }
    }

    // MARK: - Error Handling

    private func showErrorAlert(_ message: String) {
        errorMessage = message
        showError = true
        voiceState = .idle
    }

    // MARK: - Health Check

    func checkBackendHealth() async {
        do {
            let health = try await apiService.checkHealth()
            // Backend responded — connection is good
            print("✅ Backend connected: \(health.status), version: \(health.version ?? "unknown")")
        } catch {
            // Backend not reachable — log clearly so you can spot it in Xcode console
            print("❌ Backend NOT reachable at \(AppConfig.backendURL) — \(error.localizedDescription)")
            print("💡 Make sure your backend is running. Audio will not work without it.")
        }
    }

    // MARK: - Continuous Coaching Loop

    func startContinuousWorkout() {
        guard !isContinuousMode else { return }

        print("🎯 Starting continuous workout")

        do {
            // Start ONE continuous recording session
            try continuousRecordingManager.startContinuousRecording()

            isContinuousMode = true
            voiceState = .listening  // STAYS listening entire workout
            sessionStartTime = Date()
            workoutDuration = 0

            // Generate unique session ID
            sessionId = "session_\(UUID().uuidString)"

            // Auto-detect initial phase
            autoDetectPhase()

            // Start 1-second timer to update elapsed time (drives the timer ring UI)
            elapsedTimeTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
                Task { @MainActor in
                    guard let self = self, let start = self.sessionStartTime else { return }
                    self.elapsedTime = Date().timeIntervalSince(start)
                }
            }

            // Play welcome message immediately (don't wait for first 8s tick)
            Task {
                await playWelcomeMessage()
            }

            // Start coaching loop (independent of recording)
            scheduleNextTick()

            // Set auto-timeout (45 minutes)
            autoTimeoutTimer = Timer.scheduledTimer(
                withTimeInterval: AppConfig.ContinuousCoaching.maxWorkoutDuration,
                repeats: false
            ) { [weak self] _ in
                Task { @MainActor in
                    self?.handleAutoTimeout()
                }
            }

            print("✅ Continuous workout started - session: \(sessionId ?? "unknown")")

        } catch {
            showErrorAlert("Failed to start continuous workout: \(error.localizedDescription)")
            isContinuousMode = false
        }
    }

    func stopContinuousWorkout() {
        guard isContinuousMode else { return }

        print("⏹️ Stopping continuous workout")

        // Stop recording
        continuousRecordingManager.stopContinuousRecording()

        // Cancel timers
        coachingTimer?.invalidate()
        coachingTimer = nil
        autoTimeoutTimer?.invalidate()
        autoTimeoutTimer = nil
        elapsedTimeTimer?.invalidate()
        elapsedTimeTimer = nil

        // Update state
        isContinuousMode = false
        voiceState = .idle
        sessionId = nil

        // Update final workout duration and save to history
        if let startTime = sessionStartTime {
            workoutDuration = Date().timeIntervalSince(startTime)
            print("📊 Workout completed: \(Int(workoutDuration)) seconds")

            // Save workout record for dashboard history
            let record = WorkoutRecord(
                durationSeconds: Int(workoutDuration),
                phase: currentPhase,
                intensity: breathAnalysis?.intensity ?? "moderate"
            )
            workoutHistory.insert(record, at: 0)

            // Update user stats
            userStats.totalWorkouts += 1
            userStats.totalMinutes += Int(workoutDuration / 60)
            userStats.workoutsThisWeek += 1
        }

        elapsedTime = 0
        print("✅ Continuous workout stopped")
    }

    private func coachingLoopTick() {
        guard isContinuousMode else { return }

        // Update workout duration
        if let startTime = sessionStartTime {
            workoutDuration = Date().timeIntervalSince(startTime)
        }

        // Auto-detect phase based on elapsed time
        autoDetectPhase()

        // 1. Get latest chunk WITHOUT stopping recording
        guard let audioChunk = continuousRecordingManager.getLatestChunk(
            duration: AppConfig.ContinuousCoaching.chunkDuration
        ) else {
            print("⚠️ No audio chunk available, retrying next tick")
            scheduleNextTick()
            return
        }

        print("🎤 Coaching tick: \(Int(workoutDuration))s, phase: \(currentPhase.rawValue)")

        // 2. Send to backend (background task)
        Task {
            do {
                let response = try await apiService.getContinuousCoachFeedback(
                    audioChunk,
                    sessionId: sessionId ?? "",
                    phase: currentPhase,
                    lastCoaching: coachMessage ?? "",
                    elapsedSeconds: Int(workoutDuration)
                )

                // 3. Update metrics silently (NO UI state change)
                breathAnalysis = response.breathAnalysis
                coachMessage = response.text

                print("📊 Analysis: \(response.breathAnalysis.intensity), should_speak: \(response.shouldSpeak), reason: \(response.reason ?? "none")")

                // 4. Coach speaks ONLY if backend says so
                // voiceState STAYS .listening (no visual state change during workout)
                if response.shouldSpeak, let audioURL = response.audioURL {
                    print("🗣️ Coach speaking: '\(response.text)'")
                    await playCoachAudio(audioURL)
                } else {
                    print("🤐 Coach silent: \(response.reason ?? "no reason")")
                }

                // 5. Adjust next interval dynamically
                coachingInterval = response.waitSeconds
                print("⏱️ Next tick in: \(Int(coachingInterval))s")

            } catch {
                // Network error: skip this cycle, continue next
                print("❌ Coaching cycle failed: \(error.localizedDescription)")
            }

            // Always schedule next tick (loop continues)
            scheduleNextTick()
        }
    }

    private func scheduleNextTick() {
        guard isContinuousMode else { return }

        coachingTimer?.invalidate()
        coachingTimer = Timer.scheduledTimer(
            withTimeInterval: coachingInterval,
            repeats: false
        ) { [weak self] _ in
            Task { @MainActor in
                self?.coachingLoopTick()
            }
        }
    }

    private func handleAutoTimeout() {
        print("⏰ Auto-timeout triggered after 45 minutes")

        // User forgot to stop - gracefully end workout
        stopContinuousWorkout()

        // Show gentle post-workout message (NOT during workout)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.coachMessage = AppConfig.ContinuousCoaching.autoTimeoutMessage
        }
    }

    private func playWelcomeMessage() async {
        do {
            print("👋 Fetching welcome message...")
            let welcome = try await apiService.getWelcomeMessage()
            coachMessage = welcome.text
            print("👋 Welcome: '\(welcome.text)' - downloading audio...")
            await playCoachAudio(welcome.audioURL)
        } catch {
            print("⚠️ Welcome message failed: \(error.localizedDescription)")
            // Non-critical: workout continues even if welcome fails
        }
    }

    private func playCoachAudio(_ audioURL: String) async {
        do {
            let audioData = try await apiService.downloadVoiceAudio(from: audioURL)

            // Save to temporary file (WAV format from Qwen3-TTS)
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("continuous_coach_\(Date().timeIntervalSince1970).wav")
            try audioData.write(to: tempURL)

            // Play audio (NO state change - stays .listening)
            await playAudio(from: tempURL)

        } catch {
            print("Failed to download/play coach audio: \(error.localizedDescription)")
            // Don't show error to user - just log and continue
        }
    }
}
