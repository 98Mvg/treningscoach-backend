//
//  AuthView.swift
//  TreningsCoach
//
//  Sign-in screen: Google, Facebook, Vipps
//

import SwiftUI

struct AuthView: View {
    @ObservedObject var authManager: AuthManager

    var body: some View {
        ZStack {
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                // Header
                VStack(spacing: 12) {
                    Image(systemName: "person.crop.circle.badge.plus")
                        .font(.system(size: 56))
                        .foregroundStyle(AppTheme.primaryAccent)

                    Text(L10n.signIn)
                        .font(.largeTitle.bold())
                        .foregroundStyle(AppTheme.textPrimary)

                    Text(L10n.signInSubtitle)
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                        .multilineTextAlignment(.center)
                }

                // Sign-in buttons
                VStack(spacing: 14) {
                    // Google
                    signInButton(
                        title: L10n.signInWithGoogle,
                        icon: "g.circle.fill",
                        backgroundColor: .white,
                        textColor: .black
                    ) {
                        Task { await authManager.signInWithGoogle() }
                    }

                    // Facebook
                    signInButton(
                        title: L10n.signInWithFacebook,
                        icon: "f.circle.fill",
                        backgroundColor: Color(hex: "1877F2"),
                        textColor: .white
                    ) {
                        Task { await authManager.signInWithFacebook() }
                    }

                    // Vipps
                    signInButton(
                        title: L10n.signInWithVipps,
                        icon: "v.circle.fill",
                        backgroundColor: Color(hex: "FF5B24"),
                        textColor: .white
                    ) {
                        Task { await authManager.signInWithVipps() }
                    }
                }
                .padding(.horizontal, 32)
                .disabled(authManager.isLoading)

                // Loading indicator
                if authManager.isLoading {
                    ProgressView()
                        .tint(AppTheme.primaryAccent)
                        .padding()
                }

                // Error message
                if let error = authManager.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(AppTheme.danger)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }

                Spacer()
                Spacer()
            }
        }
    }

    private func signInButton(
        title: String,
        icon: String,
        backgroundColor: Color,
        textColor: Color,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(textColor)

                Text(title)
                    .font(.body.weight(.semibold))
                    .foregroundStyle(textColor)

                Spacer()
            }
            .padding(16)
            .background(backgroundColor)
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }
}
