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
    @EnvironmentObject var authManager: AuthManager
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
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 16.0 : 20.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            // Cap bottom inset so keyboard safe-area growth does not shove content upward.
            let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer().frame(height: max(18.0, geo.safeAreaInsets.top + 8.0))

                    Text(L10n.signIn)
                        .font(.largeTitle.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .opacity(appeared ? 1 : 0)
                        .frame(width: contentWidth, alignment: .center)

                    VStack(spacing: 12) {
                        if AppConfig.Auth.appleSignInEnabled {
                            socialButton(title: L10n.registerWithApple, icon: "applelogo") {
                                Task {
                                    let signedIn = await authManager.signInWithApple()
                                    if signedIn {
                                        onContinue()
                                    }
                                }
                            }
                        }
                        if AppConfig.Auth.googleSignInEnabled {
                            socialButton(title: L10n.registerWithGoogle, icon: "g.circle.fill") {
                                Task {
                                    await authManager.signInWithGoogle()
                                    if authManager.isAuthenticated {
                                        onContinue()
                                    }
                                }
                            }
                        } else {
                            socialButton(
                                title: "\(L10n.registerWithGoogle) (\(L10n.comingSoon))",
                                icon: "g.circle.fill",
                                isEnabled: false
                            ) {}
                        }
                    }
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 24)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 16)

                    if let errorMessage = authManager.errorMessage, !errorMessage.isEmpty {
                        Text(errorMessage)
                            .font(.footnote.weight(.medium))
                            .foregroundColor(CoachiTheme.primary)
                            .multilineTextAlignment(.center)
                            .frame(width: contentWidth, alignment: .center)
                            .padding(.top, 10)
                    }

                    HStack(spacing: 12) {
                        Rectangle()
                            .fill(CoachiTheme.textTertiary.opacity(0.35))
                            .frame(height: 1)
                        Text(L10n.or)
                            .font(.subheadline.weight(.semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                        Rectangle()
                            .fill(CoachiTheme.textTertiary.opacity(0.35))
                            .frame(height: 1)
                    }
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 20)

                    VStack(alignment: .leading, spacing: 10) {
                        Text(L10n.signInSubtitle)
                            .font(.headline.weight(.semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .fixedSize(horizontal: false, vertical: true)
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
                                    .font(.title3.weight(.medium))
                                    .foregroundColor(acceptedTerms ? CoachiTheme.primary : CoachiTheme.textSecondary)
                                    .padding(.top, 1)
                                Text(L10n.acceptTerms)
                                    .font(.footnote.weight(.medium))
                                    .foregroundColor(CoachiTheme.textSecondary)
                                    .multilineTextAlignment(.leading)
                                    .fixedSize(horizontal: false, vertical: true)
                                Spacer(minLength: 0)
                            }
                        }
                        .buttonStyle(.plain)
                        .padding(.top, 2)

                        Button(action: onContinue) {
                            Text(L10n.register)
                                .font(.headline.weight(.bold))
                                .foregroundColor(canRegisterWithEmail ? .white : CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity)
                                .frame(height: 52)
                                .background(
                                    canRegisterWithEmail
                                        ? AnyView(CoachiTheme.primaryGradient)
                                        : AnyView(CoachiTheme.surfaceElevated.opacity(0.85))
                                )
                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                        .disabled(!canRegisterWithEmail)
                        .padding(.top, 4)

                        Button(action: onContinue) {
                            Text(L10n.alreadyHaveUser)
                                .font(.body.weight(.semibold))
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
                            .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
                    )
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 18)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 18)

                    Spacer().frame(height: bottomInset)
                }
                .frame(width: layoutWidth, alignment: .top)
                .frame(maxWidth: .infinity, alignment: .top)
            }
            .scrollBounceBehavior(.basedOnSize, axes: .vertical)
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .clipped()
        }
        .onTapGesture { hideKeyboard() }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private func socialButton(title: String, icon: String, isEnabled: Bool = true, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.title3.weight(.semibold))
                    .foregroundColor(isEnabled ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)
                    .frame(width: 22)
                Text(title)
                    .font(.body.weight(.bold))
                    .foregroundColor(isEnabled ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)
                Spacer()
            }
            .padding(.horizontal, 18)
            .frame(height: 54)
            .background(isEnabled ? CoachiTheme.surface : CoachiTheme.surfaceElevated.opacity(0.65))
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
        }
        .disabled(!isEnabled)
    }

    private func onboardingInputField(
        placeholder: String,
        text: Binding<String>,
        keyboard: UIKeyboardType = .default,
        contentType: UITextContentType?
    ) -> some View {
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
            .font(.body.weight(.medium))
            .foregroundColor(CoachiTheme.textPrimary)
            .keyboardType(keyboard)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .textContentType(contentType)
            .padding(.horizontal, 14)
            .frame(height: 50)
            .background(CoachiTheme.surfaceElevated.opacity(0.65))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
    }

    private func onboardingSecureInputField(
        placeholder: String,
        text: Binding<String>,
        contentType: UITextContentType?
    ) -> some View {
        SecureField("", text: text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
            .font(.body.weight(.medium))
            .foregroundColor(CoachiTheme.textPrimary)
            .textContentType(contentType)
            .padding(.horizontal, 14)
            .frame(height: 50)
            .background(CoachiTheme.surfaceElevated.opacity(0.65))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
    }

    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
