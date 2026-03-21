import json
import plistlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_COMPLETE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "WorkoutCompleteView.swift"
)
ACTIVE_WORKOUT = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ActiveWorkoutView.swift"
)
AUTH_MANAGER = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "AuthManager.swift"
)
LIVE_VOICE_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "LiveCoachConversationView.swift"
)
MODELS_SWIFT = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Models" / "Models.swift"
)
VOICE_SERVICE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "XAIRealtimeVoiceService.swift"
)
TRACKER = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "LiveVoiceSessionTracker.swift"
)
XAI_VOICE_HELPER = REPO_ROOT / "xai_voice.py"
CONFIG_SWIFT = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Config.swift"
)
INFO_PLIST = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Info.plist"
)
PBXPROJ = REPO_ROOT / "TreningsCoach" / "TreningsCoach.xcodeproj" / "project.pbxproj"
AUDIO_PACK_MANIFEST = REPO_ROOT / "output" / "audio_pack" / "v2" / "manifest.json"
CORE_AUDIO_EN = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Resources" / "CoreAudioPack" / "en" / "voice.preview.free_limit.1.mp3"
)
CORE_AUDIO_NO = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Resources" / "CoreAudioPack" / "no" / "voice.preview.free_limit.1.mp3"
)
PACK_AUDIO_EN = REPO_ROOT / "output" / "audio_pack" / "v2" / "en" / "voice.preview.free_limit.1.mp3"
PACK_AUDIO_NO = REPO_ROOT / "output" / "audio_pack" / "v2" / "no" / "voice.preview.free_limit.1.mp3"


def test_summary_screen_exposes_live_voice_cta_with_tracker_and_paywall_gating() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "@EnvironmentObject var authManager: AuthManager" in text
    assert 'Text(isNorwegian ? "Treningsoversikt" : "Workout Summary")' in text
    assert "private var hasLiveVoiceAccountAccess: Bool {" in text
    assert "authManager.hasUsableSession()" in text
    assert "LiveVoiceSessionTracker.shared" in text
    assert "liveVoiceTracker.remainingToday(isPremium: hasPremiumAccess)" in text
    assert "liveVoiceTracker.canStart(isPremium: hasPremiumAccess)" in text
    assert "liveVoiceTracker.synchronize()" in text
    assert "showLiveVoicePaywall = true" in text
    assert ".sheet(isPresented: $showWorkoutSummary)" in text
    assert ".sheet(isPresented: $showLiveVoicePaywall)" in text
    assert "liveVoiceStatusText" in text
    assert "liveVoiceQuotaDetailText" in text
    assert '"Free today: \\(remaining) remaining"' in text
    assert '"30 seconds max per session"' in text
    assert "private var sheetCardMaxWidth: CGFloat { 392 }" in text
    assert "private var summaryCardBackground: some View {" in text
    assert 'Text(isNorwegian ? "Coachi innsikt" : "Coachi Insight")' in text
    assert 'Text(isNorwegian ? "Coachi samtale" : "Coachi Conversation")' in text
    assert "SummarySurfaceButtonStyle(" in text
    assert ".background(summaryCardBackground)" in text
    assert ".frame(height: 44)" in text
    assert "PaywallView(context: .liveVoice)" in text
    assert "isPlayingPreviewLimitAudio" in text
    assert "await liveCoachVM.service.playFreePreviewLockClipIfAvailable()" in text
    assert "authManager.currentUser?.resolvedDisplayName ?? appViewModel.userProfile.name" in text
    assert 'Text(isNorwegian ? "Snakk med Coach" : "Talk to Coach")' in text
    assert 'event: "voice_cta_tapped"' in text
    assert '"entry_point"] = "workout_summary_sheet"' in text
    assert '"live_voice_available"] = liveVoiceIsAvailable' in text
    assert '"is_premium"] = hasPremiumAccess' in text
    assert '"remaining_today"] = remainingToday' in text
    assert "BackendAPIService.shared.wakeBackend()" in text
    assert "if isPresented {" in text
    assert '"Stopp" : "Stop"' in text
    assert '"Start" : "Start"' in text
    assert "presentationMode: .compactComposer" in text
    assert '"Share with Coachi"' not in text
    assert '"Del med Coachi"' not in text
    assert "liveVoiceTracker.recordSession()" not in text


