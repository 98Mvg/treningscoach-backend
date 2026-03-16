# Post-Workout Flow Design
_2026-03-16_

## What this changes

Refines the post-workout experience into a cleaner two-surface pattern:

1. **WorkoutCompleteView** — celebration + quick coach CTA + "View Workout" exit
2. **Session summary** — full stats + primary coach CTA (accessed via Workout History)

No new systems. No parallel logic. Only extensions to existing code paths.

---

## Constraints

- Reuse `LiveVoiceSessionTracker.remainingToday(isPremium:)` for all quota display
- Reuse `LiveCoachConversationViewModel.service.turnCount` for turn enforcement
- Reuse existing `WorkoutCompleteView`, `LiveCoachConversationView`, and Workout History
- Do not introduce new session managers, counters, or limit systems

---

## Surface 1 — WorkoutCompleteView (modified)

**File:** `TreningsCoach/TreningsCoach/Views/Tabs/WorkoutCompleteView.swift`

### Layout changes (minimal)

Current order: score ring → metrics → live coach button → Done

New order:
```
[Score ring + XP animation]
[Coach score summary line]

[Talk to Coach Live]           ← secondary CTA (outline style, existing component)
[Session label: "Free: N left" or "Premium" or "Come back tomorrow"]

[View Workout]                 ← rename from "Done", same action (home tab)
```

### CTA label logic (reuse existing tracker)

```swift
// Already available via LiveVoiceSessionTracker.shared
let remaining = liveVoiceTracker.remainingToday(isPremium: isPremium)

// Label under button:
// isPremium         → "Premium"
// remaining > 0     → "Free: \(remaining!) session left today"
// remaining == 0    → "No sessions left today"
```

### Button state

- `remaining > 0` or `isPremium` → enabled, opens `LiveCoachConversationView` sheet (unchanged)
- `remaining == 0` → disabled appearance or opens `PaywallView(context: .liveVoice)` (existing paywall, already used elsewhere)

### Button rename

Change button label from `"Done"` to `"View Workout"`. Action unchanged: calls `viewModel.resetWorkout()` which navigates to home tab.

---

## Surface 2 — Session Summary (existing Workout History, extended)

**Open question:** What does the current Workout History detail view look like in ProfileView? Before designing this surface, the existing history item / detail view must be read to understand what's already rendered and where to add the coach CTA.

**Do not design or implement this surface until the existing view has been read.**

---

## Config changes — session limits

### iOS — `AppConfig.swift`

Update these values only. No new properties.

| Property | Current | New |
|---|---|---|
| `freeSessionsPerDay` | 3 | 1 |
| `freeMaxDurationSeconds` | 120 | 60 |
| `premiumSessionsPerDay` | 10 | 3 |
| `premiumMaxDurationSeconds` | 300 | 180 |

New property to add (turn limit for free users):
```swift
static let freeTurnLimit = 3
```

### Backend — `config.py` or Render env vars

| Variable | Current | New |
|---|---|---|
| `XAI_LIVE_VOICE_FREE_SESSIONS_PER_DAY` | 3 | 1 |
| `XAI_LIVE_VOICE_FREE_MAX_DURATION` | 120 | 60 |
| `XAI_LIVE_VOICE_PREMIUM_SESSIONS_PER_DAY` | 10 | 3 |
| `XAI_LIVE_VOICE_PREMIUM_MAX_DURATION` | 300 | 180 |

---

## Turn limit enforcement (free users only)

**File:** `LiveCoachConversationView.swift` — `LiveCoachConversationViewModel`

`service.turnCount` is already published by `XAIRealtimeVoiceService`. The ViewModel already observes `service.$connectionState`. Extend the existing `connectionState` sink or add a separate `turnCount` sink:

```swift
service.$turnCount
    .sink { [weak self] count in
        guard let self, !self.isPremium else { return }
        if count >= AppConfig.LiveVoice.freeTurnLimit {
            Task { await self.service.disconnect(reason: .timeLimit) }
        }
    }
    .store(in: &cancellables)
```

No new state. No new counter. Hooks into existing `turnCount` and existing `disconnect(reason:)`.

---

## HealthKit — distanse

**Status: Open question.**

The app does not currently have HealthKit integration. Adding distance from HealthKit requires:
- A new HealthKit query after workout ends
- New `NSHealthShareUsageDescription` in Info.plist
- New field in `WorkoutCompletionSnapshot`

This is out of scope for the initial flow change. Decide separately whether to include before implementation begins.

**For now:** The session summary shows what's already in `PostWorkoutSummaryContext` — HR, duration, zone %, score. Distance is omitted until HealthKit is explicitly scoped.

---

## Files to modify

| File | Change |
|---|---|
| `WorkoutCompleteView.swift` | Reorder layout, rename button, adjust CTA state logic |
| `AppConfig.swift` | Update 4 existing values, add `freeTurnLimit` |
| `LiveCoachConversationView.swift` | Add `turnCount` sink with hard stop at `freeTurnLimit` |
| `config.py` / Render env vars | Update 4 backend session limit values |

**Not touched:** `LiveVoiceSessionTracker`, `XAIRealtimeVoiceService`, `LiveCoachConversationViewModel` core logic, `WorkoutViewModel`, `BackendAPIService`.

---

## What to read before implementing Surface 2

```
TreningsCoach/TreningsCoach/Views/Tabs/ProfileView.swift
```
Find: workout history detail view, how past workouts are rendered, where a coach CTA could be added.
