from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IOS_KEYS = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "WC" / "WCKeys.swift"
WATCH_KEYS = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WCKeys.swift"
PHONE_WC = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "PhoneWCManager.swift"
WATCH_WC = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WatchWCManager.swift"
WATCH_WORKOUT = REPO_ROOT / "TreningsCoach" / "TreningsCoachWatchApp" / "WatchWorkoutManager.swift"
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_request_id_key_exists_on_phone_and_watch() -> None:
    ios_text = IOS_KEYS.read_text(encoding="utf-8")
    watch_text = WATCH_KEYS.read_text(encoding="utf-8")
    assert 'static let requestId = "request_id"' in ios_text
    assert 'static let requestId = "request_id"' in watch_text
    assert 'static let warmupSeconds = "warmup_seconds"' in ios_text
    assert 'static let warmupSeconds = "warmup_seconds"' in watch_text
    assert 'static let easyRunSessionMode = "easy_run_session_mode"' in ios_text
    assert 'static let easyRunSessionMode = "easy_run_session_mode"' in watch_text


def test_phone_wc_start_and_stop_payloads_include_request_id() -> None:
    text = PHONE_WC.read_text(encoding="utf-8")
    assert "context: [String: Any] = [:]" in text
    assert "context.forEach { payload[$0.key] = $0.value }" in text
    assert "func sendWorkoutStopped(timestamp: TimeInterval, requestID: String)" in text
    assert "WCKeys.requestId: requestID" in text
    assert "onWorkoutStartedAck: ((String, TimeInterval, String) -> Void)?" in text


def test_watch_side_deduplicates_start_requests_by_request_id_with_ttl() -> None:
    text = WATCH_WC.read_text(encoding="utf-8")
    assert "@Published var pendingRequestId: String?" in text
    assert "private var handledRequestIDs: [String: TimeInterval] = [:]" in text
    assert "requestTTLSeconds: TimeInterval = 120" in text
    assert "guard !requestID.isEmpty else { return }" in text
    assert "handledRequestIDs[requestID] = timestamp" in text


def test_watch_ack_fail_stop_payloads_include_request_id() -> None:
    text = WATCH_WORKOUT.read_text(encoding="utf-8")
    assert "WCKeys.requestId: requestID ?? \"\"" in text
    assert "WCKeys.Command.workoutStarted" in text
    assert "WCKeys.Command.workoutStartFailed" in text
    assert "WCKeys.Command.workoutStopped" in text


def test_view_model_accepts_pending_ack_and_matching_late_ack_for_same_request_id() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    ack_section = text.split("private func handleWatchWorkoutStartedAck(")[1].split(
        "private func handleWatchWorkoutStartFailed("
    )[0]
    assert "private var pendingWatchRequestId: String?" in text
    assert "private var activeWatchRequestId: String?" in text
    assert "private var isPendingWatchStartDeferred = false" in text
    assert "private var didRetryPendingWatchStartAfterReachability = false" in text
    assert "guard requestID == pendingWatchRequestId else { return }" in ack_section
    assert "guard requestID == activeWatchRequestId else { return }" in ack_section
    assert "guard isContinuousMode else { return }" in ack_section
    assert "guard !isWatchBackedContinuousSession else { return }" in ack_section
    assert "adoptWatchBackedSession(" in ack_section
    assert "WATCH_ACK request_id=\\(requestID) status=late_started" in ack_section
    assert "guard isWaitingForWatchStart else { return }" not in ack_section
    assert "guard let pendingTimestamp = pendingWatchRequestTimestamp" not in text


def test_phone_owned_fallback_sessions_ignore_late_watch_stop_events() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var isWatchBackedContinuousSession = false" in text
    assert "isWatchBackedContinuousSession = true" in text
    assert "guard isWatchBackedContinuousSession," in text
    assert "requestID == activeWatchRequestId else { return }" in text


def test_deferred_watch_start_retries_same_request_once_when_reachability_returns() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func retryDeferredWatchStartIfNeeded(trigger: String)" in text
    assert "guard isPendingWatchStartDeferred else { return }" in text
    assert "guard !didRetryPendingWatchStartAfterReachability else { return }" in text
    assert "phoneWCManager.retryDeferredStartRequest(" in text
    assert "WATCH_START_RETRY request_id=" in text