def test_auth_manager_fetches_runtime_flags_for_live_voice_policy() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "@Published var productFlags: ProductFlags = .launchDefaults" in text
    assert "await fetchRuntimeFlags()" in text
    assert "BackendAPIService.shared.fetchAppRuntime()" in text


def test_live_voice_mode_stays_out_of_active_workout_surface() -> None:
    text = ACTIVE_WORKOUT.read_text(encoding="utf-8")
    assert "LiveCoachConversationView" not in text
    assert "XAIRealtimeVoiceService" not in text
    assert "voice_cta_tapped" not in text


def test_live_voice_view_has_retry_disconnect_and_text_fallback() -> None:
    text = LIVE_VOICE_VIEW.read_text(encoding="utf-8")
    assert "final class LiveCoachConversationViewModel: ObservableObject" in text
    assert "struct LiveCoachConversationView: View" in text
    assert "service.$didReceiveFirstAssistantResponse" in text
    assert "hasRecordedSuccessfulStart" in text
    assert "liveVoiceTracker.recordSession(isPremium: self.isPremium)" in text
    assert "guard !self.hasRecordedSuccessfulStart else { return }" in text
    assert "service.$turnCount" not in text
    assert "freeTurnLimit" not in text
    assert "BackendAPIService.shared.wakeBackend()" in text
    assert "ConversationActivityState" in text
    assert "service.isSpeaking" in text
    assert "service.micState == .capturing" in text
    assert "ScrollViewReader" in text
    assert '.id(transcriptBottomAnchor)' in text
    assert "scrollTranscriptToBottom" in text
    assert "viewModel.orbLabel" in text
    assert 'Button(viewModel.languageCode == "no" ? "Avslutt samtalen" : "End Conversation")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Prov igjen" : "Try Again")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Skriv i stedet" : "Type instead")' in text
    assert "PostWorkoutTextCoachView(" in text
    assert "enum PostWorkoutTextCoachPresentationMode: Equatable" in text
    assert "case compactComposer" in text
    assert ".presentationDetents([presentationMode.compactDetent])" in text
    assert "private var compactComposerBody: some View" in text
    assert "Text(compactContextLine)" not in text
    assert "private var compactContextLine: String" not in text
    assert 'event: "voice_fallback_text_opened"' in text
    assert 'Button(viewModel.languageCode == "no" ? "Lukk" : "Close")' in text
    assert "dismiss()" in text
    assert "private var hasPremiumAccess: Bool" in text
    assert "authManager.currentUser?.subscriptionTier.isPremium == true" in text
    assert "if let failureMessage = viewModel.failureMessage, viewModel.canUseTextFallback {" in text


def test_live_voice_view_generates_shareable_insight_card_after_conversation() -> None:
    text = LIVE_VOICE_VIEW.read_text(encoding="utf-8")
    assert "PostWorkoutInsightShareSection(" in text
    assert "viewModel.latestShareInsight" in text
    assert "viewModel.isConversationEnded" in text
    assert "ShareDestinationPillButton(" in text
    assert 'label: "Instagram"' in text
    assert 'label: "Snapchat"' in text
    assert 'label: "TikTok"' in text
    assert 'label: "X"' in text
    assert 'label: languageCode == "no" ? "Kopier lenke" : "Copy Link"' in text
    assert 'openGenericShareSheet(for: "x")' in text
    assert "ImageRenderer(" in text
    assert "UIActivityViewController(activityItems:" in text
    assert 'AppConfig.Share.instagramStoriesScheme' in text
    assert 'UIPasteboard.general.url = shareURL' in text


