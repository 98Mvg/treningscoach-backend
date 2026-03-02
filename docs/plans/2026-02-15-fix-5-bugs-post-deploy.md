# Fix 5 Post-Deploy Bugs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 5 bugs reported after testing commit `3a01e33`: coach silence after welcome, broken diagnostic panel, Grok not used, Norwegian missing æøå, mic/breath analysis uncertainty.

**Architecture:** All bugs have independent root causes. Backend fixes need sync to root + push. iOS fixes need Xcode rebuild. No new files — only edits to existing code.

**Tech Stack:** Swift/SwiftUI (iOS), Python/Flask (backend), ElevenLabs TTS, xAI Grok API

---

## Bug Summary

| # | Bug | Root Cause | Fix Location |
|---|-----|-----------|-------------|
| 1 | Coach silent after welcome | `coaching_intelligence.py` still has `signal_quality < 0.05` gate (was supposed to be removed but may not have deployed), plus backend `should_speak=false` cascades | Backend: `voice_intelligence.py`, `main.py` |
| 2 | Diagnostic panel doesn't appear | `CoachOrbView` absorbs touch events (no `allowsHitTesting(false)`), long-press gesture never fires | iOS: `ActiveWorkoutView.swift` |
| 3 | Grok not being used | `brain_pool` caches init failures permanently — if `XAI_API_KEY` was missing on first attempt, Grok stays `None` forever | Backend: `brain_router.py` |
| 4 | Norwegian voice can't pronounce æ, ø, å | All Norwegian message banks use ASCII substitutes (`"aa"`, `"oe"`, `"ae"`) instead of real Unicode characters | Backend: `config.py`, `persona_manager.py` |
| 5 | Mic/breath analysis uncertainty | No direct bug found — mic flow is correct, but first ticks may fail if buffer empty. Need better logging to diagnose | iOS: `WorkoutViewModel.swift` (logging) |

---

### Task 1: Fix Diagnostic Panel Touch (iOS)

**Files:**
- Modify: `TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift:35-43`

**Step 1: Add allowsHitTesting(false) to CoachOrbView**

The animated orb has multiple overlapping `Circle()` layers (glow at 1.7x size) that absorb touch events, preventing the parent `onLongPressGesture` from firing.

```swift
// ActiveWorkoutView.swift, line 35-43 — replace the ZStack block:
ZStack {
    TimerRingView(progress: viewModel.phaseProgress, size: AppConfig.Layout.timerRingSize, lineWidth: 6)
        .allowsHitTesting(false)
    CoachOrbView(state: viewModel.orbState, size: AppConfig.Layout.orbSize)
        .allowsHitTesting(false)
}
.contentShape(Circle())
.onLongPressGesture(minimumDuration: 0.8) {
    withAnimation(.easeInOut(duration: 0.3)) {
        showDiagnostics.toggle()
        AudioPipelineDiagnostics.shared.isOverlayVisible = showDiagnostics
    }
}
```

Changes:
- Add `.allowsHitTesting(false)` to both `TimerRingView` and `CoachOrbView` so touch passes through to the `ZStack`
- Add `.contentShape(Circle())` so the ZStack has an explicit hit area
- Reduce `minimumDuration` from 1.5 to 0.8 seconds (1.5s is too long with animation interference)
- Set `diagnostics.isOverlayVisible = showDiagnostics` on open (currently only set on close)

**Step 2: Verify in Xcode**

Build and run. Long-press the orb for ~1 second during a workout. The diagnostic overlay should appear at the top of the screen.

**Step 3: Commit**

```bash
git add TreningsCoach/TreningsCoach/Views/Tabs/ActiveWorkoutView.swift
git commit -m "fix: diagnostic panel — allow hit testing through orb, reduce long-press to 0.8s"
```

---

### Task 2: Fix Norwegian æ, ø, å Characters (Backend)

**Files:**
- Modify: `backend/config.py:349-468` (Norwegian message banks)
- Modify: `backend/config.py:518-561` (Toxic mode Norwegian messages)
- Modify: `backend/persona_manager.py:87-143` (EMOTIONAL_MODIFIERS_NO)
- Modify: `backend/persona_manager.py:241-343` (PERSONAS_NO)
- Modify: `backend/brains/grok_brain.py` (add Norwegian char instruction to prompt)

**Step 1: Replace ASCII substitutes in config.py Norwegian message banks**

Global find-and-replace in the Norwegian sections only (lines 349-561). Key substitutions:

