//
//  WorkoutLaunchView.swift
//  TreningsCoach
//
//  Pre-workout setup: persona selector, warmup time picker, GO button
//

import SwiftUI

struct WorkoutLaunchView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var appeared = false

    private let warmupOptions = [0, 1, 2, 3, 5]

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            ParticleBackgroundView(particleCount: 30)

            VStack(spacing: 0) {
                // Top bar
                HStack {
                    HStack(spacing: 6) {
                        CoachiLogoView(size: 24)
                        Text(AppConfig.appName).font(.system(size: 17, weight: .semibold)).foregroundColor(CoachiTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24).padding(.top, 8).opacity(appeared ? 1 : 0)

                Spacer()

                // GO button (large, centered)
                Button {
                    withAnimation(AppConfig.Anim.transitionSpring) { viewModel.startWorkout() }
                } label: {
                    ZStack {
                        // Outer glow rings
                        Circle().fill(CoachiTheme.primary.opacity(0.06))
                            .frame(width: 200, height: 200)
                        Circle().fill(CoachiTheme.primary.opacity(0.12))
                            .frame(width: 170, height: 170)

                        // Main button
                        Circle()
                            .fill(CoachiTheme.primaryGradient)
                            .frame(width: 140, height: 140)
                            .shadow(color: CoachiTheme.primary.opacity(0.4), radius: 25, y: 8)

                        Text(L10n.go)
                            .font(.system(size: 42, weight: .black, design: .rounded))
                            .foregroundColor(.white)
                    }
                }
                .buttonStyle(ScaleButtonStyle())
                .opacity(appeared ? 1 : 0).scaleEffect(appeared ? 1 : 0.8)

                Spacer().frame(height: 48)

                // Warmup time picker
                VStack(spacing: 12) {
                    Text(L10n.warmupTime.uppercased())
                        .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                        .tracking(1)

                    HStack(spacing: 10) {
                        ForEach(warmupOptions, id: \.self) { minutes in
                            Button {
                                withAnimation(AppConfig.Anim.buttonSpring) {
                                    viewModel.selectedWarmupMinutes = minutes
                                }
                            } label: {
                                Text(minutes == 0 ? L10n.noWarmup : "\(minutes) \(L10n.min)")
                                    .font(.system(size: 14, weight: .bold))
                                    .foregroundColor(viewModel.selectedWarmupMinutes == minutes ? .white : CoachiTheme.textSecondary)
                                    .padding(.horizontal, 16).padding(.vertical, 10)
                                    .background(
                                        Capsule().fill(
                                            viewModel.selectedWarmupMinutes == minutes
                                                ? CoachiTheme.primary.opacity(0.8)
                                                : CoachiTheme.surface
                                        )
                                    )
                            }
                        }
                    }
                }
                .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 15)

                Spacer().frame(height: 28)

                // Persona selector
                VStack(spacing: 12) {
                    Text(L10n.selectCoach.uppercased())
                        .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                        .tracking(1)
                    HStack(spacing: 12) {
                        ForEach(CoachPersonality.allCases) { persona in
                            PersonaChipView(persona: persona, isSelected: viewModel.activePersonality == persona) {
                                withAnimation(AppConfig.Anim.buttonSpring) { viewModel.selectPersonality(persona) }
                            }
                        }
                    }
                }
                .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

                Spacer().frame(height: 100)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) { appeared = true }
        }
    }
}

// Simple press-down scale effect for the GO button
struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.92 : 1.0)
            .animation(.spring(response: 0.25, dampingFraction: 0.7), value: configuration.isPressed)
    }
}
