from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
ACTIVE_WORKOUT_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ActiveWorkoutView.swift"
WORKOUT_COMPLETE = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "WorkoutCompleteView.swift"


def test_continuous_start_is_not_blocked_without_auth_token() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "func startWorkout() {" in text
    assert "activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "private func startContinuousWorkoutInternal(preservePendingWatchStart: Bool = false) {" in text
    assert "guard !isContinuousMode else { return }" in text
    assert "clearWatchStartPendingState()" in text
    assert "Continuous workout blocked: missing auth token" not in text
    assert "You must sign in to start coaching." not in text


def test_continuous_loop_stops_on_auth_failure_for_authenticated_workouts() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if handleAuthFailureIfNeeded(error) {" in text
    assert "private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {" in text
    assert "stopContinuousWorkout()" in text
    assert "workoutState = .idle" in text


def test_guest_mode_uses_local_workout_path_instead_of_protected_continuous_backend() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func shouldSuppressProtectedBackendRequests() -> Bool {" in text
    assert "Guest workouts stay fully local through the summary screen." in text
    assert "if !AppConfig.Auth.requireSignInForWorkoutStart {" in text
    assert "return true" in text
    assert "if shouldSuppressProtectedBackendRequests() {" in text
    assert 'await playStartupFallbackCueIfNeeded(reason: "guest_local_workout")' in text
    assert "if self.pendingStartupSpokenCue != nil {" in text
    assert "self.lastGuestFallbackCueElapsedSeconds = tickElapsedSeconds" in text
    assert "await handleSuppressedGuestCoachingTick(elapsedSeconds: tickElapsedSeconds)" in text
    assert "allowGuestPreview: false" in text
    assert 'print("⚠️ GUEST_BACKEND_PRESET active=true")' not in text
    assert "await BackendAPIService.shared.refreshGuestPreviewTokenIfNeeded(force: true)" not in text


def test_guest_continuous_start_keeps_summary_flow_clean_and_prompt_free() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    start_block = text.split(
        "private func startContinuousWorkoutInternal(preservePendingWatchStart: Bool = false) {",
        1,
    )[1].split('print("✅ Continuous workout started', 1)[0]
    assert "resetGuestBackendSuppression()" in start_block
    assert "primeGuestCoachingPreviewIfNeeded()" not in start_block
    assert "guestCoachingPromptPresented = false" in text
    assert "guestCoachingAuthSheetPresented = false" in text
    assert "guestCoachingPaywallPresented = false" in text
    assert '?? nil' in text
    assert "elapsedSeconds - (lastGuestFallbackCueElapsedSeconds ?? .min)" not in text
    assert "if let lastGuestFallbackCueElapsedSeconds {" in text


def test_active_workout_view_still_uses_existing_auth_and_paywall_surfaces_when_explicitly_requested() -> None:
    text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert ".sheet(isPresented: $viewModel.guestCoachingAuthSheetPresented)" in text
    assert "AuthView(" in text
    assert "mode: .login" in text
    assert ".sheet(isPresented: $viewModel.guestCoachingPaywallPresented)" in text
    assert "PaywallView(context: .general)" in text


def test_post_workout_talk_to_coach_remains_auth_gated_and_auto_starts_after_login() -> None:
    text = WORKOUT_COMPLETE.read_text(encoding="utf-8")
    assert "showLiveVoiceAuth = true" in text
    assert ".sheet(isPresented: $showLiveVoiceAuth)" in text
    assert "AuthView(" in text
    assert "mode: .login" in text
    assert "showLiveVoiceAuth = false" in text
    assert "if let vm = liveCoachVM {" in text
    assert "Task { await vm.startIfNeeded() }" in text
