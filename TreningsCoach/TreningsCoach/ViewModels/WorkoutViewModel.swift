//
//  WorkoutViewModel.swift
//  TreningsCoach
//
//  Main view model for workout screen
//

import Foundation
import SwiftUI
import AVFoundation
import HealthKit
import CoreMotion
import UIKit

/// State machine for coach interaction during workout
enum CoachInteractionState: String {
    case passiveListening   // Mic on, waiting for wake word or button
    case wakeWordDetected   // Wake word heard, capturing command
    case commandMode        // User is speaking a command
    case responding         // Coach is generating/speaking response
}

private final class HealthKitHeartRateService {
    struct Update {
        let bpm: Int
        let date: Date
        let isWatchSource: Bool
    }

    private let healthStore = HKHealthStore()
    private var observerQuery: HKObserverQuery?
    private var anchoredQuery: HKAnchoredObjectQuery?
    private var queryAnchor: HKQueryAnchor?
    private var onUpdate: ((Update) -> Void)?

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

    func fetchLatestHeartRateSnapshot() async -> Update? {
        guard let heartRateType else { return nil }
        return await withCheckedContinuation { continuation in
            let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
            let query = HKSampleQuery(
                sampleType: heartRateType,
                predicate: nil,
                limit: 1,
                sortDescriptors: [sort]
            ) { [weak self] _, samples, _ in
                guard let sample = (samples as? [HKQuantitySample])?.first,
                      let update = self?.makeUpdate(from: sample) else {
                    continuation.resume(returning: nil)
                    return
                }
                continuation.resume(returning: update)
            }
            healthStore.execute(query)
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
            healthStore.execute(query)
        }
    }

    func startHeartRateUpdates(onUpdate: @escaping (Update) -> Void) {
        stopHeartRateUpdates()
        guard let heartRateType else { return }

        self.onUpdate = onUpdate
        queryAnchor = nil

        observerQuery = HKObserverQuery(sampleType: heartRateType, predicate: nil) { [weak self] _, completionHandler, _ in
            self?.runAnchoredHeartRateQuery()
            completionHandler()
        }

        if let observerQuery {
            healthStore.execute(observerQuery)
        }

        runAnchoredHeartRateQuery()
    }

    func stopHeartRateUpdates() {
        if let observerQuery {
            healthStore.stop(observerQuery)
        }
        if let anchoredQuery {
            healthStore.stop(anchoredQuery)
        }
        observerQuery = nil
        anchoredQuery = nil
        queryAnchor = nil
        onUpdate = nil
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
        guard let onUpdate else { return }
        let quantitySamples = (samples as? [HKQuantitySample] ?? []).sorted { $0.endDate < $1.endDate }
        for sample in quantitySamples {
            if let update = makeUpdate(from: sample) {
                onUpdate(update)
            }
        }
    }

    private func makeUpdate(from sample: HKQuantitySample) -> Update? {
        let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
        let bpm = Int(round(sample.quantity.doubleValue(for: unit)))
        guard bpm > 0 else { return nil }

        let productType = sample.sourceRevision.productType?.lowercased() ?? ""
        let sourceName = sample.sourceRevision.source.name.lowercased()
        let deviceModel = sample.device?.model?.lowercased() ?? ""
        let isWatch = productType.contains("watch") || sourceName.contains("watch") || deviceModel.contains("watch")

        return Update(bpm: bpm, date: sample.endDate, isWatchSource: isWatch)
    }
}

private final class MotionCadenceService {
    struct Update {
        let movementScore: Double?
        let cadenceSPM: Double?
        let source: String
        let date: Date
    }

    private let pedometer = CMPedometer()
    private var onUpdate: ((Update) -> Void)?
    private var lastStepCount: Int?
    private var lastStepDate: Date?

    static func movementScore(from cadenceSPM: Double) -> Double {
        clamp((cadenceSPM - 30.0) / 150.0, lower: 0.0, upper: 1.0)
    }

    func startUpdates(onUpdate: @escaping (Update) -> Void) {
        stopUpdates()
        guard CMPedometer.isStepCountingAvailable() else { return }

        self.onUpdate = onUpdate
        pedometer.startUpdates(from: Date()) { [weak self] data, error in
            guard let self, error == nil, let data else { return }

            let now = data.endDate
            if let cadenceHz = data.currentCadence?.doubleValue, cadenceHz > 0 {
                let cadenceSPM = cadenceHz * 60.0
                let score = Self.movementScore(from: cadenceSPM)
                self.onUpdate?(Update(movementScore: score, cadenceSPM: cadenceSPM, source: "cadence", date: now))
            }

            let stepCount = data.numberOfSteps.intValue
            if let prevSteps = self.lastStepCount, let prevDate = self.lastStepDate {
                let deltaSteps = max(0, stepCount - prevSteps)
                let deltaSeconds = max(0.0, now.timeIntervalSince(prevDate))
                if deltaSeconds >= 0.5 {
                    let cadenceSPM = (Double(deltaSteps) / deltaSeconds) * 60.0
                    let score = Self.movementScore(from: cadenceSPM)
                    self.onUpdate?(Update(movementScore: score, cadenceSPM: cadenceSPM, source: "steps_fallback", date: now))
                }
            }

            self.lastStepCount = stepCount
            self.lastStepDate = now
        }
    }

    func stopUpdates() {
        pedometer.stopUpdates()
        onUpdate = nil
        lastStepCount = nil
        lastStepDate = nil
    }

    private static func clamp(_ value: Double, lower: Double, upper: Double) -> Double {
        guard value.isFinite else { return lower }
        return max(lower, min(upper, value))
    }
}

@MainActor
class WorkoutViewModel: ObservableObject {
    private let spotifyPromptPendingKey = "spotify_prompt_pending"
    private let spotifyPromptSeenKey = "spotify_prompt_seen"
    private let goodCoachWorkoutCountKey = "good_coach_workout_count"

    // MARK: - Published Properties

    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var breathAnalysis: BreathAnalysis?
    @Published var coachMessage: String?
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var voiceState: VoiceState = .idle
    @Published var currentPhase: WorkoutPhase = .intense
    @Published var activePersonality: CoachPersonality = .personalTrainer

    // MARK: - Coach Interaction State Machine

