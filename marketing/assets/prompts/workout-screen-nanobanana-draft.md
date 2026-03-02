# Coachi Workout Screen - Nano Banana Draft Pack

Status: Draft only. Not inserted into app UI.

Use these prompts in Nano Banana to generate concept images for workout screens.
All prompts are iPhone portrait (9:16) with no baked-in text.

---

## Base Style Prefix

Use this prefix before each prompt:

```text
Cinematic, dark atmosphere, Midnight Ember palette (#1a1a2e background), neon purple (#7B68EE) and cyan (#00D9FF) accent lighting, dramatic shadows, futuristic athletic aesthetic, photorealistic, premium mobile app UI screenshot style, no brand logos, no text overlays, no watermark, no mockup frame.
```

---

## Prompt A - Active Workout (Top-right media + clear CTA)

```text
Create an iPhone workout screen UI concept for a running coach app. Full-screen athletic photo background with dark gradient overlay. Top row has compact phase pills on the left and a small circular media icon on the top right. Center has one large glowing orb used as the main control. Under orb: large elapsed timer in monospaced digits and a compact heart-rate capsule. Bottom has three controls in one row: end workout, pause/play primary, and a clear "Talk to Coach" pill button with mic icon. Design should feel polished, readable, and premium in low light. Keep spacing balanced and leave safe area margins for all iPhone sizes. 9:16.
```

---

## Prompt B - Finish Workout (Classic card, clear completion)

```text
Create an iPhone post-workout completion screen UI concept for a running coach app. Background is Midnight Ember gradient. Top center has a soft success checkmark badge. Title area communicates workout completion. Main content is one glass card with duration, intensity, coach profile used, and a short coaching summary line. Bottom has one strong primary gradient button for done. Keep hierarchy clean, readable, and realistic for production SwiftUI. No duplicate buttons. 9:16.
```

---

## Prompt C - Finish Workout (Gamified CS ring, less neon noise)

```text
Create an iPhone post-workout screen with a gamified Coach Score ring. Use a large circular score component in the upper-middle showing a 0-100 score, with smooth segmented ring progress and subtle particle accents only near the ring. Below: duration, calories, average bpm, and one short insight sentence. Two actions at bottom: primary "Share" and secondary "Done". Keep effects tasteful, not noisy. Emphasize clarity and premium athletic look. 9:16.
```

---

## Prompt D - Workout Setup (Simple, no clipping, all iPhone safe areas)

```text
Create an iPhone workout setup screen for running. Header with app mark and title "Quick setup". Step sections as rounded cards: session variant, input source status, workout intensity selector (easy/medium/hard), and advanced options. Include a large warmup duration wheel section. Bottom sticky action row with back and start coaching buttons. Ensure text never clips, respects safe areas, and has clear left/right padding for small iPhones. 9:16.
```

---

## Negative Prompt Add-on

Append this to any prompt if output drifts:

```text
Avoid: cluttered UI, tiny unreadable text, text clipping, cropped controls, duplicate call-to-action buttons, bright white backgrounds, cartoon style, unrealistic perspective, fake device frame.
```

---

## Fast Selection Rubric

Choose candidate that best matches:

1. Text and controls readable at first glance.
2. Clear hierarchy: primary action obvious.
3. Top-right media icon visible but not dominant.
4. "Talk to Coach" control is explicit and easy to hit.
5. Safe-area clean on iPhone notch/home indicator.

---

## Output Naming

Save selected drafts here:

- `.claude/worktrees/elegant-bardeen/marketing/assets/mockups/workout-active-draft-a.png`
- `.claude/worktrees/elegant-bardeen/marketing/assets/mockups/workout-complete-draft-b.png`
- `.claude/worktrees/elegant-bardeen/marketing/assets/mockups/workout-complete-draft-cs.png`
- `.claude/worktrees/elegant-bardeen/marketing/assets/mockups/workout-setup-draft-d.png`

