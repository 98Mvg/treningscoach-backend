//
//  WorkoutCompleteView.swift
//  TreningsCoach
//
//  Post-workout summary screen
//

import SwiftUI
import UIKit

struct WorkoutCompleteView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var subscriptionManager: SubscriptionManager
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var checkmarkScale: CGFloat = 0.65
    @State private var contentVisible = false
    @State private var displayedScore: Int = 0
    @State private var displayedRingProgress: Double = 0
    @State private var ringGlowPulse = false
    @State private var hasAnimatedScore = false
    @State private var finalDurationText = "00:00"
    @State private var finalBPMText = "0 BPM"
    @State private var showLiveCoachVoice = false
    @State private var showShareOptions = false
    @State private var showShareSheet = false
    @State private var shareSheetItems: [Any] = []
    @State private var copiedLink = false

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

    private var coachScoreStreakCount: Int {
        let threshold = AppConfig.Progression.goodCoachScoreThreshold
        var streak = 0
        for record in viewModel.coachScoreHistory.sorted(by: { $0.date > $1.date }) {
            guard record.score >= threshold else { break }
            streak += 1
        }
        return streak
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

    private var doneLabel: String { L10n.current == .no ? "FERDIG" : "DONE" }
    private var shareLabel: String { L10n.current == .no ? "DEL" : "SHARE" }
    private var shareChooserTitle: String { L10n.current == .no ? "Del økten" : "Share workout" }
    private var shareChooserSubtitle: String {
        L10n.current == .no
            ? "Velg hvor du vil dele kortet ditt."
            : "Choose where you want to share your card."
    }
    private var liveCoachVoiceLabel: String { L10n.current == .no ? "SNAKK MED COACH LIVE" : "TALK TO COACH LIVE" }
    private var actionButtonWidth: CGFloat { UIScreen.main.bounds.width < 390 ? 140 : 156 }
    private var shareURL: URL { URL(string: AppConfig.Share.coachiWebsiteURLString)! }
    private var canUseLiveCoachVoice: Bool {
        guard AppConfig.LiveVoice.isEnabled,
              authManager.isAuthenticated,
              authManager.currentUser != nil else {
            return false
        }
        return true
    }
    private var liveVoiceLanguageCode: String {
        authManager.currentUser?.language.rawValue ?? L10n.current.rawValue
    }
    private var liveVoiceUserName: String {
        authManager.currentUser?.displayName ?? ""
    }

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

                    progressHighlightsCard
                        .padding(.top, 22)
                        .padding(.horizontal, 18)
                        .opacity(contentVisible ? 1 : 0)

                    Spacer()

                    if canUseLiveCoachVoice {
                        liveCoachVoiceButton
                            .padding(.horizontal, 30)
                            .padding(.bottom, 14)
                            .opacity(contentVisible ? 1 : 0)
                    }

                    buttonGroup
                    .padding(.horizontal, 30)
                    .padding(.bottom, max(geo.safeAreaInsets.bottom + 12, 26))
                    .opacity(contentVisible ? 1 : 0)
                }
                .padding(.horizontal, 12)
            }
        }
        .sheet(isPresented: $showLiveCoachVoice) {
            LiveCoachConversationView(
                summaryContext: viewModel.postWorkoutSummaryContext,
                languageCode: liveVoiceLanguageCode,
                userName: liveVoiceUserName
            )
            .presentationDetents([.medium, .large])
            .presentationDragIndicator(.visible)
            .presentationBackgroundInteraction(.enabled(upThrough: .medium))
        }
        .sheet(isPresented: $showShareOptions) {
            WorkoutShareDestinationsSheet(
                title: shareChooserTitle,
                subtitle: shareChooserSubtitle,
                languageCode: L10n.current.rawValue,
                onInstagram: {
                    performShareSelection { shareToInstagramStory() }
                },
                onSnapchat: {
                    performShareSelection { openGenericShareSheet(destination: "snapchat") }
                },
                onTikTok: {
                    performShareSelection { openGenericShareSheet(destination: "tiktok") }
                },
                onX: {
                    performShareSelection { openGenericShareSheet(destination: "x") }
                },
                onCopyLink: {
                    performShareSelection { copyWorkoutLink() }
                }
            )
            .presentationDetents([.height(330)])
            .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $showShareSheet) {
            WorkoutSummaryActivityShareSheet(activityItems: shareSheetItems)
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

    private var liveCoachVoiceButton: some View {
        Button {
            let metadata = viewModel.postWorkoutSummaryContext.telemetryMetadata()
            Task {
                _ = await BackendAPIService.shared.trackVoiceTelemetry(
                    event: "voice_cta_tapped",
                    metadata: metadata
                )
            }
            showLiveCoachVoice = true
        } label: {
            HStack(spacing: 9) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 17, weight: .bold))
                Text(liveCoachVoiceLabel)
                    .font(.system(size: 20, weight: .semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .foregroundColor(CoachiTheme.textPrimary)
            .frame(maxWidth: .infinity)
            .frame(height: 64)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(Color.white.opacity(0.76))
            )
        }
        .buttonStyle(.plain)
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
        VStack(spacing: 10) {
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

            if copiedLink {
                Text(L10n.current == .no ? "Lenke kopiert." : "Link copied.")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: "A5F3EC"))
                    .transition(.opacity)
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

    private var progressHighlightsCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 12) {
                progressStatCard(
                    title: L10n.streak,
                    value: "\(coachScoreStreakCount)",
                    detail: L10n.current == .no ? "gode økter på rad" : "good workouts in a row"
                )

                progressStatCard(
                    title: L10n.experienceLevel,
                    value: appViewModel.trainingLevelDisplayName,
                    detail: appViewModel.levelBadgeLine
                )
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(L10n.current == .no ? "Neste nivå" : "Next level")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color.white.opacity(0.84))
                    Spacer()
                    Text(appViewModel.trainingLevelDisplayName)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(Color(hex: "A5F3EC"))
                }

                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        Capsule(style: .continuous)
                            .fill(Color.white.opacity(0.12))
                            .frame(height: 8)

                        Capsule(style: .continuous)
                            .fill(
                                LinearGradient(
                                    colors: [Color(hex: "67E8F9"), Color(hex: "A5F3EC")],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: max(12, geo.size.width * appViewModel.levelProgressFraction), height: 8)
                    }
                }
                .frame(height: 8)

                Text(appViewModel.levelProgressLine)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.74))
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.white.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(Color.white.opacity(0.12), lineWidth: 1)
        )
    }

    @ViewBuilder
    private func progressStatCard(title: String, value: String, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.6)
                .foregroundColor(Color.white.opacity(0.64))

            Text(value)
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color.white.opacity(0.96))
                .lineLimit(1)
                .minimumScaleFactor(0.75)

            Text(detail)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(Color.white.opacity(0.70))
                .lineLimit(2)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.black.opacity(0.14))
        )
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
        Button {
            showShareOptions = true
        } label: {
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
        .buttonStyle(.plain)
    }

    private func copyWorkoutLink() {
        UIPasteboard.general.url = shareURL
        withAnimation(.easeOut(duration: 0.2)) {
            copiedLink = true
        }
        Task {
            try? await Task.sleep(nanoseconds: 1_600_000_000)
            await MainActor.run {
                withAnimation(.easeOut(duration: 0.2)) {
                    copiedLink = false
                }
            }
        }
    }

    private func performShareSelection(_ action: @escaping () -> Void) {
        showShareOptions = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            action()
        }
    }

    private func shareToInstagramStory() {
        guard let storyURL = URL(string: AppConfig.Share.instagramStoriesScheme),
              UIApplication.shared.canOpenURL(storyURL),
              let cardImage = renderedShareCardImage(),
              let stickerData = cardImage.pngData() else {
            openGenericShareSheet(destination: "instagram_story")
            return
        }

        UIPasteboard.general.setItems(
            [[
                "com.instagram.sharedSticker.stickerImage": stickerData,
                "com.instagram.sharedSticker.contentURL": shareURL.absoluteString,
                "com.instagram.sharedSticker.backgroundTopColor": "#081225",
                "com.instagram.sharedSticker.backgroundBottomColor": "#112B44",
            ]],
            options: [.expirationDate: Date().addingTimeInterval(300)]
        )

        UIApplication.shared.open(storyURL)
    }

    private func openGenericShareSheet(destination: String) {
        var items: [Any] = [shareSummaryText, shareURL]
        if let cardImage = renderedShareCardImage() {
            items.insert(cardImage, at: 0)
        }
        shareSheetItems = items
        showShareSheet = true

        if destination == "snapchat" {
            _ = URL(string: AppConfig.Share.snapchatScheme)
        }
    }

    @MainActor
    private func renderedShareCardImage() -> UIImage? {
        let renderer = ImageRenderer(
            content: WorkoutSummaryShareCardView(
                workoutLabel: workoutLabel,
                durationText: finalDurationText,
                heartRateText: hasFinalHeartRate ? finalBPMText : nil,
                coachScore: targetScore,
                languageCode: L10n.current.rawValue
            )
            .frame(width: 1080, height: 1920)
        )
        renderer.scale = 1
        return renderer.uiImage
    }
}

