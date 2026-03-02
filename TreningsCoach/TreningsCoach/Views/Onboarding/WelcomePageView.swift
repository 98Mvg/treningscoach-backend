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
        GeometryReader { geo in
            ScrollView(showsIndicators: false) {
                VStack(spacing: 24) {
                    Spacer(minLength: max(24, geo.size.height * 0.15))

                    CoachiLogoView(size: 120, animated: true)
                        .opacity(appeared ? 1 : 0)

                    Text(AppConfig.appName)
                        .font(.largeTitle.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .multilineTextAlignment(.center)
                        .opacity(appeared ? 1 : 0)

                    Text(AppConfig.appTagline)
                        .font(.body.weight(.medium))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .opacity(appeared ? 1 : 0)

                    Spacer(minLength: max(24, geo.size.height * 0.2))

                    Button(action: onContinue) {
                        Text(L10n.getStarted)
                            .font(.headline.weight(.bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(minHeight: 56)
                            .background(CoachiTheme.primaryGradient)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                    .opacity(appeared ? 1 : 0)
                }
                .frame(minHeight: geo.size.height)
                .padding(.horizontal, geo.size.width < 390 ? 20 : 24)
                .padding(.top, max(20, geo.safeAreaInsets.top + 4))
                .padding(.bottom, max(24, geo.safeAreaInsets.bottom + 8))
                .frame(width: geo.size.width, alignment: .top)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.8).delay(0.2)) { appeared = true }
        }
    }
}
