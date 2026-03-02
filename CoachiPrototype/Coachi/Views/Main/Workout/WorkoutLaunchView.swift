import SwiftUI

struct WorkoutLaunchView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var appeared = false

    var body: some View {
        ZStack {
            // Background
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            ParticleBackgroundView(particleCount: 30)

            VStack(spacing: 0) {
                // Top bar
                HStack {
                    // Logo text
                    HStack(spacing: 6) {
                        CoachiLogoView(size: 24)
                        Text(AppConfig.appName)
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24)
                .padding(.top, 8)
                .opacity(appeared ? 1 : 0)

                Spacer()

                // Main CTA
                PulseButtonView(title: "Start\nworkout", icon: "play.fill", size: 160) {
                    withAnimation(AppConfig.Anim.transitionSpring) {
                        viewModel.startWorkout()
                    }
                }
                .opacity(appeared ? 1 : 0)
                .scaleEffect(appeared ? 1 : 0.8)

                // Waveform
                WaveformView(isActive: false, barCount: 16, height: 50)
                    .padding(.horizontal, 40)
                    .padding(.top, 24)
                    .opacity(appeared ? 1 : 0)

                Spacer()

                // Persona selector
                VStack(spacing: 12) {
                    Text("Choose your coach")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(CoachiTheme.textTertiary)
                        .textCase(.uppercase)
                        .tracking(1)

                    HStack(spacing: 12) {
                        ForEach(CoachPersonality.allCases) { persona in
                            PersonaChipView(
                                persona: persona,
                                isSelected: viewModel.activePersonality == persona
                            ) {
                                withAnimation(AppConfig.Anim.buttonSpring) {
                                    viewModel.selectPersonality(persona)
                                }
                            }
                        }
                    }
                }
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 20)

                Spacer()
                    .frame(height: 100) // Tab bar space
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) {
                appeared = true
            }
        }
    }
}

#Preview {
    WorkoutLaunchView(viewModel: WorkoutViewModel())
}
