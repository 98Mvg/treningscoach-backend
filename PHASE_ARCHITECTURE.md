# Workout Phase Architecture

## Overview

The TreningsCoach system adapts its behavior based on **workout phases** and **breathing intensity**. This creates a dynamic coaching experience that matches the athlete's current state.

---

## 🏃 Three Workout Phases

### 1. **Warmup Phase** (0-2 minutes)
**Purpose:** Ease into the workout, establish baseline

**Timing:**
- Duration: 120 seconds (2 minutes)
- Starts: Immediately when workout begins
- Ends: At 2:00 elapsed time

**Coach Behavior:**
- ✅ Calm, encouraging tone
- ✅ Slower coaching intervals (+2 seconds modifier)
- ✅ Focus on "steady tempo" and "easy start"
- ✅ Avoid pushing hard

**Sample Messages:**
```
"Easy start. Warming up."
"Good. Keep this pace."
"Steady tempo. Continue."
```

**Interval Timing:**
- Calm breathing: 14s (12s base + 2s warmup modifier)
- Moderate: 10s (8s base + 2s)
- Intense: 8s (6s base + 2s)
- Critical: 5s (safety override, no modifier)

---

### 2. **Intense Phase** (2-15 minutes)
**Purpose:** Hard work, push limits, build fitness

**Timing:**
- Duration: 900 seconds (15 minutes)
- Starts: At 2:00 elapsed time
- Ends: At 17:00 elapsed time

**Coach Behavior:**
- ✅ Assertive, demanding tone
- ✅ No phase modifier (let intensity drive frequency)
- ✅ Push harder if breathing is "calm" during this phase
- ✅ Encourage when "intense" or "moderate"

**Sample Messages:**
```
Calm breathing (push harder):
"PUSH! Harder!"
"You got more!"
"Faster! NOW!"

Moderate breathing (keep going):
"Keep going! Don't stop!"
"You have more in you!"
"Good! Hold the pace!"

Intense breathing (encourage):
"YES! Hold on! Ten more!"
"Perfect! Keep it up!"
"There it is! Five seconds!"
```

**Interval Timing:**
- Calm: 12s (athlete not working hard enough)
- Moderate: 8s (good work rate)
- Intense: 6s (great intensity)
- Critical: 5s (safety override)

**Special Rule:**
If breathing is "calm" during intense phase → Coach says "push_harder"

---

### 3. **Cooldown Phase** (15+ minutes)
**Purpose:** Recover, lower heart rate, end workout safely

**Timing:**
- Duration: Until workout ends
- Starts: At 17:00 elapsed time
- Ends: When user stops workout

**Coach Behavior:**
- ✅ Calm, soothing tone
- ✅ Slower intervals (+3 seconds modifier)
- ✅ Remind to slow down if still breathing intense
- ✅ Focus on recovery and ease

**Sample Messages:**
```
"Bring it down."
"Breathe easy."
"Good. Nice and easy."
```

**Interval Timing:**
- Calm: 15s (12s base + 3s cooldown modifier)
- Moderate: 11s (8s base + 3s)
- Intense: 9s (6s base + 3s)
- Critical: 5s (safety override)

**Special Rule:**
If breathing is "intense" during cooldown → Coach says "slow_down"

---

## 🎯 Breathing Intensity Levels

The system classifies breathing into 4 intensity levels:

### **Calm** (Low Intensity)
**Indicators:**
- Volume ≤ 20
- Silence ≥ 50%
- Tempo: slow, relaxed

**Coach Response:**
- Warmup: "Good, steady"
- Intense: **"PUSH HARDER!"** (not working hard enough)
- Cooldown: "Perfect, keep it calm"

**Interval:** 12s (+phase modifier)

---

### **Moderate** (Medium Intensity)
**Indicators:**
- Volume ≤ 40
- Tempo ≤ 20 BPM
- Some breathing effort visible

**Coach Response:**
- Warmup: "Nice pace"
- Intense: "Keep going! Hold it!"
- Cooldown: "Easy now, bring it down"

**Interval:** 8s (+phase modifier)

---

### **Intense** (High Intensity)
**Indicators:**
- Volume ≤ 70
- Tempo ≤ 35 BPM
- Hard breathing, significant effort

