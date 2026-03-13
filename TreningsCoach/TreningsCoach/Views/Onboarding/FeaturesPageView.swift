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
            titleNo: "Rolig coaching fra foerste oekt",
            titleEn: "Calm coaching from your first workout",
            bodyNo: "Coachi guider deg gjennom intervaller og rolige turer, med eller uten puls.",
            bodyEn: "Coachi guides intervals and easy runs, with or without heart rate.",
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
            titleNo: "Se framgang etter hver økt",
            titleEn: "See progress after every workout",
            bodyNo: "CoachScore gir deg et enkelt tall på kontroll, flyt og gjennomføring.",
            bodyEn: "CoachScore gives you one simple score for control, flow, and execution.",
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
            showsCoachScoreCard: false,
            presentationStyle: .intro,
            previewKind: .none
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
            showsCoachScoreCard: false,
            presentationStyle: .intro,
            previewKind: .none
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
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .ignoresSafeArea(edges: [.top, .bottom])
        .onAppear {
            if case .intro = mode {
                startAutoAdvance()
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
                    .font(.system(size: 32, weight: .bold, design: .default))
                    .foregroundColor(.white)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(width: textWidth, alignment: .leading)
                    .layoutPriority(1)

                Text(activePage.body(for: L10n.current))
                    .font(.system(size: 16, weight: .semibold))
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
        isNarrow: Bool,
        cardSideInset: CGFloat,
        ctaSideInset: CGFloat,
        topSpacing: CGFloat,
        bottomInset: CGFloat
    ) -> some View {
        let showcaseTextWidth = max(0.0, min(textWidth, isNarrow ? 288.0 : 328.0))

        return VStack(alignment: .leading, spacing: 0) {
            Color.clear.frame(height: max(topSpacing - 16, 120))

            VStack(alignment: .leading, spacing: 22) {
                Text(activePage.title(for: L10n.current))
                    .font(.system(size: isNarrow ? 31 : 34, weight: .semibold, design: .rounded))
                    .foregroundColor(.white)
                    .lineSpacing(3)
                    .multilineTextAlignment(.leading)
                    .frame(width: showcaseTextWidth, alignment: .leading)

                if !activePage.body(for: L10n.current).isEmpty {
                    Text(activePage.body(for: L10n.current))
                        .font(.body.weight(.medium))
                        .foregroundColor(.white.opacity(0.9))
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

    private func postAuthPages(displayName _: String) -> [IntroStoryPage] {
        [
            IntroStoryPage(
                imageName: "OnboardingBgOutdoor",
                icon: "figure.run",
                titleNo: "La oss starte med å bli litt bedre kjent med deg og regne ut kondisjonsalderen din.",
                titleEn: "Let's start by getting to know you a little better and estimate your fitness age.",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .fitnessAgePrompt
            ),
            IntroStoryPage(
                imageName: "OnboardingBgOutdoor",
                icon: "chart.line.uptrend.xyaxis",
                titleNo: "Vi kan finne ut hvor gammel kroppen din faktisk er.",
                titleEn: "We can estimate how old your body really feels.",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .fitnessAgeExample
            ),
            IntroStoryPage(
                imageName: "OnboardingBgOutdoor",
                icon: "waveform",
                titleNo: "Vi kan hjelpe deg med å forstå om du er aktiv nok til å holde deg sunn og frisk.",
                titleEn: "We can help you understand whether you are active enough to stay healthy and fit.",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: [],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .activityQuotient
            ),
            IntroStoryPage(
                imageName: "OnboardingBgOutdoor",
                icon: "applewatch.side.right",
                titleNo: "Coachi tilpasser coachingen med pulsklokke eller pustanalyse fra første økt.",
                titleEn: "Coachi adapts your coaching with a watch or breath analysis from your very first workout.",
                bodyNo: "",
                bodyEn: "",
                supplementalTitleNo: nil,
                supplementalTitleEn: nil,
                supplementalBodyNo: nil,
                supplementalBodyEn: nil,
                deviceTags: ["Apple Watch", "Garmin", "Polar", "Bluetooth HR"],
                showsCoachScoreCard: false,
                presentationStyle: .showcase,
                previewKind: .deviceSupport
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
            EmptyView()
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
        }
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
        .background(Color.white.opacity(0.13))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.white.opacity(0.2), lineWidth: 1)
        )
    }
}
