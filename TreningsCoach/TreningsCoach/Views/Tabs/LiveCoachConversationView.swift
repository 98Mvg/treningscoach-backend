//
//  LiveCoachConversationView.swift
//  TreningsCoach
//
//  Isolated post-workout live voice modal.
//

import Combine
import SwiftUI
import UIKit

@MainActor
final class LiveCoachConversationViewModel: ObservableObject {
    @Published var showTextFallback = false

    let service: XAIRealtimeVoiceService
    let summaryContext: PostWorkoutSummaryContext
    let languageCode: String
    let userName: String

    private var hasAutoStarted = false
    private var cancellables = Set<AnyCancellable>()

    init(
        summaryContext: PostWorkoutSummaryContext,
        languageCode: String,
        userName: String
    ) {
        self.summaryContext = summaryContext
        self.languageCode = languageCode
        self.userName = userName
        self.service = XAIRealtimeVoiceService(
            summaryContext: summaryContext,
            languageCode: languageCode,
            userName: userName
        )

        service.objectWillChange
            .sink { [weak self] _ in
                self?.objectWillChange.send()
            }
            .store(in: &cancellables)
    }

    var transcriptEntries: [LiveCoachTranscriptEntry] {
        service.transcriptEntries
    }

    var isConnected: Bool {
        if case .connected = service.connectionState {
            return true
        }
        return false
    }

    var canUseTextFallback: Bool {
        service.canUseTextFallback
    }

    var failureMessage: String? {
        if case .failed(let message) = service.connectionState {
            return message
        }
        return service.lastErrorMessage
    }

    var statusLabel: String {
        switch service.connectionState {
        case .idle:
            return languageCode == "no" ? "Klar" : "Ready"
        case .preparing:
            return languageCode == "no" ? "Forbereder" : "Preparing"
        case .connecting:
            return languageCode == "no" ? "Kobler til" : "Connecting"
        case .connected:
            return languageCode == "no" ? "Live" : "Live"
        case .failed:
            return languageCode == "no" ? "Feilet" : "Failed"
        case .ended:
            return languageCode == "no" ? "Avsluttet" : "Ended"
        }
    }

    var statusTint: Color {
        switch service.connectionState {
        case .connected:
            return Color(hex: "67E8F9")
        case .failed:
            return Color.red.opacity(0.85)
        case .ended:
            return Color.white.opacity(0.55)
        default:
            return Color.white.opacity(0.75)
        }
    }

    var isConversationEnded: Bool {
        if case .ended = service.connectionState {
            return true
        }
        return false
    }

    var latestShareInsight: String? {
        let assistantText = service.transcriptEntries
            .reversed()
            .first(where: { $0.role == .assistant && !$0.isPartial })?
            .text

        guard let assistantText else { return nil }
        return Self.sanitizedShareInsight(from: assistantText)
    }

    func startIfNeeded() async {
        guard !hasAutoStarted else { return }
        hasAutoStarted = true
        await service.start()
    }

    func retry() async {
        await service.start()
    }

    func disconnect() async {
        await service.disconnect(reason: .user)
    }

    func shutdownIfNeeded() async {
        await service.disconnect(reason: .user)
    }

    func openTextFallback() {
        showTextFallback = true
        Task {
            _ = await BackendAPIService.shared.trackVoiceTelemetry(
                event: "voice_fallback_text_opened",
                metadata: summaryContext.telemetryMetadata()
            )
        }
    }

    static func sanitizedShareInsight(from raw: String) -> String? {
        let collapsed = raw
            .replacingOccurrences(of: "\n", with: " ")
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !collapsed.isEmpty else { return nil }

        let terminalCharacters = CharacterSet(charactersIn: ".!?")
        let firstSentence = collapsed.components(separatedBy: terminalCharacters).first?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let candidate = (firstSentence?.count ?? 0) >= 24 ? firstSentence! : collapsed
        guard candidate.count > 132 else { return candidate }

        let prefix = candidate.prefix(132)
        if let lastSpace = prefix.lastIndex(of: " ") {
            return String(prefix[..<lastSpace]) + "..."
        }
        return String(prefix) + "..."
    }
}

