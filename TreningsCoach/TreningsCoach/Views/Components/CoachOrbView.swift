//
//  CoachOrbView.swift
//  TreningsCoach
//
//  Animated orb with 4 states: idle, listening, speaking, paused
//

import SwiftUI

struct CoachOrbView: View {
    let state: OrbState
    var size: CGFloat = 120

    @State private var isPulsing = false
    @State private var glowScale: CGFloat = 1.0

    private var gradient: LinearGradient {
        switch state {
        case .idle:      return CoachiTheme.emberGradient
        case .listening: return CoachiTheme.tealGradient
        case .speaking:  return CoachiTheme.goldGradient
        case .paused:    return CoachiTheme.grayGradient
        }
    }

    private var glowColor: Color {
        switch state {
        case .idle:      return CoachiTheme.primary
        case .listening: return CoachiTheme.secondary
        case .speaking:  return CoachiTheme.accent
        case .paused:    return CoachiTheme.textTertiary
        }
    }

    private var icon: String {
        switch state {
        case .idle:      return "mic.fill"
        case .listening: return "waveform"
        case .speaking:  return "speaker.wave.3.fill"
        case .paused:    return "pause.fill"
        }
    }

    private var pulseDuration: Double {
        switch state {
        case .idle:      return AppConfig.Anim.orbIdlePulse
        case .listening: return AppConfig.Anim.orbListeningPulse
        case .speaking:  return AppConfig.Anim.orbSpeakingWave
        case .paused:    return 0
        }
    }

    var body: some View {
        ZStack {
            if state != .paused {
                Circle().fill(glowColor.opacity(0.06))
                    .frame(width: size * 1.7, height: size * 1.7)
                    .scaleEffect(isPulsing ? 1.1 : 0.95)
            }
            if state != .paused {
                Circle().fill(glowColor.opacity(0.12))
                    .frame(width: size * 1.4, height: size * 1.4)
                    .scaleEffect(isPulsing ? 1.06 : 0.97)
            }
            Circle()
                .fill(gradient)
                .frame(width: size, height: size)
                .shadow(color: glowColor.opacity(0.3), radius: 20, y: 10)
                .scaleEffect(state == .paused ? 1.0 : (isPulsing ? 1.04 : 1.0))

            Image(systemName: icon)
                .font(.system(size: size * 0.3, weight: .light))
                .foregroundColor(.white)
                .contentTransition(.symbolEffect(.replace))
        }
        .animation(.easeInOut(duration: 0.5), value: state)
        .onChange(of: state) { _, _ in isPulsing = false; startPulse() }
        .onAppear { startPulse() }
    }

    private func startPulse() {
        guard state != .paused else { return }
        withAnimation(.easeInOut(duration: pulseDuration).repeatForever(autoreverses: true)) {
            isPulsing = true
        }
    }
}
