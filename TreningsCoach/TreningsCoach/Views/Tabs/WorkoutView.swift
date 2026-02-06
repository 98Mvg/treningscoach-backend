//
//  WorkoutView.swift
//  TreningsCoach
//
//  Main workout screen — audio-first, glanceable design
//  Voice orb at center with timer ring, phase indicator
//  Coach personality selector during main workout phase
//

import SwiftUI

struct WorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel

    var body: some View {
        ZStack {
            // Dark background
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {

                // MARK: - Phase Indicator (top)
                if viewModel.isContinuousMode {
                    phaseIndicator
                        .padding(.top, 20)
                        .transition(.opacity)
                }

                Spacer()

                // MARK: - Personality Selector (during main workout)
                if viewModel.isContinuousMode && viewModel.currentPhase == .intense {
                    PersonalitySelectorView(
                        selectedPersonality: $viewModel.activePersonality
                    ) { personality in
                        viewModel.switchPersonality(personality)
                    }
                    .padding(.bottom, 12)
                    .transition(.opacity)
                }

                // MARK: - Voice Orb / Workout Player (center)
                ZStack {
                    if viewModel.isContinuousMode {
                        // Show workout player with controls
                        WorkoutPlayerView(
                            elapsedTime: viewModel.elapsedTime,
                            totalTime: AppConfig.ContinuousCoaching.maxWorkoutDuration,
                            isPaused: viewModel.isPaused,
                            onPlayPause: {
                                viewModel.togglePause()
                            },
                            onStop: {
                                viewModel.stopContinuousWorkout()
                            }
                        )
                        .transition(.scale.combined(with: .opacity))
                    } else {
                        // Show voice orb for starting workout
                        VoiceOrbView(state: viewModel.voiceState) {
                            if viewModel.isRecording {
                                viewModel.stopRecording()
                            } else {
                                viewModel.startContinuousWorkout()
                            }
                        }
                        .transition(.scale.combined(with: .opacity))
                    }
                }


                // MARK: - Intensity Badge + Breath Phase
                if viewModel.isContinuousMode, let analysis = viewModel.breathAnalysis {
                    VStack(spacing: 6) {
                        intensityBadge(level: analysis.intensityLevel)

                        // Breath phase indicator (only when DSP data available)
                        if let phase = analysis.latestBreathPhase {
                            breathPhaseIndicator(phase: phase)
                                .transition(.opacity)
                        }

                        // Real respiratory rate
                        if let rate = analysis.respiratoryRate {
                            Text("\(Int(rate)) BPM")
                                .font(.caption2.weight(.medium).monospacedDigit())
                                .foregroundStyle(AppTheme.textSecondary.opacity(0.7))
                        }
                    }
                    .padding(.top, 8)
                    .transition(.opacity)
                }

                // Hint text when idle
                if !viewModel.isContinuousMode {
                    Text(L10n.tapToStart)
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                        .padding(.top, 16)
                }

                Spacer()

                // MARK: - Skip Warmup Button
                if viewModel.isContinuousMode && viewModel.currentPhase == .warmup {
                    Button {
                        viewModel.skipToIntensePhase()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "forward.fill")
                                .font(.caption)
                            Text(L10n.skipToWorkout)
                                .font(.subheadline.weight(.semibold))
                        }
                        .foregroundStyle(AppTheme.secondaryAccent)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(AppTheme.secondaryAccent.opacity(0.15))
                        .clipShape(Capsule())
                    }
                    .transition(.opacity)
                }

                // MARK: - Wake Word Indicator
                if viewModel.isContinuousMode {
                    wakeWordIndicator
                        .padding(.top, 8)
                        .transition(.opacity)
                }


                Spacer()
                    .frame(height: 20)
            }
            .padding(.bottom, 80) // Space for tab bar
            .animation(.spring(response: 0.5, dampingFraction: 0.8), value: viewModel.isContinuousMode)
            .animation(.spring(response: 0.3, dampingFraction: 0.9), value: viewModel.isPaused)
        }
        // Error alert
        .alert(L10n.error, isPresented: $viewModel.showError) {
            Button(L10n.ok, role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage)
        }
    }

    // MARK: - Phase Indicator

    private var phaseIndicator: some View {
        HStack(spacing: 4) {
            ForEach(WorkoutPhase.allCases) { phase in
                HStack(spacing: 4) {
                    Image(systemName: phaseIcon(for: phase))
                        .font(.caption2)

                    Text(phaseLabel(for: phase))
                        .font(.caption.weight(.medium))
                }
                .foregroundStyle(
                    viewModel.currentPhase == phase
                        ? AppTheme.textPrimary
                        : AppTheme.textSecondary.opacity(0.5)
                )
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    viewModel.currentPhase == phase
                        ? AppTheme.primaryAccent.opacity(0.3)
                        : Color.clear
                )
                .clipShape(Capsule())
            }
        }
    }

    // MARK: - Intensity Badge

    private func intensityBadge(level: IntensityLevel) -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(intensityColor(for: level))
                .frame(width: 8, height: 8)

            Text(level.displayName)
                .font(.caption.weight(.medium))
                .foregroundStyle(AppTheme.textSecondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(intensityColor(for: level).opacity(0.12))
        .clipShape(Capsule())
        .animation(.easeInOut(duration: 0.3), value: level.rawValue)
    }

    // MARK: - Helpers

    private func phaseIcon(for phase: WorkoutPhase) -> String {
        switch phase {
        case .warmup: return "flame.fill"
        case .intense: return "bolt.fill"
        case .cooldown: return "wind"
        }
    }

    private func phaseLabel(for phase: WorkoutPhase) -> String {
        switch phase {
        case .warmup: return L10n.warmup
        case .intense: return L10n.intense
        case .cooldown: return L10n.cooldown
        }
    }

    private func intensityColor(for level: IntensityLevel) -> Color {
        switch level {
        case .calm: return AppTheme.secondaryAccent
        case .moderate: return AppTheme.primaryAccent
        case .intense: return AppTheme.warning
        case .critical: return AppTheme.danger
        }
    }

    // MARK: - Wake Word Indicator

    private var wakeWordIndicator: some View {
        HStack(spacing: 6) {
            if viewModel.isWakeWordActive || viewModel.wakeWordManager.isCapturingUtterance {
                // Active: capturing user speech
                Image(systemName: "mic.fill")
                    .font(.caption)
                    .foregroundStyle(AppTheme.success)
                    .symbolEffect(.pulse)

                Text(viewModel.wakeWordManager.isCapturingUtterance ? L10n.listeningForYou : L10n.coachHeard)
                    .font(.caption2.weight(.medium))
                    .foregroundStyle(AppTheme.success)
            } else if viewModel.wakeWordManager.wakeWordDetected {
                // Wake word just detected — brief flash
                Image(systemName: "mic.fill")
                    .font(.caption)
                    .foregroundStyle(AppTheme.primaryAccent)

                Text(L10n.coachHeard)
                    .font(.caption2.weight(.medium))
                    .foregroundStyle(AppTheme.primaryAccent)
            } else {
                // Idle: show hint
                Image(systemName: "mic.badge.xmark")
                    .font(.caption2)
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.4))

                Text(L10n.sayCoachToSpeak)
                    .font(.caption2)
                    .foregroundStyle(AppTheme.textSecondary.opacity(0.4))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            (viewModel.isWakeWordActive ? AppTheme.success : AppTheme.textSecondary)
                .opacity(viewModel.isWakeWordActive ? 0.15 : 0.05)
        )
        .clipShape(Capsule())
        .animation(.easeInOut(duration: 0.3), value: viewModel.isWakeWordActive)
        .animation(.easeInOut(duration: 0.3), value: viewModel.wakeWordManager.wakeWordDetected)
    }

    // MARK: - Breath Phase Indicator

    private func breathPhaseIndicator(phase: BreathPhaseEvent) -> some View {
        HStack(spacing: 4) {
            Image(systemName: phase.icon)
                .font(.caption2)
                .foregroundStyle(breathPhaseColor(phase.type))

            Text(phase.displayName)
                .font(.caption2.weight(.medium))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.8))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(breathPhaseColor(phase.type).opacity(0.1))
        .clipShape(Capsule())
        .animation(.easeInOut(duration: 0.2), value: phase.type)
    }

    private func breathPhaseColor(_ type: String) -> Color {
        switch type {
        case "inhale": return AppTheme.secondaryAccent
        case "exhale": return AppTheme.primaryAccent
        default: return AppTheme.textSecondary
        }
    }
}
