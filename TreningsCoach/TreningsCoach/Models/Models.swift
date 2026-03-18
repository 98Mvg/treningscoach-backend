//
//  Models.swift
//  TreningsCoach
//
//  Data models for the app
//

import Foundation

// MARK: - Voice State

enum VoiceState {
    case idle
    case listening
    case speaking
}

// MARK: - Workout State

enum WorkoutState: String {
    case idle
    case active
    case paused
    case complete
}

// MARK: - Orb State

enum OrbState: String {
    case idle
    case listening
    case speaking
    case paused
}

// MARK: - Workout Phase

enum WorkoutPhase: String, CaseIterable, Identifiable, Codable {
    case warmup = "warmup"
    case intense = "intense"
    case cooldown = "cooldown"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .warmup: return "Warm-up"
        case .intense: return "Intense"
        case .cooldown: return "Cool-down"
        }
    }

    var description: String {
        switch self {
        case .warmup: return "Gentle coaching for warming up"
        case .intense: return "Motivational coaching for intense workout"
        case .cooldown: return "Calming coaching for cooling down"
        }
    }

    var duration: TimeInterval {
        switch self {
        case .warmup: return AppConfig.warmupDuration
        case .intense: return AppConfig.intenseDuration
        case .cooldown: return 180  // 3 minutes
        }
    }
}

enum WorkoutMode: String, CaseIterable, Identifiable, Codable {
    case easyRun = "easy_run"
    case intervals = "interval"
    case standard = "standard"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .easyRun:
            return "Easy Run"
        case .intervals:
            return "Intervals"
        case .standard:
            return "Standard"
        }
    }
}

enum EasyRunSessionMode: String, CaseIterable, Identifiable, Codable {
    case timed = "timed"
    case freeRun = "free_run"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .timed:
            return L10n.current == .no ? "Timed" : "Timed"
        case .freeRun:
            return L10n.current == .no ? "Free Run" : "Free Run"
        }
    }
}

enum IntervalTemplate: String, CaseIterable, Identifiable, Codable {
    case fourByFour = "4x4"
    case eightByOne = "8x1"
    case tenByThirtyThirty = "10x30/30"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .fourByFour:
            return "4×4"
        case .eightByOne:
            return "8×1"
        case .tenByThirtyThirty:
            return "10×30/30"
        }
    }
}

enum CoachingStyle: String, CaseIterable, Identifiable, Codable {
    case easy = "minimal"
    case medium = "normal"
    case hard = "motivational"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .easy:
            return L10n.intensityEasy
        case .medium:
            return L10n.intensityMedium
        case .hard:
            return L10n.intensityHard
        }
    }
}

// MARK: - Breath Analysis

struct BreathAnalysis: Codable {
    let analysisVersion: Int?
    let silence: Double
    let volume: Double
    let tempo: Double
    let intensity: String
    let duration: Double

    // Advanced breath metrics (from BreathAnalyzer DSP pipeline)
    let breathPhases: [BreathPhaseEvent]?
    let respiratoryRate: Double?
    let breathRegularity: Double?
    let inhaleExhaleRatio: Double?
    let signalQuality: Double?
    let dominantFrequency: Double?
    let intensityScore: Double?
    let intensityConfidence: Double?
    let intervalState: String?
    let intervalStateConfidence: Double?
    let intervalZone: String?

    enum CodingKeys: String, CodingKey {
        case analysisVersion = "analysis_version"
        case silence, volume, tempo, intensity, duration
        case breathPhases = "breath_phases"
        case respiratoryRate = "respiratory_rate"
        case breathRegularity = "breath_regularity"
        case inhaleExhaleRatio = "inhale_exhale_ratio"
        case signalQuality = "signal_quality"
        case dominantFrequency = "dominant_frequency"
        case intensityScore = "intensity_score"
        case intensityConfidence = "intensity_confidence"
        case intervalState = "interval_state"
        case intervalStateConfidence = "interval_state_confidence"
        case intervalZone = "interval_zone"
    }

    var intensityLevel: IntensityLevel {
        IntensityLevel(rawValue: intensity.lowercased()) ?? .moderate
    }

    var latestBreathPhase: BreathPhaseEvent? {
        breathPhases?.last(where: { $0.type != "pause" })
    }

    var effectiveRespiratoryRate: Double {
        respiratoryRate ?? tempo
    }
}

// MARK: - Breath Phase Event

