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

private enum TalkTriggerSource: String {
    case wakeWord = "wake_word"
    case button = "button"
}

struct SpeechTranscriptEntry: Identifiable {
    let id = UUID()
    let timestamp: Date
    let utteranceId: String
    let eventType: String
    let source: String
    let text: String?
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
    private struct WorkoutSessionPlan {
        let workoutMode: WorkoutMode
        let easyRunSessionMode: EasyRunSessionMode
        let warmupSeconds: Int
        let mainSeconds: Int
        let cooldownSeconds: Int
        let intervalRepeats: Int?
        let intervalWorkSeconds: Int?
        let intervalRecoverySeconds: Int?

        var isEasyRunFreeRun: Bool {
            workoutMode == .easyRun && easyRunSessionMode == .freeRun
        }
    }

    private let spotifyPromptPendingKey = "spotify_prompt_pending"
    private let spotifyPromptSeenKey = "spotify_prompt_seen"
    private let goodCoachWorkoutCountKey = "good_coach_workout_count"
    private let coachScoreHistoryKey = "coach_score_history_v1"
    private let lastCoachScoreKey = "last_real_coach_score"
    private let maxCoachScoreHistoryCount = 42
    private let workoutIntensityPreferenceKey = "workout_intensity_preference"
    private let breathAnalysisEnabledKey = "breath_analysis_enabled"
    private let easyRunSessionModePreferenceKey = "easy_run_session_mode"

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
    @Published var selectedWarmupMinutes: Int = 2
    @Published var selectedWorkoutMode: WorkoutMode = .easyRun
    @Published var selectedEasyRunSessionMode: EasyRunSessionMode = .timed {
        didSet {
            UserDefaults.standard.set(selectedEasyRunSessionMode.rawValue, forKey: easyRunSessionModePreferenceKey)
            applyEasyRunSessionModeSelection(selectedEasyRunSessionMode)
        }
    }
    @Published var selectedEasyRunMinutes: Int = 30
    @Published var selectedIntervalSets: Int = 6
    @Published var selectedIntervalWorkMinutes: Int = 2
    @Published var selectedIntervalBreakMinutes: Int = 1
    @Published var selectedIntervalTemplate: IntervalTemplate = .fourByFour
    @Published var coachingStyle: CoachingStyle = .medium {
        didSet {
            UserDefaults.standard.set(coachingStyle.rawValue, forKey: workoutIntensityPreferenceKey)
        }
    }
    @Published var useBreathingMicCues: Bool = true {
        didSet {
            UserDefaults.standard.set(useBreathingMicCues, forKey: breathAnalysisEnabledKey)
        }
    }
    @Published var watchSessionReachable: Bool = false
    @Published var isWaitingForWatchStart: Bool = false
    @Published var watchStartStatusLine: String?
    @Published var watchConnected: Bool = false
    @Published var bleConnected: Bool = false
    @Published var hrSignalQuality: String = "poor"
    @Published private(set) var hrSource: HRSource = .none
    @Published var liveHRBannerText: String?
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
    @Published var coachScore: Int = 0
    @Published var coachScoreLine: String = ""
    @Published private(set) var hasAuthoritativeCoachScore: Bool = false
    @Published var coachScoreV2: Int?
    @Published var coachScoreComponents: CoachScoreComponents?
    @Published var coachScoreCapReasonCodes: [String] = []
    @Published var coachScoreCapApplied: Int?
    @Published var coachScoreCapAppliedReason: String?
    @Published var coachScoreHRValidMainSetSeconds: Double?
    @Published var coachScoreZoneValidMainSetSeconds: Double?
    @Published var coachScoreZoneCompliance: Double?
    @Published var breathAvailableReliable: Bool = false
    @Published private(set) var coachScoreHistory: [CoachScoreRecord] = []
    @Published private(set) var lastPersistedCoachScore: Int = 0
    @Published var zoneTimeInTargetPct: Double?
    @Published var zoneOvershoots: Int = 0
    @Published var workoutContextSummary: WorkoutContextSummary?
    @Published var personalizationTip: String = ""
    @Published var recoveryLine: String = ""
    @Published var isSpotifyConnected: Bool = UserDefaults.standard.bool(forKey: "spotify_connected")
    @Published var showSpotifyConnectSheet: Bool = false
    @Published private(set) var speechTranscript: [SpeechTranscriptEntry] = []
    private var timedEasyRunWarmupBackup: Int = 2
    private var timedEasyRunDurationBackup: Int = 30
    private var activeSessionPlan: WorkoutSessionPlan?

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

    private var effectiveSessionPlan: WorkoutSessionPlan {
        activeSessionPlan ?? buildSessionPlanFromSelections()
    }

    private var runtimeWorkoutMode: WorkoutMode {
        effectiveSessionPlan.workoutMode
    }

    private var runtimeEasyRunSessionMode: EasyRunSessionMode {
        effectiveSessionPlan.easyRunSessionMode
    }

    var isEasyRunFreeRunActive: Bool {
        runtimeWorkoutMode == .easyRun && runtimeEasyRunSessionMode == .freeRun
    }

    var phaseCountdownPrimaryText: String {
        if isEasyRunFreeRunActive && (resolvedPhaseKey == "main" || resolvedPhaseKey == "work") {
            return currentLanguage == "no"
                ? "Total tid: \(elapsedFormatted)"
                : "Total time: \(elapsedFormatted)"
        }

        let remainingText = formatPhaseRemaining(seconds: currentPhaseRemainingSeconds)
        let phaseKey = resolvedPhaseKey

        switch phaseKey {
        case "warmup":
            return currentLanguage == "no"
                ? "Oppvarming – \(remainingText) igjen"
                : "Warmup – \(remainingText) remaining"
        case "work":
            if runtimeWorkoutMode == .intervals {
                if let (repIndex, repsTotal) = intervalRepProgress {
                    return currentLanguage == "no"
                        ? "Drag \(repIndex) / \(repsTotal) – \(remainingText) igjen"
                        : "Interval \(repIndex) / \(repsTotal) – \(remainingText) remaining"
                }
                return currentLanguage == "no"
                    ? "Intervall – \(remainingText) igjen"
                    : "Interval – \(remainingText) remaining"
            }
            return currentLanguage == "no"
                ? "Hoveddel – \(remainingText) igjen"
                : "Main set – \(remainingText) remaining"
        case "recovery":
            if runtimeWorkoutMode == .intervals {
                return currentLanguage == "no"
                    ? "Pause – neste drag om \(remainingText)"
                    : "Recovery – next interval in \(remainingText)"
            }
            return currentLanguage == "no"
                ? "Hoveddel – \(remainingText) igjen"
                : "Main set – \(remainingText) remaining"
        case "cooldown":
            return currentLanguage == "no"
                ? "Nedtrapping – \(remainingText) igjen"
                : "Cooldown – \(remainingText) remaining"
        case "main":
            return currentLanguage == "no"
                ? "Hoveddel – \(remainingText) igjen"
                : "Main set – \(remainingText) remaining"
        default:
            return currentLanguage == "no"
                ? "Økt – \(remainingText) igjen"
                : "Workout – \(remainingText) remaining"
        }
    }

    var phaseCountdownSecondaryText: String? {
        guard runtimeWorkoutMode == .intervals else { return nil }
        guard let summary = workoutContextSummary else { return nil }

        guard let repsTotal = summary.repsTotal, repsTotal > 0 else { return nil }
        let repIndex = max(1, summary.repIndex ?? 1)
        let repsLeft = max(0, summary.repsRemainingIncludingCurrent ?? (repsTotal - repIndex + 1))

        if currentLanguage == "no" {
            return "Drag \(min(repIndex, repsTotal))/\(repsTotal) · \(repsLeft) igjen"
        }
        return "Interval \(min(repIndex, repsTotal))/\(repsTotal) · \(repsLeft) left"
    }

    var coachScoreSummaryLine: String {
        if !coachScoreLine.isEmpty { return coachScoreLine }
        return formattedCoachScoreLine(score: coachScore)
    }

    var coachScoreCapHint: String? {
        let sensorHintNo = "Koble til klokke eller aktiver pusteanalyse for mer nøyaktig score."
        let sensorHintEn = "Connect watch or enable breath analysis for more accurate scoring."
        let sensorHint = L10n.current == .no ? sensorHintNo : sensorHintEn

        if let reason = coachScoreCapAppliedReason {
            switch reason {
            case "HR_MISSING":
                return sensorHint
            case "ZONE_MISSING_OR_UNENFORCED":
                return sensorHint
            case "ZONE_FAIL":
                return L10n.current == .no ? "Du var for kort tid i målsonen." : "You spent too little time in the target zone."
            case "BREATH_MISSING":
                return sensorHint
            case "BREATH_FAIL":
                return L10n.current == .no ? "Pustesignalet var svakt i denne økten." : "Breath signal quality was weak in this workout."
            case "NO_BREATH_STRONG_HR_REQUIRED", "DURATION_ONLY_CAP":
                return sensorHint
            case "SHORT_DURATION":
                return L10n.current == .no ? "Økter under 20 min får begrenset score." : "Workouts under 20 min have a score cap."
            default:
                break
            }
        }

        if let components = coachScoreComponents {
            let zoneAvailable = components.zoneAvailable ?? false
            let breathReliable = components.breathAvailableReliable ?? false
            if !zoneAvailable || !breathReliable {
                return sensorHint
            }
        }

        return nil
    }