| ASCII | Unicode | Example |
|-------|---------|---------|
| `naar` | `når` | "Klar når du er" |
| `saa` | `så` | "finn roen, så setter vi i gang" |
| `paa` | `på` | "Kjenn på kroppen" |
| `naa` | `nå` | "Nå begynner vi" |
| `aa` (standalone/word-internal å) | `å` | "å begynne med" |
| `foerst` | `først` | "Sikkerhet først" |
| `foelger` | `følger` | "Alt annet følger derfra" |
| `oyeblikk` | `øyeblikk` | "Ta et øyeblikk" |
| `aapent` | `åpent` | "brystet åpent" |
| `oekt` | `økt` | "God økt" |
| `Kjoer` | `Kjør` | "Kjør på!" |
| `Troekk` | `Trøkk` | "Trøkk i beina!" |
| `aerlig`/`Aerlig` | `ærlig`/`Ærlig` | "Ærlig og konstruktiv" |
| `forstar` | `forstår` | "Du forstår" |
| `moete` | `møte` | "å møte opp" |

**IMPORTANT:** Do NOT do blind search-replace. Some `aa` sequences are legitimate (e.g., "Bra at" should NOT become "Bra åt"). Replace word-by-word in context. Read each line.

**Step 2: Replace ASCII substitutes in persona_manager.py**

Same substitution patterns for `PERSONAS_NO` and `EMOTIONAL_MODIFIERS_NO` sections.

**Step 3: Add Norwegian character instruction to Grok prompt**

In `backend/brains/grok_brain.py`, add to the Norwegian language instruction:

```python
# In the realtime coaching prompt (around line 128), after language instruction:
if language == "no":
    context += "\n- IMPORTANT: Use proper Norwegian characters: æ, ø, å (NOT ae, oe, aa). Example: 'Kjør på!' not 'Kjoer paa!'"
```

Also add same instruction in `backend/persona_manager.py` where the Norwegian prompt is built (around line 392):

```python
prompt += "\n\nIMPORTANT: Always respond in Norwegian (Bokmål). Use proper Norwegian characters: æ, ø, å. Short, direct coaching phrases."
```

**Step 4: Sync backend to root**

```bash
cp backend/*.py . && cp -r backend/brains/*.py brains/
diff backend/config.py config.py && echo "SYNCED"
diff backend/persona_manager.py persona_manager.py && echo "SYNCED"
diff backend/brains/grok_brain.py brains/grok_brain.py && echo "SYNCED"
```

**Step 5: Verify with curl**

```bash
curl "https://treningscoach-backend.onrender.com/welcome?language=no&persona=personal_trainer"
```

Check that the returned `text` field contains æ, ø, å characters.

**Step 6: Commit**

```bash
git add backend/config.py backend/persona_manager.py backend/brains/grok_brain.py config.py persona_manager.py brains/grok_brain.py
git commit -m "fix: Norwegian message banks — use proper æ, ø, å instead of ASCII substitutes"
```

---

### Task 3: Fix Grok Brain Pool Failure Cache (Backend)

**Files:**
- Modify: `backend/brain_router.py:129-143`

**Step 1: Allow retry after cooldown expires**

The current code caches `None` in `brain_pool` permanently if init fails. Change `_get_brain_instance` to retry after cooldown:

```python
def _get_brain_instance(self, brain_name: str):
    """Get or lazily initialize a brain instance."""
    if brain_name in self.brain_pool:
        cached = self.brain_pool[brain_name]
        if cached is not None:
            return cached
        # Cached failure — retry if cooldown expired
        cooldown_until = self.brain_cooldowns.get(brain_name, 0)
        if time.time() < cooldown_until:
            return None  # Still in cooldown
        # Cooldown expired — clear cache and retry below
        del self.brain_pool[brain_name]
    try:
        brain = self._create_brain(brain_name)
        self.brain_pool[brain_name] = brain
        if brain is not None:
            print(f"✅ Brain Router: Loaded {brain_name} (model: {brain.model})")
        return brain
    except Exception as e:
        print(f"⚠️ Brain Router: Failed to initialize {brain_name}: {e}")
        self._set_cooldown(brain_name)
        self.brain_pool[brain_name] = None
        return None
```

This ensures:
- Successful inits are cached forever (no change)
- Failed inits are retried after the 60-second cooldown expires
- If `XAI_API_KEY` is added to Render while the server is running, Grok will recover on next request after cooldown

**Step 2: Sync to root**

```bash
cp backend/brain_router.py .
diff backend/brain_router.py brain_router.py && echo "SYNCED"
```

**Step 3: Verify brain health**

After deploy:
```bash
curl https://treningscoach-backend.onrender.com/brain/health
```

Check `brain_stats.grok.calls > 0`. If `XAI_API_KEY` is set, Grok should show as available.

**Step 4: Commit**

