//
//  ActiveWorkoutView.swift
//  TreningsCoach
//
//  Active workout screen with orb, timer ring, controls
//

import SwiftUI
import UIKit

struct ActiveWorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var showDiagnostics = false
    @State private var showStopConfirmation = false
    private let workoutBackgroundImageName = "OnboardingBgOutdoor"

    var body: some View {
        ZStack {
            WorkoutPhotoBackground(imageName: workoutBackgroundImageName)
                .ignoresSafeArea()
            LinearGradient(
                colors: [Color.black.opacity(0.14), Color.black.opacity(0.22), Color.black.opacity(0.38)],
                startPoint: .top,
                endPoint: .bottom
            )
                .ignoresSafeArea()

            GeometryReader { geo in
                let ringSize = min(geo.size.width * 0.74, 320)

                VStack(spacing: 0) {
                    HStack(spacing: 10) {
                        Spacer()
                        consoleIconButton
                        spotifyIconButton
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, max(geo.safeAreaInsets.top + 8, 20))

                    Spacer(minLength: 14)

                    ZStack {
                        Circle()
                            .fill(Color.white.opacity(0.12))
                            .frame(width: ringSize + 34, height: ringSize + 34)
                            .blur(radius: 10)

                        TimerRingView(progress: viewModel.phaseProgress, size: ringSize, lineWidth: 12)
                            .allowsHitTesting(false)

                        Text(viewModel.elapsedFormatted)
                            .font(.system(size: ringSize * 0.22, weight: .semibold, design: .monospaced))
                            .foregroundColor(.white.opacity(0.96))
                            .minimumScaleFactor(0.7)
                            .lineLimit(1)
                            .shadow(color: .black.opacity(0.35), radius: 8, y: 2)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top, 18)
                    .contentShape(Circle())
                    .onTapGesture {
                        withAnimation(AppConfig.Anim.buttonSpring) {
                            if viewModel.workoutState == .paused {
                                viewModel.resumeWorkout()
                            } else {
                                viewModel.pauseWorkout()
                            }
                        }
                    }

                    bpmStatusPill
                        .padding(.top, 22)

                    phaseCountdownPanel
                        .padding(.top, 10)

                    Spacer()

                    bottomControlPanel
                        .padding(.horizontal, 20)
                        .padding(.bottom, max(geo.safeAreaInsets.bottom + 10, 24))
                }
            }
        }
        .onAppear {
            showDiagnostics = AudioPipelineDiagnostics.shared.isOverlayVisible
        }
        .onChange(of: showDiagnostics) { _, isVisible in
            AudioPipelineDiagnostics.shared.isOverlayVisible = isVisible
        }
        .sheet(isPresented: $showDiagnostics) {
            ZStack {
                CoachiTheme.backgroundGradient
                    .ignoresSafeArea()
                VStack {
                    AudioDiagnosticOverlayView(workoutViewModel: viewModel, isPresented: $showDiagnostics)
                    Spacer()
                }
                .padding(.top, 20)
            }
            .presentationDetents([.height(320), .large])
            .presentationDragIndicator(.visible)
        }
        .alert(
            L10n.current == .no ? "Avslutte økten?" : "End workout?",
            isPresented: $showStopConfirmation
        ) {
            if viewModel.workoutState == .paused {
                Button(L10n.current == .no ? "Fortsett" : "Resume") {
                    withAnimation(AppConfig.Anim.buttonSpring) {
                        viewModel.resumeWorkout()
                    }
                }
            } else {
                Button(L10n.current == .no ? "Pause" : "Pause") {
                    withAnimation(AppConfig.Anim.buttonSpring) {
                        viewModel.pauseWorkout()
                    }
                }
            }

            Button(L10n.current == .no ? "Avslutt" : "End", role: .destructive) {
                withAnimation(AppConfig.Anim.transitionSpring) {
                    viewModel.stopWorkout()
                }
            }
            Button(L10n.current == .no ? "Fortsett økt" : "Keep workout", role: .cancel) {}
        } message: {
            Text(L10n.current == .no ? "Vil du avslutte treningen nå?" : "Do you want to end the workout now?")
        }
    }

    private var bpmText: String {
        if viewModel.watchConnected {
            return "LIVE \(viewModel.watchBPMDisplayText)"
        }
        return "0 BPM"
    }

    private var bpmColor: Color {
        viewModel.watchConnected ? .green : .red
    }

    private var consoleIconButton: some View {
        Button {
            showDiagnostics = true
        } label: {
            Image(systemName: "gearshape.fill")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(Color.white.opacity(0.95))
                .frame(width: 40, height: 40)
                .background(
                    Circle()
                        .fill(Color.black.opacity(0.28))
                        .overlay(
                            Circle()
                                .stroke(Color.white.opacity(0.24), lineWidth: 1)
                        )
                )
        }
        .buttonStyle(.plain)
    }

    private var spotifyIconButton: some View {
        Button {
            viewModel.handleSpotifyButtonTapped()
        } label: {
            SpotifyLogoBadge(size: 22)
                .frame(width: 40, height: 40)
                .background(
                    Circle()
                        .fill(Color.black.opacity(0.28))
                        .overlay(
                            Circle()
                                .stroke(Color.white.opacity(0.24), lineWidth: 1)
                        )
                )
        }
        .buttonStyle(.plain)
    }

    private var bpmStatusPill: some View {
        HStack(spacing: 9) {
            Image(systemName: "heart.fill")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(bpmColor)

            Text(bpmText)
                .font(.system(size: 18, weight: .semibold, design: .monospaced))
                .foregroundColor(Color.white.opacity(0.95))
                .lineLimit(1)
                .minimumScaleFactor(0.8)

            Circle()
                .fill(bpmColor)
                .frame(width: 8, height: 8)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(
            Capsule()
                .fill(Color.black.opacity(0.24))
                .overlay(
                    Capsule()
                        .stroke(Color.white.opacity(0.20), lineWidth: 1)
                )
        )
    }

    private var phaseCountdownPanel: some View {
        VStack(spacing: 4) {
            Text(viewModel.phaseCountdownPrimaryText)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(Color.white.opacity(0.96))
                .lineLimit(1)
                .minimumScaleFactor(0.8)

            if let secondary = viewModel.phaseCountdownSecondaryText {
                Text(secondary)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.white.opacity(0.78))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(Color.black.opacity(0.22))
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .stroke(Color.white.opacity(0.20), lineWidth: 1)
                )
        )
        .padding(.horizontal, 20)
    }

    @ViewBuilder
    private var bottomControlPanel: some View {
        HStack(spacing: 12) {
            Button {
                viewModel.talkToCoachButtonPressed()
            } label: {
                HStack(spacing: 9) {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 17, weight: .bold))
                    Text(L10n.talkToCoachButton)
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

            Button {
                showStopConfirmation = true
            } label: {
                Image(systemName: "figure.run")
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(.white.opacity(0.96))
                    .frame(width: 82, height: 82)
                    .background(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .fill(CoachiTheme.primaryGradient)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(Color.white.opacity(0.26), lineWidth: 1)
                    )
                    .shadow(color: CoachiTheme.primary.opacity(0.34), radius: 16, y: 6)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(L10n.current == .no ? "Avslutt trening" : "Finish workout")
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 30, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 30, style: .continuous)
                        .stroke(Color.white.opacity(0.28), lineWidth: 1)
                )
        )
        .shadow(color: Color.black.opacity(0.18), radius: 14, y: 6)
    }
}

