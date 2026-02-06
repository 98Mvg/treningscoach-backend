# AI Coaching Test Guide

This guide helps you test Claude AI coaching on both the iOS app and website.

## Prerequisites

1. **Backend must be running**: https://treningscoach-backend.onrender.com
2. **Environment variables set on Render**:
   - `ANTHROPIC_API_KEY` - Your Claude API key
   - `ELEVENLABS_API_KEY` - Your ElevenLabs TTS key
   - `ELEVENLABS_VOICE_ID` - Voice ID for English
   - `ELEVENLABS_VOICE_ID_NO` - Voice ID for Norwegian

## Quick Health Check

Before testing, verify the backend is healthy:

```bash
curl https://treningscoach-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0",
  "endpoints": ["/health", "/welcome", "/coach", "/coach/continuous", ...]
}
```

---

## Testing on Website

### 1. Open the Website
Navigate to: https://treningscoach-backend.onrender.com

### 2. Start a Workout
- Click the purple microphone orb
- **Allow microphone access** when browser prompts
- The UI should transform into the workout player

### 3. What to Expect

**Immediately:**
- Welcome message plays (voice)
- Timer starts counting
- Status shows "Workout Active"

**Every 8 seconds:**
- App sends audio to backend
- Claude AI analyzes your breathing
- If `should_speak: true`, you'll hear coach feedback

**Voice Responses:**
- Claude decides when to speak based on:
  - Workout phase (warmup/intense/cooldown)
  - Breathing intensity
  - Time since last coaching
  - Context awareness (no repetition)

### 4. Test Controls
- **Pause button**: Should pause recording and timer
- **Resume**: Should continue from where you left off
- **Stop**: Should end workout and return to orb

### 5. Check Browser Console
Open DevTools (F12) → Console tab

Look for:
```
✅ Welcome: "Let's warm up! Focus on deep, controlled breaths..."
✅ Coach response: "Good breathing rhythm. Keep it steady."
✅ Should speak: true
```

---

## Testing on iOS App

### 1. Open Xcode
```bash
cd /Users/mariusgaarder/Documents/treningscoach/TreningsCoach
open TreningsCoach.xcodeproj
```

### 2. Check Backend URL
File: `TreningsCoach/Config.swift`

Verify:
```swift
static let backendURL = productionURL  // Should point to Render
```

### 3. Build and Run
- Select your device or simulator
- Press ⌘R to build and run
- App should launch successfully

### 4. Start a Workout
- Tap the purple microphone orb
- **Allow microphone access** when iOS prompts
- Orb transforms into workout player

### 5. What to Expect

**Immediately:**
- Welcome message plays
- Progress ring appears
- Timer starts (00:00)
- Phase indicator shows "Warm-up"

**Every 8 seconds:**
- Audio sent to backend
- Breath analysis updates (intensity badge)
- Coach may speak if needed

**UI Elements:**
- Timer in center
- Progress ring fills gradually
- Play/pause button pulses when active
- Stop button to end workout

### 6. Check Xcode Console
Look for logs:
```
✅ Continuous workout started - session: session_abc123
🎤 Coaching tick: 8s, phase: warmup
📊 Analysis: moderate, should_speak: true, reason: welcome
🗣️ Coach speaking: 'Let's begin with some easy breathing...'
⏱️ Next tick in: 8s
```

---

## What Claude AI Does

### Analysis Phase
Every 8 seconds, Claude receives:
- **Audio chunk**: Your breathing sounds
- **Context**: Workout phase, elapsed time, previous coaching
- **User profile**: Training level, language

### Decision Making
Claude decides whether to speak based on:
1. **Breath intensity**: Is user struggling or doing well?
2. **Timing**: Enough time since last coaching?
3. **Phase**: Different guidance for warmup/intense/cooldown
4. **Patterns**: Avoid repetitive advice

### Voice Output
If `should_speak: true`:
- ElevenLabs generates natural voice
- Audio plays automatically
- Coach message updates in UI

---

## Troubleshooting

### Website: No voice response

**Check:**
1. Browser console for errors
2. Microphone permission granted
3. Audio playing (unmute browser)
4. Backend health endpoint

**Debug:**
```javascript
// In browser console
console.log('Session ID:', sessionId);
console.log('Recording active:', mediaRecorder?.state);
```

### iOS: Audio error -10875

**Fix:**
```swift
// Already handled in ContinuousRecordingManager
// Deactivates session before changing category
```

### Backend: "No ANTHROPIC_API_KEY"

**Fix on Render Dashboard:**
1. Go to https://dashboard.render.com
2. Select your service
3. Environment → Add `ANTHROPIC_API_KEY`
4. Redeploy

### No coaching responses

**Possible reasons:**
1. Silent audio (too quiet to analyze)
2. Claude decided not to speak (check `reason` field)
3. API quota exceeded
4. Network error

**Test manually:**
```bash
# Send test audio
curl -X POST https://treningscoach-backend.onrender.com/coach/continuous \
  -F "audio=@test.wav" \
  -F "session_id=test123" \
  -F "phase=warmup"
```

---

## Expected Claude Responses

### Warmup Phase (0-2 min)
- "Let's start with gentle breathing"
- "Focus on deep, controlled breaths"
- "Take your time warming up"

### Intense Phase (2-15 min)
- "Push harder, you've got this!"
- "Maintain that intensity!"
- "Great breathing rhythm!"

### Cooldown Phase (15+ min)
- "Nice work, let's slow it down"
- "Deep breaths to recover"
- "You crushed it!"

### When Silent
Claude may choose not to speak:
- Breathing is stable
- Too soon after last coaching
- User is doing well without guidance

---

## Success Criteria

✅ **Website works if:**
- Microphone access granted
- Timer updates every second
- Welcome message plays
- Coach speaks at appropriate times
- Console shows successful API calls

✅ **iOS app works if:**
- Audio session configures correctly
- Progress ring animates
- Phase transitions automatically
- Voice playback works
- Xcode shows successful coaching cycles

✅ **Claude AI works if:**
- Contextual responses (not repetitive)
- Appropriate timing (not too frequent)
- Phase-aware coaching
- Human-like variation in language

---

## Quick Test Script

### Browser (DevTools Console)
```javascript
// Check if recording works
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => console.log('✅ Mic access granted'))
  .catch(err => console.error('❌ Mic error:', err));
```

### Backend API
```bash
# Test welcome endpoint
curl https://treningscoach-backend.onrender.com/welcome?language=en

# Test health
curl https://treningscoach-backend.onrender.com/health
```

---

## Notes

- **First load**: Render may take 30s to wake up (cold start)
- **Audio format**: Website sends WebM, iOS sends WAV
- **Coaching interval**: 8 seconds (configurable in backend)
- **Max workout**: 45 minutes (auto-timeout)

Enjoy testing your AI coach! 🏋️‍♂️