    @Published var coachInteractionState: CoachInteractionState = .passiveListening

    // MARK: - Computed Properties

    var currentPhaseDisplay: String {
        switch currentPhase {
        case .warmup:
            return L10n.warmup
        case .intense:
            return L10n.intense
        case .cooldown:
            return L10n.cooldown
        }
    }

    // MARK: - Continuous Coaching Properties

    @Published var isContinuousMode = false
    @Published var isPaused = false
    @Published var coachingInterval: TimeInterval = AppConfig.ContinuousCoaching.defaultInterval

    // MARK: - UI Properties (for new dashboard/profile screens)

    @Published var elapsedTime: TimeInterval = 0
    @Published var workoutHistory: [WorkoutRecord] = []
    @Published var userStats: UserStats = UserStats()

    // MARK: - Coachi UI State

    @Published var workoutState: WorkoutState = .idle
    @Published var showComplete: Bool = false
    @Published var selectedWarmupMinutes: Int = 2  // User picks: 0, 1, 2, 3, 5
    @Published var selectedWorkoutMode: WorkoutMode = .easyRun
    @Published var selectedEasyRunMinutes: Int = 30
    @Published var selectedIntervalTemplate: IntervalTemplate = .fourByFour
    @Published var coachingStyle: CoachingStyle = .normal
    @Published var useBreathingMicCues: Bool = true
    @Published var watchConnected: Bool = false
    @Published var hrSignalQuality: String = "poor"
    @Published var heartRate: Int?
    @Published var movementScore: Double?
    @Published var cadenceSPM: Double?
    @Published var movementSource: String = "none"
    @Published var movementState: String = "unknown"
    @Published var zoneStatus: String = "hr_unstable"
    @Published var targetZoneLabel: String = "Z2"
    @Published var targetHRLow: Int?
    @Published var targetHRHigh: Int?
    @Published var zoneScoreConfidence: String = "low"
    @Published var coachScore: Int = 82
    @Published var coachScoreLine: String = ""
    @Published var zoneTimeInTargetPct: Double?
    @Published var zoneOvershoots: Int = 0
    @Published var personalizationTip: String = ""
    @Published var recoveryLine: String = ""
    @Published var isSpotifyConnected: Bool = UserDefaults.standard.bool(forKey: "spotify_connected")
    @Published var showSpotifyConnectSheet: Bool = false

    // Computed: map voiceState to OrbState
    var orbState: OrbState {
        if workoutState == .paused { return .paused }
        switch voiceState {
        case .idle: return .idle
        case .listening: return .listening
        case .speaking: return .speaking
        }
    }

    // Computed: intensity from latest analysis
    var currentIntensity: IntensityLevel {
        breathAnalysis?.intensityLevel ?? .moderate
    }

    // Computed: phase progress (0.0 to 1.0)
    var phaseProgress: Double {
        let warmupSecs = configuredWarmupDuration
        let intenseSecs = configuredIntenseDuration
        let cooldownSecs = configuredCooldownDuration
        let phaseDuration: TimeInterval
        let phaseStart: TimeInterval

        switch currentPhase {
        case .warmup:
            phaseDuration = warmupSecs
            phaseStart = 0
        case .intense:
            phaseDuration = intenseSecs
            phaseStart = warmupSecs
        case .cooldown:
            phaseDuration = cooldownSecs
            phaseStart = warmupSecs + intenseSecs
        }

        guard phaseDuration > 0 else { return 0 }
        let phaseElapsed = max(0, elapsedTime - phaseStart)
        return min(phaseElapsed / phaseDuration, 1.0)
    }

    // Formatted elapsed time for Coachi display (MM:SS)
    var elapsedFormatted: String {
        let mins = Int(elapsedTime) / 60
        let secs = Int(elapsedTime) % 60
        return String(format: "%02d:%02d", mins, secs)
    }

    var coachScoreSummaryLine: String {
        if !coachScoreLine.isEmpty { return coachScoreLine }
        return formattedCoachScoreLine(score: coachScore)
    }

    var coachScoreHeadline: String {
        let clamped = max(0, min(100, coachScore))
        let band = scoreBand(for: clamped)
        if currentLanguage == "no" {
            return "CoachScore: \(clamped) — \(coachWorkPhraseNo(for: band))"
        }
        return "CoachScore: \(clamped) — \(coachWorkPhraseEn(for: band))"
    }

    var effortScore: Int {
        max(0, min(100, coachScore + 4))
    }

    var effortScoreSummaryLine: String {
        let score = effortScore
        if currentLanguage == "no" {
            return "Innsatsscore \(score) (\(scoreLabelNo(for: scoreBand(for: score))))"
        }
        return "Effort Score \(score) (\(scoreLabelEn(for: scoreBand(for: score))))"
    }

    var targetRangeText: String {
        guard let low = targetHRLow, let high = targetHRHigh else { return "--" }
        return "\(low)-\(high) bpm"
    }

    var zoneStatusDisplay: String {
        switch zoneStatus {
        case "in_zone":
            return "In zone"
        case "above_zone":
            return "Above zone"
        case "below_zone":
            return "Below zone"
        case "timing_control":
            return "Timing control"
        default:
            return "HR unstable"
        }
    }

    var hrIsReliable: Bool {
        watchConnected && hrSignalQuality == "good"
    }

    var hrQualityDisplay: String {
        hrIsReliable ? "HR good" : "HR limited"
    }

    var hrQualityHint: String {
        hrIsReliable ? "Zone cues are using heart rate." : "Using timing and movement fallback until HR stabilizes."
    }

    var sensorConnectionLabel: String {
        watchConnected ? "Apple Watch connected" : "Watch not connected"
    }

    var heartRateSampleAgeText: String {
        guard let date = latestHeartRateSampleDate else { return "--" }
        let age = max(0, Date().timeIntervalSince(date))
        return String(format: "%.1fs", age)
    }

    var movementSampleAgeText: String {
        guard let date = latestMovementSampleDate else { return "--" }
        let age = max(0, Date().timeIntervalSince(date))
        return String(format: "%.1fs", age)
    }

    var movementScoreDisplayText: String {
        guard let movementScore else { return "--" }
        return String(format: "%.2f", movementScore)
    }

    var restingHeartRateDisplayText: String {
        guard let value = storedRestingHR else { return "--" }
        return "\(value) bpm"
    }

