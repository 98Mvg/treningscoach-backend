//
//  FeaturesPageView.swift
//  TreningsCoach
//
//  Onboarding step 3: Feature highlights carousel
//

import SwiftUI

struct FeaturesPageView: View {
    let onContinue: () -> Void
    @State private var currentPage = 0
    @State private var appeared = false

    private let features: [(icon: String, title: String, description: String)] = [
        ("waveform", L10n.realTimeCoaching, L10n.current == .no ? "AI-coachen lytter og gir tilbakemeldinger i sanntid" : "AI coach listens and gives real-time feedback"),
        ("chart.bar.fill", L10n.trackProgress, L10n.current == .no ? "Folg med paa treningsfremgang over tid" : "Track your workout progress over time"),
        ("person.fill", L10n.personalTouch, L10n.current == .no ? "Velg din coach-personlighet" : "Choose your coach personality")
    ]

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            TabView(selection: $currentPage) {
                ForEach(0..<features.count, id: \.self) { index in
                    VStack(spacing: 24) {
                        Image(systemName: features[index].icon)
                            .font(.system(size: 60, weight: .light))
                            .foregroundStyle(CoachiTheme.primaryGradient)

                        Text(features[index].title)
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)

                        Text(features[index].description)
                            .font(.system(size: 16))
                            .foregroundColor(CoachiTheme.textSecondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 40)
                    }
                    .tag(index)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .always))
            .frame(height: 300)
            .opacity(appeared ? 1 : 0)

            Spacer()

            Button(action: onContinue) {
                Text(L10n.continueButton)
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
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }
}
