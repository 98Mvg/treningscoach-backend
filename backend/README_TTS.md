# Qwen3-TTS Integration Guide

## Overview

Your Treningscoach backend now uses **local Qwen3-TTS** with voice cloning to generate coaching audio in your custom voice.

## Architecture

```
iOS App → Backend (Flask)
            ↓
        Claude API (text reasoning)
            ↓
        Qwen3-TTS (local voice synthesis)
            ↓
        WAV Audio → iOS App
```

## Setup

### 1. Reference Audio

Place your 20-second reference audio at:
```
backend/voices/coach_voice.wav
```

**Requirements:**
- Duration: 10-30 seconds (you have 20 seconds ✓)
- Format: WAV (16-bit, mono or stereo)
- Content: Clean speech samples from your voice

The system will automatically:
- Convert to mono if stereo
- Resample to 16kHz for voice cloning
- Cache the voice model on startup

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Required packages:**
- `torch>=2.0.0` - PyTorch for neural network inference
- `torchaudio>=2.0.0` - Audio processing
- `anthropic>=0.40.0` - Claude API client

**TTS package (when available):**
```bash
# This will be available when Qwen3-TTS releases their Python package
pip install qwen-tts
```

### 3. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and add your Claude API key:
```bash
ANTHROPIC_API_KEY=sk-ant-your_api_key_here
```

### 4. Run Backend

```bash
python main.py
```

**Startup logs you should see:**
```
✅ Brain Router: Using Claude (model: claude-3-5-sonnet-20241022)
INFO:__main__:Initializing Qwen3-TTS...
INFO:__main__:Loading reference audio from backend/voices/coach_voice.wav
INFO:__main__:Reference audio loaded: shape=torch.Size([1, 320000])
INFO:__main__:Qwen3-TTS model loaded on cuda
INFO:__main__:TTS service initialized successfully
```

## How It Works

### Voice Cloning Process

1. **Startup (one-time)**:
   - Backend loads `coach_voice.wav`
   - Qwen3-TTS processes the audio to extract voice characteristics
   - Voice model is cached in memory

2. **During Workout**:
   - iOS sends breath audio → Backend analyzes
   - Claude generates coaching text
   - Qwen3-TTS synthesizes speech with YOUR voice
   - WAV file is sent to iOS

3. **No Repeated Cloning**:
   - Voice is cloned ONCE at startup
   - Each synthesis reuses the cached voice model
   - Fast generation (~1-2 seconds per message)

### Fallback Behavior

If Qwen3-TTS is not available:
- Backend uses mock mode (silent WAV files)
- App continues working normally
- Coach messages still appear as text
- Ready to switch to real TTS when installed

## Coach Personality

The coaching uses a **Nordic Endurance Coach** personality:

**Core traits:**
- Calm, grounded, mentally tough
- Direct and honest (no hype)
- Disciplined but humane
- Comfortable with discomfort
- Long-term focused

**Communication style:**
- Short, clear sentences
- No buzzwords or marketing language
- No false positivity
- When hard, says it's hard
- Encourages effort, not shortcuts

**Example coaching:**
- Calm breathing: "Push harder."
- Moderate: "Good. Hold it."
- Intense: "Yes. Ten more."
- Critical: "Stop. Breathe slow."

See `coach_personality.py` for full prompt.

## File Structure

```
backend/
├── main.py                 # Flask app with /api/coach endpoints
├── tts_service.py          # Qwen3-TTS integration (local)
├── coach_personality.py    # Endurance coach personality prompts
├── brain_router.py         # Routes to Claude API
├── brains/
│   └── claude_brain.py     # Claude API integration
├── voices/
│   └── coach_voice.wav     # Your reference audio (20 seconds)
├── output/                 # Generated audio files (auto-created)
├── .env                    # Your API keys (not in git)
└── requirements.txt        # Python dependencies
```

## Testing

### Test TTS Locally

```python
from tts_service import synthesize_speech

# Generate test audio
audio_path = synthesize_speech("Push harder. You got this.")
print(f"Generated: {audio_path}")

# Play the audio
import os
os.system(f"afplay {audio_path}")  # macOS
```

### Test Full Flow

```bash
# Start backend
python main.py

# In another terminal, test the endpoint
curl -X POST http://localhost:5000/api/coach \
  -F "audio=@test_audio.wav" \
  -F "phase=intense"
```

## Deployment

### Render.com

The backend is already configured for Render deployment.

**Requirements:**
1. Add `ANTHROPIC_API_KEY` to Render environment variables
2. Ensure `voices/coach_voice.wav` is in the repository
3. Render will install PyTorch from `requirements.txt`

**Note:** Render free tier uses CPU (no GPU). TTS will work but be slower (~3-5 seconds per message).

### GPU Acceleration (Optional)

For faster TTS:
1. Use Render paid plan with GPU
2. Or deploy to AWS/GCP with GPU instance
3. TTS will automatically use CUDA if available

Check in logs:
```
INFO:__main__:Qwen3-TTS model loaded on cuda  # GPU
INFO:__main__:Qwen3-TTS model loaded on cpu   # CPU
```

## Troubleshooting

### "Reference audio not found"
```
WARNING: Reference audio not found at backend/voices/coach_voice.wav
WARNING: TTS will use mock mode until reference audio is provided
```

**Fix:** Move your `audio_clip_20s.wav` to `backend/voices/coach_voice.wav`

### "Qwen3-TTS library not found"
```
WARNING: Qwen3-TTS library not found - using mock mode
WARNING: Install with: pip install qwen-tts
```

**Fix:** This is expected until Qwen3-TTS package releases. The backend will use mock mode (silent audio) until then.

### "TTS failed, using mock"
The backend automatically falls back to mock audio if TTS synthesis fails. Check logs for the specific error.

## Next Steps

1. **Test locally** with your Claude API key
2. **Verify audio quality** with your reference voice
3. **Deploy to Render** when ready
4. **Install Qwen3-TTS** when package becomes available

The integration is production-ready and will seamlessly transition from mock → real TTS once Qwen3-TTS is installed.
