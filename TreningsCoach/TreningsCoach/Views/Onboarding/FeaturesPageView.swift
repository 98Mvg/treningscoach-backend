//
//  FeaturesPageView.swift
//  TreningsCoach
//
//  Intro carousel shown at first launch:
//  4 high-ROI value pages with register/login actions.
//

import SwiftUI
import UIKit

private struct IntroStoryPage {
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

struct FeaturesPageView: View {
    let onRegister: () -> Void
    let onExistingUser: () -> Void

    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    @State private var currentPage = 0
    @State private var autoAdvanceTask: Task<Void, Never>?

    private let introPages: [IntroStoryPage] = [
        IntroStoryPage(
            imageName: "IntroStory1",
            icon: "bolt.fill",
            titleNo: "Løp med coach i riktig pulssone",
            titleEn: "Run with a coach in the right HR zone",
            bodyNo: "La coachen hjelpe deg holde riktig puls",
            bodyEn: "Let the coach help you keep the right heart rate.",
            showsCoachScoreCard: false
        ),
        IntroStoryPage(
            imageName: "IntroStory2",
            icon: "chart.line.uptrend.xyaxis",
            titleNo: "Få Coach score på sonekontroll",
            titleEn: "Get Coach score from zone control",
            bodyNo: "Scoren viser hvor godt du holdt riktig pulssone gjennom økten.",
            bodyEn: "Your score shows how well you held the right HR zone.",
            showsCoachScoreCard: true
        ),
        IntroStoryPage(
            imageName: "IntroStory3",
            icon: "music.note",
            titleNo: "Spotify i bakgrunnen mens du trener",
            titleEn: "Spotify in the background while you train",
            bodyNo: "Koble Spotify og behold flyten mens coachen guider.",
            bodyEn: "Connect Spotify and keep the flow while the coach guides you.",
            showsCoachScoreCard: false
        ),
        IntroStoryPage(
            imageName: "IntroStory4",
            icon: "applewatch.side.right",
            titleNo: "Koble Apple Watch på sekunder",
            titleEn: "Connect Apple Watch in seconds",
            bodyNo: "Pulsklokke gir mer presis coaching og tryggere styring av intensitet.",
            bodyEn: "Apple Watch unlocks more precise heart-rate coaching and safer intensity control.",
            showsCoachScoreCard: false
        ),
    ]

    private var activePage: IntroStoryPage {
        introPages[max(0, min(introPages.count - 1, currentPage))]
    }

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let safeAreaInsets = geo.safeAreaInsets
            let horizontalSafeInset = max(safeAreaInsets.leading, safeAreaInsets.trailing)

            let isNarrow = layoutWidth < 390
            let cardSideInset: CGFloat = (isNarrow ? 14 : 16) + horizontalSafeInset
            let cardContentInset: CGFloat = isNarrow ? 16 : 20
            let ctaSideInset: CGFloat = (isNarrow ? 18 : 24) + horizontalSafeInset
            let cardWidth: CGFloat = max(0, layoutWidth - (cardSideInset * 2))
            let textWidth: CGFloat = max(0, cardWidth - (cardContentInset * 2))
            let topSpacing: CGFloat = max(20, safeAreaInsets.top + 12)
            let bottomInset: CGFloat = max(22, safeAreaInsets.bottom + 8)
            let needsVerticalScroll = renderHeight < 730 || dynamicTypeSize.isAccessibilitySize
            let introCardTopSpacing: CGFloat = topSpacing