struct LiveCoachConversationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel: LiveCoachConversationViewModel

    init(summaryContext: PostWorkoutSummaryContext, languageCode: String, userName: String) {
        _viewModel = StateObject(
            wrappedValue: LiveCoachConversationViewModel(
                summaryContext: summaryContext,
                languageCode: languageCode,
                userName: userName
            )
        )
    }

    var body: some View {
        NavigationStack {
            ZStack {
                CoachiTheme.backgroundGradient.ignoresSafeArea()

                VStack(spacing: 18) {
                    headerCard
                    transcriptCard
                    if let failureMessage = viewModel.failureMessage, viewModel.canUseTextFallback {
                        failureCard(message: failureMessage)
                    }
                    if let insight = viewModel.latestShareInsight, viewModel.isConversationEnded {
                        PostWorkoutInsightShareSection(
                            summaryContext: viewModel.summaryContext,
                            languageCode: viewModel.languageCode,
                            insightText: insight
                        )
                    }
                    Spacer(minLength: 0)
                    actionBar
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 28)
            }
            .navigationTitle(viewModel.languageCode == "no" ? "Snakk med coach live" : "Talk to Coach Live")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(viewModel.languageCode == "no" ? "Lukk" : "Close") {
                        dismiss()
                        Task {
                            await viewModel.disconnect()
                        }
                    }
                    .foregroundStyle(Color.white.opacity(0.92))
                }
            }
        }
        .task {
            await viewModel.startIfNeeded()
        }
        .onDisappear {
            Task {
                await viewModel.shutdownIfNeeded()
            }
        }
        .sheet(isPresented: $viewModel.showTextFallback) {
            PostWorkoutTextCoachView(
                summaryContext: viewModel.summaryContext,
                languageCode: viewModel.languageCode,
                userName: viewModel.userName
            )
        }
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text(viewModel.languageCode == "no" ? "Rex live coach" : "Rex live coach")
                        .font(.system(size: 26, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.96))
                    Text(viewModel.languageCode == "no"
                         ? "Denne modusen er isolert fra selve treningsmotoren og fokuserer bare pa oppsummeringen av den siste okten."
                         : "This mode is isolated from the workout runtime and only uses the summary from the workout you just finished.")
                        .font(.system(size: 14, weight: .regular))
                        .foregroundStyle(Color.white.opacity(0.74))
                }
                Spacer()
                statusPill
            }

            HStack(spacing: 12) {
                metricChip(
                    title: viewModel.languageCode == "no" ? "Coach score" : "Coach score",
                    value: "\(viewModel.summaryContext.coachScore)"
                )
                metricChip(
                    title: viewModel.languageCode == "no" ? "Varighet" : "Duration",
                    value: viewModel.summaryContext.durationText
                )
                metricChip(
                    title: viewModel.languageCode == "no" ? "Turns" : "Turns",
                    value: "\(viewModel.service.turnCount)"
                )
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(Color.white.opacity(0.08))
                .overlay(
                    RoundedRectangle(cornerRadius: 28, style: .continuous)
                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                )
        )
    }

    private var statusPill: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(viewModel.statusTint)
                .frame(width: 9, height: 9)
            Text(viewModel.statusLabel.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.8)
                .foregroundStyle(Color.white.opacity(0.92))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            Capsule(style: .continuous)
                .fill(Color.black.opacity(0.26))
        )
    }

    private func metricChip(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title.uppercased())
                .font(.system(size: 10, weight: .semibold))
                .tracking(0.6)
                .foregroundStyle(Color.white.opacity(0.6))
            Text(value)
                .font(.system(size: 15, weight: .medium, design: .monospaced))
                .foregroundStyle(Color.white.opacity(0.94))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.white.opacity(0.06))
        )
    }

    private var transcriptCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text(viewModel.languageCode == "no" ? "Samtale" : "Conversation")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.94))
                Spacer()
                Text("\(viewModel.service.sessionDurationSeconds)s")
                    .font(.system(size: 13, weight: .medium, design: .monospaced))
                    .foregroundStyle(Color.white.opacity(0.72))
            }

            ScrollView {
                VStack(spacing: 12) {
                    ForEach(viewModel.transcriptEntries) { entry in
                        transcriptBubble(entry: entry)
                    }
                    if viewModel.transcriptEntries.isEmpty {
                        emptyTranscriptState
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(Color.black.opacity(0.22))
                .overlay(
                    RoundedRectangle(cornerRadius: 28, style: .continuous)
                        .stroke(Color.white.opacity(0.10), lineWidth: 1)
                )
        )
    }

    private var emptyTranscriptState: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(viewModel.languageCode == "no" ? "Venter pa den forste stemmen..." : "Waiting for the first voice turn...")
                .font(.system(size: 16, weight: .medium))
                .foregroundStyle(Color.white.opacity(0.84))
            Text(viewModel.languageCode == "no"
                 ? "Nar live-forbindelsen er oppe, blir transkripsjoner og coach-svar vist her."
                 : "Once the live connection is up, transcripts and coach replies will show here.")
                .font(.system(size: 13, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.68))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Color.white.opacity(0.04))
        )
    }

    private func transcriptBubble(entry: LiveCoachTranscriptEntry) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(roleLabel(for: entry.role))
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.7)
                .foregroundStyle(Color.white.opacity(0.58))
            Text(entry.text)
                .font(.system(size: 16, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.94))
            if entry.isPartial {
                Text(viewModel.languageCode == "no" ? "Svar genereres..." : "Generating response...")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(Color(hex: "67E8F9"))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(bubbleColor(for: entry.role))
        )
    }

    private func failureCard(message: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(viewModel.languageCode == "no" ? "Live voice kunne ikke fortsette" : "Live voice could not continue")
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(Color.white.opacity(0.96))
            Text(message)
                .font(.system(size: 14, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.78))
            HStack(spacing: 10) {
                Button(viewModel.languageCode == "no" ? "Prov igjen" : "Try Again") {
                    Task { await viewModel.retry() }
                }
                .buttonStyle(LiveVoicePrimaryButtonStyle())

                Button(viewModel.languageCode == "no" ? "Spors med tekst i stedet" : "Ask in Text Instead") {
                    viewModel.openTextFallback()
                }
                .buttonStyle(LiveVoiceSecondaryButtonStyle())
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.red.opacity(0.16))
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color.red.opacity(0.30), lineWidth: 1)
                )
        )
    }

    private var actionBar: some View {
        HStack(spacing: 12) {
            if viewModel.isConversationEnded {
                Button(viewModel.languageCode == "no" ? "Lukk" : "Close") {
                    dismiss()
                }
                .buttonStyle(LiveVoiceSecondaryButtonStyle())
            } else {
                Button(viewModel.languageCode == "no" ? "Avslutt samtalen" : "End Conversation") {
                    Task {
                        await viewModel.disconnect()
                    }
                }
                .buttonStyle(LiveVoiceSecondaryButtonStyle())

                if viewModel.canUseTextFallback {
                    Button(viewModel.languageCode == "no" ? "Spors med tekst i stedet" : "Ask in Text Instead") {
                        viewModel.openTextFallback()
                    }
                    .buttonStyle(LiveVoicePrimaryButtonStyle())
                }
            }
        }
    }

    private func roleLabel(for role: LiveCoachTranscriptRole) -> String {
        switch role {
        case .user:
            return viewModel.languageCode == "no" ? "DEG" : "YOU"
        case .assistant:
            return "REX"
        case .system:
            return viewModel.languageCode == "no" ? "SYSTEM" : "SYSTEM"
        }
    }

    private func bubbleColor(for role: LiveCoachTranscriptRole) -> Color {
        switch role {
        case .assistant:
            return Color(hex: "113042").opacity(0.86)
        case .user:
            return Color.white.opacity(0.08)
        case .system:
            return Color.black.opacity(0.22)
        }
    }
}

