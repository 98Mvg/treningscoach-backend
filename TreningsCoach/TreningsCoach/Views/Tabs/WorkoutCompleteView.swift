//
//  WorkoutCompleteView.swift
//  TreningsCoach
//
//  Post-workout summary screen (neon score design)
//

import SwiftUI

struct WorkoutCompleteView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var contentVisible = false

    var body: some View {
        GeometryReader { geo in
            ZStack {
                completeBackground

                VStack(spacing: 0) {
                    Spacer(minLength: 42)

                    ZStack {
                        NeonScoreParticles()
                            .frame(width: 340, height: 340)
                        NeonCoachScoreRingView(
                            score: viewModel.coachScore,
                            size: min(geo.size.width * 0.62, 260)
                        )
                    }
                    .opacity(contentVisible ? 1 : 0)
                    .scaleEffect(contentVisible ? 1 : 0.94)

                    VStack(spacing: 14) {
                        HStack(spacing: 10) {
                            Image(systemName: "clock")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(Color(hex: "2FE3E0"))
                            Text(durationLine)
                                .font(.system(size: 40, weight: .medium, design: .rounded))
                                .foregroundColor(Color.white.opacity(0.88))
                        }

                        Divider()
                            .overlay(Color.white.opacity(0.16))

                        HStack(spacing: 30) {
                            statPill(icon: "flame.fill", color: Color(hex: "FF9C44"), text: "\(estimatedCalories) kcal")
                            statPill(icon: "heart.fill", color: Color(hex: "2FE3E0"), text: heartRateLine)
                        }

                        if let capHint = viewModel.coachScoreCapHint {
                            Text(capHint)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(Color.white.opacity(0.62))
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 10)
                        }
                    }
                    .frame(maxWidth: 360)
                    .padding(.horizontal, 28)
                    .padding(.top, 20)
                    .opacity(contentVisible ? 1 : 0)
                    .offset(y: contentVisible ? 0 : 16)

                    Spacer(minLength: 22)

                    ShareLink(item: shareSummaryText) {
                        Text(L10n.current == .no ? "Del" : "Share")
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(Color.white.opacity(0.92))
                            .frame(width: min(geo.size.width * 0.68, 280), height: 70)
                            .background(
                                Capsule(style: .continuous)
                                    .fill(
                                        LinearGradient(
                                            colors: [Color(hex: "2FE3E0"), Color(hex: "35C8D6")],
                                            startPoint: .leading,
                                            endPoint: .trailing
                                        )
                                    )
                                    .shadow(color: Color(hex: "2FE3E0").opacity(0.42), radius: 16, y: 0)
                            )
                    }
                    .buttonStyle(.plain)
                    .opacity(contentVisible ? 1 : 0)

                    Button {
                        withAnimation(AppConfig.Anim.transitionSpring) {
                            viewModel.resetWorkout()
                        }
                    } label: {
                        Text(L10n.done)
                            .font(.system(size: 38, weight: .regular, design: .rounded))
                            .foregroundColor(Color.white.opacity(0.58))
                    }
                    .buttonStyle(.plain)
                    .padding(.top, 12)
                    .opacity(contentVisible ? 1 : 0)
                }
                .padding(.bottom, max(24, geo.safeAreaInsets.bottom + 10))
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) {
                contentVisible = true
            }
        }
    }

    private var completeBackground: some View {
        ZStack {
            RadialGradient(
                colors: [Color(hex: "0E1E48"), Color(hex: "050A1E")],
                center: .center,
                startRadius: 40,
                endRadius: 620
            )
            .ignoresSafeArea()

            LinearGradient(
                colors: [Color(hex: "091436").opacity(0.96), Color(hex: "020615").opacity(0.98)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
        }
    }

    private var finalDurationSeconds: Int {
        max(0, viewModel.workoutHistory.first?.durationSeconds ?? 0)
    }

    private var durationMinutes: Int {
        max(0, Int(round(Double(finalDurationSeconds) / 60.0)))
    }

    private var durationLine: String {
        "\(durationMinutes) min"
    }

    private var estimatedCalories: Int {
        let caloriesPerMinute: Double
        switch viewModel.currentIntensity {
        case .calm:
            caloriesPerMinute = 6.0
        case .moderate:
            caloriesPerMinute = 8.0
        case .intense:
            caloriesPerMinute = 10.0
        case .critical:
            caloriesPerMinute = 11.0
        }
        return max(0, Int(round(Double(durationMinutes) * caloriesPerMinute)))
    }

    private var heartRateLine: String {
        guard let heartRate = viewModel.heartRate, heartRate > 0 else {
            return "0 BPM"
        }
        return "\(heartRate) BPM"
    }

    private var shareSummaryText: String {
        let header = L10n.current == .no ? "Coachi økt fullført" : "Coachi workout complete"
        let minutesText = L10n.current == .no ? "\(durationMinutes) min" : "\(durationMinutes) min"
        let scoreText = "\(L10n.coachScore): \(viewModel.coachScore)"
        return "\(header)\n\(scoreText)\n\(minutesText), \(estimatedCalories) kcal, \(heartRateLine)"
    }

    private func statPill(icon: String, color: Color, text: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(color)
            Text(text)
                .font(.system(size: 19, weight: .medium, design: .rounded))
                .foregroundColor(Color.white.opacity(0.78))
                .lineLimit(1)
        }
    }
}

