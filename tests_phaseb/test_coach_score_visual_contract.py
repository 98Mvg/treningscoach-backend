from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Theme"
    / "AppTheme.swift"
)
HOME_VIEW = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "HomeView.swift"
)
WORKOUT_COMPLETE = (
    REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "WorkoutCompleteView.swift"
)
ONBOARDING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "OnboardingContainerView.swift"
)


def test_gamified_ring_component_counts_from_zero_to_target_score() -> None:
    text = RING_VIEW.read_text(encoding="utf-8")
    assert "struct GamifiedCoachScoreRingView: View" in text
    assert "@State private var displayedScore: Int = 0" in text
    assert "displayedScore = 0" in text
    assert "max(0, min(100, score))" in text
    assert "var animationDuration: Double = 2.1" in text
    assert "for step in 1...steps" in text
    assert '.task(id: clampedScore)' in text


def test_home_uses_gamified_score_ring_for_coach_score() -> None:
    text = HOME_VIEW.read_text(encoding="utf-8")
    assert "scoreHistory: workoutViewModel.coachScoreHistory" in text
    assert "coachScore: workoutViewModel.homeCoachScore" in text
    assert "GamifiedCoachScoreRingView(" in text


def test_workout_complete_uses_gamified_score_ring() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "NeonCoachScoreRingView(" in text
    assert "score: viewModel.coachScore" in text
    assert 'Text("CS")' in text
    assert 'return "0 BPM"' in text
    assert "ShareLink(item: shareSummaryText)" in text
    assert "Text(L10n.done)" in text


def test_onboarding_data_and_result_use_gamified_ring() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "GamifiedCoachScoreRingView(" in text
    assert "score: 82" in text
    assert "score: score" in text
