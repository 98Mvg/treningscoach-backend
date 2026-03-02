import SwiftUI

struct FeatureItem: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let description: String
    let color: Color
}

struct FeaturesPageView: View {
    let onContinue: () -> Void

    @State private var currentPage = 0
    @State private var appeared = false

    private let features = [
        FeatureItem(
            icon: "waveform.path.ecg",
            title: "Real-Time Coaching",
            description: "AI-powered voice feedback\nduring your workout",
            color: CoachiTheme.primary
        ),
        FeatureItem(
            icon: "chart.line.uptrend.xyaxis",
            title: "Track Progress",
            description: "See your improvement\nover time",
            color: CoachiTheme.secondary
        ),
        FeatureItem(
            icon: "person.wave.2",
            title: "Personal Touch",
            description: "Choose your coach\npersonality",
            color: CoachiTheme.accent
        )
    ]

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Feature carousel
                TabView(selection: $currentPage) {
                    ForEach(Array(features.enumerated()), id: \.element.id) { index, feature in
                        VStack(spacing: 24) {
                            Image(systemName: feature.icon)
                                .font(.system(size: 60, weight: .light))
                                .foregroundStyle(feature.color)
                                .frame(height: 80)

                            Text(feature.title)
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(CoachiTheme.textPrimary)

                            Text(feature.description)
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .multilineTextAlignment(.center)
                                .lineSpacing(4)
                        }
                        .tag(index)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .frame(height: 280)

                // Page dots
                HStack(spacing: 8) {
                    ForEach(0..<features.count, id: \.self) { index in
                        Circle()
                            .fill(index == currentPage ? CoachiTheme.primary : CoachiTheme.textTertiary)
                            .frame(width: 8, height: 8)
                            .animation(.easeInOut(duration: 0.2), value: currentPage)
                    }
                }
                .padding(.top, 20)

                Spacer()

                // Continue
                Button(action: onContinue) {
                    Text("Continue")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40)
                .opacity(appeared ? 1 : 0)

                Spacer()
                    .frame(height: 60)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5).delay(0.2)) {
                appeared = true
            }
        }
    }
}

#Preview {
    FeaturesPageView { }
}