            ZStack {
                Image(activePage.imageName)
                    .resizable()
                    .scaledToFill()
                    .frame(width: layoutWidth, height: renderHeight)
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

                Color.clear
                    .onAppear {
#if DEBUG
                        print(
                            "ONBOARD_LAYOUT "
                                + "render=\(Int(renderWidth)) "
                                + "device=\(Int(deviceWidth)) "
                                + "layout=\(Int(layoutWidth)) "
                                + "card=\(Int(cardWidth)) "
                                + "text=\(Int(textWidth))"
                        )
#endif
                    }

                if needsVerticalScroll {
                    ScrollView(.vertical, showsIndicators: false) {
                        content(
                            cardWidth: cardWidth,
                            textWidth: textWidth,
                            isNarrow: isNarrow,
                            cardSideInset: cardSideInset,
                            cardContentInset: cardContentInset,
                            ctaSideInset: ctaSideInset,
                            topSpacing: introCardTopSpacing,
                            bottomInset: bottomInset
                        )
                        .frame(maxWidth: .infinity, alignment: .top)
                    }
                    .scrollBounceBehavior(.basedOnSize, axes: .vertical)
                    .frame(width: layoutWidth, height: renderHeight, alignment: .top)
                } else {
                    content(
                        cardWidth: cardWidth,
                        textWidth: textWidth,
                        isNarrow: isNarrow,
                        cardSideInset: cardSideInset,
                        cardContentInset: cardContentInset,
                        ctaSideInset: ctaSideInset,
                        topSpacing: introCardTopSpacing,
                        bottomInset: bottomInset
                    )
                    .frame(width: layoutWidth, height: renderHeight, alignment: .top)
                }
            }
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 24).onEnded { value in
                    let horizontal = value.translation.width
                    let vertical = value.translation.height
                    guard abs(horizontal) > abs(vertical), abs(horizontal) > 44 else { return }

                    if horizontal < 0 {
                        guard currentPage < introPages.count - 1 else { return }
                        withAnimation(.easeInOut(duration: 0.25)) {
                            currentPage += 1
                        }
                    } else {
                        guard currentPage > 0 else { return }
                        withAnimation(.easeInOut(duration: 0.25)) {
                            currentPage -= 1
                        }
                    }
                }
            )
        }
        .ignoresSafeArea(edges: [.top, .bottom])
        .onAppear {
            startAutoAdvance()
        }
        .onDisappear {
            autoAdvanceTask?.cancel()
            autoAdvanceTask = nil
        }
    }

    private func content(
        cardWidth: CGFloat,
        textWidth: CGFloat,
        isNarrow: Bool,
        cardSideInset: CGFloat,
        cardContentInset: CGFloat,
        ctaSideInset: CGFloat,
        topSpacing: CGFloat,
        bottomInset: CGFloat
    ) -> some View {
        VStack(spacing: 0) {
            Color.clear.frame(height: topSpacing)

            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 8) {
                    Image(systemName: activePage.icon)
                        .font(.caption.weight(.bold))
                    Text("Coachi")
                        .font(.caption.weight(.bold))
                }
                .foregroundColor(.white.opacity(0.96))
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.white.opacity(0.16))
                .clipShape(Capsule())

                Text(activePage.title(for: L10n.current))
                    .font(.system(size: isNarrow ? 30 : 32, weight: .bold, design: .default))
                    .foregroundColor(.white)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(width: textWidth, alignment: .leading)
                    .layoutPriority(1)

                Text(activePage.body(for: L10n.current))
                    .font(.system(size: isNarrow ? 15 : 16, weight: .semibold))
                    .foregroundColor(.white.opacity(0.92))
                    .lineSpacing(2.5)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(width: textWidth, alignment: .leading)
                    .layoutPriority(1)

                if activePage.showsCoachScoreCard {
                    CoachScorePreviewCard()
                        .padding(.top, 2)
                }
            }
            .dynamicTypeSize(.small ... .xxxLarge)
            .padding(.horizontal, cardContentInset)
            .padding(.vertical, 18)
            .frame(width: cardWidth, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(Color.black.opacity(0.28))
                    .overlay(
                        RoundedRectangle(cornerRadius: 24, style: .continuous)
                            .stroke(Color.white.opacity(0.18), lineWidth: 1)
                    )
            )
            .padding(.horizontal, cardSideInset)

            Spacer(minLength: 18)

            VStack(spacing: 12) {
                HStack(spacing: 10) {
                    ForEach(0 ..< introPages.count, id: \.self) { index in
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

                Button(action: onRegister) {
                    Text(L10n.current == .no ? "Registrer deg" : "Register")
                        .font(.headline.weight(.bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 54)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }

                Button(action: onExistingUser) {
                    Text(L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account")
                        .font(.body.weight(.semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 48)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(.horizontal, ctaSideInset)
            .padding(.bottom, bottomInset)
        }
    }

    private func startAutoAdvance() {
        autoAdvanceTask?.cancel()
        autoAdvanceTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 7_000_000_000)
                if Task.isCancelled { return }
                await MainActor.run {
                    withAnimation(.easeInOut(duration: 0.28)) {
                        currentPage = (currentPage + 1) % introPages.count
                    }
                }
            }
        }
    }
}

private struct CoachScorePreviewCard: View {
    @ScaledMetric(relativeTo: .title2) private var scoreCircleSize: CGFloat = 76
    @ScaledMetric(relativeTo: .body) private var scoreRingWidth: CGFloat = 6
    @ScaledMetric(relativeTo: .caption) private var scoreGaugeHeight: CGFloat = 8
    @ScaledMetric(relativeTo: .caption) private var scoreMarkerSize: CGFloat = 10

    var body: some View {
        HStack(spacing: 14) {
            GamifiedCoachScoreRingView(
                score: 100,
                label: "Score",
                size: scoreCircleSize,
                lineWidth: scoreRingWidth,
                trackColor: Color.white.opacity(0.25),
                gradientColors: [Color.white.opacity(0.9), Color.white],
                valueColor: .white,
                labelColor: .white.opacity(0.82)
            )

            VStack(alignment: .leading, spacing: 8) {
                Text(L10n.current == .no ? "God sonekontroll" : "Strong zone control")
                    .font(.subheadline.weight(.bold))
                    .foregroundColor(.white)
                    .fixedSize(horizontal: false, vertical: true)

                RoundedRectangle(cornerRadius: 99, style: .continuous)
                    .fill(LinearGradient(colors: [CoachiTheme.secondary, Color(hex: "FF7A59")], startPoint: .leading, endPoint: .trailing))
                    .frame(height: scoreGaugeHeight)
                    .overlay(alignment: .leading) {
                        Circle()
                            .fill(Color.white)
                            .frame(width: scoreMarkerSize, height: scoreMarkerSize)
                            .offset(x: (scoreCircleSize * 0.6))
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
