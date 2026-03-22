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
TIMER_RING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Components"
    / "TimerRingView.swift"
)
CONFIG_SWIFT = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Config.swift"
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


def _timer_ring_view_text() -> str:
    return TIMER_RING_VIEW.read_text(encoding="utf-8")


def _config_text() -> str:
    return CONFIG_SWIFT.read_text(encoding="utf-8")


def test_finish_control_requires_confirmation_alert() -> None:
    text = _active_workout_view_text()
    assert ".onLongPressGesture(minimumDuration: 2.0" not in text
    assert "showStopConfirmation = true" in text
    assert ".alert(" in text
    assert "viewModel.stopWorkout()" in text


def test_primary_talk_button_uses_tap_to_talk() -> None:
    text = _active_workout_view_text()
    assert "Text(L10n.talkToCoachButton)" in text
    assert "viewModel.talkToCoachButtonPressed()" in text
    assert "LongPressGesture(minimumDuration: 1.5" not in text


def test_active_workout_has_visible_finish_button() -> None:
    text = _active_workout_view_text()
    assert "Image(systemName: \"figure.run\")" in text
    assert "showStopConfirmation = true" in text
    assert "\"End workout?\"" in text


def test_spotify_is_in_top_row_corner_button() -> None:
    text = _active_workout_view_text()
    assert "spotifyIconButton" in text
    assert "SpotifyLogoBadge(size: 30)" in text
    assert ".offset(y: -1)" in text
    assert "SpotifyGlyph(size: size * 0.62)" in text


def test_diagnostics_panel_uses_sheet_presentation() -> None:
    text = _active_workout_view_text()
    assert ".sheet(isPresented: diagnosticsSheetIsPresented)" in text


def test_diagnostics_button_is_hidden_behind_admin_whitelist() -> None:
    text = _active_workout_view_text()
    config = _config_text()
    assert "@EnvironmentObject var authManager: AuthManager" in text
    assert "if canAccessWorkoutDiagnostics {" in text
    assert "AppConfig.Debug.canAccessWorkoutDiagnostics(email: authManager.currentUser?.email)" in text
    assert "AudioPipelineDiagnostics.shared.isOverlayVisible = false" in text
    assert "WORKOUT_DIAGNOSTICS_ALLOWED_EMAILS" in config
    assert "static func canAccessWorkoutDiagnostics(email: String?) -> Bool" in config


def test_main_workout_surface_has_no_coach_text_line() -> None:
    text = _active_workout_view_text()
    assert "Text(guidanceLine)" not in text


def test_active_workout_shows_live_hr_degraded_banner_hook() -> None:
    text = _active_workout_view_text()
    assert "if let liveBanner = viewModel.liveHRBannerText {" in text
    assert "Text(liveBanner)" in text


def test_active_workout_timer_ring_uses_live_timeline_progress() -> None:
    text = _active_workout_view_text()
    assert "TimelineView(.animation(minimumInterval: 1.0 / 30.0)) { context in" in text
    assert "progress: viewModel.ringProgress(at: context.date)" in text


def test_timer_ring_view_does_not_add_one_second_lag_animation() -> None:
    text = _timer_ring_view_text()
    assert '.animation(.easeInOut(duration: 1), value: safeProgress)' not in text
    assert ".trim(from: 0, to: CGFloat(safeProgress))" in text
    assert ".rotationEffect(.degrees(360 * safeProgress - 90))" in text


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
    assert "valueRange: 1...120" in text
    assert 'stageCheckButton(title: L10n.current == .no ? "Fortsett" : "Continue")' in text
    assert 'stageCheckButton(title: L10n.current == .no ? "Bekreft" : "Confirm")' in text
    assert "setupSummaryCard(" not in text
    assert "summaryEditButton(" not in text
    assert "private var easyRunSessionTotalSeconds: Int {" in text
    assert "private func totalDurationText(for totalSeconds: Int) -> String {" in text
    assert "let canStartAction = canStartWorkout &&" in text
    assert ".disabled(!canStartAction)" in text