struct BreathPhaseEvent: Codable, Identifiable {
    var id: String { "\(type)-\(start)" }
    let type: String       // "inhale", "exhale", "pause"
    let start: Double
    let end: Double
    let confidence: Double

    enum CodingKeys: String, CodingKey {
        case type, start, end, confidence
    }

    var duration: Double { end - start }

    var displayName: String {
        switch type {
        case "inhale": return "Inhale"
        case "exhale": return "Exhale"
        case "pause": return "Pause"
        default: return type.capitalized
        }
    }

    var icon: String {
        switch type {
        case "inhale": return "arrow.down.circle"
        case "exhale": return "arrow.up.circle"
        case "pause": return "pause.circle"
        default: return "circle"
        }
    }
}

// MARK: - Intensity Level

enum IntensityLevel: String, CaseIterable {
    case calm = "calm"
    case moderate = "moderate"
    case intense = "intense"
    case critical = "critical"

    var displayName: String {
        switch self {
        case .calm: return "Calm"
        case .moderate: return "Moderate"
        case .intense: return "Intense"
        case .critical: return "Critical"
        }
    }

    var emoji: String {
        switch self {
        case .calm: return "😌"
        case .moderate: return "💪"
        case .intense: return "🔥"
        case .critical: return "⚠️"
        }
    }

    var color: String {
        switch self {
        case .calm:     return "4ECDC4"
        case .moderate: return "FF6B35"
        case .intense:  return "FFD93D"
        case .critical: return "FF4757"
        }
    }
}

// MARK: - Continuous Coach Response

struct ContinuousCoachResponse: Codable {
    let contractVersion: String?
    let text: String
    let shouldSpeak: Bool
    let breathAnalysis: BreathAnalysis
    let audioURL: String?
    let waitSeconds: Double
    let phase: String
    let reason: String?
    let coachScore: Int?
    let coachScoreLine: String?
    let brainProvider: String?
    let brainSource: String?
    let brainStatus: String?
    let brainMode: String?
    let coachingStyle: String?
    let intervalTemplate: String?
    let zoneStatus: String?
    let zoneEvent: String?
    let heartRate: Int?
    let targetZoneLabel: String?
    let targetHRLow: Int?
    let targetHRHigh: Int?
    let targetSource: String?
    let targetHREnforced: Bool?
    let hrQuality: String?
    let hrQualityReasons: [String]?
    let movementScore: Double?
    let cadenceSPM: Double?
    let movementSource: String?
    let movementState: String?
    let zoneScoreConfidence: String?
    let zoneTimeInTargetPct: Double?
    let zoneOvershoots: Int?
    let recoverySeconds: Double?
    let recoveryAvgSeconds: Double?
    let personalizationTip: String?
    let recoveryLine: String?
    let recoveryBaselineSeconds: Double?
    let coachScoreV2: Int?
    let coachScoreComponents: CoachScoreComponents?
    let capReasonCodes: [String]?
    let capApplied: Int?
    let capAppliedReason: String?
    let hrValidMainSetSeconds: Double?
    let zoneValidMainSetSeconds: Double?
    let zoneCompliance: Double?
    let breathAvailableReliable: Bool?
    let events: [CoachingEvent]?
    let zonePrimaryEvent: String?
    let zonePriority: Int?
    let zonePhraseId: String?
    let sensorMode: String?
    let phaseId: Int?
    let zoneState: String?
    let deltaToBand: Int?
    let workoutContextSummary: WorkoutContextSummary?

