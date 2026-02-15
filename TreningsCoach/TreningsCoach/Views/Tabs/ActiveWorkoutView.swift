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

                // Intensity badge
                Text(viewModel.currentIntensity.displayName)
                    .font(.system(size: 12, weight: .bold)).foregroundColor(Color(hex: viewModel.currentIntensity.color))
                    .padding(.horizontal, 14).padding(.vertical, 6)
                    .background(Capsule().fill(Color(hex: viewModel.currentIntensity.color).opacity(0.15)))
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
                }
                .padding(.bottom, 40)
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
}
