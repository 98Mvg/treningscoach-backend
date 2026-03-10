//
//  XAIRealtimeVoiceService.swift
//  TreningsCoach
//
//  Isolated post-workout live voice mode using xAI Voice Agent.
//

@preconcurrency import AVFAudio
import Combine
import Foundation

enum LiveVoiceConnectionState: Equatable {
    case idle
    case preparing
    case connecting
    case connected
    case failed(String)
    case ended
}

enum LiveVoiceMicState: Equatable {
    case idle
    case requestingPermission
    case capturing
}

enum LiveVoiceDisconnectReason: String {
    case user
    case timeLimit = "time_limit"
    case socketClosed = "socket_closed"
    case error
}

@MainActor
final class XAIRealtimeVoiceService: NSObject, ObservableObject {
    @Published private(set) var connectionState: LiveVoiceConnectionState = .idle
    @Published private(set) var micState: LiveVoiceMicState = .idle
    @Published private(set) var transcriptEntries: [LiveCoachTranscriptEntry] = []
    @Published private(set) var sessionDurationSeconds: Int = 0
    @Published private(set) var turnCount: Int = 0
    @Published private(set) var voiceSessionId: String?
    @Published private(set) var lastErrorMessage: String?

    private let apiService: BackendAPIService
    private let summaryContext: PostWorkoutSummaryContext
    private let languageCode: String
    private let userName: String

    private let playbackEngine = AVAudioEngine()
    private let playbackNode = AVAudioPlayerNode()
    private let playbackFormat = AVAudioFormat(
        commonFormat: .pcmFormatInt16,
        sampleRate: 24_000,
        channels: 1,
        interleaved: false
    )!

    private var playbackPrepared = false
    private var captureEngine: AVAudioEngine?
    private var captureConverter: AVAudioConverter?
    private var webSocketTask: URLSessionWebSocketTask?
    private var receiveTask: Task<Void, Never>?
    private var sessionTimerTask: Task<Void, Never>?
    private var sessionBootstrap: VoiceSessionBootstrap?
    private var didSendStartTelemetry = false
    private var hasConnectedSession = false
    private var assistantDraftID: UUID?

    init(
        apiService: BackendAPIService = .shared,
        summaryContext: PostWorkoutSummaryContext,
        languageCode: String,
        userName: String = ""
    ) {
        self.apiService = apiService
        self.summaryContext = summaryContext
        self.languageCode = languageCode
        self.userName = userName
        super.init()
    }

    func start() async {
        if case .failed = connectionState {
            await resetForRetry()
        } else if case .ended = connectionState {
            await resetForRetry()
        } else if case .idle = connectionState {
            // Normal fresh start.
        } else {
            return
        }

        connectionState = .preparing
        lastErrorMessage = nil
        transcriptEntries = []
        turnCount = 0
        sessionDurationSeconds = 0
        didSendStartTelemetry = false
        hasConnectedSession = false
        assistantDraftID = nil

        micState = .requestingPermission
        let microphoneGranted = await ensureMicrophonePermission()
        guard microphoneGranted else {
            await handleFailure("Microphone access is required to start live voice.")
            return
        }

        do {
            let bootstrap = try await apiService.createLiveVoiceSession(
                summaryContext: summaryContext,
                language: languageCode,
                userName: userName
            )
            self.sessionBootstrap = bootstrap
            self.voiceSessionId = bootstrap.voiceSessionId

            try configureAudioSession()
            try preparePlaybackGraphIfNeeded()
            try openRealtimeSocket(using: bootstrap)
            try await sendSessionUpdate(bootstrap.sessionUpdateJSON)
            try startAudioCapture()

            hasConnectedSession = true
            connectionState = .connected
            micState = .capturing
            appendSystemMessage(
                languageCode == "no"
                    ? "Live voice er koblet til. Still et sporsmal om den siste okten."
                    : "Live voice is connected. Ask about the workout you just completed."
            )

            if !didSendStartTelemetry {
                didSendStartTelemetry = true
                _ = await apiService.trackVoiceTelemetry(
                    event: "voice_session_started",
                    metadata: mergedTelemetryMetadata(
                        extra: [
                            "voice_session_id": bootstrap.voiceSessionId,
                            "voice": bootstrap.voice,
                        ]
                    )
                )
            }

            sessionTimerTask = Task { [weak self] in
                await self?.runSessionTimer(maxDurationSeconds: bootstrap.maxDurationSeconds)
            }
        } catch let apiError as APIError {
            await handleFailure(apiError.localizedDescription)
        } catch {
            await handleFailure(error.localizedDescription)
        }
    }