    enum CodingKeys: String, CodingKey {
        case contractVersion = "contract_version"
        case text
        case shouldSpeak = "should_speak"
        case breathAnalysis = "breath_analysis"
        case audioURL = "audio_url"
        case waitSeconds = "wait_seconds"
        case phase
        case reason
        case coachScore = "coach_score"
        case coachScoreLine = "coach_score_line"
        case brainProvider = "brain_provider"
        case brainSource = "brain_source"
        case brainStatus = "brain_status"
        case brainMode = "brain_mode"
        case coachingStyle = "coaching_style"
        case intervalTemplate = "interval_template"
        case zoneStatus = "zone_status"
        case zoneEvent = "zone_event"
        case heartRate = "heart_rate"
        case targetZoneLabel = "target_zone_label"
        case targetHRLow = "target_hr_low"
        case targetHRHigh = "target_hr_high"
        case targetSource = "target_source"
        case targetHREnforced = "target_hr_enforced"
        case hrQuality = "hr_quality"
        case hrQualityReasons = "hr_quality_reasons"
        case movementScore = "movement_score"
        case cadenceSPM = "cadence_spm"
        case movementSource = "movement_source"
        case movementState = "movement_state"
        case zoneScoreConfidence = "zone_score_confidence"
        case zoneTimeInTargetPct = "zone_time_in_target_pct"
        case zoneOvershoots = "zone_overshoots"
        case recoverySeconds = "recovery_seconds"
        case recoveryAvgSeconds = "recovery_avg_seconds"
        case personalizationTip = "personalization_tip"
        case recoveryLine = "recovery_line"
        case recoveryBaselineSeconds = "recovery_baseline_seconds"
        case coachScoreV2 = "coach_score_v2"
        case coachScoreComponents = "coach_score_components"
        case capReasonCodes = "cap_reason_codes"
        case capApplied = "cap_applied"
        case capAppliedReason = "cap_applied_reason"
        case hrValidMainSetSeconds = "hr_valid_main_set_seconds"
        case zoneValidMainSetSeconds = "zone_valid_main_set_seconds"
        case zoneCompliance = "zone_compliance"
        case breathAvailableReliable = "breath_available_reliable"
        case events
        case zonePrimaryEvent = "zone_primary_event"
        case zonePriority = "zone_priority"
        case zonePhraseId = "zone_phrase_id"
        case sensorMode = "sensor_mode"
        case phaseId = "phase_id"
        case zoneState = "zone_state"
        case deltaToBand = "delta_to_band"
        case workoutContextSummary = "workout_context_summary"
    }
}

struct WorkoutContextSummary: Codable {
    let phase: String?
    let elapsedS: Int?
    let timeLeftS: Int?
    let repIndex: Int?
    let repsTotal: Int?
    let repRemainingS: Int?
    let repsRemainingIncludingCurrent: Int?
    let elapsedSource: String?

    enum CodingKeys: String, CodingKey {
        case phase
        case elapsedS = "elapsed_s"
        case timeLeftS = "time_left_s"
        case repIndex = "rep_index"
        case repsTotal = "reps_total"
        case repRemainingS = "rep_remaining_s"
        case repsRemainingIncludingCurrent = "reps_remaining_including_current"
        case elapsedSource = "elapsed_source"
    }
}

struct PostWorkoutSummaryContext: Codable, Equatable {
    let workoutMode: String
    let workoutLabel: String
    let durationText: String
    let finalHeartRateText: String
    let coachScore: Int
    let coachScoreSummaryLine: String
    let zoneTimeInTargetPct: Double?
    let zoneOvershoots: Int
    let phase: String?
    let elapsedS: Int?
    let timeLeftS: Int?
    let repIndex: Int?
    let repsTotal: Int?
    let repRemainingS: Int?
    let repsRemainingIncludingCurrent: Int?
    let elapsedSource: String?
    let averageHeartRate: Int?
    let distanceMeters: Double?
    let coachingStyle: String?

    enum CodingKeys: String, CodingKey {
        case workoutMode = "workout_mode"
        case workoutLabel = "workout_label"
        case durationText = "duration_text"
        case finalHeartRateText = "final_heart_rate_text"
        case coachScore = "coach_score"
        case coachScoreSummaryLine = "coach_score_summary_line"
        case zoneTimeInTargetPct = "zone_time_in_target_pct"
        case zoneOvershoots = "zone_overshoots"
        case phase
        case elapsedS = "elapsed_s"
        case timeLeftS = "time_left_s"
        case repIndex = "rep_index"
        case repsTotal = "reps_total"
        case repRemainingS = "rep_remaining_s"
        case repsRemainingIncludingCurrent = "reps_remaining_including_current"
        case elapsedSource = "elapsed_source"
        case averageHeartRate = "average_heart_rate"
        case distanceMeters = "distance_meters"
        case coachingStyle = "coaching_style"
    }

