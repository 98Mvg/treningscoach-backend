import SwiftUI

struct SetupPageView: View {
    @State private var name: String = ""
    @State private var selectedLevel: TrainingLevel = .intermediate
    @State private var appeared = false

    let onComplete: (String, TrainingLevel) -> Void

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()
                    .frame(height: 80)

                // Title
                Text("Set up your profile")
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .opacity(appeared ? 1 : 0)

                Text("Personalize your coaching experience")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .padding(.top, 8)
                    .opacity(appeared ? 1 : 0)

                // Name field
                VStack(alignment: .leading, spacing: 8) {
                    Text("What should we call you?")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(CoachiTheme.textSecondary)

                    TextField("Your name", text: $name)
                        .font(.system(size: 17))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .padding(.horizontal, 16)
                        .frame(height: 50)
                        .background(CoachiTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(CoachiTheme.textTertiary.opacity(0.3), lineWidth: 1)
                        )
                        .tint(CoachiTheme.primary)
                }
                .padding(.horizontal, 30)
                .padding(.top, 40)
                .opacity(appeared ? 1 : 0)

                // Training level
                VStack(alignment: .leading, spacing: 12) {
                    Text("Training level")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(CoachiTheme.textSecondary)

                    HStack(spacing: 10) {
                        ForEach(TrainingLevel.allCases) { level in
                            Button {
                                withAnimation(AppConfig.Anim.buttonSpring) {
                                    selectedLevel = level
                                }
                            } label: {
                                VStack(spacing: 8) {
                                    Image(systemName: level.icon)
                                        .font(.system(size: 22))
                                    Text(level.displayName)
                                        .font(.system(size: 13, weight: .semibold))
                                }
                                .foregroundColor(selectedLevel == level ? .white : CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                                .background(
                                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                                        .fill(selectedLevel == level ? AnyShapeStyle(CoachiTheme.primaryGradient) : AnyShapeStyle(CoachiTheme.surface))
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                                        .stroke(
                                            selectedLevel == level ? Color.clear : CoachiTheme.textTertiary.opacity(0.3),
                                            lineWidth: 1
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(.horizontal, 30)
                .padding(.top, 32)
                .opacity(appeared ? 1 : 0)

                Spacer()

                // Start button
                Button {
                    onComplete(name, selectedLevel)
                } label: {
                    HStack(spacing: 8) {
                        Text("Start Training")
                            .font(.system(size: 17, weight: .bold))
                        Image(systemName: "arrow.right")
                            .font(.system(size: 15, weight: .bold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(CoachiTheme.primaryGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40)
                .opacity(appeared ? 1 : 0)

                Spacer()
                    .frame(height: 60)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5).delay(0.15)) {
                appeared = true
            }
        }
    }
}

#Preview {
    SetupPageView { _, _ in }
}
