# iOS Entitlements Build Fix (Strict Mode)

## Goal
Resolve Xcode build failure:

`Entitlements file "TreningsCoach.entitlements" was modified during the build, which is not supported.`

without enabling `CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION=YES`.

## Policy
- Apple Sign-In is disabled by default for this target (`APPLE_SIGN_IN_ENABLED=0`).
- Entitlements are strict and deterministic.
- No backend/runtime architecture changes.

## Source of Truth
- Entitlements file:
  `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/TreningsCoach.entitlements`
- Target signing settings:
  `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach.xcodeproj/project.pbxproj`
- Feature flag:
  `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist`

## Verification Steps
1. Validate entitlements file is parseable:
   - `plutil -p TreningsCoach/TreningsCoach/TreningsCoach.entitlements`
2. Confirm no mutation override:
   - `rg -n "CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION = YES;" TreningsCoach/TreningsCoach.xcodeproj/project.pbxproj`
   - expected: no matches
3. Confirm Apple Sign-In flag is disabled:
   - `plutil -p TreningsCoach/TreningsCoach/Info.plist | rg APPLE_SIGN_IN_ENABLED`
   - expected: `0`
4. Build settings check:
   - `xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -showBuildSettings | rg "CODE_SIGN_ENTITLEMENTS|CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION|CODE_SIGN_STYLE"`
5. Rebuild from Xcode to device after cleaning build folder.

## Expected Outcome
- Build succeeds without entitlement mutation error.
- Apple Sign-In is hidden in onboarding for this configuration.
- Signing invariants are covered by tests:
  - `tests_phaseb/test_ios_apple_signin_contract.py`
  - `tests_phaseb/test_ios_entitlements_signing_guard.py`
