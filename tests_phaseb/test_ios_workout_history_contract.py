from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"


def test_workout_history_handles_missing_auth_token_without_error() -> None:
    text = API.read_text(encoding="utf-8")
    assert "guard let token = KeychainHelper.readString(key: KeychainHelper.tokenKey), !token.isEmpty else {" in text
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
