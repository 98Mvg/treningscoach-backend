import SwiftUI

struct OnboardingContainerView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @State private var currentStep = 0

    var body: some View {
        ZStack {
            switch currentStep {
            case 0:
                WelcomePageView {
                    withAnimation(AppConfig.Anim.transitionSpring) {
                        currentStep = 1
                    }
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing).combined(with: .opacity),
                    removal: .move(edge: .leading).combined(with: .opacity)
                ))

            case 1:
                FeaturesPageView {
                    withAnimation(AppConfig.Anim.transitionSpring) {
                        currentStep = 2
                    }
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing).combined(with: .opacity),
                    removal: .move(edge: .leading).combined(with: .opacity)
                ))

            default:
                SetupPageView { name, level in
                    appViewModel.completeOnboarding(name: name, level: level)
                }
                .transition(.asymmetric(
                    insertion: .move(edge: .trailing).combined(with: .opacity),
                    removal: .move(edge: .leading).combined(with: .opacity)
                ))
            }
        }
    }
}

#Preview {
    OnboardingContainerView()
        .environmentObject(AppViewModel())
}
