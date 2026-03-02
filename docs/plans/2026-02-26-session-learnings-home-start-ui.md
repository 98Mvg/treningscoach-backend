# 2026-02-26 Session Learnings — Home Start Button UI

## What changed
- Home order updated so `Start trening` is directly below `Koble til pulsmåleren din`.
- Added a reusable `PulseButtonLayout` with two modes:
  - `.orb` for circular CTA.
  - `.card` for horizontal CTA.
- Home now uses the `.card` variant.
- Removed the left icon cluster in `Start trening` card per latest UX preference:
  - no mini ring icon,
  - no inner blue circle,
  - no play glyph.

## Single source of truth
- Start CTA component logic: `TreningsCoach/TreningsCoach/Views/Components/PulseButtonView.swift`
- Home section ordering: `TreningsCoach/TreningsCoach/Views/Tabs/HomeView.swift`

## What to keep for future iterations
- Keep CTA variants in one component (`PulseButtonView`) and switch by param, not separate duplicate views.
- Apply visual changes by toggling layout flags first; only add new shapes when needed.
- For Home changes, adjust order in `HomeView` before touching unrelated sections.
- Always run iOS build after UI edits to catch SwiftUI regressions quickly.

## Validation
- `xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach -configuration Debug -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build` passed after each step.
