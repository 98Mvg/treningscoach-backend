//
//  AudioDiagnosticOverlayView.swift
//  TreningsCoach
//
//  Compact diagnostic overlay for troubleshooting voice pipeline + breath analysis.
//  Two tabs: Voice (mic/VAD/wake word) and Breath (backend DSP analysis).
//  Toggle via triple-tap on the workout screen.
//

import SwiftUI

struct AudioDiagnosticOverlayView: View {
    @ObservedObject var diagnostics: AudioPipelineDiagnostics = .shared
    @Binding var isPresented: Bool
    @State private var showFullLog = false

    init(diagnostics: AudioPipelineDiagnostics = .shared, isPresented: Binding<Bool>? = nil) {
        self._diagnostics = ObservedObject(wrappedValue: diagnostics)
        self._isPresented = isPresented ?? .constant(true)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header bar with tab selector
            headerBar

            // Tab content
            VStack(spacing: 8) {
                if diagnostics.diagnosticTab == .voice {
                    voiceDiagnosticsContent
                } else {
                    breathDiagnosticsContent
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
        }
        .background(.ultraThinMaterial)
        .background(Color.black.opacity(0.6))
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .overlay(
            RoundedRectangle(cornerRadius: 14)
                .stroke(AppTheme.primaryAccent.opacity(0.3), lineWidth: 0.5)
        )
        .padding(.horizontal, 12)
    }

    // MARK: - Header with Tabs

    private var headerBar: some View {
        HStack(spacing: 6) {
            // Live dot
            Circle()
                .fill(diagnostics.isMicActive ? AppTheme.success : AppTheme.danger)
                .frame(width: 6, height: 6)

            Text("DIAGNOSTICS")
                .font(.system(size: 9, weight: .bold))
                .foregroundStyle(AppTheme.textPrimary.opacity(0.7))
                .tracking(0.8)

            Spacer()

            // Tab selector
            HStack(spacing: 0) {
                tabButton("Voice", tab: .voice)
                tabButton("Breath", tab: .breath)
            }
            .background(Color.white.opacity(0.06))
            .clipShape(RoundedRectangle(cornerRadius: 5))

            Spacer()

            // Log toggle (voice tab only)
            if diagnostics.diagnosticTab == .voice {
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showFullLog.toggle()
                    }
                } label: {
                    Image(systemName: showFullLog ? "chevron.down" : "list.bullet")
                        .font(.system(size: 9))
                        .foregroundStyle(AppTheme.textSecondary.opacity(0.6))
                }
            }

            Button {
                diagnostics.isOverlayVisible = false
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
    }

    private func tabButton(_ label: String, tab: DiagnosticTab) -> some View {
        Button {
            withAnimation(.easeInOut(duration: 0.15)) {
                diagnostics.diagnosticTab = tab
            }
        } label: {
            Text(label)
                .font(.system(size: 8, weight: .semibold))
                .foregroundStyle(diagnostics.diagnosticTab == tab ? AppTheme.textPrimary : AppTheme.textSecondary.opacity(0.5))
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(diagnostics.diagnosticTab == tab ? AppTheme.primaryAccent.opacity(0.3) : Color.clear)
                .clipShape(RoundedRectangle(cornerRadius: 4))
        }
    }

    // MARK: - Voice Diagnostics Content (existing)

    private var voiceDiagnosticsContent: some View {
        VStack(spacing: 8) {
            micTestButton
            audioLevelRow
            signalPathRow
            wakeWordRow
            if showFullLog {
                eventLogSection
            }
        }
    }

    // MARK: - Breath Diagnostics Content (NEW)

    private var breathDiagnosticsContent: some View {
        VStack(spacing: 8) {
            if let analysis = diagnostics.lastBreathAnalysis {
                // Status row
                breathStatusRow

                // Signal quality bar
                breathSignalQualityRow(quality: analysis.signalQuality ?? 0)

                // Intensity badge
                breathIntensityRow(intensity: analysis.intensityLevel)

                // Metrics grid
                breathMetricsGrid(analysis: analysis)

                // Breath phases
                if let phases = analysis.breathPhases, !phases.isEmpty {
                    breathPhasesRow(phases: phases)
                }

                // Chunk + error info
                breathChunkInfoRow
            } else {
                // No data state
                breathNoDataView
            }
        }
    }

    // MARK: - Breath: Status Row

    private var breathStatusRow: some View {
        HStack(spacing: 8) {
            HStack(spacing: 3) {
                Circle()
                    .fill(AppTheme.success)
                    .frame(width: 5, height: 5)
                Text(diagnostics.timeSinceLastBreathAnalysis)
                    .font(.system(size: 8, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.7))
            }

            if let rtt = diagnostics.backendResponseTime {
                Text("RTT: \(Int(rtt * 1000))ms")
                    .font(.system(size: 8, weight: .medium, design: .monospaced))
                    .foregroundStyle(rtt < 1.0 ? AppTheme.success.opacity(0.7) : AppTheme.warning.opacity(0.7))
            }

            Spacer()

            Text("#\(diagnostics.breathAnalysisCount)")
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
        }
    }

    // MARK: - Breath: Signal Quality

    private func breathSignalQualityRow(quality: Double) -> some View {
        HStack(spacing: 8) {
            Text("Signal")
                .font(.system(size: 8, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.6))
                .frame(width: 35, alignment: .leading)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.white.opacity(0.08))

                    RoundedRectangle(cornerRadius: 3)
                        .fill(signalQualityColor(quality))
                        .frame(width: geo.size.width * CGFloat(min(quality, 1.0)))
                }
            }
            .frame(height: 10)

