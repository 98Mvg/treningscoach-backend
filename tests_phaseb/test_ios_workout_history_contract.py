from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_workout_history_handles_missing_auth_token_without_error() -> None:
    text = API.read_text(encoding="utf-8")
    assert "guard currentAuthToken() != nil else {" in text
    assert "return []" in text


def test_workout_history_treats_unauthorized_as_empty_history() -> None:
    text = API.read_text(encoding="utf-8")
    assert "if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {" in text
    assert "return []" in text


def test_workout_history_accepts_wrapped_and_raw_array_shapes() -> None:
    text = API.read_text(encoding="utf-8")
    assert "if let dict = json as? [String: Any]," in text
    assert "let workouts = dict[\"workouts\"] as? [[String: Any]]" in text
    assert "if let workouts = json as? [[String: Any]] {" in text


def test_workout_completion_persists_to_backend_instead_of_in_memory_history() -> None:
    vm_text = WORKOUT_VM.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")
    assert "private func persistCompletedWorkoutIfNeeded(durationSeconds: Int, intensity: String)" in vm_text
    assert "try await apiService.saveWorkout(" in vm_text
    assert "workoutHistory.insert(" not in vm_text
    assert "func saveWorkout(durationSeconds: Int, phase: String, intensity: String, persona: String? = nil, language: String? = nil)" in api_text
    assert 'if let language = language, !language.isEmpty { body["language"] = language }' in api_text
