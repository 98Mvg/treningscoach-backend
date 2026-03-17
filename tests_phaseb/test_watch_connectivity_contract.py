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
    assert 'static let warmupSeconds = "warmup_seconds"' in ios_text
    assert 'static let mainSeconds = "main_seconds"' in watch_text
    assert 'static let intervalWorkSeconds = "interval_work_seconds"' in ios_text
    assert 'static let easyRunSessionMode = "easy_run_session_mode"' in watch_text

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
    watch_ready_section = text.split("case .watchReady:")[1].split("case .watchInstalledNotReachable:")[0]
    assert "enum WatchCapabilityState: String" in text
    assert "enum WatchLaunchOutcome: Equatable" in text
    assert "case noWatchSupport" in text
    assert "case watchNotInstalled" in text
    assert "case watchInstalledNotReachable" in text
    assert "case watchReady" in text
    assert "var canUseWatchTransport: Bool" in text
    assert "var onSessionStateChanged: ((WatchCapabilityState) -> Void)?" in text
    assert "enum StartRequestOutcome" in text
    assert "session.sendMessage(payload" in text
    assert "session.updateApplicationContext(payload)" in text
    assert "func retryDeferredStartRequest(" in text
    assert "WATCH_START_RETRY_TRANSPORT" in text
    assert "didReceiveUserInfo" in text
    assert ".liveRequestSent" in text
    assert ".deferredAwaitingReachability" in text
    assert "WCKeys.requestId: requestID" in text
    assert "context.forEach { payload[$0.key] = $0.value }" in text
    assert "guard canUseWatchTransport else {" in text
    assert "guard canUseWatchTransport else {" in text
    assert "WATCH_NOTIFY_SKIPPED reason=watch_unavailable" in text
    assert "private var hasActivatedSession = false" in text
    assert "private let healthStore = HKHealthStore()" in text
    assert "func launchWatchAppForWorkout(workoutType: String) async -> WatchLaunchOutcome" in text
    assert "try await healthStore.startWatchApp(toHandle: configuration)" in text
    assert "try session.updateApplicationContext(payload)" in watch_ready_section
    assert "session.sendMessage(payload, replyHandler: nil)" in watch_ready_section
    assert "WATCH_START_TRANSPORT_DEGRADED request_id=" in watch_ready_section
    assert "onWorkoutStartFailed?" not in watch_ready_section


def test_phone_wc_manager_activates_once_after_callbacks_are_wired() -> None:
    wc_text = PHONE_WC.read_text(encoding="utf-8")
    vm_text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "override init() {\n        super.init()\n    }" in wc_text
    assert "guard !hasActivatedSession else { return }" in wc_text
    assert "phoneWCManager.activate()" in vm_text
    assert "WATCH_CAPABILITY state=" not in vm_text


def test_workout_view_model_has_watch_gated_start_and_ack_handlers() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    timeout_section = text.split("private func scheduleWatchStartAckTimeout(")[1].split(
        "private func requestSystemWatchLaunch("
    )[0]
    assert "@Published var isWaitingForWatchStart: Bool = false" in text
    assert "private var pendingWatchRequestTimestamp: TimeInterval?" in text
    assert "private var pendingWatchRequestId: String?" in text
    assert "private var activeWatchRequestId: String?" in text
    assert "private var isWatchBackedContinuousSession = false" in text
    assert "private var watchLaunchTask: Task<Void, Never>?" in text
    assert "private let watchStartAckTimeoutSeconds: TimeInterval = 12.0" in text
    assert "requestWatchStartOrFallback()" in text
    assert "requestSystemWatchLaunch(workoutType: workoutType, requestID: requestID)" in text
    assert "scheduleWatchStartAckTimeout(requestTimestamp:" in text
    assert "handleWatchWorkoutStartedAck(workoutType" in text
    assert "handleWatchWorkoutStartFailed(error:" in text
    assert "handleWatchWorkoutStopped(timestamp:" in text
    assert "guard requestID == pendingWatchRequestId else { return }" in text
    assert "guard requestID == activeWatchRequestId else { return }" in text
    assert "guard isContinuousMode else { return }" in text
    assert "guard isWatchBackedContinuousSession," in text
    assert "adoptWatchBackedSession(" in text
    assert "status=late_started" in text
    assert "self.startContinuousWorkoutInternal()" in timeout_section
    assert "self.phoneWCManager.sendWorkoutStopped(" not in timeout_section
    assert "func startWorkout()" in text
    assert "func startWorkout() {\n        activeSessionPlan = buildSessionPlanFromSelections()" in text
    assert "watchStartStatusLine = launchAuthRequirementText" not in text


def test_watch_side_receives_both_message_and_application_context() -> None:
    text = WATCH_WC.read_text(encoding="utf-8")
    assert "static let shared = WatchWCManager()" in text
    assert "didReceiveMessage" in text
    assert "didReceiveApplicationContext" in text
    assert "applyPendingApplicationContextIfNeeded(from: session)" in text
    assert "let applicationContext = session.receivedApplicationContext" in text
    assert "requestTTLSeconds: TimeInterval = 120" in text
    assert "handledRequestIDs" in text
    assert "guard !requestID.isEmpty else { return }" in text
    assert "@Published var pendingSessionPlan: WatchSessionPlanSnapshot?" in text
    assert "pendingSessionPlan = WatchSessionPlanSnapshot(payload: payload)" in text
    assert "if !requestID.isEmpty, requestID == pendingRequestId {" in text
    assert "showStartScreen = false" in text


def test_watch_side_can_prime_start_prompt_from_system_workout_launch() -> None:
    text = WATCH_WC.read_text(encoding="utf-8")
    assert "func primePendingStartFromSystemLaunch(workoutConfiguration: HKWorkoutConfiguration)" in text
    assert "pendingWorkoutType = Self.normalizedWorkoutType(from: workoutConfiguration)" in text
    assert "showStartScreen = true" in text


def test_watch_workout_ack_and_failure_semantics() -> None:
    text = WATCH_WORKOUT.read_text(encoding="utf-8")
    assert "sessionPlan: WatchSessionPlanSnapshot?" in text
    assert "builder.beginCollection(withStart: startDate)" in text
    assert "self.sendStartedAck(workoutType: workoutType)" in text
    assert "self.sendStartFailed(error:" in text
    assert "WCKeys.Command.workoutStarted" in text
    assert "WCKeys.Command.workoutStartFailed" in text
    assert "WCKeys.Command.workoutStopped" in text
    assert "WCKeys.requestId: requestID ?? \"\"" in text
    assert "WCSession.default.transferUserInfo(payload)" in text
    assert "private func shouldQueueFallbackHeartRatePayload(bpm: Int, at sampleDate: Date) -> Bool" in text
    assert "WATCH_HR_SEND_FAILED transport=message" in text
    assert "self.queueFallbackHeartRatePayload(payload, bpm: roundedBPM, at: sampleDate)" in text
    assert "private let queuedHRTransferIntervalSeconds: TimeInterval = 2.0" in text