    var coachScoreHeadline: String {
        let clamped = max(0, min(100, coachScore))
        let band = scoreBand(for: clamped)
        if currentLanguage == "no" {
            return "Coach score: \(clamped) — \(coachWorkPhraseNo(for: band))"
        }
        return "Coach score: \(clamped) — \(coachWorkPhraseEn(for: band))"
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

    var homeCoachScore: Int {
        if let latest = coachScoreHistory.first {
            return latest.score
        }
        return max(0, min(100, lastPersistedCoachScore))
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
        (hrSource == .wc || hrSource == .ble) && hrSignalQuality == HRQuality.good.rawValue
    }

    var hrQualityDisplay: String {
        hrIsReliable ? "HR good" : "HR limited"
    }

    var watchBPMDisplayText: String {
        guard (hrSource == .wc || hrSource == .ble || hrSource == .hk),
              let value = heartRate, value > 0 else { return "0 BPM" }
        return "\(value) BPM"
    }

    var launchStartButtonTitle: String {
        if watchSessionReachable {
            return currentLanguage == "no" ? "Start på Watch" : "Start on Watch"
        }
        return currentLanguage == "no" ? "Start" : "Start"
    }

    var launchStartSubtext: String {
        if watchSessionReachable {
            return currentLanguage == "no" ? "Live puls + sonecoaching" : "Live HR + zone coaching"
        }
        if bleConnected {
            return currentLanguage == "no" ? "Live puls via Bluetooth-sensor" : "Live HR via Bluetooth sensor"
        }
        return currentLanguage == "no" ? "Ingen live puls (du kan fortsatt coache)" : "No live HR (you can still coach)"
    }

    var canInitiateWorkoutStart: Bool {
        hasValidAuthToken()
    }

    var launchAuthRequirementText: String? {
        guard !canInitiateWorkoutStart else { return nil }
        return currentLanguage == "no"
            ? "Logg inn for å starte coaching."
            : "Sign in to start coaching."
    }

    var watchReachabilityHelperText: String? {
        guard !watchSessionReachable, phoneWCManager.isPaired, phoneWCManager.isWatchAppInstalled else {
            return nil
        }
        return currentLanguage == "no"
            ? "Åpne TreningsCoach på Watch for å aktivere live puls"
            : "Open TreningsCoach on Watch to enable live HR"
    }

    var isCoachTalkActive: Bool {
        coachInteractionState == .commandMode ||
            coachInteractionState == .responding ||
            isWakeWordActive ||
            isTalkingToCoach
    }

    /// True only while user speech is actively being captured.
    /// Used for mic pulse/haptics so feedback stops when coach is just responding.
    var isCoachCapturingSpeech: Bool {
        coachInteractionState == .commandMode || isWakeWordActive
    }

    var hrQualityHint: String {
        hrIsReliable ? "Zone cues are using heart rate." : "Using timing and movement fallback until HR stabilizes."
    }

    var sensorConnectionLabel: String {
        switch hrSource {
        case .wc:
            return "Apple Watch live"
        case .ble:
            return "Bluetooth HR live"
        case .hk:
            return "HealthKit fallback"
        case .none:
            return "No live HR source"
        }
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
        hrIsReliable ? "Live HR zone mode" : "Timing + movement fallback"
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
        guard hasValidAuthToken() else {
            clearWatchStartPendingState()
            activeWatchRequestId = nil
            watchStartStatusLine = launchAuthRequirementText
            workoutState = .idle
            let message = currentLanguage == "no"
                ? "Du må logge inn for å starte coaching."
                : "You must sign in to start coaching."
            showErrorAlert(message)
            return
        }

        activeSessionPlan = buildSessionPlanFromSelections()
        clearWatchStartPendingState()
        watchStartStatusLine = nil
        workoutState = .idle
        showComplete = false
        coachScore = 0
        coachScoreLine = ""
        hasAuthoritativeCoachScore = false
        coachScoreV2 = nil
        coachScoreComponents = nil
        coachScoreCapReasonCodes = []
        coachScoreCapApplied = nil
        coachScoreCapAppliedReason = nil
        coachScoreHRValidMainSetSeconds = nil
        coachScoreZoneValidMainSetSeconds = nil
        coachScoreZoneCompliance = nil
        breathAvailableReliable = false
        zoneStatus = "hr_unstable"
        targetZoneLabel = runtimeWorkoutMode == .easyRun ? "Z2" : "Z4"
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
        workoutContextSummary = nil
        workoutContextSummaryReceivedAt = nil
        // If no warmup selected, start directly in intense phase
        if configuredWarmupDuration == 0 {
            hasSkippedWarmup = true
        } else {
            hasSkippedWarmup = false
        }
        requestWatchStartOrFallback()
    }

    func pauseWorkout() {
        workoutState = .paused
        pauseContinuousWorkout()
    }

    func resumeWorkout() {
        workoutState = .active
        resumeContinuousWorkout()
    }

    func stopWorkout(notifyWatch: Bool = true) {
        if notifyWatch {
            let requestID = activeWatchRequestId ?? pendingWatchRequestId ?? UUID().uuidString
            phoneWCManager.sendWorkoutStopped(timestamp: Date().timeIntervalSince1970, requestID: requestID)
        }
        stopContinuousWorkout()
        workoutState = .complete
        showComplete = true
    }

    func resetWorkout() {
        clearWatchStartPendingState()
        activeWatchRequestId = nil
        watchStartStatusLine = nil
        workoutState = .idle
        showComplete = false
        elapsedTime = 0
        coachMessage = nil
        breathAnalysis = nil
        coachScore = 0
        coachScoreLine = ""
        hasAuthoritativeCoachScore = false
        coachScoreV2 = nil
        coachScoreComponents = nil
        coachScoreCapReasonCodes = []
        coachScoreCapApplied = nil
        coachScoreCapAppliedReason = nil
        coachScoreHRValidMainSetSeconds = nil
        coachScoreZoneValidMainSetSeconds = nil
        coachScoreZoneCompliance = nil
        breathAvailableReliable = false
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
        workoutContextSummary = nil
        workoutContextSummaryReceivedAt = nil
        lastEventSpeechAt = nil
        lastEventSpeechPriority = -1
        lastResolvedUtteranceID = nil
        lastResolvedEventType = nil
        activeSessionPlan = nil

        // Cleanup stale audio pack files now that workout is idle
        AudioPackSyncManager.shared.purgeStaleFiles()
    }

    /// Trigger background audio pack sync. Call from MainTabView.onAppear.
    func triggerAudioPackSync() {
        Task {
            await AudioPackSyncManager.shared.syncIfNeeded(workoutState: self.workoutState)
        }
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
        TimeInterval(max(0, effectiveSessionPlan.warmupSeconds))
    }

    private var configuredIntenseDuration: TimeInterval {
        TimeInterval(max(0, effectiveSessionPlan.mainSeconds))
    }

    private var configuredCooldownDuration: TimeInterval {
        TimeInterval(max(0, effectiveSessionPlan.cooldownSeconds))
    }

    private var workoutContextSummaryReceivedAt: Date?

    private var resolvedPhaseKey: String {
        if let phase = workoutContextSummary?.phase?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased(),
           !phase.isEmpty {
            return phase
        }
        switch currentPhase {
        case .warmup:
            return "warmup"
        case .cooldown:
            return "cooldown"
        case .intense:
            return runtimeWorkoutMode == .intervals ? "work" : "main"
        }
    }

    private var workoutContextSummaryAgeSeconds: Int {
        guard let anchor = workoutContextSummaryReceivedAt else { return 0 }
        return max(0, Int(Date().timeIntervalSince(anchor)))
    }

    private var intervalRepProgress: (Int, Int)? {
        guard let summary = workoutContextSummary,
              let repsTotal = summary.repsTotal, repsTotal > 0 else { return nil }
        let repIndex = max(1, min(repsTotal, summary.repIndex ?? 1))
        return (repIndex, repsTotal)
    }

    private var currentPhaseRemainingSeconds: Int {
        if let summary = workoutContextSummary {
            let age = workoutContextSummaryAgeSeconds
            let phase = resolvedPhaseKey
            if phase == "work" || phase == "recovery",
               let repRemaining = summary.repRemainingS {
                return max(0, repRemaining - age)
            }
            if let timeLeft = summary.timeLeftS {
                return max(0, timeLeft - age)
            }
        }
        return fallbackPhaseRemainingSeconds()
    }

    private func fallbackPhaseRemainingSeconds() -> Int {
        let warmup = Int(configuredWarmupDuration)
        let intense = Int(configuredIntenseDuration)
        let cooldown = Int(configuredCooldownDuration)
        let elapsed = max(0, Int(elapsedTime))

        switch currentPhase {
        case .warmup:
            return max(0, warmup - elapsed)
        case .intense:
            let elapsedInIntense = max(0, elapsed - warmup)
            return max(0, intense - elapsedInIntense)
        case .cooldown:
            let elapsedInCooldown = max(0, elapsed - warmup - intense)
            return max(0, cooldown - elapsedInCooldown)
        }
    }

    private func formatPhaseRemaining(seconds: Int) -> String {
        let clamped = max(0, seconds)
        let mins = clamped / 60
        let secs = clamped % 60
        return String(format: "%02d:%02d", mins, secs)
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
    private let motionCadenceService = MotionCadenceService()
    private let phoneWCManager = PhoneWCManager()
    private let watchHRProvider = AppleWatchWCProvider()
    private let bleHeartRateProvider = BLEHeartRateProvider()
    private let hkFallbackProvider = HealthKitFallbackProvider()
    private let heartRateArbiter = HeartRateArbiter()
    private var latestHeartRateSampleDate: Date?
    private var lastWCHRSampleAt: Date?
    private var lastBLEHRSampleAt: Date?
    private var lastHKSampleAt: Date?
    private var pendingWatchRequestTimestamp: TimeInterval?
    private var pendingWatchRequestId: String?
    private var activeWatchRequestId: String?
    private var latestWatchStatusForBackend: String = "no_live_hr"
    private var watchStartAckTimeoutTask: Task<Void, Never>?
    private let watchStartAckTimeoutSeconds: TimeInterval = 15.0
    private var latestMovementSampleDate: Date?
    private var latestMovementSource: String = "none"
    private let eventSpeechCollisionWindowSeconds: TimeInterval = 2.0
    private var lastEventSpeechAt: Date?
    private var lastEventSpeechPriority: Int = -1
    private var lastResolvedUtteranceID: String?
    private var lastResolvedEventType: String?
    private let maxSpeechTranscriptEntries = 120
    private var talkCaptureTask: Task<Void, Never>?
    private let workoutTalkCaptureSeconds: TimeInterval = 6.0

    // Wake word for user-initiated speech ("Coach" / "Trener")
    let wakeWordManager = WakeWordManager()
    @Published var isWakeWordActive = false  // Show UI indicator when wake word heard

    // MARK: - Initialization

    init() {
        loadPersistedCoachScores()
        loadWorkoutSetupPreferences()
        configureHeartRatePipeline()
        configureWatchConnectivity()
        watchSessionReachable = phoneWCManager.isReachable
        watchHRProvider.updateSessionState(
            reachable: phoneWCManager.isReachable,
            paired: phoneWCManager.isPaired,
            installed: phoneWCManager.isWatchAppInstalled
        )

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

    private func loadWorkoutSetupPreferences() {
        let defaults = UserDefaults.standard
        if let storedStyleRaw = defaults.string(forKey: workoutIntensityPreferenceKey),
           let storedStyle = CoachingStyle(rawValue: storedStyleRaw) {
            coachingStyle = storedStyle
        }
        if defaults.object(forKey: breathAnalysisEnabledKey) != nil {
            useBreathingMicCues = defaults.bool(forKey: breathAnalysisEnabledKey)
        }
        if let storedModeRaw = defaults.string(forKey: easyRunSessionModePreferenceKey),
           let storedMode = EasyRunSessionMode(rawValue: storedModeRaw) {
            selectedEasyRunSessionMode = storedMode
        }
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
                let response = try await apiService.talkToCoach(
                    message: message,
                    language: currentLanguage,
                    persona: activePersonality.rawValue,
                    userName: currentUserName,
                    responseMode: "qa",
                    context: isContinuousMode ? "workout" : "chat"
                )
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

    /// Handle wake trigger from on-device keyword spotting.
    private func handleWakeWordUtterance(_ utterance: String) {
        _ = utterance // Wake callbacks currently pass only the matched wake phrase.
        guard isContinuousMode, !isPaused else { return }
        startWorkoutTalkCapture(triggerSource: .wakeWord, playWakeAck: true)
    }

    /// "Talk to Coach" button — manually triggered
    /// Starts a short workout-context capture session.
    func talkToCoachButtonPressed() {
        guard isContinuousMode else { return }
        guard !isPaused else { return }
        guard !isTalkingToCoach else {
            print("⚠️ Talk button ignored while coach is responding")
            return
        }
        startWorkoutTalkCapture(triggerSource: .button, playWakeAck: false)
    }

    private func startWorkoutTalkCapture(triggerSource: TalkTriggerSource, playWakeAck: Bool) {
        guard isContinuousMode, !isPaused else { return }
        guard !isTalkingToCoach else { return }

        talkCaptureTask?.cancel()
        isTalkingToCoach = true
        isWakeWordActive = true
        coachInteractionState = .commandMode
        voiceState = .listening

        if playWakeAck {
            Task { [weak self] in
                await self?.playWakeAcknowledgement()
            }
        }

        let captureDuration = workoutTalkCaptureSeconds
        let startedAt = Date()
        print("🎤 Workout talk capture started source=\(triggerSource.rawValue) duration=\(captureDuration)s")

        talkCaptureTask = Task { [weak self] in
            guard let self = self else { return }
            try? await Task.sleep(nanoseconds: UInt64(captureDuration * 1_000_000_000))
            guard !Task.isCancelled else { return }
            guard self.isContinuousMode, !self.isPaused else {
                await MainActor.run {
                    self.isTalkingToCoach = false
                    self.isWakeWordActive = false
                    self.coachInteractionState = .passiveListening
                }
                return
            }

            let audioURL = self.continuousRecordingManager.getLatestChunk(duration: captureDuration)
            if audioURL == nil {
                print("⚠️ Workout talk capture empty — using text fallback prompt")
            }
            await self.sendWorkoutTalkRequest(
                audioURL: audioURL,
                triggerSource: triggerSource,
                captureStartedAt: startedAt
            )
        }
    }

    private func sendWorkoutTalkRequest(
        audioURL: URL?,
        triggerSource: TalkTriggerSource,
        captureStartedAt: Date
    ) async {
        coachInteractionState = .responding

        let talkContext = workoutTalkContextPayload()
        let fallbackPrompt = defaultWorkoutTalkPrompt()
        let requestStartedAt = Date()

        do {
            guard let sid = sessionId, !sid.isEmpty else {
                print("⚠️ session_id missing for workout talk; using generic talk endpoint fallback")
                let response = try await apiService.talkToCoach(
                    message: fallbackPrompt,
                    language: currentLanguage,
                    persona: activePersonality.rawValue,
                    userName: currentUserName,
                    responseMode: "qa",
                    context: "workout",
                    triggerSource: triggerSource.rawValue
                )
                coachMessage = response.text
                voiceState = .speaking
                _ = await playCoachAudio(response.audioURL, transcriptText: response.text)
                finalizeWorkoutTalkSession()
                return
            }

            let response = try await apiService.talkToCoachDuringWorkoutUnified(
                audioURL: audioURL,
                fallbackMessage: fallbackPrompt,
                triggerSource: triggerSource.rawValue,
                sessionId: sid,
                workoutContext: talkContext,
                persona: activePersonality.rawValue,
                language: currentLanguage,
                userName: currentUserName
            )

            let latencyMs = Int(Date().timeIntervalSince(requestStartedAt) * 1000)
            print(
                "🗣️ Coach talk response source=\(triggerSource.rawValue) latency_ms=\(latencyMs) provider=\(response.provider ?? "unknown") mode=\(response.mode ?? "unknown") fallback_used=\(response.fallbackUsed ?? false)"
            )
            if response.policyBlocked == true {
                print(
                    "🛡️ TALK_POLICY_BLOCKED category=\(response.policyCategory ?? "unknown") reason=\(response.policyReason ?? "n/a")"
                )
            }
            coachMessage = response.text
            voiceState = .speaking
            _ = await playCoachAudio(response.audioURL, transcriptText: response.text)
        } catch {
            print("❌ Coach talk failed: \(error.localizedDescription)")
            coachMessage = currentLanguage == "no"
                ? "Fikk ikke kontakt med coach akkurat nå. Prøv igjen."
                : "Could not reach coach right now. Try again."
        }

        let captureMs = Int(Date().timeIntervalSince(captureStartedAt) * 1000)
        print("🎙️ Workout talk completed source=\(triggerSource.rawValue) total_capture_window_ms=\(captureMs)")
        finalizeWorkoutTalkSession()
    }

    private func finalizeWorkoutTalkSession() {
        talkCaptureTask?.cancel()
        talkCaptureTask = nil
        isTalkingToCoach = false
        isWakeWordActive = false
        coachInteractionState = .passiveListening
        voiceState = isContinuousMode && !isPaused ? .listening : .idle
        // Drop stale event scheduler state once talk flow ends.
        lastEventSpeechAt = nil
        lastEventSpeechPriority = -1
        lastResolvedUtteranceID = nil
        lastResolvedEventType = nil
    }

    private func defaultWorkoutTalkPrompt() -> String {
        switch zoneStatus {
        case "above_zone":
            return currentLanguage == "no"
                ? "Jeg er over målsonen nå. Hva bør jeg gjøre?"
                : "I am above target zone right now. What should I do?"
        case "below_zone":
            return currentLanguage == "no"
                ? "Jeg er under målsonen nå. Hva bør jeg gjøre?"
                : "I am below target zone right now. What should I do?"
        case "in_zone":
            return currentLanguage == "no"
                ? "Jeg er i målsonen nå. Hva bør jeg fokusere på?"
                : "I am in target zone now. What should I focus on?"
        default:
            return currentLanguage == "no" ? "Hvordan ligger jeg an nå?" : "How am I doing right now?"
        }
    }

    private func workoutTalkContextPayload() -> WorkoutTalkContext {
        WorkoutTalkContext(
            phase: currentPhase.rawValue,
            heartRate: heartRate ?? 0,
            targetHRLow: targetHRLow,
            targetHRHigh: targetHRHigh,
            zoneState: zoneStatus,
            timeLeftS: workoutContextSummary?.timeLeftS,
            repIndex: workoutContextSummary?.repIndex,
            repsTotal: workoutContextSummary?.repsTotal,
            repRemainingS: workoutContextSummary?.repRemainingS,
            repsRemainingIncludingCurrent: workoutContextSummary?.repsRemainingIncludingCurrent
        )
    }

    private func wakeAcknowledgementUtteranceID() -> String {
        currentLanguage == "no" ? "wake_ack.no.default" : "wake_ack.en.default"
    }

    private func playWakeAcknowledgement() async {
        let utteranceID = wakeAcknowledgementUtteranceID()
        print("🎧 Wake ack: \(utteranceID)")
        _ = await playCoachAudio(
            nil,
            utteranceID: utteranceID,
            eventType: "wake_ack",
            transcriptText: nil,
            allowRemotePackFetch: false,
            allowBackendTTSFallback: false
        )
    }

    /// Legacy text path retained for non-workout chat interactions.
    private func sendUserMessageToCoach(_ message: String) {
        let trimmedMessage = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedMessage.isEmpty else {
            isWakeWordActive = false
            coachInteractionState = .passiveListening
            return
        }

        coachInteractionState = .responding
        isTalkingToCoach = true

        Task {
            do {
                let response: CoachTalkResponse
                if let sid = sessionId, !sid.isEmpty {
                    response = try await apiService.talkToCoachDuringWorkout(
                        message: trimmedMessage,
                        sessionId: sid,
                        phase: currentPhase.rawValue,
                        intensity: breathAnalysis?.intensity ?? "moderate",
                        persona: activePersonality.rawValue,
                        language: currentLanguage,
                        userName: currentUserName
                    )
                } else {
                    print("⚠️ session_id missing for workout talk; using generic talk endpoint fallback")
                    response = try await apiService.talkToCoach(
                        message: trimmedMessage,
                        language: currentLanguage,
                        persona: activePersonality.rawValue,
                        userName: currentUserName,
                        responseMode: "qa",
                        context: "workout"
                    )
                }

                coachMessage = response.text
                print("🗣️ Coach replied to user: '\(response.text)'")

                // Play the response audio
                voiceState = .speaking
                await playCoachAudio(response.audioURL)
            } catch {
                print("❌ Coach talk failed: \(error.localizedDescription)")
                coachMessage = currentLanguage == "no"
                    ? "Fikk ikke kontakt med coach akkurat nå. Prøv igjen."
                    : "Could not reach coach right now. Try again."
            }

            // Return to passive listening
            isTalkingToCoach = false
            isWakeWordActive = false
            coachInteractionState = .passiveListening
            voiceState = isContinuousMode && !isPaused ? .listening : .idle
        }
    }

    // MARK: - Phase Auto-Detection

    private func autoDetectPhase() {
        // Auto-detect workout phase based on duration
        // Uses user-selected warmup time (0–40 minutes)
        // After warmup: intense for 15 minutes
        // After intense: cooldown

        guard let startTime = sessionStartTime else {
            currentPhase = configuredWarmupDuration > 0 ? .warmup : .intense
            return
        }

        let duration = Date().timeIntervalSince(startTime)
        let warmupSeconds = configuredWarmupDuration
        let intenseEndSeconds = warmupSeconds + configuredIntenseDuration

        if warmupSeconds > 0 && duration < warmupSeconds && !hasSkippedWarmup {
            currentPhase = .warmup
        } else if isEasyRunFreeRunActive {
            currentPhase = .intense
        } else if duration < intenseEndSeconds {
            currentPhase = .intense
        } else {
            currentPhase = .cooldown
        }
    }

    private func buildSessionPlanFromSelections() -> WorkoutSessionPlan {
        let mode = selectedWorkoutMode
        let easyMode = selectedEasyRunSessionMode
        let warmupSeconds = max(0, selectedWarmupMinutes * 60)

        switch mode {
        case .easyRun:
            let mainSeconds: Int
            if easyMode == .freeRun {
                mainSeconds = 0
            } else {
                mainSeconds = max(0, selectedEasyRunMinutes * 60)
            }
            return WorkoutSessionPlan(
                workoutMode: .easyRun,
                easyRunSessionMode: easyMode,
                warmupSeconds: easyMode == .freeRun ? 0 : warmupSeconds,
                mainSeconds: mainSeconds,
                cooldownSeconds: 5 * 60,
                intervalRepeats: nil,
                intervalWorkSeconds: nil,
                intervalRecoverySeconds: nil
            )
        case .intervals:
            let repeats = max(2, min(10, selectedIntervalSets))
            let workSeconds = max(1, min(20, selectedIntervalWorkMinutes)) * 60
            let recoverySeconds = max(0, min(10, selectedIntervalBreakMinutes)) * 60
            let mainSeconds = (repeats * workSeconds) + (max(0, repeats - 1) * recoverySeconds)
            return WorkoutSessionPlan(
                workoutMode: .intervals,
                easyRunSessionMode: .timed,
                warmupSeconds: warmupSeconds,
                mainSeconds: mainSeconds,
                cooldownSeconds: 6 * 60,
                intervalRepeats: repeats,
                intervalWorkSeconds: workSeconds,
                intervalRecoverySeconds: recoverySeconds
            )
        case .standard:
            return WorkoutSessionPlan(
                workoutMode: .standard,
                easyRunSessionMode: .timed,
                warmupSeconds: Int(AppConfig.warmupDuration),
                mainSeconds: Int(AppConfig.intenseDuration),
                cooldownSeconds: 180,
                intervalRepeats: nil,
                intervalWorkSeconds: nil,
                intervalRecoverySeconds: nil
            )
        }
    }

    func applyEasyRunSessionModeSelection(_ mode: EasyRunSessionMode) {
        switch mode {
        case .timed:
            let restoreWarmup = max(0, timedEasyRunWarmupBackup)
            let restoreDuration = max(0, timedEasyRunDurationBackup)
            if selectedWarmupMinutes == 0 && restoreWarmup > 0 {
                selectedWarmupMinutes = restoreWarmup
            }
            if selectedEasyRunMinutes == 0 && restoreDuration > 0 {
                selectedEasyRunMinutes = restoreDuration
            }
        case .freeRun:
            if selectedWarmupMinutes > 0 {
                timedEasyRunWarmupBackup = selectedWarmupMinutes
            }
            if selectedEasyRunMinutes > 0 {
                timedEasyRunDurationBackup = selectedEasyRunMinutes
            }
            selectedWarmupMinutes = 0
            selectedEasyRunMinutes = 0
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
            return "Coach score: \(clampedScore) — \(coachWorkPhraseNo(for: band))"
        }
        return "Coach score: \(clampedScore) — \(coachWorkPhraseEn(for: band))"
    }

    private func loadPersistedCoachScores() {
        let defaults = UserDefaults.standard
        let fallback = max(0, min(100, defaults.integer(forKey: lastCoachScoreKey)))

        guard let data = defaults.data(forKey: coachScoreHistoryKey),
              let decoded = try? JSONDecoder().decode([CoachScoreRecord].self, from: data) else {
            coachScoreHistory = []
            lastPersistedCoachScore = fallback
            return
        }

        coachScoreHistory = decoded
            .sorted(by: { $0.date > $1.date })
            .prefix(maxCoachScoreHistoryCount)
            .map { $0 }

        if let latest = coachScoreHistory.first {
            lastPersistedCoachScore = latest.score
        } else {
            lastPersistedCoachScore = fallback
        }
    }

    private func persistFinalCoachScore(_ score: Int, at date: Date) {
        let clamped = max(0, min(100, score))
        var updated = coachScoreHistory
        updated.insert(
            CoachScoreRecord(
                date: date,
                score: clamped,
                capApplied: coachScoreCapApplied,
                capAppliedReason: coachScoreCapAppliedReason,
                zoneCompliance: coachScoreZoneCompliance,
                hrValidMainSetSeconds: coachScoreHRValidMainSetSeconds,
                zoneValidMainSetSeconds: coachScoreZoneValidMainSetSeconds
            ),
            at: 0
        )
        if updated.count > maxCoachScoreHistoryCount {
            updated = Array(updated.prefix(maxCoachScoreHistoryCount))
        }

        coachScoreHistory = updated
        lastPersistedCoachScore = clamped

        let defaults = UserDefaults.standard
        defaults.set(clamped, forKey: lastCoachScoreKey)
        if let data = try? JSONEncoder().encode(updated) {
            defaults.set(data, forKey: coachScoreHistoryKey)
        }
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

    private func eventPriority(for eventType: String) -> Int {
        switch eventType {
        case "interval_countdown_start", "hr_signal_lost":
            return 100
        case "hr_signal_restored":
            return 98
        case "interval_countdown_5":
            return 95
        case "interval_countdown_15":
            return 94
        case "interval_countdown_30":
            return 93
        case "warmup_started", "main_started", "cooldown_started", "workout_finished":
            return 90
        case "pause_detected":
            return 86
        case "pause_resumed":
            return 85
        case "watch_disconnected_notice", "no_sensors_notice", "watch_restored_notice":
            return 88
        case "max_silence_override", "max_silence_breath_guide":
            return 68
        case "max_silence_go_by_feel":
            return 66
        case "exited_target_above", "exited_target_below":
            return 70
        case "entered_target":
            return 60
        case "interval_in_target_sustained", "easy_run_in_target_sustained":
            return 55
        case "max_silence_motivation":
            return 69
        default:
            return 0
        }
    }

    private func utteranceID(for event: CoachingEvent) -> String? {
        let eventType = event.eventType
        let phase = event.payload.phase.lowercased()

        switch eventType {
        case "warmup_started":
            return "zone.phase.warmup.1"
        case "main_started":
            return "zone.main_started.1"
        case "cooldown_started":
            return "zone.phase.cooldown.1"
        case "workout_finished":
            return "zone.workout_finished.1"
        case "entered_target":
            return "zone.in_zone.default.1"
        case "exited_target_above":
            return "zone.above.default.1"
        case "exited_target_below":
            return "zone.below.default.1"
        case "hr_signal_lost":
            return "zone.hr_poor_enter.1"
        case "hr_signal_restored":
            return "zone.hr_poor_exit.1"
        case "watch_disconnected_notice":
            return "zone.watch_disconnected.1"
        case "no_sensors_notice":
            return "zone.no_sensors.1"
        case "watch_restored_notice":
            return "zone.watch_restored.1"
        case "interval_countdown_30":
            return "zone.countdown.30"
        case "interval_countdown_15":
            return "zone.countdown.15"
        case "interval_countdown_5":
            return "zone.countdown.5"
        case "interval_countdown_start":
            return "zone.countdown.start"
        case "max_silence_override":
            if phase == "work" {
                return "zone.silence.work.1"
            }
            if phase == "recovery" {
                return "zone.silence.rest.1"
            }
            return "zone.silence.default.1"
        case "max_silence_go_by_feel":
            if phase == "work" {
                return "zone.feel.work.1"
            }
            if phase == "recovery" {
                return "zone.feel.recovery.1"
            }
            return "zone.feel.easy_run.1"
        case "max_silence_breath_guide":
            if phase == "work" {
                return "zone.breath.work.1"
            }
            if phase == "recovery" {
                return "zone.breath.recovery.1"
            }
            return "zone.breath.easy_run.1"
        case "max_silence_motivation":
            return "motivation.1"
        case "interval_in_target_sustained", "easy_run_in_target_sustained":
            // Backend sends dynamic phrase_id via event payload; this is fallback only
            return "interval.motivate.s2.1"
        default:
            return nil
        }
    }

    private func resolvedEventPriority(for event: CoachingEvent) -> (value: Int, source: String) {
        if let backendPriority = event.priority {
            return (backendPriority, "backend")
        }
        return (eventPriority(for: event.eventType), "local_fallback")
    }

    private func selectHighestPriorityEvent(from events: [CoachingEvent]) -> CoachingEvent? {
        guard !events.isEmpty else { return nil }
        return events.sorted { lhs, rhs in
            let l = resolvedEventPriority(for: lhs).value
            let r = resolvedEventPriority(for: rhs).value
            if l == r {
                return lhs.ts < rhs.ts
            }
            return l > r
        }.first
    }

    private func shouldSpeakEventFirst(response: ContinuousCoachResponse) -> (speak: Bool, reason: String) {
        guard AppConfig.ContinuousCoaching.iosEventSpeechEnabled else {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            return (response.shouldSpeak && response.audioURL != nil, "legacy_fallback")
        }

        if isCoachTalkActive {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            print("🤫 EVENT_SUPPRESSED reason=talk_arbitration state=\(coachInteractionState.rawValue)")
            return (false, "talk_arbitration")
        }

        // Event-capable contract:
        // - Backend owns the speech/no-speech decision via should_speak.
        // - If events array is missing, fall back to legacy audio path.
        guard let events = response.events else {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            return (response.shouldSpeak && response.audioURL != nil, "legacy_fallback")
        }

        // Backend said don't speak — respect it unconditionally.
        guard response.shouldSpeak else {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            return (false, "backend_silent")
        }

        guard !events.isEmpty else {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            // Backend says speak but no events — fall back to audio URL if available.
            return (response.audioURL != nil, "backend_speak_no_events")
        }

        guard let selected = selectHighestPriorityEvent(from: events) else {
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            return (response.audioURL != nil, "event_router_no_event")
        }

        // Resolve utterance ID: prefer backend-provided phrase_id, fall back to local mapping.
        let payloadPhraseID = selected.phraseId?.trimmingCharacters(in: .whitespacesAndNewlines)
        let resolvedUtterance: String?
        if let payloadPhraseID, !payloadPhraseID.isEmpty {
            resolvedUtterance = payloadPhraseID
        } else {
            resolvedUtterance = utteranceID(for: selected)
            if let fallbackUtterance = resolvedUtterance {
                print("🧭 EVENT_PHRASE_FALLBACK event=\(selected.eventType) utterance=\(fallbackUtterance) source=ios_mapping")
            }
        }
        guard let utteranceID = resolvedUtterance else {
            print("🔇 EVENT_SUPPRESSED reason=no_utterance event=\(selected.eventType)")
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil
            // Backend says speak — still allow audio URL fallback even without utterance mapping.
            return (response.audioURL != nil, "event_router_no_utterance_audio_fallback")
        }

        // Collision window: legitimate audio dedup to prevent overlapping playback.
        let selectedPriorityInfo = resolvedEventPriority(for: selected)
        let selectedPriority = selectedPriorityInfo.value
        let now = Date()
        if let lastAt = lastEventSpeechAt,
           now.timeIntervalSince(lastAt) < eventSpeechCollisionWindowSeconds,
           selectedPriority <= lastEventSpeechPriority {
            print("🔇 EVENT_SUPPRESSED reason=collision event=\(selected.eventType) priority=\(selectedPriority) priority_source=\(selectedPriorityInfo.source) last_priority=\(lastEventSpeechPriority)")
            return (false, "event_router_collision")
        }

        if selected.eventType == "workout_finished" {
            // Clear scheduler state at session end to avoid stale suppression on next workout.
            lastEventSpeechAt = nil
            lastEventSpeechPriority = -1
        } else {
            lastEventSpeechAt = now
            lastEventSpeechPriority = selectedPriority
        }
        lastResolvedUtteranceID = utteranceID
        lastResolvedEventType = selected.eventType
        print("🎙️ EVENT_SELECTED event=\(selected.eventType) utterance=\(utteranceID) priority=\(selectedPriority) priority_source=\(selectedPriorityInfo.source)")
        return (true, "event_router")
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

    // MARK: - Watch Connectivity

    private func configureHeartRatePipeline() {
        watchHRProvider.onSample = { [weak self] sample in
            self?.heartRateArbiter.ingest(sample: sample)
        }
        watchHRProvider.onStatus = { [weak self] status in
            self?.heartRateArbiter.updateStatus(source: .wc, status: status)
        }

        bleHeartRateProvider.onSample = { [weak self] sample in
            self?.heartRateArbiter.ingest(sample: sample)
        }
        bleHeartRateProvider.onStatus = { [weak self] status in
            self?.heartRateArbiter.updateStatus(source: .ble, status: status)
        }

        hkFallbackProvider.onSample = { [weak self] sample in
            self?.heartRateArbiter.ingest(sample: sample)
        }
        hkFallbackProvider.onStatus = { [weak self] status in
            self?.heartRateArbiter.updateStatus(source: .hk, status: status)
        }

        heartRateArbiter.onLog = { line in
            print(line)
        }
        heartRateArbiter.onOutput = { [weak self] output in
            guard let self else { return }
            self.heartRate = output.currentBPM
            self.hrSource = output.hrSource
            self.hrSignalQuality = output.hrSignalQuality.rawValue
            self.watchConnected = output.watchConnected
            self.bleConnected = output.bleConnected
            self.latestWatchStatusForBackend = output.watchStatus
            self.latestHeartRateSampleDate = output.lastSampleAt
            self.liveHRBannerText = output.hrSignalQuality == .degraded || output.hrSource == .none
                ? (self.currentLanguage == "no" ? "Live puls utilgjengelig / degradert" : "Live HR unavailable / degraded")
                : nil

            switch output.hrSource {
            case .wc:
                self.lastWCHRSampleAt = output.lastSampleAt
            case .ble:
                self.lastBLEHRSampleAt = output.lastSampleAt
            case .hk:
                self.lastHKSampleAt = output.lastSampleAt
            case .none:
                break
            }
        }
    }

    private func configureWatchConnectivity() {
        phoneWCManager.onReachabilityChanged = { [weak self] reachable in
            guard let self else { return }
            self.watchSessionReachable = reachable
            self.watchHRProvider.updateSessionState(
                reachable: reachable,
                paired: self.phoneWCManager.isPaired,
                installed: self.phoneWCManager.isWatchAppInstalled
            )
        }
        phoneWCManager.onHeartRate = { [weak self] bpm, ts in
            self?.handleWCHRUpdate(bpm: bpm, timestamp: ts)
        }
        phoneWCManager.onWorkoutStartedAck = { [weak self] workoutType, ts, requestID in
            self?.handleWatchWorkoutStartedAck(workoutType: workoutType, timestamp: ts, requestID: requestID)
        }
        phoneWCManager.onWorkoutStartFailed = { [weak self] error, ts, requestID in
            self?.handleWatchWorkoutStartFailed(error: error, timestamp: ts, requestID: requestID)
        }
        phoneWCManager.onWorkoutStopped = { [weak self] ts, requestID in
            self?.handleWatchWorkoutStopped(timestamp: ts, requestID: requestID)
        }
    }

    private var requestedWatchWorkoutType: String {
        runtimeWorkoutMode == .intervals ? WCKeys.WorkoutType.intervals : WCKeys.WorkoutType.easyRun
    }

    private func requestWatchStartOrFallback() {
        let requestTimestamp = Date().timeIntervalSince1970
        let requestID = UUID().uuidString
        pendingWatchRequestTimestamp = requestTimestamp
        pendingWatchRequestId = requestID
        activeWatchRequestId = requestID
        let workoutType = requestedWatchWorkoutType

        let result = phoneWCManager.sendStartRequest(
            workoutType: workoutType,
            timestamp: requestTimestamp,
            requestID: requestID
        )

        switch result {
        case .liveRequestSent:
            print("START_REQUEST request_id=\(requestID) workout_type=\(workoutType) path=watch")
            isWaitingForWatchStart = true
            watchStartStatusLine = currentLanguage == "no"
                ? "Venter på bekreftelse fra Watch…"
                : "Waiting for Watch confirmation..."
            scheduleWatchStartAckTimeout(requestTimestamp: requestTimestamp, requestID: requestID)
        case .deferredAndFallback:
            print("START_REQUEST request_id=\(requestID) workout_type=\(workoutType) path=local")
            isWaitingForWatchStart = false
            watchStartStatusLine = currentLanguage == "no"
                ? "Watch ikke tilgjengelig. Starter på iPhone nå."
                : "Watch unavailable. Starting on iPhone now."
            startContinuousWorkoutInternal()
        case .failed(let reason):
            print("START_REQUEST request_id=\(requestID) workout_type=\(workoutType) path=local reason=\(reason)")
            isWaitingForWatchStart = false
            watchStartStatusLine = currentLanguage == "no"
                ? "Kunne ikke nå Watch (\(reason)). Starter på iPhone."
                : "Could not reach Watch (\(reason)). Starting on iPhone."
            startContinuousWorkoutInternal()
        }
    }

    private func scheduleWatchStartAckTimeout(requestTimestamp: TimeInterval, requestID: String) {
        watchStartAckTimeoutTask?.cancel()
        watchStartAckTimeoutTask = Task { [weak self] in
            guard let self else { return }
            try? await Task.sleep(nanoseconds: UInt64(self.watchStartAckTimeoutSeconds * 1_000_000_000))
            await MainActor.run {
                guard self.isWaitingForWatchStart else { return }
                guard self.pendingWatchRequestTimestamp == requestTimestamp else { return }
                guard self.pendingWatchRequestId == requestID else { return }
                self.isWaitingForWatchStart = false
                self.pendingWatchRequestTimestamp = nil
                self.pendingWatchRequestId = nil
                self.watchStartStatusLine = self.currentLanguage == "no"
                    ? "Ingen svar fra Watch. Starter på iPhone."
                    : "No Watch response. Starting on iPhone."
                self.startContinuousWorkoutInternal()
            }
        }
    }

    private func clearWatchStartPendingState() {
        watchStartAckTimeoutTask?.cancel()
        watchStartAckTimeoutTask = nil
        isWaitingForWatchStart = false
        pendingWatchRequestTimestamp = nil
        pendingWatchRequestId = nil
    }

    private func handleWatchWorkoutStartedAck(workoutType _: String, timestamp _: TimeInterval, requestID: String) {
        guard isWaitingForWatchStart else { return }
        guard !requestID.isEmpty else { return }
        guard requestID == pendingWatchRequestId else { return }

        clearWatchStartPendingState()
        watchStartStatusLine = currentLanguage == "no"
            ? "Watch startet økten."
            : "Workout started on Watch."
        print("WATCH_ACK request_id=\(requestID) status=started")
        startContinuousWorkoutInternal()
    }

    private func handleWatchWorkoutStartFailed(error: String, timestamp _: TimeInterval, requestID: String) {
        guard isWaitingForWatchStart else { return }
        guard !requestID.isEmpty else { return }
        guard requestID == pendingWatchRequestId else { return }

        clearWatchStartPendingState()
        watchStartStatusLine = currentLanguage == "no"
            ? "Watch-feil (\(error)). Starter på iPhone."
            : "Watch failed (\(error)). Starting on iPhone."
        print("WATCH_ACK request_id=\(requestID) status=failed")
        startContinuousWorkoutInternal()
    }

    private func handleWatchWorkoutStopped(timestamp _: TimeInterval, requestID: String) {
        if !requestID.isEmpty,
           let activeWatchRequestId,
           requestID != activeWatchRequestId {
            return
        }
        clearWatchStartPendingState()
        print("WATCH_ACK request_id=\(requestID) status=stopped")
        if isContinuousMode {
            stopWorkout(notifyWatch: false)
        }
    }

    private func handleWCHRUpdate(bpm: Double, timestamp: TimeInterval) {
        let sampleDate = Date(timeIntervalSince1970: timestamp)
        lastWCHRSampleAt = sampleDate
        watchHRProvider.ingestHeartRate(bpm: bpm, timestamp: timestamp)
    }

    private func refreshWCLiveness() {
        heartRateArbiter.refreshLiveness()
    }

    // MARK: - HealthKit HR Signals

    private func setupHealthSignals() async {
        guard HKHealthStore.isHealthDataAvailable() else {
            heartRateArbiter.updateStatus(source: .hk, status: .disconnected)
            return
        }

        let authorized = await hkFallbackProvider.requestAuthorization()
        guard authorized else {
            heartRateArbiter.updateStatus(source: .hk, status: .error(reason: "healthkit_auth_denied"))
            return
        }

        if let resting = await hkFallbackProvider.fetchLatestRestingHeartRate() {
            UserDefaults.standard.set(resting, forKey: "resting_hr")
        }

        if let snapshot = await hkFallbackProvider.fetchLatestHeartRateSnapshot() {
            heartRateArbiter.ingest(sample: snapshot)
        }
    }

    func refreshHealthSensors() {
        Task {
            await setupHealthSignals()
            watchHRProvider.updateSessionState(
                reachable: phoneWCManager.isReachable,
                paired: phoneWCManager.isPaired,
                installed: phoneWCManager.isWatchAppInstalled
            )
            heartRateArbiter.refreshLiveness()
        }
    }

    func beginSensorDiscovery() {
        watchHRProvider.start()
        watchHRProvider.updateSessionState(
            reachable: phoneWCManager.isReachable,
            paired: phoneWCManager.isPaired,
            installed: phoneWCManager.isWatchAppInstalled
        )
        bleHeartRateProvider.start()
        heartRateArbiter.refreshLiveness()
    }

    func endSensorDiscovery() {
        guard !isContinuousMode else { return }
        bleHeartRateProvider.stop()
        watchHRProvider.stop()
        heartRateArbiter.refreshLiveness()
    }

    private func startHealthMonitoring() {
        watchHRProvider.start()
        bleHeartRateProvider.start()
        hkFallbackProvider.start()
        heartRateArbiter.refreshLiveness()
    }

    private func stopHealthMonitoring() {
        watchHRProvider.stop()
        bleHeartRateProvider.stop()
        hkFallbackProvider.stop()
        heartRateArbiter.refreshLiveness()
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

    private var hrSampleAgeSecondsForRequest: Double? {
        guard let sampleDate = latestHeartRateSampleDate else { return nil }
        return max(0, Date().timeIntervalSince(sampleDate))
    }

    private func refreshHeartRateSignalQualityFromAge() {
        heartRateArbiter.refreshLiveness()
    }

    private func resolvedHRQualityForRequest(
        heartRate: Int?,
        watchConnected: Bool,
        currentQuality: String,
        source: HRSource
    ) -> String {
        guard heartRate != nil else { return "poor" }
        if source == .wc || source == .ble || source == .hk {
            return currentQuality == "good" ? "good" : "poor"
        }
        guard watchConnected else { return "poor" }
        return currentQuality == "good" ? "good" : "poor"
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
        startContinuousWorkoutInternal()
    }

    private func startContinuousWorkoutInternal() {
        guard !isContinuousMode else { return }
        guard hasValidAuthToken() else {
            clearWatchStartPendingState()
            watchStartStatusLine = nil
            workoutState = .idle
            let message = currentLanguage == "no"
                ? "Du må logge inn for å starte coaching."
                : "You must sign in to start coaching."
            showErrorAlert(message)
            print("⚠️ Continuous workout blocked: missing auth token")
            return
        }
        clearWatchStartPendingState()
        watchStartStatusLine = nil
        workoutState = .active

        print("🎯 Starting continuous workout")
        if activeSessionPlan == nil {
            activeSessionPlan = buildSessionPlanFromSelections()
        }

        do {
            // Start ONE continuous recording session
            try continuousRecordingManager.startContinuousRecording()

            isContinuousMode = true
            voiceState = .listening  // STAYS listening entire workout
            coachInteractionState = .passiveListening
            isWakeWordActive = false
            isTalkingToCoach = false
            talkCaptureTask?.cancel()
            talkCaptureTask = nil
            hrSource = .none
            watchConnected = false
            bleConnected = false
            heartRate = nil
            hrSignalQuality = HRQuality.none.rawValue
            liveHRBannerText = nil
            latestWatchStatusForBackend = "no_live_hr"
            lastWCHRSampleAt = nil
            lastBLEHRSampleAt = nil
            lastHKSampleAt = nil
            sessionStartTime = Date()
            workoutDuration = 0

            // Generate unique session ID
            sessionId = "session_\(UUID().uuidString)"
            lastEventSpeechAt = nil
            lastEventSpeechPriority = -1
            lastResolvedUtteranceID = nil
            lastResolvedEventType = nil

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
                    self.refreshWCLiveness()
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

            // Force manifest sync on every workout start so welcome/event playback
            // resolves against the latest cached local pack when available.
            // Then play welcome and start the coaching loop.
            Task {
                await syncProfileSnapshotToBackend(reason: "workout_start")
                await AudioPackSyncManager.shared.syncIfNeeded(workoutState: self.workoutState)
                await prefetchCoreAudioIfNeeded()
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

    private func syncProfileSnapshotToBackend(reason: String) async {
        guard hasValidAuthToken() else { return }

        let defaults = UserDefaults.standard
        let payload = BackendUserProfilePayload(
            name: defaults.string(forKey: "user_display_name"),
            sex: defaults.string(forKey: "user_gender"),
            age: defaults.object(forKey: "user_age") as? Int,
            heightCm: defaults.object(forKey: "user_height_cm") as? Int,
            weightKg: defaults.object(forKey: "user_weight_kg") as? Int,
            maxHrBpm: defaults.object(forKey: "hr_max") as? Int,
            restingHrBpm: defaults.object(forKey: "resting_hr") as? Int,
            profileUpdatedAt: ISO8601DateFormatter().string(from: Date())
        )

        do {
            try await apiService.upsertUserProfile(payload)
            print("📤 Profile upsert reason=\(reason)")
        } catch {
            print("⚠️ Profile upsert failed reason=\(reason) error=\(error.localizedDescription)")
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
        coachInteractionState = .passiveListening
        isWakeWordActive = false
        isTalkingToCoach = false
        talkCaptureTask?.cancel()
        talkCaptureTask = nil
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
        coachInteractionState = .passiveListening
        isWakeWordActive = false
        isTalkingToCoach = false
        talkCaptureTask?.cancel()
        talkCaptureTask = nil

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
                self.refreshWCLiveness()
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
        clearWatchStartPendingState()
        activeWatchRequestId = nil
        watchStartStatusLine = nil
        isContinuousMode = false
        isPaused = false
        voiceState = .idle
        coachInteractionState = .passiveListening
        isWakeWordActive = false
        isTalkingToCoach = false
        talkCaptureTask?.cancel()
        talkCaptureTask = nil
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
        hrSource = .none
        watchConnected = false
        bleConnected = false
        heartRate = nil
        hrSignalQuality = HRQuality.none.rawValue
        liveHRBannerText = nil
        latestWatchStatusForBackend = "no_live_hr"
        lastWCHRSampleAt = nil
        lastBLEHRSampleAt = nil
        lastHKSampleAt = nil
        lastEventSpeechAt = nil
        lastEventSpeechPriority = -1
        lastResolvedUtteranceID = nil
        lastResolvedEventType = nil
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
            coachScoreLine = formattedCoachScoreLine(score: coachScore)
        }

        if let duration = finalDurationSeconds {
            applyExperienceProgression(durationSeconds: duration, finalCoachScore: coachScore)
        }
        if hasAuthoritativeCoachScore {
            persistFinalCoachScore(coachScore, at: Date())
        } else {
            print("⚠️ Skipping coach score persistence: no authoritative score received")
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
                let tickQuality = resolvedHRQualityForRequest(
                    heartRate: tickHeartRate,
                    watchConnected: watchConnected,
                    currentQuality: hrSignalQuality,
                    source: hrSource
                )
                let tickMovementScore = movementScore
                let tickCadenceSPM = cadenceSPM
                let tickMovementSource = (tickMovementScore != nil || tickCadenceSPM != nil) ? latestMovementSource : "none"
                let liveHRConnected = hrSource == .wc || hrSource == .ble
                let sessionPlan = effectiveSessionPlan
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
                    workoutMode: runtimeWorkoutMode,
                    easyRunFreeMode: isEasyRunFreeRunActive,
                    coachingStyle: coachingStyle,
                    intervalTemplate: selectedIntervalTemplate,
                    warmupSeconds: Int(configuredWarmupDuration),
                    mainSeconds: Int(configuredIntenseDuration),
                    cooldownSeconds: Int(configuredCooldownDuration),
                    intervalRepeats: sessionPlan.intervalRepeats,
                    intervalWorkSeconds: sessionPlan.intervalWorkSeconds,
                    intervalRecoverySeconds: sessionPlan.intervalRecoverySeconds,
                    userProfileId: personalizationProfileId,
                    heartRate: tickHeartRate,
                    hrSampleAgeSeconds: tickSampleAge,
                    hrQuality: tickQuality,
                    hrConfidence: tickQuality == "good" ? 0.9 : 0.2,
                    watchConnected: liveHRConnected,
                    watchStatus: latestWatchStatusForBackend,
                    movementScore: tickMovementScore,
                    cadenceSPM: tickCadenceSPM,
                    movementSource: tickMovementSource,
                    hrMax: storedHRMax,
                    restingHR: storedRestingHR,
                    age: storedAge,
                    breathAnalysisEnabled: useBreathingMicCues,
                    micPermissionGranted: AVAudioSession.sharedInstance().recordPermission == .granted
                )

                let responseTime = Date().timeIntervalSince(tickStart)

                // 3. Update metrics silently (NO UI state change)
                breathAnalysis = response.breathAnalysis
                coachMessage = response.text
                if let scoreV2 = response.coachScoreV2 {
                    coachScore = max(0, min(100, scoreV2))
                    hasAuthoritativeCoachScore = true
                } else if let score = response.coachScore {
                    coachScore = max(0, min(100, score))
                    hasAuthoritativeCoachScore = true
                }
                if let line = response.coachScoreLine, !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    coachScoreLine = line
                } else if hasAuthoritativeCoachScore {
                    coachScoreLine = formattedCoachScoreLine(score: coachScore)
                }
                coachScoreV2 = response.coachScoreV2
                coachScoreComponents = response.coachScoreComponents
                coachScoreCapReasonCodes = response.capReasonCodes ?? []
                coachScoreCapApplied = response.capApplied
                coachScoreCapAppliedReason = response.capAppliedReason
                coachScoreHRValidMainSetSeconds = response.hrValidMainSetSeconds
                coachScoreZoneValidMainSetSeconds = response.zoneValidMainSetSeconds
                coachScoreZoneCompliance = response.zoneCompliance
                breathAvailableReliable = response.breathAvailableReliable ?? false
                if let responseStyle = response.coachingStyle,
                   let parsedStyle = CoachingStyle(rawValue: responseStyle) {
                    coachingStyle = parsedStyle
                }
                if let zone = response.zoneStatus {
                    zoneStatus = zone
                }
                if let label = response.targetZoneLabel {
                    targetZoneLabel = label
                }
                targetHRLow = response.targetHRLow
                targetHRHigh = response.targetHRHigh
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
                workoutContextSummary = response.workoutContextSummary
                if response.workoutContextSummary != nil {
                    workoutContextSummaryReceivedAt = Date()
                }
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

                let eventCount = response.events?.count ?? 0
                let hasEventsField = response.events != nil
                print("📊 Backend response: should_speak=\(response.shouldSpeak), has_audio=\(response.audioURL != nil), has_events_field=\(hasEventsField), events=\(eventCount), text_len=\(response.text.count), wait=\(response.waitSeconds)s, reason=\(response.reason ?? "none"), brain=\(response.brainProvider ?? "unknown")/\(response.brainSource ?? "unknown")/\(response.brainStatus ?? "unknown")")

                // 4. Event-first speech routing:
                // - If events field exists (even empty), event scheduler decides.
                // - Legacy fallback is only for payloads missing events.
                let eventSpeechDecision = shouldSpeakEventFirst(response: response)
                if eventSpeechDecision.speak {
                    let didPlay = await playCoachAudio(
                        response.audioURL,
                        utteranceID: lastResolvedUtteranceID,
                        eventType: lastResolvedEventType,
                        transcriptText: response.text
                    )
                    if didPlay {
                        print("🗣️ Coach speaking via \(eventSpeechDecision.reason): '\(response.text)'")
                    } else {
                        print("🤐 Coach silent via event_router_no_audio_source")
                    }
                } else {
                    print("🤐 Coach silent via \(eventSpeechDecision.reason)")
                }

                // 5. Adjust next interval dynamically
                coachingInterval = response.waitSeconds
                print("⏱️ Next tick in: \(Int(coachingInterval))s")

            } catch {
                // Network/decode error: skip this cycle, continue next
                print("❌ Coaching cycle failed: \(error)")
                if handleAuthFailureIfNeeded(error) {
                    return
                }
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

    private func hasValidAuthToken() -> Bool {
        guard let token = KeychainHelper.readString(key: KeychainHelper.tokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
            !token.isEmpty else {
            return false
        }
        return true
    }

    private func isAuthFailure(_ error: Error) -> Bool {
        if let apiError = error as? APIError {
            switch apiError {
            case .authenticationRequired:
                return true
            case .httpError(let statusCode):
                return statusCode == 401 || statusCode == 403
            case .serverError(let message):
                let normalized = message.lowercased()
                return normalized.contains("authorization") || normalized.contains("unauthorized")
            case .invalidURL, .invalidResponse, .downloadFailed, .networkError:
                return false
            }
        }
        return false
    }

    private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {
        guard isAuthFailure(error) else { return false }
        print("🛑 Stopping continuous workout due to auth failure")
        stopContinuousWorkout()
        workoutState = .idle
        let message = currentLanguage == "no"
            ? "Innloggingen mangler eller er utløpt. Logg inn igjen."
            : "Your sign-in is missing or expired. Please sign in again."
        showErrorAlert(message)
        return true
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

    private func normalizedLanguageCode(_ raw: String) -> String {
        let lower = raw.lowercased()
        if lower.hasPrefix("no") || lower.hasPrefix("nb") || lower.hasPrefix("nn") {
            return "no"
        }
        return "en"
    }

    private var audioPackVersion: String {
        AudioPackSyncManager.shared.currentPackVersion ?? AppConfig.AudioPack.version
    }

    private var activeAudioPersonaKey: String {
        switch activePersonality {
        case .personalTrainer:
            return "personal_trainer"
        case .toxicMode:
            // UI name is "Performance Mode", keep neutral cache key.
            return "performance_mode"
        }
    }

    private func isLocalPackAllowed(for utteranceID: String) -> Bool {
        // Personal trainer must never play toxic/performance phrase ids from cached packs.
        if activePersonality == .personalTrainer && utteranceID.hasPrefix("toxic.") {
            return false
        }
        return true
    }

    private var audioPackRootDirectory: URL {
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return documents.appendingPathComponent("audio_pack", isDirectory: true)
    }

    private func localPackFileURL(for utteranceID: String, language: String, personaKey: String) -> URL? {
        let versionDir = audioPackRootDirectory
            .appendingPathComponent(audioPackVersion, isDirectory: true)
            .appendingPathComponent(language, isDirectory: true)

        // Prefer persona-specific cached files first.
        let personaSpecific = versionDir
            .appendingPathComponent(personaKey, isDirectory: true)
            .appendingPathComponent("\(utteranceID).mp3")
        if FileManager.default.fileExists(atPath: personaSpecific.path) {
            return personaSpecific
        }

        // Manifest sync stores generic files at vX/<lang>/<utterance>.mp3.
        let generic = versionDir
            .appendingPathComponent("\(utteranceID).mp3")
        if FileManager.default.fileExists(atPath: generic.path) {
            return generic
        }

        return nil
    }

    private func bundledPackFileURL(for utteranceID: String, language: String, personaKey: String) -> URL? {
        if let personaSpecific = Bundle.main.url(
            forResource: utteranceID,
            withExtension: "mp3",
            subdirectory: "CoreAudioPack/\(language)/\(personaKey)"
        ) {
            return personaSpecific
        }
        return Bundle.main.url(
            forResource: utteranceID,
            withExtension: "mp3",
            subdirectory: "CoreAudioPack/\(language)"
        )
    }

    private func remotePackFileURLs(for utteranceID: String, language: String, personaKey: String) -> [URL] {
        let base = AppConfig.AudioPack.r2PublicURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !base.isEmpty else { return [] }
        let encodedID = utteranceID.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? utteranceID
        let personaURLString = "\(base)/\(audioPackVersion)/\(language)/\(personaKey)/\(encodedID).mp3"
        let genericURLString = "\(base)/\(audioPackVersion)/\(language)/\(encodedID).mp3"
        return [personaURLString, genericURLString].compactMap(URL.init(string:))
    }

    private func downloadAudioPackFileIfNeeded(
        for utteranceID: String,
        language: String,
        personaKey: String
    ) async -> URL? {
        let remoteURLs = remotePackFileURLs(for: utteranceID, language: language, personaKey: personaKey)
        guard !remoteURLs.isEmpty else {
            return nil
        }

        let localDir = audioPackRootDirectory
            .appendingPathComponent(audioPackVersion, isDirectory: true)
            .appendingPathComponent(language, isDirectory: true)
            .appendingPathComponent(personaKey, isDirectory: true)
        let localFile = localDir.appendingPathComponent("\(utteranceID).mp3")
        if FileManager.default.fileExists(atPath: localFile.path) {
            return localFile
        }

        do {
            try FileManager.default.createDirectory(at: localDir, withIntermediateDirectories: true)
            for remoteURL in remoteURLs {
                let (data, response) = try await URLSession.shared.data(from: remoteURL)
                guard let http = response as? HTTPURLResponse, http.statusCode == 200, !data.isEmpty else {
                    continue
                }
                try data.write(to: localFile, options: .atomic)
                return localFile
            }
            return nil
        } catch {
            print("📦 Audio pack fetch failed for \(utteranceID): \(error.localizedDescription)")
            return nil
        }
    }

    private func corePrefetchUtteranceIDs() -> [String] {
        var ids = [
            "wake_ack.en.default",
            "wake_ack.no.default",
            "zone.phase.warmup.1",
            "zone.countdown.30",
            "zone.countdown.15",
            "zone.countdown.5",
            "zone.countdown.start",
            "zone.in_zone.default.1",
            "zone.above.default.1",
            "zone.below.default.1",
            "zone.feel.easy_run.1",
            "zone.breath.easy_run.1",
            "zone.hr_poor_enter.1",
            "zone.hr_poor_exit.1",
            "zone.watch_disconnected.1",
            "zone.watch_restored.1",
            "zone.no_sensors.1",
        ]
        for idx in 1 ... 5 {
            ids.append("welcome.standard.\(idx)")
        }
        return ids
    }

    private func prefetchCoreAudioIfNeeded() async {
        guard AppConfig.AudioPack.prefetchEnabled else { return }
        let language = normalizedLanguageCode(currentLanguage)
        let personaKey = activeAudioPersonaKey
        var downloaded = 0
        var missing = 0
        for utteranceID in corePrefetchUtteranceIDs() {
            guard isLocalPackAllowed(for: utteranceID) else { continue }
            if localPackFileURL(for: utteranceID, language: language, personaKey: personaKey) != nil {
                continue
            }
            if bundledPackFileURL(for: utteranceID, language: language, personaKey: personaKey) != nil {
                continue
            }
            if let _ = await downloadAudioPackFileIfNeeded(
                for: utteranceID,
                language: language,
                personaKey: personaKey
            ) {
                downloaded += 1
            } else {
                missing += 1
            }
        }
        print("📦 AUDIO_PREFETCH downloaded=\(downloaded) missing=\(missing) language=\(language)")
    }

    private func logSpeechTranscript(utteranceID: String, eventType: String, source: String, text: String?) {
        let entry = SpeechTranscriptEntry(
            timestamp: Date(),
            utteranceId: utteranceID,
            eventType: eventType,
            source: source,
            text: text
        )
        speechTranscript.append(entry)
        if speechTranscript.count > maxSpeechTranscriptEntries {
            speechTranscript.removeFirst(speechTranscript.count - maxSpeechTranscriptEntries)
        }
        AudioPipelineDiagnostics.shared.logSpeech(
            utteranceId: utteranceID,
            eventType: eventType,
            source: source
        )
    }

    private func playWelcomeMessage() async {
        do {
            print("👋 Fetching welcome message...")
            let welcome = try await apiService.getWelcomeMessage(language: currentLanguage, persona: activePersonality.rawValue, userName: currentUserName)
            coachMessage = welcome.text
            print("👋 Welcome [\(welcome.utteranceID)]: '\(welcome.text)' - resolving audio source...")
            _ = await playCoachAudio(
                welcome.audioURL,
                utteranceID: welcome.utteranceID,
                eventType: "welcome_message",
                transcriptText: welcome.text
            )
        } catch {
            print("⚠️ Welcome message failed: \(error.localizedDescription)")
            // Non-critical: workout continues even if welcome fails
        }
    }

    @discardableResult
    private func playCoachAudio(
        _ audioURL: String?,
        utteranceID: String? = nil,
        eventType: String? = nil,
        transcriptText: String? = nil,
        allowRemotePackFetch: Bool = true,
        allowBackendTTSFallback: Bool = true
    ) async -> Bool {
        let language = normalizedLanguageCode(currentLanguage)
        let resolvedEventType = eventType ?? "unknown"
        let personaKey = activeAudioPersonaKey

        if let utteranceID {
            if isLocalPackAllowed(for: utteranceID) {
                if let localURL = localPackFileURL(for: utteranceID, language: language, personaKey: personaKey) {
                    print("🔊 Resolving audio source: cached_local_pack utterance=\(utteranceID) event=\(resolvedEventType)")
                    await playAudio(from: localURL)
                    logSpeechTranscript(
                        utteranceID: utteranceID,
                        eventType: resolvedEventType,
                        source: "local_pack",
                        text: transcriptText
                    )
                    return true
                }

                if let bundledURL = bundledPackFileURL(for: utteranceID, language: language, personaKey: personaKey) {
                    print("🔊 Resolving audio source: bundled_core utterance=\(utteranceID) event=\(resolvedEventType)")
                    await playAudio(from: bundledURL)
                    logSpeechTranscript(
                        utteranceID: utteranceID,
                        eventType: resolvedEventType,
                        source: "bundled_core",
                        text: transcriptText
                    )
                    return true
                }

                if allowRemotePackFetch {
                    if let downloadedURL = await downloadAudioPackFileIfNeeded(
                        for: utteranceID,
                        language: language,
                        personaKey: personaKey
                    ) {
                        print("🔊 Resolving audio source: r2_pack utterance=\(utteranceID) event=\(resolvedEventType)")
                        await playAudio(from: downloadedURL)
                        logSpeechTranscript(
                            utteranceID: utteranceID,
                            eventType: resolvedEventType,
                            source: "r2_pack",
                            text: transcriptText
                        )
                        return true
                    }
                }
            } else {
                print("🔇 PACK_SUPPRESSED persona=personal_trainer utterance=\(utteranceID)")
            }
        }

        guard allowBackendTTSFallback, let audioURL else {
            return false
        }

        do {
            print("🔊 Resolving audio source: backend_tts event=\(resolvedEventType)")
            let audioData = try await apiService.downloadVoiceAudio(from: audioURL)
            let ext = URL(string: audioURL)?.pathExtension ?? "mp3"
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("continuous_coach_\(Date().timeIntervalSince1970).\(ext.isEmpty ? "mp3" : ext)")
            try audioData.write(to: tempURL)
            await playAudio(from: tempURL)

            logSpeechTranscript(
                utteranceID: utteranceID ?? "dynamic",
                eventType: resolvedEventType,
                source: "backend_tts",
                text: transcriptText
            )
            return true
        } catch {
            print("Failed to resolve/play coach audio source: \(error.localizedDescription)")
            return false
        }
    }
}
