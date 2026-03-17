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
    @State private var showLiveVoicePaywall = false
    @State private var showWorkoutSummary = false
    @State private var summaryDetent: PresentationDetent = .medium
    @State private var showShareOptions = false
    @State private var showShareSheet = false
    @State private var shareSheetItems: [Any] = []
    @State private var copiedLink = false
    @State private var xpBadgeVisible = false
    @State private var displayedScore = 0
    @State private var particlesVisible = false
    @State private var particlesDone = false
    @State private var particles: [SummaryParticle] = SummaryParticle.make()
    @State private var liveCoachVM: LiveCoachConversationViewModel? = nil
    // inlineCoachActive removed — voice coach lives inside WorkoutSummarySheet

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
    // liveCoachVoiceLabel removed — replaced by seeWorkoutButton
    private var hasPremiumAccess: Bool { subscriptionManager.hasPremiumAccess }
    // shouldShowLiveCoachVoiceButton removed — voice coach lives inside WorkoutSummarySheet
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
    private var actionButtonWidth: CGFloat { UIScreen.main.bounds.width < 390 ? 120 : 136 }
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

                    if targetScore > 0 && !coachScoreSummaryLine.isEmpty {
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

                    // Primary CTA — "See Workout" opens summary sheet (voice coach inside)
                    seeWorkoutButton
                        .padding(.horizontal, 30)
                        .padding(.bottom, 8)
                        .opacity(contentVisible ? 1 : 0)

                    // Secondary actions row
                    VStack(spacing: 6) {
                        HStack(spacing: 14) {
                            doneButton
                            shareButton
                        }

                        if copiedLink {
                            Text(L10n.current == .no ? "Lenke kopiert." : "Link copied.")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(Color(hex: "A5F3EC"))
                                .transition(.opacity)
                        }
                    }
                    .padding(.horizontal, 30)
                    .padding(.bottom, max(geo.safeAreaInsets.bottom + 12, 26))
                    .opacity(contentVisible ? 1 : 0)
                }
                .padding(.horizontal, 12)
            }
        }
        .sheet(isPresented: $showWorkoutSummary) {
            if let vm = liveCoachVM {
                WorkoutSummarySheet(
                    workoutLabel: workoutLabel,
                    xpGained: xpAwardForSummary,
                    xpToNextLevel: xpToNextLevel,
                    heartRateText: finalBPMText,
                    durationText: finalDurationText,
                    zoneTimePct: viewModel.postWorkoutSummaryContext.zoneTimeInTargetPct,
                    coachScore: targetScore,
                    liveVoiceIsAvailable: liveVoiceIsAvailable,
                    liveVoiceStatusText: liveVoiceStatusText,
                    isNorwegian: L10n.current == .no,
                    liveCoachVM: vm,
                    onStartCoaching: {
                        if liveVoiceIsAvailable {
                            summaryDetent = .large
                            Task { await vm.startIfNeeded() }
                        } else {
                            showWorkoutSummary = false
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
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
                .presentationDetents([.medium, .large], selection: $summaryDetent)
                .presentationDragIndicator(.visible)
                .presentationCornerRadius(28)
            }
        }
        .onChange(of: showWorkoutSummary) { _, isPresented in
            if !isPresented { summaryDetent = .medium }
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
            // Create voice VM eagerly so it's ready when sheet opens
            if liveCoachVM == nil {
                liveCoachVM = LiveCoachConversationViewModel(
                    summaryContext: viewModel.postWorkoutSummaryContext,
                    languageCode: liveVoiceLanguageCode,
                    userName: liveVoiceUserName,
                    isPremium: hasPremiumAccess
                )
            }
            withAnimation(.spring(response: 0.72, dampingFraction: 0.65).delay(0.10)) {
                checkmarkScale = 1
            }
            withAnimation(.easeOut(duration: 0.45).delay(0.28)) {
                contentVisible = true
            }
            // Score counter animation
            if targetScore > 0 {
                Task {
                    try? await Task.sleep(nanoseconds: 200_000_000)
                    let steps = max(1, min(targetScore, 50))
                    let stepSize = max(1, targetScore / steps)
                    let delayNs = UInt64(0.9 / Double(steps) * 1_000_000_000)
                    var current = 0
                    while current < targetScore {
                        current = min(current + stepSize, targetScore)
                        await MainActor.run { displayedScore = current }
                        try? await Task.sleep(nanoseconds: delayNs)
                    }
                }
            }
            // Particle burst
            Task {
                try? await Task.sleep(nanoseconds: 300_000_000)
                withAnimation(.easeOut(duration: 1.0)) { particlesVisible = true }
                try? await Task.sleep(nanoseconds: 1_500_000_000)
                await MainActor.run { particlesDone = true }
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

    // Primary CTA: opens workout summary sheet (voice coach lives inside)
    private var seeWorkoutButton: some View {
        Button {
            showWorkoutSummary = true
        } label: {
            HStack(spacing: 10) {
                Image(systemName: "list.bullet.rectangle.portrait")
                    .font(.system(size: 16, weight: .semibold))
                Text(L10n.current == .no ? "Se treningsøkt" : "See Workout")
                    .font(.system(size: 17, weight: .bold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(Color(hex: "1B7A8E"))
            )
        }
        .buttonStyle(.plain)
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

    private var ringGlowColor: Color {
        if targetScore >= 80 { return Color(hex: "A5F3EC") }
        if targetScore >= 60 { return Color(hex: "F59E0B") }
        return Color(hex: "4A6FA5")
    }

    private static func makeParticles() -> [SummaryParticle] { SummaryParticle.make() }

    private func scoreRingView(ringSize: CGFloat) -> some View {
        ZStack {
            // Score-based radial glow
            if targetScore > 0 {
                RadialGradient(
                    colors: [ringGlowColor.opacity(0.26), Color.clear],
                    center: .center,
                    startRadius: 0,
                    endRadius: ringSize * 0.72
                )
                .frame(width: ringSize + 56, height: ringSize + 56)
                .opacity(contentVisible ? 1 : 0)
                .animation(.easeOut(duration: 0.7).delay(0.3), value: contentVisible)
            }

            Circle()
                .fill(Color.white.opacity(0.07))
                .frame(width: ringSize + 56, height: ringSize + 56)
                .blur(radius: 18)

            // Particle burst
            if !particlesDone {
                ForEach(particles) { p in
                    Circle()
                        .fill(ringGlowColor.opacity(0.75))
                        .frame(width: p.size, height: p.size)
                        .offset(
                            x: particlesVisible ? cos(p.angle * .pi / 180) * p.distance : 0,
                            y: particlesVisible ? sin(p.angle * .pi / 180) * p.distance : 0
                        )
                        .opacity(particlesVisible ? 0 : 0.88)
                }
            }

            GamifiedCoachScoreRingView(
                score: displayedScore,
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
            .shadow(color: ringGlowColor.opacity(0.18), radius: 18, y: 2)

            if xpAwardForSummary > 0 {
                Text("+\(xpAwardForSummary) XP")
                    .font(.system(size: 26, weight: .bold, design: .rounded))
                    .foregroundColor(Color(hex: "A5F3EC"))
                    .shadow(color: Color(hex: "A5F3EC").opacity(0.5), radius: 8, y: 0)
                    .offset(y: xpBadgeVisible ? -(ringSize / 2 + 20) : -(ringSize / 2 + 10))
                    .opacity(xpBadgeVisible ? 1 : 0)
            }
        }
    }

    @ViewBuilder
    private func summaryRow(metricFontSize: CGFloat) -> some View {
        if hasFinalHeartRate {
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
        } else {
            Text(finalDurationText)
                .font(.system(size: metricFontSize, weight: .medium, design: .monospaced))
                .foregroundColor(.white.opacity(0.95))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
    }

    private var doneButton: some View {
        Button {
            withAnimation(AppConfig.Anim.transitionSpring) {
                viewModel.resetWorkout()
            }
        } label: {
            Text(doneLabel)
                .font(.system(size: 13, weight: .medium))
                .tracking(0.8)
                .foregroundColor(Color.white.opacity(0.85))
                .frame(width: actionButtonWidth, height: 42)
                .background(
                    Capsule(style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [Color(hex: "9FB08C").opacity(0.7), Color(hex: "8CA078").opacity(0.7)],
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
                .font(.system(size: 13, weight: .medium))
                .tracking(0.8)
                .foregroundColor(Color.white.opacity(0.82))
                .frame(width: actionButtonWidth, height: 42)
                .background(
                    Capsule(style: .continuous)
                        .stroke(Color(hex: "A5F3FC").opacity(0.6), lineWidth: 1.5)
                        .background(
                            Capsule(style: .continuous)
                                .fill(Color.black.opacity(0.1))
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

// MARK: - Particle Model

private struct SummaryParticle: Identifiable {
    let id = UUID()
    let angle: Double
    let distance: CGFloat
    let size: CGFloat

    static func make() -> [SummaryParticle] {
        (0..<14).map { _ in
            SummaryParticle(
                angle: Double.random(in: 0..<360),
                distance: CGFloat.random(in: 60...90),
                size: CGFloat.random(in: 4...6)
            )
        }
    }
}

// MARK: - Waveform Bars View

private struct WaveformBarsView: View {
    @ObservedObject var service: XAIRealtimeVoiceService
    let isNorwegian: Bool

    @State private var barHeights: [CGFloat] = [8, 8, 8, 8, 8, 8, 8]
    @State private var animationTimer: Timer?

    private var isConnected: Bool {
        if case .connected = service.connectionState { return true }
        return false
    }

    private var isActive: Bool { isConnected && service.isSpeaking }
    private var isUserSpeaking: Bool { isConnected && !service.isSpeaking }

    private var barColor: Color {
        if service.isSpeaking { return Color(hex: "A5F3EC") }
        if isConnected { return Color.white.opacity(0.72) }
        return Color.white.opacity(0.25)
    }

    private var statusLabel: String {
        switch service.connectionState {
        case .preparing, .connecting:
            return isNorwegian ? "KOBLER TIL..." : "CONNECTING..."
        case .connected:
            if service.isSpeaking { return isNorwegian ? "COACH SNAKKER" : "COACH SPEAKING" }
            return isNorwegian ? "HØRER PÅ DEG" : "LISTENING"
        case .ended:
            return isNorwegian ? "SAMTALE AVSLUTTET" : "CONVERSATION ENDED"
        case .failed:
            return isNorwegian ? "KUNNE IKKE KOBLE TIL" : "COULD NOT CONNECT"
        case .idle:
            return ""
        }
    }

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 5) {
                ForEach(0..<7, id: \.self) { i in
                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(barColor)
                        .frame(width: 5, height: barHeights[i])
                        .animation(.easeInOut(duration: 0.08), value: barHeights[i])
                }
            }
            .frame(height: 52)

            if !statusLabel.isEmpty {
                Text(statusLabel)
                    .font(.system(size: 14, weight: .semibold))
                    .tracking(0.8)
                    .foregroundColor(service.isSpeaking ? Color(hex: "A5F3EC") : Color.white.opacity(isConnected ? 0.75 : 0.45))
            }
        }
        .frame(maxWidth: .infinity)
        .onChange(of: isActive) { _, active in
            if active { startAnimating() } else { stopAnimating() }
        }
        .onChange(of: isUserSpeaking) { _, active in
            if active { startAnimating() } else if !service.isSpeaking { stopAnimating() }
        }
        .onDisappear { animationTimer?.invalidate() }
    }

    private func startAnimating() {
        animationTimer?.invalidate()
        animationTimer = Timer.scheduledTimer(withTimeInterval: 0.08, repeats: true) { _ in
            barHeights = (0..<7).map { _ in CGFloat.random(in: 14...44) }
        }
    }

    private func stopAnimating() {
        animationTimer?.invalidate()
        animationTimer = nil
        withAnimation(.easeOut(duration: 0.2)) {
            barHeights = [8, 8, 8, 8, 8, 8, 8]
        }
    }
}

// MARK: - Workout Summary Sheet

private struct WorkoutSummarySheet: View {
    @Environment(\.dismiss) private var dismiss

    let workoutLabel: String
    let xpGained: Int
    let xpToNextLevel: Int?
    let heartRateText: String
    let durationText: String
    let zoneTimePct: Double?
    let coachScore: Int
    let liveVoiceIsAvailable: Bool
    let liveVoiceStatusText: String
    let isNorwegian: Bool
    @ObservedObject var liveCoachVM: LiveCoachConversationViewModel
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
    // Duration shown in context header, score shown as hero element
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
        if let zone = zoneTimeFormatted {
            cells.append((isNorwegian ? "Tid i sone" : "Time in Zone", zone))
        }
        return cells
    }

    private var scoreAccentColor: Color {
        if coachScore >= 80 { return Color(hex: "A5F3EC") }
        if coachScore >= 60 { return Color(hex: "F59E0B") }
        return Color(hex: "4A6FA5")
    }

    private var showCoachPanel: Bool {
        switch liveCoachVM.service.connectionState {
        case .idle: return false
        default: return true
        }
    }

    // Compact chip row shown when coaching panel is active
    private var compactStatsLine: String {
        var parts: [String] = []
        if xpGained > 0 { parts.append("+\(xpGained) XP") }
        parts.append(durationText)
        if hasHeartRate { parts.append(heartRateText) }
        if coachScore > 0 { parts.append("Score \(coachScore)") }
        return parts.joined(separator: " · ")
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 16) {
                    // Title — shrinks when coaching active
                    Text(isNorwegian ? "Treningsoversikt" : "Workout Summary")
                        .font(.system(size: showCoachPanel ? 14 : 18, weight: showCoachPanel ? .medium : .semibold))
                        .foregroundColor(showCoachPanel ? CoachiTheme.textSecondary : CoachiTheme.textPrimary)
                        .padding(.top, 8)
                        .animation(.spring(duration: 0.35), value: showCoachPanel)

                    // Context header: workout label + duration
                    if !showCoachPanel {
                        Text("\(workoutLabel) · \(durationText)")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }

                    if showCoachPanel {
                        // Compact stat chips
                        Text(compactStatsLine)
                            .font(.system(size: 13, weight: .medium, design: .monospaced))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.7)
                            .transition(.opacity.combined(with: .move(edge: .top)))
                    } else {
                        // Score hero section
                        if coachScore > 0 {
                            VStack(spacing: 6) {
                                Text("\(coachScore)")
                                    .font(.system(size: 44, weight: .bold, design: .rounded))
                                    .foregroundColor(CoachiTheme.textPrimary)
                                Text("Coachi Score")
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .fill(scoreAccentColor.opacity(0.08))
                            )
                        }

                        // Stats grid
                        if !statCells.isEmpty {
                            statsGrid
                        }
                    }

                    if AppConfig.LiveVoice.isEnabled {
                        Divider()
                            .background(CoachiTheme.borderSubtle.opacity(0.4))

                        if showCoachPanel {
                            inlineCoachPanel
                                .transition(.move(edge: .bottom).combined(with: .opacity))
                        } else {
                            liveCoachSection
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 32)
                .animation(.spring(duration: 0.35), value: showCoachPanel)
            }
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
        VStack(spacing: 5) {
            Text(value)
                .font(.system(size: 20, weight: .bold))
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
        .padding(.vertical, 16)
    }

    private var liveCoachSection: some View {
        VStack(spacing: 16) {
            // Status badge: green dot + "Premium" OR clicks left
            HStack(spacing: 6) {
                Circle()
                    .fill(liveVoiceIsAvailable ? Color(hex: "34D399") : CoachiTheme.textSecondary.opacity(0.4))
                    .frame(width: 8, height: 8)
                Text(liveVoiceStatusText)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(liveVoiceIsAvailable ? Color(hex: "34D399") : CoachiTheme.textSecondary)
            }

            // Primary CTA — "Get feedback"
            Button {
                onStartCoaching()
            } label: {
                Text(isNorwegian ? "Få tilbakemelding" : "Get Feedback")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(
                        RoundedRectangle(cornerRadius: 28, style: .continuous)
                            .fill(
                                liveVoiceIsAvailable
                                    ? LinearGradient(
                                        colors: [Color(hex: "1B7A8E"), Color(hex: "166A7C")],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                    : LinearGradient(
                                        colors: [CoachiTheme.surfaceElevated, CoachiTheme.surfaceElevated],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                            )
                    )
                    .shadow(color: liveVoiceIsAvailable ? Color(hex: "1B7A8E").opacity(0.3) : .clear, radius: 12, y: 4)
            }
            .buttonStyle(.plain)

            bottomButtons
        }
    }

    // MARK: - Inline Coach Panel

    private var userTranscriptEntries: [LiveCoachTranscriptEntry] {
        liveCoachVM.transcriptEntries.filter { $0.role == .user }
    }

    private var inlineCoachPanel: some View {
        VStack(spacing: 16) {
            // Waveform indicator — prominent voice mode orb
            WaveformBarsView(service: liveCoachVM.service, isNorwegian: isNorwegian)
                .padding(.vertical, 20)

            // User messages only (coach speech shown via waveform, not text)
            if !userTranscriptEntries.isEmpty {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 8) {
                        ForEach(userTranscriptEntries) { entry in
                            inlineTranscriptBubble(entry: entry)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(maxHeight: 120)
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(Color.white.opacity(0.05))
                )
            }

            // Toggle button
            toggleCoachingButton

            // Home/Share
            bottomButtons
        }
    }

    private func inlineTranscriptBubble(entry: LiveCoachTranscriptEntry) -> some View {
        Text(entry.text)
            .font(.system(size: 14, weight: .regular))
            .foregroundColor(Color.white.opacity(0.82))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(Color.white.opacity(0.07))
            )
    }

    @ViewBuilder
    private var toggleCoachingButton: some View {
        let isConnecting: Bool = {
            switch liveCoachVM.service.connectionState {
            case .preparing, .connecting: return true
            default: return false
            }
        }()
        let isActive: Bool = {
            if case .connected = liveCoachVM.service.connectionState { return true }
            return false
        }()
        let isEnded: Bool = {
            switch liveCoachVM.service.connectionState {
            case .ended, .failed, .idle: return true
            default: return false
            }
        }()

        Button {
            if isEnded {
                onStartCoaching()
            } else {
                Task { await liveCoachVM.disconnect() }
            }
        } label: {
            HStack(spacing: 10) {
                if isConnecting {
                    ProgressView()
                        .tint(Color.black.opacity(0.7))
                        .scaleEffect(0.85)
                }
                Text(isActive
                    ? (isNorwegian ? "Avslutt samtalen" : "End Conversation")
                    : (isNorwegian ? "Få tilbakemelding" : "Get Feedback"))
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(.white)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(
                Group {
                    if isActive {
                        RoundedRectangle(cornerRadius: 26, style: .continuous)
                            .fill(Color.white.opacity(0.06))
                            .overlay(
                                RoundedRectangle(cornerRadius: 26, style: .continuous)
                                    .stroke(Color.white.opacity(0.28), lineWidth: 1.5)
                            )
                    } else {
                        RoundedRectangle(cornerRadius: 26, style: .continuous)
                            .fill(
                                LinearGradient(
                                    colors: [Color(hex: "1B7A8E"), Color(hex: "166A7C")],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                    }
                }
            )
            .shadow(color: isActive ? .clear : Color(hex: "1B7A8E").opacity(0.3), radius: 12, y: 4)
        }
        .buttonStyle(.plain)
        .disabled(isConnecting)
    }

    private var bottomButtons: some View {
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