private struct WorkoutPhotoBackground: View {
    let imageName: String

    var body: some View {
        GeometryReader { geo in
            Image(imageName)
                .resizable()
                .scaledToFill()
                .frame(width: geo.size.width, height: geo.size.height)
                .clipped()
                .saturation(0.85)
                .contrast(1.05)
                .overlay(
                    LinearGradient(
                        colors: [Color.black.opacity(0.18), Color.black.opacity(0.34)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
        }
        .transition(.opacity)
    }
}

struct SpotifyConnectView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @Environment(\.dismiss) private var dismiss

    private var isNorwegian: Bool { L10n.current == .no }

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "160019"), Color(hex: "081534"), Color(hex: "06070D")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 20) {
                HStack {
                    Spacer()
                    Button {
                        viewModel.dismissSpotifyConnectSheet()
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .frame(width: 36, height: 36)
                            .background(CoachiTheme.surface.opacity(0.75))
                            .clipShape(Circle())
                    }
                }
                .padding(.top, 8)

                Text(isNorwegian ? "SPOTIFY PREMIUM-\nTILKOBLING" : "SPOTIFY PREMIUM\nCONNECTION")
                    .font(.system(size: 44, weight: .medium))
                    .multilineTextAlignment(.center)
                    .foregroundColor(.white)
                    .minimumScaleFactor(0.65)
                    .lineLimit(2)

                Text(
                    isNorwegian
                        ? "Har du Spotify Premium, kan du koble appen til Spotify og styre musikk i bakgrunnen."
                        : "If you have Spotify Premium, connect your app to Spotify and control music in the background."
                )
                .font(.system(size: 17, weight: .regular))
                .multilineTextAlignment(.center)
                .foregroundColor(CoachiTheme.textPrimary.opacity(0.9))
                .padding(.horizontal, 8)

                Spacer(minLength: 18)

                ZStack {
                    Circle()
                        .trim(from: 0.10, to: 1.00)
                        .stroke(
                            LinearGradient(
                                colors: [Color(hex: "16B8FF"), Color(hex: "2FD4FF")],
                                startPoint: .leading,
                                endPoint: .trailing
                            ),
                            style: StrokeStyle(lineWidth: 5.5, lineCap: .round)
                        )
                        .rotationEffect(.degrees(132))
                        .frame(width: 220, height: 220)
                        .shadow(color: Color(hex: "16B8FF").opacity(0.45), radius: 18, y: 0)

                    Image(systemName: "music.note")
                        .font(.system(size: 46, weight: .light))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color(hex: "FF4EE9"), Color(hex: "A852FF")],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .offset(x: -78, y: -60)
                }

