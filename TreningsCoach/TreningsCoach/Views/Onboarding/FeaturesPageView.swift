//
//  FeaturesPageView.swift
//  TreningsCoach
//
//  Intro carousel shown at first launch:
//  4 high-ROI value pages with register/login actions.
//

import SwiftUI

struct FeaturesPageView: View {
    let onRegister: () -> Void
    let onExistingUser: () -> Void

    @Environment(\.colorScheme) private var colorScheme
    @State private var currentPage = 0
    private let autoAdvanceTimer = Timer.publish(every: 7.0, on: .main, in: .common).autoconnect()

    private struct IntroPage {
        let imageName: String
        let icon: String
        let titleNo: String
        let titleEn: String
        let bodyNo: String
        let bodyEn: String

        func title(for language: AppLanguage) -> String {
            language == .no ? titleNo : titleEn
        }

        func body(for language: AppLanguage) -> String {
            language == .no ? bodyNo : bodyEn
        }
    }

    private var introPages: [IntroPage] {
        [
            IntroPage(
                imageName: "IntroStory1",
                icon: "bolt.fill",
                titleNo: "Hold riktig puls hele økten",
                titleEn: "Stay in the right HR zone",
                bodyNo: "Coachi er en sanntids coach som holder deg i riktig sone med korte, tydelige råd.",
                bodyEn: "Coachi is a real-time coach that keeps you in the right zone with short, clear guidance."
            ),
            IntroPage(
                imageName: "IntroStory2",
                icon: "chart.line.uptrend.xyaxis",
                titleNo: "Få CoachScore etter hver økt",
                titleEn: "Get CoachScore after every workout",
                bodyNo: "Scoren viser hvor godt du holdt pulsen i målsonen gjennom hele økten.",
                bodyEn: "Your score is based on how well you stayed in the right zone during the workout."
            ),
            IntroPage(
                imageName: "IntroStory3",
                icon: "music.note",
                titleNo: "Spotify + coaching i samme økt",
                titleEn: "Connect Spotify and stay in flow",
                bodyNo: "Spill musikken din i bakgrunnen mens coachen guider deg i sanntid.",
                bodyEn: "Play your music in the background while the coach guides you in real time."
            ),
            IntroPage(
                imageName: "IntroStory4",
                icon: "applewatch.side.right",
                titleNo: "Koble Apple Watch på sekunder",
                titleEn: "Connect Apple Watch in seconds",
                bodyNo: "Pulsklokke gir mer presis coaching og tryggere styring av intensitet.",
                bodyEn: "Apple Watch unlocks more precise heart-rate coaching and safer intensity control."
            ),
        ]
    }

    private var activePage: IntroPage {
        let index = max(0, min(introPages.count - 1, currentPage))
        return introPages[index]
    }

    var body: some View {
        ZStack {
            TabView(selection: $currentPage) {
                ForEach(Array(introPages.enumerated()), id: \.offset) { index, page in
                    ZStack {
                        Image(page.imageName)
                            .resizable()
                            .scaledToFill()
                            .saturation(colorScheme == .dark ? 0.95 : 1.08)
                            .contrast(colorScheme == .dark ? 1.04 : 0.98)
                            .ignoresSafeArea()
                            .overlay(
                                LinearGradient(
                                    colors: colorScheme == .dark
                                        ? [Color.black.opacity(0.56), CoachiTheme.primary.opacity(0.12), Color.black.opacity(0.58)]
                                        : [Color.black.opacity(0.35), CoachiTheme.primary.opacity(0.18), Color.black.opacity(0.44)],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                            .overlay(
                                LinearGradient(
                                    colors: [
                                        Color.white.opacity(colorScheme == .dark ? 0.02 : 0.12),
                                        Color.clear,
                                        Color.white.opacity(colorScheme == .dark ? 0.0 : 0.08),
                                    ],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                    }
                    .tag(index)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .never))

            VStack(spacing: 0) {
                HStack(spacing: 10) {
                    ForEach(Array(introPages.enumerated()), id: \.offset) { index, _ in
                        Button {
                            withAnimation(.easeInOut(duration: 0.25)) {
                                currentPage = index
                            }
                        } label: {
                            Circle()
                                .fill(index == currentPage ? Color.white : Color.white.opacity(0.45))
                                .frame(width: 8, height: 8)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    Capsule()
                        .fill(Color.black.opacity(0.26))
                        .overlay(
                            Capsule()
                                .stroke(Color.white.opacity(0.2), lineWidth: 1)
                        )
                )
                .padding(.top, 16)

                Spacer()

                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 8) {
                        Image(systemName: activePage.icon)
                            .font(.system(size: 13, weight: .bold))
                        Text(L10n.current == .no ? "Coachi" : "Coachi")
                            .font(.system(size: 13, weight: .bold))
                    }
                    .foregroundColor(.white.opacity(0.96))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(Color.white.opacity(0.16))
                    .clipShape(Capsule())

                    Text(activePage.title(for: L10n.current))
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.white)
                        .lineLimit(3)

                    Text(activePage.body(for: L10n.current))
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white.opacity(0.92))
                        .lineSpacing(3)
                        .lineLimit(4)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 24)
                .padding(.vertical, 18)
                .background(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .fill(Color.black.opacity(0.28))
                        .overlay(
                            RoundedRectangle(cornerRadius: 24, style: .continuous)
                                .stroke(Color.white.opacity(0.18), lineWidth: 1)
                        )
                )
                .padding(.horizontal, 18)

                Spacer(minLength: 20)

                VStack(spacing: 12) {
                    Button(action: onRegister) {
                        Text(L10n.current == .no ? "Registrer deg" : "Register")
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 54)
                            .background(CoachiTheme.primaryGradient)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }

                    Button(action: onExistingUser) {
                        Text(L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 28)
            }
        }
        .onReceive(autoAdvanceTimer) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                currentPage = (currentPage + 1) % introPages.count
            }
        }
    }
}
