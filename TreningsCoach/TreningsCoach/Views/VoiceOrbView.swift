//
//  VoiceOrbView.swift
//  TreningsCoach
//
//  Voice orb component with idle, listening, and speaking states
//

import SwiftUI

enum VoiceState {
    case idle
    case listening
    case speaking
}

struct VoiceOrbView: View {
    let state: VoiceState
    let action: () -> Void

    @State private var pulseScale: CGFloat = 1.0
    @State private var waveOffset: CGFloat = 0

    var body: some View {
        Button(action: action) {
            ZStack {
                // Outer glow rings for listening/speaking
                if state != .idle {
                    Circle()
                        .fill(orbColor.opacity(0.2))
                        .frame(width: 140, height: 140)
                        .scaleEffect(pulseScale)
                        .opacity(2 - pulseScale)

                    Circle()
                        .fill(orbColor.opacity(0.1))
                        .frame(width: 160, height: 160)
                        .scaleEffect(pulseScale * 1.1)
                        .opacity(2 - pulseScale)
                }

                // Main orb
                Circle()
                    .fill(
                        LinearGradient(
                            gradient: Gradient(colors: gradientColors),
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 120, height: 120)
                    .shadow(color: orbColor.opacity(0.3), radius: 20, x: 0, y: 10)

                // Icon
                Image(systemName: iconName)
                    .font(.system(size: 48, weight: .light))
                    .foregroundColor(.white)
            }
        }
        .buttonStyle(PlainButtonStyle())
        .onAppear {
            startAnimation()
        }
        .onChange(of: state) { _ in
            startAnimation()
        }
    }

    // MARK: - Computed Properties

    private var orbColor: Color {
        switch state {
        case .idle:
            return AppConfig.Colors.idle
        case .listening:
            return AppConfig.Colors.listening
        case .speaking:
            return AppConfig.Colors.speaking
        }
    }

    private var gradientColors: [Color] {
        switch state {
        case .idle:
            return AppConfig.Colors.idleGradient
        case .listening:
            return AppConfig.Colors.listeningGradient
        case .speaking:
            return AppConfig.Colors.speakingGradient
        }
    }

    private var iconName: String {
        switch state {
        case .idle:
            return "mic.fill"
        case .listening:
            return "waveform"
        case .speaking:
            return "speaker.wave.3.fill"
        }
    }

    // MARK: - Animations

    private func startAnimation() {
        // Stop all animations first
        withAnimation(.linear(duration: 0)) {
            pulseScale = 1.0
        }

        switch state {
        case .idle:
            // No animation for idle
            break

        case .listening:
            // Gentle pulsing for listening
            withAnimation(
                .easeInOut(duration: AppConfig.Animation.pulseDuration)
                .repeatForever(autoreverses: true)
            ) {
                pulseScale = 1.15
            }

        case .speaking:
            // Faster wave animation for speaking
            withAnimation(
                .easeInOut(duration: AppConfig.Animation.waveDuration)
                .repeatForever(autoreverses: true)
            ) {
                pulseScale = 1.1
            }
        }
    }
}

// MARK: - Preview

struct VoiceOrbView_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 50) {
            VoiceOrbView(state: .idle, action: {})
            VoiceOrbView(state: .listening, action: {})
            VoiceOrbView(state: .speaking, action: {})
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            LinearGradient(
                colors: [.white, Color(.systemGray6)],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }
}