```bash
git add backend/brain_router.py brain_router.py
git commit -m "fix: brain_pool retries failed inits after cooldown instead of caching None permanently"
```

---

### Task 4: Improve Coach Silence Resilience (Backend + iOS)

**Files:**
- Verify: `backend/coaching_intelligence.py:182-186` — confirm signal_quality gate is removed
- Modify: `backend/main.py` — add logging around speak decision
- Modify: `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift:606-612` — delay first coaching tick until welcome finishes

**Step 1: Verify coaching_intelligence.py fix deployed**

```bash
curl https://treningscoach-backend.onrender.com/health
```

Then check the deployed code has the signal_quality gate removed. If it's still there, the sync from previous session didn't deploy.

```bash
diff backend/coaching_intelligence.py coaching_intelligence.py
```

**Step 2: Add delay before first coaching tick (iOS)**

The welcome message takes 3-8 seconds. The first coaching tick fires at 8 seconds. If welcome is still playing, the mic picks up speaker audio, causing bad signal quality. Add a delay:

```swift
// WorkoutViewModel.swift, around line 606-612
// Replace:
Task {
    await playWelcomeMessage()
}
scheduleNextTick()

// With:
Task {
    await playWelcomeMessage()
    // Wait 2 seconds after welcome finishes before starting coaching loop
    // This avoids the first tick picking up speaker audio from the welcome message
    try? await Task.sleep(nanoseconds: 2_000_000_000)
    scheduleNextTick()
}
```

This ensures the coaching loop doesn't start until after the welcome audio finishes playing, avoiding the mic-picks-up-speaker problem.

**Step 3: Add better logging in main.py for debugging**

In `backend/main.py`, around the speak decision (line 744-758), add more verbose logging:

```python
logger.info(f"Speak decision: should_speak={speak_decision}, reason={reason}, "
            f"signal_quality={breath_data.get('signal_quality', 'N/A')}, "
            f"elapsed_since_last={elapsed_since_last}, "
            f"is_first_breath={is_first_breath}")
```

**Step 4: Sync and commit**

```bash
cp backend/main.py . && cp backend/coaching_intelligence.py .
git add backend/main.py main.py backend/coaching_intelligence.py coaching_intelligence.py TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift
git commit -m "fix: delay coaching loop until welcome finishes, add speak decision logging"
```

---

### Task 5: Add Diagnostic Logging for Mic/Breath Pipeline (iOS)

**Files:**
- Modify: `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift:788-862`

**Step 1: Add more logging around the coaching loop**

The coaching loop already has good logging, but add a summary log at the start of each tick to confirm the loop is running:

```swift
// At the top of coachingLoopTick(), after the guard:
print("🔄 Coaching tick #\(AudioPipelineDiagnostics.shared.breathAnalysisCount + 1) at \(Int(workoutDuration))s | phase: \(currentPhase.rawValue) | interval: \(Int(coachingInterval))s")
```

And after the API call, log whether audio was returned:

```swift
// After line 821:
print("📊 Backend response: should_speak=\(response.shouldSpeak), has_audio=\(response.audioURL != nil), text_len=\(response.text.count), wait=\(response.waitSeconds)s")
```

**Step 2: Commit**

```bash
git add TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift
git commit -m "feat: add diagnostic logging to coaching loop for debugging"
```

---

## Execution Order

1. **Task 1** (Diagnostic panel) — iOS only, independent
2. **Task 2** (Norwegian æøå) — Backend, biggest change, most lines
3. **Task 3** (Grok brain_pool) — Backend, small targeted fix
4. **Task 4** (Coach silence) — Backend + iOS, depends on understanding Task 2/3
5. **Task 5** (Logging) — iOS, independent

Tasks 1, 2, 3 can be done in parallel. Task 4 should be verified after Task 3 deploys. Task 5 can be done anytime.

## Final Sync & Deploy

```bash
# Sync all backend changes to root
cp backend/*.py . && cp -r backend/brains/*.py brains/ && cp backend/requirements.txt .

# Verify sync
diff backend/main.py main.py && diff backend/config.py config.py && diff backend/brain_router.py brain_router.py && echo "ALL SYNCED"

# Push to main for auto-deploy
git push origin main
```

## Verification After Deploy

```bash
# 1. Health check
curl https://treningscoach-backend.onrender.com/health

# 2. Norwegian with proper characters
curl "https://treningscoach-backend.onrender.com/welcome?language=no"

# 3. Brain health — Grok should show calls > 0
curl https://treningscoach-backend.onrender.com/brain/health

# 4. iOS: Long-press orb → diagnostic panel appears
# 5. iOS: Coach should speak after welcome message
# 6. iOS: Norwegian voice pronounces æ, ø, å correctly
```
