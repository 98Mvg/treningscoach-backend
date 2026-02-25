from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_WORKOUT_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "ActiveWorkoutView.swift"
)
CONTENT_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "ContentView.swift"
)
WORKOUT_LAUNCH_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Tabs"
    / "WorkoutLaunchView.swift"
)
WORKOUT_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "WorkoutViewModel.swift"
)
WAVEFORM_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Components"
    / "WaveformView.swift"
)


def _active_workout_view_text() -> str:
    return ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")


def _content_view_text() -> str:
    return CONTENT_VIEW.read_text(encoding="utf-8")


def _workout_launch_view_text() -> str:
    return WORKOUT_LAUNCH_VIEW.read_text(encoding="utf-8")


def _workout_view_model_text() -> str:
    return WORKOUT_VIEW_MODEL.read_text(encoding="utf-8")


def _waveform_view_text() -> str:
    return WAVEFORM_VIEW.read_text(encoding="utf-8")


def test_orb_stop_requires_long_press_and_confirmation() -> None:
    text = _active_workout_view_text()
    assert ".onLongPressGesture(minimumDuration: 2.0" in text
    assert "showStopConfirmation = true" in text

    start = text.index(".onLongPressGesture(minimumDuration: 2.0")
    snippet = text[start : start + 320]
    assert "stopWorkout()" not in snippet


def test_primary_talk_button_uses_tap_to_talk() -> None:
    text = _active_workout_view_text()
    assert 'Text(L10n.current == .no ? "Snakk med coach" : "Talk to coach")' in text
    assert "viewModel.talkToCoachButtonPressed()" in text
    assert "LongPressGesture(minimumDuration: 1.5" not in text


def test_spotify_is_in_top_row_corner_button() -> None:
    text = _active_workout_view_text()
    assert "spotifyCornerButton" in text
    assert "SpotifyLogoBadge(size: 34)" in text


def test_diagnostics_panel_uses_sheet_presentation() -> None:
    text = _active_workout_view_text()
    assert ".sheet(isPresented: $showDiagnostics)" in text


def test_main_workout_surface_has_no_coach_text_line() -> None:
    text = _active_workout_view_text()
    assert "Text(guidanceLine)" not in text


def test_mic_haptics_run_only_during_user_speech_capture() -> None:
    text = _active_workout_view_text()
    assert "guard isTalkCaptureActive else { return }" in text
    assert "private var isTalkCaptureActive: Bool {" in text
    assert "viewModel.isCoachCapturingSpeech" in text


def test_hidden_workout_tab_disables_animated_background() -> None:
    content = _content_view_text()
    launch = _workout_launch_view_text()
    assert "showsAnimatedBackground: selectedTab == .workout" in content
    assert "if showsAnimatedBackground {" in launch
    assert "ParticleBackgroundView(particleCount: 30)" in launch


def test_waveform_is_static_when_inactive() -> None:
    text = _waveform_view_text()
    assert "if isActive {" in text
    assert "TimelineView(.animation(minimumInterval: 1.0 / 20.0))" in text
    assert "barView(height: barHeight, isAnimated: false)" in text


def test_workout_launch_uses_staged_wheel_setup_for_easy_run() -> None:
    text = _workout_launch_view_text()
    assert "private enum SetupStage" in text
    assert "case easyWarmup" in text
    assert "case easyDuration" in text
    assert "valueRange: 0...120" in text
    assert "Confirm duration" in text
    assert ".disabled(!canStartWorkout)" in text


def test_workout_launch_uses_sets_break_duration_for_intervals() -> None:
    text = _workout_launch_view_text()
    assert "case intervalWarmup" in text
    assert "case intervalSets" in text
    assert "case intervalDuration" in text
    assert "case intervalBreak" in text
    assert "selectedIntervalSets" in text
    assert "selectedIntervalBreakMinutes" in text
    assert "selectedIntervalWorkMinutes" in text
    assert "Total interval time" in text
    assert "intervalBreakSelector" not in text
    assert "dialSize: 124" not in text


def test_workout_launch_moves_style_to_advanced_options() -> None:
    text = _workout_launch_view_text()
    assert "launchSection(title: \"Step C\"" not in text
    assert "Text(\"COACHING STYLE\")" in text
    assert "DisclosureGroup(" in text


def test_view_model_interval_duration_uses_custom_sets_work_and_break() -> None:
    text = _workout_view_model_text()
    assert "@Published var selectedIntervalSets: Int = 6" in text
    assert "@Published var selectedIntervalWorkMinutes: Int = 2" in text
    assert "@Published var selectedIntervalBreakMinutes: Int = 1" in text
    assert "let totalMinutes = (sets * work) + (max(0, sets - 1) * pause)" in text
