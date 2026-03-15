from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Models" / "Models.swift"
APP_VIEW_MODEL = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "AppViewModel.swift"
)
WORKOUT_VIEW_MODEL = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
)
CONFIG = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Config.swift"


def test_coachi_progress_model_is_separate_from_training_level() -> None:
    text = MODELS.read_text(encoding="utf-8")
    assert "struct CoachiProgressState: Codable, Equatable" in text
    assert "static let startingLevel = 1" in text
    assert "static let maximumLevel = 99" in text
    assert "static let xpPerLevel = 100" in text
    assert 'var levelLabel: String {' in text
    assert '"Lv.\\(level)"' in text
    assert "enum CoachiProgressStore" in text
    assert 'private static let guestKey = "coachi_progress_guest"' in text
    assert 'return "coachi_progress_\\(normalized)"' in text


def test_workout_view_model_awards_xp_once_on_completion_path() -> None:
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    config_text = CONFIG.read_text(encoding="utf-8")
    assert "@Published private(set) var lastCoachiProgressAward: CoachiProgressAward?" in text
    assert "private func applyCoachiProgression(durationSeconds: Int, finalCoachScore: Int)" in text
    assert "durationSeconds > AppConfig.Progression.minWorkoutSecondsForXPAward" in text
    assert "finalCoachScore >= AppConfig.Progression.minCoachScoreForXPAward" in text
    assert "CoachiProgressStore.awardXP(" in text
    assert "AppConfig.Progression.xpAwardPerQualifiedWorkout" in text
    assert "lastCoachiProgressAward = currentState.applyingXPAward(0)" in text
    assert "applyCoachiProgression(durationSeconds: duration, finalCoachScore: coachScore)" in text
    assert "good_coach_workout_count" not in text
    assert "applyExperienceProgression" not in text
    assert "static let minWorkoutSecondsForXPAward: Int = 30" in config_text


def test_app_view_model_reads_coachi_progress_without_overloading_profile_training_level() -> None:
    text = APP_VIEW_MODEL.read_text(encoding="utf-8")
    assert "@Published private(set) var coachiProgressState = CoachiProgressState()" in text
    assert "func refreshCoachiProgress()" in text
    assert "coachiProgressState = CoachiProgressStore.load(for: currentProgressUserID)" in text
    assert "var trainingLevelDisplayName: String {" in text
    assert "var coachiLevelLabel: String {" in text
    assert 'return "Nivå \\(coachiProgressState.level)"' in text
    assert 'return "Level \\(coachiProgressState.level)"' in text
    assert "var coachiXPProgressFraction: Double {" in text
    assert "var coachiXPLine: String {" in text
    assert "var coachiXPValueLine: String {" in text
    assert "@AppStorage(\"good_coach_workout_count\")" not in text
