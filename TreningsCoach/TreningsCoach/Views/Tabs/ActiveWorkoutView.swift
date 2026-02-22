//
//  ActiveWorkoutView.swift
//  TreningsCoach
//
//  Active workout screen with orb, timer ring, controls
//

import SwiftUI

struct ActiveWorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var micPulse = false

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer().frame(height: 24)

                Spacer()

                // Orb is the main control surface:
                // tap = pause/resume, long-press = stop
                ZStack {
                    TimerRingView(progress: viewModel.phaseProgress, size: AppConfig.Layout.timerRingSize, lineWidth: 6)
                        .allowsHitTesting(false)
                    CoachOrbView(state: viewModel.orbState, size: AppConfig.Layout.orbSize)
                        .allowsHitTesting(false)

                    Image(systemName: viewModel.workoutState == .paused ? "play.fill" : "pause.fill")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.white.opacity(0.85))
                        .shadow(color: .black.opacity(0.25), radius: 6, y: 2)
                }
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
                .onLongPressGesture(minimumDuration: 0.8) {
                    withAnimation(AppConfig.Anim.transitionSpring) {
                        viewModel.stopWorkout()
                    }
                }

                // Elapsed time
                Text(viewModel.elapsedFormatted)
                    .font(.system(size: 48, weight: .light, design: .monospaced)).foregroundColor(CoachiTheme.textPrimary).padding(.top, 20)

                if viewModel.watchConnected {
                    HStack(spacing: 10) {
                        Circle()
                            .fill(viewModel.hrIsReliable ? CoachiTheme.success : CoachiTheme.textTertiary)
                            .frame(width: 10, height: 10)
                        Text(hrStatusText)
                            .font(.system(size: 18, weight: .semibold, design: .monospaced))
                            .foregroundColor(CoachiTheme.textPrimary)
                    }
                    .padding(.horizontal, 18)
                    .padding(.vertical, 10)
                    .background(
                        Capsule()
                            .fill(CoachiTheme.surface)
                            .overlay(Capsule().stroke(Color.white.opacity(0.06), lineWidth: 1))
                    )
                    .padding(.top, 16)
                }

                Spacer()

                // Minimal bottom controls (no extra start/stop buttons)
                HStack(spacing: 22) {
                    Button { viewModel.talkToCoachButtonPressed() } label: {
                        ZStack {
                            Circle()
                                .stroke(CoachiTheme.secondary.opacity(0.45), lineWidth: 2)
                                .frame(width: 88, height: 88)
                                .scaleEffect(micPulse ? 1.1 : 0.9)
                                .opacity(micPulse ? 0.15 : 0.6)

                            Circle()
                                .fill(CoachiTheme.secondary.opacity(0.16))
                                .frame(width: 70, height: 70)

                            Circle()
                                .fill(CoachiTheme.surface)
                                .frame(width: 58, height: 58)

                            Image(systemName: "mic.fill")
                                .font(.system(size: 26, weight: .bold))
                                .foregroundColor(CoachiTheme.secondary)
                        }
                    }

                    // Spotify quick-access (late-phase media UX, does not affect coaching logic)
                    Button { viewModel.handleSpotifyButtonTapped() } label: {
                        ZStack(alignment: .bottomTrailing) {
                            SpotifyLogoBadge(size: 56)
                            if viewModel.isSpotifyConnected {
                                Circle()
                                    .fill(CoachiTheme.success)
                                    .frame(width: 16, height: 16)
                                    .overlay(
                                        Image(systemName: "checkmark")
                                            .font(.system(size: 8, weight: .bold))
                                            .foregroundColor(.white)
                                    )
                                    .offset(x: 2, y: 2)
                            }
                        }
                    }
                }
                .padding(.bottom, 34)
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.3).repeatForever(autoreverses: true)) {
                micPulse = true
            }
        }
    }

    private var hrStatusText: String {
        if viewModel.hrIsReliable, let heartRate = viewModel.heartRate {
            return "HR \(heartRate) bpm"
        }
        return "HR --"
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
        .preferredColorScheme(.dark)
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
