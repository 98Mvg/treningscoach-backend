//
//  FeaturesPageView.swift
//  TreningsCoach
//
//  Intro carousel shown at first launch:
//  4 high-ROI value pages with register/login actions.
//

import SwiftUI
import UIKit

private enum StoryPresentationStyle {
    case intro
    case showcase
}

private enum StoryPreviewKind {
    case none
    case fitnessAgePrompt
    case fitnessAgeExample
    case activityQuotient
    case deviceSupport
    case watchBPM
    case intensityBar
    case talkToCoach
}

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
    let presentationStyle: StoryPresentationStyle
    let previewKind: StoryPreviewKind

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
            titleNo: "Få veiledning av en coach live på øret",
            titleEn: "Get live guidance from a coach in your ear",
            bodyNo: "",
            bodyEn: "",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: false,
            presentationStyle: .intro,
            previewKind: .none
        ),
        IntroStoryPage(
            imageName: "IntroStory3",
            icon: "music.note",
            titleNo: "Coachen holder fokus på det viktige i økten",
            titleEn: "Your coach keeps focus on what matters in the workout",
            bodyNo: "",
            bodyEn: "",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: false,
            presentationStyle: .intro,
            previewKind: .none
        ),
        IntroStoryPage(
            imageName: "IntroStory2",
            icon: "chart.line.uptrend.xyaxis",
            titleNo: "Få en score av Coachen etter hver økt",
            titleEn: "Get a coach score after every workout",
            bodyNo: "",
            bodyEn: "",
            supplementalTitleNo: nil,
            supplementalTitleEn: nil,
            supplementalBodyNo: nil,
            supplementalBodyEn: nil,
            deviceTags: [],
            showsCoachScoreCard: true,
            presentationStyle: .intro,
            previewKind: .none
        ),
        IntroStoryPage(
            imageName: "IntroStory4",
            icon: "applewatch.side.right",
            titleNo: "Coachi kobles enkelt til pulsklokka di",
            titleEn: "Connect easily to your watch",
            bodyNo: "",
            bodyEn: "",
            supplementalTitleNo: "Ingen pulsklokke?",
            supplementalTitleEn: "No watch?",
            supplementalBodyNo: "Alt i orden! Du kan fortsatt bli coachet pa pustanalyse.",
            supplementalBodyEn: "That is okay. You can still be coached with breath analysis.",
            deviceTags: ["Apple Watch", "Garmin", "Fitbit", "Polar", "Withings", "Suunto"],
            showsCoachScoreCard: false,
            presentationStyle: .intro,
            previewKind: .none
        ),
    ]

    private var activePage: IntroStoryPage {
        pages[max(0, min(pages.count - 1, currentPage))]
    }

    private var backgroundGradientColors: [Color] {
        if activePage.presentationStyle == .showcase {
            return colorScheme == .dark
                ? [Color.clear, Color.clear, Color.black.opacity(0.44)]
                : [Color.clear, Color.clear, Color.black.opacity(0.34)]
        }

        return colorScheme == .dark
            ? [Color.black.opacity(0.48), CoachiTheme.primary.opacity(0.08), Color.black.opacity(0.62)]
            : [Color.black.opacity(0.3), CoachiTheme.primary.opacity(0.06), Color.black.opacity(0.56)]
    }

    private var backgroundDimOpacity: Double {
        if activePage.presentationStyle == .showcase {
            return 0.0
        }

        return colorScheme == .dark ? 0.08 : 0.06
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

            ZStack {
                // Background image: full screen, no clipping
                Image(activePage.imageName)
                    .resizable()
                    .scaledToFill()
                    .frame(width: renderWidth, height: renderHeight)
                    .clipped()
                    .overlay(
                        LinearGradient(
                            colors: backgroundGradientColors,
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .overlay(
                        Color.black.opacity(backgroundDimOpacity)
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
                            renderHeight: renderHeight,
                            isNarrow: isNarrow,
                            cardSideInset: cardSideInset,
                            cardContentInset: cardContentInset,
                            ctaSideInset: ctaSideInset,
                            topSpacing: topSpacing,
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
                        renderHeight: renderHeight,
                        isNarrow: isNarrow,
                        cardSideInset: cardSideInset,
                        cardContentInset: cardContentInset,
                        ctaSideInset: ctaSideInset,
                        topSpacing: topSpacing,
                        bottomInset: bottomInset
                    )
                    .frame(width: layoutWidth, height: renderHeight, alignment: .top)
                }
            }
            .frame(width: renderWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .ignoresSafeArea(edges: [.top, .bottom])
        .onAppear {
            if case .intro = mode {
                startAutoAdvance(intervalSeconds: 6)
            } else {
                autoAdvanceTask?.cancel()
                autoAdvanceTask = nil
            }
        }
        .onDisappear {
            autoAdvanceTask?.cancel()
            autoAdvanceTask = nil
        }
    }

    private func content(
        cardWidth: CGFloat,
        textWidth: CGFloat,
        renderHeight: CGFloat,
        isNarrow: Bool,
        cardSideInset: CGFloat,
        cardContentInset: CGFloat,
        ctaSideInset: CGFloat,
        topSpacing: CGFloat,
        bottomInset: CGFloat
    ) -> some View {
        Group {
            if activePage.presentationStyle == .intro {
                introContent(
                    cardWidth: cardWidth,
                    textWidth: textWidth,
                    cardSideInset: cardSideInset,
                    cardContentInset: cardContentInset,
                    ctaSideInset: ctaSideInset,
                    topSpacing: topSpacing,
                    bottomInset: bottomInset
                )
            } else {
                showcaseContent(
                    cardWidth: cardWidth,
                    textWidth: textWidth,
                    renderHeight: renderHeight,
                    isNarrow: isNarrow,
                    cardSideInset: cardSideInset,
                    ctaSideInset: ctaSideInset,
                    topSpacing: topSpacing,
                    bottomInset: bottomInset
                )
            }
        }
    }

    private func introContent(
        cardWidth: CGFloat,
        textWidth: CGFloat,
        cardSideInset: CGFloat,
        cardContentInset: CGFloat,
        ctaSideInset: CGFloat,
        topSpacing: CGFloat,
        bottomInset: CGFloat
    ) -> some View {
        VStack(spacing: 0) {
            Color.clear.frame(height: topSpacing)

            VStack(alignment: .leading, spacing: 12) {
                Text(activePage.title(for: L10n.current))
                    .font(.system(size: 32, weight: .bold, design: .default))
                    .foregroundColor(.white)
                    .shadow(color: Color.black.opacity(0.38), radius: 16, x: 0, y: 6)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(width: textWidth, alignment: .leading)
                    .layoutPriority(1)

                if !activePage.body(for: L10n.current).isEmpty {
                    Text(activePage.body(for: L10n.current))
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white.opacity(0.92))
                        .shadow(color: Color.black.opacity(0.28), radius: 12, x: 0, y: 4)
                        .lineSpacing(2.5)
                        .multilineTextAlignment(.leading)
                        .lineLimit(nil)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(width: textWidth, alignment: .leading)
                        .layoutPriority(1)
                }

                if !activePage.deviceTags.isEmpty {
                    deviceLogoGrid(activePage.deviceTags)
                        .frame(width: textWidth, alignment: .leading)
                        .padding(.top, 6)
                }

                if let supplementalTitle = activePage.supplementalTitle(for: L10n.current),
                   let supplementalBody = activePage.supplementalBody(for: L10n.current) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(supplementalTitle)
                            .font(.subheadline.weight(.bold))
                            .foregroundColor(.white)
                            .shadow(color: Color.black.opacity(0.28), radius: 10, x: 0, y: 3)
                            .fixedSize(horizontal: false, vertical: true)

                        Text(supplementalBody)
                            .font(.subheadline.weight(.semibold))
                            .foregroundColor(.white.opacity(0.88))
                            .shadow(color: Color.black.opacity(0.24), radius: 8, x: 0, y: 3)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.top, 4)
                    .frame(width: textWidth, alignment: .leading)
                }

                introPreviewCard()
                    .padding(.top, 2)
            }
            .dynamicTypeSize(.small ... .xxxLarge)
            .padding(.horizontal, cardContentInset)
            .padding(.vertical, 18)
            .frame(width: cardWidth, alignment: .leading)
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
        .contentShape(Rectangle())
        .simultaneousGesture(
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

    private func showcaseContent(
        cardWidth: CGFloat,
        textWidth: CGFloat,
        renderHeight: CGFloat,
        isNarrow: Bool,
        cardSideInset: CGFloat,
        ctaSideInset: CGFloat,
        topSpacing: CGFloat,
        bottomInset: CGFloat
    ) -> some View {
        let showcaseTextWidth = max(0.0, min(textWidth, isNarrow ? 288.0 : 328.0))
        let showcaseTopSpacing = activePage.body(for: L10n.current).isEmpty
            ? max(renderHeight * 0.25, topSpacing + 24)
            : max(topSpacing - 16, 120)

        return VStack(alignment: .leading, spacing: 0) {
            Color.clear.frame(height: showcaseTopSpacing)

            VStack(alignment: .leading, spacing: 22) {
                Text(activePage.title(for: L10n.current))
                    .font(.system(size: isNarrow ? 31 : 34, weight: .semibold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: Color.black.opacity(0.38), radius: 16, x: 0, y: 6)
                    .lineSpacing(3)
                    .multilineTextAlignment(.leading)
                    .frame(width: showcaseTextWidth, alignment: .leading)

                if !activePage.body(for: L10n.current).isEmpty {
                    Text(activePage.body(for: L10n.current))
                        .font(.body.weight(.medium))
                        .foregroundColor(.white.opacity(0.9))
                        .shadow(color: Color.black.opacity(0.28), radius: 12, x: 0, y: 4)
                        .frame(width: showcaseTextWidth, alignment: .leading)
                }

                showcasePreviewCard(width: min(cardWidth, isNarrow ? 320 : 360))
                    .padding(.top, 6)
            }
            .padding(.horizontal, cardSideInset)

            Spacer(minLength: 16)
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            HStack(spacing: 18) {
                Button(action: showcaseSecondaryAction) {
                    Image(systemName: "chevron.left")
                        .font(.title2.weight(.bold))
                        .foregroundColor(CoachiTheme.primary)
                        .frame(width: 74, height: 74)
                        .background(Color.white.opacity(0.97))
                        .clipShape(Circle())
                        .overlay(
                            Circle()
                                .stroke(CoachiTheme.primary.opacity(0.85), lineWidth: 2)
                        )
                }
                .buttonStyle(.plain)

                Spacer(minLength: 12)

                Button(action: showcasePrimaryAction) {
                    HStack(spacing: 14) {
                        Text(showcasePrimaryTitle)
                            .font(.title3.weight(.bold))
                        Image(systemName: "chevron.right")
                            .font(.title3.weight(.bold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 32)
                    .frame(height: 74)
                    .background(CoachiTheme.primaryGradient.opacity(0.96))
                    .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, ctaSideInset)
            .padding(.top, 10)
            .padding(.bottom, bottomInset)
        }
    }

    private func startAutoAdvance(intervalSeconds: UInt64 = 5) {
        autoAdvanceTask?.cancel()
        autoAdvanceTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: intervalSeconds * 1_000_000_000)
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
        let greeting = displayName.isEmpty
            ? (L10n.current == .no ? "Hei!" : "Hi!")
            : (L10n.current == .no ? "Hei, \(displayName)!" : "Hi, \(displayName)!")
        return [
            IntroStoryPage(
                imageName: "IntroStory1",
                icon: "hand.wave.fill",
                titleNo: greeting,
                titleEn: greeting,
                bodyNo: "La meg først forklare hvordan vi kan hjelpe deg.",
                bodyEn: "Let me first explain how we can help you.",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .none
            ),
            IntroStoryPage(
                imageName: "IntroStory1",
                icon: "applewatch.side.right",
                titleNo: "Jeg guider deg live med pulssoner",
                titleEn: "I guide you live using heart rate zones",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .watchBPM
            ),
            IntroStoryPage(
                imageName: "IntroStory2",
                icon: "heart.fill",
                titleNo: "Jeg motiverer og tilpasser økten dynamisk",
                titleEn: "I motivate you and adjust the workout dynamically",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .intensityBar
            ),
            IntroStoryPage(
                imageName: "IntroStory3",
                icon: "chart.line.uptrend.xyaxis",
                titleNo: "Du får en CoachScore etter hver økt",
                titleEn: "You get a CoachScore after each workout",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: true,
                presentationStyle: .showcase,
                previewKind: .none
            ),
            IntroStoryPage(
                imageName: "IntroStory4",
                icon: "bubble.left.and.bubble.right.fill",
                titleNo: "Etter økten kan vi snakke live",
                titleEn: "After the workout we can talk live",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .talkToCoach
            ),
        ]
    }

    private var showcasePrimaryTitle: String {
        if currentPage == pages.count - 1 {
            return primaryTitle
        }

        return L10n.current == .no ? "Neste" : "Next"
    }

    private func showcasePrimaryAction() {
        if currentPage < pages.count - 1 {
            withAnimation(.easeInOut(duration: 0.28)) {
                currentPage += 1
            }
        } else {
            onPrimary()
        }
    }

    private func showcaseSecondaryAction() {
        if currentPage > 0 {
            withAnimation(.easeInOut(duration: 0.28)) {
                currentPage -= 1
            }
        } else if let onSecondary {
            onSecondary()
        }
    }

    @ViewBuilder
    private func showcasePreviewCard(width: CGFloat) -> some View {
        switch activePage.previewKind {
        case .none:
            if activePage.showsCoachScoreCard {
                CoachScorePreviewCard()
                    .frame(width: width)
            } else {
                EmptyView()
            }
        case .fitnessAgePrompt:
            FitnessAgePromptCard()
                .frame(width: width)
        case .fitnessAgeExample:
            FitnessAgeExampleCard()
                .frame(width: width)
        case .activityQuotient:
            ActivityQuotientPreviewCard()
                .frame(width: width)
        case .deviceSupport:
            DeviceSupportPreviewCard(deviceTags: activePage.deviceTags)
                .frame(width: width)
        case .watchBPM:
            WatchBPMPreviewCard()
                .frame(width: width)
        case .intensityBar:
            IntensityBarPreviewCard()
                .frame(width: width)
        case .talkToCoach:
            TalkToCoachPreviewCard()
                .frame(width: width)
        }
    }

    @ViewBuilder
    private func introPreviewCard() -> some View {
        switch activePage.previewKind {
        case .watchBPM:
            WatchBPMPreviewCard()
        case .intensityBar:
            IntensityBarPreviewCard()
        case .talkToCoach:
            TalkToCoachPreviewCard()
        default:
            if activePage.showsCoachScoreCard {
                CoachScorePreviewCard()
            }
        }
    }

    private func deviceLogoGrid(_ tags: [String]) -> some View {
        let columns = [
            GridItem(.flexible(), spacing: 18, alignment: .leading),
            GridItem(.flexible(), spacing: 18, alignment: .leading),
        ]

        return LazyVGrid(columns: columns, alignment: .leading, spacing: 18) {
            ForEach(tags, id: \.self) { tag in
                deviceLogoWordmark(tag)
            }
        }
    }

    private func deviceLogoWordmark(_ label: String) -> some View {
        HStack(spacing: 8) {
            switch label {
            case "Apple Watch":
                Image(systemName: "apple.logo")
                    .font(.title3.weight(.bold))
                Text("WATCH")
                    .font(.system(size: 22, weight: .heavy, design: .rounded))
                    .tracking(0.6)
            case "Garmin":
                HStack(spacing: 4) {
                    Text("GARMIN")
                        .font(.system(size: 22, weight: .heavy, design: .rounded))
                        .tracking(0.8)
                    Image(systemName: "triangle.fill")
                        .font(.caption.weight(.bold))
                        .offset(y: -8)
                }
            case "Fitbit":
                HStack(spacing: 8) {
                    fitbitDots
                    Text("fitbit")
                        .font(.system(size: 20, weight: .medium, design: .rounded))
                }
            case "Polar":
                Text("POLAR")
                    .font(.system(size: 24, weight: .black, design: .rounded))
                    .italic()
                    .tracking(0.5)
            case "Withings":
                Text("WITHINGS")
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .tracking(1.2)
            case "Suunto":
                VStack(alignment: .leading, spacing: 2) {
                    Image(systemName: "triangle.fill")
                        .font(.caption2.weight(.bold))
                    Text("SUUNTO")
                        .font(.system(size: 22, weight: .heavy, design: .rounded))
                        .tracking(1.0)
                }
            default:
                Text(label.uppercased())
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .tracking(0.8)
            }
        }
        .foregroundColor(.white.opacity(0.96))
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var fitbitDots: some View {
        VStack(spacing: 3) {
            HStack(spacing: 3) {
                Circle().frame(width: 4, height: 4)
                Circle().frame(width: 4, height: 4)
            }
            HStack(spacing: 3) {
                Circle().frame(width: 4, height: 4)
                Circle().frame(width: 4, height: 4)
                Circle().frame(width: 4, height: 4)
            }
            HStack(spacing: 3) {
                Circle().frame(width: 4, height: 4)
                Circle().frame(width: 4, height: 4)
            }
        }
        .foregroundColor(.white.opacity(0.96))
    }
}

private struct FitnessAgePromptCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Din kondisjonsalder")
                .font(.title3.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)

            VStack(spacing: 10) {
                Text("?")
                    .font(.system(size: 56, weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.primary)

                Image(systemName: "triangle.fill")
                    .font(.title3.weight(.bold))
                    .foregroundColor(CoachiTheme.primary)
                    .offset(y: -10)

                FitnessAgeScaleView()
            }

            Text("Faktisk alder")
                .font(.title3.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)
                .frame(maxWidth: .infinity, alignment: .trailing)
        }
        .padding(22)
        .background(Color.white.opacity(0.96))
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}

private struct FitnessAgeExampleCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Din kondisjonsalder")
                .font(.title3.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)

            VStack(spacing: 10) {
                Text("48")
                    .font(.system(size: 62, weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.primary)

                Image(systemName: "triangle.fill")
                    .font(.title3.weight(.bold))
                    .foregroundColor(CoachiTheme.primary)
                    .offset(y: -12)

                FitnessAgeScaleView()
            }

            Text("Eksempel på kondisjonsalder")
                .font(.title3.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)
        }
        .padding(22)
        .background(Color.white.opacity(0.96))
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}

private struct FitnessAgeScaleView: View {
    var body: some View {
        ZStack(alignment: .leading) {
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [Color(hex: "6F56D9"), Color(hex: "9D8AF2"), Color(hex: "B9AEFF")],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 22)

            HStack {
                Spacer()
                    .frame(width: 96)
                Rectangle().fill(Color.white.opacity(0.75)).frame(width: 2, height: 32)
                Spacer()
                Rectangle().fill(Color.white.opacity(0.75)).frame(width: 2, height: 32)
                Spacer()
                    .frame(width: 96)
            }

            HStack {
                Text("40")
                Spacer()
                Text("50")
            }
            .font(.title3.weight(.medium))
            .foregroundColor(CoachiTheme.textSecondary)
            .padding(.horizontal, 28)
            .offset(y: -28)
        }
    }
}

private struct ActivityQuotientPreviewCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Din AQ")
                .font(.title3.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)

            HStack {
                Spacer()
                ZStack {
                    Circle()
                        .stroke(Color(hex: "E3E1E8"), lineWidth: 16)
                        .frame(width: 150, height: 150)

                    Circle()
                        .trim(from: 0.1, to: 0.72)
                        .stroke(
                            LinearGradient(
                                colors: [Color(hex: "D8C9FF"), Color(hex: "79D1C9")],
                                startPoint: .topTrailing,
                                endPoint: .bottomLeading
                            ),
                            style: StrokeStyle(lineWidth: 16, lineCap: .round)
                        )
                        .frame(width: 150, height: 150)
                        .rotationEffect(.degrees(-90))

                    VStack(spacing: 2) {
                        Text("52")
                            .font(.system(size: 50, weight: .bold, design: .rounded))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [Color(hex: "D8C9FF"), Color(hex: "79D1C9")],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                        Text("Totalt")
                            .font(.title3.weight(.semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                    }
                }
                Spacer()
            }
        }
        .padding(22)
        .background(Color.white.opacity(0.96))
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}

private struct DeviceSupportPreviewCard: View {
    let deviceTags: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Kobles til")
                .font(.title3.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)

            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 8) {
                    ForEach(deviceTags.prefix(2), id: \.self) { tag in
                        supportTag(tag)
                    }
                }

                HStack(spacing: 8) {
                    ForEach(deviceTags.dropFirst(2), id: \.self) { tag in
                        supportTag(tag)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Ingen pulsklokke?")
                    .font(.body.weight(.bold))
                    .foregroundColor(CoachiTheme.textPrimary)

                Text("Alt i orden! Coachi kan fortsatt coache deg på pustanalyse.")
                    .font(.body.weight(.medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(22)
        .background(Color.white.opacity(0.96))
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
    }

    private func supportTag(_ label: String) -> some View {
        HStack(spacing: 7) {
            if label == "Apple Watch" {
                Image(systemName: "applewatch.side.right")
                    .font(.caption.weight(.bold))
            } else if label == "Bluetooth HR" {
                Image(systemName: "dot.radiowaves.left.and.right")
                    .font(.caption.weight(.bold))
            } else {
                Circle()
                    .fill(CoachiTheme.primary.opacity(0.85))
                    .frame(width: 7, height: 7)
            }

            Text(label)
                .font(.caption.weight(.semibold))
        }
        .foregroundColor(CoachiTheme.textPrimary)
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color(hex: "F1EDFF"))
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
    }
}

// MARK: - Page 1: Apple Watch BPM Preview

private struct WatchBPMPreviewCard: View {
    var body: some View {
        HStack(spacing: 16) {
            // Watch face
            ZStack {
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color.black.opacity(0.85))
                    .frame(width: 80, height: 96)
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(Color.white.opacity(0.25), lineWidth: 2)
                    )

                VStack(spacing: 2) {
                    Text("BPM")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(.white.opacity(0.6))

                    Text("142")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(Color(hex: "FF3B5C"))

                    HStack(spacing: 3) {
                        Image(systemName: "heart.fill")
                            .font(.system(size: 8))
                            .foregroundColor(Color(hex: "FF3B5C"))
                        Text("Live Heart Rate")
                            .font(.system(size: 7, weight: .semibold))
                            .foregroundColor(.white.opacity(0.7))
                    }
                }
            }

            // Zone info
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(Color(hex: "FF3B5C"))
                        .frame(width: 8, height: 8)
                    Text(L10n.current == .no ? "Sone 4 — Hardt" : "Zone 4 — Hard")
                        .font(.subheadline.weight(.bold))
                        .foregroundColor(.white)
                }

                Text(L10n.current == .no ? "Hold intensiteten!" : "Hold the intensity!")
                    .font(.caption.weight(.semibold))
                    .foregroundColor(.white.opacity(0.8))

                // Mini zone bar
                HStack(spacing: 2) {
                    ForEach(0 ..< 5, id: \.self) { i in
                        RoundedRectangle(cornerRadius: 3, style: .continuous)
                            .fill(zoneColor(i))
                            .frame(height: 6)
                            .opacity(i == 3 ? 1.0 : 0.4)
                    }
                }
            }
        }
        .padding(12)
    }

    private func zoneColor(_ index: Int) -> Color {
        switch index {
        case 0: return Color(hex: "7BC8F6")
        case 1: return Color(hex: "4ADE80")
        case 2: return Color(hex: "FACC15")
        case 3: return Color(hex: "FF7A59")
        case 4: return Color(hex: "FF3B5C")
        default: return .white
        }
    }
}

