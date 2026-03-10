from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PBXPROJ = REPO_ROOT / "TreningsCoach" / "TreningsCoach.xcodeproj" / "project.pbxproj"
GITIGNORE = REPO_ROOT / ".gitignore"
USER_MEMORY = REPO_ROOT / "user_memory.py"
HOME_VIEW_MODEL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "HomeViewModel.swift"


def test_deleted_ios_artifacts_are_gone_from_repo_and_project() -> None:
    deleted_files = [
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "AudioRecordingManager.swift",
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "ProfileViewModel.swift",
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "SetupPageView.swift",
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "TrainingLevelView.swift",
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "WelcomePageView.swift",
    ]
    for path in deleted_files:
        assert not path.exists(), f"Expected deleted artifact to be removed: {path}"

    pbxproj_text = PBXPROJ.read_text(encoding="utf-8")
    assert "AudioRecordingManager.swift" not in pbxproj_text
    assert "ProfileViewModel.swift" not in pbxproj_text
    assert "SetupPageView.swift" not in pbxproj_text
    assert "TrainingLevelView.swift" not in pbxproj_text
    assert "WelcomePageView.swift" not in pbxproj_text


def test_repo_cleanup_removes_runtime_db_and_unused_memory_hook() -> None:
    assert not (REPO_ROOT / "CoachiPrototype").exists()

    gitignore_text = GITIGNORE.read_text(encoding="utf-8")
    user_memory_text = USER_MEMORY.read_text(encoding="utf-8")

    assert "uploads/*" in gitignore_text
    assert "output/cache/" in gitignore_text
    assert "instance/*.db" in gitignore_text
    assert "instance/*.json" in gitignore_text
    assert "instance/cache/" in gitignore_text
    assert "def detect_coaching_preference(" not in user_memory_text


def test_dead_home_components_and_history_stats_path_are_removed() -> None:
    deleted_files = [
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Components" / "RecentWorkoutRow.swift",
        REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Components" / "WeeklyProgressRing.swift",
    ]
    for path in deleted_files:
        assert not path.exists(), f"Expected dead component to be removed: {path}"

    pbxproj_text = PBXPROJ.read_text(encoding="utf-8")
    assert "RecentWorkoutRow.swift" not in pbxproj_text
    assert "WeeklyProgressRing.swift" not in pbxproj_text

    home_view_model_text = HOME_VIEW_MODEL.read_text(encoding="utf-8")
    assert "@Published var recentWorkouts" not in home_view_model_text
    assert "@Published var stats" not in home_view_model_text
    assert "getWorkoutHistory(limit: 10)" not in home_view_model_text
    assert "computeStreak(" not in home_view_model_text