def test_voice_service_uses_realtime_socket_and_session_cap() -> None:
    text = VOICE_SERVICE.read_text(encoding="utf-8")
    assert "final class XAIRealtimeVoiceService: NSObject, ObservableObject" in text
    assert "private final class OutboundAudioSender" in text
    assert "URLSession.shared.webSocketTask(with: url, protocols: protocols)" in text
    assert 'try await socket.send(.string(rawJSON))' in text
    assert 'try await sendInitialAssistantKickoff()' in text
    assert '"type": "response.create"' in text
    assert "standardFormatWithSampleRate: 24_000" in text
    assert 'let payload = "{\\"type\\":\\"input_audio_buffer.append\\",\\"audio\\":\\"\\(encoded)\\"}"' in text
    assert 'event: "voice_session_started"' in text
    assert 'event: "voice_first_assistant_response"' in text
    assert 'event: "voice_first_assistant_audio"' in text
    assert 'event: "voice_session_failed"' in text
    assert 'event: "voice_session_ended"' in text
    assert "@Published private(set) var didReceiveFirstAssistantResponse: Bool = false" in text
    assert "@Published private(set) var didReceiveFirstAssistantAudio: Bool = false" in text
    assert "await self?.runSessionTimer(maxDurationSeconds: bootstrap.maxDurationSeconds)" in text
    assert "let limit = max(15, maxDurationSeconds)" in text
    assert 'case timeLimit = "time_limit"' in text
    assert "mode: .voiceChat" in text
    assert "playFreePreviewLockClipIfAvailable()" in text
    assert '"voice.preview.free_limit.1"' in text
    assert "Float(source[index]) / Float(Int16.max)" in text
    assert "startupTimeoutTask" in text
    assert "apiService.wakeBackend()" in text
    assert "connectionState = .connecting" in text
    assert "Live voice is taking longer than expected to connect" in text
    assert "Deliver the required opening recap now. Follow the active session instructions exactly." in text
    assert "outboundAudioSender.updateSocket(socket)" in text
    assert "outboundAudioSender.enqueue(payload)" in text
    assert "pendingPayloads.count >= self.maxDepth" in text
    assert "pendingPayloads.removeFirst()" in text
    assert 'socket.send(.string(payload)) { error in' in text
    assert "await self?.sendAudioAppend(payload)" not in text


def test_live_voice_tracker_queries_are_side_effect_free_for_summary_reads() -> None:
    text = TRACKER.read_text(encoding="utf-8")
    assert "func synchronize()" in text
    assert "currentStoredCount(resetIfNeeded: false)" in text
    assert "sessionsUsedToday = currentStoredCount(resetIfNeeded: true)" in text
    assert "publishSessionsUsedToday(currentStoredCount(resetIfNeeded: true))" in text
    assert "publishSessionsUsedToday(updated)" in text
    assert "DispatchQueue.main.async" in text
    assert "refreshDailyCount()" not in text


def test_live_voice_prompt_uses_structured_workout_history_without_chat_memory() -> None:
    text = XAI_VOICE_HELPER.read_text(encoding="utf-8")
    assert "Workout summary:" in text
    assert "sanitize_workout_history_context" in text
    assert "def _opening_recap_brief(" in text
    assert "def _opening_metric_candidates(" in text
    assert "def _opening_insight_cue(" in text
    assert "Workout history:" in text
    assert "post_workout_voice" in text
    assert "sanitize_post_workout_summary_context" in text
    assert "def _canonical_workout_reference(" in text
    assert '"average_heart_rate": _clean_int("average_heart_rate")' in text
    assert '"distance_meters": _clean_float("distance_meters")' in text
    assert '"coaching_style": _clean_string("coaching_style", 40)' in text
    assert "Do not mention gym work, strength training" in text
    assert "general running workout" in text
    assert "Do not repeat the raw generic label 'Workout' or 'Standard'." in text
    assert "YOUR FIRST RESPONSE" in text
    assert "Opening recap brief:" in text
    assert "Mention one or two stats from the recap brief below." in text
    assert "End with a short insight, not a question." in text
    assert "general workout session" not in text
    assert "conversation_history" not in text
    assert "session_history" not in text