    func disconnect(reason: LiveVoiceDisconnectReason = .user) async {
        if case .ended = connectionState {
            return
        }
        let shouldSendEndedTelemetry = hasConnectedSession && !isFailureState
        cleanupRealtimeRuntime()
        connectionState = .ended
        micState = .idle

        if shouldSendEndedTelemetry {
            _ = await apiService.trackVoiceTelemetry(
                event: "voice_session_ended",
                metadata: mergedTelemetryMetadata(
                    extra: [
                        "voice_session_id": voiceSessionId ?? "",
                        "reason": reason.rawValue,
                        "duration_seconds": sessionDurationSeconds,
                        "turn_count": turnCount,
                    ]
                )
            )
        }
    }

    var canUseTextFallback: Bool {
        isFailureState
    }

    private var isFailureState: Bool {
        if case .failed = connectionState {
            return true
        }
        return false
    }

    private func resetForRetry() async {
        cleanupRealtimeRuntime()
        connectionState = .idle
        micState = .idle
        lastErrorMessage = nil
    }

    private func configureAudioSession() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setActive(false)
        try audioSession.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetoothHFP])
        try audioSession.setActive(true)
    }

    private func preparePlaybackGraphIfNeeded() throws {
        guard !playbackPrepared else {
            if !playbackEngine.isRunning {
                try playbackEngine.start()
            }
            if !playbackNode.isPlaying {
                playbackNode.play()
            }
            return
        }

        playbackEngine.attach(playbackNode)
        playbackEngine.connect(playbackNode, to: playbackEngine.mainMixerNode, format: playbackFormat)
        try playbackEngine.start()
        playbackNode.play()
        playbackPrepared = true
    }

    private func openRealtimeSocket(using bootstrap: VoiceSessionBootstrap) throws {
        guard let url = URL(string: bootstrap.websocketURL) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url, timeoutInterval: 30)
        request.setValue("Bearer \(bootstrap.clientSecret)", forHTTPHeaderField: "Authorization")
        let socket = URLSession.shared.webSocketTask(with: request)
        socket.resume()
        self.webSocketTask = socket
        connectionState = .connecting

        receiveTask = Task { [weak self] in
            await self?.receiveLoop()
        }
    }

    private func sendSessionUpdate(_ rawJSON: String) async throws {
        guard let socket = webSocketTask else {
            throw APIError.invalidResponse
        }
        try await socket.send(.string(rawJSON))
    }

    private func startAudioCapture() throws {
        let engine = AVAudioEngine()
        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)
        let targetFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 24_000,
            channels: 1,
            interleaved: false
        )!

        guard let converter = AVAudioConverter(from: inputFormat, to: targetFormat) else {
            throw APIError.invalidResponse
        }

        captureConverter = converter
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 2_048, format: inputFormat) { [weak self] buffer, _ in
            guard let self else { return }
            let rawPCM = self.convertBufferToPCM16(buffer, using: converter, targetFormat: targetFormat)
            guard let rawPCM, !rawPCM.isEmpty else { return }
            let encoded = rawPCM.base64EncodedString()
            let payload = "{\"type\":\"input_audio_buffer.append\",\"audio\":\"\(encoded)\"}"
            Task { [weak self] in
                await self?.sendAudioAppend(payload)
            }
        }

        engine.prepare()
        try engine.start()
        captureEngine = engine
    }

    private func convertBufferToPCM16(
        _ buffer: AVAudioPCMBuffer,
        using converter: AVAudioConverter,
        targetFormat: AVAudioFormat
    ) -> Data? {
        let ratio = targetFormat.sampleRate / max(1.0, buffer.format.sampleRate)
        let capacity = AVAudioFrameCount(max(256, Int(Double(buffer.frameLength) * ratio) + 32))
        guard let convertedBuffer = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else {
            return nil
        }

        var providedInput = false
        var conversionError: NSError?
        let status = converter.convert(to: convertedBuffer, error: &conversionError) { _, outStatus in
            if providedInput {
                outStatus.pointee = .noDataNow
                return nil
            }
            providedInput = true
            outStatus.pointee = .haveData
            return buffer
        }

        guard status != .error,
              conversionError == nil,
              convertedBuffer.frameLength > 0,
              let channelData = convertedBuffer.int16ChannelData?[0] else {
            return nil
        }

        let frameCount = Int(convertedBuffer.frameLength)
        let byteCount = frameCount * MemoryLayout<Int16>.size
        return Data(bytes: channelData, count: byteCount)
    }

    private func sendAudioAppend(_ payload: String) async {
        guard let socket = webSocketTask else { return }
        do {
            try await socket.send(.string(payload))
        } catch {
            await handleFailure("Live voice connection dropped while sending audio.")
        }
    }

    private func receiveLoop() async {
        guard let socket = webSocketTask else { return }
        do {
            while true {
                let message = try await socket.receive()
                try await handleSocketMessage(message)
            }
        } catch {
            if case .ended = connectionState {
                return
            }
            await handleFailure("Live voice connection closed unexpectedly.")
        }
    }

    private func handleSocketMessage(_ message: URLSessionWebSocketTask.Message) async throws {
        let data: Data
        switch message {
        case .data(let payload):
            data = payload
        case .string(let text):
            guard let encoded = text.data(using: .utf8) else { return }
            data = encoded
        @unknown default:
            return
        }

        let raw = try JSONSerialization.jsonObject(with: data)
        guard let event = raw as? [String: Any] else { return }
        let type = String(describing: event["type"] ?? "")

        switch type {
        case "conversation.item.input_audio_transcription.completed":
            if let transcript = stringValue(in: event, keys: ["transcript", "text"]), !transcript.isEmpty {
                transcriptEntries.append(LiveCoachTranscriptEntry(role: .user, text: transcript))
            }
        case "response.output_audio_transcript.delta", "response.audio_transcript.delta", "response.text.delta":
            if let delta = stringValue(in: event, keys: ["delta", "text"]), !delta.isEmpty {
                appendAssistantDelta(delta)
            }
        case "response.output_audio.delta", "response.audio.delta":
            if let audio = stringValue(in: event, keys: ["delta", "audio"]), !audio.isEmpty {
                queuePlaybackChunk(base64Audio: audio)
            }
        case "response.done":
            finalizeAssistantDraft()
        case "error":
            let message = stringValue(in: event, keys: ["message"]) ?? "Live voice failed."
            await handleFailure(message)
        default:
            break
        }
    }

    private func appendAssistantDelta(_ delta: String) {
        let sanitizedDelta = delta.trimmingCharacters(in: .newlines)
        guard !sanitizedDelta.isEmpty else { return }

        if let draftID = assistantDraftID,
           let index = transcriptEntries.firstIndex(where: { $0.id == draftID }) {
            let updatedText = transcriptEntries[index].text + sanitizedDelta
            transcriptEntries[index] = LiveCoachTranscriptEntry(
                id: draftID,
                role: .assistant,
                text: updatedText,
                timestamp: transcriptEntries[index].timestamp,
                isPartial: true
            )
        } else {
            let draftID = UUID()
            assistantDraftID = draftID
            transcriptEntries.append(
                LiveCoachTranscriptEntry(
                    id: draftID,
                    role: .assistant,
                    text: sanitizedDelta,
                    isPartial: true
                )
            )
        }
    }

    private func finalizeAssistantDraft() {
        guard let draftID = assistantDraftID,
              let index = transcriptEntries.firstIndex(where: { $0.id == draftID }) else {
            return
        }

        let finalized = transcriptEntries[index]
        transcriptEntries[index] = LiveCoachTranscriptEntry(
            id: finalized.id,
            role: finalized.role,
            text: finalized.text,
            timestamp: finalized.timestamp,
            isPartial: false
        )
        assistantDraftID = nil
        turnCount += 1
    }

    private func queuePlaybackChunk(base64Audio: String) {
        guard let audioData = Data(base64Encoded: base64Audio, options: .ignoreUnknownCharacters) else {
            return
        }
        let frameCount = audioData.count / MemoryLayout<Int16>.size
        guard frameCount > 0,
              let buffer = AVAudioPCMBuffer(pcmFormat: playbackFormat, frameCapacity: AVAudioFrameCount(frameCount)),
              let channelData = buffer.int16ChannelData?[0] else {
            return
        }

        buffer.frameLength = AVAudioFrameCount(frameCount)
        audioData.withUnsafeBytes { rawBuffer in
            guard let source = rawBuffer.bindMemory(to: Int16.self).baseAddress else { return }
            channelData.update(from: source, count: frameCount)
        }
        if !playbackEngine.isRunning {
            try? playbackEngine.start()
        }
        if !playbackNode.isPlaying {
            playbackNode.play()
        }
        playbackNode.scheduleBuffer(buffer, completionHandler: nil)
    }

    private func runSessionTimer(maxDurationSeconds: Int) async {
        let limit = max(60, maxDurationSeconds)
        while !Task.isCancelled && sessionDurationSeconds < limit {
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            guard !Task.isCancelled else { return }
            sessionDurationSeconds += 1
        }

        guard !Task.isCancelled else { return }
        appendSystemMessage(
            languageCode == "no"
                ? "Live voice-okten er ferdig. Du kan starte en ny hvis du vil fortsette."
                : "This live voice session has ended. Start a new one if you want to continue."
        )
        await disconnect(reason: .timeLimit)
    }

    private func cleanupRealtimeRuntime() {
        receiveTask?.cancel()
        receiveTask = nil
        sessionTimerTask?.cancel()
        sessionTimerTask = nil

        if let engine = captureEngine {
            engine.inputNode.removeTap(onBus: 0)
            engine.stop()
        }
        captureEngine = nil
        captureConverter = nil

        playbackNode.stop()
        if playbackEngine.isRunning {
            playbackEngine.stop()
        }

        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        micState = .idle
    }

    private func handleFailure(_ message: String) async {
        cleanupRealtimeRuntime()
        lastErrorMessage = message
        appendSystemMessage(message)
        connectionState = .failed(message)
        micState = .idle

        _ = await apiService.trackVoiceTelemetry(
            event: "voice_session_failed",
            metadata: mergedTelemetryMetadata(
                extra: [
                    "voice_session_id": voiceSessionId ?? "",
                    "reason": message,
                    "turn_count": turnCount,
                ]
            )
        )
    }

    private func appendSystemMessage(_ message: String) {
        let normalized = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalized.isEmpty else { return }
        transcriptEntries.append(LiveCoachTranscriptEntry(role: .system, text: normalized))
    }

    private func mergedTelemetryMetadata(extra: [String: Any]) -> [String: Any] {
        var metadata = summaryContext.telemetryMetadata().reduce(into: [String: Any]()) { partialResult, entry in
            partialResult[entry.key] = entry.value
        }
        metadata["language"] = languageCode
        metadata["turn_count"] = turnCount
        metadata["duration_seconds"] = sessionDurationSeconds
        for (key, value) in extra {
            metadata[key] = value
        }
        return metadata
    }

    private func stringValue(in payload: [String: Any], keys: [String]) -> String? {
        for key in keys {
            if let value = payload[key] as? String, !value.isEmpty {
                return value
            }
        }
        if let errorDict = payload["error"] as? [String: Any] {
            for key in keys {
                if let value = errorDict[key] as? String, !value.isEmpty {
                    return value
                }
            }
        }
        return nil
    }

    private func ensureMicrophonePermission() async -> Bool {
        switch AVAudioApplication.shared.recordPermission {
        case .granted:
            return true
        case .denied:
            return false
        case .undetermined:
            return await withCheckedContinuation { continuation in
                AVAudioApplication.requestRecordPermission { granted in
                    continuation.resume(returning: granted)
                }
            }
        @unknown default:
            return false
        }
    }
}
