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


def test_summary_screen_exposes_live_voice_cta_behind_flag_and_premium_gate() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "@EnvironmentObject var authManager: AuthManager" in text
    assert 'private var liveCoachVoiceLabel: String { L10n.current == .no ? "SNAKK MED COACH LIVE" : "TALK TO COACH LIVE" }' in text
    assert "AppConfig.LiveVoice.isEnabled" in text
    assert "authManager.isAuthenticated" in text
    assert "authManager.currentUser != nil" in text
    assert ".fullScreenCover(isPresented: $showLiveCoachVoice)" in text
    assert 'event: "voice_cta_tapped"' in text
    assert 'Image(systemName: "mic.fill")' in text
    assert ".frame(height: 64)" in text
    assert "RoundedRectangle(cornerRadius: 22, style: .continuous)" in text


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
    assert 'Button(viewModel.languageCode == "no" ? "Koble fra" : "Disconnect")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Prov igjen" : "Try Again")' in text
    assert 'Button(viewModel.languageCode == "no" ? "Spors med tekst i stedet" : "Ask in Text Instead")' in text
    assert "PostWorkoutTextCoachView(" in text
    assert 'event: "voice_fallback_text_opened"' in text


def test_voice_service_uses_realtime_socket_and_session_cap() -> None:
    text = VOICE_SERVICE.read_text(encoding="utf-8")
    assert "final class XAIRealtimeVoiceService: NSObject, ObservableObject" in text
    assert "URLSession.shared.webSocketTask(with: request)" in text
    assert 'try await socket.send(.string(rawJSON))' in text
    assert "input_audio_buffer.append" in text
    assert 'event: "voice_session_started"' in text
    assert 'event: "voice_session_failed"' in text
    assert 'event: "voice_session_ended"' in text
    assert "await self?.runSessionTimer(maxDurationSeconds: bootstrap.maxDurationSeconds)" in text
    assert 'case timeLimit = "time_limit"' in text


def test_live_voice_prompt_is_scoped_to_post_workout_summary_not_full_history() -> None:
    text = XAI_VOICE_HELPER.read_text(encoding="utf-8")
    assert "Stay tightly focused on the just-finished workout summary and recovery guidance." in text
    assert "sanitize_post_workout_summary_context" in text
    assert "conversation_history" not in text
    assert "session_history" not in text


def test_live_voice_flag_and_microphone_usage_are_declared() -> None:
    config_text = CONFIG_SWIFT.read_text(encoding="utf-8")
    assert "struct LiveVoice" in config_text
    assert 'static let isEnabled: Bool = boolInfoValue("LIVE_COACH_VOICE_ENABLED", default: true)' in config_text

    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)

    assert info.get("LIVE_COACH_VOICE_ENABLED") is True
    assert "NSMicrophoneUsageDescription" in info


def test_xcode_project_tracks_new_live_voice_files() -> None:
    text = PBXPROJ.read_text(encoding="utf-8")
    assert "XAIRealtimeVoiceService.swift" in text
    assert "LiveCoachConversationView.swift" in text
