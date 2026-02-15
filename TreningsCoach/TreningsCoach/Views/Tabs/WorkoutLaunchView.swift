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

            VStack(spacing: 0) {
                // Top bar
                HStack {
                    HStack(spacing: 6) {
                        CoachiLogoView(size: 24)
                        Text(AppConfig.appName).font(.system(size: 17, weight: .semibold)).foregroundColor(CoachiTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24).padding(.top, 8).opacity(appeared ? 1 : 0)

                Spacer()

                // GO button (large, centered)
                Button {
                    // Persist warmup selection for next session
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
                        Text(L10n.go)
                            .font(.system(size: 42, weight: .black, design: .rounded))
                            .foregroundColor(.white)
                    }
                }
                .buttonStyle(ScaleButtonStyle())
                .opacity(appeared ? 1 : 0).scaleEffect(appeared ? 1 : 0.8)

                Spacer().frame(height: 20)

                // Warmup time — circular dial
                VStack(spacing: 4) {
                    Text(L10n.warmupTime.uppercased())
                        .font(.system(size: 13, weight: .semibold)).foregroundColor(CoachiTheme.textTertiary)
                        .tracking(1)

                    CircularDialPicker(selectedMinutes: $viewModel.selectedWarmupMinutes)
                }
                .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 15)

                Spacer().frame(height: 20)

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
                .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

                Spacer().frame(height: 80)
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