    func fallbackPrompt(for question: String, languageCode: String) -> String {
        let isNorwegian = languageCode.lowercased() == "no"
        let spokenDurationText = verbalizedDurationText(languageCode: languageCode)
        let workoutReference = normalizedWorkoutReference(languageCode: languageCode)
        var lines = [
            isNorwegian ? "Oppsummering fra den siste treningsokten:" : "Summary from the last workout:",
            isNorwegian ? "- Oekt: \(workoutReference)" : "- Workout: \(workoutReference)",
            isNorwegian ? "- Varighet: \(spokenDurationText)" : "- Duration: \(spokenDurationText)",
            isNorwegian ? "- Sluttpuls: \(finalHeartRateText)" : "- Final heart rate: \(finalHeartRateText)",
            isNorwegian ? "- Coach score: \(coachScore)" : "- Coach score: \(coachScore)",
            isNorwegian ? "- Oppsummering: \(coachScoreSummaryLine)" : "- Summary: \(coachScoreSummaryLine)",
        ]

        if let zoneTimeInTargetPct {
            let normalizedPct = zoneTimeInTargetPct <= 1 ? zoneTimeInTargetPct * 100.0 : zoneTimeInTargetPct
            let pctText = String(format: "%.0f%%", normalizedPct)
            lines.append(isNorwegian ? "- Tid i malsonen: \(pctText)" : "- Time in target zone: \(pctText)")
        }

        lines.append(isNorwegian ? "- Overshoots over malsonen: \(zoneOvershoots)" : "- Zone overshoots: \(zoneOvershoots)")

        if let avgHR = averageHeartRate, avgHR > 0 {
            lines.append(isNorwegian ? "- Gjennomsnittspuls: \(avgHR) BPM" : "- Average heart rate: \(avgHR) BPM")
        }

        if let dist = distanceMeters, dist > 0 {
            let km = dist / 1000.0
            let distText = String(format: "%.2f km", km)
            lines.append(isNorwegian ? "- Distanse: \(distText)" : "- Distance: \(distText)")
        }

        if let style = coachingStyle, !style.isEmpty {
            lines.append(isNorwegian ? "- Intensitetsniva: \(style)" : "- Intensity level: \(style)")
        }

        if let phase, !phase.isEmpty {
            lines.append(isNorwegian ? "- Siste fase: \(phase)" : "- Last phase: \(phase)")
        }

        lines.append("")
        lines.append(
            isNorwegian
                ? "Denne coach-samtalen er kun for løpeøkter. Behandle også generiske etiketter som 'Økt' som en generell løpeøkt."
                : "This coach conversation is for running workouts only. Treat generic labels like 'Workout' as a general running workout."
        )
        lines.append(
            isNorwegian
                ? "I første svar skal du bare bruke sammendraget fra denne økten, ikke eldre økter eller historikk."
                : "In the first reply, use only the summary from this workout, not older workouts or history."
        )
        lines.append(
            isNorwegian
                ? "Hvis etiketten er generisk som 'Økt' eller 'Standard', omtaler du den som en generell løpeøkt i stedet for å gjenta råetiketten."
                : "If the label is generic like 'Workout' or 'Standard', refer to it as a general running workout instead of repeating the raw label."
        )
        lines.append(
            isNorwegian
                ? "Hvis sammendraget er generisk, veldig kort eller tynt, holder du første svar generelt og løpsspesifikt."
                : "If the summary is generic, very short, or sparse, keep the first reply generic and running-specific."
        )
        lines.append(
            isNorwegian
                ? "Tolk timerverdier bokstavelig. Hvis tiden vises som MM:SS, betyr 00:07 syv sekunder, ikke sju minutter."
                : "Interpret timer strings literally. If the timer is shown as MM:SS, then 00:07 means 7 seconds, not 7 minutes."
        )
        if let durationSeconds = resolvedDurationSeconds(), durationSeconds < 60 {
            let shortDurationText = verbalizedDurationText(languageCode: languageCode)
            lines.append(
                isNorwegian
                    ? "Denne økten var bare \(shortDurationText). Behandle den som en veldig kort eller tidlig avsluttet løpeøkt, ikke som en statisk hold eller styrkeøvelse."
                    : "This workout lasted only \(shortDurationText). Treat it as a very short or early-stopped running session, not as a static hold or strength exercise."
            )
        }
        lines.append(
            isNorwegian
                ? "Ikke nevn styrketrening, gymøvelser eller spesifikke øvelser som squats, lunges, push-ups, burpees eller planker."
                : "Do not mention strength training, gym work, or specific exercises such as squats, lunges, push-ups, burpees, or planks."
        )
        lines.append(
            isNorwegian
                ? "Ikke si at du la merke til en spesifikk øvelse tidligere med mindre sammendraget faktisk nevner den."
                : "Do not say you noticed the athlete doing a specific exercise earlier unless the summary explicitly names it."
        )

        lines.append("")
        lines.append(isNorwegian ? "Sporsmal: \(question)" : "Question: \(question)")
        return lines.joined(separator: "\n")
    }

