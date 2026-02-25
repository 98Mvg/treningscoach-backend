//
//  WorkoutLaunchView.swift
//  TreningsCoach
//
//  Pre-workout setup: persona selector, warmup time circular dial, GO button
//

import SwiftUI

struct WorkoutLaunchView: View {
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
    @State private var setupStage: SetupStage = .easyWarmup
    @State private var easyRunConfigured = false
    @State private var intervalsConfigured = false

    private var canStartWorkout: Bool {
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            return setupStage == .easyDuration && easyRunConfigured
        case .intervals:
            return setupStage == .intervalBreak && intervalsConfigured
        case .standard:
            return true
        }
    }

    private var intervalTotalMinutes: Int {
        let sets = max(1, viewModel.selectedIntervalSets)
        let work = max(0, viewModel.selectedIntervalWorkMinutes)
        let pause = max(0, viewModel.selectedIntervalBreakMinutes)
        return (sets * work) + (max(0, sets - 1) * pause)
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
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Quick setup")
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(CoachiTheme.textPrimary)
                            Text("Session details, wheels, and coaching options.")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)

                        launchSection(title: "Step A", subtitle: stepASubtitle) {
                            if viewModel.selectedWorkoutMode == .easyRun {
                                easyRunSetupContent
                            } else {
                                intervalsSetupContent
                            }
                        }

                        launchSection(title: "Step B", subtitle: "Input sources") {
                            HStack(spacing: 8) {
                                Circle()
                                    .fill(viewModel.watchConnected ? CoachiTheme.success : CoachiTheme.textTertiary)
                                    .frame(width: 8, height: 8)
                                Text("Apple Watch")
                                    .font(.system(size: 13, weight: .semibold))
                                    .foregroundColor(CoachiTheme.textSecondary)
                                Spacer()
                                if viewModel.watchConnected {
                                    Text(viewModel.hrSignalQuality == "good" ? "HR good" : "HR limited")
                                        .font(.system(size: 12, weight: .semibold))
                                        .foregroundColor(viewModel.hrSignalQuality == "good" ? CoachiTheme.success : CoachiTheme.textTertiary)
                                } else {
                                    Text(L10n.notConnected)
                                        .font(.system(size: 12, weight: .semibold))
                                        .foregroundColor(CoachiTheme.textTertiary)
                                }
                            }
                            Toggle(isOn: $viewModel.useBreathingMicCues) {
                                Text("Use breathing mic cues")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                            }
                            .tint(CoachiTheme.primary)
                        }

                        DisclosureGroup(
                            isExpanded: $showAdvancedOptions,
                            content: {
                                VStack(spacing: 14) {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("COACHING STYLE")
                                            .font(.system(size: 13, weight: .semibold))
                                            .foregroundColor(CoachiTheme.textTertiary)
                                            .tracking(1)
                                        HStack(spacing: 8) {
                                            styleChip(.minimal)
                                            styleChip(.normal)
                                            styleChip(.motivational)
                                        }
                                    }

                                    VStack(spacing: 12) {
                                        Text(L10n.selectCoach.uppercased())
                                            .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                                            .tracking(1)
                                        HStack(spacing: 12) {
                                            ForEach(CoachPersonality.allCases) { persona in
                                                PersonaChipView(persona: persona, isSelected: viewModel.activePersonality == persona) {
                                                    withAnimation(AppConfig.Anim.buttonSpring) { viewModel.selectPersonality(persona) }
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

                        HStack(spacing: 10) {
                            Button {
                                withAnimation(.spring(response: 0.34, dampingFraction: 0.9)) {
                                    launchStep = 1
                                }
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
                                UserDefaults.standard.set(viewModel.selectedWarmupMinutes, forKey: "last_warmup_minutes")
                                withAnimation(AppConfig.Anim.transitionSpring) { viewModel.startWorkout() }
                            } label: {
                                Text("Start coaching")
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity, minHeight: 52)
                                    .background(
                                        Group {
                                            if canStartWorkout {
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
                                    .shadow(color: canStartWorkout ? CoachiTheme.primary.opacity(0.28) : .clear, radius: 10, y: 3)
                            }
                            .disabled(!canStartWorkout)
                            .buttonStyle(.plain)
                        }
                        .padding(.top, 4)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 60)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 12)
            }
        }
        .onAppear {
            // Restore last session warmup time
            if let saved = UserDefaults.standard.object(forKey: "last_warmup_minutes") as? Int {
                viewModel.selectedWarmupMinutes = saved
            }
            launchStep = 1
            resetSetupFlowForSelectedMode()
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) { appeared = true }
        }
    }

    @ViewBuilder
    private func launchSection<Content: View>(title: String, subtitle: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Text(title.uppercased())
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(CoachiTheme.primary)
                Text(subtitle)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textSecondary)
            }
            content()
        }
        .padding(14)
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

    private var stepASubtitle: String {
        switch setupStage {
        case .easyWarmup, .intervalWarmup:
            return L10n.warmupTime
        case .easyDuration:
            return L10n.current == .no ? "Løpsvarighet" : "Run duration"
        case .intervalSets:
            return L10n.current == .no ? "Drag" : "Drag"
        case .intervalDuration:
            return L10n.current == .no ? "Tid" : "Time"
        case .intervalBreak:
            return L10n.current == .no ? "Pauser" : "Breaks"
        }
    }

    @ViewBuilder
    private var easyRunSetupContent: some View {
        if setupStage == .easyWarmup {
            VStack(spacing: 10) {
                Text(L10n.warmupTime.uppercased())
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)
                CircularDialPicker(
                    selectedValue: $viewModel.selectedWarmupMinutes,
                    valueRange: 0...40,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: L10n.skipWarmup
                )
                stageCheckButton(title: L10n.current == .no ? "Bekreft oppvarming" : "Confirm warm-up") {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                        setupStage = .easyDuration
                        easyRunConfigured = false
                    }
                }
            }
        } else {
            VStack(spacing: 10) {
                Text((L10n.current == .no ? "LØPSVARIGHET" : "RUN DURATION"))
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)
                CircularDialPicker(
                    selectedValue: $viewModel.selectedEasyRunMinutes,
                    valueRange: 0...120,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: L10n.current == .no ? "0 MIN" : "0 MIN"
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

                    stageCheckButton(title: L10n.current == .no ? "Bekreft varighet" : "Confirm duration") {
                        easyRunConfigured = true
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var intervalsSetupContent: some View {
        if setupStage == .intervalWarmup {
            VStack(spacing: 10) {
                Text(L10n.warmupTime.uppercased())
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)
                CircularDialPicker(
                    selectedValue: $viewModel.selectedWarmupMinutes,
                    valueRange: 0...40,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: L10n.skipWarmup
                )
                stageCheckButton(title: L10n.current == .no ? "Bekreft oppvarming" : "Confirm warm-up") {
                    withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                        setupStage = .intervalSets
                        intervalsConfigured = false
                    }
                }
            }
        } else if setupStage == .intervalSets {
            VStack(spacing: 12) {
                Text((L10n.current == .no ? "DRAG" : "DRAG"))
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)

                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalSets,
                    valueRange: 2...20,
                    unitLabel: L10n.current == .no ? "DRAG" : "DRAG",
                    zeroLabel: nil
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

                    stageCheckButton(title: L10n.current == .no ? "Bekreft" : "Confirm") {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalDuration
                            intervalsConfigured = false
                        }
                    }
                }
            }
        } else if setupStage == .intervalDuration {
            VStack(spacing: 12) {
                Text((L10n.current == .no ? "TID" : "TIME"))
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)

                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalWorkMinutes,
                    valueRange: 1...30,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: nil
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

                    stageCheckButton(title: L10n.current == .no ? "Bekreft" : "Confirm") {
                        withAnimation(.spring(response: 0.28, dampingFraction: 0.88)) {
                            setupStage = .intervalBreak
                            intervalsConfigured = false
                        }
                    }
                }
            }
        } else {
            VStack(spacing: 12) {
                Text((L10n.current == .no ? "PAUSER" : "BREAKS"))
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(1)

                CircularDialPicker(
                    selectedValue: $viewModel.selectedIntervalBreakMinutes,
                    valueRange: 0...10,
                    unitLabel: L10n.minutesUpper,
                    zeroLabel: L10n.current == .no ? "INGEN" : "NONE"
                )

                Text(
                    L10n.current == .no
                        ? "Total intervalltid: \(intervalTotalMinutes) min"
                        : "Total interval time: \(intervalTotalMinutes) min"
                )
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

    private func resetSetupFlowForSelectedMode() {
        showAdvancedOptions = false
        switch viewModel.selectedWorkoutMode {
        case .easyRun:
            setupStage = .easyWarmup
            easyRunConfigured = false
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

    @ViewBuilder
    private func styleChip(_ style: CoachingStyle) -> some View {
        let selected = viewModel.coachingStyle == style
        Button {
            viewModel.coachingStyle = style
        } label: {
            Text(style.displayName)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(selected ? .white : CoachiTheme.textPrimary)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .fill(selected ? CoachiTheme.primary : CoachiTheme.surface)
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Circular Dial Picker

struct CircularDialPicker: View {
    @Binding var selectedValue: Int

    var valueRange: ClosedRange<Int> = 0...40
    var unitLabel: String = L10n.minutesUpper
    var zeroLabel: String? = L10n.skipWarmup
    var dialSize: CGFloat = 220
    var trackWidth: CGFloat = 18
    var knobSize: CGFloat = 30

    // Internal drag state (continuous, not snapped)
    @State private var currentAngle: Double = 0 // 0-360 degrees, 0 = 12 o'clock
    @State private var isDragging = false
    private let hapticGenerator = UIImpactFeedbackGenerator(style: .light)

    private var minValue: Int { valueRange.lowerBound }
    private var maxValue: Int { valueRange.upperBound }
    private var valueSpan: CGFloat { CGFloat(max(1, maxValue - minValue)) }
    private var containerSize: CGFloat { dialSize + max(30, trackWidth + knobSize) }

    private var safeAngle: Double {
        guard currentAngle.isFinite else { return 0 }
        return max(0, min(360, currentAngle))
    }

    private var progress: Double {
        let raw = safeAngle / 360.0
        guard raw.isFinite else { return 0 }
        return max(0, min(1, raw))
    }

    private var displayValue: Int {
        let raw = progress * valueSpan
        guard raw.isFinite else { return minValue }
        let rounded = Int(round(raw))
        return max(minValue, min(maxValue, minValue + rounded))
    }

    private var valueUnitText: String {
        if displayValue == 0, let zeroLabel {
            return zeroLabel
        }
        return unitLabel
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
            if progress > 0.001 {
                Circle()
                    .trim(from: 0, to: CGFloat(min(progress, 1.0)))
                    .stroke(
                        AngularGradient(
                            colors: [CoachiTheme.dialPurple, CoachiTheme.dialMagenta, CoachiTheme.dialMagenta],
                            center: .center,
                            startAngle: .degrees(-90),
                            endAngle: .degrees(-90 + 360 * progress)
                        ),
                        style: StrokeStyle(lineWidth: trackWidth, lineCap: .round)
                    )
                    .frame(width: dialSize, height: dialSize)
                    .rotationEffect(.degrees(-90))
            }

            // Center content
            VStack(spacing: 2) {
                Text("\(displayValue)")
                    .font(.system(size: max(36, dialSize * 0.25), weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .contentTransition(.numericText())
                    .animation(.easeInOut(duration: 0.15), value: displayValue)

                Text(valueUnitText)
                    .font(.system(size: max(11, dialSize * 0.065), weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(2)
            }

            // Draggable knob
            knobView
                .offset(y: -dialSize / 2)
                .rotationEffect(.degrees(safeAngle))
        }
        .frame(width: containerSize, height: containerSize)
        .contentShape(Circle()) // Make entire dial tappable
        .gesture(dialDragGesture)
        .onAppear { syncAngleFromMinutes() }
        .onChange(of: selectedValue) { _, _ in
            if !isDragging { syncAngleFromMinutes() }
        }
    }

    // MARK: - Knob

    private var knobView: some View {
        ZStack {
            // Outer glow
            Circle()
                .fill(CoachiTheme.dialMagenta.opacity(isDragging ? 0.4 : 0.2))
                .frame(width: knobSize + 12, height: knobSize + 12)
                .blur(radius: 6)

            // Metallic knob
            Circle()
                .fill(
                    RadialGradient(
                        colors: [Color.white, Color(hex: "C0C0C0"), Color(hex: "888888")],
                        center: .init(x: 0.4, y: 0.35),
                        startRadius: 0,
                        endRadius: knobSize / 2
                    )
                )
                .frame(width: knobSize, height: knobSize)
                .shadow(color: .black.opacity(0.5), radius: 4, y: 2)

            // Inner highlight
            Circle()
                .fill(Color.white.opacity(0.3))
                .frame(width: knobSize * 0.4, height: knobSize * 0.4)
                .offset(x: -2, y: -2)
        }
        .scaleEffect(isDragging ? 1.15 : 1.0)
        .animation(.spring(response: 0.25, dampingFraction: 0.7), value: isDragging)
    }

    // MARK: - Gesture

    private var dialDragGesture: some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { value in
                if !isDragging {
                    isDragging = true
                    hapticGenerator.prepare()
                    hapticGenerator.impactOccurred()
                }
                updateAngle(from: value.location, in: containerSize)
            }
            .onEnded { _ in
                isDragging = false
                // Commit final value
                selectedValue = displayValue
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

        let oldMinutes = displayValue
        currentAngle = angle

        let newMinutes = displayValue
        if newMinutes != oldMinutes {
            hapticGenerator.impactOccurred(intensity: 0.4)
        }
    }

    private func syncAngleFromMinutes() {
        let clamped = min(max(selectedValue, minValue), maxValue)
        let span = max(1, maxValue - minValue)
        guard span > 0 else {
            currentAngle = 0
            return
        }
        let normalized = Double(clamped - minValue) / Double(span)
        let nextAngle = normalized * 360.0
        currentAngle = nextAngle.isFinite ? nextAngle : 0
    }
}
