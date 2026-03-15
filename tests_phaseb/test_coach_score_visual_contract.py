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
    assert "@State private var displayedXPProgress: CGFloat = 0.0" in text
    assert "@State private var displayedLevelLabel: String?" in text
    assert "max(0, min(100, score))" in text
    assert "var animationDuration: Double = 2.1" in text
    assert "var levelColor: Color? = nil" in text
    assert "var levelLabel: String? = nil" in text
    assert "var xpProgress: Double? = nil" in text
    assert "var showsOuterXPRing: Bool = false" in text
    assert "var animateXPAward: Bool = false" in text
    assert "let startScore = clampedScore > 0 ? 1 : 0" in text
    assert "for step in (startScore + 1)...clampedScore" in text
    assert '.task(id: animationKey)' in text
    assert "await animateXP(" in text
    assert "formattedLevelLabel(for: finalLevelNumber - 1, template: finalLabel)" in text


def test_home_uses_gamified_score_ring_for_coach_score() -> None:
    text = HOME_VIEW.read_text(encoding="utf-8")
    assert "ScrollView(.vertical, showsIndicators: false)" in text
    assert "private var homeHorizontalPadding: CGFloat { 16 }" in text
    assert 'Text(L10n.current == .no ? "Nivå \\(appViewModel.coachiProgressState.level)" : "Level \\(appViewModel.coachiProgressState.level)")' in text
    assert '.font(.system(size: 16, weight: .heavy))' in text
    assert '.frame(maxWidth: .infinity, alignment: .leading)' in text
    assert '.frame(maxWidth: 440, alignment: .leading)' not in text
    assert "scoreHistory: workoutViewModel.coachScoreHistory" in text
    assert "coachScore: workoutViewModel.homeCoachScore" in text
    assert "xpProgress: appViewModel.coachiXPProgressFraction" in text
    assert "GamifiedCoachScoreRingView(" in text
    assert "showsOuterXPRing: true" in text
    assert "levelLabel: levelLabel" not in text


def test_workout_complete_uses_gamified_score_ring() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "@EnvironmentObject var appViewModel: AppViewModel" in text
    assert "Text(\"COACH SCORE\")" in text
    assert '@State private var finalBPMText = "0 BPM"' in text
    assert "private var shareSummaryText: String {" in text
    assert "private var coachScoreStreakCount: Int {" in text
    assert "private var xpAwardForSummary: Int {" in text
    assert "L10n.streak" in text
    assert "L10n.xpEarned" in text
    assert "L10n.coachiLevel" in text
    assert "appViewModel.coachiLevelLabel" in text
    assert "appViewModel.coachiXPProgressFraction" in text
    assert "appViewModel.coachiXPLine" in text
    assert "appViewModel.coachiXPValueLine" in text
    assert "showsOuterXPRing: true" in text
    assert "levelColor: CoachiTheme.success" in text
    assert "animateXPAward: xpAwardForSummary > 0" in text
    assert "xpAnimationFrom: viewModel.lastCoachiProgressAward?.xpProgressBeforeFraction" in text
    assert "xpAnimationTo: viewModel.lastCoachiProgressAward?.xpProgressAfterFraction" in text
    assert "scoreRingView(ringSize: ringSize)" in text
    assert "progressHighlightsCard" in text
    assert "private var progressHighlightsStatsRow: some View" in text
    assert "private var progressHighlightsLevelSection: some View" in text
    assert "private var progressHighlightsLevelBar: some View" in text
    assert "private var progressHighlightsLevelFooter: some View" in text
    assert "I finished \\(workoutLabel) with Coachi." in text
    assert "Jeg fullførte \\(workoutLabel) med Coachi." in text
    assert "@State private var showShareOptions = false" in text
    assert "WorkoutShareDestinationsSheet(" in text
    assert ".presentationDetents([.height(330)])" in text
    assert 'performShareSelection { openGenericShareSheet(destination: "x") }' in text
    assert 'shareButton(label: "Instagram"' in text
    assert 'shareButton(label: "Snapchat"' in text
    assert 'shareButton(label: "TikTok"' in text
    assert 'shareButton(label: "X"' in text
    assert 'shareButton(label: languageCode == "no" ? "Kopier lenke" : "Copy Link"' in text
    assert "WorkoutSummaryShareCardView(" in text
    assert "showProgressToast" not in text
    assert "trainingLevelDisplayName" not in text
    assert "levelProgressFraction" not in text
    assert "levelProgressLine" not in text


def test_onboarding_data_and_result_use_gamified_ring() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "GamifiedCoachScoreRingView(" in text
    assert "score: score" in text