    private func normalizedWorkoutReference(languageCode: String) -> String {
        let isNorwegian = languageCode.lowercased() == "no"
        let normalizedLabel = workoutLabel
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .folding(options: [.diacriticInsensitive, .caseInsensitive], locale: Locale(identifier: isNorwegian ? "no_NO" : "en_US"))
            .lowercased()
        let normalizedMode = workoutMode.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()

        if normalizedMode == WorkoutMode.easyRun.rawValue || normalizedLabel.contains("easy") || normalizedLabel.contains("rolig") {
            return isNorwegian ? "Rolig tur" : "Easy Run"
        }

        if normalizedMode == WorkoutMode.intervals.rawValue || normalizedLabel.contains("interval") || normalizedLabel.contains("intervall") {
            return isNorwegian ? "Intervaller" : "Intervals"
        }

        let genericLabels = Set(["", "workout", "standard", "okt", "okt"])
        if normalizedMode == WorkoutMode.standard.rawValue || genericLabels.contains(normalizedLabel) {
            return isNorwegian ? "Generell løpeøkt" : "General running workout"
        }

        return workoutLabel
    }

    private func resolvedDurationSeconds() -> Int? {
        if let elapsedS, elapsedS >= 0 {
            return elapsedS
        }

        let parts = durationText.split(separator: ":").map(String.init)
        guard (2...3).contains(parts.count) else { return nil }
        let numbers = parts.compactMap(Int.init)
        guard numbers.count == parts.count else { return nil }

        if numbers.count == 2 {
            return (numbers[0] * 60) + numbers[1]
        }

        return (numbers[0] * 3600) + (numbers[1] * 60) + numbers[2]
    }

    private func verbalizedDurationText(languageCode: String) -> String {
        let isNorwegian = languageCode.lowercased() == "no"
        guard let totalSeconds = resolvedDurationSeconds() else {
            return durationText
        }

        let hours = totalSeconds / 3600
        let minutes = (totalSeconds % 3600) / 60
        let seconds = totalSeconds % 60
        var parts: [String] = []

        if hours > 0 {
            parts.append(
                isNorwegian
                    ? "\(hours) \(hours == 1 ? "time" : "timer")"
                    : "\(hours) \(hours == 1 ? "hour" : "hours")"
            )
        }

        if minutes > 0 {
            parts.append(
                isNorwegian
                    ? "\(minutes) \(minutes == 1 ? "minutt" : "minutter")"
                    : "\(minutes) \(minutes == 1 ? "minute" : "minutes")"
            )
        }

        if seconds > 0 || parts.isEmpty {
            parts.append(
                isNorwegian
                    ? "\(seconds) \(seconds == 1 ? "sekund" : "sekunder")"
                    : "\(seconds) \(seconds == 1 ? "second" : "seconds")"
            )
        }

        return parts.joined(separator: " ")
    }

    func telemetryMetadata() -> [String: String] {
        [
            "workout_mode": workoutMode,
            "workout_label": workoutLabel,
            "coach_score": String(coachScore),
            "duration_text": durationText,
        ]
    }
}

struct CoachingEvent: Codable, Identifiable {
    var id: String { "\(eventType)-\(ts)" }
    let eventType: String
    let priority: Int?
    let phraseId: String?
    let ts: Double
    let payload: CoachingEventPayload

    enum CodingKeys: String, CodingKey {
        case eventType = "event_type"
        case priority
        case phraseId = "phrase_id"
        case ts
        case payload
    }
}

struct CoachingEventPayload: Codable {
    let sessionId: String
    let workoutType: String
    let phase: String
    let selectedIntensity: String
    let hrBPM: Int
    let targetLow: Int?
    let targetHigh: Int?
    let targetEnforced: Bool
    let zoneState: String
    let deltaToBand: Int?
    let elapsedSeconds: Int
    let remainingPhaseSeconds: Int?
    let phaseId: Int

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case workoutType = "workout_type"
        case phase
        case selectedIntensity = "selected_intensity"
        case hrBPM = "hr_bpm"
        case targetLow = "target_low"
        case targetHigh = "target_high"
        case targetEnforced = "target_enforced"
        case zoneState = "zone_state"
        case deltaToBand = "delta_to_band"
        case elapsedSeconds = "elapsed_seconds"
        case remainingPhaseSeconds = "remaining_phase_seconds"
        case phaseId = "phase_id"
    }
}