def test_workout_launch_uses_sets_break_duration_for_intervals() -> None:
    text = _workout_launch_view_text()
    assert "case intervalWarmup" in text
    assert "case intervalSets" in text
    assert "case intervalDuration" in text
    assert "case intervalBreak" in text
    assert "selectedIntervalSets" in text
    assert "selectedIntervalBreakSeconds" in text
    assert "selectedIntervalWorkMinutes" in text
    assert "valueRange: 0...120" in text
    assert "stepSize: 15" in text
    assert "valueLabelFormatter: intervalBreakDialLabel" in text
    assert 'unitLabel: L10n.current == .no ? "SEK" : "SEC"' in text
    assert "if clamped > 60 {" in text
    assert "formattedBreakClockValue(for: clamped)" in text
    assert "intervalTotalDurationText" in text
    assert "intervalBreakSelector" not in text
    assert "dialSize: 124" not in text


def test_workout_launch_surfaces_intensity_before_advanced_options() -> None:
    text = _workout_launch_view_text()
    assert 'launchSection(title: "Step B"' not in text
    assert "private var showsSetupSelectionSection: Bool {" in text
    assert "if showsSetupSelectionSection {" in text
    assert "if showsPostSetupSections {" in text
    assert 'Text(showsPostSetupSections ? L10n.workoutIntensityPrompt : "Quick setup")' in text
    assert "if !showsPostSetupSections {" in text
    assert '"Choose your coaching intensity before you start."' not in text
    assert '"Velg ønsket coachingintensitet før du starter."' not in text
    assert "Text(title)" in text
    assert '.font(.system(size: 19, weight: .bold))' in text
    assert "if let setupCompletionDurationText {" in text
    assert "handleBottomBackAction()" in text
    assert "intensityOptionCard(" in text
    assert "title: L10n.workoutIntensityEasyDetail" in text
    assert "title: L10n.workoutIntensityModerateDetail" in text
    assert "title: L10n.workoutIntensityHardDetail" in text
    assert "Text(L10n.breathAnalysisTitle)" in text
    assert "DisclosureGroup(" in text
    assert "private var launchSectionVerticalPadding: CGFloat {" in text
    assert "showsSetupSelectionSection ? 18 : 14" in text


def test_workout_launch_omits_step_b_input_sources_section() -> None:
    text = _workout_launch_view_text()
    assert "L10n.inputSources" not in text
    assert 'Text("Apple Watch")' not in text
    assert 'Image(systemName: "applewatch.side.right")' in text
    assert 'let statusColor = connected ? Color.green : CoachiTheme.warning' in text
    assert 'let statusTitle = connected' in text
    assert 'return L10n.current == .no ? "Live puls ikke tilgjengelig" : "Live heart rate unavailable"' in text
    assert 'return L10n.current == .no ? "Venter på puls" : "Awaiting heart rate"' in text
    assert "return viewModel.watchBPMDisplayText" in text


def test_performance_mode_chip_is_marked_pro() -> None:
    text = _workout_launch_view_text()
    chip_text = (
        REPO_ROOT
        / "TreningsCoach"
        / "TreningsCoach"
        / "Views"
        / "Components"
        / "PersonaChipView.swift"
    ).read_text(encoding="utf-8")
    assert "CoachPersonality.allCases" in text
    assert 'Text("PRO")' in chip_text
    assert "@EnvironmentObject private var subscriptionManager: SubscriptionManager" in text
    assert "@State private var showPerformanceModePaywall = false" in text
    assert '.sheet(isPresented: $showPerformanceModePaywall)' in text
    assert "PaywallView(context: .general)" in text
    assert "guard !(persona == .toxicMode && !subscriptionManager.hasPremiumAccess) else {" in text
    assert "showPerformanceModePaywall = true" in text


def test_workout_launch_start_cta_is_watch_adaptive_and_pending_safe() -> None:
    text = _workout_launch_view_text()
    assert "Text(viewModel.launchStartButtonTitle)" in text
    assert "Text(viewModel.launchStartSubtext)" in text
    assert "if let authHelper = viewModel.launchAuthRequirementText {" in text
    assert "if let helper = viewModel.watchReachabilityHelperText {" in text
    assert ".disabled(!canStartAction)" in text
    assert "if let watchStatus = viewModel.watchStartStatusLine {" in text


def test_workout_view_model_launch_cta_and_helper_are_watch_capability_driven() -> None:
    text = _workout_view_model_text()
    assert "@Published private(set) var watchCapabilityState: PhoneWCManager.WatchCapabilityState = .noWatchSupport" in text
    assert "if watchCapabilityState == .watchReady {" in text
    assert "guard watchCapabilityState == .watchInstalledNotReachable else {" in text
    assert ' ? "Starter Coachi på Apple Watch når du trykker Start. Hvis ingenting skjer, åpne appen manuelt og godkjenn tilgang hvis du blir spurt."' in text
    assert ' : "Coachi opens on Apple Watch when you press Start. If nothing happens, open the app manually and accept access if prompted."' in text