private struct TextCoachMessage: Identifiable {
    let id = UUID()
    let role: LiveCoachTranscriptRole
    let text: String
}

struct PostWorkoutTextCoachView: View {
    @Environment(\.dismiss) private var dismiss

    let summaryContext: PostWorkoutSummaryContext
    let languageCode: String
    let userName: String

    @State private var draft = ""
    @State private var isSending = false
    @State private var errorMessage: String?
    @State private var messages: [TextCoachMessage] = []

    private var latestShareInsight: String? {
        let assistantText = messages.reversed().first(where: { $0.role == .assistant })?.text
        guard let assistantText else { return nil }
        return LiveCoachConversationViewModel.sanitizedShareInsight(from: assistantText)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 14) {
                ScrollView {
                    VStack(spacing: 12) {
                        summaryCard
                        if let insight = latestShareInsight {
                            PostWorkoutInsightShareSection(
                                summaryContext: summaryContext,
                                languageCode: languageCode,
                                insightText: insight
                            )
                        }
                        ForEach(messages) { message in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(message.role == .assistant ? "COACH" : (languageCode == "no" ? "DEG" : "YOU"))
                                    .font(.system(size: 11, weight: .semibold))
                                    .tracking(0.7)
                                    .foregroundStyle(Color.white.opacity(0.58))
                                Text(message.text)
                                    .font(.system(size: 16, weight: .regular))
                                    .foregroundStyle(Color.white.opacity(0.94))
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(14)
                            .background(
                                RoundedRectangle(cornerRadius: 20, style: .continuous)
                                    .fill(message.role == .assistant ? Color(hex: "113042").opacity(0.86) : Color.white.opacity(0.08))
                            )
                        }
                    }
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundStyle(Color.red.opacity(0.85))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                HStack(alignment: .bottom, spacing: 10) {
                    TextField(
                        languageCode == "no" ? "Still et oppfolgingssporsmal" : "Ask a follow-up question",
                        text: $draft,
                        axis: .vertical
                    )
                    .textFieldStyle(.plain)
                    .padding(14)
                    .background(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .fill(Color.white.opacity(0.08))
                    )

                    Button(isSending ? "..." : (languageCode == "no" ? "Send" : "Send")) {
                        Task {
                            await sendQuestion()
                        }
                    }
                    .buttonStyle(LiveVoicePrimaryButtonStyle())
                    .disabled(isSending || draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
            .padding(20)
            .background(CoachiTheme.backgroundGradient.ignoresSafeArea())
            .navigationTitle(languageCode == "no" ? "Coach med tekst" : "Coach in Text")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(languageCode == "no" ? "Lukk" : "Close") {
                        dismiss()
                    }
                    .foregroundStyle(Color.white.opacity(0.92))
                }
            }
        }
    }

