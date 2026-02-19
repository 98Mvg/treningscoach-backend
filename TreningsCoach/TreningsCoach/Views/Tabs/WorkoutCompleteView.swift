//
//  WorkoutCompleteView.swift
//  TreningsCoach
//
//  Post-workout summary screen
//

import SwiftUI

struct WorkoutCompleteView: View {
    @ObservedObject var viewModel: WorkoutViewModel
    @State private var checkmarkScale: CGFloat = 0
    @State private var contentVisible = false

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            VStack(spacing: 0) {
                Spacer()

                ZStack {
                    Circle().fill(CoachiTheme.success.opacity(0.15)).frame(width: 100, height: 100)
                    Image(systemName: "checkmark").font(.system(size: 44, weight: .bold)).foregroundColor(CoachiTheme.success)
                }
                .scaleEffect(checkmarkScale)

                Text(L10n.greatWorkout).font(.system(size: 28, weight: .bold)).foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 24).opacity(contentVisible ? 1 : 0)

                GlassCardView {
                    VStack(spacing: 20) {
                        VStack(spacing: 4) {
                            Text(L10n.duration).font(.system(size: 13, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
                            Text(viewModel.elapsedFormatted).font(.system(size: 40, weight: .light, design: .monospaced)).foregroundColor(CoachiTheme.primary)
                        }
                        Divider().overlay(CoachiTheme.textTertiary.opacity(0.3))
                        HStack(spacing: 0) {
                            SummaryStatItem(label: L10n.intenseLvl, value: viewModel.currentIntensity.displayName)
                            SummaryStatItem(label: viewModel.currentPhase.displayName, value: viewModel.currentPhase.displayName)
                            SummaryStatItem(label: L10n.selectCoach, value: viewModel.activePersonality.displayName)
                        }
                        Divider().overlay(CoachiTheme.textTertiary.opacity(0.3))
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Coach vibe")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(CoachiTheme.textTertiary)
                                .tracking(1.2)
                            Text(viewModel.coachScoreHeadline)
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .fixedSize(horizontal: false, vertical: true)
                            Text(viewModel.effortScoreSummaryLine)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(CoachiTheme.textPrimary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        Divider().overlay(CoachiTheme.textTertiary.opacity(0.3))
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Why")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(CoachiTheme.textTertiary)
                                .tracking(1.2)
                            ForEach(viewModel.zoneWhyBullets, id: \.self) { bullet in
                                Text("• \(bullet)")
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        Divider().overlay(CoachiTheme.textTertiary.opacity(0.3))
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Next time")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(CoachiTheme.textTertiary)
                                .tracking(1.2)
                            Text(viewModel.nextTimeAdvice)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(CoachiTheme.textPrimary)
                                .fixedSize(horizontal: false, vertical: true)
                            if !viewModel.recoveryLine.isEmpty {
                                Text(viewModel.recoveryLine)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        if let confidenceNote = viewModel.scoreConfidenceNote {
                            Text(confidenceNote)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(CoachiTheme.textTertiary)
                                .multilineTextAlignment(.center)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.horizontal, 30).padding(.top, 28).opacity(contentVisible ? 1 : 0).offset(y: contentVisible ? 0 : 20)

                Spacer()

                Button {
                    withAnimation(AppConfig.Anim.transitionSpring) { viewModel.resetWorkout() }
                } label: {
                    Text(L10n.done).font(.system(size: 17, weight: .bold)).foregroundColor(.white)
                        .frame(maxWidth: .infinity).frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40).opacity(contentVisible ? 1 : 0)

                Spacer().frame(height: 60)
            }
        }
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.5).delay(0.2)) { checkmarkScale = 1 }
            withAnimation(.easeOut(duration: 0.5).delay(0.5)) { contentVisible = true }
        }
    }
}

struct SummaryStatItem: View {
    let label: String
    let value: String
    var body: some View {
        VStack(spacing: 4) {
            Text(label).font(.system(size: 11, weight: .medium)).foregroundColor(CoachiTheme.textTertiary)
            Text(value).font(.system(size: 15, weight: .semibold)).foregroundColor(CoachiTheme.textPrimary)
        }
        .frame(maxWidth: .infinity)
    }
}
