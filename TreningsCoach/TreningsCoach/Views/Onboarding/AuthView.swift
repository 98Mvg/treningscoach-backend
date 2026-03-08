//
//  AuthView.swift
//  TreningsCoach
//
//  Honest launch-safe account step:
//  Apple is the only exposed provider in Phase 1. Users can continue without an account.
//

import SwiftUI
import UIKit

struct AuthView: View {
    @EnvironmentObject var authManager: AuthManager
    let onContinue: () -> Void
    @State private var appeared = false

    private var hasEnabledProviders: Bool {
        AppConfig.Auth.appleSignInEnabled
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
                    Spacer().frame(height: max(18.0, geo.safeAreaInsets.top + 8.0))

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

                    VStack(alignment: .leading, spacing: 12) {
                        authBenefitRow(icon: "chart.line.uptrend.xyaxis", text: L10n.authBenefitSaveHistory)
                        authBenefitRow(icon: "person.crop.circle.badge.checkmark", text: L10n.authBenefitSyncProfile)
                        authBenefitRow(icon: "figure.run", text: L10n.authBenefitStartWithoutAccount)
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
                            socialButton(title: L10n.registerWithApple, icon: "applelogo") {
                                Task {
                                    let signedIn = await authManager.signInWithApple()
                                    if signedIn {
                                        onContinue()
                                    }
                                }
                            }
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

                    if hasEnabledProviders {
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
                    }

                    VStack(alignment: .leading, spacing: 12) {
                        Text(L10n.continueWithoutAccount)
                            .font(.headline.weight(.semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .fixedSize(horizontal: false, vertical: true)

                        Text(L10n.signInLaterHint)
                            .font(.footnote.weight(.medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .fixedSize(horizontal: false, vertical: true)

                        Button(action: onContinue) {
                            Text(L10n.continueWithoutAccount)
                                .font(.headline.weight(.bold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 52)
                                .background(CoachiTheme.primaryGradient)
                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                        .padding(.top, 4)
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

    private func socialButton(title: String, icon: String, action: @escaping () -> Void) -> some View {
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