struct CoachScoreComponents: Codable {
    let zone: Int?
    let breath: Int?
    let duration: Int?
    let zoneAvailable: Bool?
    let breathInPlay: Bool?
    let breathAvailableReliable: Bool?
    let breathEnabledByUser: Bool?
    let micPermissionGranted: Bool?
    let breathConfidence: Double?
    let breathSampleCount: Int?
    let breathMedianQuality: Double?
    let zoneCompliance: Double?
    let hrValidMainSetSeconds: Double?
    let zoneValidMainSetSeconds: Double?
    let mainSetSeconds: Double?

    enum CodingKeys: String, CodingKey {
        case zone
        case breath
        case duration
        case zoneAvailable = "zone_available"
        case breathInPlay = "breath_in_play"
        case breathAvailableReliable = "breath_available_reliable"
        case breathEnabledByUser = "breath_enabled_by_user"
        case micPermissionGranted = "mic_permission_granted"
        case breathConfidence = "breath_confidence"
        case breathSampleCount = "breath_sample_count"
        case breathMedianQuality = "breath_median_quality"
        case zoneCompliance = "zone_compliance"
        case hrValidMainSetSeconds = "hr_valid_main_set_seconds"
        case zoneValidMainSetSeconds = "zone_valid_main_set_seconds"
        case mainSetSeconds = "main_set_seconds"
    }
}

// MARK: - Workout Record

struct WorkoutRecord: Identifiable, Codable {
    let id: UUID
    let date: Date
    let durationSeconds: Int
    let finalPhase: String
    let avgIntensity: String
    let personaUsed: String
    let coachScore: Int?

    init(id: UUID = UUID(), date: Date = Date(), durationSeconds: Int, finalPhase: String = "cooldown", avgIntensity: String = "moderate", personaUsed: String = "personal_trainer", coachScore: Int? = nil) {
        self.id = id
        self.date = date
        self.durationSeconds = durationSeconds
        self.finalPhase = finalPhase
        self.avgIntensity = avgIntensity
        self.personaUsed = personaUsed
        self.coachScore = coachScore
    }

    // Backward compat: init from old WorkoutPhase + intensity String
    init(id: UUID = UUID(), date: Date = Date(), durationSeconds: Int, phase: WorkoutPhase, intensity: String) {
        self.id = id
        self.date = date
        self.durationSeconds = durationSeconds
        self.finalPhase = phase.rawValue
        self.avgIntensity = intensity
        self.personaUsed = "personal_trainer"
        self.coachScore = nil
    }

    var durationFormatted: String {
        let mins = durationSeconds / 60
        let secs = durationSeconds % 60
        if mins > 0 {
            return "\(mins)m \(secs)s"
        }
        return "\(secs)s"
    }

    var formattedDuration: String { durationFormatted }

    var dateFormatted: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: date)
    }

    var dayOfWeek: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE"
        return formatter.string(from: date)
    }

    // Legacy compatibility
    var phase: WorkoutPhase {
        WorkoutPhase(rawValue: finalPhase) ?? .cooldown
    }

    var intensity: String { avgIntensity }
}

// MARK: - Coach Score Record

struct CoachScoreRecord: Identifiable, Codable {
    let id: UUID
    let date: Date
    let score: Int
    let capApplied: Int?
    let capAppliedReason: String?
    let zoneCompliance: Double?
    let hrValidMainSetSeconds: Double?
    let zoneValidMainSetSeconds: Double?

    init(
        id: UUID = UUID(),
        date: Date = Date(),
        score: Int,
        capApplied: Int? = nil,
        capAppliedReason: String? = nil,
        zoneCompliance: Double? = nil,
        hrValidMainSetSeconds: Double? = nil,
        zoneValidMainSetSeconds: Double? = nil
    ) {
        self.id = id
        self.date = date
        self.score = max(0, min(100, score))
        self.capApplied = capApplied
        self.capAppliedReason = capAppliedReason
        self.zoneCompliance = zoneCompliance
        self.hrValidMainSetSeconds = hrValidMainSetSeconds
        self.zoneValidMainSetSeconds = zoneValidMainSetSeconds
    }
}

extension Array where Element == CoachScoreRecord {
    func currentWorkoutStreak(calendar: Calendar = .autoupdatingCurrent) -> Int {
        let uniqueDays = Set(map { calendar.startOfDay(for: $0.date) })
        guard let mostRecentDay = uniqueDays.max() else { return 0 }

        let today = calendar.startOfDay(for: Date())
        let recency = calendar.dateComponents([.day], from: mostRecentDay, to: today).day ?? 0
        guard recency <= 1 else { return 0 }

        var streak = 0
        var cursor = mostRecentDay
        while uniqueDays.contains(cursor) {
            streak += 1
            guard let previousDay = calendar.date(byAdding: .day, value: -1, to: cursor) else {
                break
            }
            cursor = previousDay
        }
        return streak
    }
}

