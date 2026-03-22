from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
ACTIVE_WORKOUT_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ActiveWorkoutView.swift"
)
WORKOUT_LAUNCH_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "WorkoutLaunchView.swift"
)


def test_view_model_exposes_phase_countdown_text_contract():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert "var phaseCountdownPrimaryText: String {" in text
    assert "var phaseCountdownSecondaryText: String?" in text
    assert "workoutContextSummary?.timeLeftS" in text
    assert "summary.repRemainingS" in text
    assert "summary.repsTotal" in text
    assert "summary.repIndex" in text
    assert "private var effectiveSessionPlan: WorkoutSessionPlan" in text
    assert "activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "workoutMode: runtimeWorkoutMode" in text


def test_view_model_exposes_live_segment_ring_progress_contract():
    text = WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")
    assert "func ringProgress(at date: Date) -> Double {" in text
    assert "let elapsed = liveElapsedTime(at: date)" in text
    assert "if let intervalProgress = intervalRingProgress(elapsedTime: elapsed) {" in text
    assert "if isEasyRunFreeRunActive {" in text
    assert "private func liveElapsedTime(at date: Date) -> TimeInterval {" in text
    assert "private func intervalRingProgress(elapsedTime: TimeInterval) -> Double?" in text
    assert "private func buildIntervalRingProgress(" in text


def test_active_workout_view_renders_phase_countdown_panel():
    text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert "phaseCountdownPanel" in text
    assert "if let secondary = viewModel.phaseCountdownSecondaryText {" in text
    assert "if let tertiary = viewModel.phaseCountdownTertiaryText {" in text


def test_interval_picker_caps_and_sensitivity_are_applied():
    text = WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "valueRange: 2...10" in text
    assert "valueRange: 1...20" in text
    assert "valueRange: 1...120" in text
    assert "valueRange: 0...120" in text
    assert "dragSensitivity: 1.55" in text
    assert "dragSensitivity: 1.45" in text
    assert "var dragSensitivity: Double = 1.0" in text
    assert "var stepSize: Int = 1" in text
    assert "stepSize: 15" in text
    assert "var dialSize: CGFloat = 236" in text


def test_circular_dial_visual_progress_is_value_synced():
    text = WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "private var hasActivePreview: Bool {" in text
    assert "previewValue != nil" in text
    assert "private var displayValue: Int {" in text
    assert "if let previewValue {" in text
    assert "private var displayProgress: Double {" in text
    assert "if isDragging || hasActivePreview {" in text
    assert "return min(1.0, max(0.0, safeAngle / 360.0))" in text
    assert "return normalizedProgress(for: displayValue)" in text
    assert "private func rawValue(forVisualAngle angle: Double) -> Double" in text
    assert "private func snappedValue(forRawValue rawValue: Double) -> Int" in text
    assert "private func snappedValue(forVisualAngle angle: Double) -> Int" in text
    assert ".onChange(of: selectedValue) { _, _ in" in text
    assert "previewValue = nil" in text
    assert "private func snapToNearestStepAndCommit()" in text
    assert "selectedValue = snapped" in text
    assert "currentAngle = normalizedProgress(for: snapped) * 360.0" in text
    snap_section = text.split("private func snapToNearestStepAndCommit() {", 1)[1].split("private func syncAngleFromMinutes()", 1)[0]
    assert "previewValue = nil" not in snap_section
    assert ".stroke(CoachiTheme.dialMagenta" in text
    assert ".shadow(color: CoachiTheme.dialMagenta.opacity(isDragging ? 0.42 : 0.18)" in text
    assert ".fill(Color.white)" in text
    assert "private var indicatorRadius: CGFloat {" in text
    assert "private var indicatorSize: CGFloat {" in text
    assert "private var indicatorPosition: CGSize {" in text
    assert "let theta = (displayProgress * 2.0 * .pi)" in text
    assert "width: CGFloat(sin(theta)) * indicatorRadius" in text
    assert "height: CGFloat(-cos(theta)) * indicatorRadius" in text
    assert ".offset(x: indicatorPosition.width, y: indicatorPosition.height)" in text
    assert "let newPreview = snappedValue(forVisualAngle: angle)" in text
    assert "currentAngle = angle" in text
    assert "lastHapticStepValue = committedValue" in text
    assert "if lastHapticStepValue != newPreview {" in text
    assert "var valueLabelFormatter: ((Int) -> (String, String))? = nil" in text
    assert "private var displayValueText: String {" in text
    assert "knobView" not in text


def test_interval_break_dial_switches_to_minutes_above_sixty_seconds():
    text = WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")
    assert "private func intervalBreakDialLabel(_ seconds: Int) -> (String, String) {" in text
    assert "let clamped = max(0, min(120, seconds))" in text
    assert "if clamped > 60 {" in text
    assert 'return (formattedBreakClockValue(for: clamped), L10n.minutesUpper)' in text
    assert "private func formattedBreakClockValue(for seconds: Int) -> String {" in text
    assert "let minutes = clamped / 60" in text
    assert "let remainingSeconds = clamped % 60" in text
    assert 'String(format: "%d:%02d", minutes, remainingSeconds)' in text
