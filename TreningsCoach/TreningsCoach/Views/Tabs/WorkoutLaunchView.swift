//
//  WorkoutLaunchView.swift
//  TreningsCoach
//
//  Pre-workout setup: persona selector, warmup time wheel, GO button
//

import SwiftUI

struct WorkoutLaunchView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var appeared = false

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
                    // Persist warmup selection for next session
                    UserDefaults.standard.set(viewModel.selectedWarmupMinutes, forKey: "last_warmup_minutes")
                    withAnimation(AppConfig.Anim.transitionSpring) { viewModel.startWorkout() }
                } label: {
                    ZStack {
                        Circle().fill(CoachiTheme.primary.opacity(0.06))
                            .frame(width: 200, height: 200)
                        Circle().fill(CoachiTheme.primary.opacity(0.12))
                            .frame(width: 170, height: 170)
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

                Spacer().frame(height: 36)

                // Warmup time — scroll wheel only
                VStack(spacing: 8) {
                    Text(L10n.warmupTime.uppercased())
                        .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                        .tracking(1)

                    WarmupWheelPicker(selectedMinutes: $viewModel.selectedWarmupMinutes)
                }
                .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 15)

                Spacer().frame(height: 20)

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

                Spacer().frame(height: 80)
            }
        }
        .onAppear {
            // Restore last session warmup time
            let saved = UserDefaults.standard.integer(forKey: "last_warmup_minutes")
            if saved > 0 {
                viewModel.selectedWarmupMinutes = saved
            }
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) { appeared = true }
        }
    }
}

// MARK: - Premium Scroll Wheel Picker

struct WarmupWheelPicker: View {
    @Binding var selectedMinutes: Int

    // 0 (None), then 1-40 minutes
    private let values: [Int] = [0] + Array(1...40)

    var body: some View {
        Picker("", selection: $selectedMinutes) {
            ForEach(values, id: \.self) { minutes in
                if minutes == 0 {
                    Text(L10n.noWarmup)
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .tag(0)
                } else {
                    Text("\(minutes) \(L10n.min)")
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .tag(minutes)
                }
            }
        }
        .pickerStyle(.wheel)
        .frame(height: 120)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(CoachiTheme.surface.opacity(0.5))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(CoachiTheme.primary.opacity(0.2), lineWidth: 0.5)
        )
        .padding(.horizontal, 50)
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
