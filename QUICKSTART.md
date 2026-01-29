# 🚀 Quickstart Guide

## What You Have

A **complete voice-cloning workout coach** with:
- **Claude API** for intelligent coaching (Nordic endurance coach personality)
- **Qwen3-TTS** for voice synthesis with YOUR voice
- **FastAPI** backend serving iOS app
- **20-second reference audio** ready for voice cloning

## Architecture

```
iOS App (breath audio)
    ↓
FastAPI Backend
    ↓
Claude API (coaching text with personality)
    ↓
Qwen3-TTS (synthesize in YOUR voice)
    ↓
WAV Audio → iOS App
```

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**What installs:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `anthropic` - Claude API client
- `torch` - PyTorch for neural networks
- `soundfile` - Audio I/O
- `qwen-tts` - Qwen3-TTS voice cloning

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Claude API key
# Get key from: https://console.anthropic.com/
nano .env
```

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-your_actual_key_here
```

### 3. Verify Reference Audio

```bash
# Check that reference audio exists
ls -lh voices/coach_voice.wav

# Should show: ~625KB WAV file
```

### 4. Start Server

```bash
# Option 1: Use start script
./start.sh

# Option 2: Manual start
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Expected startup output:**
```
==================================================
🎯 Treningscoach Backend v1.2.0
==================================================
✅ FastAPI server ready
✅ Claude API configured
🎤 Loading Qwen3-TTS model...
✅ Qwen3-TTS loaded on cuda
✅ Reference audio: voices/coach_voice.wav
✅ Coach personality: Nordic Endurance Coach
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test It

```bash
# Health check
curl http://localhost:8000/health | jq

# Expected response:
{
  "status": "healthy",
  "version": "1.2.0",
  "services": {
    "claude": true,
    "qwen3_tts": true,
    "reference_audio": true
  }
}
```

## Testing the Full Pipeline

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Should return `status: healthy` with all services `true`.

### Test 2: Coach Endpoint (Simple)

```bash
# Create a test audio file (2 seconds of silence)
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 2 -q:a 9 -acodec pcm_s16le test_breath.wav

# Send to coach endpoint
curl -X POST http://localhost:8000/api/coach \
  -F "audio=@test_breath.wav" \
  -F "phase=intense" \
  -F "mode=realtime_coach" \
  --output coach_response.wav

# Play the response (macOS)
afplay coach_response.wav
```

You should hear YOUR voice speaking coaching text!

### Test 3: Check Response Headers

```bash
curl -X POST http://localhost:8000/api/coach \
  -F "audio=@test_breath.wav" \
  -F "phase=intense" \
  -F "mode=realtime_coach" \
  -I

# Look for headers:
# X-Coach-Text: Push harder.
# X-Breath-Intensity: calm
```

## iOS App Integration

### Update Backend URL

In `TreningsCoach/TreningsCoach/Config.swift`:

```swift
// For local testing
static let backendURL = "http://localhost:8000"

// For production (after deploying)
static let backendURL = "https://your-app.onrender.com"
```

### Test Continuous Coaching

1. Open Xcode project
2. Run app in simulator
3. Tap voice orb to start workout
4. Speak/breathe into microphone
5. Listen for coach responses in YOUR voice!

## Coach Personality

The coach uses a **Nordic Endurance Coach** persona:

**Traits:**
- Calm, grounded, mentally tough
- Direct and honest (no hype)
- Disciplined but humane
- Comfortable with discomfort

**Example responses:**
- Calm breathing: "Push harder."
- Moderate: "Good. Hold it."
- Intense: "Yes. Ten more."
- Critical: "Stop. Breathe slow."

See `coach_personality.py` for full prompt.

## Troubleshooting

### "Reference audio not found"
```bash
# Move reference audio to correct location
mkdir -p voices
cp reference_audio/coach_voice.wav voices/
```

### "ANTHROPIC_API_KEY not found"
```bash
# Check .env file exists and has key
cat .env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### "CUDA out of memory"
```bash
# In .env, force CPU mode
echo "DEVICE=cpu" >> .env

# Restart server
```

### "Module 'qwen_tts' not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install directly
pip install qwen-tts
```

## Performance

### First Request (Voice Cloning)
- **Time**: ~5-10 seconds
- **What happens**: Qwen3 processes reference audio and extracts voice characteristics
- **Cached**: Voice model stays in memory for future requests

### Subsequent Requests
- **Time**: ~1-2 seconds
- **What happens**: Text → Speech synthesis only
- **Cached**: Voice model reused from memory

### GPU vs CPU
- **GPU (CUDA)**: ~1-2 seconds per synthesis
- **CPU**: ~3-5 seconds per synthesis
- Both work fine for continuous coaching (5-15 second intervals)

## Deployment

### Render.com

1. **Push to GitHub** (reference audio included at `backend/voices/coach_voice.wav`)

2. **Create new Web Service** in Render dashboard

3. **Configure:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     ```
     ANTHROPIC_API_KEY=sk-ant-your_key_here
     DEVICE=cpu
     ```

4. **Deploy** - First deploy takes ~5 minutes (installing PyTorch)

5. **Test production endpoint:**
   ```bash
   curl https://your-app.onrender.com/health
   ```

### GPU Deployment (Optional)

For faster TTS on Render:
- Use paid plan with GPU
- Set `DEVICE=cuda` in environment
- TTS will be ~3x faster

## Next Steps

1. ✅ **Backend running** - Server starts successfully
2. ✅ **Claude responding** - Coaching text generates
3. ✅ **Qwen3 synthesizing** - Audio plays in your voice
4. 🎯 **Test with iOS app** - Full end-to-end flow
5. 🚀 **Deploy to production** - Make it accessible online

---

**You're ready!** Start the server with `./start.sh` and test with the iOS app.
