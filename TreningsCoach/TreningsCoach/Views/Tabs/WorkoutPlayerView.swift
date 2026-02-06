//
//  WorkoutPlayerView.swift
//  TreningsCoach
//
//  Workout player UI with timer, play/pause controls, and progress
//

import SwiftUI

struct WorkoutPlayerView: View {
    let elapsedTime: TimeInterval
    let totalTime: TimeInterval
    let isPaused: Bool
    let onPlayPause: () -> Void
    let onStop: () -> Void

    @State private var pulseScale: CGFloat = 1.0

    var body: some View {
        VStack(spacing: 24) {
            // MARK: - Circular Progress Ring
            ZStack {
                // Background ring
                Circle()
                    .stroke(
                        AppTheme.textSecondary.opacity(0.2),
                        lineWidth: 8
                    )
                    .frame(width: 220, height: 220)

                // Progress ring
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(
                        LinearGradient(
                            gradient: Gradient(colors: [
                                AppTheme.primaryAccent,
                                AppTheme.secondaryAccent
                            ]),
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(
                            lineWidth: 8,
                            lineCap: .round
                        )
                    )
                    .frame(width: 220, height: 220)
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 1.0), value: progress)

                // Center content
                VStack(spacing: 8) {
                    // Timer display
                    Text(timeFormatted)
                        .font(.system(size: 48, weight: .light, design: .monospaced))
                        .foregroundStyle(AppTheme.textPrimary)

                    // Status text
                    Text(isPaused ? L10n.paused : L10n.recording)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(AppTheme.textSecondary)
                        .textCase(.uppercase)
                        .tracking(1.2)
                }
            }

            // MARK: - Control Buttons
            HStack(spacing: 40) {
                // Play/Pause button
                Button(action: onPlayPause) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    gradient: Gradient(colors: [
                                        AppTheme.primaryAccent,
                                        AppTheme.secondaryAccent
                                    ]),
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 70, height: 70)
                            .scaleEffect(pulseScale)
                            .shadow(color: AppTheme.primaryAccent.opacity(0.3), radius: 15, x: 0, y: 5)

                        Image(systemName: isPaused ? "play.fill" : "pause.fill")
                            .font(.system(size: 28, weight: .medium))
                            .foregroundColor(.white)
                            .contentTransition(.symbolEffect(.replace))
                    }
                }
                .buttonStyle(PlainButtonStyle())
                .onAppear {
                    startPulseAnimation()
                }
                .onChange(of: isPaused) { _ in
                    startPulseAnimation()
                }

                // Stop button
                Button(action: onStop) {
                    ZStack {
                        Circle()
                            .fill(AppTheme.danger.opacity(0.2))
                            .frame(width: 60, height: 60)

                        Image(systemName: "stop.fill")
                            .font(.system(size: 24, weight: .medium))
                            .foregroundColor(AppTheme.danger)
                    }
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
    }

    // MARK: - Computed Properties

    private var progress: CGFloat {
        guard totalTime > 0 else { return 0 }
        return CGFloat(min(elapsedTime / totalTime, 1.0))
    }

    private var timeFormatted: String {
        let mins = Int(elapsedTime) / 60
        let secs = Int(elapsedTime) % 60
        return String(format: "%02d:%02d", mins, secs)
    }

    // MARK: - Animations

    private func startPulseAnimation() {
        // Reset scale
        withAnimation(.linear(duration: 0)) {
            pulseScale = 1.0
        }

        // Pulse if not paused
        if !isPaused {
            withAnimation(
                .easeInOut(duration: 1.5)
                .repeatForever(autoreverses: true)
            ) {
                pulseScale = 1.08
            }
        }
    }
}

// MARK: - Preview

struct WorkoutPlayerView_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 50) {
                WorkoutPlayerView(
                    elapsedTime: 125,
                    totalTime: 2700,
                    isPaused: false,
                    onPlayPause: {},
                    onStop: {}
                )

                WorkoutPlayerView(
                    elapsedTime: 125,
                    totalTime: 2700,
                    isPaused: true,
                    onPlayPause: {},
                    onStop: {}
                )
            }
        }
    }
}
