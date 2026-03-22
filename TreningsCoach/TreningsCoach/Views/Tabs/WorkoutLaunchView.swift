//
//  WorkoutLaunchView.swift
//  TreningsCoach
//
//  Pre-workout setup: persona selector, warmup time circular dial, GO button
//

import SwiftUI

struct WorkoutLaunchView: View {
    @EnvironmentObject private var subscriptionManager: SubscriptionManager

    private enum SetupStage {
        case easyWarmup
        case easyDuration
        case intervalWarmup
        case intervalSets
        case intervalDuration
        case intervalBreak
    }

    @ObservedObject var viewModel: WorkoutViewModel
    var showsAnimatedBackground: Bool = true
    @State private var appeared = false
    @State private var launchStep = 1
    @State private var showAdvancedOptions = false
    @State private var showPerformanceModePaywall = false
    @State private var setupStage: SetupStage = .easyWarmup
    @State private var easyRunConfigured = false
    @State private var intervalsConfigured = false

    private var setupDetailsComplete: Bool {
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            return viewModel.selectedEasyRunSessionMode == .freeRun || easyRunConfigured
        case .intervals:
            return intervalsConfigured
        case .standard:
            return true
        }
    }

    private var canStartWorkout: Bool {
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            return setupDetailsComplete
        case .intervals:
            return setupDetailsComplete
        case .standard:
            return true
        }
    }

    private var showsPostSetupSections: Bool {
        launchStep == 2 && setupDetailsComplete
    }

    private var showsSetupSelectionSection: Bool {
        launchStep == 2 && !showsPostSetupSections
    }

    private var intervalTotalSeconds: Int {
        let sets = max(1, viewModel.selectedIntervalSets)
        let work = max(0, viewModel.selectedIntervalWorkMinutes)
        let pause = max(0, min(120, viewModel.selectedIntervalBreakSeconds))
        return (sets * work * 60) + (max(0, sets - 1) * pause)
    }

    private var intervalSessionTotalSeconds: Int {
        (max(0, viewModel.selectedWarmupMinutes) * 60) + intervalTotalSeconds
    }

    private var easyRunSessionTotalSeconds: Int {
        (max(0, viewModel.selectedWarmupMinutes) + max(0, viewModel.selectedEasyRunMinutes)) * 60
    }

    private var intervalTotalDurationText: String {
        let totalMinutes = intervalTotalSeconds / 60
        let totalSeconds = intervalTotalSeconds % 60
        if totalSeconds == 0 {
            return L10n.current == .no
                ? "Total intervalltid: \(totalMinutes) min"
                : "Total interval time: \(totalMinutes) min"
        }
        return L10n.current == .no
            ? "Total intervalltid: \(totalMinutes) min \(totalSeconds) sek"
            : "Total interval time: \(totalMinutes) min \(totalSeconds) sec"
    }

    private var setupCompletionDurationText: String? {
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            guard viewModel.selectedEasyRunSessionMode != .freeRun else { return nil }
            return totalDurationText(for: easyRunSessionTotalSeconds)
        case .intervals:
            return totalDurationText(for: intervalSessionTotalSeconds)
        case .standard:
            return nil
        }
    }

    private var launchSectionVerticalPadding: CGFloat {
        showsSetupSelectionSection ? 18 : 14
    }

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            if showsAnimatedBackground {
                ParticleBackgroundView(particleCount: 30)
            }

            ScrollView(showsIndicators: false) {
                VStack(spacing: 18) {
                    HStack {
                        HStack(spacing: 6) {
                            CoachiLogoView(size: 24)
                            Text(AppConfig.appName).font(.system(size: 17, weight: .semibold)).foregroundColor(CoachiTheme.textSecondary)
                        }
                        Spacer()
                    }
                    .padding(.top, 8)

                    if launchStep == 1 {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("What are you doing today?")
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(CoachiTheme.textPrimary)
                            Text("Choose your session first.")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)

                        HStack(spacing: 10) {
                            launchCard(
                                title: "Easy Run",
                                subtitle: "Stay easy. Build endurance.",
                                selected: viewModel.selectedWorkoutMode == .easyRun
                            ) {
                                viewModel.selectedWorkoutMode = .easyRun
                                resetSetupFlowForSelectedMode()
                            }
                            launchCard(
                                title: "Intervals",
                                subtitle: "Fast reps + guided recovery.",
                                selected: viewModel.selectedWorkoutMode == .intervals
                            ) {
                                viewModel.selectedWorkoutMode = .intervals
                                resetSetupFlowForSelectedMode()
                            }
                        }
                        launchComingSoonCard(
                            title: "Strength",
                            subtitle: "Coming soon."
                        )

                        Button {
                            if viewModel.selectedWorkoutMode == .easyRun {
                                viewModel.selectedEasyRunSessionMode = .timed
                            }
                            resetSetupFlowForSelectedMode()
                            withAnimation(.spring(response: 0.34, dampingFraction: 0.9)) {
                                launchStep = 2
                            }
                        } label: {
                            HStack {
                                Text("Next")
                                    .font(.system(size: 17, weight: .bold))
                                Spacer()
                                Image(systemName: "arrow.right")
                                    .font(.system(size: 14, weight: .bold))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 18)
                            .frame(height: 56)
                            .background(CoachiTheme.primaryGradient)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                            .shadow(color: CoachiTheme.primary.opacity(0.3), radius: 12, y: 4)
                        }
                        .buttonStyle(.plain)
                        .padding(.top, 4)
                    } else {
                        let canStartAction = canStartWorkout &&
                            !viewModel.isWaitingForWatchStart &&
                            viewModel.canInitiateWorkoutStart

                        VStack(alignment: .leading, spacing: 6) {
                            Text(showsPostSetupSections ? L10n.workoutIntensityPrompt : "Quick setup")
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(CoachiTheme.textPrimary)
                            if !showsPostSetupSections {
                                Text("Session details, wheels, and coaching options.")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)

                        if showsSetupSelectionSection {
                            launchSection(title: stepATitle, subtitle: stepASubtitle) {
                                if viewModel.selectedWorkoutMode == .easyRun {
                                    easyRunSetupContent
                                } else {
                                    intervalsSetupContent
                                }
                            }
                        }

                        if showsPostSetupSections {
                            launchSection(title: "", subtitle: "") {
                                intensitySelectionSection
                            }

                            watchStatusSection

                            DisclosureGroup(
                                isExpanded: $showAdvancedOptions,
                                content: {
                                    VStack(spacing: 14) {
                                        Toggle(isOn: $viewModel.useBreathingMicCues) {
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(L10n.breathAnalysisTitle)
                                                    .font(.system(size: 13, weight: .semibold))
                                                    .foregroundColor(CoachiTheme.textPrimary)
                                                Text(L10n.breathAnalysisSubtitle)
                                                    .font(.system(size: 12, weight: .medium))
                                                    .foregroundColor(CoachiTheme.textSecondary)
                                                    .fixedSize(horizontal: false, vertical: true)
                                            }
                                        }
                                        .tint(CoachiTheme.primary)

                                        VStack(spacing: 12) {
                                            Text(L10n.selectCoach.uppercased())
                                                .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                                                .tracking(1)
                                            HStack(spacing: 12) {
                                                ForEach(CoachPersonality.allCases) { persona in
                                                    PersonaChipView(persona: persona, isSelected: viewModel.activePersonality == persona) {
                                                        guard !(persona == .toxicMode && !subscriptionManager.hasPremiumAccess) else {
                                                            showPerformanceModePaywall = true
                                                            return
                                                        }
                                                        withAnimation(AppConfig.Anim.buttonSpring) {
                                                            viewModel.selectPersonality(persona)
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    .padding(.top, 8)
                                },
                                label: {
                                    Text("Advanced options")
                                        .font(.system(size: 13, weight: .semibold))
                                        .foregroundColor(CoachiTheme.textSecondary)
                                }
                            )
                            .padding(14)
                            .background(CoachiTheme.surface.opacity(0.9))
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }

                        HStack(spacing: 10) {
                            Button {
                                handleBottomBackAction()
                            } label: {
                                Text("Back")
                                    .font(.system(size: 16, weight: .semibold))
                                    .foregroundColor(CoachiTheme.textSecondary)
                                    .frame(maxWidth: .infinity, minHeight: 52)
                                    .background(CoachiTheme.surface)
                                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            }
                            .buttonStyle(.plain)

                            Button {
                                if viewModel.selectedEasyRunSessionMode != .freeRun {
                                    UserDefaults.standard.set(viewModel.selectedWarmupMinutes, forKey: "last_warmup_minutes")
                                }
                                withAnimation(AppConfig.Anim.transitionSpring) { viewModel.startWorkout() }
                            } label: {
                                Text(viewModel.launchStartButtonTitle)
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity, minHeight: 52)
                                    .background(
                                        Group {
                                            if canStartAction {
                                                CoachiTheme.primaryGradient
                                            } else {
                                                LinearGradient(
                                                    colors: [CoachiTheme.textTertiary.opacity(0.55), CoachiTheme.textTertiary.opacity(0.7)],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                )
                                            }
                                        }
                                    )
                                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                                    .shadow(
                                        color: canStartAction
                                            ? CoachiTheme.primary.opacity(0.28)
                                            : .clear,
                                        radius: 10,
                                        y: 3
                                    )
                            }
                            .disabled(!canStartAction)
                            .buttonStyle(.plain)
                        }
                        .padding(.top, 4)

                        if !viewModel.launchStartSubtext.isEmpty {
                            Text(viewModel.launchStartSubtext)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.top, 4)
                        }

                        if let authHelper = viewModel.launchAuthRequirementText {
                            Text(authHelper)
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(CoachiTheme.warning)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.top, 2)
                        }

                        if let helper = viewModel.watchReachabilityHelperText {
                            Text(helper)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.top, 2)
                        }

                        if let watchStatus = viewModel.watchStartStatusLine {
                            Text(watchStatus)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.top, 6)
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 92)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 12)
            }
        }
        .onAppear {
            // Restore last session warmup time
            if viewModel.selectedEasyRunSessionMode != .freeRun,
               let saved = UserDefaults.standard.object(forKey: "last_warmup_minutes") as? Int {
                viewModel.selectedWarmupMinutes = saved
            }
            launchStep = 1
            resetSetupFlowForSelectedMode()
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) { appeared = true }
        }
        .sheet(isPresented: $showPerformanceModePaywall) {
            PaywallView(context: .general)
                .environmentObject(subscriptionManager)
        }
    }

    @ViewBuilder
    private var intensitySelectionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let setupCompletionDurationText {
                Text(setupCompletionDurationText)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textSecondary)
            }

            VStack(spacing: 10) {
                intensityOptionCard(
                    style: .easy,
                    title: L10n.workoutIntensityEasyDetail
                )
                intensityOptionCard(
                    style: .medium,
                    title: L10n.workoutIntensityModerateDetail
                )
                intensityOptionCard(
                    style: .hard,
                    title: L10n.workoutIntensityHardDetail
                )
            }
        }
    }

    @ViewBuilder
    private var watchStatusSection: some View {
        let connected = viewModel.watchCapabilityState == .watchReady
        let statusColor = connected ? Color.green : CoachiTheme.warning
        let statusTitle = connected
            ? (L10n.current == .no ? "Tilkoblet" : "Connected")
            : (L10n.current == .no ? "Ikke tilkoblet" : "Not connected")
        let statusDetail = watchStatusDetailText(connected: connected)

        launchSection(title: "", subtitle: "") {
            HStack(spacing: 14) {
                ZStack {
                    Circle()
                        .fill(statusColor.opacity(0.14))
                        .frame(width: 44, height: 44)
                    Image(systemName: "applewatch.side.right")
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(statusColor)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(statusTitle)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(CoachiTheme.textPrimary)
                    Text(statusDetail)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }

                Spacer()

                Circle()
                    .fill(statusColor)
                    .frame(width: 12, height: 12)
            }
        }
    }

    @ViewBuilder
    private func launchSection<Content: View>(title: String, subtitle: String, @ViewBuilder content: () -> Content) -> some View {
        let isCurrentSetupAction = showsSetupSelectionSection && !title.isEmpty && subtitle.isEmpty
        VStack(alignment: .leading, spacing: 10) {
            if !title.isEmpty || !subtitle.isEmpty {
                VStack(alignment: isCurrentSetupAction ? .center : .leading, spacing: 4) {
                    if !title.isEmpty {
                        Text(title)
                            .font(.system(size: isCurrentSetupAction ? 30 : 19, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .multilineTextAlignment(isCurrentSetupAction ? .center : .leading)
                            .frame(maxWidth: .infinity, alignment: isCurrentSetupAction ? .center : .leading)
                    }
                    if !subtitle.isEmpty {
                        Text(subtitle)
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: isCurrentSetupAction ? .center : .leading)
            }
            content()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, launchSectionVerticalPadding)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CoachiTheme.surface.opacity(0.9))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    @ViewBuilder
    private func launchComingSoonCard(title: String, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 15, weight: .bold))
                .foregroundColor(CoachiTheme.textSecondary)
            Text(subtitle)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(CoachiTheme.textTertiary)
        }
        .frame(maxWidth: .infinity, minHeight: 70, alignment: .leading)
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(CoachiTheme.surface.opacity(0.7))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(CoachiTheme.textTertiary.opacity(0.2), lineWidth: 1)
        )
    }

    @ViewBuilder
    private func launchCard(title: String, subtitle: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(selected ? .white : CoachiTheme.textPrimary)
                Text(subtitle)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(selected ? .white.opacity(0.9) : CoachiTheme.textSecondary)
                    .multilineTextAlignment(.leading)
            }
            .frame(maxWidth: .infinity, minHeight: 82, alignment: .leading)
            .padding(12)
            .background(
                Group {
                    if selected {
                        RoundedRectangle(cornerRadius: 14, style: .continuous).fill(CoachiTheme.primaryGradient)
                    } else {
                        RoundedRectangle(cornerRadius: 14, style: .continuous).fill(CoachiTheme.surface)
                    }
                }
            )
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func intensityOptionCard(style: CoachingStyle, title: String) -> some View {
        let selected = viewModel.coachingStyle == style
        Button {
            viewModel.coachingStyle = style
        } label: {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(selected ? .white : CoachiTheme.textPrimary)
                        .multilineTextAlignment(.leading)
                }
                Spacer()
                Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(selected ? .white : CoachiTheme.textTertiary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)
            .background {
                if selected {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(CoachiTheme.primaryGradient)
                } else {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(CoachiTheme.surface)
                }
            }
        }
        .buttonStyle(.plain)
    }

    private func watchStatusDetailText(connected: Bool) -> String {
        guard connected else {
            return L10n.current == .no ? "Live puls ikke tilgjengelig" : "Live heart rate unavailable"
        }

        if viewModel.watchBPMDisplayText != "0 BPM" {
            return viewModel.watchBPMDisplayText
        }

        return L10n.current == .no ? "Venter på puls" : "Awaiting heart rate"
    }

    private var stepASubtitle: String {
        ""
    }

    private var stepATitle: String {
        switch setupStage {
        case .easyWarmup, .intervalWarmup:
            return L10n.current == .no ? "Oppvarming" : "Warm up"
        case .easyDuration:
            return L10n.current == .no ? "Varighet" : "Duration"
        case .intervalSets:
            return L10n.current == .no ? "Drag" : "Sets"
        case .intervalDuration:
            return L10n.current == .no ? "Varighet" : "Duration"
        case .intervalBreak:
            return L10n.current == .no ? "Pause" : "Rest"
        }
    }

    @ViewBuilder
    private var easyRunSetupContent: some View {
        VStack(spacing: 14) {
            easyRunModeToggle

            if viewModel.selectedEasyRunSessionMode != .freeRun, setupStage == .easyWarmup {
                VStack(spacing: 14) {
                    CircularDialPicker(
                        selectedValue: $viewModel.selectedWarmupMinutes,
                        valueRange: 0...40,
                        unitLabel: L10n.minutesUpper,
                        zeroLabel: L10n.skipWarmup
                    )
                    stageCheckButton(title: L10n.current == .no ? "Fortsett" : "Continue") {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .easyDuration
                            easyRunConfigured = false
                        }
                    }
                }
            } else if viewModel.selectedEasyRunSessionMode != .freeRun {
                VStack(spacing: 14) {
                    CircularDialPicker(
                        selectedValue: $viewModel.selectedEasyRunMinutes,
                        valueRange: 1...120,
                        unitLabel: L10n.minutesUpper,
                        zeroLabel: nil
                    )
                    HStack(spacing: 10) {
                        Button {
                            withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                                setupStage = .easyWarmup
                                easyRunConfigured = false
                            }
                        } label: {
                            Text(L10n.current == .no ? "Tilbake" : "Back")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity, minHeight: 42)
                                .background(CoachiTheme.surface)
                                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        }
                        .buttonStyle(.plain)

                        stageCheckButton(title: L10n.current == .no ? "Bekreft" : "Confirm") {
                            easyRunConfigured = true
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var intervalsSetupContent: some View {
        if setupStage == .intervalWarmup {
            VStack(spacing: 14) {
                CircularDialPicker(
                    selectedValue: $viewModel.selectedWarmupMinutes,
                    valueRange: 0...40,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: L10n.skipWarmup
                )
                stageCheckButton(title: L10n.current == .no ? "Fortsett" : "Continue") {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                        setupStage = .intervalSets
                        intervalsConfigured = false
                    }
                }
            }
        } else if setupStage == .intervalSets {
            VStack(spacing: 12) {
                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalSets,
                    valueRange: 2...10,
                    unitLabel: L10n.current == .no ? "DRAG" : "DRAG",
                    zeroLabel: nil,
                    dragSensitivity: 1.55
                )

                HStack(spacing: 10) {
                    Button {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalWarmup
                            intervalsConfigured = false
                        }
                    } label: {
                        Text(L10n.current == .no ? "Tilbake" : "Back")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .frame(maxWidth: .infinity, minHeight: 42)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                    .buttonStyle(.plain)

                    stageCheckButton(title: L10n.current == .no ? "Fortsett" : "Continue") {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalDuration
                            intervalsConfigured = false
                        }
                    }
                }
            }
        } else if setupStage == .intervalDuration {
            VStack(spacing: 12) {
                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalWorkMinutes,
                    valueRange: 1...20,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: nil,
                    dragSensitivity: 1.45
                )

                HStack(spacing: 10) {
                    Button {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalSets
                            intervalsConfigured = false
                        }
                    } label: {
                        Text(L10n.current == .no ? "Tilbake" : "Back")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .frame(maxWidth: .infinity, minHeight: 42)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                    .buttonStyle(.plain)

                    stageCheckButton(title: L10n.current == .no ? "Fortsett" : "Continue") {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalBreak
                            intervalsConfigured = false
                        }
                    }
                }
            }
        } else {
            VStack(spacing: 12) {
                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalBreakSeconds,
                    valueRange: 0...120,
                    stepSize: 15,
                    unitLabel: L10n.current == .no ? "SEK" : "SEC",
                    zeroLabel: nil,
                    dragSensitivity: 1.35,
                    valueLabelFormatter: intervalBreakDialLabel
                )

                Text(intervalTotalDurationText)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(CoachiTheme.textPrimary)

                HStack(spacing: 10) {
                    Button {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalDuration
                            intervalsConfigured = false
                        }
                    } label: {
                        Text(L10n.current == .no ? "Tilbake" : "Back")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .frame(maxWidth: .infinity, minHeight: 42)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                    .buttonStyle(.plain)

                    stageCheckButton(title: L10n.current == .no ? "Bekreft" : "Confirm") {
                        intervalsConfigured = true
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func stageCheckButton(title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 15, weight: .bold))
                Text(title)
                    .font(.system(size: 14, weight: .bold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity, minHeight: 42)
            .background(CoachiTheme.primaryGradient)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func totalDurationText(for totalSeconds: Int) -> String {
        let clamped = max(0, totalSeconds)
        let totalMinutes = clamped / 60
        let remainingSeconds = clamped % 60
        if remainingSeconds == 0 {
            return L10n.current == .no
                ? "Total varighet: \(totalMinutes) min"
                : "Total duration: \(totalMinutes) min"
        }
        return L10n.current == .no
            ? "Total varighet: \(totalMinutes) min \(remainingSeconds) sek"
            : "Total duration: \(totalMinutes) min \(remainingSeconds) sec"
    }

    private func formattedIntervalBreak(_ seconds: Int) -> String {
        let clamped = max(0, min(120, seconds))
        if clamped == 0 {
            return L10n.current == .no ? "Ingen pause" : "No break"
        }
        return L10n.current == .no ? "\(clamped) sek" : "\(clamped) sec"
    }

    private func intervalBreakDialLabel(_ seconds: Int) -> (String, String) {
        let clamped = max(0, min(120, seconds))
        if clamped == 0 {
            return (L10n.current == .no ? "INGEN" : "NONE", "")
        }
        if clamped > 60 {
            return (formattedBreakClockValue(for: clamped), L10n.minutesUpper)
        }
        return ("\(clamped)", L10n.current == .no ? "SEK" : "SEC")
    }

    private func formattedBreakClockValue(for seconds: Int) -> String {
        let clamped = max(0, min(120, seconds))
        let minutes = clamped / 60
        let remainingSeconds = clamped % 60
        return String(format: "%d:%02d", minutes, remainingSeconds)
    }

    private func handleBottomBackAction() {
        withAnimation(.spring(response: 0.34, dampingFraction: 0.9)) {
            guard showsPostSetupSections else {
                launchStep = 1
                return
            }

            showAdvancedOptions = false
            switch viewModel.selectedWorkoutMode {
            case .easyRun:
                if viewModel.selectedEasyRunSessionMode == .freeRun {
                    launchStep = 1
                } else {
                    setupStage = .easyDuration
                    easyRunConfigured = false
                }
            case .intervals:
                setupStage = .intervalBreak
                intervalsConfigured = false
            case .standard:
                launchStep = 1
            }
        }
    }

    private func resetSetupFlowForSelectedMode() {
        showAdvancedOptions = false
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            if viewModel.selectedEasyRunSessionMode == .freeRun {
                setupStage = .easyDuration
                easyRunConfigured = true
            } else {
                setupStage = .easyWarmup
                easyRunConfigured = false
            }
            intervalsConfigured = false
        case .intervals:
            setupStage = .intervalWarmup
            easyRunConfigured = false
            intervalsConfigured = false
        case .standard:
            setupStage = .easyWarmup
            easyRunConfigured = true
            intervalsConfigured = true
        }
    }

    private var easyRunModeToggle: some View {
        HStack(spacing: 0) {
            ForEach(EasyRunSessionMode.allCases) { mode in
                let isSelected = viewModel.selectedEasyRunSessionMode == mode
                Button {
                    guard viewModel.selectedEasyRunSessionMode != mode else { return }
                    viewModel.selectedEasyRunSessionMode = mode
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                        if mode == .freeRun {
                            setupStage = .easyDuration
                            easyRunConfigured = true
                        } else {
                            setupStage = .easyWarmup
                            easyRunConfigured = false
                        }
                    }
                } label: {
                    Text(mode.displayName)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(isSelected ? .white : CoachiTheme.textSecondary)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .background(
                            Group {
                                if isSelected {
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .fill(CoachiTheme.primaryGradient)
                                } else {
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .fill(Color.clear)
                                }
                            }
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(CoachiTheme.bgDeep.opacity(0.55))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

// MARK: - Circular Dial Picker

struct CircularDialPicker: View {
    @Binding var selectedValue: Int

    var valueRange: ClosedRange<Int> = 0...40
    var stepSize: Int = 1
    var unitLabel: String = L10n.minutesUpper
    var zeroLabel: String? = L10n.skipWarmup
    var dialSize: CGFloat = 236
    var trackWidth: CGFloat = 18
    var dragSensitivity: Double = 1.0
    var valueLabelFormatter: ((Int) -> (String, String))? = nil

    // Internal drag state (continuous, not snapped)
    @State private var currentAngle: Double = 0 // 0-360 degrees, 0 = 12 o'clock
    @State private var isDragging = false
    @State private var previewValue: Int?
    @State private var lastHapticStepValue: Int?
    private let hapticGenerator = UIImpactFeedbackGenerator(style: .light)

    private var minValue: Int { valueRange.lowerBound }
    private var maxValue: Int { valueRange.upperBound }
    private var valueSpan: CGFloat { CGFloat(max(1, maxValue - minValue)) }
    private var safeStepSize: Int { max(1, stepSize) }
    private var containerSize: CGFloat { dialSize + max(28, trackWidth + 12) }

    private var safeAngle: Double {
        guard currentAngle.isFinite else { return 0 }
        return max(0, min(360, currentAngle))
    }

    private var committedValue: Int {
        max(minValue, min(maxValue, selectedValue))
    }

    private var hasActivePreview: Bool {
        previewValue != nil
    }

    private var displayValue: Int {
        if let previewValue {
            return previewValue
        }
        return committedValue
    }

    private var displayProgress: Double {
        if isDragging || hasActivePreview {
            return min(1.0, max(0.0, safeAngle / 360.0))
        }
        return normalizedProgress(for: displayValue)
    }

    private var displayValueText: String {
        if let valueLabelFormatter {
            return valueLabelFormatter(displayValue).0
        }
        return "\(displayValue)"
    }

    private var valueUnitText: String {
        if let valueLabelFormatter {
            return valueLabelFormatter(displayValue).1
        }
        if displayValue == 0, let zeroLabel {
            return zeroLabel
        }
        return unitLabel
    }

    private var indicatorRadius: CGFloat {
        (dialSize / 2) + 6
    }

    private var indicatorSize: CGFloat {
        max(trackWidth + 8, 22)
    }

    private var indicatorPosition: CGSize {
        let theta = (displayProgress * 2.0 * .pi)
        return CGSize(
            width: CGFloat(sin(theta)) * indicatorRadius,
            height: CGFloat(-cos(theta)) * indicatorRadius
        )
    }

    var body: some View {
        ZStack {
            // Outer dark background circle
            Circle()
                .fill(CoachiTheme.bgDeep)
                .frame(width: dialSize + 24, height: dialSize + 24)

            // Track (dark ring)
            Circle()
                .stroke(CoachiTheme.surface, lineWidth: trackWidth)
                .frame(width: dialSize, height: dialSize)

            // Filled arc (purple → magenta gradient)
            if displayProgress > 0.001 {
                Circle()
                    .trim(from: 0, to: CGFloat(min(displayProgress, 1.0)))
                    .stroke(CoachiTheme.dialMagenta, style: StrokeStyle(lineWidth: trackWidth, lineCap: .round))
                    .frame(width: dialSize, height: dialSize)
                    .rotationEffect(.degrees(-90))
                    .shadow(color: CoachiTheme.dialMagenta.opacity(isDragging ? 0.42 : 0.18), radius: isDragging ? 10 : 4)
            }

            if displayProgress > 0.03 {
                Circle()
                    .trim(from: CGFloat(max(0, displayProgress - 0.065)), to: CGFloat(min(displayProgress, 1.0)))
                    .stroke(CoachiTheme.dialMagenta.opacity(isDragging ? 0.42 : 0.2), style: StrokeStyle(lineWidth: trackWidth + 6, lineCap: .round))
                    .frame(width: dialSize, height: dialSize)
                    .rotationEffect(.degrees(-90))
                    .blur(radius: isDragging ? 5 : 3)
            }

            Circle()
                .fill(Color.white)
                .frame(width: indicatorSize, height: indicatorSize)
                .shadow(color: Color.white.opacity(isDragging ? 0.46 : 0.28), radius: isDragging ? 10 : 5)
                .offset(x: indicatorPosition.width, y: indicatorPosition.height)

            // Center content
            VStack(spacing: 2) {
                Text(displayValueText)
                    .font(.system(size: max(36, dialSize * 0.25), weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .contentTransition(.numericText())
                    .animation(.easeInOut(duration: 0.15), value: displayValue)

                Text(valueUnitText)
                    .font(.system(size: max(11, dialSize * 0.065), weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(2)
            }
        }
        .frame(width: containerSize, height: containerSize)
        .contentShape(Circle()) // Make entire dial tappable
        .gesture(dialDragGesture)
        .onAppear {
            previewValue = nil
            syncAngleFromMinutes()
        }
        .onChange(of: selectedValue) { _, _ in
            if !isDragging {
                previewValue = nil
                syncAngleFromMinutes()
            }
        }
    }

    // MARK: - Gesture

    private var dialDragGesture: some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { value in
                if !isDragging {
                    isDragging = true
                    hapticGenerator.prepare()
                    lastHapticStepValue = committedValue
                }
                updateAngle(from: value.location, in: containerSize)
            }
            .onEnded { _ in
                isDragging = false
                snapToNearestStepAndCommit()
            }
    }

    private func updateAngle(from point: CGPoint, in size: CGFloat) {
        let center = CGPoint(x: size / 2, y: size / 2)
        let dx = point.x - center.x
        let dy = point.y - center.y

        // Dead-zone: ignore touches near center where angle is unreliable
        let distance = sqrt(dx * dx + dy * dy)
        guard distance > max(24, dialSize * 0.16) else { return }

        // atan2 gives angle from positive x-axis; convert to clockwise from 12 o'clock
        var angle = atan2(dx, -dy) * 180 / .pi // degrees, 0 = 12 o'clock, clockwise positive
        if angle < 0 { angle += 360 }

        currentAngle = angle
        let newPreview = snappedValue(forVisualAngle: angle)
        previewValue = newPreview

        if lastHapticStepValue != newPreview {
            if lastHapticStepValue != nil {
                hapticGenerator.impactOccurred(intensity: 0.35)
            }
            lastHapticStepValue = newPreview
        }
    }

    private func normalizedProgress(for value: Int) -> Double {
        let clamped = max(minValue, min(maxValue, value))
        let span = max(1, maxValue - minValue)
        return Double(clamped - minValue) / Double(span)
    }

    private func rawValue(forVisualAngle angle: Double) -> Double {
        let normalized = min(1.0, max(0.0, angle / 360.0))
        return Double(minValue) + (normalized * Double(valueSpan))
    }

    private func snappedValue(forRawValue rawValue: Double) -> Int {
        let clamped = max(Double(minValue), min(Double(maxValue), rawValue))
        let snappedOffset = ((clamped - Double(minValue)) / Double(safeStepSize)).rounded() * Double(safeStepSize)
        let snapped = Double(minValue) + snappedOffset
        let rounded = Int(snapped.rounded())
        return max(minValue, min(maxValue, rounded))
    }

    private func snappedValue(forVisualAngle angle: Double) -> Int {
        snappedValue(forRawValue: rawValue(forVisualAngle: angle))
    }

    private func snapToNearestStepAndCommit() {
        let snapped = snappedValue(forVisualAngle: safeAngle)
        lastHapticStepValue = nil
        withAnimation(.spring(response: 0.22, dampingFraction: 0.82)) {
            selectedValue = snapped
            currentAngle = normalizedProgress(for: snapped) * 360.0
        }
    }

    private func syncAngleFromMinutes() {
        previewValue = nil
        let normalized = normalizedProgress(for: committedValue)
        let nextAngle = normalized * 360.0
        currentAngle = nextAngle.isFinite ? nextAngle : 0
    }
}