    private var summaryCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(languageCode == "no" ? "Oppsummering" : "Summary")
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(Color.white.opacity(0.92))
            Text(summaryContext.coachScoreSummaryLine)
                .font(.system(size: 14, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.76))
            Text("\(summaryContext.workoutLabel) • \(summaryContext.durationText) • \(summaryContext.finalHeartRateText)")
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .foregroundStyle(Color.white.opacity(0.68))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Color.black.opacity(0.20))
        )
    }

    private func sendQuestion() async {
        let question = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !question.isEmpty else { return }

        errorMessage = nil
        isSending = true
        draft = ""
        messages.append(TextCoachMessage(role: .user, text: question))

        do {
            let response = try await BackendAPIService.shared.talkToCoach(
                message: summaryContext.fallbackPrompt(for: question, languageCode: languageCode),
                language: languageCode,
                persona: "personal_trainer",
                userName: userName,
                responseMode: "qa",
                context: "chat",
                triggerSource: "button"
            )
            messages.append(TextCoachMessage(role: .assistant, text: response.text))
        } catch {
            errorMessage = error.localizedDescription
        }

        isSending = false
    }
}

private struct PostWorkoutInsightShareSection: View {
    let summaryContext: PostWorkoutSummaryContext
    let languageCode: String
    let insightText: String

    @State private var showSystemShareSheet = false
    @State private var shareSheetItems: [Any] = []
    @State private var copiedLink = false

    private var shareURL: URL {
        URL(string: AppConfig.Share.coachiWebsiteURLString)!
    }

    private var titleText: String {
        languageCode == "no" ? "Del coach-innsikt" : "Share coach insight"
    }

    private var helperText: String {
        languageCode == "no"
            ? "Kortet lages lokalt fra den siste coach-samtalen og er klart for story eller lenke."
            : "The card is generated locally from the latest coach conversation and is ready for story or link sharing."
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(titleText)
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Color.white.opacity(0.96))

            Text(helperText)
                .font(.system(size: 13, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.72))

