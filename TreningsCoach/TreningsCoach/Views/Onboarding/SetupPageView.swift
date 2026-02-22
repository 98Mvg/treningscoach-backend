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
    @State private var appeared = false

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

            // Auto-progression intro
            VStack(alignment: .leading, spacing: 12) {
                Text(L10n.trainingLevel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                HStack(spacing: 14) {
                    Image(systemName: "leaf.fill")
                        .font(.system(size: 18))
                        .foregroundColor(CoachiTheme.success)
                        .frame(width: 40, height: 40)
                        .background(CoachiTheme.success.opacity(0.15))
                        .clipShape(Circle())

                    VStack(alignment: .leading, spacing: 2) {
                        Text(L10n.current == .no ? "Du starter som Nybegynner" : "You start as Beginner")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(
                            L10n.current == .no
                                ? "Nivået ditt går opp når du fullfører gode økter."
                                : "Your level goes up as you complete high-quality workouts."
                        )
                        .font(.system(size: 13))
                        .foregroundColor(CoachiTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(14)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
            }
            .padding(.horizontal, 40).padding(.top, 28)
            .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

            Spacer()

            Button {
                let finalName = name.trimmingCharacters(in: .whitespacesAndNewlines)
                onComplete(finalName.isEmpty ? L10n.athlete : finalName, "beginner")
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
