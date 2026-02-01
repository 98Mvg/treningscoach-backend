//
//  WorkoutView.swift
//  TreningsCoach
//
//  Main workout screen — audio-first, glanceable design
//  Voice orb at center with timer ring, phase indicator, coach message
//  User should NOT need to stare at this screen — quick glance only
//

import SwiftUI

struct WorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var showChatSheet = false
    @State private var chatInput = ""

    var body: some View {
        ZStack {
            // Dark background
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {

                // MARK: - Top Bar (Phase + Chat Button)
                HStack {
                    if viewModel.isContinuousMode {
                        phaseIndicator
                            .transition(.opacity)
                    }
                    Spacer()
                    // Talk to Coach button
                    Button {
                        showChatSheet = true
                    } label: {
                        Image(systemName: "bubble.left.fill")
                            .font(.title3)
                            .foregroundStyle(AppTheme.secondaryAccent)
                            .padding(10)
                            .background(AppTheme.cardSurface)
                            .clipShape(Circle())
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)

                Spacer()

                // MARK: - Voice Orb + Timer Ring (center)
                ZStack {
                    // Timer ring wraps around the orb
                    if viewModel.isContinuousMode {
                        TimerRingView(
                            elapsedTime: viewModel.elapsedTime,
                            totalTime: AppConfig.ContinuousCoaching.maxWorkoutDuration,
                            ringSize: 170,
                            lineWidth: 5
                        )
                        .transition(.opacity)
                    }

                    // The voice orb — THE interaction element
                    VoiceOrbView(state: viewModel.voiceState) {
                        if viewModel.isContinuousMode {
                            viewModel.stopContinuousWorkout()
                        } else if viewModel.isRecording {
                            viewModel.stopRecording()
                        } else {
                            viewModel.startContinuousWorkout()
                        }
                    }
                }

                // MARK: - Elapsed Time
                if viewModel.isContinuousMode {
                    Text(viewModel.elapsedTimeFormatted)
                        .font(.system(size: 32, weight: .light, design: .monospaced))
                        .foregroundStyle(AppTheme.textPrimary)
                        .padding(.top, 16)
                        .transition(.opacity)
                }

                // MARK: - Intensity Badge
                if viewModel.isContinuousMode, let analysis = viewModel.breathAnalysis {
                    intensityBadge(level: analysis.intensityLevel)
                        .padding(.top, 8)
                        .transition(.opacity)
                }

                // Hint text when idle
                if !viewModel.isContinuousMode {
                    Text("Tap to start workout")
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                        .padding(.top, 16)
                }

                Spacer()

                // MARK: - Skip Warmup Button
                if viewModel.isContinuousMode && viewModel.currentPhase == .warmup {
                    Button {
                        viewModel.skipToIntensePhase()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "forward.fill")
                                .font(.caption)
                            Text("Skip to Workout")
                                .font(.subheadline.weight(.semibold))
                        }
                        .foregroundStyle(AppTheme.secondaryAccent)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(AppTheme.secondaryAccent.opacity(0.15))
                        .clipShape(Capsule())
                    }
                    .transition(.opacity)
                }

                // MARK: - Stop Button (only during workout)
                if viewModel.isContinuousMode {
                    Button {
                        viewModel.stopContinuousWorkout()
                    } label: {
                        Text("Stop Workout")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(AppTheme.danger)
                            .padding(.horizontal, 24)
                            .padding(.vertical, 10)
                            .background(AppTheme.danger.opacity(0.15))
                            .clipShape(Capsule())
                    }
                    .padding(.top, 12)
                    .transition(.opacity)
                }

                Spacer()
                    .frame(height: 20)
            }
            .padding(.bottom, 80) // Space for tab bar
            .animation(.easeInOut(duration: 0.3), value: viewModel.isContinuousMode)
        }
        // Error alert
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage)
        }
        // Chat sheet
        .sheet(isPresented: $showChatSheet) {
            coachChatSheet
        }
    }

    // MARK: - Coach Chat Sheet

    private var coachChatSheet: some View {
        NavigationView {
            ZStack {
                AppTheme.background.ignoresSafeArea()

                VStack(spacing: 0) {
                    // Conversation history
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(Array(viewModel.coachConversation.enumerated()), id: \.offset) { _, msg in
                                HStack {
                                    if msg.role == "user" { Spacer() }
                                    Text(msg.text)
                                        .font(.body)
                                        .padding(12)
                                        .background(msg.role == "user" ? AppTheme.primaryAccent.opacity(0.3) : AppTheme.cardSurface)
                                        .foregroundStyle(AppTheme.textPrimary)
                                        .clipShape(RoundedRectangle(cornerRadius: 16))
                                    if msg.role == "coach" { Spacer() }
                                }
                            }

                            if viewModel.isTalkingToCoach {
                                HStack {
                                    Text("Coach is thinking...")
                                        .font(.caption)
                                        .foregroundStyle(AppTheme.textSecondary)
                                    Spacer()
                                }
                            }
                        }
                        .padding(16)
                    }

                    // Quick prompts
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(["Motivate me", "How's my breathing?", "Push me harder", "Give me a quote"], id: \.self) { prompt in
                                Button {
                                    chatInput = prompt
                                    sendChat()
                                } label: {
                                    Text(prompt)
                                        .font(.caption)
                                        .foregroundStyle(AppTheme.secondaryAccent)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(AppTheme.secondaryAccent.opacity(0.15))
                                        .clipShape(Capsule())
                                }
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                    }

                    // Input bar
                    HStack(spacing: 12) {
                        TextField("Ask your coach...", text: $chatInput)
                            .textFieldStyle(.plain)
                            .padding(12)
                            .background(AppTheme.cardSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 20))
                            .foregroundStyle(AppTheme.textPrimary)

                        Button {
                            sendChat()
                        } label: {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.title2)
                                .foregroundStyle(chatInput.isEmpty ? AppTheme.textSecondary : AppTheme.primaryAccent)
                        }
                        .disabled(chatInput.isEmpty || viewModel.isTalkingToCoach)
                    }
                    .padding(16)
                }
            }
            .navigationTitle("Talk to Coach")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { showChatSheet = false }
                        .foregroundStyle(AppTheme.primaryAccent)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func sendChat() {
        let message = chatInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !message.isEmpty else { return }
        chatInput = ""
        viewModel.talkToCoach(message: message)
    }

    // MARK: - Phase Indicator

    private var phaseIndicator: some View {
        HStack(spacing: 4) {
            ForEach(WorkoutPhase.allCases) { phase in
                HStack(spacing: 4) {
                    Image(systemName: phaseIcon(for: phase))
                        .font(.caption2)

                    Text(phaseLabel(for: phase))
                        .font(.caption.weight(.medium))
                }
                .foregroundStyle(
                    viewModel.currentPhase == phase
                        ? AppTheme.textPrimary
                        : AppTheme.textSecondary.opacity(0.5)
                )
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    viewModel.currentPhase == phase
                        ? AppTheme.primaryAccent.opacity(0.3)
                        : Color.clear
                )
                .clipShape(Capsule())
            }
        }
    }

    // MARK: - Intensity Badge

    private func intensityBadge(level: IntensityLevel) -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(intensityColor(for: level))
                .frame(width: 8, height: 8)

            Text(level.displayName)
                .font(.caption.weight(.medium))
                .foregroundStyle(AppTheme.textSecondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(intensityColor(for: level).opacity(0.12))
        .clipShape(Capsule())
        .animation(.easeInOut(duration: 0.3), value: level.rawValue)
    }

    // MARK: - Helpers

    private func phaseIcon(for phase: WorkoutPhase) -> String {
        switch phase {
        case .warmup: return "flame.fill"
        case .intense: return "bolt.fill"
        case .cooldown: return "wind"
        }
    }

    private func phaseLabel(for phase: WorkoutPhase) -> String {
        switch phase {
        case .warmup: return "Warmup"
        case .intense: return "Intense"
        case .cooldown: return "Cool"
        }
    }

    private func intensityColor(for level: IntensityLevel) -> Color {
        switch level {
        case .calm: return AppTheme.secondaryAccent
        case .moderate: return AppTheme.primaryAccent
        case .intense: return AppTheme.warning
        case .critical: return AppTheme.danger
        }
    }
}
