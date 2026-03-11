//
//  AuthView.swift
//  TreningsCoach
//
//  Launch-safe account step:
//  Users must continue with Apple or passwordless email before onboarding can continue.
//

import SwiftUI
import UIKit

struct AuthView: View {
    @EnvironmentObject var authManager: AuthManager
    let onContinue: () -> Void

    @State private var appeared = false
    @State private var emailAddress = ""
    @State private var verificationCode = ""
    @State private var emailCodeRequested = false

    private var hasEnabledProviders: Bool {
        AppConfig.Auth.appleSignInEnabled || AppConfig.Auth.emailSignInEnabled
    }

    private var normalizedEmail: String {
        emailAddress.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private var canRequestEmailCode: Bool {
        AppConfig.Auth.emailSignInEnabled
            && normalizedEmail.contains("@")
            && normalizedEmail.contains(".")
            && !authManager.isLoading
    }

    private var canVerifyEmailCode: Bool {
        emailCodeRequested
            && verificationCode.trimmingCharacters(in: .whitespacesAndNewlines).count == 6
            && !authManager.isLoading
    }

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 16.0 : 20.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer().frame(height: max(renderHeight * 0.16, geo.safeAreaInsets.top + 22.0))

                    Text(L10n.signIn)
                        .font(.largeTitle.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .opacity(appeared ? 1 : 0)
                        .frame(width: contentWidth, alignment: .center)

                    Text(L10n.signInSubtitle)
                        .font(.body.weight(.medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .frame(width: contentWidth, alignment: .center)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, 12)
                        .opacity(appeared ? 1 : 0)
                        .offset(y: appeared ? 0 : 12)

                    Text(L10n.accountRequiredHint)
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(CoachiTheme.primary)
                        .multilineTextAlignment(.center)
                        .frame(width: contentWidth, alignment: .center)
                        .padding(.top, 12)
                        .opacity(appeared ? 1 : 0)

                    VStack(alignment: .leading, spacing: 12) {
                        authBenefitRow(icon: "chart.line.uptrend.xyaxis", text: L10n.authBenefitSaveHistory)
                        authBenefitRow(icon: "person.crop.circle.badge.checkmark", text: L10n.authBenefitSyncProfile)
                        authBenefitRow(icon: "envelope.badge", text: L10n.authBenefitAppleOrEmail)
                    }
                    .padding(18)
                    .background(CoachiTheme.surface.opacity(0.96))
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
                    )
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 20)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 14)

                    VStack(spacing: 12) {
                        if AppConfig.Auth.appleSignInEnabled {
                            socialButton(title: L10n.registerWithApple, icon: "applelogo", disabled: authManager.isLoading) {
                                Task {
                                    let signedIn = await authManager.signInWithApple()
                                    if signedIn {
                                        onContinue()
                                    }
                                }
                            }
                        }

                        if AppConfig.Auth.appleSignInEnabled && AppConfig.Auth.emailSignInEnabled {
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
                            .padding(.top, 4)
                        }

                        if AppConfig.Auth.emailSignInEnabled {
                            VStack(alignment: .leading, spacing: 12) {
                                Text(L10n.continueWithEmail)
                                    .font(.headline.weight(.semibold))
                                    .foregroundColor(CoachiTheme.textPrimary)

                                inputField(
                                    title: L10n.emailAddress,
                                    text: $emailAddress,
                                    keyboard: .emailAddress,
                                    textContentType: .emailAddress
                                )

                                if emailCodeRequested {
                                    inputField(
                                        title: L10n.emailCodeLabel,
                                        text: $verificationCode,
                                        keyboard: .numberPad,
                                        textContentType: .oneTimeCode
                                    )

                                    Text(L10n.emailCodeSentHint)
                                        .font(.footnote.weight(.medium))
                                        .foregroundColor(CoachiTheme.textSecondary)
                                        .fixedSize(horizontal: false, vertical: true)

                                    primaryActionButton(
                                        title: L10n.verifyEmailCode,
                                        disabled: !canVerifyEmailCode
                                    ) {
                                        Task {
                                            let signedIn = await authManager.signInWithEmail(
                                                email: normalizedEmail,
                                                code: verificationCode
                                            )
                                            if signedIn {
                                                onContinue()
                                            }
                                        }
                                    }
                                } else {
                                    primaryActionButton(
                                        title: L10n.sendEmailCode,
                                        disabled: !canRequestEmailCode
                                    ) {
                                        Task {
                                            let requested = await authManager.requestEmailSignInCode(email: normalizedEmail)
                                            if requested {
                                                emailCodeRequested = true
                                            }
                                        }
                                    }
                                }
                            }
                            .padding(20)
                            .background(CoachiTheme.surface.opacity(0.95))
                            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 22, style: .continuous)
                                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
                            )
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
                            .padding(.top, 14)
                    }

                    if !hasEnabledProviders {
                        Text(L10n.emailDeliveryUnavailable)
                            .font(.footnote.weight(.medium))
                            .foregroundColor(CoachiTheme.primary)
                            .multilineTextAlignment(.center)
                            .frame(width: contentWidth, alignment: .center)
                            .padding(.top, 14)
                    }

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
        .onChange(of: normalizedEmail) { _, _ in
            verificationCode = ""
            emailCodeRequested = false
        }
    }

    private func socialButton(title: String, icon: String, disabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.title3.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .frame(width: 22)
                Text(title)
                    .font(.body.weight(.bold))
                    .foregroundColor(CoachiTheme.textPrimary)
                Spacer()
                if disabled {
                    ProgressView()
                        .tint(CoachiTheme.primary)
                }
            }
            .padding(.horizontal, 18)
            .frame(height: 54)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
        }
        .disabled(disabled)
    }

    private func primaryActionButton(title: String, disabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Spacer()
                if authManager.isLoading {
                    ProgressView()
                        .tint(.white)
                } else {
                    Text(title)
                        .font(.headline.weight(.bold))
                        .foregroundColor(.white)
                }
                Spacer()
            }
            .frame(height: 52)
        }
        .background {
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(disabled ? AnyShapeStyle(CoachiTheme.textTertiary.opacity(0.55)) : AnyShapeStyle(CoachiTheme.primaryGradient))
        }
        .disabled(disabled)
    }

    private func inputField(
        title: String,
        text: Binding<String>,
        keyboard: UIKeyboardType,
        textContentType: UITextContentType?
    ) -> some View {
        TextField(title, text: text)
            .font(.body.weight(.semibold))
            .foregroundColor(CoachiTheme.textPrimary)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .padding(.horizontal, 16)
            .frame(height: 52)
            .background(CoachiTheme.surfaceElevated)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
    }

    private func authBenefitRow(icon: String, text: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.primary)
                .frame(width: 20)

            Text(text)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 0)
        }
    }

    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
