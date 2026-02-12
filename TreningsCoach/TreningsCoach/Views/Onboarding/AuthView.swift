//
//  AuthView.swift
//  TreningsCoach
//
//  Sign-in screen: Google, Facebook, Vipps — Coachi theme
//

import SwiftUI

struct AuthView: View {
    @ObservedObject var authManager: AuthManager
    var onSkip: (() -> Void)? = nil
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            Image(systemName: "person.crop.circle.badge.plus")
                .font(.system(size: 56, weight: .light))
                .foregroundStyle(CoachiTheme.primaryGradient)
                .opacity(appeared ? 1 : 0)

            Text(L10n.signIn)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.top, 20)
                .opacity(appeared ? 1 : 0)

            Text(L10n.signInSubtitle)
                .font(.system(size: 15))
                .foregroundColor(CoachiTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.top, 8)
                .opacity(appeared ? 1 : 0)

            VStack(spacing: 12) {
                signInButton(title: L10n.signInWithGoogle, icon: "g.circle.fill", backgroundColor: .white, textColor: .black) {
                    Task { await authManager.signInWithGoogle() }
                }
                signInButton(title: L10n.signInWithFacebook, icon: "f.circle.fill", backgroundColor: Color(hex: "1877F2"), textColor: .white) {
                    Task { await authManager.signInWithFacebook() }
                }
                signInButton(title: L10n.signInWithVipps, icon: "v.circle.fill", backgroundColor: Color(hex: "FF5B24"), textColor: .white) {
                    Task { await authManager.signInWithVipps() }
                }
            }
            .padding(.horizontal, 40).padding(.top, 32)
            .disabled(authManager.isLoading)
            .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

            if authManager.isLoading {
                ProgressView().tint(CoachiTheme.primary).padding(.top, 16)
            }

            if let error = authManager.errorMessage {
                Text(error)
                    .font(.system(size: 13))
                    .foregroundColor(CoachiTheme.danger)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40).padding(.top, 12)
            }

            Spacer()

            if let onSkip = onSkip {
                Button(action: onSkip) {
                    Text(L10n.continueWithoutAccount)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                }
                .opacity(appeared ? 1 : 0)
            }

            Spacer().frame(height: 60)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private func signInButton(title: String, icon: String, backgroundColor: Color, textColor: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon).font(.title2).foregroundColor(textColor)
                Text(title).font(.system(size: 16, weight: .semibold)).foregroundColor(textColor)
                Spacer()
            }
            .padding(16)
            .background(backgroundColor)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
    }
}
