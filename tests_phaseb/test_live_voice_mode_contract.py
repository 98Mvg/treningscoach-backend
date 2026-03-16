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
VOICE_SERVICE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "XAIRealtimeVoiceService.swift"
)
XAI_VOICE_HELPER = REPO_ROOT / "xai_voice.py"
CONFIG_SWIFT = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Config.swift"
)
INFO_PLIST = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Info.plist"
)
PBXPROJ = REPO_ROOT / "TreningsCoach" / "TreningsCoach.xcodeproj" / "project.pbxproj"


def test_summary_screen_exposes_live_voice_cta_with_tracker_and_paywall_gating() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "@EnvironmentObject var authManager: AuthManager" in text
    assert 'private var liveCoachVoiceLabel: String { L10n.current == .no ? "Snakk med Coach Live" : "Talk to Coach Live" }' in text
    assert "private var shouldShowLiveCoachVoiceButton: Bool { AppConfig.LiveVoice.isEnabled }" in text
    assert "private var hasLiveVoiceAccountAccess: Bool {" in text
    assert "authManager.hasUsableSession()" in text
    assert "LiveVoiceSessionTracker.shared" in text
    assert "showLiveVoicePaywall = true" in text
    assert ".sheet(isPresented: $showLiveCoachVoice)" in text
    assert ".sheet(isPresented: $showLiveVoicePaywall)" in text
    assert 'event: "voice_cta_tapped"' in text
    assert "liveVoiceStatusText" in text
    assert ".frame(height: 44)" in text
    assert "RoundedRectangle(cornerRadius: 16, style: .continuous)" in text
    assert "PaywallView(context: .liveVoice)" in text
    assert "authManager.currentUser?.displayName ?? appViewModel.userProfile.name" in text
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
    assert "service.$connectionState" in text
    assert "hasRecordedSuccessfulStart" in text
    assert "liveVoiceTracker.recordSession(isPremium: self.isPremium)" in text
    assert 'Button(viewModel.languageCode == "no" ? "Avslutt samtalen" : "End Conversation")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Prov igjen" : "Try Again")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Spors med tekst i stedet" : "Ask in Text Instead")' in text
    assert "PostWorkoutTextCoachView(" in text
    assert 'event: "voice_fallback_text_opened"' in text
    assert 'Button(viewModel.languageCode == "no" ? "Lukk" : "Close")' in text
    assert "dismiss()" in text
    assert "private var hasPremiumAccess: Bool" in text
    assert "authManager.currentUser?.subscriptionTier.isPremium == true" in text


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
    assert "URLSession.shared.webSocketTask(with: url, protocols: protocols)" in text
    assert 'try await socket.send(.string(rawJSON))' in text
    assert "standardFormatWithSampleRate: 24_000" in text
    assert 'let payload = "{\\"type\\":\\"input_audio_buffer.append\\",\\"audio\\":\\"\\(encoded)\\"}"' in text
    assert 'event: "voice_session_started"' in text
    assert 'event: "voice_session_failed"' in text
    assert 'event: "voice_session_ended"' in text
    assert "await self?.runSessionTimer(maxDurationSeconds: bootstrap.maxDurationSeconds)" in text
    assert 'case timeLimit = "time_limit"' in text
    assert "Float(source[index]) / Float(Int16.max)" in text
    assert "startupTimeoutTask" in text
    assert "Live voice took too long to start" in text
    assert "Task {" in text


def test_live_voice_prompt_uses_structured_workout_history_without_chat_memory() -> None:
    text = XAI_VOICE_HELPER.read_text(encoding="utf-8")
    assert "Use the just-finished workout summary first." in text
    assert "sanitize_workout_history_context" in text
    assert "full-history aggregates and recent workout entries" in text
    assert "Do not claim to remember prior conversations" in text
    assert "sanitize_post_workout_summary_context" in text
    assert "conversation_history" not in text
    assert "session_history" not in text


def test_live_voice_flag_and_microphone_usage_are_declared() -> None:
    config_text = CONFIG_SWIFT.read_text(encoding="utf-8")
    assert "struct LiveVoice" in config_text
    assert 'static let isEnabled: Bool = boolInfoValue("LIVE_COACH_VOICE_ENABLED", default: true)' in config_text
    assert "static let freeMaxDurationSeconds: Int = 120" in config_text
    assert "static let premiumMaxDurationSeconds: Int = 300" in config_text
    assert "static let freeSessionsPerDay: Int = 3" in config_text
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
