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
        GeometryReader { geo in
            let sidePadding = geo.size.width < 390 ? 20.0 : 24.0

            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer(minLength: max(20, geo.size.height * 0.08))

                    Text(L10n.aboutYou)
                        .font(.title.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .multilineTextAlignment(.center)
                        .opacity(appeared ? 1 : 0)

                    VStack(alignment: .leading, spacing: 8) {
                        Text(L10n.firstNameLabel)
                            .font(.subheadline.weight(.medium))
                            .foregroundColor(CoachiTheme.textSecondary)

                        TextField("", text: $firstName, prompt: Text(L10n.firstNamePlaceholder).foregroundColor(CoachiTheme.textTertiary))
                            .font(.body)
                            .foregroundColor(CoachiTheme.textPrimary)
                            .textInputAutocapitalization(.words)
                            .autocorrectionDisabled()
                            .textContentType(.givenName)
                            .padding(16)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12, style: .continuous)
                                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
                            )

                        Text(L10n.lastNameLabel)
                            .font(.subheadline.weight(.medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .padding(.top, 6)

                        TextField("", text: $lastName, prompt: Text(L10n.lastNamePlaceholder).foregroundColor(CoachiTheme.textTertiary))
                            .font(.body)
                            .foregroundColor(CoachiTheme.textPrimary)
                            .textInputAutocapitalization(.words)
                            .autocorrectionDisabled()
                            .textContentType(.familyName)
                            .padding(16)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12, style: .continuous)
                                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
                            )
                    }
                    .padding(.top, 24)
                    .opacity(appeared ? 1 : 0)

                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.trainingLevel)
                            .font(.subheadline.weight(.medium))
                            .foregroundColor(CoachiTheme.textSecondary)

                        HStack(spacing: 12) {
                            Image(systemName: "leaf.fill")
                                .font(.body)
                                .foregroundColor(CoachiTheme.success)
                                .frame(width: 34, height: 34)
                                .background(CoachiTheme.success.opacity(0.15))
                                .clipShape(Circle())

                            Text(L10n.beginnerAutoLevelLine)
                                .font(.footnote.weight(.medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .multilineTextAlignment(.leading)
                                .fixedSize(horizontal: false, vertical: true)
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
                    .padding(.top, 20)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 20)

                    Spacer(minLength: max(22, geo.size.height * 0.1))

                    Button {
                        let finalFirst = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
                        let finalLast = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
                        let combinedName = [finalFirst, finalLast]
                            .filter { !$0.isEmpty }
                            .joined(separator: " ")
                        onComplete(combinedName.isEmpty ? L10n.athlete : combinedName, "beginner")
                    } label: {
                        Text(L10n.continueButton)
                            .font(.headline.weight(.bold))
                            .foregroundColor(canContinue ? .white : CoachiTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                            .frame(minHeight: 56)
                            .background(
                                canContinue
                                    ? AnyView(CoachiTheme.primaryGradient)
                                    : AnyView(Color.white.opacity(0.08))
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                    .disabled(!canContinue)
                    .opacity(appeared ? 1 : 0)
                }
                .frame(minHeight: geo.size.height)
                .padding(.horizontal, sidePadding)
                .padding(.top, max(20, geo.safeAreaInsets.top + 4))
                .padding(.bottom, max(24, geo.safeAreaInsets.bottom + 8))
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }
}
