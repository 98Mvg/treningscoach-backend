# Final Step Before Live Launch: Watch Gate

Date: 2026-03-05

## Goal
Ship iOS/backend safely first, with Apple Watch hardware gate as the final launch blocker.

## Already Prepared (No Paid Dev Membership Required)
1. Watch-gated start flow is implemented with dual delivery:
   - `sendMessage` when reachable.
   - `updateApplicationContext` fallback when unreachable.
2. Request correlation is strict via `request_id`.
3. iPhone local fallback start is preserved when Watch is unreachable or ACK times out.
4. Live HR source arbitration is active:
   - priority `wc` -> `ble` -> `hk` -> `none`.
5. BLE provider resilience updated:
   - scan timeout guard,
   - reconnect backoff,
   - cleanup of pending reconnect/scan work on stop.
6. iOS auth lifecycle hardened:
   - refresh token storage,
   - one-shot request retry on 401/403,
   - refresh rotation through `/auth/refresh`.
7. Compile-level checks pass:
   - iOS generic build,
   - watchOS generic build.

## Final Watch Gate (Last Step Before Live Launch)
1. Apple Developer Program active on the same team used by all app targets.
2. Xcode signing for:
   - iOS target `TreningsCoach`,
   - watchOS target `TreningsCoachWatchApp`.
3. Verify entitlements/capabilities on real provisioning:
   - HealthKit,
   - watch workout processing.
4. Real-device acceptance (required):
   - iPhone request -> Watch ready screen -> Watch Start tap -> iPhone workout active.
   - Watch HR stream visible on iPhone in real time.
   - Watch stop propagates to iPhone and clears active state.
5. Unreachable Watch fallback acceptance:
   - iPhone starts immediately.
   - Opening watch later shows deferred request.
   - Late Watch start does not restart iPhone workout.

## Launch Decision Rule
Go live only when all five final watch gate checks pass on physical iPhone + Apple Watch.
