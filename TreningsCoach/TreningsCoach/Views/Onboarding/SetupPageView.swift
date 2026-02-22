//
//  SetupPageView.swift
//  TreningsCoach
//
//  Onboarding profile step: first/last name + beginner auto-leveling
//

import SwiftUI

struct SetupPageView: View {
    let onComplete: (String, String) -> Void
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var appeared = false

    private var canContinue: Bool {
        !firstName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: 60)

            Text(L10n.aboutYou)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .opacity(appeared ? 1 : 0)

            VStack(alignment: .leading, spacing: 8) {
                Text(L10n.firstNameLabel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                TextField("", text: $firstName, prompt: Text(L10n.firstNamePlaceholder).foregroundColor(CoachiTheme.textTertiary))
                    .font(.system(size: 17))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .textInputAutocapitalization(.words)
                    .padding(16)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(Color.white.opacity(0.06), lineWidth: 1)
                    )

                Text(L10n.lastNameLabel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .padding(.top, 6)

                TextField("", text: $lastName, prompt: Text(L10n.lastNamePlaceholder).foregroundColor(CoachiTheme.textTertiary))
                    .font(.system(size: 17))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .textInputAutocapitalization(.words)
                    .padding(16)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(Color.white.opacity(0.06), lineWidth: 1)
                    )
            }
            .padding(.horizontal, 40)
            .padding(.top, 28)
            .opacity(appeared ? 1 : 0)

            VStack(alignment: .leading, spacing: 12) {
                Text(L10n.trainingLevel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                HStack(spacing: 12) {
                    Image(systemName: "leaf.fill")
                        .font(.system(size: 16))
                        .foregroundColor(CoachiTheme.success)
                        .frame(width: 34, height: 34)
                        .background(CoachiTheme.success.opacity(0.15))
                        .clipShape(Circle())

                    Text(L10n.beginnerAutoLevelLine)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.leading)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 12)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
            }
            .padding(.horizontal, 40)
            .padding(.top, 24)
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 20)

            Spacer()

            Button {
                let finalFirst = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
                let finalLast = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
                let combinedName = [finalFirst, finalLast]
                    .filter { !$0.isEmpty }
                    .joined(separator: " ")
                onComplete(combinedName.isEmpty ? L10n.athlete : combinedName, "beginner")
            } label: {
                Text(L10n.continueButton)
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(canContinue ? .white : CoachiTheme.textSecondary)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(
                        canContinue
                            ? AnyView(CoachiTheme.primaryGradient)
                            : AnyView(Color.white.opacity(0.08))
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }
            .padding(.horizontal, 40)
            .disabled(!canContinue)
            .opacity(appeared ? 1 : 0)

            Spacer().frame(height: 60)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }
}
