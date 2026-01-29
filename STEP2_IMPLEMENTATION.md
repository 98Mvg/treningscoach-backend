# STEP 2 Implementation: Coaching Intensity Levels

## ✅ COMPLETED

**Goal:** Make the coach feel personal by adapting tone, sentence length, and frequency based on breathing intensity.

## What Changed

### 1. Intensity-Driven Frequency (coaching_intelligence.py:93-147)

The coaching loop now adapts its check frequency based on intensity, NOT phase:

| Intensity | Interval | Personality | Use Case |
|-----------|----------|-------------|----------|
| **kritisk** | 5s | FIRM, safety-first | User breathing dangerously hard - urgent monitoring |
| **hard** | 6s | ASSERTIVE, focused | User working hard - frequent affirmation |
| **moderat** | 8s | GUIDING, encouraging | User at good pace - balanced support |
| **rolig** | 12s | REASSURING, calm | User too relaxed - give space but encourage |

**Phase modifiers** (subtle adjustments):
- Warmup: +2s (slower, gentle start)
- Intense: +0s (intensity drives everything)
- Cooldown: +3s (slower, recovery focus)

**Critical override:** `kritisk` ALWAYS returns 5s, ignoring phase modifiers (safety-first).

### 2. Message Personality (config.py:112-161)

Messages now reflect intensity-specific personalities:

#### kritisk → FIRM, URGENT (1-3 words)
```python
["STOP!", "Breathe slow!", "Easy now!", "Slow down!", "Too hard!"]
```
- **Character:** Direct, commanding, safety-focused
- **Length:** 1-3 words (urgent = concise)
- **Example:** "STOP!" (1 word, immediate action)

#### hard during intense → ASSERTIVE, FOCUSED (2-3 words)
```python
["Perfect! Hold it!", "Yes! Strong!", "Keep this!", "Excellent work!", "Ten more seconds!"]
```
- **Character:** Celebratory, focused, direct motivation
- **Length:** 2-3 words (concise affirmation)
- **Example:** "Perfect! Hold it!" (3 words, focused)

#### moderat during intense → GUIDING, ENCOURAGING (2-4 words)
```python
["Keep going, good pace!", "Stay with it!", "Nice rhythm, maintain!", "You got this!", "Good work, keep steady!"]
```
- **Character:** Supportive, guiding, encouraging
- **Length:** 2-4 words (balanced)
- **Example:** "Keep going, good pace!" (4 words, encouraging)

#### rolig during intense → REASSURING, CALM (3-5 words)
```python
["You can push harder!", "More effort, you got this!", "Speed up a bit!", "Give me more power!", "Let's pick up the pace!"]
```
- **Character:** Gentle encouragement, reassuring tone
- **Length:** 3-5 words (conversational)
- **Example:** "You can push harder!" (4 words, reassuring but motivating)

#### warmup/cooldown → REASSURING, CALM (3-5 words)
```python
# Warmup
["Easy pace, nice start.", "Steady, good warmup.", "Gentle, keep warming up.", "Nice and easy.", "Perfect warmup pace."]

# Cooldown
["Bring it down, easy now.", "Slow breaths, good cooldown.", "Ease off, nice work.", "Almost done, slow it.", "Perfect, keep slowing down."]
```
- **Character:** Calm, reassuring, patient
- **Length:** 3-5 words (relaxed pacing)

### 3. iOS Configuration Update (Config.swift:83)

Updated minimum interval to match backend:
```swift
static let minInterval: TimeInterval = 5.0  // STEP 2: kritisk = 5s (urgent)
```

## How It Feels

### Same Workout, Different Experience

**Scenario:** User is in INTENSE phase

1. **User breathing calmly (rolig):**
   - ⏱️ Checks every 12s
   - 💬 "You can push harder!" (reassuring encouragement)
   - 🎭 Coach gives space but motivates

2. **User picks up pace (moderat):**
   - ⏱️ Checks every 8s
   - 💬 "Keep going, good pace!" (guiding support)
   - 🎭 Coach actively supports effort

3. **User working hard (hard):**
   - ⏱️ Checks every 6s
   - 💬 "Perfect! Hold it!" (assertive celebration)
   - 🎭 Coach celebrates intensity