    var hrMaxDisplayText: String {
        if let value = storedHRMax {
            return "\(value) bpm"
        }
        if let age = storedAge {
            let estimated = max(120, 220 - age)
            return "\(estimated) bpm (est.)"
        }
        return "--"
    }

    var sensorModeDisplayText: String {
        hrIsReliable ? "HR zone mode" : "Timing + movement fallback"
    }

    var movementStateDisplay: String {
        switch movementState {
        case "paused":
            return "Paused"
        case "moving":
            return "Moving"
        default:
            return "Unknown"
        }
    }

    var movementSourceDisplay: String {
        switch movementSource {
        case "cadence":
            return "Cadence"
        case "steps_fallback":
            return "Steps"
        case "movement_score":
            return "Movement"
        default:
            return "None"
        }
    }

    var cadenceDisplayText: String {
        guard let cadenceSPM else { return "--" }
        return "\(Int(round(cadenceSPM))) spm"
    }

    var scoreConfidenceNote: String? {
        switch zoneScoreConfidence {
        case "low":
            return "Score confidence is low due to HR signal gaps."
        case "partial":
            return "Score includes some periods with HR gaps."
        default:
            return nil
        }
    }

    var zoneWhyBullets: [String] {
        var items: [String] = []
        if let pct = zoneTimeInTargetPct {
            items.append(String(format: "%.0f%% in target zone", pct))
        }
        items.append("\(zoneOvershoots) overshoots above target")
        return items
    }

