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
    @State private var showLiveVoiceAuth = false
    @State private var showWorkoutSummary = false
    @State private var summaryDetent: PresentationDetent = .medium
    @State private var showShareOptions = false
    @State private var showShareSheet = false
    @State private var shareSheetItems: [Any] = []
    @State private var copiedLink = false
    @State private var xpBadgeVisible = false
    @State private var xpCelebrationFinished = false
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

    private var showXPCelebration: Bool {
        xpAwardForSummary > 0 && !xpCelebrationFinished
    }

    private var summaryLevelLabel: String { "" }

    private var xpToNextLevel: Int? {
        summaryProgressAward?.stateAfterAward.xpToNextLevel
    }

    private var summaryXPProgress: Double {
        summaryProgressAward?.xpProgressAfterFraction ?? appViewModel.coachiXPProgressFraction
    }

    private var summaryStreakDays: Int {
        viewModel.coachScoreHistory.currentWorkoutStreak()
    }

    private var summaryXPLineText: String {
        if let xpToNextLevel {
            if xpToNextLevel == 0 {
                return L10n.maxLevelReached
            }
            return "\(xpToNextLevel) \(L10n.xpToNextLevel)"
        }
        return appViewModel.coachiXPLine
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
    // liveCoachVoiceLabel removed — replaced by getFeedbackButton
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

                    summaryProgressPills
                        .padding(.top, 18)
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

                    // Primary CTA — "Get Feedback" opens session summary sheet
                    getFeedbackButton
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
                    averageHeartRate: viewModel.averageHeartRate,
                    distanceMeters: viewModel.distanceMeters,
                    durationText: finalDurationText,
                    zoneTimePct: viewModel.postWorkoutSummaryContext.zoneTimeInTargetPct,
                    coachScore: targetScore,
                    liveVoiceIsAvailable: liveVoiceIsAvailable,
                    liveVoiceStatusText: liveVoiceStatusText,
                    liveVoiceQuotaDetailText: liveVoiceQuotaDetailText,
                    isPremium: hasPremiumAccess,
                    isNorwegian: L10n.current == .no,
                    liveCoachVM: vm,
                    subscriptionManager: subscriptionManager,
                    onStartCoaching: {
                        Task {
                            var metadata = vm.summaryContext.telemetryMetadata().reduce(into: [String: Any]()) { partialResult, entry in
                                partialResult[entry.key] = entry.value
                            }
                            metadata["entry_point"] = "workout_summary_sheet"
                            metadata["live_voice_available"] = liveVoiceIsAvailable
                            metadata["is_premium"] = hasPremiumAccess
                            if let remainingToday = liveVoiceTracker.remainingToday(isPremium: hasPremiumAccess) {
                                metadata["remaining_today"] = remainingToday
                            }
                            _ = await BackendAPIService.shared.trackVoiceTelemetry(
                                event: "voice_cta_tapped",
                                metadata: metadata
                            )
                        }
                        if liveVoiceIsAvailable {
                            Task { await vm.startIfNeeded() }
                        } else if !hasLiveVoiceAccountAccess {
                            // Guest: show sign-in, not paywall
                            showWorkoutSummary = false
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                                showLiveVoiceAuth = true
                            }
                        } else {
                            // Signed in but quota exhausted: show paywall
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
                .presentationDragIndicator(.hidden)
                .presentationBackground(.clear)
            }
        }
        .onChange(of: showWorkoutSummary) { _, isPresented in
            if isPresented {
                BackendAPIService.shared.wakeBackend()
            } else {
                summaryDetent = .medium
            }
        }
        .sheet(isPresented: $showLiveVoiceAuth) {
            AuthView(
                mode: .login,
                onContinue: {
                    showLiveVoiceAuth = false
                    // Auto-start voice session after successful login
                    if let vm = liveCoachVM {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                            Task { await vm.startIfNeeded() }
                        }
                    }
                },
                onContinueWithoutAccount: {
                    showLiveVoiceAuth = false
                },
                onSeePremium: {
                    showLiveVoiceAuth = false
                    showLiveVoicePaywall = true
                },
                allowsContinueWithoutAccountInLoginMode: true
            )
            .environmentObject(authManager)
        }
        .sheet(isPresented: $showLiveVoicePaywall) {
            NavigationStack {
                ScrollView(showsIndicators: false) {
                    WatchConnectedPremiumOfferStepView(
                        watchManager: PhoneWCManager.shared,
                        onBack: { showLiveVoicePaywall = false },
                        onContinue: { showLiveVoicePaywall = false },
                        presentationMode: .manageSubscriptionInline
                    )
                    .environmentObject(subscriptionManager)
                    .frame(height: max(UIScreen.main.bounds.height * 0.86, 760))
                }
                .background(CoachiTheme.bg.ignoresSafeArea())
                .navigationTitle(L10n.current == .no ? "Administrer abonnement" : "Manage subscription")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button(L10n.current == .no ? "Tilbake" : "Back") {
                            showLiveVoicePaywall = false
                        }
                    }
                }
            }
        }
        .sheet(isPresented: $showShareOptions) {
            WorkoutShareDestinationsSheet(
                title: shareChooserTitle,
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
            .presentationDetents([.height(420)])
            .presentationDragIndicator(.hidden)
            .presentationBackground(.clear)
        }
        .sheet(isPresented: $showShareSheet) {
            WorkoutSummaryActivityShareSheet(activityItems: shareSheetItems)
        }
        .onAppear {
            liveVoiceTracker.synchronize()
            freezeSummaryValues()
            xpCelebrationFinished = false
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
                    try? await Task.sleep(nanoseconds: 1_500_000_000)
                    await MainActor.run {
                        withAnimation(.easeOut(duration: 0.4)) {
                            xpBadgeVisible = false
                            xpCelebrationFinished = true
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

    // Primary CTA: opens session summary sheet
    private var getFeedbackButton: some View {
        Button {
            showWorkoutSummary = true
        } label: {
            ZStack {
                Text(L10n.current == .no ? "Få tilbakemelding" : "Get Feedback")
                    .font(.system(size: 18, weight: .bold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.84)

                HStack(spacing: 0) {
                    Image(systemName: "chart.bar.doc.horizontal")
                        .font(.system(size: 18, weight: .bold))
                        .frame(width: 24)
                    Spacer()
                }
            }
            .padding(.horizontal, 22)
            .frame(maxWidth: 332)
            .frame(height: 60)
        }
        .buttonStyle(SummarySurfaceButtonStyle(variant: .hero))
    }

    private var liveVoiceStatusText: String {
        if liveVoiceIsAvailable {
            if let remaining = remainingLiveSessions {
                return L10n.current == .no
                    ? "Gratis i dag: \(remaining) igjen"
                    : "Free today: \(remaining) remaining"
            }
            return L10n.current == .no ? "Premium live coach" : "Premium live coach"
        }
        if !hasLiveVoiceAccountAccess {
            return L10n.current == .no ? "Logg inn for å snakke med coachen" : "Sign in to talk to your coach"
        }
        return L10n.current == .no
            ? "Dagens gratispreview er brukt"
            : "Today's free preview is used"
    }

    private var liveVoiceQuotaDetailText: String {
        if !hasLiveVoiceAccountAccess {
            return L10n.current == .no
                ? "Opprett en gratis konto og få 30 sekunder coaching."
                : "Create a free account and get 30 seconds of coaching."
        }

        if hasPremiumAccess {
            return L10n.current == .no
                ? "Opptil \(AppConfig.LiveVoice.premiumMaxDurationSeconds / 60) minutter per samtale"
                : "Up to \(AppConfig.LiveVoice.premiumMaxDurationSeconds / 60) minutes per session"
        }

        return L10n.current == .no ? "30 sekunder maks per samtale" : "30 seconds max per session"
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
                xpProgress: showXPCelebration ? summaryXPProgress : nil,
                showsOuterXPRing: showXPCelebration,
                animateXPAward: showXPCelebration,
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

    private var summaryProgressPills: some View {
        HStack(spacing: 10) {
            progressPill(
                icon: "flame.fill",
                title: L10n.streak,
                value: "\(summaryStreakDays)"
            )
            if showXPCelebration {
                progressPill(
                    icon: "sparkles",
                    title: "XP",
                    value: summaryXPLineText
                )
            }
        }
        .frame(maxWidth: .infinity)
    }

    private func progressPill(icon: String, title: String, value: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(Color(hex: "A5F3EC"))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.white.opacity(0.72))
                Text(value)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white.opacity(0.96))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(Color.white.opacity(0.08))
        .clipShape(Capsule(style: .continuous))
    }

    private var displayHeartRateText: String {
        if let avg = viewModel.averageHeartRate, avg > 0 {
            "Avg \(avg) BPM"
        } else {
            finalBPMText
        }
    }

    @ViewBuilder
    private func summaryRow(metricFontSize: CGFloat) -> some View {
        if hasFinalHeartRate || (viewModel.averageHeartRate ?? 0) > 0 {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 18) {
                    Label(displayHeartRateText, systemImage: "heart.fill")
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
                    Label(displayHeartRateText, systemImage: "heart.fill")
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
                .frame(width: actionButtonWidth, height: 42)
        }
        .buttonStyle(SummarySurfaceButtonStyle(variant: .utility))
    }

    private var shareButton: some View {
        Button {
            showShareOptions = true
        } label: {
            Text(shareLabel)
                .font(.system(size: 13, weight: .medium))
                .tracking(0.8)
                .frame(width: actionButtonWidth, height: 42)
        }
        .buttonStyle(SummarySurfaceButtonStyle(variant: .outline))
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
        if service.isSpeaking { return CoachiTheme.secondary }
        if isConnected { return CoachiTheme.primary.opacity(0.78) }
        return CoachiTheme.textTertiary.opacity(0.45)
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

    private var statusColor: Color {
        switch service.connectionState {
        case .preparing, .connecting:
            return Color.white.opacity(0.92)
        case .connected:
            return service.isSpeaking ? CoachiTheme.secondary : Color.white.opacity(0.96)
        case .ended:
            return Color.white.opacity(0.98)
        case .failed:
            return CoachiTheme.danger.opacity(0.96)
        case .idle:
            return .clear
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
                    .foregroundColor(statusColor)
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
    @State private var showTimeLimitPaywall = false
    @State private var showTextCoach = false
    @State private var isPlayingPreviewLimitAudio = false

    let workoutLabel: String
    let xpGained: Int
    let xpToNextLevel: Int?
    let heartRateText: String
    let averageHeartRate: Int?
    let distanceMeters: Double?
    let durationText: String
    let zoneTimePct: Double?
    let coachScore: Int
    let liveVoiceIsAvailable: Bool
    let liveVoiceStatusText: String
    let liveVoiceQuotaDetailText: String
    let isPremium: Bool
    let isNorwegian: Bool
    @ObservedObject var liveCoachVM: LiveCoachConversationViewModel
    @ObservedObject var subscriptionManager: SubscriptionManager
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

        if let avgHR = averageHeartRate, avgHR > 0 {
            cells.append((isNorwegian ? "Snitt puls" : "Avg Heart Rate", "\(avgHR) BPM"))
        } else if hasHeartRate {
            cells.append((isNorwegian ? "Puls" : "Heart Rate", heartRateText))
        }
        if let dist = distanceMeters, dist > 0 {
            let km = dist / 1000.0
            cells.append((isNorwegian ? "Distanse" : "Distance", String(format: "%.2f km", km)))
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

    private var sheetCardMaxWidth: CGFloat { 392 }

    private var summaryCardBackground: some View {
        WorkoutModalCardBackground()
    }

    // Compact chip row shown when coaching panel is active
    private var compactStatsLine: String {
        var parts: [String] = []
        parts.append(durationText)
        if let dist = distanceMeters, dist > 0 {
            parts.append(String(format: "%.1f km", dist / 1000.0))
        }
        if let avgHR = averageHeartRate, avgHR > 0 {
            parts.append("\(avgHR) BPM")
        } else if hasHeartRate {
            parts.append(heartRateText)
        }
        if coachScore > 0 { parts.append("Score \(coachScore)") }
        return parts.joined(separator: " · ")
    }

    var body: some View {
        ZStack {
            Color.clear.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer(minLength: 0)

                Group {
                    if showCoachPanel {
                        fullScreenCoachPanel
                    } else {
                        ScrollView(showsIndicators: false) {
                            VStack(alignment: .leading, spacing: 18) {
                                HStack(spacing: 8) {
                                    Image(systemName: "sparkles.rectangle.stack.fill")
                                        .font(.system(size: 11, weight: .bold))
                                    Text(isNorwegian ? "Coachi innsikt" : "Coachi Insight")
                                        .font(.system(size: 11, weight: .bold))
                                        .tracking(0.5)
                                }
                                .foregroundColor(CoachiTheme.accent.opacity(0.92))
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(
                                    Capsule(style: .continuous)
                                        .fill(Color.white.opacity(0.10))
                                        .overlay(
                                            Capsule(style: .continuous)
                                                .stroke(CoachiTheme.accent.opacity(0.22), lineWidth: 1)
                                        )
                                )

                                VStack(alignment: .leading, spacing: 4) {
                                    Text(isNorwegian ? "Treningsoversikt" : "Workout Summary")
                                        .font(.system(size: 21, weight: .semibold, design: .serif))
                                        .foregroundColor(Color.white.opacity(0.94))

                                    Text("\(workoutLabel) · \(durationText)")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(CoachiTheme.accent.opacity(0.88))
                                }

                                if !statCells.isEmpty {
                                    statsGrid
                                }

                                if AppConfig.LiveVoice.isEnabled {
                                    liveCoachSection
                                }
                            }
                            .padding(.horizontal, 18)
                            .padding(.vertical, 20)
                        }
                        .background(summaryCardBackground)
                    }
                }
            }
            .frame(maxWidth: sheetCardMaxWidth, maxHeight: .infinity, alignment: .bottom)
            .padding(.horizontal, 16)
            .padding(.top, 18)
            .padding(.bottom, 16)
        }
        .animation(.spring(duration: 0.35), value: showCoachPanel)
        .onChange(of: liveCoachVM.service.lastDisconnectReason) { _, reason in
            guard reason == .timeLimit, !isPremium, !isPlayingPreviewLimitAudio else { return }
            isPlayingPreviewLimitAudio = true
            Task {
                await liveCoachVM.service.playFreePreviewLockClipIfAvailable()
                await MainActor.run {
                    isPlayingPreviewLimitAudio = false
                    showTimeLimitPaywall = true
                }
            }
        }
        .sheet(isPresented: $showTimeLimitPaywall) {
            NavigationStack {
                ScrollView(showsIndicators: false) {
                    WatchConnectedPremiumOfferStepView(
                        watchManager: PhoneWCManager.shared,
                        onBack: { showTimeLimitPaywall = false },
                        onContinue: { showTimeLimitPaywall = false },
                        presentationMode: .manageSubscriptionInline
                    )
                    .environmentObject(subscriptionManager)
                    .frame(height: max(UIScreen.main.bounds.height * 0.86, 760))
                }
                .background(CoachiTheme.bg.ignoresSafeArea())
                .navigationTitle(isNorwegian ? "Administrer abonnement" : "Manage subscription")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button(isNorwegian ? "Tilbake" : "Back") {
                            showTimeLimitPaywall = false
                        }
                    }
                }
            }
        }
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
                if rowIdx > 0 { Divider().overlay(Color.white.opacity(0.10)) }
                HStack(spacing: 0) {
                    statCell(title: statRows[rowIdx][0].title, value: statRows[rowIdx][0].value)
                    if statRows[rowIdx].count > 1 {
                        Divider()
                            .overlay(Color.white.opacity(0.10))
                            .frame(width: 1)
                        statCell(title: statRows[rowIdx][1].title, value: statRows[rowIdx][1].value)
                    }
                }
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(Color.white.opacity(0.09))
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(0.06),
                                    Color.clear
                                ],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(Color.white.opacity(0.14), lineWidth: 1)
        )
    }

    private func statCell(title: String, value: String) -> some View {
        VStack(spacing: 5) {
            Text(value)
                .font(.system(size: 19, weight: .bold))
                .foregroundColor(Color.white.opacity(0.95))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.white.opacity(0.62))
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
    }

    private var liveCoachSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle()
                    .fill(liveVoiceIsAvailable ? CoachiTheme.accent : Color.white.opacity(0.46))
                    .frame(width: 8, height: 8)
                VStack(alignment: .leading, spacing: 3) {
                    Text(liveVoiceStatusText)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color.white.opacity(0.94))
                    Text(liveVoiceQuotaDetailText)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.white.opacity(0.74))
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }

            Text(
                isNorwegian
                    ? "Få en kort Coachi-samtale om akkurat denne økten."
                    : "Get a short Coachi follow-up about this exact workout."
            )
            .font(.system(size: 14, weight: .medium))
            .foregroundColor(Color.white.opacity(0.72))

            Button {
                onStartCoaching()
            } label: {
                HStack(spacing: 10) {
                    Image(systemName: liveVoiceIsAvailable ? "mic.fill" : "lock.fill")
                        .font(.system(size: 17, weight: .semibold))
                    Text(isNorwegian ? "Snakk med Coach" : "Talk to Coach")
                        .font(.system(size: 17, weight: .bold))
                }
                .frame(maxWidth: .infinity)
                .frame(height: 56)
            }
            .buttonStyle(
                SummarySurfaceButtonStyle(
                    variant: liveVoiceIsAvailable ? .coach : .glassOutline
                )
            )

            bottomButtons
                .padding(.top, 2)
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.white.opacity(0.08))
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                )
        )
    }

    // MARK: - Inline Coach Panel

    // Full-sheet voice coach — waveform dominant, minimal chrome
    private var fullScreenCoachPanel: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "waveform.path.ecg")
                    .font(.system(size: 11, weight: .bold))
                Text(isNorwegian ? "Coachi samtale" : "Coachi Conversation")
                    .font(.system(size: 11, weight: .bold))
                    .tracking(0.5)
            }
            .foregroundColor(CoachiTheme.primary)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                Capsule(style: .continuous)
                    .fill(CoachiTheme.primary.opacity(0.12))
            )
            .padding(.top, 18)

            // Compact workout context at top
            Text(compactStatsLine)
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .foregroundColor(CoachiTheme.textSecondary)
                .lineLimit(2)
                .minimumScaleFactor(0.7)
                .multilineTextAlignment(.center)
                .padding(.top, 14)
                .padding(.horizontal, 20)

            Spacer().frame(minHeight: 20)

            // Top 40% spacer — pushes waveform to lower-center
            Spacer()

            // Waveform — main focus, 2x scale, full width
            WaveformBarsView(service: liveCoachVM.service, isNorwegian: isNorwegian)
                .scaleEffect(x: 2.0, y: 2.0, anchor: .center)
                .frame(maxWidth: .infinity)
                .frame(height: 130)

            Spacer().frame(height: 28)

            toggleCoachingButton
                .padding(.horizontal, 20)

            Button {
                showTextCoach = true
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "keyboard")
                        .font(.system(size: 12, weight: .regular))
                    Text(isNorwegian ? "Skriv i stedet" : "Type instead")
                        .font(.system(size: 13, weight: .medium))
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 9)
                .foregroundColor(Color.white.opacity(0.82))
                .background(
                    Capsule(style: .continuous)
                        .fill(Color.white.opacity(0.10))
                        .overlay(
                            Capsule(style: .continuous)
                                .stroke(Color.white.opacity(0.16), lineWidth: 1)
                        )
                )
            }
            .buttonStyle(.plain)

            // Bottom spacer — less than top to keep waveform in lower-center
            Spacer().frame(minHeight: 16)

            VStack(spacing: 12) {
                bottomButtons
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .sheet(isPresented: $showTextCoach) {
            PostWorkoutTextCoachView(
                summaryContext: liveCoachVM.summaryContext,
                languageCode: liveCoachVM.languageCode,
                userName: liveCoachVM.userName,
                presentationMode: .compactComposer
            )
        }
        .background(summaryCardBackground)
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
                        .tint(isActive ? CoachiTheme.textPrimary.opacity(0.72) : Color.white.opacity(0.95))
                        .scaleEffect(0.85)
                }
                Text(isActive
                    ? (isNorwegian ? "Stopp" : "Stop")
                    : (isNorwegian ? "Start" : "Start"))
                    .font(.system(size: 17, weight: .bold))
            }
            .frame(maxWidth: .infinity)
            .frame(height: 52)
        }
        .buttonStyle(SummarySurfaceButtonStyle(variant: isActive ? .glassOutline : .coach))
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
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
            }
            .buttonStyle(SummarySurfaceButtonStyle(variant: .glass))

            Button {
                onShare()
            } label: {
                Text(isNorwegian ? "DEL" : "SHARE")
                    .font(.system(size: 14, weight: .medium))
                    .tracking(0.6)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
            }
            .buttonStyle(SummarySurfaceButtonStyle(variant: .glassOutline))
        }
        .padding(.top, 4)
    }
}

