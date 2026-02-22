# 2026-02-22 - App Inspo to Coachi Mapping (Image-by-Image)

## Goal

Map each inspiration screen to Coachi implementation choices while keeping:
- app free now (`APP_FREE_MODE=true`)
- billing-ready later via backend flags
- no parallel runtime paths

## Image mapping

1. `IMG_5548` Hero trust + CTA -> Adopt tone for onboarding opening.
2. `IMG_5549` "one-number" pedagogy -> Adapt for CoachScore / zone-hold narrative.
3. `IMG_5550` secondary KPI card -> Adapt for recovery quality visuals.
4. `IMG_5551` wearable trust + fallback -> Adopt (watch connect + no-watch fallback).
5. `IMG_5552` low-friction signup -> Adopt.
6. `IMG_5553` profile basics start -> Adopt.
7. `IMG_5554` personalized intro copy -> Adopt.
8. `IMG_5555` explain core metric simply -> Adopt.
9. `IMG_5556` explain second metric -> Adapt later.
10. `IMG_5557` clear "start now" CTA -> Adopt for baseline run.
11. `IMG_5558` DOB + gender step -> Adopt (HR personalization inputs).
12. `IMG_5559` height/weight + units -> Adopt.
13. `IMG_5560` HRmax auto + override -> Adopt (Zone 2 setup).
14. `IMG_5561` RHR guidance + FAQ -> Adopt.
15. `IMG_5562` endurance yes/no -> Adapt as training history question.
16. `IMG_5563` intensity option cards -> Adopt (coaching aggressiveness baseline).
17. `IMG_5564` frequency/duration selectors -> Adopt.
18. `IMG_5565` progressive form dependencies -> Adopt.
19. `IMG_5566` editable summary screen -> Adopt.
20. `IMG_5567` summary CTA -> Adopt ("Start coaching").
21. `IMG_5568` locked result card -> Defer paywall behavior (layout can be reused).
22. `IMG_5569` subscription paywall -> Defer.
23. `IMG_5570` connect sensor dual-action -> Adopt.
24. `IMG_5571` no-sensor fallback -> Adopt (remove premium upsell copy).
25. `IMG_5572` notifications opt-in -> Adopt.
26. `IMG_5573` home banner + simple card hierarchy -> Adopt.
27. `IMG_5574` clean home variant (no banner) -> Adopt.
28. `IMG_5575` subscription management -> Defer.
29. `IMG_5576` empty-state CTA -> Adopt for challenges/history empty states.

## Implemented now (Step 3 slice)

- Active workout UI moved toward glanceable state:
  - top status pills (phase + zone)
  - compact HR + target range row (watch-connected only)
  - single short guidance line (no long lyric-like transcript)
- Home sensor pattern:
  - watch-connected status card
  - not-connected banner with explicit "Connect Apple Watch" action
- Onboarding now includes the "one-number" CoachScore pedagogy:
  - added a dedicated CoachScore intro screen after profile setup
  - shows one sample score + 3 short reasons (zone hold, consistency, recovery)
  - flow updated to: Welcome -> Language -> Features -> Account -> Setup -> CoachScore Intro

## Deferred intentionally

- Any paywall/subscription surface remains OFF while free mode is active.
- Premium/subscription UI can be enabled later when product quality target is met.