    var nextTimeAdvice: String {
        let trimmed = personalizationTip.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            return trimmed
        }
        if currentLanguage == "no" {
            return "Start 5 bpm lavere de første 10 minuttene."
        }
        return "Start 5 bpm lower the first 10 minutes."
    }

    // MARK: - Coachi Convenience Methods

    func startWorkout() {
        workoutState = .active
        showComplete = false
        coachScore = 82
        coachScoreLine = ""
        zoneStatus = "hr_unstable"
        targetZoneLabel = selectedWorkoutMode == .easyRun ? "Z2" : "Z4"
        targetHRLow = nil
        targetHRHigh = nil
        zoneScoreConfidence = "low"
        zoneTimeInTargetPct = nil
        zoneOvershoots = 0
        personalizationTip = ""
        recoveryLine = ""
        movementScore = nil
        cadenceSPM = nil
        movementSource = "none"
        movementState = "unknown"
        // If no warmup selected, start directly in intense phase
        if selectedWorkoutMode != .intervals && selectedWarmupMinutes == 0 {
            hasSkippedWarmup = true
        } else {
            hasSkippedWarmup = false
        }
        startContinuousWorkout()
    }

    func pauseWorkout() {
        workoutState = .paused
        pauseContinuousWorkout()
    }

    func resumeWorkout() {
        workoutState = .active
        resumeContinuousWorkout()
    }

    func stopWorkout() {
        stopContinuousWorkout()
        workoutState = .complete
        showComplete = true
    }

    func resetWorkout() {
        workoutState = .idle
        showComplete = false
        elapsedTime = 0
        coachMessage = nil
        breathAnalysis = nil
        coachScore = 82
        coachScoreLine = ""
        zoneStatus = "hr_unstable"
        targetHRLow = nil
        targetHRHigh = nil
        zoneScoreConfidence = "low"
        zoneTimeInTargetPct = nil
        zoneOvershoots = 0
        personalizationTip = ""
        recoveryLine = ""
        movementScore = nil
        cadenceSPM = nil
        movementSource = "none"
        movementState = "unknown"
    }

    func selectPersonality(_ persona: CoachPersonality) {
        switchPersonality(persona)
    }

    func openSpotify() {
        let appURL = URL(string: "spotify://")!
        let webURL = URL(string: "https://open.spotify.com")!

        if UIApplication.shared.canOpenURL(appURL) {
            UIApplication.shared.open(appURL)
        } else {
            UIApplication.shared.open(webURL)
        }
    }

    func handleSpotifyButtonTapped() {
        if isSpotifyConnected {
            openSpotify()
        } else {
            showSpotifyConnectSheet = true
        }
    }

    func presentSpotifyPromptIfNeeded() {
        let defaults = UserDefaults.standard
        let pending = defaults.bool(forKey: spotifyPromptPendingKey)
        let seen = defaults.bool(forKey: spotifyPromptSeenKey)
        if !pending || seen || isSpotifyConnected {
            if pending {
                defaults.set(false, forKey: spotifyPromptPendingKey)
            }
            return
        }

        defaults.set(false, forKey: spotifyPromptPendingKey)
        showSpotifyConnectSheet = true
    }

    func connectSpotifyFromSheet() {
        let defaults = UserDefaults.standard
        isSpotifyConnected = true
        defaults.set(true, forKey: "spotify_connected")
        defaults.set(true, forKey: spotifyPromptSeenKey)
        defaults.set(false, forKey: spotifyPromptPendingKey)
        showSpotifyConnectSheet = false
        openSpotify()
    }

    func dismissSpotifyConnectSheet() {
        let defaults = UserDefaults.standard
        defaults.set(true, forKey: spotifyPromptSeenKey)
        defaults.set(false, forKey: spotifyPromptPendingKey)
        showSpotifyConnectSheet = false
    }

    // Time-of-day greeting for the home screen
    var greetingText: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return L10n.goodMorning
        case 12..<17: return L10n.goodAfternoon
        case 17..<22: return L10n.goodEvening
        default: return L10n.goodNight
        }
    }

    // Current language, training level, and user name from UserDefaults
    private var currentLanguage: String {
        UserDefaults.standard.string(forKey: "app_language") ?? "en"
    }

    private var currentTrainingLevel: String {
        UserDefaults.standard.string(forKey: "training_level") ?? "beginner"
    }

    /// User's display name for personalized coaching (e.g., "Great work, Marius!")
    private var currentUserName: String {
        UserDefaults.standard.string(forKey: "user_display_name") ?? ""
    }

    private var storedHRMax: Int? {
        let value = UserDefaults.standard.integer(forKey: "hr_max")
        return value > 0 ? value : nil
    }

    private var storedRestingHR: Int? {
        let value = UserDefaults.standard.integer(forKey: "resting_hr")
        return value > 0 ? value : nil
    }

    private var storedAge: Int? {
        let value = UserDefaults.standard.integer(forKey: "user_age")
        return value > 0 ? value : nil
    }

    private var personalizationProfileId: String {
        let key = "personalization_profile_id"
        if let existing = UserDefaults.standard.string(forKey: key), !existing.isEmpty {
            return existing
        }
        let generated = "profile_\(UUID().uuidString.lowercased())"
        UserDefaults.standard.set(generated, forKey: key)
        return generated
    }

    private var configuredWarmupDuration: TimeInterval {
        if selectedWorkoutMode == .intervals {
            return 10 * 60
        }
        return TimeInterval(selectedWarmupMinutes * 60)
    }

    private var configuredIntenseDuration: TimeInterval {
        switch selectedWorkoutMode {
        case .easyRun:
            return TimeInterval(selectedEasyRunMinutes * 60)
        case .intervals:
            switch selectedIntervalTemplate {
            case .fourByFour:
                return TimeInterval((4 * (4 + 3)) * 60) // 4x (4 min work + 3 min recovery)
            case .eightByOne:
                return TimeInterval((8 * (1 + 1)) * 60) // 8x (1 min work + 1 min recovery)
            case .tenByThirtyThirty:
                return TimeInterval(10 * 60) // 10x (30/30) = 10 minutes total
            }
        case .standard:
            return AppConfig.intenseDuration
        }
    }

    private var configuredCooldownDuration: TimeInterval {
        if selectedWorkoutMode == .intervals {
            switch selectedIntervalTemplate {
            case .tenByThirtyThirty:
                return 6 * 60
            default:
                return 8 * 60
            }
        }
        return 5 * 60
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
    private var hasSkippedWarmup = false
    private var coachingTimer: Timer?
    private var sessionId: String?
    private var autoTimeoutTimer: Timer?
    private var elapsedTimeTimer: Timer?
    private var consecutiveChunkFailures: Int = 0
    private var lastAudioRecoveryAttempt: Date?
    private let healthKitService = HealthKitHeartRateService()
    private let motionCadenceService = MotionCadenceService()
    private var latestHeartRateSampleDate: Date?
    private var previousHeartRate: Int?
    private var previousHeartRateSampleDate: Date?
    private var latestMovementSampleDate: Date?
    private var latestMovementSource: String = "none"

    // Wake word for user-initiated speech ("Coach" / "Trener")
    let wakeWordManager = WakeWordManager()
    @Published var isWakeWordActive = false  // Show UI indicator when wake word heard

    // MARK: - Initialization

    init() {
        // Configure audio session for playback
        setupAudioSession()

        // Request speech recognition authorization for wake word
        Task {
            let authorized = await wakeWordManager.requestAuthorization()
            if authorized {
                print("✅ Speech recognition authorized for wake word")
            }
        }

        // Check backend connectivity on launch
        Task {
            await checkBackendHealth()
        }

        Task {
            await setupHealthSignals()
        }
        print("🔗 Backend URL: \(AppConfig.backendURL)")
    }

    private func setupAudioSession() {
        // NOTE: Don't set audio category here on init.
        // ContinuousRecordingManager will configure .playAndRecord when workout starts.
        // Setting .playback here and then .playAndRecord later causes error -10875.
        //
        // The audio session will be properly configured in:
        // - ContinuousRecordingManager.startContinuousRecording() for workouts
        // - playAudio() for standalone playback
        print("✅ Audio session will be configured on workout start")
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

    // MARK: - Talk to Coach (Conversational)

    @Published var isTalkingToCoach = false
    @Published var coachConversation: [(role: String, text: String)] = []

    func talkToCoach(message: String) {
        guard !isTalkingToCoach else { return }

        isTalkingToCoach = true
        coachConversation.append((role: "user", text: message))

        Task {
            do {
                print("💬 Talking to coach: '\(message)'")
                let response = try await apiService.talkToCoach(message: message)
                coachConversation.append((role: "coach", text: response.text))
                coachMessage = response.text
                print("🗣️ Coach replied: '\(response.text)'")

                // Play the response audio
                await playCoachAudio(response.audioURL)
            } catch {
                print("❌ Talk to coach failed: \(error.localizedDescription)")
                showErrorAlert("Could not reach coach: \(error.localizedDescription)")
            }
            isTalkingToCoach = false
        }
    }

    // MARK: - Skip Warmup

    func skipToIntensePhase() {
        guard isContinuousMode else { return }
        print("⏩ Skipping warmup — jumping to intense phase")
        hasSkippedWarmup = true
        currentPhase = .intense
    }

    // MARK: - Personality Switching

    func switchPersonality(_ personality: CoachPersonality) {
        guard personality != activePersonality else { return }
        print("🎭 Switching personality: \(activePersonality.rawValue) → \(personality.rawValue)")
        activePersonality = personality

        // Notify backend of persona switch mid-session
        if isContinuousMode, let sid = sessionId {
            Task {
                try? await apiService.switchPersona(
                    sessionId: sid,
                    persona: personality.rawValue
                )
            }
        }
    }

    // MARK: - Wake Word Speech-to-Coach

    /// Handle user utterance after wake word detection
    /// This is the user-initiated channel — short, contextual questions
    private func handleWakeWordUtterance(_ utterance: String) {
        guard isContinuousMode else { return }

        print("🗣️ User spoke to coach: '\(utterance)'")
        isWakeWordActive = true
        coachInteractionState = .commandMode

        sendUserMessageToCoach(utterance)
    }

    /// "Talk to Coach" button — manually triggered
    /// Starts a short speech capture session so the user can speak freely
    func talkToCoachButtonPressed() {
        guard isContinuousMode else { return }
        guard coachInteractionState == .passiveListening else { return }
        guard !wakeWordManager.isCapturingUtterance && !wakeWordManager.wakeWordDetected else {
            print("⚠️ Ignoring button capture while wake-word capture is active")
            return
        }

        print("🎤 Talk-to-coach button pressed — starting speech capture")
        coachInteractionState = .commandMode
        isWakeWordActive = true

        // Use speech recognition to capture what the user actually says
        wakeWordManager.captureUtterance(duration: 6.0) { [weak self] transcription in
            Task { @MainActor in
                guard let self = self else { return }

                let text = transcription.trimmingCharacters(in: .whitespacesAndNewlines)

                if text.isEmpty {
                    // No speech detected — fall back to a generic prompt
                    print("⚠️ No speech captured, using fallback prompt")
                    let fallback = self.currentLanguage == "no"
                        ? "Hvordan gjør jeg det?"
                        : "How am I doing?"
                    self.sendUserMessageToCoach(fallback)
                } else {
                    print("💬 Captured user speech: '\(text)'")
                    self.sendUserMessageToCoach(text)
                }
            }
        }
    }

    /// Common path: send a user message to the coach backend
    private func sendUserMessageToCoach(_ message: String) {
        coachInteractionState = .responding

        Task {
            do {
                let response = try await apiService.talkToCoachDuringWorkout(
                    message: message,
                    sessionId: sessionId ?? "",
                    phase: currentPhase.rawValue,
                    intensity: breathAnalysis?.intensity ?? "moderate",
                    persona: activePersonality.rawValue,
                    language: currentLanguage,
                    userName: currentUserName
                )

                coachMessage = response.text
                print("🗣️ Coach replied to user: '\(response.text)'")

                // Play the response audio
                await playCoachAudio(response.audioURL)
            } catch {
                print("❌ Coach talk failed: \(error.localizedDescription)")
            }

            // Return to passive listening
            isWakeWordActive = false
            coachInteractionState = .passiveListening
        }
    }

    // MARK: - Phase Auto-Detection

    private func autoDetectPhase() {
        // Auto-detect workout phase based on duration
        // Uses user-selected warmup time (0–40 minutes)
        // After warmup: intense for 15 minutes
        // After intense: cooldown

        guard let startTime = sessionStartTime else {
            currentPhase = selectedWarmupMinutes > 0 ? .warmup : .intense
            return
        }

        let duration = Date().timeIntervalSince(startTime)
        let warmupSeconds = configuredWarmupDuration
        let intenseEndSeconds = warmupSeconds + configuredIntenseDuration

        if warmupSeconds > 0 && duration < warmupSeconds && !hasSkippedWarmup {
            currentPhase = .warmup
        } else if duration < intenseEndSeconds {
            currentPhase = .intense
        } else {
            currentPhase = .cooldown
        }
    }

    private func estimatedCoachScore(for intensity: IntensityLevel) -> Int {
        switch intensity {
        case .calm:
            return 74
        case .moderate:
            return 82
        case .intense:
            return 88
        case .critical:
            return 68
        }
    }

    private enum ScoreBand {
        case strong
        case solid
        case mixed
        case needsControl
    }

    private func scoreBand(for score: Int) -> ScoreBand {
        if score >= 85 { return .strong }
        if score >= 70 { return .solid }
        if score >= 55 { return .mixed }
        return .needsControl
    }

    private func scoreLabelEn(for band: ScoreBand) -> String {
        switch band {
        case .strong:
            return "Strong"
        case .solid:
            return "Solid"
        case .mixed:
            return "Mixed"
        case .needsControl:
            return "Needs control"
        }
    }

    private func scoreLabelNo(for band: ScoreBand) -> String {
        switch band {
        case .strong:
            return "Sterk"
        case .solid:
            return "Solid"
        case .mixed:
            return "Blandet"
        case .needsControl:
            return "Trenger kontroll"
        }
    }

    private func coachWorkPhraseEn(for band: ScoreBand) -> String {
        switch band {
        case .strong:
            return "Strong work."
        case .solid:
            return "Solid work."
        case .mixed:
            return "Good effort."
        case .needsControl:
            return "Keep building."
        }
    }

    private func coachWorkPhraseNo(for band: ScoreBand) -> String {
        switch band {
        case .strong:
            return "Sterk jobb."
        case .solid:
            return "Solid jobb."
        case .mixed:
            return "Bra innsats."
        case .needsControl:
            return "Bygg videre."
        }
    }

    private func formattedCoachScoreLine(score: Int) -> String {
        let clampedScore = max(0, min(100, score))
        let band = scoreBand(for: clampedScore)
        if currentLanguage == "no" {
            return "CoachScore: \(clampedScore) — \(coachWorkPhraseNo(for: band))"
        }
        return "CoachScore: \(clampedScore) — \(coachWorkPhraseEn(for: band))"
    }

    private func applyExperienceProgression(durationSeconds: Int, finalCoachScore: Int) {
        guard durationSeconds >= AppConfig.Progression.minWorkoutSecondsForProgression else { return }
        guard finalCoachScore >= AppConfig.Progression.goodCoachScoreThreshold else { return }

        let defaults = UserDefaults.standard
        let previousGoodWorkouts = defaults.integer(forKey: goodCoachWorkoutCountKey)
        let newGoodWorkouts = previousGoodWorkouts + 1
        defaults.set(newGoodWorkouts, forKey: goodCoachWorkoutCountKey)

        let nextLevel = experienceLevel(forGoodWorkoutCount: newGoodWorkouts)
        let currentLevel = defaults.string(forKey: "training_level") ?? "beginner"
        if currentLevel != nextLevel {
            defaults.set(nextLevel, forKey: "training_level")
            print("⬆️ Experience level up: \(currentLevel) -> \(nextLevel) (\(newGoodWorkouts) good workouts)")
        } else {
            print("✅ Good workout counted (\(newGoodWorkouts) total)")
        }
    }

    private func experienceLevel(forGoodWorkoutCount count: Int) -> String {
        if count >= AppConfig.Progression.advancedAtGoodWorkouts {
            return "advanced"
        }
        if count >= AppConfig.Progression.intermediateAtGoodWorkouts {
            return "intermediate"
        }
        return "beginner"
    }

    // MARK: - API Communication

    func sendToBackend(audioURL: URL, phase: WorkoutPhase) async {
        isProcessing = true
        voiceState = .idle // Show processing state

        let tickStart = Date()
        do {
            // Send to coach endpoint
            let response = try await apiService.getCoachFeedback(audioURL, phase: phase)
            let responseTime = Date().timeIntervalSince(tickStart)

            // Update UI with response
            breathAnalysis = response.breathAnalysis
            coachMessage = response.text

            // Feed breath analysis to diagnostics
            AudioPipelineDiagnostics.shared.updateBreathAnalysis(
                response.breathAnalysis,
                responseTime: responseTime,
                chunkBytes: nil,
                chunkDur: nil,
                reason: nil
            )

            // Play voice and show speaking state
            voiceState = .speaking
            await downloadAndPlayVoice(audioURL: response.audioURL)

            // Return to idle after speaking
            voiceState = .idle

        } catch {
            showErrorAlert("Failed to analyze: \(error.localizedDescription)")
            AudioPipelineDiagnostics.shared.recordBreathAnalysisError(error.localizedDescription)
            voiceState = .idle
        }

        isProcessing = false
    }

    private func downloadAndPlayVoice(audioURL: String) async {
        do {
            let audioData = try await apiService.downloadVoiceAudio(from: audioURL)

            // Detect file extension from URL (backend returns .mp3 from ElevenLabs)
            let ext = URL(string: audioURL)?.pathExtension ?? "mp3"
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("coach_voice.\(ext.isEmpty ? "mp3" : ext)")
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

            // Configure audio session for playback
            // If already in .playAndRecord (during workout), keep it - that mode supports playback
            // Otherwise, set .playback mode for standalone audio playback
            let session = AVAudioSession.sharedInstance()
            if session.category != .playAndRecord {
                // Deactivate first to allow category change (prevents error -10875)
                try? session.setActive(false)
                try session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
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

    // MARK: - HealthKit HR Signals

    private func setupHealthSignals() async {
        guard HKHealthStore.isHealthDataAvailable() else {
            watchConnected = false
            hrSignalQuality = "poor"
            return
        }

        let authorized = await healthKitService.requestAuthorization()
        guard authorized else {
            watchConnected = false
            hrSignalQuality = "poor"
            return
        }

        if let resting = await healthKitService.fetchLatestRestingHeartRate() {
            UserDefaults.standard.set(resting, forKey: "resting_hr")
        }

        if let snapshot = await healthKitService.fetchLatestHeartRateSnapshot() {
            applyHeartRateUpdate(snapshot)
        }
    }

    func refreshHealthSensors() {
        Task {
            await setupHealthSignals()
        }
    }

    private func startHealthMonitoring() {
        healthKitService.startHeartRateUpdates { [weak self] update in
            Task { @MainActor in
                self?.applyHeartRateUpdate(update)
            }
        }
    }

    private func stopHealthMonitoring() {
        healthKitService.stopHeartRateUpdates()
    }

    private func startMotionMonitoring() {
        motionCadenceService.startUpdates { [weak self] update in
            Task { @MainActor in
                self?.applyMotionUpdate(update)
            }
        }
    }

    private func stopMotionMonitoring() {
        motionCadenceService.stopUpdates()
    }

    private func applyHeartRateUpdate(_ update: HealthKitHeartRateService.Update) {
        heartRate = update.bpm
        latestHeartRateSampleDate = update.date

        let ageSeconds = max(0, Date().timeIntervalSince(update.date))
        let stale = ageSeconds > AppConfig.Health.hrStaleThresholdSeconds

        var quality = stale ? "poor" : "good"
        if let prev = previousHeartRate, let prevDate = previousHeartRateSampleDate {
            let gap = abs(update.date.timeIntervalSince(prevDate))
            if gap <= AppConfig.Health.hrPoorSpikeWindowSeconds &&
                abs(update.bpm - prev) > AppConfig.Health.hrPoorSpikeDeltaBPM {
                quality = "poor"
            }
        }

        watchConnected = update.isWatchSource && !stale
        hrSignalQuality = quality
        previousHeartRate = update.bpm
        previousHeartRateSampleDate = update.date
    }

    private var hrSampleAgeSecondsForRequest: Double? {
        guard let sampleDate = latestHeartRateSampleDate else { return nil }
        return max(0, Date().timeIntervalSince(sampleDate))
    }

    private func refreshHeartRateSignalQualityFromAge() {
        guard let age = hrSampleAgeSecondsForRequest else {
            watchConnected = false
            hrSignalQuality = "poor"
            return
        }
        if age > AppConfig.Health.hrStaleThresholdSeconds {
            watchConnected = false
            hrSignalQuality = "poor"
        }
    }

    private func applyMotionUpdate(_ update: MotionCadenceService.Update) {
        movementScore = update.movementScore
        cadenceSPM = update.cadenceSPM
        movementSource = update.source
        latestMovementSource = update.source
        latestMovementSampleDate = update.date
    }

    private func refreshMotionSignalFromAge() {
        guard let sampleDate = latestMovementSampleDate else {
            movementScore = nil
            cadenceSPM = nil
            movementSource = "none"
            latestMovementSource = "none"
            return
        }

        let age = max(0.0, Date().timeIntervalSince(sampleDate))
        if age > AppConfig.Motion.staleThresholdSeconds {
            movementScore = nil
            cadenceSPM = nil
            movementSource = "none"
            latestMovementSource = "none"
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
            consecutiveChunkFailures = 0
            lastAudioRecoveryAttempt = nil

            // Start live heart-rate monitoring from HealthKit/Watch
            startHealthMonitoring()
            startMotionMonitoring()

            // Start 1-second timer to update elapsed time (drives the timer ring UI)
            elapsedTimeTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
                Task { @MainActor in
                    guard let self = self, let start = self.sessionStartTime else { return }
                    self.elapsedTime = Date().timeIntervalSince(start)
                }
            }

            // Connect wake word manager to audio stream
            continuousRecordingManager.onAudioBuffer = { [weak self] buffer in
                self?.wakeWordManager.feedAudioBuffer(buffer)
            }

            // Start wake word listening
            wakeWordManager.updateLanguage()
            wakeWordManager.startListening(audioEngine: continuousRecordingManager.engine) { [weak self] utterance in
                Task { @MainActor in
                    self?.handleWakeWordUtterance(utterance)
                }
            }

            // Play welcome message, then start coaching loop after a delay
            // This avoids the first tick picking up speaker audio from the welcome message
            Task {
                await playWelcomeMessage()
                try? await Task.sleep(nanoseconds: 2_000_000_000)
                await MainActor.run {
                    scheduleNextTick()
                }
            }

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

    func pauseContinuousWorkout() {
        guard isContinuousMode && !isPaused else { return }

        print("⏸️ Pausing continuous workout")

        isPaused = true

        // Pause recording
        continuousRecordingManager.pauseRecording()

        // Pause wake word listening
        wakeWordManager.stopListening()

        // Pause timers (but don't invalidate - we'll resume them)
        coachingTimer?.invalidate()
        coachingTimer = nil
        elapsedTimeTimer?.invalidate()
        elapsedTimeTimer = nil

        voiceState = .idle
        consecutiveChunkFailures = 0

        print("✅ Workout paused")
    }

    func resumeContinuousWorkout() {
        guard isContinuousMode && isPaused else { return }

        print("▶️ Resuming continuous workout")

        isPaused = false

        // Resume recording
        do {
            try continuousRecordingManager.resumeRecording()
        } catch {
            showErrorAlert("Failed to resume recording: \(error.localizedDescription)")
            return
        }

        voiceState = .listening

        // Resume wake word listening
        wakeWordManager.startListening(audioEngine: continuousRecordingManager.engine) { [weak self] utterance in
            Task { @MainActor in
                self?.handleWakeWordUtterance(utterance)
            }
        }

        // Restart elapsed time timer
        elapsedTimeTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self = self, let start = self.sessionStartTime else { return }
                self.elapsedTime = Date().timeIntervalSince(start)
            }
        }

        // Resume coaching loop
        consecutiveChunkFailures = 0
        scheduleNextTick()

        print("✅ Workout resumed")
    }

    func togglePause() {
        if isPaused {
            resumeContinuousWorkout()
        } else {
            pauseContinuousWorkout()
        }
    }

    func stopContinuousWorkout() {
        guard isContinuousMode else { return }

        print("⏹️ Stopping continuous workout")

        // Stop wake word listening
        wakeWordManager.stopListening()
        continuousRecordingManager.onAudioBuffer = nil

        // Stop recording
        continuousRecordingManager.stopContinuousRecording()
        stopHealthMonitoring()
        stopMotionMonitoring()

        // Cancel timers
        coachingTimer?.invalidate()
        coachingTimer = nil
        autoTimeoutTimer?.invalidate()
        autoTimeoutTimer = nil
        elapsedTimeTimer?.invalidate()
        elapsedTimeTimer = nil

        // Update state
        isContinuousMode = false
        isPaused = false
        voiceState = .idle
        isWakeWordActive = false
        sessionId = nil
        hasSkippedWarmup = false
        consecutiveChunkFailures = 0
        lastAudioRecoveryAttempt = nil
        movementScore = nil
        cadenceSPM = nil
        movementSource = "none"
        movementState = "unknown"
        latestMovementSource = "none"
        latestMovementSampleDate = nil

        // Update final workout duration and save to history
        var finalDurationSeconds: Int?
        if let startTime = sessionStartTime {
            workoutDuration = Date().timeIntervalSince(startTime)
            print("📊 Workout completed: \(Int(workoutDuration)) seconds")
            finalDurationSeconds = Int(workoutDuration)

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

        if coachScoreLine.isEmpty {
            coachScore = estimatedCoachScore(for: breathAnalysis?.intensityLevel ?? .moderate)
            coachScoreLine = formattedCoachScoreLine(score: coachScore)
        }

        if let duration = finalDurationSeconds {
            applyExperienceProgression(durationSeconds: duration, finalCoachScore: coachScore)
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

        print("🔄 Coaching tick #\(AudioPipelineDiagnostics.shared.breathAnalysisCount + 1) at \(Int(workoutDuration))s | phase: \(currentPhase.rawValue) | interval: \(Int(coachingInterval))s")

        // 1. Get latest chunk WITHOUT stopping recording
        guard let audioChunk = continuousRecordingManager.getLatestChunk(
            duration: AppConfig.ContinuousCoaching.chunkDuration
        ) else {
            print("⚠️ No audio chunk available, retrying next tick")
            AudioPipelineDiagnostics.shared.recordBreathAnalysisError("No audio chunk available (buffer empty?)")
            consecutiveChunkFailures += 1
            attemptAudioPipelineRecoveryIfNeeded(reason: "no_chunk")
            scheduleNextTick()
            return
        }

        print("🎤 Coaching tick: \(Int(workoutDuration))s, phase: \(currentPhase.rawValue)")

        // Measure chunk size for diagnostics
        let chunkBytes = (try? FileManager.default.attributesOfItem(atPath: audioChunk.path)[.size] as? Int) ?? 0

        // Skip invalid/too-small chunks
        if chunkBytes < AppConfig.ContinuousCoaching.minChunkBytes {
            let msg = "Chunk too small (\(chunkBytes) bytes) — skipping"
            print("⚠️ \(msg)")
            AudioPipelineDiagnostics.shared.recordBreathAnalysisError(msg)
            consecutiveChunkFailures += 1
            attemptAudioPipelineRecoveryIfNeeded(reason: "chunk_too_small")
            scheduleNextTick()
            return
        }

        // Chunk extraction recovered.
        consecutiveChunkFailures = 0

        // 2. Send to backend (background task)
        Task {
            let tickStart = Date()
            do {
                refreshHeartRateSignalQualityFromAge()
                refreshMotionSignalFromAge()
                let tickHeartRate = heartRate
                let tickSampleAge = hrSampleAgeSecondsForRequest
                let tickQuality = (tickHeartRate != nil && watchConnected) ? "good" : "poor"
                let tickMovementScore = movementScore
                let tickCadenceSPM = cadenceSPM
                let tickMovementSource = (tickMovementScore != nil || tickCadenceSPM != nil) ? latestMovementSource : "none"
                hrSignalQuality = tickQuality
                let response = try await apiService.getContinuousCoachFeedback(
                    audioChunk,
                    sessionId: sessionId ?? "",
                    phase: currentPhase,
                    lastCoaching: coachMessage ?? "",
                    elapsedSeconds: Int(workoutDuration),
                    language: currentLanguage,
                    trainingLevel: currentTrainingLevel,
                    persona: activePersonality.rawValue,
                    userName: currentUserName,
                    workoutMode: selectedWorkoutMode,
                    coachingStyle: coachingStyle,
                    intervalTemplate: selectedIntervalTemplate,
                    userProfileId: personalizationProfileId,
                    heartRate: tickHeartRate,
                    hrSampleAgeSeconds: tickSampleAge,
                    hrQuality: tickQuality,
                    hrConfidence: tickQuality == "good" ? 0.9 : 0.2,
                    watchConnected: watchConnected,
                    watchStatus: watchConnected ? "connected" : "disconnected",
                    movementScore: tickMovementScore,
                    cadenceSPM: tickCadenceSPM,
                    movementSource: tickMovementSource,
                    hrMax: storedHRMax,
                    restingHR: storedRestingHR,
                    age: storedAge
                )

                let responseTime = Date().timeIntervalSince(tickStart)

                // 3. Update metrics silently (NO UI state change)
                breathAnalysis = response.breathAnalysis
                coachMessage = response.text
                if let score = response.coachScore {
                    coachScore = max(0, min(100, score))
                } else {
                    coachScore = estimatedCoachScore(for: response.breathAnalysis.intensityLevel)
                }
                if let line = response.coachScoreLine, !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    coachScoreLine = line
                } else {
                    coachScoreLine = formattedCoachScoreLine(score: coachScore)
                }
                if let responseStyle = response.coachingStyle,
                   let parsedStyle = CoachingStyle(rawValue: responseStyle) {
                    coachingStyle = parsedStyle
                }
                if let zone = response.zoneStatus {
                    zoneStatus = zone
                }
                if let hr = response.heartRate {
                    heartRate = hr
                }
                if let label = response.targetZoneLabel {
                    targetZoneLabel = label
                }
                targetHRLow = response.targetHRLow
                targetHRHigh = response.targetHRHigh
                if let quality = response.hrQuality {
                    hrSignalQuality = quality
                }
                if let score = response.movementScore {
                    movementScore = score
                }
                if let cadence = response.cadenceSPM {
                    cadenceSPM = cadence
                }
                if let source = response.movementSource, !source.isEmpty {
                    movementSource = source
                    latestMovementSource = source
                }
                if let state = response.movementState, !state.isEmpty {
                    movementState = state
                }
                if let confidence = response.zoneScoreConfidence {
                    zoneScoreConfidence = confidence
                }
                zoneTimeInTargetPct = response.zoneTimeInTargetPct
                zoneOvershoots = response.zoneOvershoots ?? zoneOvershoots
                if let tip = response.personalizationTip, !tip.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    personalizationTip = tip
                }
                if let line = response.recoveryLine, !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    recoveryLine = line
                }

                // Feed breath analysis + coach decision to diagnostics panel
                AudioPipelineDiagnostics.shared.updateBreathAnalysis(
                    response.breathAnalysis,
                    responseTime: responseTime,
                    chunkBytes: chunkBytes,
                    chunkDur: AppConfig.ContinuousCoaching.chunkDuration,
                    reason: response.reason,
                    shouldSpeak: response.shouldSpeak,
                    coachText: response.text
                )

                print("📊 Backend response: should_speak=\(response.shouldSpeak), has_audio=\(response.audioURL != nil), text_len=\(response.text.count), wait=\(response.waitSeconds)s, reason=\(response.reason ?? "none"), brain=\(response.brainProvider ?? "unknown")/\(response.brainSource ?? "unknown")/\(response.brainStatus ?? "unknown")")

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
                // Network/decode error: skip this cycle, continue next
                print("❌ Coaching cycle failed: \(error)")
                // Show full error (not just localizedDescription) to catch JSON decode details
                let errorDetail: String
                if let decodingError = error as? DecodingError {
                    switch decodingError {
                    case .keyNotFound(let key, _):
                        errorDetail = "JSON missing key: \(key.stringValue)"
                    case .typeMismatch(let type, let context):
                        errorDetail = "JSON type mismatch: expected \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: "."))"
                    case .valueNotFound(let type, let context):
                        errorDetail = "JSON null value: \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: "."))"
                    case .dataCorrupted(let context):
                        errorDetail = "JSON corrupted: \(context.debugDescription)"
                    @unknown default:
                        errorDetail = "JSON decode: \(error.localizedDescription)"
                    }
                } else {
                    errorDetail = error.localizedDescription
                }
                AudioPipelineDiagnostics.shared.recordBreathAnalysisError(errorDetail)
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

    private func attemptAudioPipelineRecoveryIfNeeded(reason: String) {
        // Recover only after repeated failures; avoid restart thrashing.
        let failureThreshold = 3
        let minRecoveryGap: TimeInterval = 10

        guard consecutiveChunkFailures >= failureThreshold else { return }

        if let last = lastAudioRecoveryAttempt,
           Date().timeIntervalSince(last) < minRecoveryGap {
            return
        }

        lastAudioRecoveryAttempt = Date()
        print("🛠️ Recovering audio pipeline (\(reason), failures=\(consecutiveChunkFailures))")

        wakeWordManager.stopListening()
        continuousRecordingManager.stopContinuousRecording()

        do {
            try continuousRecordingManager.startContinuousRecording()

            // Reconnect wake-word feed to the restarted recorder.
            continuousRecordingManager.onAudioBuffer = { [weak self] buffer in
                self?.wakeWordManager.feedAudioBuffer(buffer)
            }

            wakeWordManager.updateLanguage()
            wakeWordManager.startListening(audioEngine: continuousRecordingManager.engine) { [weak self] utterance in
                Task { @MainActor in
                    self?.handleWakeWordUtterance(utterance)
                }
            }

            consecutiveChunkFailures = 0
            print("✅ Audio pipeline recovered")
        } catch {
            print("❌ Audio pipeline recovery failed: \(error.localizedDescription)")
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
            let welcome = try await apiService.getWelcomeMessage(language: currentLanguage, persona: activePersonality.rawValue, userName: currentUserName)
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

            // Detect file extension from URL (backend returns .mp3 from ElevenLabs)
            let ext = URL(string: audioURL)?.pathExtension ?? "mp3"
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("continuous_coach_\(Date().timeIntervalSince1970).\(ext.isEmpty ? "mp3" : ext)")
            try audioData.write(to: tempURL)

            // Play audio (NO state change - stays .listening)
            await playAudio(from: tempURL)

        } catch {
            print("Failed to download/play coach audio: \(error.localizedDescription)")
            // Don't show error to user - just log and continue
        }
    }
}