// MARK: - Page 2: Intensity Bar Preview

private struct IntensityBarPreviewCard: View {
    private let labels = ["Rolig", "Moderat", "Hardt", "Maks"]
    private let labelsEn = ["Easy", "Moderate", "Hard", "Max"]

    var body: some View {
        VStack(spacing: 12) {
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text("152")
                    .font(.system(size: 38, weight: .bold, design: .rounded))
                    .foregroundColor(CoachiTheme.secondary)
                Text("bpm")
                    .font(.subheadline.weight(.bold))
                    .foregroundColor(CoachiTheme.secondary.opacity(0.8))
            }

            // Intensity bar
            ZStack(alignment: .leading) {
                GeometryReader { geo in
                    RoundedRectangle(cornerRadius: 6, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color(hex: "7BC8F6"),
                                    Color(hex: "4ADE80"),
                                    Color(hex: "FACC15"),
                                    Color(hex: "FF7A59"),
                                    Color(hex: "FF3B5C"),
                                ],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(height: 10)

                    // Needle indicator at ~75%
                    Image(systemName: "triangle.fill")
                        .font(.system(size: 10))
                        .foregroundColor(CoachiTheme.secondary)
                        .rotationEffect(.degrees(180))
                        .offset(x: geo.size.width * 0.72 - 5, y: -10)
                }
                .frame(height: 10)
            }
            .padding(.top, 4)

            // Labels
            HStack {
                ForEach(0 ..< 4, id: \.self) { i in
                    Text(L10n.current == .no ? labels[i] : labelsEn[i])
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.white.opacity(i == 2 ? 1.0 : 0.55))
                    if i < 3 { Spacer() }
                }
            }
        }
        .padding(14)
    }
}

// MARK: - Page 4: Talk to Coach Preview

private struct TalkToCoachPreviewCard: View {
    var body: some View {
        VStack(spacing: 14) {
            // Simulated chat bubbles
            HStack {
                Spacer()
                HStack(spacing: 8) {
                    Text(L10n.current == .no ? "Hvordan var økten min?" : "How was my workout?")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(CoachiTheme.primary.opacity(0.7))
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }

            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "waveform")
                        .font(.caption.weight(.bold))
                        .foregroundColor(CoachiTheme.secondary)
                    Text(L10n.current == .no ? "Du holdt sonene godt i dag..." : "You held your zones well today...")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Color.white.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                Spacer()
            }

            // Talk button
            HStack(spacing: 10) {
                Image(systemName: "mic.fill")
                    .font(.body.weight(.bold))
                    .foregroundColor(.white)
                Text(L10n.current == .no ? "Snakk med Coachi" : "Talk to Coachi")
                    .font(.subheadline.weight(.bold))
                    .foregroundColor(.white)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity)
            .background(CoachiTheme.primaryGradient.opacity(0.85))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .padding(14)
    }
}
