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

                // Checkmark
                ZStack {
                    Circle()
                        .fill(CoachiTheme.success.opacity(0.15))
                        .frame(width: 100, height: 100)

                    Image(systemName: "checkmark")
                        .font(.system(size: 44, weight: .bold))
                        .foregroundColor(CoachiTheme.success)
                }
                .scaleEffect(checkmarkScale)

                Text("Great Workout!")
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 24)
                    .opacity(contentVisible ? 1 : 0)

                // Summary card
                GlassCardView {
                    VStack(spacing: 20) {
                        // Duration
                        VStack(spacing: 4) {
                            Text("Duration")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                            Text(viewModel.elapsedFormatted)
                                .font(.system(size: 40, weight: .light, design: .monospaced))
                                .foregroundColor(CoachiTheme.primary)
                        }

                        Divider()
                            .overlay(CoachiTheme.textTertiary.opacity(0.3))

                        // Stats grid
                        HStack(spacing: 0) {
                            SummaryStatItem(label: "Intensity", value: viewModel.currentIntensity.displayName)
                            SummaryStatItem(label: "Phase", value: viewModel.currentPhase.displayName)
                            SummaryStatItem(label: "Coach", value: viewModel.activePersonality.displayName)
                        }
                    }
                }
                .padding(.horizontal, 30)
                .padding(.top, 28)
                .opacity(contentVisible ? 1 : 0)
                .offset(y: contentVisible ? 0 : 20)

                Spacer()

                // Done button
                Button {
                    withAnimation(AppConfig.Anim.transitionSpring) {
                        viewModel.resetWorkout()
                    }
                } label: {
                    Text("Done")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40)
                .opacity(contentVisible ? 1 : 0)

                Spacer()
                    .frame(height: 60)
            }
        }
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.5).delay(0.2)) {
                checkmarkScale = 1
            }
            withAnimation(.easeOut(duration: 0.5).delay(0.5)) {
                contentVisible = true
            }
        }
    }
}

struct SummaryStatItem: View {
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 4) {
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(CoachiTheme.textTertiary)
            Text(value)
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(CoachiTheme.textPrimary)
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    WorkoutCompleteView(viewModel: WorkoutViewModel())
}
