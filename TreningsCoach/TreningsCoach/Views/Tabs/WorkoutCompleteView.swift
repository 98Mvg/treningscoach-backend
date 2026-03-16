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
    @Environment(\.scenePhase) private var scenePhase
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var checkmarkScale: CGFloat = 0.65
    @State private var contentVisible = false
    @State private var finalDurationText = "00:00"
    @State private var finalBPMText = "0 BPM"
    @StateObject private var liveVoiceTracker = LiveVoiceSessionTracker.shared
    @State private var showLiveCoachVoice = false
    @State private var showLiveVoicePaywall = false
    @State private var showWorkoutSummary = false
    @State private var showShareOptions = false
    @State private var showShareSheet = false
    @State private var shareSheetItems: [Any] = []
    @State private var copiedLink = false
    @State private var xpBadgeVisible = false

    private var targetScore: Int {
        if viewModel.hasAuthoritativeCoachScore {
            return max(0, min(100, viewModel.coachScore))
        }
        return 0
    }

    private var coachScoreSummaryLine: String {
        let line = viewModel.completedWorkoutSnapshot?.summaryContext.coachScoreSummaryLine
            ?? viewModel.postWorkoutSummaryContext.coachScoreSummaryLine
        return line
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

    private var summaryProgressAward: CoachiProgressAward? {
        viewModel.completedWorkoutSnapshot?.coachiProgressAward ?? viewModel.lastCoachiProgressAward
    }

    private var xpAwardForSummary: Int {
        summaryProgressAward?.xpAwarded ?? 0
    }

    private var summaryLevelLabel: String { "" }

    private var xpToNextLevel: Int? {
        summaryProgressAward?.stateAfterAward.xpToNextLevel
    }

    private var summaryXPProgress: Double {
        summaryProgressAward?.xpProgressAfterFraction ?? appViewModel.coachiXPProgressFraction
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

    private var doneLabel: String { L10n.current == .no ? "HJEM" : "HOME" }
    private var shareLabel: String { L10n.current == .no ? "DEL" : "SHARE" }
    private var shareChooserTitle: String { L10n.current == .no ? "Del økten" : "Share workout" }
    private var shareChooserSubtitle: String {
        L10n.current == .no
            ? "Velg hvor du vil dele kortet ditt."
            : "Choose where you want to share your card."
    }
    private var liveCoachVoiceLabel: String { L10n.current == .no ? "Treningsoversikt" : "Workout Summary" }
    private var hasPremiumAccess: Bool { subscriptionManager.hasPremiumAccess }
    private var shouldShowLiveCoachVoiceButton: Bool { AppConfig.LiveVoice.isEnabled }
    private var hasLiveVoiceAccountAccess: Bool {
        authManager.hasUsableSession()
    }
    private var remainingLiveSessions: Int? {
        guard hasLiveVoiceAccountAccess else { return nil }
        return liveVoiceTracker.remainingToday(isPremium: hasPremiumAccess)
    }
    private var liveVoiceIsAvailable: Bool {
        hasLiveVoiceAccountAccess && liveVoiceTracker.canStart(isPremium: hasPremiumAccess)
    }
    private var actionButtonWidth: CGFloat { UIScreen.main.bounds.width < 390 ? 140 : 156 }
    private var shareURL: URL { URL(string: AppConfig.Share.coachiWebsiteURLString)! }
    private var liveVoiceLanguageCode: String {
        authManager.currentUser?.language.rawValue ?? L10n.current.rawValue
    }
    private var liveVoiceUserName: String {
        authManager.currentUser?.resolvedDisplayName ?? appViewModel.userProfile.name
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

                    scoreRingView(ringSize: ringSize)
                    .padding(.top, 26)
                    .opacity(contentVisible ? 1 : 0)

                    if !coachScoreSummaryLine.isEmpty {
                        Text(coachScoreSummaryLine)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.white.opacity(0.72))
                            .multilineTextAlignment(.center)
                            .lineLimit(2)
                            .minimumScaleFactor(0.85)
                            .padding(.horizontal, 20)
                            .padding(.top, 18)
                            .opacity(contentVisible ? 1 : 0)
                    }

                    summaryRow(metricFontSize: metricFontSize)
                    .padding(.top, coachScoreSummaryLine.isEmpty ? 34 : 14)
                    .opacity(contentVisible ? 1 : 0)
                    .frame(maxWidth: .infinity)

                    Spacer()

                    if shouldShowLiveCoachVoiceButton {
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
        .sheet(isPresented: $showWorkoutSummary) {
            WorkoutSummarySheet(
                xpGained: xpAwardForSummary,
                xpToNextLevel: xpToNextLevel,
                heartRateText: finalBPMText,
                durationText: finalDurationText,
                zoneTimePct: viewModel.postWorkoutSummaryContext.zoneTimeInTargetPct,
                coachScore: targetScore,
                liveVoiceIsAvailable: liveVoiceIsAvailable,
                liveVoiceStatusText: liveVoiceStatusText,
                isNorwegian: L10n.current == .no,
                onStartCoaching: {
                    showWorkoutSummary = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                        if liveVoiceIsAvailable {
                            showLiveCoachVoice = true
                        } else {
                            showLiveVoicePaywall = true
                        }
                    }
                },
                onHome: {
                    showWorkoutSummary = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                        withAnimation(AppConfig.Anim.transitionSpring) {
                            viewModel.resetWorkout()
                        }
                    }
                },
                onShare: {
                    showWorkoutSummary = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                        showShareOptions = true
                    }
                }
            )
            .presentationDetents([.medium])
            .presentationDragIndicator(.visible)
            .presentationCornerRadius(28)
        }
        .sheet(isPresented: $showLiveCoachVoice) {
            LiveCoachConversationView(
                summaryContext: viewModel.postWorkoutSummaryContext,
                languageCode: liveVoiceLanguageCode,
                userName: liveVoiceUserName,
                isPremium: hasPremiumAccess
            )
            .presentationDetents([.medium, .large])
            .presentationDragIndicator(.visible)
            .presentationBackgroundInteraction(.enabled(upThrough: .medium))
        }
        .sheet(isPresented: $showLiveVoicePaywall) {
            PaywallView(context: .liveVoice)
                .environmentObject(subscriptionManager)
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
            liveVoiceTracker.synchronize()
            freezeSummaryValues()
            withAnimation(.spring(response: 0.72, dampingFraction: 0.65).delay(0.10)) {
                checkmarkScale = 1
            }
            withAnimation(.easeOut(duration: 0.45).delay(0.28)) {
                contentVisible = true
            }
            if xpAwardForSummary > 0 {
                withAnimation(.spring(response: 0.55, dampingFraction: 0.62).delay(0.55)) {
                    xpBadgeVisible = true
                }
                Task {
                    try? await Task.sleep(nanoseconds: 2_400_000_000)
                    await MainActor.run {
                        withAnimation(.easeOut(duration: 0.4)) {
                            xpBadgeVisible = false
                        }
                    }
                }
            }
        }
        .onChange(of: scenePhase) { _, newPhase in
            if newPhase == .active {
                liveVoiceTracker.synchronize()
            }
        }
    }

    private var liveCoachVoiceButton: some View {
        VStack(spacing: 6) {
            // Status line
            HStack(spacing: 6) {
                Circle()
                    .fill(liveVoiceIsAvailable ? CoachiTheme.success : Color.white.opacity(0.35))
                    .frame(width: 6, height: 6)
                Text(liveVoiceStatusText)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.55))
                    .lineLimit(1)
            }

            // Button
            Button {
                let metadata = viewModel.postWorkoutSummaryContext.telemetryMetadata()
                Task {
                    _ = await BackendAPIService.shared.trackVoiceTelemetry(
                        event: "voice_cta_tapped",
                        metadata: metadata
                    )
                }
                showWorkoutSummary = true
            } label: {
                Text(liveCoachVoiceLabel)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(CoachiTheme.textPrimary.opacity(liveVoiceIsAvailable ? 1 : 0.55))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .fill(Color.white.opacity(liveVoiceIsAvailable ? 0.55 : 0.22))
                    )
            }
            .buttonStyle(.plain)
        }
    }

    private var liveVoiceStatusText: String {
        if liveVoiceIsAvailable {
            if let remaining = remainingLiveSessions {
                // Free user with sessions available
                let unit = L10n.current == .no
                    ? (remaining == 1 ? "økt igjen i dag" : "økter igjen i dag")
                    : (remaining == 1 ? "session left today" : "sessions left today")
                return L10n.current == .no ? "Gratis: \(remaining) \(unit)" : "Free: \(remaining) \(unit)"
            }
            // Premium — no session counting shown
            return "Premium"
        }
        if !hasLiveVoiceAccountAccess {
            return L10n.current == .no ? "Logg inn for å bruke live" : "Sign in to use live"
        }
        return L10n.current == .no ? "Ingen økter igjen i dag" : "No sessions left today"
    }

    private func freezeSummaryValues() {
        finalDurationText = viewModel.completedWorkoutSnapshot?.durationText ?? viewModel.elapsedFormatted
        finalBPMText = viewModel.completedWorkoutSnapshot?.finalHeartRateText ?? viewModel.watchBPMDisplayText
    }

    private func scoreRingView(ringSize: CGFloat) -> some View {
        ZStack {
            Circle()
                .fill(Color.white.opacity(0.07))
                .frame(width: ringSize + 56, height: ringSize + 56)
                .blur(radius: 18)

            GamifiedCoachScoreRingView(
                score: targetScore,
                label: L10n.current == .no ? "Score" : "Score",
                size: ringSize,
                lineWidth: 14,
                animateFromOne: false,
                fullSweepBeforeSettling: false,
                animationDuration: 2.2,
                trackColor: Color.white.opacity(0.20),
                gradientColors: [
                    Color.white.opacity(0.97),
                    Color(hex: "A5F3EC"),
                    Color(hex: "67E8F9"),
                    Color.white.opacity(0.9),
                ],
                valueColor: Color.white.opacity(0.97),
                labelColor: Color.white.opacity(0.80),
                levelColor: CoachiTheme.success,
                levelLabel: summaryLevelLabel,
                xpProgress: summaryXPProgress,
                showsOuterXPRing: true,
                animateXPAward: xpAwardForSummary > 0,
                xpAnimationFrom: summaryProgressAward?.xpProgressBeforeFraction,
                xpAnimationTo: summaryProgressAward?.xpProgressAfterFraction
            )
            .shadow(color: Color.white.opacity(0.12), radius: 16, y: 2)

            if xpAwardForSummary > 0 {
                Text("+\(xpAwardForSummary) XP")
                    .font(.system(size: 22, weight: .bold, design: .rounded))
                    .foregroundColor(Color(hex: "A5F3EC"))
                    .shadow(color: Color(hex: "A5F3EC").opacity(0.55), radius: 8, y: 0)
                    .offset(y: xpBadgeVisible ? -(ringSize / 2 + 20) : -(ringSize / 2 + 10))
                    .opacity(xpBadgeVisible ? 1 : 0)
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

// MARK: - Workout Summary Sheet

private struct WorkoutSummarySheet: View {
    @Environment(\.dismiss) private var dismiss

    let xpGained: Int
    let xpToNextLevel: Int?
    let heartRateText: String
    let durationText: String
    let zoneTimePct: Double?
    let coachScore: Int
    let liveVoiceIsAvailable: Bool
    let liveVoiceStatusText: String
    let isNorwegian: Bool
    let onStartCoaching: () -> Void
    let onHome: () -> Void
    let onShare: () -> Void

    private var hasHeartRate: Bool {
        !heartRateText.isEmpty && heartRateText != "0 BPM" && heartRateText != "—"
    }

    private var zoneTimeFormatted: String? {
        guard let pct = zoneTimePct else { return nil }
        let clamped = max(0.0, min(pct <= 1.0 ? pct * 100.0 : pct, 100.0))
        return "\(Int(clamped))%"
    }

    // Build ordered list of (title, value) cells — only available data
    private var statCells: [(title: String, value: String)] {
        var cells: [(String, String)] = []

        if xpGained > 0 {
            cells.append((isNorwegian ? "XP opptjent" : "XP Gained", "+\(xpGained)"))
        }
        if let toNext = xpToNextLevel, toNext > 0 {
            cells.append((isNorwegian ? "XP til neste nivå" : "XP to Next Level", "\(toNext)"))
        }
        if hasHeartRate {
            cells.append((isNorwegian ? "Puls" : "Heart Rate", heartRateText))
        }
        cells.append((isNorwegian ? "Varighet" : "Duration", durationText))
        if let zone = zoneTimeFormatted {
            cells.append((isNorwegian ? "Tid i sone" : "Time in Zone", zone))
        }
        if coachScore > 0 {
            cells.append(("Coachi Score", "\(coachScore)"))
        }
        return cells
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // Title
                Text(isNorwegian ? "Treningsoversikt" : "Workout Summary")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 8)

                // Adaptive stats grid
                if !statCells.isEmpty {
                    statsGrid
                }

                if AppConfig.LiveVoice.isEnabled {
                    Divider()
                        .background(CoachiTheme.borderSubtle.opacity(0.4))

                    liveCoachSection
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 32)
        }
        .background(CoachiTheme.bg.ignoresSafeArea())
    }

    private var statRows: [[(title: String, value: String)]] {
        var result: [[(title: String, value: String)]] = []
        var i = 0
        while i < statCells.count {
            if i + 1 < statCells.count {
                result.append([statCells[i], statCells[i + 1]])
            } else {
                result.append([statCells[i]])
            }
            i += 2
        }
        return result
    }

    private var statsGrid: some View {
        VStack(spacing: 0) {
            ForEach(statRows.indices, id: \.self) { rowIdx in
                if rowIdx > 0 { Divider() }
                HStack(spacing: 0) {
                    statCell(title: statRows[rowIdx][0].title, value: statRows[rowIdx][0].value)
                    if statRows[rowIdx].count > 1 {
                        Divider().frame(width: 1)
                        statCell(title: statRows[rowIdx][1].title, value: statRows[rowIdx][1].value)
                    }
                }
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(CoachiTheme.surface)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.28), lineWidth: 1)
        )
    }

    private func statCell(title: String, value: String) -> some View {
        VStack(spacing: 6) {
            Text(value)
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
    }

    private var liveCoachSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text(isNorwegian ? "Snakk med Coach Live" : "Talk to Coach Live")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                Text(isNorwegian
                    ? "Still spørsmål om denne økten"
                    : "Ask questions about this workout")
                    .font(.system(size: 14))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            Button {
                onStartCoaching()
            } label: {
                Text(isNorwegian ? "Start coaching" : "Start Coaching")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 64)
                    .background(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .fill(liveVoiceIsAvailable
                                ? CoachiTheme.accent
                                : CoachiTheme.surfaceElevated)
                    )
            }
            .buttonStyle(.plain)

            HStack(spacing: 6) {
                Circle()
                    .fill(liveVoiceIsAvailable ? CoachiTheme.success : CoachiTheme.textSecondary.opacity(0.4))
                    .frame(width: 6, height: 6)
                Text(liveVoiceStatusText)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            HStack(spacing: 12) {
                Button {
                    onHome()
                } label: {
                    Text(isNorwegian ? "HJEM" : "HOME")
                        .font(.system(size: 14, weight: .medium))
                        .tracking(0.6)
                        .foregroundColor(Color.white.opacity(0.9))
                        .frame(maxWidth: .infinity)
                        .frame(height: 44)
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
                .buttonStyle(.plain)

                Button {
                    onShare()
                } label: {
                    Text(isNorwegian ? "DEL" : "SHARE")
                        .font(.system(size: 14, weight: .medium))
                        .tracking(0.6)
                        .foregroundColor(Color.white.opacity(0.92))
                        .frame(maxWidth: .infinity)
                        .frame(height: 44)
                        .background(
                            Capsule(style: .continuous)
                                .stroke(Color(hex: "A5F3FC").opacity(0.88), lineWidth: 2)
                                .background(
                                    Capsule(style: .continuous)
                                        .fill(Color.black.opacity(0.08))
                                )
                        )
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 4)
        }
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
