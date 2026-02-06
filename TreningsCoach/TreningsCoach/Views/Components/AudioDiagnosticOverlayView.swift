//
//  AudioDiagnosticOverlayView.swift
//  TreningsCoach
//
//  Compact diagnostic overlay for voice pipeline troubleshooting.
//  Shows: audio level, VAD state, wake-word status, signal path, event log.
//  Designed to float over workout UI without blocking it.
//
//  Toggle via triple-tap on the workout screen.
//

import SwiftUI

struct AudioDiagnosticOverlayView: View {
    @ObservedObject var diagnostics = AudioPipelineDiagnostics.shared
    @State private var showFullLog = false

    var body: some View {
        VStack(spacing: 0) {
            // Header bar with drag handle
            headerBar

            // Compact diagnostic content
            VStack(spacing: 8) {
                // 0. Mic Test Button
                micTestButton

                // 1. Audio Level + dB readout (compact)
                audioLevelRow

                // 2. Signal Path (MIC → AUDIO → VAD → WAKE → CMD)
                signalPathRow

                // 3. Wake Word Status (inline)
                wakeWordRow

                // 4. Event Log (collapsed by default)
                if showFullLog {
                    eventLogSection
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

    // MARK: - Header

    private var headerBar: some View {
        HStack(spacing: 6) {
            // Live dot
            Circle()
                .fill(diagnostics.isMicActive ? AppTheme.success : AppTheme.danger)
                .frame(width: 6, height: 6)

            Text("VOICE DIAGNOSTICS")
                .font(.system(size: 9, weight: .bold))
                .foregroundStyle(AppTheme.textPrimary.opacity(0.7))
                .tracking(0.8)

            Spacer()

            // Log toggle
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showFullLog.toggle()
                }
            } label: {
                Image(systemName: showFullLog ? "chevron.down" : "list.bullet")
                    .font(.system(size: 9))
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.6))
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

    // MARK: - Mic Test Button

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

    // MARK: - Audio Level Row (compact meter + dB)

    private var audioLevelRow: some View {
        HStack(spacing: 8) {
            // Level bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.white.opacity(0.08))

                    RoundedRectangle(cornerRadius: 3)
                        .fill(levelColor)
                        .frame(width: geo.size.width * CGFloat(diagnostics.audioLevel))
                        .animation(.linear(duration: 0.05), value: diagnostics.audioLevel)

                    // VAD threshold marker
                    Rectangle()
                        .fill(AppTheme.warning.opacity(0.5))
                        .frame(width: 1)
                        .offset(x: geo.size.width * CGFloat(diagnostics.vadThreshold * 5.0))
                }
            }
            .frame(height: 14)

            // dB readout
            Text(String(format: "%.0fdB", diagnostics.decibelLevel))
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(diagnostics.isVoiceDetected ? AppTheme.success : AppTheme.textSecondary.opacity(0.5))
                .frame(width: 38, alignment: .trailing)

            // VAD badge
            Text(diagnostics.isVoiceDetected ? "VOICE" : "—")
                .font(.system(size: 8, weight: .bold))
                .foregroundStyle(diagnostics.isVoiceDetected ? AppTheme.success : AppTheme.textSecondary.opacity(0.3))
                .frame(width: 32)
        }
    }

    // MARK: - Signal Path Row

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

    // MARK: - Wake Word Row (inline)

    private var wakeWordRow: some View {
        HStack(spacing: 6) {
            // Status pill
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

            // Recognizer badge
            Image(systemName: diagnostics.speechRecognizerAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                .font(.system(size: 8))
                .foregroundStyle(diagnostics.speechRecognizerAvailable ? AppTheme.success.opacity(0.6) : AppTheme.danger.opacity(0.6))

            Spacer()

            // Last utterance (if any)
            if let utterance = diagnostics.lastUtterance {
                Text("\"\(utterance)\"")
                    .font(.system(size: 8, design: .monospaced))
                    .foregroundStyle(AppTheme.secondaryAccent.opacity(0.8))
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
        }
    }

    // MARK: - Event Log (expandable)

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
