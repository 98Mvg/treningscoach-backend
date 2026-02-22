//
//  ActiveWorkoutView.swift
//  TreningsCoach
//
//  Active workout screen with orb, timer ring, controls
//

import SwiftUI

struct ActiveWorkoutView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var showDiagnostics = false

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                // Phase indicator pills
                HStack(spacing: 8) {
                    ForEach(WorkoutPhase.allCases) { phase in
                        Text(phase.displayName)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(viewModel.currentPhase == phase ? .white : CoachiTheme.textTertiary)
                            .padding(.horizontal, 14).padding(.vertical, 7)
                            .background(Capsule().fill(viewModel.currentPhase == phase ? CoachiTheme.primary.opacity(0.8) : CoachiTheme.surface))
                            .animation(.easeInOut(duration: 0.3), value: viewModel.currentPhase)
                    }
                }
                .padding(.top, 16)

                Spacer()

                // Orb + timer ring
                ZStack {
                    TimerRingView(progress: viewModel.phaseProgress, size: AppConfig.Layout.timerRingSize, lineWidth: 6)
                        .allowsHitTesting(false)
                    CoachOrbView(state: viewModel.orbState, size: AppConfig.Layout.orbSize)
                        .allowsHitTesting(false)
                }
                .contentShape(Circle())
                .onLongPressGesture(minimumDuration: 0.8) {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        showDiagnostics.toggle()
                        AudioPipelineDiagnostics.shared.isOverlayVisible = showDiagnostics
                    }
                }

                // Elapsed time
                Text(viewModel.elapsedFormatted)
                    .font(.system(size: 48, weight: .light, design: .monospaced)).foregroundColor(CoachiTheme.textPrimary).padding(.top, 20)

                Text(viewModel.workoutState == .paused ? L10n.paused.uppercased() : viewModel.currentPhase.displayName.uppercased())
                    .font(.system(size: 11, weight: .bold)).foregroundColor(CoachiTheme.textSecondary).tracking(2).padding(.top, 4)

                // Minimal HR status only (user-facing)
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

                Spacer()

                // Controls: stop / pause-play
                HStack(spacing: 30) {
                    Button { viewModel.stopWorkout() } label: {
                        Image(systemName: "stop.fill").font(.system(size: 22, weight: .semibold)).foregroundColor(CoachiTheme.danger)
                            .frame(width: 56, height: 56).background(CoachiTheme.danger.opacity(0.15)).clipShape(Circle())
                    }

                    Button {
                        if viewModel.workoutState == .paused { viewModel.resumeWorkout() }
                        else { viewModel.pauseWorkout() }
                    } label: {
                        Image(systemName: viewModel.workoutState == .paused ? "play.fill" : "pause.fill")
                            .font(.system(size: 28, weight: .semibold)).foregroundColor(.white)
                            .frame(width: 70, height: 70).background(CoachiTheme.primaryGradient).clipShape(Circle())
                            .shadow(color: CoachiTheme.primary.opacity(0.3), radius: 15, y: 5)
                    }
                    .contentTransition(.symbolEffect(.replace))

                    // Talk to coach button
                    Button { viewModel.talkToCoachButtonPressed() } label: {
                        Image(systemName: "mic.fill").font(.system(size: 22, weight: .semibold)).foregroundColor(CoachiTheme.secondary)
                            .frame(width: 56, height: 56).background(CoachiTheme.secondary.opacity(0.15)).clipShape(Circle())
                    }

                    // Spotify quick-access (late-phase media UX, does not affect coaching logic)
                    Button { viewModel.handleSpotifyButtonTapped() } label: {
                        ZStack(alignment: .bottomTrailing) {
                            SpotifyLogoBadge(size: 48)
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
                .padding(.bottom, 10)

                HStack(spacing: 10) {
                    Button {
                        viewModel.coachingStyle = .minimal
                    } label: {
                        Text("Less coaching")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(viewModel.coachingStyle == .minimal ? .white : CoachiTheme.textSecondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .fill(viewModel.coachingStyle == .minimal ? CoachiTheme.primary : CoachiTheme.surface)
                            )
                    }
                    .buttonStyle(.plain)

                    Button {
                        viewModel.coachingStyle = .motivational
                    } label: {
                        Text("More coaching")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(viewModel.coachingStyle == .motivational ? .white : CoachiTheme.textSecondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .fill(viewModel.coachingStyle == .motivational ? CoachiTheme.primary : CoachiTheme.surface)
                            )
                    }
                    .buttonStyle(.plain)
                }
                .padding(.bottom, 34)
            }

            // Diagnostics overlay (long-press orb to toggle)
            if showDiagnostics {
                VStack {
                    AudioDiagnosticOverlayView(isPresented: $showDiagnostics)
                        .transition(.move(edge: .top).combined(with: .opacity))
                        .padding(.top, 60)
                    Spacer()
                }
            }
        }
    }

    private var hrStatusText: String {
        if viewModel.hrIsReliable, let heartRate = viewModel.heartRate {
            return "HR \(heartRate) bpm"
        }
        return L10n.current == .no ? "HR IKKE TILKOBLET" : "HR NOT CONNECTED"
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
