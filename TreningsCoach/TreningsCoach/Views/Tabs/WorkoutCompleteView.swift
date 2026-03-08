//
//  WorkoutCompleteView.swift
//  TreningsCoach
//
//  Post-workout summary screen
//

import SwiftUI

struct WorkoutCompleteView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var checkmarkScale: CGFloat = 0.65
    @State private var contentVisible = false
    @State private var displayedScore: Int = 0
    @State private var displayedRingProgress: Double = 0
    @State private var ringGlowPulse = false
    @State private var hasAnimatedScore = false
    @State private var finalDurationText = "00:00"
    @State private var finalBPMText = "0 BPM"

    private var targetScore: Int {
        if viewModel.hasAuthoritativeCoachScore {
            return max(0, min(100, viewModel.coachScore))
        }
        return 0
    }

    private var workoutLabel: String {
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            return L10n.current == .no ? "Rolig tur" : "Easy Run"
        case .intervals:
            return L10n.current == .no ? "Intervaller" : "Intervals"
        case .standard:
            return L10n.current == .no ? "Økt" : "Workout"
        }
    }

    private var hasFinalHeartRate: Bool {
        finalBPMText != "0 BPM"
    }

    private var shareSummaryText: String {
        let metrics = hasFinalHeartRate
            ? "\(targetScore) CS • \(finalDurationText) • \(finalBPMText)"
            : "\(targetScore) CS • \(finalDurationText)"

        if L10n.current == .no {
            return "Jeg fullførte \(workoutLabel) med Coachi. \(metrics)"
        }

        return "I finished \(workoutLabel) with Coachi. \(metrics)"
    }

    private var sharePreviewTitle: String {
        if L10n.current == .no {
            return "\(workoutLabel) med Coachi"
        }
        return "\(workoutLabel) with Coachi"
    }

    private var doneLabel: String { L10n.current == .no ? "FERDIG" : "DONE" }
    private var shareLabel: String { L10n.current == .no ? "DEL" : "SHARE" }
    private var actionButtonWidth: CGFloat { UIScreen.main.bounds.width < 390 ? 140 : 156 }

    var body: some View {
        ZStack {
            Image("OnboardingBgOutdoor")
                .resizable()
                .scaledToFill()
                .ignoresSafeArea()

            LinearGradient(
                colors: [Color.black.opacity(0.22), Color.black.opacity(0.42), Color.black.opacity(0.68)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                let verticalBudget = max(180, geo.size.height - geo.safeAreaInsets.top - geo.safeAreaInsets.bottom - 360)
                let ringSize = min(min(geo.size.width * 0.58, verticalBudget), 246)
                let titleSize = min(max(24, geo.size.width * 0.072), 34)
                let metricFontSize = geo.size.width < 370 ? 15.0 : 17.0

                VStack(spacing: 0) {
                    Spacer().frame(height: max(geo.safeAreaInsets.top + 18, 44))

                    ZStack {
                        Circle()
                            .stroke(Color.white.opacity(0.5), lineWidth: 2)
                            .frame(width: 74, height: 74)
                        Image(systemName: "checkmark")
                            .font(.system(size: 34, weight: .light))
                            .foregroundColor(Color.white.opacity(0.94))
                    }
                    .scaleEffect(checkmarkScale)

                    Text("COACH SCORE")
                        .font(.system(size: titleSize, weight: .light, design: .default))
                        .foregroundColor(Color.white.opacity(0.96))
                        .tracking(1)
                        .lineLimit(1)
                        .minimumScaleFactor(0.75)
                        .padding(.top, 22)
                        .opacity(contentVisible ? 1 : 0)

                    ZStack {
                        Circle()
                            .fill(Color.white.opacity(0.07))
                            .frame(width: ringSize + 34, height: ringSize + 34)
                            .blur(radius: 16)

                        Circle()
                            .stroke(Color.white.opacity(0.20), lineWidth: 14)
                            .frame(width: ringSize, height: ringSize)

                        Circle()
                            .trim(from: 0, to: displayedRingProgress)
                            .stroke(
                                LinearGradient(
                                    colors: [Color.white.opacity(0.97), Color(hex: "A5F3EC"), Color(hex: "67E8F9"), Color.white.opacity(0.9)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ),
                                style: StrokeStyle(lineWidth: 14, lineCap: .round, lineJoin: .round)
                            )
                            .frame(width: ringSize, height: ringSize)
                            .rotationEffect(.degrees(-90))
                            .shadow(color: Color.white.opacity(0.24), radius: 10, y: 1)

                        if displayedRingProgress > 0.01 {
                            Circle()
                                .fill(Color.white.opacity(0.95))
                                .frame(width: 14, height: 14)
                                .shadow(color: Color.white.opacity(0.64), radius: 7, y: 0)
                                .offset(y: -ringSize / 2)
                                .rotationEffect(.degrees(360 * displayedRingProgress - 90))
                        }

                        Text("\(displayedScore)")
                            .font(.system(size: ringSize * 0.32, weight: .medium))
                            .foregroundColor(Color.white.opacity(0.97))
                            .shadow(color: .black.opacity(0.30), radius: 8, y: 2)
                    }
                    .frame(width: ringSize + 34, height: ringSize + 34)
                    .padding(.top, 26)
                    .overlay {
                        Circle()
                            .stroke(Color.white.opacity(0.34), lineWidth: 2.5)
                            .blur(radius: ringGlowPulse ? 6 : 2.5)
                            .scaleEffect(ringGlowPulse ? 1.06 : 0.98)
                            .opacity(ringGlowPulse ? 0.58 : 0.18)
                            .animation(.easeInOut(duration: 1.9).repeatForever(autoreverses: true), value: ringGlowPulse)
                    }
                    .opacity(contentVisible ? 1 : 0)

                    summaryRow(metricFontSize: metricFontSize)
                    .padding(.top, 34)
                    .opacity(contentVisible ? 1 : 0)
                    .frame(maxWidth: .infinity)

                    Spacer()

                    buttonGroup
                    .padding(.horizontal, 30)
                    .padding(.bottom, max(geo.safeAreaInsets.bottom + 12, 26))
                    .opacity(contentVisible ? 1 : 0)
                }
                .padding(.horizontal, 12)
            }
        }
        .onAppear {
            freezeSummaryValues()
            withAnimation(.spring(response: 0.72, dampingFraction: 0.65).delay(0.10)) {
                checkmarkScale = 1
            }
            withAnimation(.easeOut(duration: 0.45).delay(0.28)) {
                contentVisible = true
            }
            ringGlowPulse = true
            animateScoreIfNeeded()
        }
    }

    private func freezeSummaryValues() {
        finalDurationText = viewModel.elapsedFormatted
        finalBPMText = viewModel.watchBPMDisplayText
    }

    private func animateScoreIfNeeded() {
        guard !hasAnimatedScore else { return }
        hasAnimatedScore = true

        let score = targetScore
        guard score > 0 else {
            displayedScore = 0
            displayedRingProgress = 0
            return
        }

        Task {
            let animationDuration = 2.2
            let start = CACurrentMediaTime()
            while true {
                let elapsed = CACurrentMediaTime() - start
                let progress = min(max(elapsed / animationDuration, 0), 1)
                let eased = 1 - pow(1 - progress, 3)
                let nextScore = max(1, Int(round(Double(score) * eased)))

                await MainActor.run {
                    displayedScore = min(score, nextScore)
                    displayedRingProgress = Double(displayedScore) / 100.0
                }

                if progress >= 1 {
                    break
                }
                try? await Task.sleep(nanoseconds: 16_000_000)
            }

            await MainActor.run {
                displayedScore = score
                displayedRingProgress = Double(score) / 100.0
            }
        }
    }

    @ViewBuilder
    private var buttonGroup: some View {
        if UIScreen.main.bounds.width < 335 {
            VStack(spacing: 10) {
                doneButton
                shareButton
            }
        } else {
            HStack(spacing: 14) {
                doneButton
                shareButton
            }
        }
    }

    @ViewBuilder
    private func summaryRow(metricFontSize: CGFloat) -> some View {
        ViewThatFits(in: .horizontal) {
            HStack(spacing: 18) {
                Label(finalBPMText, systemImage: "heart.fill")
                    .font(.system(size: metricFontSize, weight: .medium, design: .monospaced))
                    .foregroundColor(.white.opacity(0.95))
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)

                Text("•")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(Color(hex: "67E8F9"))

                Text(finalDurationText)
                    .font(.system(size: metricFontSize, weight: .medium, design: .monospaced))
                    .foregroundColor(.white.opacity(0.95))
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
            }

            VStack(spacing: 6) {
                Label(finalBPMText, systemImage: "heart.fill")
                    .font(.system(size: metricFontSize, weight: .medium, design: .monospaced))
                    .foregroundColor(.white.opacity(0.95))
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)

                Text(finalDurationText)
                    .font(.system(size: metricFontSize, weight: .medium, design: .monospaced))
                    .foregroundColor(.white.opacity(0.95))
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
            }
        }
    }

    private var doneButton: some View {
        Button {
            withAnimation(AppConfig.Anim.transitionSpring) {
                viewModel.resetWorkout()
            }
        } label: {
            Text(doneLabel)
                .font(.system(size: 16, weight: .medium))
                .tracking(0.8)
                .foregroundColor(Color.white.opacity(0.95))
                .frame(width: actionButtonWidth, height: 52)
                .background(
                    Capsule(style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [Color(hex: "9FB08C").opacity(0.96), Color(hex: "8CA078").opacity(0.96)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                )
        }
    }

    private var shareButton: some View {
        ShareLink(
            item: shareSummaryText,
            preview: SharePreview(sharePreviewTitle)
        ) {
            Text(shareLabel)
                .font(.system(size: 16, weight: .medium))
                .tracking(0.8)
                .foregroundColor(Color.white.opacity(0.92))
                .frame(width: actionButtonWidth, height: 52)
                .background(
                    Capsule(style: .continuous)
                        .stroke(Color(hex: "A5F3FC").opacity(0.88), lineWidth: 2)
                        .background(
                            Capsule(style: .continuous)
                                .fill(Color.black.opacity(0.14))
                        )
                )
        }
    }
}
