import plistlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "AppViewModel.swift"
)
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
BACKEND_API_SERVICE = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "BackendAPIService.swift"
)
CONFIG = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Config.swift"
)
AUTH_MANAGER = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "AuthManager.swift"
)
PROFILE_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ProfileView.swift"
)
INFO_PLIST = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Info.plist"
)


def test_backend_api_exposes_profile_upsert():
    text = BACKEND_API_SERVICE.read_text(encoding="utf-8")
    assert "func upsertUserProfile(_ profile: BackendUserProfilePayload) async throws" in text
    assert 'URL(string: "\\(baseURL)/profile/upsert")!' in text


def test_onboarding_triggers_profile_upsert():
    text = APP_VIEW_MODEL.read_text(encoding="utf-8")
    assert "Task {" in text
    assert 'await syncProfileToBackend(reason: "onboarding")' in text
    assert "func syncProfileToBackend(reason: String) async" in text


def test_profile_edit_triggers_profile_upsert():
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "try? await BackendAPIService.shared.upsertUserProfile(snapshot)" in text
    assert 'PROFILE_UPSERT reason=profile_edit' in text


def test_profile_avatar_update_stays_on_existing_auth_me_path():
    backend_text = BACKEND_API_SERVICE.read_text(encoding="utf-8")
    auth_text = AUTH_MANAGER.read_text(encoding="utf-8")
    profile_text = PROFILE_VIEW.read_text(encoding="utf-8")

    assert "func updateAuthenticatedProfileAvatar(" in backend_text
    assert 'URL(string: "\\(baseURL)/auth/me")!' in backend_text
    assert 'name=\\"avatar\\"' in backend_text
    assert "func updateProfileAvatar(imageData: Data" in auth_text
    assert "performProfileAvatarUpdateRequest(" in auth_text
    assert "PhotosPicker(selection: $selectedPhotoItem, matching: .images)" in profile_text
    assert "CoachiProfileAvatarView(avatarURL: authManager.currentUser?.avatarURL)" in profile_text
    assert "authManager.updateProfileAvatar(imageData: jpegData)" in profile_text


def test_profile_photo_permission_is_declared():
    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)

    assert info.get("NSPhotoLibraryUsageDescription")


def test_workout_start_triggers_profile_upsert():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    startup_block = text.split("private func startContinuousWorkoutInternal(preservePendingWatchStart: Bool = false) {", 1)[1].split("private func syncProfileSnapshotToBackend", 1)[0]
    assert "scheduleNextTick()" in startup_block
    assert "kickOffWorkoutStartBackgroundPreparation()" in startup_block
    assert 'await self.syncProfileSnapshotToBackend(reason: "workout_start")' in text
    assert "private func kickOffWorkoutStartBackgroundPreparation()" in text
    assert "private func syncProfileSnapshotToBackend(reason: String) async" in text


def test_workout_start_prewarms_backend_and_uses_one_time_startup_tick():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    start_block = text.split("func startWorkout() {", 1)[1].split("private func startContinuousWorkoutInternal", 1)[0]

    assert "BackendAPIService.shared.wakeBackend()" in start_block
    assert "startupCoachingRequestPending = true" in text
    assert "let isStartupTick = startupCoachingRequestPending" in text
    assert "? AppConfig.ContinuousCoaching.startupChunkDuration" in text
    assert "duration: captureDuration" in text
    assert "? AppConfig.ContinuousCoaching.startupInitialTickDelay" in text
    assert "static let startupInitialTickDelay: TimeInterval = 2.0" in config_text
    assert "static let startupChunkDuration: TimeInterval = 2.0" in config_text


def test_startup_failure_falls_back_immediately_and_deduplicates_context_cues():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")

    assert "private func playStartupFallbackCueIfNeeded(reason: String) async" in text
    assert 'utteranceID: "zone.main_started.1"' in text
    assert 'utteranceID: "zone.phase.warmup.1"' in text
    assert 'reason: "startup_request_failed"' in text
    assert 'reason: "startup_response_stale"' in text
    assert 'reason: "startup_backend_failsafe"' in text
    assert "startupContextCueHandledEventType == selected.eventType" in text
    assert '"startup_context_cue_already_handled"' in text


def test_workout_start_does_not_prefetch_audio_pack_before_first_tick():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert "prefetchCoreAudioIfNeeded" not in text
    assert "corePrefetchUtteranceIDs" not in text