private struct NeonCoachScoreRingView: View {
    let score: Int
    var size: CGFloat = 250
    var lineWidth: CGFloat = 20
    var animationDuration: Double = 2.8

    @State private var displayedScore: Int = 0
    @State private var displayedProgress: CGFloat = 0

    private var clampedScore: Int {
        max(0, min(100, score))
    }

    private var targetProgress: CGFloat {
        CGFloat(clampedScore) / 100.0
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.white.opacity(0.1), lineWidth: lineWidth)

            Circle()
                .trim(from: 0, to: displayedProgress)
                .stroke(
                    Color(hex: "2FE3E0"),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .butt)
                )
                .rotationEffect(.degrees(-90))
                .shadow(color: Color(hex: "2FE3E0").opacity(0.82), radius: 14)

            Circle()
                .trim(from: displayedProgress, to: 1)
                .stroke(
                    Color(hex: "FF9C44"),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .butt)
                )
                .rotationEffect(.degrees(-90))
                .shadow(color: Color(hex: "FF9C44").opacity(0.68), radius: 12)

            VStack(spacing: 6) {
                Text("\(displayedScore)")
                    .font(.system(size: size * 0.34, weight: .bold, design: .rounded))
                    .foregroundColor(Color.white.opacity(0.96))
                    .monospacedDigit()

                Text("CS")
                    .font(.system(size: size * 0.1, weight: .semibold, design: .rounded))
                    .foregroundColor(Color.white.opacity(0.5))
                    .tracking(1.4)
            }
        }
        .frame(width: size, height: size)
        .task(id: clampedScore) {
            await animateScore()
        }
    }

    private func animateScore() async {
        displayedScore = 0
        displayedProgress = 0

        withAnimation(.easeOut(duration: animationDuration)) {
            displayedProgress = targetProgress
        }

        let steps = clampedScore
        guard steps > 0 else { return }

        let stepNanos = UInt64((animationDuration / Double(steps)) * 1_000_000_000)
        let safeStepNanos = max(UInt64(10_000_000), stepNanos)

        for step in 1...steps {
            try? await Task.sleep(nanoseconds: safeStepNanos)
            if Task.isCancelled { return }
            displayedScore = step
        }
    }
}

private struct NeonScoreParticles: View {
    private let particles: [(x: CGFloat, y: CGFloat, size: CGFloat, color: Color, opacity: Double)] = [
        (-124, -132, 6, Color(hex: "2FE3E0"), 0.9),
        (-88, -176, 4, Color(hex: "2FE3E0"), 0.85),
        (-30, -188, 5, Color(hex: "2FE3E0"), 0.85),
        (18, -194, 4, Color(hex: "FF9C44"), 0.84),
        (70, -176, 5, Color(hex: "2FE3E0"), 0.88),
        (122, -160, 4, Color(hex: "2FE3E0"), 0.82),
        (146, -96, 6, Color(hex: "FF9C44"), 0.88),
        (168, -40, 5, Color(hex: "2FE3E0"), 0.86),
        (138, 8, 6, Color(hex: "FF9C44"), 0.9),
        (-154, -74, 4, Color(hex: "2FE3E0"), 0.82),
        (-160, -26, 3, Color(hex: "2FE3E0"), 0.78),
        (-132, 16, 4, Color(hex: "FF9C44"), 0.8),
    ]

    var body: some View {
        ZStack {
            ForEach(Array(particles.enumerated()), id: \.offset) { _, particle in
                Circle()
                    .fill(particle.color.opacity(particle.opacity))
                    .frame(width: particle.size, height: particle.size)
                    .shadow(color: particle.color.opacity(0.75), radius: particle.size * 1.8)
                    .offset(x: particle.x, y: particle.y)
            }
        }
    }
}
