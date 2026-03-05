from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"
PHONE_WC = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "PhoneWCManager.swift"
IOS_KEYS = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "WC" / "WCKeys.swift"
WATCH_WC = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WatchWCManager.swift"
WATCH_WORKOUT = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WatchWorkoutManager.swift"
WATCH_KEYS = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WCKeys.swift"


def test_wc_keys_define_required_commands_on_both_sides() -> None:
    ios_text = IOS_KEYS.read_text(encoding="utf-8")
    watch_text = WATCH_KEYS.read_text(encoding="utf-8")

    assert 'static let requestId = "request_id"' in ios_text
    assert 'static let requestId = "request_id"' in watch_text

    for command in (
        "request_start_workout",
        "workout_started",
        "workout_start_failed",
        "workout_stopped",
    ):
        assert command in ios_text
        assert command in watch_text


def test_phone_wc_manager_uses_dual_delivery_path() -> None:
    text = PHONE_WC.read_text(encoding="utf-8")
    assert "enum WatchCapabilityState: String" in text
    assert "case noWatchSupport" in text
    assert "case watchNotInstalled" in text
    assert "case watchInstalledNotReachable" in text
    assert "case watchReady" in text
    assert "var canUseWatchTransport: Bool" in text
    assert "var onSessionStateChanged: ((WatchCapabilityState) -> Void)?" in text
    assert "enum StartRequestOutcome" in text
    assert "session.sendMessage(payload" in text
    assert "session.updateApplicationContext(payload)" in text
    assert ".liveRequestSent" in text
    assert ".deferredAndFallback" in text
    assert "WCKeys.requestId: requestID" in text
    assert "guard canUseWatchTransport else {" in text
    assert "guard canUseWatchTransport else {" in text
    assert "WATCH_NOTIFY_SKIPPED reason=watch_unavailable" in text


def test_workout_view_model_has_watch_gated_start_and_ack_handlers() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "@Published var isWaitingForWatchStart: Bool = false" in text
    assert "private var pendingWatchRequestTimestamp: TimeInterval?" in text
    assert "private var pendingWatchRequestId: String?" in text
    assert "private var activeWatchRequestId: String?" in text
    assert "private let watchStartAckTimeoutSeconds: TimeInterval = 15.0" in text
    assert "requestWatchStartOrFallback()" in text
    assert "scheduleWatchStartAckTimeout(requestTimestamp:" in text
    assert "handleWatchWorkoutStartedAck(workoutType" in text
    assert "handleWatchWorkoutStartFailed(error:" in text
    assert "handleWatchWorkoutStopped(timestamp:" in text
    assert "guard requestID == pendingWatchRequestId else { return }" in text
    assert "func startWorkout()" in text
    assert "func startWorkout() {\n        activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "watchStartStatusLine = launchAuthRequirementText" not in text


def test_watch_side_receives_both_message_and_application_context() -> None:
    text = WATCH_WC.read_text(encoding="utf-8")
    assert "didReceiveMessage" in text
    assert "didReceiveApplicationContext" in text
    assert "requestTTLSeconds: TimeInterval = 120" in text
    assert "handledRequestIDs" in text
    assert "guard !requestID.isEmpty else { return }" in text


def test_watch_workout_ack_and_failure_semantics() -> None:
    text = WATCH_WORKOUT.read_text(encoding="utf-8")
    assert "builder.beginCollection(withStart: startDate)" in text
    assert "self.sendStartedAck(workoutType: workoutType)" in text
    assert "self.sendStartFailed(error:" in text
    assert "WCKeys.Command.workoutStarted" in text
    assert "WCKeys.Command.workoutStartFailed" in text
    assert "WCKeys.Command.workoutStopped" in text
    assert "WCKeys.requestId: requestID ?? \"\"" in text
