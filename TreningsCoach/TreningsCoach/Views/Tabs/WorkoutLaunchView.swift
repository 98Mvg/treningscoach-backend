//
//  WorkoutLaunchView.swift
//  TreningsCoach
//
//  Pre-workout setup: persona selector, warmup time circular dial, GO button
//

import SwiftUI

struct WorkoutLaunchView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var appeared = false

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            ParticleBackgroundView(particleCount: 30)

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

                    VStack(alignment: .leading, spacing: 6) {
                        Text("What are you doing today?")
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text("Choose session, inputs, and coaching style.")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)

                    // Session choice (Step A)
                    HStack(spacing: 10) {
                        launchCard(
                            title: "Easy Run",
                            subtitle: "Stay easy. Build endurance.",
                            selected: viewModel.selectedWorkoutMode == .easyRun
                        ) {
                            viewModel.selectedWorkoutMode = .easyRun
                        }
                        launchCard(
                            title: "Intervals",
                            subtitle: "Fast reps + recovery.",
                            selected: viewModel.selectedWorkoutMode == .intervals
                        ) {
                            viewModel.selectedWorkoutMode = .intervals
                        }
                    }
                    launchComingSoonCard(
                        title: "Strength",
                        subtitle: "Coming soon."
                    )

                    if viewModel.selectedWorkoutMode == .easyRun {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Easy Run duration")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(CoachiTheme.textTertiary)
                            HStack(spacing: 8) {
                                durationChip(20)
                                durationChip(30)
                                durationChip(45)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    } else if viewModel.selectedWorkoutMode == .intervals {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Interval template")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(CoachiTheme.textTertiary)
                            HStack(spacing: 8) {
                                templateChip(.fourByFour)
                                templateChip(.eightByOne)
                                templateChip(.tenByThirtyThirty)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    // Input source status (Step B)
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Inputs")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(CoachiTheme.textTertiary)
                        HStack {
                            Label(viewModel.watchConnected ? "Apple Watch connected" : "Apple Watch not connected", systemImage: viewModel.watchConnected ? "checkmark.circle.fill" : "xmark.circle.fill")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(viewModel.watchConnected ? CoachiTheme.secondary : CoachiTheme.textSecondary)
                            Spacer()
                        }
                        HStack {
                            Text("HR signal quality: \(viewModel.hrSignalQuality.capitalized)")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(viewModel.hrSignalQuality == "good" ? CoachiTheme.secondary : CoachiTheme.textSecondary)
                            Spacer()
                        }
                        HStack {
                            Text("Movement source: \(viewModel.movementSourceDisplay)")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(viewModel.movementSource == "none" ? CoachiTheme.textSecondary : CoachiTheme.secondary)
                            Spacer()
                        }
                        HStack {
                            Text("Cadence: \(viewModel.cadenceDisplayText)")
                                .font(.system(size: 13, weight: .medium, design: .monospaced))
                                .foregroundColor(CoachiTheme.textSecondary)
                            Spacer()
                        }
                        Toggle(isOn: $viewModel.useBreathingMicCues) {
                            Text("Use breathing mic cues")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                        }
                        .tint(CoachiTheme.primary)
                    }
                    .padding(14)
                    .background(CoachiTheme.surface.opacity(0.9))
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                    // Coaching style (Step C)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Coaching style")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(CoachiTheme.textTertiary)
                        HStack(spacing: 8) {
                            styleChip(.minimal)
                            styleChip(.normal)
                            styleChip(.motivational)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)

                    if viewModel.selectedWorkoutMode != .intervals {
                        VStack(spacing: 4) {
                            Text(L10n.warmupTime.uppercased())
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(CoachiTheme.textTertiary)
                                .tracking(1)
                            CircularDialPicker(selectedMinutes: $viewModel.selectedWarmupMinutes)
                        }
                    }

                    // Persona selector
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

                    // GO button
                    Button {
                        UserDefaults.standard.set(viewModel.selectedWarmupMinutes, forKey: "last_warmup_minutes")
                        withAnimation(AppConfig.Anim.transitionSpring) { viewModel.startWorkout() }
                    } label: {
                        ZStack {
                            Circle().fill(CoachiTheme.primary.opacity(0.06))
                                .frame(width: 200, height: 200)
                            Circle().fill(CoachiTheme.primary.opacity(0.12))
                                .frame(width: 170, height: 170)
                            Circle()
                                .fill(CoachiTheme.primaryGradient)
                                .frame(width: 140, height: 140)
                                .shadow(color: CoachiTheme.primary.opacity(0.4), radius: 25, y: 8)
                            Text("Start coaching")
                                .font(.system(size: 28, weight: .black, design: .rounded))
                                .foregroundColor(.white)
                                .multilineTextAlignment(.center)
                        }
                    }
                    .buttonStyle(ScaleButtonStyle())
                    .padding(.top, 8)
                    .padding(.bottom, 60)
                }
                .padding(.horizontal, 20)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 12)
            }
        }
        .onAppear {
            // Restore last session warmup time
            let saved = UserDefaults.standard.integer(forKey: "last_warmup_minutes")
            if saved > 0 {
                viewModel.selectedWarmupMinutes = saved
            }
            withAnimation(.easeOut(duration: 0.7).delay(0.15)) { appeared = true }
        }
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
    private func durationChip(_ minutes: Int) -> some View {
        let selected = viewModel.selectedEasyRunMinutes == minutes
        Button {
            viewModel.selectedEasyRunMinutes = minutes
        } label: {
            Text("\(minutes) min")
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

    @ViewBuilder
    private func templateChip(_ template: IntervalTemplate) -> some View {
        let selected = viewModel.selectedIntervalTemplate == template
        Button {
            viewModel.selectedIntervalTemplate = template
        } label: {
            Text(template.displayName)
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
    @Binding var selectedMinutes: Int

    private let maxMinutes: CGFloat = 40
    private let dialSize: CGFloat = 220
    private let trackWidth: CGFloat = 18
    private let knobSize: CGFloat = 30

    // Internal drag state (continuous, not snapped)
    @State private var currentAngle: Double = 0 // 0-360 degrees, 0 = 12 o'clock
    @State private var isDragging = false
    private let hapticGenerator = UIImpactFeedbackGenerator(style: .light)

    private var progress: Double { currentAngle / 360.0 }
    private var displayMinutes: Int { Int(round(currentAngle / 360.0 * maxMinutes)) }

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
                Text("\(displayMinutes)")
                    .font(.system(size: 56, weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .contentTransition(.numericText())
                    .animation(.easeInOut(duration: 0.15), value: displayMinutes)

                Text(displayMinutes == 0 ? L10n.skipWarmup : L10n.minutesUpper)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(CoachiTheme.textTertiary)
                    .tracking(2)
            }

            // Draggable knob
            knobView
                .offset(y: -dialSize / 2)
                .rotationEffect(.degrees(currentAngle))
        }
        .frame(width: dialSize + 40, height: dialSize + 40)
        .contentShape(Circle()) // Make entire dial tappable
        .gesture(dialDragGesture)
        .onAppear { syncAngleFromMinutes() }
        .onChange(of: selectedMinutes) { _ in
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
                updateAngle(from: value.location, in: dialSize + 40)
            }
            .onEnded { _ in
                isDragging = false
                // Commit final value
                selectedMinutes = displayMinutes
            }
    }

    private func updateAngle(from point: CGPoint, in size: CGFloat) {
        let center = CGPoint(x: size / 2, y: size / 2)
        let dx = point.x - center.x
        let dy = point.y - center.y

        // Dead-zone: ignore touches near center where angle is unreliable
        let distance = sqrt(dx * dx + dy * dy)
        guard distance > 30 else { return }

        // atan2 gives angle from positive x-axis; convert to clockwise from 12 o'clock
        var angle = atan2(dx, -dy) * 180 / .pi // degrees, 0 = 12 o'clock, clockwise positive
        if angle < 0 { angle += 360 }

        let oldMinutes = displayMinutes
        currentAngle = angle

        let newMinutes = displayMinutes
        if newMinutes != oldMinutes {
            hapticGenerator.impactOccurred(intensity: 0.4)
        }
    }

    private func syncAngleFromMinutes() {
        let clamped = min(max(selectedMinutes, 0), Int(maxMinutes))
        currentAngle = Double(clamped) / Double(maxMinutes) * 360.0
    }
}

// Simple press-down scale effect for the GO button
struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.92 : 1.0)
            .animation(.spring(response: 0.25, dampingFraction: 0.7), value: configuration.isPressed)
    }
}
