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
MODELS = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Models" / "Models.swift"


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
    assert "xpLine: appViewModel.coachiXPLine" in text
    assert "GamifiedCoachScoreRingView(" in text
    assert "fullSweepBeforeSettling: false" in text
    assert "showsOuterXPRing: true" in text
    assert 'title: L10n.streak' in text
    assert 'title: "XP"' in text
    assert "scoreHistory.currentWorkoutStreak()" in text
    assert "levelLabel: levelLabel" not in text


def test_workout_complete_uses_gamified_score_ring() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "@EnvironmentObject var appViewModel: AppViewModel" in text
    assert "Text(\"COACH SCORE\")" in text
    assert '@State private var finalBPMText = "0 BPM"' in text
    assert "@State private var xpCelebrationFinished = false" in text
    assert "private var shareSummaryText: String {" in text
    assert "private var summaryProgressAward: CoachiProgressAward? {" in text
    assert "private var xpAwardForSummary: Int {" in text
    assert "private var showXPCelebration: Bool {" in text
    assert "viewModel.completedWorkoutSnapshot?.coachiProgressAward ?? viewModel.lastCoachiProgressAward" in text
    assert "private var summaryLevelLabel: String {" in text
    assert "private var summaryXPProgress: Double {" in text
    assert "private var summaryStreakDays: Int {" in text
    assert "private var summaryXPLineText: String {" in text
    assert 'finalDurationText = viewModel.completedWorkoutSnapshot?.durationText ?? viewModel.elapsedFormatted' in text
    assert 'finalBPMText = viewModel.completedWorkoutSnapshot?.finalHeartRateText ?? viewModel.watchBPMDisplayText' in text
    assert "xpCelebrationFinished = true" in text
    assert "try? await Task.sleep(nanoseconds: 1_500_000_000)" in text
    assert "showsOuterXPRing: showXPCelebration" in text
    assert "levelColor: CoachiTheme.success" in text
    assert "animateFromOne: false" in text
    assert "fullSweepBeforeSettling: false" in text
    assert "animateXPAward: showXPCelebration" in text
    assert "levelLabel: summaryLevelLabel" in text
    assert "xpProgress: showXPCelebration ? summaryXPProgress : nil" in text
    assert "xpAnimationFrom: summaryProgressAward?.xpProgressBeforeFraction" in text
    assert "xpAnimationTo: summaryProgressAward?.xpProgressAfterFraction" in text
    assert "scoreRingView(ringSize: ringSize)" in text
    assert "summaryProgressPills" in text
    assert 'title: L10n.streak' in text
    assert 'title: "XP"' in text
    assert "if showXPCelebration {" in text
    assert "XP Gained" not in text
    assert "XP to Next Level" not in text
    assert "progressHighlightsCard" not in text
    assert "I finished \\(workoutLabel) with Coachi." in text
    assert "Jeg fullførte \\(workoutLabel) med Coachi." in text
    assert "@State private var showShareOptions = false" in text
    assert "WorkoutShareDestinationsSheet(" in text
    assert ".presentationDetents([.height(420)])" in text
    assert 'performShareSelection { openGenericShareSheet(destination: "x") }' in text
    assert 'shareButton(label: "Instagram"' in text
    assert 'shareButton(label: "Snapchat"' in text
    assert 'shareButton(label: "TikTok"' in text
    assert 'shareButton(label: "X"' in text
    assert 'shareButton(label: languageCode == "no" ? "Kopier lenke" : "Copy Link"' in text
    assert "WorkoutSummaryShareCardView(" in text
    assert "SummarySurfaceButtonStyle(variant: .hero)" in text
    assert "SummarySurfaceButtonStyle(variant: .utility)" in text
    assert "SummarySurfaceButtonStyle(variant: .outline)" in text
    assert "showProgressToast" not in text
    assert "trainingLevelDisplayName" not in text
    assert "levelProgressFraction" not in text
    assert "levelProgressLine" not in text


def test_onboarding_data_and_result_use_gamified_ring() -> None:
    text = ONBOARDING_VIEW.read_text(encoding="utf-8")
    assert "GamifiedCoachScoreRingView(" in text
    assert "score: score" in text


def test_models_expose_current_workout_streak_helper_for_score_history() -> None:
    text = MODELS.read_text(encoding="utf-8")
    assert "extension Array where Element == CoachScoreRecord" in text
    assert "func currentWorkoutStreak(calendar: Calendar = .autoupdatingCurrent) -> Int" in text
    assert "let uniqueDays = Set(map { calendar.startOfDay(for: $0.date) })" in text