**Coach Response:**
- Warmup: "Slow down, easy warmup" (too hard too soon)
- Intense: **"YES! Perfect! Hold on!"** (ideal)
- Cooldown: **"Slow down! Recovery time"** (still too hard)

**Interval:** 6s (+phase modifier)

---

### **Critical** (Dangerous Intensity)
**Indicators:**
- Volume > 70
- Tempo > 35 BPM
- Potential hyperventilation

**Coach Response:**
- **ANY PHASE:** "STOP! Breathe slowly. You're safe."
- Safety override - always intervenes

**Interval:** 5s (no modifier, check frequently)

---

## 🧠 Coaching Intelligence Decision Tree

```
Every 8 seconds (breath recording):
    ↓
Analyze breath audio
    ↓
Classify intensity (calm/moderate/intense/critical)
    ↓
Check phase (warmup/intense/cooldown)
    ↓
Coaching Intelligence Decision:
    ├─ Critical breathing? → SPEAK (safety override)
    ├─ First breath? → SPEAK (welcome)
    ├─ No change from last breath? → SILENT
    ├─ Intense phase + calm breathing? → SPEAK ("push harder")
    ├─ Cooldown phase + intense breathing? → SPEAK ("slow down")
    ├─ Spoke < 20s ago? → SILENT (avoid over-coaching)
    └─ Significant change? → SPEAK
    ↓
If SPEAK:
    ├─ Strategic Brain available? → Get strategic guidance (every 2-3 min)
    ├─ Pattern detected? → Use pattern-based message
    └─ Default → Use config message for phase + intensity
    ↓
Generate voice (ElevenLabs, 1-2 sec)
    ↓
Return audio to iOS app
```

---

## 📊 Phase Transition Behavior

### Warmup → Intense (at 2:00)
**What happens:**
1. Phase changes from "warmup" to "intense"
2. Coaching intervals become more frequent (remove +2s modifier)
3. Messages shift from "steady" to "push"
4. If breathing is still calm → Coach starts pushing harder

**Example:**
```
1:50 - "Steady tempo. Continue." (warmup)
2:10 - "PUSH! Harder!" (intense phase, calm breathing)
```

---

### Intense → Cooldown (at 17:00)
**What happens:**
1. Phase changes from "intense" to "cooldown"
2. Coaching intervals become slower (+3s modifier)
3. Messages shift from "push" to "ease"
4. If breathing is still intense → Coach reminds to slow down

**Example:**
```
16:50 - "Perfect! Keep it up!" (intense phase, intense breathing)
17:10 - "Slow down! Recovery time" (cooldown phase, still intense breathing)
```

---

## 🎙️ Voice Intelligence Layer

### "Silent Confidence" System
**Purpose:** Optimal breathing = silence is the best coaching

