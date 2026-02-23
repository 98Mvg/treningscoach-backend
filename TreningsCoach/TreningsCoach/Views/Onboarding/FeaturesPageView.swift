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
        let showsCoachScoreCard: Bool

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
                titleNo: "Løp med coach i riktig pulssone",
                titleEn: "Run with a coach in the right HR zone",
                bodyNo: "Korte, tydelige råd i sanntid holder deg i riktig intensitet.",
                bodyEn: "Short, clear real-time coaching keeps your intensity on track.",
                showsCoachScoreCard: false
            ),
            IntroPage(
                imageName: "IntroStory2",
                icon: "chart.line.uptrend.xyaxis",
                titleNo: "Få CoachScore på sonekontroll",
                titleEn: "Get CoachScore from zone control",
                bodyNo: "Scoren viser hvor godt du holdt riktig pulssone gjennom økten.",
                bodyEn: "Your score shows how well you held the right HR zone.",
                showsCoachScoreCard: true
            ),
            IntroPage(
                imageName: "IntroStory3",
                icon: "music.note",
                titleNo: "Spotify i bakgrunnen mens du trener",
                titleEn: "Spotify in the background while you train",
                bodyNo: "Koble Spotify og behold flyten mens coachen guider.",
                bodyEn: "Connect Spotify and keep the flow while the coach guides you.",
                showsCoachScoreCard: false
            ),
            IntroPage(
                imageName: "IntroStory4",
                icon: "applewatch.side.right",
                titleNo: "Koble Apple Watch på sekunder",
                titleEn: "Connect Apple Watch in seconds",
                bodyNo: "Pulsklokke gir mer presis coaching og tryggere styring av intensitet.",
                bodyEn: "Apple Watch unlocks more precise heart-rate coaching and safer intensity control.",
                showsCoachScoreCard: false
            ),
        ]
    }

    private var activePage: IntroPage {
        let index = max(0, min(introPages.count - 1, currentPage))
        return introPages[index]
    }

    var body: some View {
        GeometryReader { geo in
            let isNarrow = geo.size.width < 390
            let titleSize: CGFloat = isNarrow ? 30 : 34
            let bodySize: CGFloat = isNarrow ? 15 : 16
            let sidePadding: CGFloat = isNarrow ? 14 : 16
            let ctaSidePadding: CGFloat = isNarrow ? 18 : 24
            let cardWidth = min(460, max(geo.size.width - (sidePadding * 2), 260))

            ZStack {
                TabView(selection: $currentPage) {
                    ForEach(Array(introPages.enumerated()), id: \.offset) { index, page in
                        ZStack {
                            Image(page.imageName)
                                .resizable()
                                .scaledToFill()
                                .frame(width: geo.size.width, height: geo.size.height)
                                .clipped()
                                .overlay(
                                    LinearGradient(
                                        colors: colorScheme == .dark
                                            ? [Color.black.opacity(0.48), CoachiTheme.primary.opacity(0.08), Color.black.opacity(0.62)]
                                            : [Color.black.opacity(0.3), CoachiTheme.primary.opacity(0.06), Color.black.opacity(0.56)],
                                        startPoint: .top,
                                        endPoint: .bottom
                                    )
                                )
                                .overlay(
                                    Color.black.opacity(colorScheme == .dark ? 0.08 : 0.06)
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
                            .fill(Color.black.opacity(0.28))
                            .overlay(
                                Capsule()
                                    .stroke(Color.white.opacity(0.22), lineWidth: 1)
                            )
                    )
                    .padding(.top, max(14, geo.safeAreaInsets.top + 8))

                    Spacer()

                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 8) {
                            Image(systemName: activePage.icon)
                                .font(.system(size: 13, weight: .bold))
                            Text("Coachi")
                                .font(.system(size: 13, weight: .bold))
                        }
                        .foregroundColor(.white.opacity(0.96))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(Color.white.opacity(0.16))
                        .clipShape(Capsule())

                        Text(activePage.title(for: L10n.current))
                            .font(.system(size: titleSize, weight: .bold))
                            .foregroundColor(.white)
                            .multilineTextAlignment(.leading)
                            .lineLimit(3)
                            .minimumScaleFactor(0.82)

                        Text(activePage.body(for: L10n.current))
                            .font(.system(size: bodySize, weight: .semibold))
                            .foregroundColor(.white.opacity(0.92))
                            .lineSpacing(2.5)
                            .multilineTextAlignment(.leading)
                            .lineLimit(4)
                            .minimumScaleFactor(0.88)

                        if activePage.showsCoachScoreCard {
                            CoachScorePreviewCard()
                                .padding(.top, 2)
                        }
                    }
                    .frame(width: cardWidth, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 18)
                    .background(
                        RoundedRectangle(cornerRadius: 24, style: .continuous)
                            .fill(Color.black.opacity(0.28))
                            .overlay(
                                RoundedRectangle(cornerRadius: 24, style: .continuous)
                                    .stroke(Color.white.opacity(0.18), lineWidth: 1)
                            )
                    )
                    .padding(.horizontal, sidePadding)

                    Spacer(minLength: 18)

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
                    .padding(.horizontal, ctaSidePadding)
                    .padding(.bottom, max(22, geo.safeAreaInsets.bottom + 8))
                }
            }
            .ignoresSafeArea()
        }
        .onReceive(autoAdvanceTimer) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                currentPage = (currentPage + 1) % introPages.count
            }
        }
    }
}

private struct CoachScorePreviewCard: View {
    var body: some View {
        HStack(spacing: 14) {
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.25), lineWidth: 6)
                Circle()
                    .trim(from: 0.0, to: 0.83)
                    .stroke(
                        LinearGradient(colors: [CoachiTheme.secondary, CoachiTheme.success], startPoint: .leading, endPoint: .trailing),
                        style: StrokeStyle(lineWidth: 6, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))

                VStack(spacing: 2) {
                    Text("83")
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.white)
                    Text("Score")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.white.opacity(0.82))
                }
            }
            .frame(width: 76, height: 76)

            VStack(alignment: .leading, spacing: 8) {
                Text(L10n.current == .no ? "God sonekontroll" : "Strong zone control")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                RoundedRectangle(cornerRadius: 99, style: .continuous)
                    .fill(LinearGradient(colors: [CoachiTheme.secondary, Color(hex: "FF7A59")], startPoint: .leading, endPoint: .trailing))
                    .frame(height: 8)
                    .overlay(alignment: .leading) {
                        Circle()
                            .fill(Color.white)
                            .frame(width: 10, height: 10)
                            .offset(x: 46)
                    }
            }
        }
        .padding(10)
        .background(Color.white.opacity(0.13))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.white.opacity(0.2), lineWidth: 1)
        )
    }
}
