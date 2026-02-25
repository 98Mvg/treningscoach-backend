# 2026-02-25 UI Session Learnings

## What failed before
- Repeated text clipping fixes inside child views did not solve root cause when parent/container constraints were wrong.
- Tab labels clipped on smaller widths because labels had fixed one-line assumptions and not enough horizontal budget.
- Interval setup became visually heavy and confusing when using parallel controls instead of a guided sequence.

## What worked
- Fixing layout contracts at the correct level (tab bar/item width + multiline label behavior) solved clipping reliably.
- Constraining score visuals to an explicit `0...100` model and centralizing animation behavior avoided inconsistent rings.
- Guided staged setup (confirm per step) reduced complexity and improved completion flow for workout configuration.

## Rules to keep
- When UI clipping appears, inspect parent geometry/frame/safe area first, then child text behavior.
- For tab labels, always support wrapping + scale-down and test Norwegian/English lengths.
- Prefer one primary interaction at a time on mobile (single wheel + confirm) over side-by-side dense controls.
- Keep UX changes on the existing runtime path (`WorkoutLaunchView` + `WorkoutViewModel`) and avoid parallel implementations.
