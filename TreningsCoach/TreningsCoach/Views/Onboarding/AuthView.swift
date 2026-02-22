//
//  AuthView.swift
//  TreningsCoach
//
//  Onboarding account step inspired by launch UX:
//  Apple/Google quick actions + email registration form.
//

import SwiftUI
import UIKit

struct AuthView: View {
    let onContinue: () -> Void
    @State private var appeared = false
    @State private var email = ""
    @State private var password = ""
    @State private var repeatPassword = ""
    @State private var acceptedTerms = false

    private var canRegisterWithEmail: Bool {
        let trimmed = email.trimmingCharacters(in: .whitespacesAndNewlines)
        return !trimmed.isEmpty && password.count >= 6 && password == repeatPassword && acceptedTerms
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                Spacer().frame(height: 24)

                Text(L10n.signIn)
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .opacity(appeared ? 1 : 0)

                VStack(spacing: 12) {
                    socialButton(title: L10n.registerWithApple, icon: "applelogo") {
                        onContinue()
                    }
                    socialButton(title: L10n.registerWithGoogle, icon: "g.circle.fill") {
                        onContinue()
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 24)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 16)

                HStack(spacing: 12) {
                    Rectangle()
                        .fill(CoachiTheme.textTertiary.opacity(0.35))
                        .frame(height: 1)
                    Text(L10n.or)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                    Rectangle()
                        .fill(CoachiTheme.textTertiary.opacity(0.35))
                        .frame(height: 1)
                }
                .padding(.horizontal, 24)
                .padding(.top, 20)

                VStack(alignment: .leading, spacing: 10) {
                    Text(L10n.signInSubtitle)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .padding(.bottom, 4)

                    onboardingInputField(
                        placeholder: L10n.emailAddress,
                        text: $email,
                        keyboard: .emailAddress,
                        contentType: .emailAddress
                    )

                    onboardingSecureInputField(
                        placeholder: L10n.passwordLabel,
                        text: $password,
                        contentType: .password
                    )

                    onboardingSecureInputField(
                        placeholder: L10n.repeatPasswordLabel,
                        text: $repeatPassword,
                        contentType: .newPassword
                    )

                    Button {
                        acceptedTerms.toggle()
                    } label: {
                        HStack(alignment: .top, spacing: 10) {
                            Image(systemName: acceptedTerms ? "checkmark.square.fill" : "square")
                                .font(.system(size: 18, weight: .medium))
                                .foregroundColor(acceptedTerms ? CoachiTheme.primary : CoachiTheme.textSecondary)
                                .padding(.top, 1)
                            Text(L10n.acceptTerms)
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .multilineTextAlignment(.leading)
                            Spacer(minLength: 0)
                        }
                    }
                    .buttonStyle(.plain)
                    .padding(.top, 2)

                    Button(action: onContinue) {
                        Text(L10n.register)
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(canRegisterWithEmail ? .white : CoachiTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                            .background(
                                canRegisterWithEmail
                                    ? AnyView(CoachiTheme.primaryGradient)
                                    : AnyView(Color.white.opacity(0.08))
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    }
                    .disabled(!canRegisterWithEmail)
                    .padding(.top, 4)

                    Button(action: onContinue) {
                        Text(L10n.alreadyHaveUser)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                    }
                }
                .padding(20)
                .background(CoachiTheme.surface.opacity(0.95))
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
                .padding(.horizontal, 18)
                .padding(.top, 18)
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 18)

                Spacer().frame(height: 30)
            }
        }
        .onTapGesture { hideKeyboard() }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private func socialButton(title: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 19, weight: .semibold))
                    .foregroundColor(.black)
                    .frame(width: 22)
                Text(title)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.black)
                Spacer()
            }
            .padding(.horizontal, 18)
            .frame(height: 54)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
    }

    private func onboardingInputField(
        placeholder: String,
        text: Binding<String>,
        keyboard: UIKeyboardType = .default,
        contentType: UITextContentType?
    ) -> some View {
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
            .font(.system(size: 16, weight: .medium))
            .foregroundColor(CoachiTheme.textPrimary)
            .keyboardType(keyboard)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .textContentType(contentType)
            .padding(.horizontal, 14)
            .frame(height: 50)
            .background(Color.white.opacity(0.04))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(Color.white.opacity(0.08), lineWidth: 1)
            )
    }

    private func onboardingSecureInputField(
        placeholder: String,
        text: Binding<String>,
        contentType: UITextContentType?
    ) -> some View {
        SecureField("", text: text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
            .font(.system(size: 16, weight: .medium))
            .foregroundColor(CoachiTheme.textPrimary)
            .textContentType(contentType)
            .padding(.horizontal, 14)
            .frame(height: 50)
            .background(Color.white.opacity(0.04))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(Color.white.opacity(0.08), lineWidth: 1)
            )
    }

    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