// MARK: - Coachi Progression

struct CoachiProgressState: Codable, Equatable {
    static let startingLevel = 1
    static let maximumLevel = 99
    static let xpPerLevel = 100

    let level: Int
    let xpInCurrentLevel: Int

    init(level: Int = CoachiProgressState.startingLevel, xpInCurrentLevel: Int = 0) {
        let clampedLevel = max(Self.startingLevel, min(Self.maximumLevel, level))
        self.level = clampedLevel
        if clampedLevel >= Self.maximumLevel {
            self.xpInCurrentLevel = Self.xpPerLevel
        } else {
            self.xpInCurrentLevel = max(0, min(Self.xpPerLevel - 1, xpInCurrentLevel))
        }
    }

    var levelLabel: String {
        "Lv.\(level)"
    }

    var isMaxLevel: Bool {
        level >= Self.maximumLevel
    }

    var xpFraction: Double {
        if isMaxLevel {
            return 1.0
        }
        return Double(xpInCurrentLevel) / Double(Self.xpPerLevel)
    }

    var xpToNextLevel: Int {
        if isMaxLevel {
            return 0
        }
        return max(0, Self.xpPerLevel - xpInCurrentLevel)
    }

    func applyingXPAward(_ xpAward: Int) -> CoachiProgressAward {
        let normalizedAward = max(0, xpAward)
        guard normalizedAward > 0, !isMaxLevel else {
            return CoachiProgressAward(
                xpAwarded: 0,
                levelBefore: level,
                levelAfter: level,
                xpBefore: xpInCurrentLevel,
                xpAfter: xpInCurrentLevel
            )
        }

        var nextLevel = level
        var nextXP = xpInCurrentLevel + normalizedAward

        while nextXP >= Self.xpPerLevel, nextLevel < Self.maximumLevel {
            nextXP -= Self.xpPerLevel
            nextLevel += 1
        }

        if nextLevel >= Self.maximumLevel {
            nextLevel = Self.maximumLevel
            nextXP = Self.xpPerLevel
        }

        return CoachiProgressAward(
            xpAwarded: normalizedAward,
            levelBefore: level,
            levelAfter: nextLevel,
            xpBefore: xpInCurrentLevel,
            xpAfter: nextXP
        )
    }
}

struct CoachiProgressAward: Equatable {
    let xpAwarded: Int
    let levelBefore: Int
    let levelAfter: Int
    let xpBefore: Int
    let xpAfter: Int

    var didLevelUp: Bool {
        levelAfter > levelBefore
    }

    var stateAfterAward: CoachiProgressState {
        CoachiProgressState(level: levelAfter, xpInCurrentLevel: xpAfter)
    }

    var xpProgressBeforeFraction: Double {
        if levelBefore >= CoachiProgressState.maximumLevel {
            return 1.0
        }
        return Double(xpBefore) / Double(CoachiProgressState.xpPerLevel)
    }

    var xpProgressAfterFraction: Double {
        stateAfterAward.xpFraction
    }
}

struct WorkoutCompletionSnapshot: Equatable {
    let durationText: String
    let finalHeartRateText: String
    let summaryContext: PostWorkoutSummaryContext
    let coachiProgressAward: CoachiProgressAward?
}

extension Notification.Name {
    static let coachiProgressDidChange = Notification.Name("coachiProgressDidChange")
}

enum CoachiProgressStore {
    private static let guestKey = "coachi_progress_guest"

    static func storageKey(for userID: String?) -> String {
        let normalized = userID?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !normalized.isEmpty else { return guestKey }
        return "coachi_progress_\(normalized)"
    }

    static func load(for userID: String?) -> CoachiProgressState {
        let defaults = UserDefaults.standard
        let key = storageKey(for: userID)
        guard let data = defaults.data(forKey: key),
              let decoded = try? JSONDecoder().decode(CoachiProgressState.self, from: data) else {
            return CoachiProgressState()
        }
        return decoded
    }

