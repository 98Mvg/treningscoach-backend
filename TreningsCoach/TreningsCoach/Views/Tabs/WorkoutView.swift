//
//  WorkoutView.swift
//  TreningsCoach
//
//  Main workout screen — audio-first, glanceable design
//  Voice orb at center with timer ring, phase indicator, coach message
//  User should NOT need to stare at this screen — quick glance only
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

                // MARK: - Voice Orb + Timer Ring (center)
                ZStack {
                    // Timer ring wraps around the orb
                    if viewModel.isContinuousMode {
                        TimerRingView(
                            elapsedTime: viewModel.elapsedTime,
                            totalTime: AppConfig.ContinuousCoaching.maxWorkoutDuration,
                            ringSize: 170,
                            lineWidth: 5
                        )
                        .transition(.opacity)
                    }

                    // The voice orb — THE interaction element
                    VoiceOrbView(state: viewModel.voiceState) {
                        if viewModel.isContinuousMode {
                            viewModel.stopContinuousWorkout()
                        } else if viewModel.isRecording {
                            viewModel.stopRecording()
                        } else {
                            viewModel.startContinuousWorkout()
                        }
                    }
                }

                // MARK: - Elapsed Time
                if viewModel.isContinuousMode {
                    Text(viewModel.elapsedTimeFormatted)
                        .font(.system(size: 32, weight: .light, design: .monospaced))
                        .foregroundStyle(AppTheme.textPrimary)
                        .padding(.top, 16)
                        .transition(.opacity)
                }

                // MARK: - Intensity Badge
                if viewModel.isContinuousMode, let analysis = viewModel.breathAnalysis {
                    intensityBadge(level: analysis.intensityLevel)
                        .padding(.top, 8)
                        .transition(.opacity)
                }

                // Hint text when idle
                if !viewModel.isContinuousMode {
                    Text("Tap to start workout")
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                        .padding(.top, 16)
                }

                Spacer()

                // MARK: - Coach Message (bottom)
                if let message = viewModel.coachMessage {
                    VStack(spacing: 4) {
                        HStack(spacing: 6) {
                            Image(systemName: "quote.opening")
                                .font(.caption2)
                                .foregroundStyle(AppTheme.primaryAccent)
                            Text("Coach")
                                .font(.caption.weight(.medium))
                                .foregroundStyle(AppTheme.textSecondary)
                        }

                        Text(message)
                            .font(.body)
                            .foregroundStyle(AppTheme.textPrimary)
                            .multilineTextAlignment(.center)
                            .lineLimit(3)
                    }
                    .padding(16)
                    .frame(maxWidth: .infinity)
                    .cardStyle()
                    .padding(.horizontal, 20)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }

                // MARK: - Stop Button (only during workout)
                if viewModel.isContinuousMode {
                    Button {
                        viewModel.stopContinuousWorkout()
                    } label: {
                        Text("Stop Workout")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(AppTheme.danger)
                            .padding(.horizontal, 24)
                            .padding(.vertical, 10)
                            .background(AppTheme.danger.opacity(0.15))
                            .clipShape(Capsule())
                    }
                    .padding(.top, 12)
                    .transition(.opacity)
                }

                Spacer()
                    .frame(height: 20)
            }
            .padding(.bottom, 80) // Space for tab bar
            .animation(.easeInOut(duration: 0.3), value: viewModel.isContinuousMode)
        }
        // Error alert
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) { }
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
        case .warmup: return "Warmup"
        case .intense: return "Intense"
        case .cooldown: return "Cool"
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
}