                Spacer(minLength: 26)

                Button {
                    viewModel.connectSpotifyFromSheet()
                    dismiss()
                } label: {
                    HStack(spacing: 12) {
                        Circle()
                            .fill(Color.black.opacity(0.2))
                            .frame(width: 26, height: 26)
                            .overlay(SpotifyGlyph(size: 14))
                        Text(isNorwegian ? "KOBLE TIL SPOTIFY" : "CONNECT SPOTIFY")
                            .font(.system(size: 18, weight: .bold))
                            .tracking(0.5)
                    }
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity)
                    .frame(height: 62)
                    .background(Color(hex: "1ED760"))
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                }

                Button {
                    viewModel.dismissSpotifyConnectSheet()
                    dismiss()
                } label: {
                    Text(isNorwegian ? "JEG HAR IKKE SPOTIFY PREMIUM" : "I DON'T HAVE SPOTIFY PREMIUM")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white.opacity(0.95))
                        .frame(maxWidth: .infinity)
                        .frame(height: 62)
                        .background(Color.white.opacity(0.06))
                        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 20, style: .continuous)
                                .stroke(Color.white.opacity(0.15), lineWidth: 1)
                        )
                }
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 34)
        }
    }
}

struct SpotifyLogoBadge: View {
    let size: CGFloat

    var body: some View {
        ZStack {
            Circle()
                .fill(Color(hex: "1DB954"))
                .frame(width: size, height: size)
                .shadow(color: Color(hex: "1DB954").opacity(0.4), radius: 10, y: 2)
            SpotifyGlyph(size: size * 0.56)
        }
        .overlay(
            Circle()
                .stroke(Color.black.opacity(0.12), lineWidth: 0.6)
        )
    }
}

private struct SpotifyGlyph: View {
    let size: CGFloat

    var body: some View {
        ZStack {
            arc(radius: 0.44, yOffset: 0.04, start: 205, end: 333, width: 0.145)
            arc(radius: 0.34, yOffset: 0.16, start: 210, end: 330, width: 0.125)
            arc(radius: 0.25, yOffset: 0.28, start: 214, end: 326, width: 0.11)
        }
        .frame(width: size, height: size)
    }

    @ViewBuilder
    private func arc(radius: CGFloat, yOffset: CGFloat, start: Double, end: Double, width: CGFloat) -> some View {
        let center = CGPoint(x: size * 0.5, y: size * (0.5 + yOffset))
        Path { path in
            path.addArc(
                center: center,
                radius: size * radius,
                startAngle: .degrees(start),
                endAngle: .degrees(end),
                clockwise: false
            )
        }
        .stroke(
            Color.black,
            style: StrokeStyle(
                lineWidth: size * width,
                lineCap: .round,
                lineJoin: .round
            )
        )
    }
}