def test_text_fallback_prompt_is_running_only_and_blocks_strength_references() -> None:
    text = MODELS_SWIFT.read_text(encoding="utf-8")
    assert "This coach conversation is for running workouts only." in text
    assert "Treat generic labels like 'Workout' as a general running workout." in text
    assert "In the first reply, use only the summary from this workout, not older workouts or history." in text
    assert "refer to it as a general running workout instead of repeating the raw label." in text
    assert "Interpret timer strings literally. If the timer is shown as MM:SS, then 00:07 means 7 seconds, not 7 minutes." in text
    assert "Treat it as a very short or early-stopped running session, not as a static hold or strength exercise." in text
    assert "If the summary is generic, very short, or sparse, keep the first reply generic and running-specific." in text
    assert "Do not mention strength training, gym work, or specific exercises such as squats, lunges, push-ups, burpees, or planks." in text
    assert "Do not say you noticed the athlete doing a specific exercise earlier unless the summary explicitly names it." in text


def test_live_voice_flag_and_microphone_usage_are_declared() -> None:
    config_text = CONFIG_SWIFT.read_text(encoding="utf-8")
    assert "struct LiveVoice" in config_text
    assert 'static let isEnabled: Bool = boolInfoValue("LIVE_COACH_VOICE_ENABLED", default: true)' in config_text
    assert "static let freeMaxDurationSeconds: Int = 30" in config_text
    assert "static let premiumMaxDurationSeconds: Int = 180" in config_text
    assert "static let freeSessionsPerDay: Int = 2" in config_text
    assert "static let premiumSessionsPerDay: Int = 3" in config_text
    assert "freeTurnLimit" not in config_text
    assert "struct Share" in config_text
    assert 'static let coachiWebsiteURLString = "https://coachi.app"' in config_text
    assert 'static let instagramStoriesScheme = "instagram-stories://share"' in config_text
    assert 'static let snapchatScheme = "snapchat://"' in config_text

    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)

    assert info.get("LIVE_COACH_VOICE_ENABLED") is True
    assert "NSMicrophoneUsageDescription" in info
    assert "instagram-stories" in info.get("LSApplicationQueriesSchemes", [])
    assert "snapchat" in info.get("LSApplicationQueriesSchemes", [])


def test_xcode_project_tracks_new_live_voice_files() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "XAIRealtimeVoiceService.swift" in text
    assert "LiveCoachConversationView.swift" in text
    assert "LiveVoiceSessionTracker.swift" in text
    assert "LiveVoiceSessionTracker.swift in Sources" in text


def test_backend_client_keeps_30_second_live_voice_bootstrap_timeout() -> None:
    text = (REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift").read_text(encoding="utf-8")
    assert 'var request = URLRequest(url: url, timeoutInterval: 30)' in text
    assert 'let url = URL(string: "\\(baseURL)/voice/session")!' in text


def test_live_voice_preview_limit_clip_is_shipped_in_manifest_and_bundle() -> None:
    manifest = json.loads(AUDIO_PACK_MANIFEST.read_text(encoding="utf-8"))
    phrase_ids = {
        str(item.get("id") or "").strip()
        for item in manifest.get("phrases", [])
        if str(item.get("id") or "").strip()
    }
    assert "voice.preview.free_limit.1" in phrase_ids
    assert CORE_AUDIO_EN.exists()
    assert CORE_AUDIO_NO.exists()
    assert PACK_AUDIO_EN.exists()
    assert PACK_AUDIO_NO.exists()