private enum SummarySurfaceButtonVariant: Equatable {
    case hero
    case coach
    case glass
    case glassOutline
    case primary
    case utility
    case outline
}

private struct SummarySurfaceButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    let variant: SummarySurfaceButtonVariant

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(foregroundColor)
            .background(buttonBackground(pressed: configuration.isPressed))
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .overlay(buttonBorder(pressed: configuration.isPressed))
            .shadow(
                color: shadowColor(pressed: configuration.isPressed),
                radius: configuration.isPressed ? 8 : shadowRadius,
                y: configuration.isPressed ? 3 : shadowYOffset
            )
            .scaleEffect(configuration.isPressed ? 0.985 : 1.0)
            .opacity(isEnabled ? 1.0 : 0.68)
            .animation(.easeOut(duration: 0.16), value: configuration.isPressed)
    }

    private var foregroundColor: Color {
        switch variant {
        case .hero, .primary:
            return Color.white.opacity(0.96)
        case .coach:
            return CoachiTheme.accent.opacity(0.98)
        case .glass, .glassOutline:
            return Color.white.opacity(0.92)
        case .utility, .outline:
            return CoachiTheme.textPrimary
        }
    }

    private var cornerRadius: CGFloat {
        switch variant {
        case .hero:
            return 14
        case .coach, .glass, .glassOutline, .primary, .utility, .outline:
            return 22
        }
    }

    private var borderWidth: CGFloat {
        switch variant {
        case .hero:
            return 1.35
        case .coach:
            return 1.25
        case .glass, .glassOutline:
            return 1
        case .outline:
            return 1.5
        case .primary, .utility:
            return 1
        }
    }

    private var shadowRadius: CGFloat {
        switch variant {
        case .hero:
            return 18
        case .coach:
            return 16
        case .glass, .glassOutline:
            return 8
        case .primary:
            return 14
        case .utility, .outline:
            return 10
        }
    }

    private var shadowYOffset: CGFloat {
        switch variant {
        case .hero:
            return 0
        case .coach, .glass, .glassOutline:
            return 4
        case .primary:
            return 6
        case .utility, .outline:
            return 4
        }
    }

    @ViewBuilder
    private func buttonBackground(pressed: Bool) -> some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(fillStyle(pressed: pressed))
            .overlay {
                if variant == .hero {
                    RoundedRectangle(cornerRadius: max(cornerRadius - 2, 0), style: .continuous)
                        .stroke(Color.white.opacity(pressed ? 0.04 : 0.10), lineWidth: 1)
                        .padding(2)
                }
            }
            .overlay(alignment: .top) {
                if variant == .hero {
                    RoundedRectangle(cornerRadius: max(cornerRadius - 4, 0), style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(0.18),
                                    Color.white.opacity(0.05),
                                    Color.clear
                                ],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .frame(height: 18)
                        .padding(.horizontal, 4)
                        .padding(.top, 3)
                }
            }
    }

    private func fillStyle(pressed: Bool) -> AnyShapeStyle {
        let pressedOpacity = pressed ? 0.88 : 1.0

        switch variant {
        case .hero:
            return AnyShapeStyle(
                LinearGradient(
                    colors: [
                        Color(hex: "313743").opacity(0.92 * pressedOpacity),
                        Color(hex: "1D222B").opacity(0.98 * pressedOpacity),
                        Color(hex: "12161E").opacity(0.98 * pressedOpacity)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        case .coach:
            return AnyShapeStyle(
                LinearGradient(
                    colors: [
                        Color.black.opacity(0.78 * pressedOpacity),
                        Color(hex: "2A2621").opacity(0.88 * pressedOpacity),
                        Color(hex: "151515").opacity(0.92 * pressedOpacity)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        case .glass:
            return AnyShapeStyle(
                LinearGradient(
                    colors: [
                        Color.white.opacity((isEnabled ? 0.14 : 0.08) * pressedOpacity),
                        Color.white.opacity((isEnabled ? 0.08 : 0.05) * pressedOpacity)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        case .glassOutline:
            return AnyShapeStyle(
                LinearGradient(
                    colors: [
                        Color.white.opacity((isEnabled ? 0.08 : 0.05) * pressedOpacity),
                        Color.clear
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        case .primary:
            return AnyShapeStyle(CoachiTheme.primaryGradient.opacity(isEnabled ? pressedOpacity : 0.55))
        case .utility:
            return AnyShapeStyle(CoachiTheme.surfaceElevated.opacity((isEnabled ? 0.98 : 0.78) * pressedOpacity))
        case .outline:
            return AnyShapeStyle(CoachiTheme.surface.opacity((isEnabled ? 0.70 : 0.55) * pressedOpacity))
        }
    }

    @ViewBuilder
    private func buttonBorder(pressed: Bool) -> some View {
        if variant == .hero {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(
                    LinearGradient(
                        colors: [
                            Color(hex: "67E8F9").opacity(pressed ? 0.48 : 0.86),
                            Color.white.opacity(pressed ? 0.12 : 0.24),
                            Color(hex: "67E8F9").opacity(pressed ? 0.48 : 0.86)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    lineWidth: borderWidth
                )
        } else if variant == .coach {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(
                    LinearGradient(
                        colors: [
                            CoachiTheme.accent.opacity(pressed ? 0.40 : 0.72),
                            Color.white.opacity(pressed ? 0.10 : 0.18),
                            CoachiTheme.accent.opacity(pressed ? 0.40 : 0.72)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    lineWidth: borderWidth
                )
        } else if variant == .glassOutline {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0.18),
                            CoachiTheme.accent.opacity(pressed ? 0.18 : 0.36)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    lineWidth: borderWidth
                )
        } else {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(borderColor(pressed: pressed), lineWidth: borderWidth)
        }
    }

    private func borderColor(pressed: Bool) -> Color {
        switch variant {
        case .hero:
            return Color(hex: "67E8F9").opacity(pressed ? 0.40 : 0.72)
        case .coach:
            return CoachiTheme.accent.opacity(pressed ? 0.34 : 0.62)
        case .glass:
            return Color.white.opacity(pressed ? 0.12 : 0.18)
        case .glassOutline:
            return CoachiTheme.accent.opacity(pressed ? 0.16 : 0.30)
        case .primary:
            return Color.white.opacity(pressed ? 0.10 : 0.14)
        case .utility:
            return CoachiTheme.borderSubtle.opacity(pressed ? 0.32 : 0.42)
        case .outline:
            return CoachiTheme.primary.opacity(pressed ? 0.26 : 0.38)
        }
    }

    private func shadowColor(pressed: Bool) -> Color {
        switch variant {
        case .hero:
            return Color(hex: "67E8F9").opacity(pressed ? 0.20 : 0.42)
        case .coach:
            return CoachiTheme.accent.opacity(pressed ? 0.10 : 0.22)
        case .glass, .glassOutline:
            return Color.black.opacity(pressed ? 0.06 : 0.14)
        case .primary:
            return CoachiTheme.primary.opacity(pressed ? 0.18 : 0.28)
        case .utility:
            return Color.black.opacity(pressed ? 0.05 : 0.08)
        case .outline:
            return Color.black.opacity(pressed ? 0.03 : 0.05)
        }
    }
}

private struct WorkoutShareDestinationsSheet: View {
    @Environment(\.dismiss) private var dismiss

    let title: String
    let languageCode: String
    let onInstagram: () -> Void
    let onSnapchat: () -> Void
    let onTikTok: () -> Void
    let onX: () -> Void
    let onCopyLink: () -> Void

    var body: some View {
        ZStack {
            Color.clear.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer(minLength: 0)

                VStack(alignment: .leading, spacing: 18) {
                    Text(title)
                        .font(.system(size: 21, weight: .semibold, design: .serif))
                        .foregroundStyle(Color.white.opacity(0.94))

                    VStack(spacing: 12) {
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
                    }
                    .padding(16)
                    .background(
                        RoundedRectangle(cornerRadius: 24, style: .continuous)
                            .fill(Color.white.opacity(0.08))
                            .overlay(
                                RoundedRectangle(cornerRadius: 24, style: .continuous)
                                    .stroke(Color.white.opacity(0.12), lineWidth: 1)
                            )
                    )

                    Button(languageCode == "no" ? "Lukk" : "Close") {
                        dismiss()
                    }
                    .font(.system(size: 15, weight: .semibold))
                    .frame(maxWidth: .infinity)
                    .frame(height: 46)
                    .buttonStyle(SummarySurfaceButtonStyle(variant: .glass))
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 20)
                .background(WorkoutModalCardBackground())
            }
            .frame(maxWidth: 392, maxHeight: .infinity, alignment: .bottom)
            .padding(.horizontal, 16)
            .padding(.top, 18)
            .padding(.bottom, 16)
        }
    }

    @ViewBuilder
    private func shareButton(label: String, accent: Color, icon: ShareDestinationIcon, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(accent.opacity(icon == .snapchat ? 0.92 : 0.24))
                        .frame(width: 52, height: 52)
                    Circle()
                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                        .frame(width: 52, height: 52)
                    shareIcon(for: icon)
                }
                Text(label)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.92))
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .minimumScaleFactor(0.8)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 102)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Color.white.opacity(0.06))
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(Color.white.opacity(0.10), lineWidth: 1)
                    )
            )
            .contentShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
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

private struct WorkoutModalCardBackground: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 30, style: .continuous)
            .fill(.ultraThinMaterial)
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(hex: "73523E").opacity(0.16),
                                Color(hex: "5B4769").opacity(0.18),
                                Color.black.opacity(0.12)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(Color.white.opacity(0.16), lineWidth: 1)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(CoachiTheme.accent.opacity(0.28), lineWidth: 1)
                    .padding(1)
            )
            .shadow(color: Color.black.opacity(0.22), radius: 26, y: 14)
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