            PostWorkoutInsightStoryCardView(
                summaryContext: summaryContext,
                languageCode: languageCode,
                insightText: insightText
            )
            .frame(maxWidth: .infinity)

            ViewThatFits(in: .horizontal) {
                HStack(spacing: 10) {
                    instagramButton
                    snapchatButton
                    tiktokButton
                    copyLinkButton
                }

                VStack(spacing: 10) {
                    instagramButton
                    HStack(spacing: 10) {
                        snapchatButton
                        tiktokButton
                    }
                    HStack(spacing: 10) {
                        copyLinkButton
                    }
                }
            }

            if copiedLink {
                Text(languageCode == "no" ? "Lenke kopiert." : "Link copied.")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color(hex: "A5F3EC"))
                    .transition(.opacity)
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.white.opacity(0.06))
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                )
        )
        .sheet(isPresented: $showSystemShareSheet) {
            ActivityShareSheet(activityItems: shareSheetItems)
        }
    }

    private var instagramButton: some View {
        Button("Instagram Story") {
            shareToInstagramStory()
        }
        .buttonStyle(LiveVoicePrimaryButtonStyle())
    }

    private var snapchatButton: some View {
        Button("Snapchat") {
            openGenericShareSheet(for: "snapchat")
        }
        .buttonStyle(LiveVoiceSecondaryButtonStyle())
    }

    private var tiktokButton: some View {
        Button("TikTok") {
            openGenericShareSheet(for: "tiktok")
        }
        .buttonStyle(LiveVoiceSecondaryButtonStyle())
    }

    private var copyLinkButton: some View {
        Button(languageCode == "no" ? "Kopier lenke" : "Copy Link") {
            UIPasteboard.general.url = shareURL
            withAnimation(.easeOut(duration: 0.2)) {
                copiedLink = true
            }
            Task {
                try? await Task.sleep(nanoseconds: 1_600_000_000)
                await MainActor.run {
                    withAnimation(.easeOut(duration: 0.2)) {
                        copiedLink = false
                    }
                }
            }
        }
        .buttonStyle(LiveVoiceSecondaryButtonStyle())
    }

    private func shareToInstagramStory() {
        guard let storyURL = URL(string: AppConfig.Share.instagramStoriesScheme),
              UIApplication.shared.canOpenURL(storyURL),
              let cardImage = renderedCardImage(),
              let stickerData = cardImage.pngData() else {
            openGenericShareSheet(for: "instagram_story")
            return
        }

        UIPasteboard.general.setItems(
            [[
                "com.instagram.sharedSticker.stickerImage": stickerData,
                "com.instagram.sharedSticker.contentURL": shareURL.absoluteString,
                "com.instagram.sharedSticker.backgroundTopColor": "#081225",
                "com.instagram.sharedSticker.backgroundBottomColor": "#112B44",
            ]],
            options: [.expirationDate: Date().addingTimeInterval(300)]
        )

        UIApplication.shared.open(storyURL)
    }

    private func openGenericShareSheet(for destination: String) {
        guard let cardImage = renderedCardImage() else {
            return
        }

        let caption = languageCode == "no"
            ? "Coachi-innsikt fra den siste okten • \(shareURL.absoluteString)"
            : "Coachi insight from the latest workout • \(shareURL.absoluteString)"

        shareSheetItems = [cardImage, caption, shareURL]
        showSystemShareSheet = true

        if destination == "snapchat",
           let snapchatURL = URL(string: AppConfig.Share.snapchatScheme),
           UIApplication.shared.canOpenURL(snapchatURL) {
            // The system share sheet exposes Snapchat when installed, without introducing the Creative Kit SDK.
        }
    }

    @MainActor
    private func renderedCardImage() -> UIImage? {
        let renderer = ImageRenderer(
            content: PostWorkoutInsightStoryCardView(
                summaryContext: summaryContext,
                languageCode: languageCode,
                insightText: insightText
            )
            .frame(width: 1080, height: 1920)
        )
        renderer.scale = 1
        return renderer.uiImage
    }
}

private struct PostWorkoutInsightStoryCardView: View {
    let summaryContext: PostWorkoutSummaryContext
    let languageCode: String
    let insightText: String

    private var durationLabel: String {
        languageCode == "no" ? "Varighet" : "Duration"
    }

