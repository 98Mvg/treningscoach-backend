# Session Learnings — 2026-03-16 Onboarding Explanations

## What changed

- Added Coachi-specific explanation copy directly inside the existing onboarding steps in [OnboardingContainerView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift).
- Expanded `makspuls` and `hvilepuls` with short explanation cards that define the metric and explain when a measured value is useful.
- Added an endurance explainer with examples of activities that do and do not count as utholdenhetstrening.
- Made low, moderate, and high intensity descriptions more concrete by tying them to breathing, control, and duration.

## Why this path

- The onboarding already had the right steps. The missing part was explanatory content, not flow architecture.
- Keeping the changes inside the current step views avoids navigation regressions and preserves the existing `AppViewModel` persistence path.
- Using compact explanation cards gives enough context without turning onboarding into a long educational detour.

## Verification

- `pytest -q tests_phaseb/test_onboarding_inspo_contract.py tests_phaseb/test_onboarding_theme_contract.py` -> `33 passed`
- `python3 scripts/generate_codebase_guide.py --check` -> `CODEBASE_GUIDE.md is in sync`
- `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath /Users/mariusgaarder/Documents/treningscoach/build/DerivedData CODE_SIGNING_ALLOWED=NO build` -> `BUILD SUCCEEDED`

## Follow-up note

- If the user later wants a dedicated explainer page for intensity or endurance, add it as the next step in the same onboarding sequence rather than creating a separate onboarding route.
