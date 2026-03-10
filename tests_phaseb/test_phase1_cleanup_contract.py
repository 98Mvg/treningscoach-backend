from pathlib import Path


def test_models_swift_no_legacy_unused_runtime_models() -> None:
    text = Path(
        "/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Models/Models.swift"
    ).read_text()

    assert "struct CoachResponse" not in text
    assert "struct WorkoutSession" not in text


def test_auth_py_no_unused_optional_auth_decorator() -> None:
    text = Path("/Users/mariusgaarder/Documents/treningscoach/auth.py").read_text()

    assert "def optional_auth(" not in text
