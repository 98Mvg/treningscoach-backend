# XP Badge + Workout Summary Sheet + Personal Trainer Voice
_2026-03-17_

## What this changes

Three independent improvements to the post-workout and live-voice experience:

1. **XP badge animation** — floating "+N XP" after workout, remove level label from ring
2. **Workout Summary sheet** — rename "Talk to Coach Live" CTA to "Workout Summary"; inside: full stats grid + big "Start Coaching" button
3. **xAI personal trainer personality** — wire `PersonaManager.get_system_prompt` into `xai_voice.py` so Grok Rex follows the same persona as the old pipeline

---

## 1. XP Badge + Remove Level Label (`WorkoutCompleteView.swift`)

### Remove level label
- Pass `levelLabel: ""` to `GamifiedCoachScoreRingView` (was `summaryLevelLabel` = "Level 1")
- The ring view handles empty string by hiding that text area

### "+N XP" floating badge
- New `@State private var xpBadgeVisible = false`
- Overlaid on the score ring `ZStack`, positioned above center
- Text: `"+\(xpAwardForSummary) XP"` — only shown when `xpAwardForSummary > 0`
- Animation: spring in from y+10 with opacity 0→1 (delay 0.55s after appear), fade out after 2.4s
- Style: 22pt bold, Color(hex: "A5F3EC") with subtle drop shadow

---

## 2. Workout Summary Sheet (`WorkoutCompleteView.swift`)

### Button rename
- `liveCoachVoiceLabel` → `"WORKOUT SUMMARY"` / `"TRENINGSOVERSIKT"`
- On tap: `showWorkoutSummary = true` (new state bool)
- Availability check unchanged: same `liveVoiceIsAvailable` / paywall gate
- Status dot + text unchanged

### New `WorkoutSummarySheet` view
Presented as `.sheet(isPresented: $showWorkoutSummary)` with `.large` detent.

Receives via init:
```swift
struct WorkoutSummarySheet: View {
    let xpGained: Int
    let xpToNextLevel: Int?
    let heartRateText: String
    let durationText: String
    let zoneTimePct: Double?       // nil = show "—"
    let coachScore: Int
    let liveVoiceIsAvailable: Bool
    let liveVoiceStatusText: String
    let onStartCoaching: () -> Void
    let onHome: () -> Void
    let onShare: () -> Void
}
```

### Layout (top to bottom)
```
Drag handle
"Workout Summary"  (title, 20pt semibold)

2×3 stats grid:
  ┌──────────────┬──────────────┐
  │  +25 XP      │  420 to lvl  │  XP Gained / XP to Next Level
  ├──────────────┼──────────────┤
  │  142 BPM ♥   │  24:30       │  Heart Rate / Duration
  ├──────────────┼──────────────┤
  │  73% zone    │  Score 82    │  Time in Zone / Coachi Score
  └──────────────┴──────────────┘
Distance: —   (grayed out, HealthKit deferred)

Divider

"Talk to Coach Live"     (17pt semibold)
"Ask questions about this workout"  (14pt secondary)

[        START COACHING        ]   ← full width, 56pt tall, CoachiTheme.accent

[HOME]          [SHARE]            ← existing capsule style, side by side
```

### Data sources (all already available in WorkoutCompleteView)
| Field | Source |
|---|---|
| XP Gained | `xpAwardForSummary` |
| XP to Next Level | `summaryProgressAward?.xpToNextLevel` or `appViewModel.coachiXPToNextLevel` |
| Heart Rate | `finalBPMText` (frozen on appear) |
| Duration | `finalDurationText` (frozen on appear) |
| Time in Zone | `viewModel.postWorkoutSummaryContext.zoneTimeInTargetPct` |
| Coachi Score | `targetScore` |
| Distance | `"—"` (HealthKit deferred) |

