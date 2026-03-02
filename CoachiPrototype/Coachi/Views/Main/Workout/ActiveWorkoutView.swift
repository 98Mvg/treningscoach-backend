import SwiftUI

struct ActiveWorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                // Phase indicator
                HStack(spacing: 8) {
                    ForEach(WorkoutPhase.allCases) { phase in
                        Text(phase.displayName)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(
                                viewModel.currentPhase == phase ? .white : CoachiTheme.textTertiary
                            )
                            .padding(.horizontal, 14)
                            .padding(.vertical, 7)
                            .background(
                                Capsule()
                                    .fill(viewModel.currentPhase == phase
                                        ? CoachiTheme.primary.opacity(0.8)
                                        : CoachiTheme.surface)
                            )
                            .animation(.easeInOut(duration: 0.3), value: viewModel.currentPhase)
                    }
                }
                .padding(.top, 16)

                Spacer()

                // Coach Orb with Timer Ring
                ZStack {
                    TimerRingView(
                        progress: viewModel.phaseProgress,
                        size: AppConfig.Layout.timerRingSize,
                        lineWidth: 6
                    )

                    CoachOrbView(
                        state: viewModel.orbState,
                        size: AppConfig.Layout.orbSize
                    )
                }

                // Time
                Text(viewModel.elapsedFormatted)
                    .font(.system(size: 48, weight: .light, design: .monospaced))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 20)

                // Status
                Text(viewModel.workoutState == .paused ? "PAUSED" : viewModel.currentPhase.displayName.uppercased())
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .tracking(2)
                    .padding(.top, 4)

                // Intensity badge
                Text(viewModel.currentIntensity.displayName)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(Color(hex: viewModel.currentIntensity.color))
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(
                        Capsule()
                            .fill(Color(hex: viewModel.currentIntensity.color).opacity(0.15))
                    )
                    .padding(.top, 16)

                // Coach message
                if !viewModel.coachMessage.isEmpty {
                    Text(viewModel.coachMessage)
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .lineLimit(2)
                        .padding(.horizontal, 40)
                        .padding(.top, 20)
                        .transition(.opacity.combined(with: .scale(scale: 0.95)))
                }

                Spacer()

                // Controls
                HStack(spacing: 30) {
                    // Stop
                    Button {
                        viewModel.stopWorkout()
                    } label: {
                        Image(systemName: "stop.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .foregroundColor(CoachiTheme.danger)
                            .frame(width: 56, height: 56)
                            .background(CoachiTheme.danger.opacity(0.15))
                            .clipShape(Circle())
                    }

                    // Play/Pause
                    Button {
                        if viewModel.workoutState == .paused {
                            viewModel.resumeWorkout()
                        } else {
                            viewModel.pauseWorkout()
                        }
                    } label: {
                        Image(systemName: viewModel.workoutState == .paused ? "play.fill" : "pause.fill")
                            .font(.system(size: 28, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(width: 70, height: 70)
                            .background(CoachiTheme.primaryGradient)
                            .clipShape(Circle())
                            .shadow(color: CoachiTheme.primary.opacity(0.3), radius: 15, y: 5)
                    }
                    .contentTransition(.symbolEffect(.replace))

                    // Placeholder for symmetry
                    Circle()
                        .fill(Color.clear)
                        .frame(width: 56, height: 56)
                }
                .padding(.bottom, 40)
            }
        }
    }
}

#Preview {
    ActiveWorkoutView(viewModel: {
        let vm = WorkoutViewModel()
        vm.startWorkout()
        return vm
    }())
}
