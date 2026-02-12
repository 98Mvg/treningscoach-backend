//
//  SetupPageView.swift
//  TreningsCoach
//
//  Onboarding step 4: Name + training level setup
//

import SwiftUI

struct SetupPageView: View {
    let onComplete: (String, String) -> Void
    @State private var name = ""
    @State private var selectedLevel = "intermediate"
    @State private var appeared = false

    private let levels = [
        ("beginner", L10n.current == .no ? "Nybegynner" : "Beginner", "leaf.fill"),
        ("intermediate", L10n.current == .no ? "Middels" : "Intermediate", "flame.fill"),
        ("advanced", L10n.current == .no ? "Avansert" : "Advanced", "bolt.fill")
    ]

    var body: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 60)

            Text(L10n.setupProfile)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .opacity(appeared ? 1 : 0)

            // Name field
            VStack(alignment: .leading, spacing: 8) {
                Text(L10n.whatToCallYou)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                TextField("", text: $name, prompt: Text(L10n.current == .no ? "Ditt navn" : "Your name").foregroundColor(CoachiTheme.textTertiary))
                    .font(.system(size: 17))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(16)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Color.white.opacity(0.06), lineWidth: 1))
            }
            .padding(.horizontal, 40).padding(.top, 32)
            .opacity(appeared ? 1 : 0)

            // Training level
            VStack(alignment: .leading, spacing: 12) {
                Text(L10n.trainingLevel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                ForEach(levels, id: \.0) { level in
                    Button {
                        withAnimation(AppConfig.Anim.buttonSpring) { selectedLevel = level.0 }
                    } label: {
                        HStack(spacing: 14) {
                            Image(systemName: level.2)
                                .font(.system(size: 18))
                                .foregroundColor(selectedLevel == level.0 ? CoachiTheme.primary : CoachiTheme.textTertiary)
                                .frame(width: 40, height: 40)
                                .background((selectedLevel == level.0 ? CoachiTheme.primary : CoachiTheme.textTertiary).opacity(0.15))
                                .clipShape(Circle())

                            Text(level.1)
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(selectedLevel == level.0 ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)

                            Spacer()

                            if selectedLevel == level.0 {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(CoachiTheme.primary)
                            }
                        }
                        .padding(14)
                        .background(selectedLevel == level.0 ? CoachiTheme.primary.opacity(0.1) : CoachiTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .stroke(selectedLevel == level.0 ? CoachiTheme.primary.opacity(0.5) : Color.white.opacity(0.06), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 40).padding(.top, 28)
            .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

            Spacer()

            Button {
                let finalName = name.trimmingCharacters(in: .whitespacesAndNewlines)
                onComplete(finalName.isEmpty ? L10n.athlete : finalName, selectedLevel)
            } label: {
                Text(L10n.startTraining)
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(CoachiTheme.primaryGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }
            .padding(.horizontal, 40)
            .opacity(appeared ? 1 : 0)

            Spacer().frame(height: 60)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }
}
