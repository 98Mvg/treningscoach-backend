//
//  WelcomePageView.swift
//  TreningsCoach
//
//  Onboarding step 1: Welcome with logo animation
//

import SwiftUI

struct WelcomePageView: View {
    let onContinue: () -> Void
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            CoachiLogoView(size: 120, animated: true)
                .opacity(appeared ? 1 : 0)

            Text(AppConfig.appName)
                .font(.system(size: 36, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.top, 24)
                .opacity(appeared ? 1 : 0)

            Text(AppConfig.appTagline)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .padding(.top, 8)
                .opacity(appeared ? 1 : 0)

            Spacer()

            Button(action: onContinue) {
                Text(L10n.getStarted)
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
            withAnimation(.easeOut(duration: 0.8).delay(0.2)) { appeared = true }
        }
    }
}
