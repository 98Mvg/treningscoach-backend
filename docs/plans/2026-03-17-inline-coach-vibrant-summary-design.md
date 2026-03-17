# Inline Coach UI + Vibrant Summary Screen
_2026-03-17_

## What this changes

Four improvements to the post-workout + live voice experience:

1. **Vibrant WorkoutCompleteView** — score-based ring glow, particle burst, animated score counter
2. **Expandable WorkoutSummarySheet** — sheet grows `.medium` → `.large` when coaching starts; inline waveform + transcript; no new sheet
3. **Waveform speaking/listening indicator** — animated bars, teal for Rex, white for user, single toggle button
4. **Rex persona fix** — explicit workout activity label + 25-word hard cap per reply

---

## 1. Vibrant WorkoutCompleteView

### Score-based ring glow
A `RadialGradient` overlay behind the score ring in the `ZStack`. Color determined by `targetScore`:
- ≥ 80 → teal `A5F3EC` (great)
- 60–79 → gold `F59E0B` (good)
- < 60 → muted slate `4A6FA5` (keep going)

Opacity 0.22, radius ~110pt. Fades in with `contentVisible` at 0.3s delay.

### Particle burst
On `.onAppear`, 14 small circles (4–6pt diameter) shoot outward from ring center:
- Random angle per particle
- Travel 60–90pt outward over 0.9s (`easeOut`)
- Fade to opacity 0 from 0.7s → 1.4s
- State: `@State private var particlesVisible = false`
- After 1.5s: `particlesDone = true` removes particles from view tree

### Score counter
- `@State private var displayedScore = 0`
- On appear (0.2s delay): `Timer` fires every 16ms, `displayedScore += max(1, remaining/8)`
- Ring and number display `displayedScore` until it reaches `targetScore`

### XP badge
- Font: 22pt → 26pt
- Add teal glow shadow: radius 8, `A5F3EC` at 0.5 opacity

---

## 2. Expandable WorkoutSummarySheet

### Detent behavior
```swift
@State private var selectedDetent: PresentationDetent = .medium
// Sheet presented with:
.presentationDetents([.medium, .large], selection: $selectedDetent)
```

When "Start Coaching" tapped:
```swift
selectedDetent = .large
coachingStarted = true  // triggers coach panel appearance
```

### Stats — compact mode when coaching active
When `coachingStarted == true`, stats grid collapses to a single horizontal scroll row of chips:
```
+25 XP · 142 BPM · 24:30 · Score 82
```
Title shrinks to 14pt. Animated with `.animation(.spring(duration: 0.35))`.

### Voice lifecycle — NO duplication
`LiveCoachConversationViewModel` is created and owned by `WorkoutCompleteView` (as today).
`WorkoutSummarySheet` receives it as `@ObservedObject`:

```swift
struct WorkoutSummarySheet: View {
    // existing params...
    @ObservedObject var liveCoachVM: LiveCoachConversationViewModel
    let onStartCoaching: () -> Void   // parent: startIfNeeded() + selectedDetent = .large
    let onEndCoaching: () -> Void     // parent: disconnect()
}
```

Sheet reads from existing VM:
- `liveCoachVM.service.connectionState` → waveform state + button state
- `liveCoachVM.transcriptEntries` → transcript bubbles
- `liveCoachVM.statusLabel` → status label

**No new voice service. No new lifecycle. Sheet is view-only.**

### Coach panel layout
```
Divider
WaveformBarsView(vm: liveCoachVM)       ← Section 3
ScrollView { transcript bubbles }       ← reuse existing bubble style
ToggleCoachingButton                    ← Section 3
```
Panel appears with `.transition(.move(edge: .bottom).combined(with: .opacity))`.

---

## 3. Waveform Bars + Toggle Button

### `WaveformBarsView`
5 vertical `RoundedRectangle` bars:
- Width: 4pt, max height: 32pt, `cornerRadius 2`
- `HStack(spacing: 5)`
- `@State private var barHeights: [CGFloat] = [8, 8, 8, 8, 8]`

**Colors:**
- Rex speaking → teal `A5F3EC`
- User speaking → white 0.85
- Idle/connecting → white 0.25, bars flat at 8pt

**Animation:**
`Timer` every 80ms when speaking → random heights 10–32pt per bar, `withAnimation(.easeInOut(duration: 0.08))`. Timer stops on speaking end, bars return to 8pt.

**`isSpeaking` signal — 2-line addition to `XAIRealtimeVoiceService`:**
```swift
@Published var isSpeaking = false
// In handleSocketMessage:
case "response.audio.delta": isSpeaking = true
case "response.audio.done":  isSpeaking = false
```

**Status label (12pt semibold, tracking 0.8):**
| State | Label | Color |
|---|---|---|
| `.connecting` / `.preparing` | `"CONNECTING..."` | white 0.45 |
| Rex speaking | `"REX"` | teal |
| User speaking | `"LISTENING"` | white 0.75 |
| `.connected`, idle | `"SAY SOMETHING"` | white 0.45 |
| `.ended` | `"CONVERSATION ENDED"` | white 0.45 |

### Toggle button
Full-width capsule, 52pt tall:
- Idle/ended → `"START COACHING"` — teal fill, black text
- Connected → `"END CONVERSATION"` — white outline, white text
- Connecting/preparing → disabled, spinner

---

## 4. Rex Persona Fix (`xai_voice.py`)

### Explicit activity anchor
Add `workout_label` as first line of post-workout context block:

```python
# In build_post_workout_voice_instructions():
f"""
{persona_text}

You are now in post-workout review mode.
The athlete just completed: {summary_context.workout_label}.
Speak in {language_name}.
Only reference data explicitly present in the summary below.
Do not invent movements, exercises, or effort types not mentioned.
Keep responses under 2 sentences. Never exceed 25 words per reply.
...

{athlete_line}
Workout summary:
{summary_block}
Workout history overview:
{history_block}
"""
```

### Why this fixes "Great form on the squats"
- `workout_label` (e.g. "Easy Run", "Intervals") is now the first thing Rex reads
- "Only reference data in summary" + "do not invent movements" prevents hallucinated feedback
- 25-word hard cap enforces short sentences at instruction level (reinforces PersonaManager style rule)

---

## Files to change

| File | Change |
|---|---|
| `WorkoutCompleteView.swift` | Radial glow, particles, score counter, XP badge size, sheet receives `liveCoachVM` |
| `WorkoutSummarySheet` (in WorkoutCompleteView.swift) | Expandable detent, compact stats, `WaveformBarsView`, toggle button, `@ObservedObject liveCoachVM` |
| `XAIRealtimeVoiceService.swift` | Add `@Published var isSpeaking`, set on `response.audio.delta` / `response.audio.done` |
| `xai_voice.py` | Add `workout_label` anchor line, add 25-word cap instruction |

## Not in scope
- Replacing `LiveCoachConversationView` entirely (reused as ViewModel source)
- New voice session tracking logic
- Changes to `PostWorkoutTextCoachView`
- App Store submission

## Validation
```bash
python3 -m py_compile xai_voice.py persona_manager.py
pytest -q tests_phaseb
```
iOS: build in Xcode, test post-workout flow — verify sheet expands on Start Coaching, waveform animates, no new sheet opens.