            Text(String(format: "%.2f", quality))
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(signalQualityColor(quality))
                .frame(width: 30, alignment: .trailing)
        }
    }

    private func signalQualityColor(_ quality: Double) -> Color {
        if quality < 0.3 { return AppTheme.danger }
        if quality < 0.6 { return AppTheme.warning }
        return AppTheme.success
    }

    // MARK: - Breath: Intensity

    private func breathIntensityRow(intensity: IntensityLevel) -> some View {
        HStack(spacing: 6) {
            Text("Intensity")
                .font(.system(size: 8, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.6))

            HStack(spacing: 4) {
                Circle()
                    .fill(breathIntensityColor(intensity))
                    .frame(width: 6, height: 6)
                Text(intensity.displayName.uppercased())
                    .font(.system(size: 8, weight: .bold))
                    .foregroundStyle(breathIntensityColor(intensity))
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(breathIntensityColor(intensity).opacity(0.15))
            .clipShape(Capsule())

            Spacer()
        }
    }

    private func breathIntensityColor(_ level: IntensityLevel) -> Color {
        switch level {
        case .calm: return AppTheme.secondaryAccent
        case .moderate: return AppTheme.primaryAccent
        case .intense: return AppTheme.warning
        case .critical: return AppTheme.danger
        }
    }

    // MARK: - Breath: Metrics Grid

    private func breathMetricsGrid(analysis: BreathAnalysis) -> some View {
        let intervalLabel: String = {
            guard let state = analysis.intervalState else { return "—" }
            if let zone = analysis.intervalZone {
                return "\(state.prefix(1).uppercased()) \(zone)"
            }
            return state
        }()

        return VStack(spacing: 4) {
            HStack(spacing: 0) {
                breathMetric("BPM", value: String(format: "%.0f", analysis.effectiveRespiratoryRate))
                breathMetric("Vol", value: String(format: "%.0f", analysis.volume))
                breathMetric("Silence", value: String(format: "%.0f%%", analysis.silence))
            }
            HStack(spacing: 0) {
                breathMetric("Reg", value: analysis.breathRegularity != nil ? String(format: "%.2f", analysis.breathRegularity!) : "—")
                breathMetric("I:E", value: analysis.inhaleExhaleRatio != nil ? String(format: "%.2f", analysis.inhaleExhaleRatio!) : "—")
                breathMetric("Freq", value: analysis.dominantFrequency != nil ? String(format: "%.0fHz", analysis.dominantFrequency!) : "—")
            }
            HStack(spacing: 0) {
                breathMetric("Score", value: analysis.intensityScore != nil ? String(format: "%.2f", analysis.intensityScore!) : "—")
                breathMetric("Conf", value: analysis.intensityConfidence != nil ? String(format: "%.2f", analysis.intensityConfidence!) : "—")
                breathMetric("Interval", value: intervalLabel)
            }
        }
    }

    private func breathMetric(_ label: String, value: String) -> some View {
        VStack(spacing: 1) {
            Text(value)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(AppTheme.textPrimary.opacity(0.9))
            Text(label)
                .font(.system(size: 7, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Breath: Phases

    private func breathPhasesRow(phases: [BreathPhaseEvent]) -> some View {
        HStack(spacing: 3) {
            Text("Phases")
                .font(.system(size: 7, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
                .frame(width: 32, alignment: .leading)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 2) {
                    ForEach(phases.suffix(8)) { phase in
                        HStack(spacing: 1) {
                            Text(phaseSymbol(phase.type))
                                .font(.system(size: 8))
                            Text(String(format: "%.0f%%", phase.confidence * 100))
                                .font(.system(size: 7, weight: .medium, design: .monospaced))
                        }
                        .foregroundStyle(phaseColor(phase.type))
                        .padding(.horizontal, 3)
                        .padding(.vertical, 2)
                        .background(phaseColor(phase.type).opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: 3))
                    }
                }
            }
        }
    }

    private func phaseSymbol(_ type: String) -> String {
        switch type {
        case "inhale": return "\u{2193}" // ↓
        case "exhale": return "\u{2191}" // ↑
        case "pause": return "\u{2016}"  // ‖
        default: return "?"
        }
    }

    private func phaseColor(_ type: String) -> Color {
        switch type {
        case "inhale": return AppTheme.secondaryAccent
        case "exhale": return AppTheme.primaryAccent
        case "pause": return AppTheme.textSecondary.opacity(0.5)
        default: return AppTheme.textSecondary
        }
    }

    // MARK: - Breath: Chunk Info

    private var breathChunkInfoRow: some View {
        HStack(spacing: 8) {
            if let bytes = diagnostics.chunkSizeBytes {
                Text("Chunk: \(bytes / 1024)KB")
                    .font(.system(size: 7, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
            }

            if let dur = diagnostics.chunkDuration {
                Text(String(format: "%.1fs", dur))
                    .font(.system(size: 7, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
            }

            if let analysis = diagnostics.lastBreathAnalysis,
               let quality = analysis.signalQuality {
                Text(String(format: "SQ: %.2f", quality))
                    .font(.system(size: 7, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
            }

            Spacer()

            if diagnostics.breathAnalysisErrors > 0 {
                Text("Errors: \(diagnostics.breathAnalysisErrors)")
                    .font(.system(size: 7, weight: .bold, design: .monospaced))
                    .foregroundStyle(AppTheme.danger.opacity(0.7))
            }

            if let reason = diagnostics.lastBreathReason {
                Text("Reason: \(reason)")
                    .font(.system(size: 7, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
        }
    }

    // MARK: - Breath: No Data

    private var breathNoDataView: some View {
        VStack(spacing: 6) {
            Image(systemName: "lungs")
                .font(.system(size: 20))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.3))

            Text("No breath data")
                .font(.system(size: 10, weight: .semibold))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.5))

            Text("Start a workout to see breath analysis")
                .font(.system(size: 8))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.3))

            // Show last error message for debugging
            if let error = diagnostics.lastBreathError {
                VStack(spacing: 2) {
                    Text("Last error:")
                        .font(.system(size: 7, weight: .bold))
                        .foregroundStyle(AppTheme.danger.opacity(0.7))
                    Text(error)
                        .font(.system(size: 7, design: .monospaced))
                        .foregroundStyle(AppTheme.danger.opacity(0.6))
                        .multilineTextAlignment(.center)
                        .lineLimit(4)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(AppTheme.danger.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }

            if diagnostics.breathAnalysisErrors > 0 {
                Text("Total errors: \(diagnostics.breathAnalysisErrors)")
                    .font(.system(size: 8, weight: .bold))
                    .foregroundStyle(AppTheme.danger.opacity(0.6))
            }

            // Show tick count even when no data (to see if loop is running)
            if diagnostics.breathAnalysisCount > 0 {
                Text("Ticks received: \(diagnostics.breathAnalysisCount)")
                    .font(.system(size: 7, weight: .medium, design: .monospaced))
                    .foregroundStyle(AppTheme.success.opacity(0.6))
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
    }

    // MARK: - Voice Tab: Existing Views

    private var micTestButton: some View {
        Button {
            if diagnostics.isMicTestRunning {
                diagnostics.stopMicTest()
            } else {
                diagnostics.startMicTest()
            }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: diagnostics.isMicTestRunning ? "stop.fill" : "mic.fill")
                    .font(.system(size: 9))
                Text(diagnostics.isMicTestRunning ? "Stop Test" : "Test Mic")
                    .font(.system(size: 10, weight: .semibold))
            }
            .foregroundStyle(diagnostics.isMicTestRunning ? AppTheme.danger : AppTheme.secondaryAccent)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 6)
            .background(
                (diagnostics.isMicTestRunning ? AppTheme.danger : AppTheme.secondaryAccent)
                    .opacity(0.12)
            )
            .clipShape(RoundedRectangle(cornerRadius: 6))
        }
    }

    private var audioLevelRow: some View {
        HStack(spacing: 8) {
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.white.opacity(0.08))

                    RoundedRectangle(cornerRadius: 3)
                        .fill(levelColor)
                        .frame(width: geo.size.width * CGFloat(diagnostics.audioLevel))
                        .animation(.linear(duration: 0.05), value: diagnostics.audioLevel)

                    Rectangle()
                        .fill(AppTheme.warning.opacity(0.5))
                        .frame(width: 1)
                        .offset(x: geo.size.width * CGFloat(diagnostics.vadThreshold * 5.0))
                }
            }
            .frame(height: 14)

            Text(String(format: "%.0fdB", diagnostics.decibelLevel))
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(diagnostics.isVoiceDetected ? AppTheme.success : AppTheme.textSecondary.opacity(0.5))
                .frame(width: 38, alignment: .trailing)

            Text(diagnostics.isVoiceDetected ? "VOICE" : "\u{2014}")
                .font(.system(size: 8, weight: .bold))
                .foregroundStyle(diagnostics.isVoiceDetected ? AppTheme.success : AppTheme.textSecondary.opacity(0.3))
                .frame(width: 32)
        }
    }

    private var signalPathRow: some View {
        HStack(spacing: 3) {
            signalNode("MIC", active: diagnostics.isMicActive, icon: "mic.fill")
            signalArrow(active: diagnostics.isMicActive)
            signalNode("AUDIO", active: diagnostics.framesReceived > 0, icon: "waveform")
            signalArrow(active: diagnostics.isVoiceDetected)
            signalNode("VAD", active: diagnostics.isVoiceDetected, icon: "ear.fill")
            signalArrow(active: diagnostics.isWakeWordListening)
            signalNode("WAKE", active: diagnostics.wakeWordDetected, icon: "text.bubble.fill")
            signalArrow(active: diagnostics.wakeWordDetected)
            signalNode("CMD", active: diagnostics.lastUtterance != nil, icon: "arrow.up.circle.fill")
        }
    }

    private var wakeWordRow: some View {
        HStack(spacing: 6) {
            HStack(spacing: 3) {
                Circle()
                    .fill(wakeWordStatusColor)
                    .frame(width: 5, height: 5)
                Text(wakeWordStatusText)
                    .font(.system(size: 8, weight: .medium))
                    .foregroundStyle(wakeWordStatusColor)
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(wakeWordStatusColor.opacity(0.12))
            .clipShape(Capsule())

            Image(systemName: diagnostics.speechRecognizerAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                .font(.system(size: 8))
                .foregroundStyle(diagnostics.speechRecognizerAvailable ? AppTheme.success.opacity(0.6) : AppTheme.danger.opacity(0.6))

            Spacer()

            if let utterance = diagnostics.lastUtterance {
                Text("\"\(utterance)\"")
                    .font(.system(size: 8, design: .monospaced))
                    .foregroundStyle(AppTheme.secondaryAccent.opacity(0.8))
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
        }
    }

    private var eventLogSection: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text("LOG")
                    .font(.system(size: 8, weight: .bold))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.5))

                Spacer()

                Button {
                    diagnostics.events.removeAll()
                } label: {
                    Text("Clear")
                        .font(.system(size: 8))
                        .foregroundStyle(AppTheme.danger.opacity(0.6))
                }
            }

            ForEach(Array(diagnostics.events.prefix(6))) { event in
                HStack(spacing: 4) {
                    Text(event.timeString)
                        .font(.system(size: 7, design: .monospaced))
                        .foregroundStyle(AppTheme.textSecondary.opacity(0.4))

                    Text(event.stage.rawValue)
                        .font(.system(size: 7, weight: .bold, design: .monospaced))
                        .foregroundStyle(stageColor(event.stage))
                        .frame(width: 75, alignment: .leading)

                    Text(event.detail)
                        .font(.system(size: 7, design: .monospaced))
                        .foregroundStyle(AppTheme.textPrimary.opacity(0.6))
                        .lineLimit(1)

                    Spacer()
                }
            }

            if diagnostics.events.isEmpty {
                Text("No events yet.")
                    .font(.system(size: 8))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.3))
            }
        }
    }

    // MARK: - Helper Views

    private func signalNode(_ label: String, active: Bool, icon: String) -> some View {
        VStack(spacing: 1) {
            Image(systemName: icon)
                .font(.system(size: 8))
                .foregroundStyle(active ? AppTheme.success : AppTheme.textSecondary.opacity(0.2))
            Text(label)
                .font(.system(size: 6, weight: .bold))
                .foregroundStyle(active ? AppTheme.textPrimary.opacity(0.8) : AppTheme.textSecondary.opacity(0.2))
        }
        .frame(width: 32, height: 28)
        .background(active ? AppTheme.success.opacity(0.12) : Color.white.opacity(0.02))
        .clipShape(RoundedRectangle(cornerRadius: 5))
        .overlay(
            RoundedRectangle(cornerRadius: 5)
                .stroke(active ? AppTheme.success.opacity(0.3) : Color.clear, lineWidth: 0.5)
        )
    }

    private func signalArrow(active: Bool) -> some View {
        Image(systemName: "chevron.right")
            .font(.system(size: 6, weight: .bold))
            .foregroundStyle(active ? AppTheme.success.opacity(0.5) : AppTheme.textSecondary.opacity(0.15))
    }

    // MARK: - Computed

    private var levelColor: LinearGradient {
        LinearGradient(
            colors: [AppTheme.success, AppTheme.warning, AppTheme.danger],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    private var wakeWordStatusColor: Color {
        if diagnostics.wakeWordDetected { return AppTheme.warning }
        if diagnostics.isWakeWordListening { return AppTheme.success }
        return AppTheme.textSecondary
    }

    private var wakeWordStatusText: String {
        if diagnostics.wakeWordDetected { return "DETECTED!" }
        if diagnostics.isWakeWordListening { return "Listening..." }
        return "Inactive"
    }

    private func stageColor(_ stage: PipelineStage) -> Color {
        switch stage {
        case .micInit, .micActive: return AppTheme.secondaryAccent
        case .audioFrame: return AppTheme.textSecondary
        case .vadSilence: return AppTheme.textSecondary.opacity(0.5)
        case .vadVoice: return AppTheme.success
        case .wakeWordListening: return AppTheme.primaryAccent
        case .wakeWordDetected: return AppTheme.warning
        case .utteranceCapture, .utteranceFinalized: return AppTheme.secondaryAccent
        case .speechRecogError: return AppTheme.danger
        case .backendSend, .backendResponse: return AppTheme.primaryAccent
        case .ttsPlayback: return AppTheme.warning
        }
    }
}