    private var scoreLabel: String {
        languageCode == "no" ? "Coach score" : "Coaching Score"
    }

    private var insightLabel: String {
        languageCode == "no" ? "Coach insight" : "Coach insight"
    }

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "081225"), Color(hex: "0D2034"), Color(hex: "12324A")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 34) {
                HStack(alignment: .center, spacing: 16) {
                    ZStack {
                        Circle()
                            .fill(Color.white.opacity(0.12))
                            .frame(width: 96, height: 96)
                        Image(systemName: "figure.run")
                            .font(.system(size: 40, weight: .semibold))
                            .foregroundStyle(Color(hex: "A5F3EC"))
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        Text("COACHI")
                            .font(.system(size: 56, weight: .bold))
                            .tracking(2.6)
                            .foregroundStyle(Color.white.opacity(0.98))
                        Text(summaryContext.workoutLabel.uppercased())
                            .font(.system(size: 28, weight: .semibold))
                            .tracking(1.2)
                            .foregroundStyle(Color.white.opacity(0.72))
                    }
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text(scoreLabel.uppercased())
                        .font(.system(size: 28, weight: .semibold))
                        .tracking(1.1)
                        .foregroundStyle(Color.white.opacity(0.68))
                    Text("\(summaryContext.coachScore)")
                        .font(.system(size: 214, weight: .bold, design: .rounded))
                        .foregroundStyle(Color.white.opacity(0.98))
                    Text(summaryContext.coachScoreSummaryLine)
                        .font(.system(size: 34, weight: .medium))
                        .foregroundStyle(Color.white.opacity(0.86))
                }

                VStack(alignment: .leading, spacing: 16) {
                    Text(insightLabel.uppercased())
                        .font(.system(size: 26, weight: .semibold))
                        .tracking(1.0)
                        .foregroundStyle(Color(hex: "A5F3EC"))
                    Text(insightText)
                        .font(.system(size: 52, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.96))
                        .multilineTextAlignment(.leading)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(28)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 48, style: .continuous)
                        .fill(Color.white.opacity(0.09))
                        .overlay(
                            RoundedRectangle(cornerRadius: 48, style: .continuous)
                                .stroke(Color.white.opacity(0.14), lineWidth: 2)
                        )
                )

                HStack(spacing: 18) {
                    storyMetric(label: durationLabel, value: summaryContext.durationText)
                    storyMetric(label: scoreLabel, value: "\(summaryContext.coachScore)")
                }

                Spacer()

                Text("coachi.app")
                    .font(.system(size: 30, weight: .semibold))
                    .tracking(1.1)
                    .foregroundStyle(Color.white.opacity(0.72))
            }
            .padding(.horizontal, 72)
            .padding(.vertical, 96)
        }
        .aspectRatio(9.0 / 16.0, contentMode: .fit)
        .clipShape(RoundedRectangle(cornerRadius: 44, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 44, style: .continuous)
                .stroke(Color.white.opacity(0.12), lineWidth: 2)
        )
    }

    private func storyMetric(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(label.uppercased())
                .font(.system(size: 20, weight: .semibold))
                .tracking(0.8)
                .foregroundStyle(Color.white.opacity(0.60))
            Text(value)
                .font(.system(size: 34, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color.white.opacity(0.95))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(22)
        .background(
            RoundedRectangle(cornerRadius: 30, style: .continuous)
                .fill(Color.black.opacity(0.20))
        )
    }
}

private struct ActivityShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
        controller.excludedActivityTypes = [.assignToContact, .print]
        return controller
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

private struct LiveVoicePrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 15, weight: .semibold))
            .foregroundStyle(Color.black.opacity(0.84))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                Capsule(style: .continuous)
                    .fill(Color(hex: "A5F3EC").opacity(configuration.isPressed ? 0.72 : 0.96))
            )
    }
}

private struct LiveVoiceSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 15, weight: .semibold))
            .foregroundStyle(Color.white.opacity(0.92))
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                Capsule(style: .continuous)
                    .fill(Color.white.opacity(configuration.isPressed ? 0.08 : 0.04))
                    .overlay(
                        Capsule(style: .continuous)
                            .stroke(Color.white.opacity(0.16), lineWidth: 1)
                    )
            )
    }
}