    static func save(_ state: CoachiProgressState, for userID: String?) {
        let defaults = UserDefaults.standard
        let key = storageKey(for: userID)
        if let data = try? JSONEncoder().encode(state) {
            defaults.set(data, forKey: key)
        }
        NotificationCenter.default.post(
            name: .coachiProgressDidChange,
            object: nil,
            userInfo: [
                "user_id": userID ?? "",
                "storage_key": key,
            ]
        )
    }

    static func awardXP(_ xpAward: Int, for userID: String?) -> CoachiProgressAward {
        let current = load(for: userID)
        let award = current.applyingXPAward(xpAward)
        if award.xpAwarded > 0 {
            save(award.stateAfterAward, for: userID)
        }
        return award
    }

    static func clearGuestProgress() {
        UserDefaults.standard.removeObject(forKey: guestKey)
        NotificationCenter.default.post(
            name: .coachiProgressDidChange,
            object: nil,
            userInfo: [
                "user_id": "",
                "storage_key": guestKey,
            ]
        )
    }
}

// MARK: - User Stats

struct UserStats {
    var totalWorkouts: Int = 0
    var totalMinutes: Int = 0
    var currentStreak: Int = 0
    var workoutsThisWeek: Int = 0
    var weeklyGoal: Int = 4
}

enum LiveCoachTranscriptRole: String {
    case user
    case assistant
    case system
}

struct LiveCoachTranscriptEntry: Identifiable, Equatable {
    let id: UUID
    let role: LiveCoachTranscriptRole
    let text: String
    let timestamp: Date
    let isPartial: Bool

    init(
        id: UUID = UUID(),
        role: LiveCoachTranscriptRole,
        text: String,
        timestamp: Date = Date(),
        isPartial: Bool = false
    ) {
        self.id = id
        self.role = role
        self.text = text
        self.timestamp = timestamp
        self.isPartial = isPartial
    }
}

struct ProductFlags: Codable, Equatable {
    let appFreeMode: Bool
    let billingEnabled: Bool
    let premiumSurfacesEnabled: Bool
    let monetizationPhase: String

    enum CodingKeys: String, CodingKey {
        case appFreeMode = "app_free_mode"
        case billingEnabled = "billing_enabled"
        case premiumSurfacesEnabled = "premium_surfaces_enabled"
        case monetizationPhase = "monetization_phase"
    }

    static let launchDefaults = ProductFlags(
        appFreeMode: true,
        billingEnabled: false,
        premiumSurfacesEnabled: false,
        monetizationPhase: "free_only"
    )

    var allowsPremiumGating: Bool {
        !appFreeMode && premiumSurfacesEnabled
    }
}

struct AppRuntimeResponse: Codable {
    let status: String
    let version: String?
    let timestamp: String?
    let productFlags: ProductFlags

    enum CodingKeys: String, CodingKey {
        case status
        case version
        case timestamp
        case productFlags = "product_flags"
    }
}

struct VoiceSessionBootstrap: Codable {
    let voiceSessionId: String
    let websocketURL: String
    let clientSecret: String
    let clientSecretExpiresAt: Int?
    let voice: String
    let model: String?
    let region: String?
    let maxDurationSeconds: Int
    let voiceAccessTier: String?
    let dailySessionLimit: Int?
    let sessionUpdateJSON: String

    enum CodingKeys: String, CodingKey {
        case voiceSessionId = "voice_session_id"
        case websocketURL = "websocket_url"
        case clientSecret = "client_secret"
        case clientSecretExpiresAt = "client_secret_expires_at"
        case voice
        case model
        case region
        case maxDurationSeconds = "max_duration_seconds"
        case voiceAccessTier = "voice_access_tier"
        case dailySessionLimit = "daily_session_limit"
        case sessionUpdateJSON = "session_update_json"
    }
}

// MARK: - Coach Talk Response

struct CoachTalkResponse: Codable {
    let contractVersion: String?
    let text: String
    let audioURL: String
    let personality: String
    let triggerSource: String?
    let provider: String?
    let mode: String?
    let latencyMS: Int?
    let fallbackUsed: Bool?
    let sttSource: String?
    let policyBlocked: Bool?
    let policyCategory: String?
    let policyReason: String?

    enum CodingKeys: String, CodingKey {
        case contractVersion = "contract_version"
        case text
        case audioURL = "audio_url"
        case personality
        case triggerSource = "trigger_source"
        case provider
        case mode
        case latencyMS = "latency_ms"
        case fallbackUsed = "fallback_used"
        case sttSource = "stt_source"
        case policyBlocked = "policy_blocked"
        case policyCategory = "policy_category"
        case policyReason = "policy_reason"
    }
}
