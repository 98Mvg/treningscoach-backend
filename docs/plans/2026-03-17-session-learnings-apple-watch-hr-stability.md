# Session Learnings — 2026-03-17 Apple Watch HR Stability

## Scope

Stabilize Apple Watch live heart rate on the existing Coachi runtime path:

- iPhone workout orchestration in [WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
- Watch transport in [PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift), [WatchWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWCManager.swift), and [WatchWorkoutManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift)
- Source arbitration in [HeartRateArbiter.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/HeartRate/HeartRateArbiter.swift)
- Backend deterministic event logic in [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)

## What was wrong

The failing runtime pattern was:

1. iPhone starts a watch-backed workout while `WCSession.isReachable` is still flapping.
2. Watch does start, but live HR does not reach the phone reliably enough.
3. Unreachable watch HR used `updateApplicationContext`, which is fine for state sync but weak for quasi-live HR streaming.
4. Arbiter briefly selected an HK fallback sample, then dropped to `.none` when that sample aged out.
5. Backend emitted `hr_structure_mode_notice` too early, even though this was a watch startup/transport warmup problem rather than a true "no sensors" problem.

## Correct runtime contract

### Transport split

- Keep `updateApplicationContext` for control-plane state such as start/stop/session-plan.
- Keep `sendMessage` for fast-path live HR and start ACKs when reachable.
- Use `transferUserInfo` as the queued fallback for watch HR when unreachable.

### Startup grace

- Watch-backed workouts should enter an explicit `watch_starting` grace window on the phone side for 45 seconds.
- During grace, backend deterministic logic should suppress:
  - `hr_structure_mode_notice`
  - `watch_disconnected_notice`
  - `no_sensors_notice`
- Grace ends when the first fresh watch HR sample arrives or when the timer expires.

### Arbiter semantics

- `watchConnected` should mean "watch attached enough to matter", not "watch currently reachable".
- Keep live-HR truth tied to fresh `wc` / `ble` samples.
- `.degraded` and `.connecting` watch transport states should not be treated as a hard watch disconnect.

### HK startup behavior

- HK fallback remains useful, but startup snapshots must be age-gated before they enter live workout arbitration.
- Old pre-workout HK samples must not be allowed to briefly dominate the arbiter and then decay into `none`.

## Files that define the contract

- [TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift)
- [TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift)
- [TreningsCoach/TreningsCoach/Services/HeartRate/HeartRateArbiter.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/HeartRate/HeartRateArbiter.swift)
- [TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift)
- [zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py)
- [tests_phaseb/test_watch_connectivity_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_connectivity_contract.py)
- [tests_phaseb/test_watch_request_id_correlation_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_request_id_correlation_contract.py)
- [tests_phaseb/test_hr_arbiter_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_hr_arbiter_contract.py)
- [tests_phaseb/test_hr_provider_resilience_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_hr_provider_resilience_contract.py)
- [tests_phaseb/test_watch_hr_source_arbitration_contract.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_watch_hr_source_arbitration_contract.py)
- [tests_phaseb/test_zone_event_motor.py](/Users/mariusgaarder/Documents/treningscoach/tests_phaseb/test_zone_event_motor.py)

## Guardrails for future changes

- Do not move this to a parallel HR architecture or mirror-based redesign inside a bugfix pass.
- Do not reuse `updateApplicationContext` for live HR transport again.
- Do not remove `watch_starting` without replacing it with an equally explicit startup-grace contract between iPhone and backend.
- Do not make backend notices depend on watch reachability alone; keep sample freshness and explicit watch-status semantics separate.
