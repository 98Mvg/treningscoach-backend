# Fix: Home Loading, Pattern Insights, Norwegian Language

Date: 2026-02-16

## Issues

1. **"Failed to load workout history: cancelled"** — Every app launch. MainTabView switch destroys HomeView, cancelling its .task.
2. **Home page loads slowly** — Render free tier cold-start (30-60s). First /workouts call hits cold server.
3. **Pattern insights during workout** — User doesn't want Claude insights spoken during workout.
4. **Norwegian coach says English words** — System prompt lacks explicit Norwegian-only instruction. Language guard only catches one phrase.

## Fixes

### Fix 1: Keep tab views alive (iOS)
**File:** `ContentView.swift`
Replace `switch selectedTab` with ZStack overlay — all three views exist, only selected one visible. Prevents .task cancellation.

### Fix 2: Backend wake-up ping (iOS)
**File:** `BackendAPIService.swift` + `HomeViewModel.swift`
Add `wakeBackend()` that fires GET `/health` (fire-and-forget). Call it at start of `loadData()` — backend starts warming while /workouts request is prepared. No extra latency for user.

### Fix 3: Disable pattern insights (Backend)
**File:** `config.py`
Set `USE_HYBRID_BRAIN = False`. This disables `detect_pattern()` calls during `/coach/continuous`. Core brain routing unaffected.

### Fix 4: Norwegian language enforcement (Backend)
**Files:** `coach_personality.py`, `main.py`
- Add explicit "RESPOND ONLY IN NORWEGIAN" to Norwegian system prompt variant
- Expand `enforce_language_consistency()` to detect English-dominant output when language=no and replace with Norwegian config fallback
