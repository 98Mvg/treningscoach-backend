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
    let supplementalTitleNo: String?
    let supplementalTitleEn: String?
    let supplementalBodyNo: String?
    let supplementalBodyEn: String?
    let deviceTags: [String]
    let showsCoachScoreCard: Bool

    func title(for language: AppLanguage) -> String {
        language == .no ? titleNo : titleEn
    }

    func body(for language: AppLanguage) -> String {
        language == .no ? bodyNo : bodyEn
    }

    func supplementalTitle(for language: AppLanguage) -> String? {
        language == .no ? supplementalTitleNo : supplementalTitleEn
    }

    func supplementalBody(for language: AppLanguage) -> String? {
        language == .no ? supplementalBodyNo : supplementalBodyEn
    }
}

struct FeaturesPageView: View {
    enum Mode {
        case intro
        case postAuthExplainer(displayName: String)
    }

    let mode: Mode
    let onPrimary: () -> Void
    let primaryTitle: String
    let onSecondary: (() -> Void)?
    let secondaryTitle: String?

    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    @State private var currentPage = 0
    @State private var autoAdvanceTask: Task<Void, Never>?

    private var pages: [IntroStoryPage] {
        switch mode {
        case .intro:
            return introPages
        case let .postAuthExplainer(displayName):
            return postAuthPages(displayName: displayName)
        }
    }

    private let introPages: [IntroStoryPage] = [
        IntroStoryPage(
            imageName: "IntroStory1",
            icon: "bolt.fill",
            titleNo: "Rolig coaching fra foerste oekt",
            titleEn: "Calm coaching from your first workout",
            bodyNo: "Coachi guider deg gjennom intervaller og rolige turer, med eller uten puls.",
            bodyEn: "Coachi guides intervals and easy runs, with or without heart rate.",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: false
        ),
        IntroStoryPage(
            imageName: "IntroStory2",
            icon: "chart.line.uptrend.xyaxis",
            titleNo: "Se framgang etter hver økt",
            titleEn: "See progress after every workout",
            bodyNo: "CoachScore gir deg et enkelt tall på kontroll, flyt og gjennomføring.",
            bodyEn: "CoachScore gives you one simple score for control, flow, and execution.",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: true
        ),
        IntroStoryPage(
            imageName: "IntroStory3",
            icon: "music.note",
            titleNo: "Korte cues. Mindre støy.",
            titleEn: "Short cues. Less noise.",
            bodyNo: "Du får tydelige beskjeder når det betyr noe, og ro når du bare skal løpe.",
            bodyEn: "You get clear cues when they matter, and quiet when you should just run.",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: false
        ),
        IntroStoryPage(
            imageName: "IntroStory4",
            icon: "applewatch.side.right",
            titleNo: "Kobles enkelt til pulsklokka di",
            titleEn: "Connect easily to your watch",
            bodyNo: "Apple Watch, Garmin, Polar og Bluetooth-pulsmålere gir mer presis live coaching.",
            bodyEn: "Apple Watch, Garmin, Polar, and Bluetooth heart-rate sensors give more precise live coaching.",
            supplementalTitleNo: "Ingen pulsklokke?",
            supplementalTitleEn: "No watch?",
            supplementalBodyNo: "Alt i orden! Du kan bli coachet pa pustanalyse.",
            supplementalBodyEn: "That is okay. Coachi can still guide you with breath analysis.",
            deviceTags: ["Apple Watch", "Garmin", "Polar", "Bluetooth HR"],
            showsCoachScoreCard: false
        ),
    ]

