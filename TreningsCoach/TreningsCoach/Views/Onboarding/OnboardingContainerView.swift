//
//  OnboardingContainerView.swift
//  TreningsCoach
//
//  7-step onboarding: Welcome → Language → Features → Account → Setup → CoachScore Intro → Sensor Connect
//

import SwiftUI
import UIKit

enum OnboardingStep: Int {
    case welcome = 0
    case language = 1
    case features = 2
    case auth = 3
    case setup = 4
    case coachScoreIntro = 5
    case sensorConnect = 6
}

struct OnboardingContainerView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @State private var currentStep: OnboardingStep = .welcome
    @State private var pendingUserName: String = ""
    @State private var pendingTrainingLevel: String = "beginner"

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            Group {
                switch currentStep {
                case .welcome:
                    WelcomePageView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .language }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .language:
                    LanguageSelectionView { language in
                        L10n.set(language)
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .features }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .features:
                    FeaturesPageView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .auth }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .auth:
                    AuthView {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .setup }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .setup:
                    SetupPageView { name, level in
                        pendingUserName = name
                        pendingTrainingLevel = level
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .coachScoreIntro }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .coachScoreIntro:
                    CoachScoreIntroView(name: pendingUserName) {
                        withAnimation(AppConfig.Anim.transitionSpring) { currentStep = .sensorConnect }
                    }
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))

                case .sensorConnect:
                    SensorConnectOnboardingView(
                        onConnectNow: {
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                UIApplication.shared.open(url)
                            }
                            appViewModel.completeOnboarding(name: pendingUserName, level: pendingTrainingLevel)
                        },
                        onContinueWithoutSensor: {
                            appViewModel.completeOnboarding(name: pendingUserName, level: pendingTrainingLevel)
                        }
                    )
                    .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading)))
                }
            }
        }
        .animation(AppConfig.Anim.transitionSpring, value: currentStep.rawValue)
    }
}

struct SensorConnectOnboardingView: View {
    let onConnectNow: () -> Void
    let onContinueWithoutSensor: () -> Void
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 70)

            Image(systemName: "applewatch.radiowaves.left.and.right")
                .font(.system(size: 52, weight: .medium))
                .foregroundStyle(CoachiTheme.tealGradient)
                .opacity(appeared ? 1 : 0)

            Text(L10n.sensorConnectTitle)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
                .padding(.top, 22)
                .opacity(appeared ? 1 : 0)

            Text(L10n.sensorConnectBody)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 26)
                .padding(.top, 10)
                .opacity(appeared ? 1 : 0)

            Spacer()

            VStack(spacing: 12) {
                Button(action: onConnectNow) {
                    Text(L10n.sensorConnectPrimary)
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }

                Button(action: onContinueWithoutSensor) {
                    Text(L10n.sensorConnectSecondary)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .frame(maxWidth: .infinity)
                        .frame(height: 54)
                        .background(CoachiTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 16, style: .continuous)
                                .stroke(Color.white.opacity(0.08), lineWidth: 1)
                        )
                }
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 56)
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 20)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.55)) { appeared = true }
        }
    }
}

struct CoachScoreIntroView: View {
    let name: String
    let onContinue: () -> Void
    @State private var appeared = false

    private let sampleScore = 82

    var body: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 40)

            Text(L10n.coachScoreIntroHeadline)
                .font(.system(size: 34, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.horizontal, 24)
                .multilineTextAlignment(.leading)
                .frame(maxWidth: .infinity, alignment: .leading)
                .opacity(appeared ? 1 : 0)

            Text(
                String(
                    format: L10n.coachScoreIntroSubline,
                    displayName.isEmpty ? L10n.athlete : displayName
                )
            )
            .font(.system(size: 16, weight: .medium))
            .foregroundColor(CoachiTheme.textSecondary)
            .padding(.horizontal, 24)
            .padding(.top, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .opacity(appeared ? 1 : 0)

            VStack(spacing: 18) {
                Text(L10n.coachScoreLabel)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                ZStack {
                    Circle()
                        .stroke(CoachiTheme.textTertiary.opacity(0.25), lineWidth: 14)
                    Circle()
                        .trim(from: 0.0, to: Double(sampleScore) / 100.0)
                        .stroke(
                            LinearGradient(
                                colors: [CoachiTheme.secondary, CoachiTheme.success],
                                startPoint: .leading,
                                endPoint: .trailing
                            ),
                            style: StrokeStyle(lineWidth: 14, lineCap: .round)
                        )
                        .rotationEffect(.degrees(-90))
                    VStack(spacing: 6) {
                        Text("\(sampleScore)")
                            .font(.system(size: 44, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(L10n.coachScoreSolidLabel)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                }
                .frame(width: 190, height: 190)
                .frame(maxWidth: .infinity)

                VStack(alignment: .leading, spacing: 8) {
                    scoreDetailRow(text: L10n.coachScoreReasonZone)
                    scoreDetailRow(text: L10n.coachScoreReasonConsistency)
                    scoreDetailRow(text: L10n.coachScoreReasonRecovery)
                }
            }
            .padding(22)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
            .padding(.horizontal, 24)
            .padding(.top, 26)
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 24)

            Spacer()

            Button(action: onContinue) {
                Text(L10n.startTraining)
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(CoachiTheme.primaryGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 56)
            .opacity(appeared ? 1 : 0)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.55)) { appeared = true }
        }
    }

    private var displayName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func scoreDetailRow(text: String) -> some View {
        HStack(spacing: 10) {
            Circle()
                .fill(CoachiTheme.secondary)
                .frame(width: 8, height: 8)
            Text(text)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
            Spacer(minLength: 0)
        }
    }
}
