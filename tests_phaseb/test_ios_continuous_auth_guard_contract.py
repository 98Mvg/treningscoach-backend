from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"
ACTIVE_WORKOUT_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ActiveWorkoutView.swift"
AUTH_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "AuthView.swift"


def test_continuous_start_is_not_blocked_without_auth_token() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "func startWorkout() {" in text
    assert "activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "private func startContinuousWorkoutInternal(preservePendingWatchStart: Bool = false) {" in text
    assert "guard !isContinuousMode else { return }" in text
    assert "clearWatchStartPendingState()" in text
    assert "Continuous workout blocked: missing auth token" not in text
    assert "You must sign in to start coaching." not in text


def test_continuous_loop_stops_on_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "if handleAuthFailureIfNeeded(error) {" in text
    assert "private func handleAuthFailureIfNeeded(_ error: Error) -> Bool {" in text
    assert "stopContinuousWorkout()" in text
    assert "workoutState = .idle" in text


def test_guest_mode_suppresses_further_backend_calls_after_auth_failure() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var guestBackendSuppressed = false" in text
    assert "private var guestPreviewSessionConsumedThisWorkout = false" in text
    assert 'private let guestCoachingPreviewSessionsUsedKey = "guest_coaching_preview_sessions_used_v1"' in text
    assert "private func shouldSuppressProtectedBackendRequests() -> Bool {" in text
    assert "private func suppressProtectedBackendRequestsForGuest(reason: GuestCoachingLimitReason) {" in text
    assert "private func primeGuestCoachingPreviewIfNeeded() {" in text
    assert "presentGuestCoachingPromptIfNeeded(reason: reason)" in text
    assert "print(\"⚠️ TALK_BACKEND_SUPPRESSED" in text
    assert "print(\"⚠️ COACHING_BACKEND_SUPPRESSED" in text
    assert "await handleSuppressedGuestCoachingTick(elapsedSeconds: tickElapsedSeconds)" in text
    assert "allowGuestPreview: shouldAllowGuestPreviewBackendRequests(at: tickElapsedSeconds)" in text


def test_continuous_start_primes_guest_preview_or_prompt_without_session() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    start_block = text.split("private func startContinuousWorkoutInternal(preservePendingWatchStart: Bool = false) {", 1)[1].split("print(\"✅ Continuous workout started", 1)[0]
    assert "resetGuestBackendSuppression()" in start_block
    assert "primeGuestCoachingPreviewIfNeeded()" in start_block
    assert 'print("⚠️ GUEST_BACKEND_PREVIEW active=true max_s=' in text
    assert 'print("⚠️ GUEST_BACKEND_PRESET active=true")' in text


def test_backend_continuous_request_can_send_guest_preview_header_without_auth() -> None:
    text = API.read_text(encoding="utf-8")
    assert "createContinuousMultipartRequest" in text
    assert "let didAttachAuth = addAuthHeader(to: &request)" in text
    assert 'request.setValue("1", forHTTPHeaderField: "X-Coachi-Guest-Preview")' in text
    assert "guard addAuthHeader(to: &request) else {" not in text
    assert "case authenticationRequired" in text


def test_active_workout_reuses_existing_auth_and_paywall_surfaces_for_guest_prompt() -> None:
    text = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    assert ".sheet(isPresented: $viewModel.guestCoachingAuthSheetPresented)" in text
    assert "AuthView(" in text
    assert "mode: .login" in text
    assert ".sheet(isPresented: $viewModel.guestCoachingPaywallPresented)" in text
    assert "PaywallView(context: .general)" in text
    assert "viewModel.guestCoachingPromptTitle" in text
    assert "viewModel.guestCoachingPromptMessage" in text


def test_workout_auth_sheet_offers_escape_hatches_when_login_fails() -> None:
    active = ACTIVE_WORKOUT_VIEW.read_text(encoding="utf-8")
    auth_view = AUTH_VIEW.read_text(encoding="utf-8")

    assert "allowsContinueWithoutAccountInLoginMode: true" in active
    assert "onSeePremium: {" in active
    assert "viewModel.guestCoachingPaywallPresented = true" in active

    assert "let onSeePremium: (() -> Void)?" in auth_view
    assert "let allowsContinueWithoutAccountInLoginMode: Bool" in auth_view
    assert "private var showsWorkoutLoginFallbackActions: Bool {" in auth_view
    assert "mode == .login && allowsContinueWithoutAccountInLoginMode" in auth_view
    assert 'title: L10n.current == .no ? "Fortsett lokalt" : "Continue local"' in auth_view
    assert 'title: L10n.current == .no ? "Se Premium" : "See Premium"' in auth_view
