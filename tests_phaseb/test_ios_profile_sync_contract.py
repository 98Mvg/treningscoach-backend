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


def test_workout_start_does_not_prefetch_audio_pack_before_first_tick():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert "prefetchCoreAudioIfNeeded" not in text
    assert "corePrefetchUtteranceIDs" not in text
