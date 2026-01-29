# iOS Testing Guide - Treningscoach

Quick guide to test your AI workout coach with voice cloning on iOS.

## 🎯 What You're Testing

Your AI workout coach that:
- Listens to your breathing during workouts
- Analyzes intensity (calm, moderate, intense, critical)
- Gives you real-time voice coaching **in your cloned voice**
- Adapts coaching based on your breathing patterns

---

## 📱 Step 1: Update iOS App Configuration

The iOS app needs to connect to your local backend server.

### Update Backend URL

1. Open `TreningsCoach/TreningsCoach/Config.swift`
2. Find the line:
   ```swift
   static let backendURL = "http://localhost:5000"
   ```
3. Change to your server's IP address:
   ```swift
   static let backendURL = "http://192.168.10.87:10000"
   ```
   *(Use the IP shown in your server logs)*

### Important for Real Device Testing

If testing on a real iPhone (not simulator):
- Make sure your iPhone and Mac are on the **same WiFi network**
- Use your Mac's local IP address (not localhost)
- Example: `http://192.168.1.100:10000`

---

## 🖥️ Step 2: Start Backend Server

Your backend is already running! Just verify:

```bash
# Check server is running
curl http://localhost:10000/health

# Should see:
# {"status": "healthy", "version": "1.1.0", ...}
```

**Server Details:**
- **Running on:** http://localhost:10000
- **Voice Cloning:** ✅ Enabled with Qwen3-TTS
- **Your Voice:** Loaded from `backend/voices/coach_voice.wav`
- **Synthesis Time:** ~6 minutes per utterance (CPU)

**Note:** Voice synthesis is SLOW on CPU. First coach response will take 5-7 minutes. This is normal! GPU would be ~2-5 seconds.

---

## 📲 Step 3: Build and Run iOS App

### Using Xcode

1. Open `TreningsCoach/TreningsCoach.xcodeproj` in Xcode
2. Select your device/simulator
3. Press **⌘R** to build and run

### Using Xcode CLI

```bash
cd TreningsCoach
xcodebuild -scheme TreningsCoach -destination 'platform=iOS Simulator,name=iPhone 15' build
```

---

## 🎤 Step 4: Test Workflow

### Test 1: Simple Coach Request (Legacy Endpoint)

1. **Tap the Voice Orb** in the app
2. **Breathe heavily** for 2-3 seconds
3. **Wait** (this will take 5-7 minutes for first synthesis)
4. **Listen** to the coach respond in your cloned voice!

**What's happening:**
- App records your breathing
- Backend analyzes intensity
- Generates coaching text based on breathing
- Clones your voice to speak the coaching
- Returns audio to iOS app

### Test 2: Continuous Coaching (Advanced)

1. **Start a workout session**
2. App automatically records 6-10 second chunks
3. Coach speaks when needed (not every cycle)
4. Coaching adapts to your breathing patterns

---

## 🐛 Troubleshooting

### "Connection refused" or "Cannot connect"

**Check:**
1. Backend server is running on port 10000
2. iOS app has correct IP address in Config.swift
3. iPhone and Mac on same WiFi (for real device)
4. Firewall not blocking port 10000

**Fix:**
```bash
# On Mac, check firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Temporarily disable if needed
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### Voice synthesis takes forever

**This is normal on CPU!** Qwen3-TTS synthesis takes:
- **CPU:** 5-7 minutes for first utterance, 3-5 minutes after
- **GPU:** 2-5 seconds

**Check progress:**
```bash
tail -f /tmp/server.log | grep "Synthesizing\|synthesized"
```

You'll see:
```
INFO - Synthesizing speech with voice cloning: 'Push harder!'
...wait 5-7 minutes...
INFO - ✅ Speech synthesized: output/coach_xxx.wav (24000Hz, 0.70s)
```

### Mock audio instead of real voice

Check server logs:
```bash
tail -20 /tmp/server.log | grep "TTS"
```

Should see:
```
✅ Qwen3-TTS model loaded on cpu
✅ TTS service initialized successfully with voice cloning
```

If you see "TTS will use mock mode", the model didn't load properly.

### No coaching response

Check breath analysis:
```bash
tail -20 /tmp/server.log | grep "intensity"
```

Should see intensity levels like: `calm`, `moderate`, `intense`, `critical`

---

## 📊 Monitoring During Testing

### Watch server logs in real-time

```bash
tail -f /tmp/server.log
```

### Check generated audio files

```bash
ls -lht backend/output/ | head -10
```

You should see files like:
```
coach_1769681387.911237.wav  (33KB) - Real voice cloning
coach_mock_xxx.wav          (172KB) - Mock audio (fallback)
```

### Test audio quality

```bash
# Play the most recent cloned voice
afplay $(ls -t backend/output/coach_*.wav | grep -v mock | head -1)
```

---

## ✅ Success Criteria

Your testing is successful when:

1. **Connection Works**
   - iOS app connects to backend
   - No "connection refused" errors

2. **Breath Analysis Works**
   - Server detects breathing intensity
   - Logs show: calm, moderate, intense, or critical

3. **Voice Cloning Works**
   - Server generates audio with your voice
   - Audio plays in iOS app
   - Quality is recognizable (even if CPU-slow)

4. **Coaching Makes Sense**
   - Messages match your breathing intensity
   - Nordic coach personality (calm, direct, honest)
   - No false positivity or hype

---

## 🚀 Performance Tips

### Speed up synthesis (optional)

1. **Use GPU** (if you have NVIDIA GPU)
   - Reduces synthesis from 6 min → 5 sec
   - Requires CUDA setup

2. **Reduce text length**
   - Shorter messages = faster synthesis
   - "Push harder." vs "You're doing great, keep pushing!"

3. **Pre-generate common phrases**
   - Cache common coaching messages
   - Instant playback for repeated phrases

### For production

- Deploy to GPU server (Render.com GPU plan)
- Or use API-based TTS (faster but costs money)
- Current setup works, just slower for development

---

## 📝 Test Checklist

- [ ] Backend server running on port 10000
- [ ] Voice cloning initialized (check logs)
- [ ] iOS app built and running
- [ ] Config.swift has correct backend URL
- [ ] Simple coach request works (waited 5-7 min)
- [ ] Voice audio is YOUR voice (quality check)
- [ ] Continuous mode works (optional)
- [ ] Coaching messages make sense

---

## 🎉 Next Steps

Once testing works:

1. **Deploy Backend** to Render.com or cloud server
2. **Update iOS Config** with production URL
3. **TestFlight Beta** - share with friends
4. **Optimize Performance** - consider GPU or API TTS
5. **Add Features** - workout history, goals, etc.

---

## 💡 Quick Reference

**Server URL:** http://localhost:10000 (or http://192.168.10.87:10000)

**Endpoints:**
- Health: `GET /health`
- Analyze: `POST /analyze` (breath analysis only)
- Coach: `POST /coach` (full workflow)
- Continuous: `POST /coach/continuous` (real-time mode)

**Expected Response Times:**
- Breath analysis: <1 second
- Coach text generation: 1-2 seconds
- Voice synthesis: 5-7 minutes (CPU) or 2-5 seconds (GPU)

**Reference Voice:** `backend/voices/coach_voice.wav` (20 seconds, 625KB)

---

Good luck with testing! 🏋️‍♂️🎙️
