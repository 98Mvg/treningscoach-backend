import SwiftUI

struct WelcomePageView: View {
    @State private var logoVisible = false
    @State private var titleVisible = false
    @State private var buttonVisible = false

    let onContinue: () -> Void

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()
            ParticleBackgroundView(particleCount: 20)

            VStack(spacing: 0) {
                Spacer()

                // Logo
                CoachiLogoView(size: 120, animated: true)
                    .opacity(logoVisible ? 1 : 0)
                    .scaleEffect(logoVisible ? 1 : 0.5)
                    .padding(.bottom, 24)

                // App name
                Text(AppConfig.appName)
                    .font(.system(size: 40, weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .opacity(titleVisible ? 1 : 0)
                    .offset(y: titleVisible ? 0 : 20)

                // Tagline
                Text(AppConfig.appTagline)
                    .font(.system(size: 17, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .padding(.top, 8)
                    .opacity(titleVisible ? 1 : 0)
                    .offset(y: titleVisible ? 0 : 15)

                Spacer()
                Spacer()

                // CTA
                Button(action: onContinue) {
                    Text("Get Started")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40)
                .opacity(buttonVisible ? 1 : 0)
                .offset(y: buttonVisible ? 0 : 30)

                Spacer()
                    .frame(height: 60)
            }
        }
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.6).delay(0.3)) {
                logoVisible = true
            }
            withAnimation(.easeOut(duration: 0.6).delay(0.6)) {
                titleVisible = true
            }
            withAnimation(.spring(response: 0.6, dampingFraction: 0.75).delay(0.9)) {
                buttonVisible = true
            }
        }
    }
}

#Preview {
    WelcomePageView { }
}