def test_workout_start_sets_immediate_startup_status_line() -> None:
    text = _workout_view_model_text()
    assert '? "Coachen er klar om et oyeblikk."' in text
    assert ': "Coach will be ready in a moment."' in text
    assert "scheduleNextTick()" in text


def test_workout_launch_uses_single_large_current_action_header() -> None:
    text = _workout_launch_view_text()
    assert "private var stepATitle: String {" in text
    assert 'return L10n.current == .no ? "Velg oppvarming" : "Select warm-up"' in text
    assert 'return L10n.current == .no ? "Velg drag" : "Select sets"' in text
    assert 'return L10n.current == .no ? "Velg tid" : "Select work time"' in text
    assert 'return L10n.current == .no ? "Velg pause" : "Select break time"' in text
    assert 'return "\\(L10n.warmupTime) · \\(L10n.intensityEasy)"' not in text
    assert "Text(L10n.warmupEasyBPMCue)" not in text
    assert 'Text((L10n.current == .no ? "DRAG" : "DRAG"))' not in text
    assert 'Text((L10n.current == .no ? "TID" : "TIME"))' not in text
    assert 'Text((L10n.current == .no ? "PAUSER" : "BREAKS"))' not in text


def test_active_workout_hr_fallback_is_zero_bpm() -> None:
    text = _active_workout_view_text()
    assert 'return "0 BPM"' in text
    assert 'return "HK \\(viewModel.watchBPMDisplayText)"' in text


def test_active_workout_ring_uses_time_remaining_text_inside_circle() -> None:
    text = _active_workout_view_text()
    assert "Text(viewModel.timerRingTimeText)" in text
    assert "Text(viewModel.timerRingTitleText)" not in text


def test_active_workout_interval_panel_shows_countdown_cue_and_set_dots() -> None:
    text = _active_workout_view_text()
    assert "Text(viewModel.phaseCountdownPrimaryText)" not in text
    assert "if let tertiary = viewModel.phaseCountdownTertiaryText {" in text
    assert "if !viewModel.intervalSetProgressDots.isEmpty {" in text
    assert "viewModel.intervalSetProgressDots.enumerated()" in text


def test_view_model_interval_duration_uses_custom_sets_work_and_break() -> None:
    text = _workout_view_model_text()
    assert "@Published var selectedIntervalSets: Int = 6" in text
    assert "@Published var selectedIntervalWorkMinutes: Int = 2" in text
    assert "@Published var selectedIntervalBreakSeconds: Int = 60" in text
    assert "let repeats = max(2, min(10, selectedIntervalSets))" in text
    assert "let workSeconds = max(1, min(20, selectedIntervalWorkMinutes)) * 60" in text
    assert "let recoverySeconds = max(0, min(120, selectedIntervalBreakSeconds))" in text


def test_view_model_interval_progress_supports_recovery_start_countdown_and_done_left() -> None:
    text = _workout_view_model_text()
    assert "var intervalSetProgressDots: [Bool]" in text
    assert "var phaseCountdownTertiaryText: String?" in text
    assert "? \"Til pause: \\(remainingText)\"" in text
    assert "? \"Til start: \\(remainingText)\"" in text
    assert 'case 30:' in text
    assert 'case 15:' in text
    assert 'case 5:' in text
    assert 'case 0 ... 1:' in text


def test_workout_launch_hides_no_live_hr_subtext_when_no_source_is_connected() -> None:
    text = _workout_view_model_text()
    assert 'return currentLanguage == "no" ? "Live puls + sonecoaching" : "Live HR + zone coaching"' in text
    assert 'return currentLanguage == "no" ? "Live puls via Bluetooth-sensor" : "Live HR via Bluetooth sensor"' in text
    assert 'return ""' in text


def test_view_model_persists_final_coach_score_history_for_home() -> None:
    text = _workout_view_model_text()
    assert 'private let coachScoreHistoryKey = "coach_score_history_v1"' in text
    assert 'private let lastCoachScoreKey = "last_real_coach_score"' in text
    assert "@Published private(set) var coachScoreHistory: [CoachScoreRecord] = []" in text
    assert "@Published private(set) var lastPersistedCoachScore: Int = 0" in text
    assert "loadPersistedCoachScores()" in text
    assert "persistFinalCoachScore(coachScore, at: Date())" in text