private struct WorkoutShareDestinationsSheet: View {
    @Environment(\.dismiss) private var dismiss

    let title: String
    let subtitle: String
    let languageCode: String
    let onInstagram: () -> Void
    let onSnapchat: () -> Void
    let onTikTok: () -> Void
    let onX: () -> Void
    let onCopyLink: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Capsule()
                .fill(Color.white.opacity(0.18))
                .frame(width: 44, height: 5)
                .frame(maxWidth: .infinity)
                .padding(.top, 8)

            Text(title)
                .font(.system(size: 24, weight: .bold))
                .foregroundStyle(CoachiTheme.textPrimary)

            Text(subtitle)
                .font(.system(size: 14, weight: .medium))
                .foregroundStyle(CoachiTheme.textSecondary)

            HStack(spacing: 12) {
                shareButton(label: "Instagram", accent: Color(hex: "E1306C"), icon: .camera) {
                    onInstagram()
                }
                shareButton(label: "Snapchat", accent: Color(hex: "FFFC00"), icon: .snapchat) {
                    onSnapchat()
                }
                shareButton(label: "TikTok", accent: Color.black, icon: .tiktok) {
                    onTikTok()
                }
            }

            HStack(spacing: 12) {
                shareButton(label: "X", accent: Color.black, icon: .x) {
                    onX()
                }
                shareButton(label: languageCode == "no" ? "Kopier lenke" : "Copy Link", accent: Color(hex: "4F46E5"), icon: .link) {
                    onCopyLink()
                }
            }

