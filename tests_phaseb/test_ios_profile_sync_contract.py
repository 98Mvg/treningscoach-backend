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
    assert 'print("📤 Profile upsert reason=profile_edit")' in text


def test_workout_start_triggers_profile_upsert():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert 'await syncProfileSnapshotToBackend(reason: "workout_start")' in text
    assert "private func syncProfileSnapshotToBackend(reason: String) async" in text
