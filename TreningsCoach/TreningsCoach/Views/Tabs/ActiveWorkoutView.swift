//
//  ActiveWorkoutView.swift
//  TreningsCoach
//
//  Active workout screen with orb, timer ring, controls
//

import SwiftUI

struct ActiveWorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var showDiagnostics = false

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                // Phase indicator pills
                HStack(spacing: 8) {
                    ForEach(WorkoutPhase.allCases) { phase in
                        Text(phase.displayName)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(viewModel.currentPhase == phase ? .white : CoachiTheme.textTertiary)
                            .padding(.horizontal, 14).padding(.vertical, 7)
                            .background(Capsule().fill(viewModel.currentPhase == phase ? CoachiTheme.primary.opacity(0.8) : CoachiTheme.surface))
                            .animation(.easeInOut(duration: 0.3), value: viewModel.currentPhase)
                    }
                }
                .padding(.top, 16)

                Spacer()

                // Orb + timer ring
                ZStack {
                    TimerRingView(progress: viewModel.phaseProgress, size: AppConfig.Layout.timerRingSize, lineWidth: 6)
                        .allowsHitTesting(false)
                    CoachOrbView(state: viewModel.orbState, size: AppConfig.Layout.orbSize)
                        .allowsHitTesting(false)
                }
                .contentShape(Circle())
                .onLongPressGesture(minimumDuration: 0.8) {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        showDiagnostics.toggle()
                        AudioPipelineDiagnostics.shared.isOverlayVisible = showDiagnostics
                    }
                }

                // Elapsed time
                Text(viewModel.elapsedFormatted)
                    .font(.system(size: 48, weight: .light, design: .monospaced)).foregroundColor(CoachiTheme.textPrimary).padding(.top, 20)

                Text(viewModel.workoutState == .paused ? L10n.paused.uppercased() : viewModel.currentPhase.displayName.uppercased())
                    .font(.system(size: 11, weight: .bold)).foregroundColor(CoachiTheme.textSecondary).tracking(2).padding(.top, 4)

                // Zone status (glanceable)
                VStack(spacing: 8) {
                    Text(viewModel.zoneStatusDisplay.uppercased())
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(zoneColor(for: viewModel.zoneStatus))
                        .padding(.horizontal, 14).padding(.vertical, 6)
                        .background(Capsule().fill(zoneColor(for: viewModel.zoneStatus).opacity(0.16)))

                    HStack(spacing: 8) {
                        sensorPill(
                            title: viewModel.hrQualityDisplay,
                            color: viewModel.hrIsReliable ? CoachiTheme.secondary : CoachiTheme.accent
                        )
                        sensorPill(
                            title: "Move: \(viewModel.movementStateDisplay)",
                            color: movementColor(for: viewModel.movementState)
                        )
                    }

                    HStack(spacing: 10) {
                        Text("HR: \(viewModel.heartRate.map(String.init) ?? "--")")
                            .font(.system(size: 14, weight: .semibold, design: .monospaced))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text("Target: \(viewModel.targetRangeText)")
                            .font(.system(size: 14, weight: .semibold, design: .monospaced))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }

                    HStack(spacing: 10) {
                        Text("Cadence: \(viewModel.cadenceDisplayText)")
                            .font(.system(size: 12, weight: .medium, design: .monospaced))
                            .foregroundColor(CoachiTheme.textSecondary)
                        Text("Source: \(viewModel.movementSourceDisplay)")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }

                    if !viewModel.hrIsReliable {
                        Text(viewModel.hrQualityHint)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(CoachiTheme.textTertiary)
                            .multilineTextAlignment(.center)
                    }

                    if let cue = viewModel.coachMessage, !cue.isEmpty {
                        Text(cue)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .lineLimit(1)
                            .truncationMode(.tail)
                    }
                }
                .padding(.top, 16)

                Spacer()

                // Controls: stop / pause-play
                HStack(spacing: 30) {
                    Button { viewModel.stopWorkout() } label: {
                        Image(systemName: "stop.fill").font(.system(size: 22, weight: .semibold)).foregroundColor(CoachiTheme.danger)
                            .frame(width: 56, height: 56).background(CoachiTheme.danger.opacity(0.15)).clipShape(Circle())
                    }

                    Button {
                        if viewModel.workoutState == .paused { viewModel.resumeWorkout() }
                        else { viewModel.pauseWorkout() }
                    } label: {
                        Image(systemName: viewModel.workoutState == .paused ? "play.fill" : "pause.fill")
                            .font(.system(size: 28, weight: .semibold)).foregroundColor(.white)
                            .frame(width: 70, height: 70).background(CoachiTheme.primaryGradient).clipShape(Circle())
                            .shadow(color: CoachiTheme.primary.opacity(0.3), radius: 15, y: 5)
                    }
                    .contentTransition(.symbolEffect(.replace))

                    // Talk to coach button
                    Button { viewModel.talkToCoachButtonPressed() } label: {
                        Image(systemName: "mic.fill").font(.system(size: 22, weight: .semibold)).foregroundColor(CoachiTheme.secondary)
                            .frame(width: 56, height: 56).background(CoachiTheme.secondary.opacity(0.15)).clipShape(Circle())
                    }

                    // Spotify quick-access (late-phase media UX, does not affect coaching logic)
                    Button { viewModel.openSpotify() } label: {
                        Image(systemName: "music.note")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(Color(hex: "1DB954"))
                            .frame(width: 48, height: 48)
                            .background(Color(hex: "1DB954").opacity(0.15))
                            .clipShape(Circle())
                    }
                }
                .padding(.bottom, 10)

                HStack(spacing: 10) {
                    Button {
                        viewModel.coachingStyle = .minimal
                    } label: {
                        Text("Less coaching")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(viewModel.coachingStyle == .minimal ? .white : CoachiTheme.textSecondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .fill(viewModel.coachingStyle == .minimal ? CoachiTheme.primary : CoachiTheme.surface)
                            )
                    }
                    .buttonStyle(.plain)

                    Button {
                        viewModel.coachingStyle = .motivational
                    } label: {
                        Text("More coaching")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(viewModel.coachingStyle == .motivational ? .white : CoachiTheme.textSecondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .fill(viewModel.coachingStyle == .motivational ? CoachiTheme.primary : CoachiTheme.surface)
                            )
                    }
                    .buttonStyle(.plain)
                }
                .padding(.bottom, 34)
            }

            // Diagnostics overlay (long-press orb to toggle)
            if showDiagnostics {
                VStack {
                    AudioDiagnosticOverlayView(isPresented: $showDiagnostics)
                        .transition(.move(edge: .top).combined(with: .opacity))
                        .padding(.top, 60)
                    Spacer()
                }
            }
        }
    }

    private func zoneColor(for zone: String) -> Color {
        switch zone {
        case "in_zone":
            return CoachiTheme.secondary
        case "above_zone":
            return CoachiTheme.danger
        case "below_zone":
            return CoachiTheme.accent
        case "timing_control":
            return CoachiTheme.primary
        default:
            return CoachiTheme.textSecondary
        }
    }

    private func movementColor(for state: String) -> Color {
        switch state {
        case "moving":
            return CoachiTheme.secondary
        case "paused":
            return CoachiTheme.accent
        default:
            return CoachiTheme.textSecondary
        }
    }

    @ViewBuilder
    private func sensorPill(title: String, color: Color) -> some View {
        Text(title.uppercased())
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Capsule().fill(color.opacity(0.14)))
    }
}