### Navigation flow
- `showWorkoutSummary = true` → sheet opens
- "Start Coaching" → `onStartCoaching()` callback → parent: `showWorkoutSummary = false`, then `showLiveCoachVoice = true`
- HOME → `onHome()` → `viewModel.resetWorkout()`
- SHARE → `onShare()` → `showShareOptions = true`

**All existing sheets in parent unchanged.** `WorkoutSummarySheet` is purely additive.

---

## 3. xAI Personal Trainer Personality (`xai_voice.py`)

### The problem
`build_post_workout_voice_instructions()` uses a generic 2-line tone description. The rich Personal Trainer persona in `persona_manager.py` (calm, disciplined, short sentences, no buzzwords, safety protocol) is ignored.

### The fix
```python
# xai_voice.py — add import
from persona_manager import PersonaManager

# In build_post_workout_voice_instructions():
persona_text = PersonaManager.get_system_prompt(
    persona="personal_trainer",
    language=language,
    emotional_mode="supportive",
    safety_override=False,
)
```

Replace the generic tone sentence with `{persona_text}` at the top of the instructions, followed by the post-workout context block:

```
{persona_text}

You are now in post-workout review mode.
Speak in {language_name}.
Use the just-finished workout summary first. You may also reference the
workout history for pattern and consistency questions.
Do not claim to remember prior conversations or any data beyond the
supplied summary and history overview.
If the athlete asks for medical diagnosis, tell them to seek professional care.
Do not invent metrics not in the supplied data.

{athlete_line}
Workout summary:
{summary_block}
Workout history overview:
{history_block}
```

### Why this is safe
- `PersonaManager.get_system_prompt` is already imported in `brain_router.py` and all brain adapters — no new dependency
- Norwegian is handled automatically: `language="no"` returns `PERSONAS_NO["personal_trainer"]`
- `emotional_mode="supportive"` is correct for post-workout (always calm, never peak/pressing)
- Short sentence rule is built into the persona — no separate instruction needed

---

## 4. WorkoutSessionDetailView (ProfileView — history) — Same structure, available data only

Same 2×3 grid layout as `WorkoutSummarySheet`, but cells are **conditionally rendered**.
A cell is shown only if its data is non-nil and meaningful. Missing cells are simply absent — no "—" placeholder, no empty slot.

### Cell availability per source
| Cell | Source | Show when |
|---|---|---|
| XP Gained | `summaryProgressAward?.xpAwarded` (only if persisted context matches) | > 0 |
| XP to Next Level | `summaryProgressAward?.xpToNextLevel` | non-nil and persisted context matches |
| Heart Rate | `record.finalHeartRateText` / persisted context | not nil, not "—", not "0 BPM" |
| Duration | `record.durationFormatted` | always available |
| Time in Zone | persisted context `.zoneTimeInTargetPct` | non-nil (only if richContext matched) |
| Coachi Score | `record.coachScore` | > 0 |
| Distance | — | **never shown** (HealthKit deferred, no stub) |

### Grid rendering rule
- Cells are paired left/right per row
- If only one cell is available in a row, it spans full width
- Rows with zero available cells are omitted entirely
- Minimum always rendered: Duration + Coachi Score (at least 1 row guaranteed)

### Big "Start Coaching" button
Same as `WorkoutSummarySheet`: full width, `CoachiTheme.accent`, 56pt tall.
Subtitle: `"Ask questions about this workout"` / `"Still spørsmål om denne økten"`

---

## Files to change

| File | Change |
|---|---|
| `TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift` | XP badge, remove level label, rename button, add WorkoutSummarySheet |
| `TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift` | WorkoutSessionDetailView: adaptive grid (available data only, no "—"), big Start Coaching button |
| `xai_voice.py` | Import PersonaManager, inject personal trainer persona into instructions |

## Validation
```bash
python3 -m py_compile xai_voice.py persona_manager.py
pytest -q tests_phaseb
```
iOS: build in Xcode, test post-workout flow on device.