4. **User breathing too hard (kritisk):**
   - ⏱️ Checks every 5s (URGENT)
   - 💬 "STOP!" (firm safety command)
   - 🎭 Coach prioritizes wellbeing

## Verification

Run the test suite:
```bash
cd backend
python3 test_intensity_levels.py
```

### Test Results

✅ **Interval Tests:** All 9 intensity/phase combinations return correct intervals (5s-15s)

✅ **Message Length Tests:**
- kritisk: 1-3 words ✅
- hard: 2-3 words ✅
- moderat: 2-4 words ✅
- rolig: 3-5 words ✅

✅ **Personality Comparison:** Same workout demonstrates 4 distinct coaching personalities

## Files Modified

### Backend
1. `/Users/mariusgaarder/Documents/treningscoach/backend/coaching_intelligence.py`
   - Function: `calculate_next_interval()` (lines 93-147)
   - Changed from phase-driven to intensity-driven intervals

2. `/Users/mariusgaarder/Documents/treningscoach/backend/config.py`
   - Section: `CONTINUOUS_COACH_MESSAGES` (lines 112-161)
   - Enhanced messages with intensity-specific personalities

### iOS
3. `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Config.swift`
   - Line 83: `minInterval = 5.0` (was 6.0)

### Tests
4. `/Users/mariusgaarder/Documents/treningscoach/backend/test_intensity_levels.py` (NEW)
   - Comprehensive test suite for STEP 2 verification

## Key Design Decisions

### 1. Intensity Over Phase
**Why:** Breathing intensity is a more immediate indicator of user state than workout phase. A user can be "kritisk" during warmup (bad) or "rolig" during intense (not pushing enough).

**Before (Phase-driven):**
```python
if phase == "warmup": return 10
elif phase == "intense": return 8
elif phase == "cooldown": return 12
```

**After (Intensity-driven):**
```python
if intensitet == "kritisk": return 5
elif intensitet == "hard": return 6
elif intensitet == "moderat": return 8
elif intensitet == "rolig": return 12
# Then apply phase modifiers
```

### 2. Critical Override
`kritisk` ALWAYS returns 5s, ignoring phase modifiers. Safety is paramount.

### 3. Message Length = Urgency
Urgent situations require fewer words:
- kritisk: "STOP!" (1 word)
- hard: "Perfect! Hold it!" (3 words)
- rolig: "You can push harder!" (4 words)

### 4. Clamping
Intervals clamped to 5-15s range to prevent too-frequent (annoying) or too-slow (useless) coaching.

## Impact

### Before STEP 2
Coach spoke every 8 seconds with similar messages, regardless of breathing intensity. Felt robotic and generic.

### After STEP 2
Coach adapts in real-time:
- **Frequency:** 5s (urgent) → 15s (relaxed)
- **Tone:** Firm → Assertive → Guiding → Reassuring
- **Length:** 1 word (urgent) → 5 words (conversational)

Result: **Same workout feels different based on breathing state.** The coach becomes a responsive companion rather than a timer-based announcer.

## Next Steps (Future Enhancements)

1. **Test with iOS app** during real workouts
2. **Gather user feedback** on intensity differences
3. **Tune intervals** if needed (currently 5s-15s feels good on paper)
4. **Add more message variations** per intensity level
5. **Consider dynamic TTS speed** (kritisk = fast speech, rolig = slower speech)

## Success Criteria (from User Requirements)

✅ **Done when:**
- ✅ Same workout feels different depending on breathing state
- ✅ "kritisk" feels urgent, not verbose (1-3 words, 5s intervals)
- ✅ Tone adapts: rolig → reassuring | moderat → guiding | hard → assertive | kritisk → firm
- ✅ Sentence length adapts: kritisk (1-3) < hard (2-3) < moderat (2-4) < rolig (3-5)
- ✅ Frequency adapts: kritisk (5s) < hard (6s) < moderat (8s) < rolig (12s)

---

**Implementation Date:** 2026-01-28
**Status:** ✅ Complete and Tested
**Backend:** Updated and running on port 5001
**iOS:** Config updated, ready for testing