            Button(languageCode == "no" ? "Lukk" : "Close") {
                dismiss()
            }
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(CoachiTheme.textSecondary)
            .frame(maxWidth: .infinity)
            .padding(.top, 4)
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 20)
        .background(CoachiTheme.background)
    }

    @ViewBuilder
    private func shareButton(label: String, accent: Color, icon: ShareDestinationIcon, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .fill(accent.opacity(icon == .snapchat ? 0.92 : 1))
                        .frame(width: 64, height: 64)
                    shareIcon(for: icon)
                }
                Text(label)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(CoachiTheme.textPrimary)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .minimumScaleFactor(0.8)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func shareIcon(for icon: ShareDestinationIcon) -> some View {
        switch icon {
        case .camera:
            Image(systemName: "camera.fill")
                .font(.system(size: 24, weight: .bold))
                .foregroundStyle(Color.white)
        case .snapchat:
            Text("S")
                .font(.system(size: 26, weight: .black, design: .rounded))
                .foregroundStyle(Color.black)
        case .tiktok:
            Image(systemName: "music.note")
                .font(.system(size: 24, weight: .bold))
                .foregroundStyle(Color.white)
        case .x:
            Text("X")
                .font(.system(size: 24, weight: .black, design: .rounded))
                .foregroundStyle(Color.white)
        case .link:
            Image(systemName: "link")
                .font(.system(size: 24, weight: .bold))
                .foregroundStyle(Color.white)
        }
    }
}

private enum ShareDestinationIcon: Equatable {
    case camera
    case snapchat
    case tiktok
    case x
    case link
}

private struct WorkoutSummaryShareCardView: View {
    let workoutLabel: String
    let durationText: String
    let heartRateText: String?
    let coachScore: Int
    let languageCode: String

    private var durationLabel: String {
        languageCode == "no" ? "Varighet" : "Duration"
    }

    private var heartRateLabel: String {
        languageCode == "no" ? "Puls" : "Heart Rate"
    }

    private var scoreLabel: String {
        languageCode == "no" ? "Coach score" : "Coaching Score"
    }

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "081225"), Color(hex: "10253A"), Color(hex: "153A56")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 34) {
                HStack(spacing: 16) {
                    ZStack {
                        Circle()
                            .fill(Color.white.opacity(0.12))
                            .frame(width: 96, height: 96)
                        Image(systemName: "figure.run")
                            .font(.system(size: 40, weight: .semibold))
                            .foregroundStyle(Color(hex: "A5F3EC"))
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        Text("COACHI")
                            .font(.system(size: 28, weight: .black))
                            .tracking(2.4)
                            .foregroundStyle(Color.white.opacity(0.95))
                        Text(workoutLabel.uppercased())
                            .font(.system(size: 28, weight: .medium))
                            .foregroundStyle(Color.white.opacity(0.78))
                    }
                }

                VStack(alignment: .leading, spacing: 16) {
                    Text(scoreLabel.uppercased())
                        .font(.system(size: 24, weight: .semibold))
                        .tracking(1.4)
                        .foregroundStyle(Color(hex: "A5F3EC"))

                    Text("\(coachScore)")
                        .font(.system(size: 176, weight: .black, design: .rounded))
                        .foregroundStyle(Color.white)
                        .minimumScaleFactor(0.7)
                }

                VStack(spacing: 14) {
                    metricRow(label: durationLabel, value: durationText)
                    metricRow(label: heartRateLabel, value: heartRateText ?? "--")
                }

                Spacer()

                Text(languageCode == "no" ? "Del økten din med Coachi" : "Share your workout with Coachi")
                    .font(.system(size: 34, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.88))

                Text("coachi.app")
                    .font(.system(size: 28, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.7))
            }
            .padding(72)
        }
    }

    @ViewBuilder
    private func metricRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 24, weight: .medium))
                .foregroundStyle(Color.white.opacity(0.7))
            Spacer()
            Text(value)
                .font(.system(size: 42, weight: .bold, design: .rounded))
                .foregroundStyle(Color.white)
        }
        .padding(.horizontal, 26)
        .padding(.vertical, 20)
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(Color.white.opacity(0.08))
        )
    }
}

private struct WorkoutSummaryActivityShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