**Rules:**
1. **Optimal breathing detected** → Stay silent (confidence signal)
2. **Breath pattern is stable** → Stay silent (don't interrupt flow)
3. **Just coached < 20s ago** → Stay silent (avoid over-coaching)

**When to speak:**
- Breathing becomes sub-optimal
- Safety concern (critical intensity)
- Significant pattern change
- Phase-specific intervention needed

---

## 🧠 Strategic Brain Integration

### Frequency
- **First insight:** 2 minutes into workout
- **Subsequent insights:** Every 3 minutes
- **Total in 45-min workout:** ~15 strategic insights

### What it provides
**NOT:** Raw speech text
**BUT:** Strategic guidance

```json
{
  "strategy": "reduce_overload",
  "tone": "calm_firm",
  "message_goal": "restore_rhythm",
  "suggested_phrase": "Control the exhale. Let the breath settle."
}
```

### When it overrides
Strategic Brain **suggests**, system **decides**:
- If strategic guidance available → Use strategic phrase OR config phrase matching strategy
- If no strategic guidance → Use pattern insight OR config phrase
- Config phrases always available as fallback

---

## 📈 Interval Timing Matrix

| Intensity | Base | Warmup | Intense | Cooldown |
|-----------|------|--------|---------|----------|
| **Calm** | 12s | 14s (+2s) | 12s (0s) | 15s (+3s) |
| **Moderate** | 8s | 10s (+2s) | 8s (0s) | 11s (+3s) |
| **Intense** | 6s | 8s (+2s) | 6s (0s) | 9s (+3s) |
| **Critical** | 5s | 5s (override) | 5s (override) | 5s (override) |

**Critical always = 5s** (safety first, ignore phase modifiers)

---

## 🎯 Phase-Specific Rules Summary

### Warmup Phase Rules
- ✅ Encourage steady, easy pace
- ✅ +2s to all intervals (slower coaching)
- ❌ Don't push hard
- ❌ Don't let athlete go too intense too soon

### Intense Phase Rules
- ✅ Push if breathing is calm (not working hard enough)
- ✅ Encourage when breathing is intense (ideal)
- ✅ No interval modifier (let intensity drive frequency)
- ❌ Don't over-coach (20s minimum between messages)

### Cooldown Phase Rules
- ✅ Remind to slow down if still breathing intense
- ✅ +3s to all intervals (slowest coaching)
- ✅ Calm, soothing messages
- ❌ Don't push for intensity

---

## 🔥 Strategic Brain Focus: HIGH-INTENSITY INTERVALS

**Revolutionary Moment:**
- **Target:** Minute 12-15 of intense phase
- **Athlete State:** Struggling, breathing erratic
- **Strategic Brain:** Detects 92 seconds of struggle
- **Coach Message:** "Control the exhale. Let the breath settle."
- **Result:** Breakthrough moment

**Why this works:**
1. Problem is URGENT (athlete suffering NOW)
2. Strategic Brain sees the pattern (92s struggling)
3. Tactical system provides immediate feedback (6s intervals)
4. Strategic insight provides the breakthrough guidance
5. Athlete remembers this moment forever

**"A revolutionary product wins ONE moment, not many."**

---

## 📝 Example Workout Flow

### 0:00-2:00 (Warmup)
```
0:08 - "Easy start. Warming up." (first breath, calm)
0:22 - [Silent] (calm, no change)
0:36 - [Silent] (calm, stable)
0:50 - "Steady tempo. Continue." (moderate, change detected)
1:04 - [Silent] (moderate, stable)
1:32 - "Good. Keep this pace." (still moderate)
```

### 2:00-17:00 (Intense)
```
2:08 - "PUSH! Harder!" (calm → intense phase transition)
2:16 - [Silent] (moderate, spoke 8s ago)
2:30 - "Keep going! Hold it!" (moderate → intense)
4:00 - 🧠 Strategic Brain: "Tempo is settling. Good."
7:00 - 🧠 Strategic Brain: "Control the exhale."
12:15 - 🧠 Strategic: "You're struggling. Slow the pace." (92s erratic)
```

### 17:00+ (Cooldown)
```
17:08 - "Slow down! Recovery time" (still intense)
17:23 - [Silent] (moderate → calm)
17:38 - "Breathe easy." (calm, stable)
18:00 - "Good. Nice and easy." (calm continues)
```

---

## 🎯 Key Architecture Principles

1. **Phase-driven behavior** - Different coaching for warmup/intense/cooldown
2. **Intensity-driven frequency** - Critical = 5s, Calm = 12s
3. **Silent confidence** - Optimal breathing = silence
4. **Strategic insights** - Claude every 2-3 min for high-level guidance
5. **Safety override** - Critical breathing always intervenes (5s)
6. **Avoid over-coaching** - Minimum 20s between messages
7. **Phase-specific rules** - Push in intense, calm in cooldown

---

## 📁 Files Containing Phase Logic

**Coaching Intelligence:**
- `backend/coaching_intelligence.py` - Decision logic for speaking
- `backend/voice_intelligence.py` - Silent confidence rules

**Configuration:**
- `backend/config.py` - Phase messages, timings, thresholds

**Strategic Layer:**
- `backend/strategic_brain.py` - High-level Claude insights

**iOS App:**
- `TreningsCoach/Config.swift` - Phase durations
- `TreningsCoach/ViewModels/WorkoutViewModel.swift` - Phase tracking

---

## 🚀 Production Focus

**You're building for HIGH-INTENSITY INTERVALS:**
- Minute 12-15 is the target moment
- Strategic Brain detects struggle patterns
- Tactical system provides immediate support
- Breakthrough coaching at the hardest moment

**"The AI coach that gets you through the hardest moments."**

Not a breathing app. A personal elite coach when you need them most.

---

**Phase architecture is your competitive advantage.**
**Own the hardest moment. Everything else follows.**