    private var activePage: IntroStoryPage {
        pages[max(0, min(pages.count - 1, currentPage))]
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
            let topSpacing: CGFloat = max(renderHeight * 0.22, safeAreaInsets.top + 28)
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
                        guard currentPage < pages.count - 1 else { return }
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

                if let supplementalTitle = activePage.supplementalTitle(for: L10n.current),
                   let supplementalBody = activePage.supplementalBody(for: L10n.current) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(supplementalTitle)
                            .font(.subheadline.weight(.bold))
                            .foregroundColor(.white)
                            .fixedSize(horizontal: false, vertical: true)

                        Text(supplementalBody)
                            .font(.subheadline.weight(.semibold))
                            .foregroundColor(.white.opacity(0.88))
                            .fixedSize(horizontal: false, vertical: true)

                        if !activePage.deviceTags.isEmpty {
                            deviceTagWrap(activePage.deviceTags)
                                .padding(.top, 4)
                        }
                    }
                    .padding(14)
                    .frame(width: textWidth, alignment: .leading)
                    .background(Color.white.opacity(0.12))
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(Color.white.opacity(0.18), lineWidth: 1)
                    )
                }

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
                    ForEach(0 ..< pages.count, id: \.self) { index in
                        Button {
                            withAnimation(.easeInOut(duration: 0.25)) {
                                currentPage = index
                            }
                        } label: {
                            Circle()
                                .fill(index == currentPage ? Color.white : Color.white.opacity(0.45))
                                .frame(width: 16, height: 16)
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

                Button(action: onPrimary) {
                    Text(primaryTitle)
                        .font(.headline.weight(.bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 54)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }

                if let secondaryTitle, let onSecondary {
                    Button(action: onSecondary) {
                        Text(secondaryTitle)
                            .font(.body.weight(.semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(minHeight: 48)
                            .fixedSize(horizontal: false, vertical: true)
                    }
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
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                if Task.isCancelled { return }
                await MainActor.run {
                    withAnimation(.easeInOut(duration: 0.28)) {
                        currentPage = (currentPage + 1) % max(pages.count, 1)
                    }
                }
            }
        }
    }

    private func postAuthPages(displayName: String) -> [IntroStoryPage] {
        let name = displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            ? (L10n.current == .no ? "deg" : "you")
            : displayName

        return [
            IntroStoryPage(
                imageName: "IntroStory1",
                icon: "figure.run",
                titleNo: "Vi guider \(name) gjennom oekten",
                titleEn: "We guide \(name) through the workout",
                bodyNo: "Coachi hjelper deg med intervaller, rolige turer og tydelige overganger uten at du trenger aa stirre paa skjermen.",
                bodyEn: "Coachi helps with intervals, easy runs, and clear transitions without making you stare at the screen.",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false
            ),
            IntroStoryPage(
                imageName: "IntroStory2",
                icon: "chart.line.uptrend.xyaxis",
                titleNo: "Etter hver oekt ser du fremgang",
                titleEn: "After every workout you see progress",
                bodyNo: "CoachScore oppsummerer kontroll, flyt og gjennomfoering i ett enkelt tall du kan bygge videre paa.",
                bodyEn: "CoachScore summarizes control, flow, and execution in one simple score you can build on.",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: true
            ),
            IntroStoryPage(
                imageName: "IntroStory3",
                icon: "waveform",
                titleNo: "Coachen sier bare det som betyr noe",
                titleEn: "The coach only says what matters",
                bodyNo: "Korte lydsignaler og tydelige cues hjelper deg aa holde fokus, tempo og pust uten unodig stoy.",
                bodyEn: "Short audio cues help you hold focus, pacing, and breathing without unnecessary noise.",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false
            ),
            IntroStoryPage(
                imageName: "IntroStory4",
                icon: "applewatch.side.right",
                titleNo: "Med eller uten pulsklokke fortsetter coaching",
                titleEn: "Coaching keeps going with or without a watch",
                bodyNo: "Apple Watch og pulssensorer gir mer presis live coaching. Hvis puls mangler, fortsetter Coachi paa struktur og pust.",
                bodyEn: "Apple Watch and heart-rate sensors make live coaching more precise. If heart rate is missing, Coachi keeps guiding from structure and breathing.",
                supplementalTitleNo: "Klar til aa sette opp profilen?",
                supplementalTitleEn: "Ready to set up your profile?",
                supplementalBodyNo: "Vi bruker svarene dine for aa treffe bedre paa intensitet, oppsummering og stemmecoaching fra foerste oekt.",
                supplementalBodyEn: "We use your answers to calibrate intensity, summaries, and voice coaching from your first workout.",
                deviceTags: ["Apple Watch", "Garmin", "Polar", "Bluetooth HR"],
                showsCoachScoreCard: false
            ),
        ]
    }

    private func deviceTagWrap(_ tags: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                ForEach(tags.prefix(2), id: \.self) { tag in
                    deviceTag(tag)
                }
            }

            if tags.count > 2 {
                HStack(spacing: 8) {
                    ForEach(tags.dropFirst(2), id: \.self) { tag in
                        deviceTag(tag)
                    }
                }
            }
        }
    }

    private func deviceTag(_ label: String) -> some View {
        HStack(spacing: 6) {
            if label == "Apple Watch" {
                Image(systemName: "applewatch.side.right")
                    .font(.caption.weight(.bold))
            } else if label == "Bluetooth HR" {
                Image(systemName: "dot.radiowaves.left.and.right")
                    .font(.caption.weight(.bold))
            }

            Text(label)
                .font(.caption.weight(.bold))
        }
        .foregroundColor(.white.opacity(0.95))
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.14))
        .clipShape(Capsule())
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
