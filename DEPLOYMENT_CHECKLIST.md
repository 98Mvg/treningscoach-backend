# Deployment Checklist

## ✅ Pre-Deployment (Completed)

- [x] Local Qwen3-TTS integration implemented
- [x] Endurance coach personality created
- [x] Claude brain updated with personality prompts
- [x] iOS app updated for WAV format
- [x] Reference audio moved to `backend/voices/coach_voice.wav`
- [x] Requirements.txt updated
- [x] .env.example updated

## 📋 Deployment Steps

### Step 1: Local Testing

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment (if not already done)
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-your_key_here

# Run backend
python main.py
```

**Expected output:**
```
✅ Brain Router: Using Claude (model: claude-3-5-sonnet-20241022)
INFO: Initializing Qwen3-TTS...
INFO: Loading reference audio from backend/voices/coach_voice.wav
INFO: Reference audio loaded: shape=torch.Size([1, 320000])
WARNING: Qwen3-TTS library not found - using mock mode
INFO: TTS service initialized
```

*Note: "using mock mode" is expected until Qwen3-TTS package is installed*

### Step 2: Test API Endpoint

```bash
# In another terminal, test the health endpoint
curl http://localhost:5000/health | jq

# Expected response:
{
  "status": "healthy",
  "version": "1.1.0",
  "timestamp": "2024-01-28T..."
}
```

### Step 3: Test with iOS App

1. Open Xcode project
2. Update backend URL in Config.swift (if testing locally):
   ```swift
   static let backendURL = "http://localhost:5001"
   ```
3. Run app in simulator
4. Tap the voice orb to start continuous workout
5. Verify:
   - Breath audio is recorded
   - Coach text appears
   - Audio plays (silent in mock mode)

### Step 4: Commit Changes

```bash
cd /Users/mariusgaarder/Documents/treningscoach

# Check what changed
git status

# Stage all changes
git add .

# Commit
git commit -m "Add local Qwen3-TTS integration with endurance coach personality

- Implemented local TTS service with voice cloning
- Created Nordic endurance coach personality system
- Updated Claude brain to use personality prompts
- Changed iOS app to handle WAV instead of MP3
- Added reference audio at backend/voices/coach_voice.wav
- Updated requirements.txt for PyTorch/torchaudio
- Ready for deployment (works in mock mode until Qwen3-TTS package available)"

# Push to GitHub
git push origin main
```

### Step 5: Deploy to Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Add Environment Variable**:
   - Navigate to your backend service
   - Go to "Environment" tab
   - Add new variable:
     ```
     ANTHROPIC_API_KEY=sk-ant-your_actual_key_here
     ```
   - Save

3. **Trigger Deploy**:
   - Render will auto-deploy on git push, OR
   - Click "Manual Deploy" → "Deploy latest commit"

4. **Monitor Deployment**:
   - Watch logs for:
     ```
     ✅ Brain Router: Using Claude
     INFO: Initializing Qwen3-TTS...
     INFO: Loading reference audio from backend/voices/coach_voice.wav
     INFO: Reference audio loaded: shape=torch.Size([1, 320000])
     WARNING: Qwen3-TTS library not found - using mock mode
     ```

5. **Verify Deployment**:
   ```bash
   # Test health endpoint
   curl https://treningscoach-backend.onrender.com/health | jq
   ```

### Step 6: Update iOS App for Production

1. In `Config.swift`, ensure production URL is active:
   ```swift
   static let backendURL = productionURL  // ✓
   ```

2. Build and test app with production backend

3. Verify continuous coaching works end-to-end

## 🔄 Future: Installing Real Qwen3-TTS

When Qwen3-TTS Python package becomes available:

### On Render

1. **Update requirements.txt**:
   ```txt
   # Add to requirements.txt
   qwen-tts>=1.0.0
   ```

2. **Redeploy** - Render will install the package

3. **Verify in logs**:
   ```
   INFO: Qwen3-TTS model loaded on cpu
   ✅ TTS service initialized successfully
   ```

4. **Test voice quality** - Coach will now speak in YOUR voice

### Locally

```bash
# Install package
pip install qwen-tts

# Restart backend
python main.py
```

The system will automatically detect the package and switch from mock → real TTS.

## 🎯 Current Status

### What Works Now (Mock Mode)
- ✅ Backend runs successfully
- ✅ Claude generates coaching text with endurance personality
- ✅ TTS service generates WAV files (silent placeholders)
- ✅ iOS app receives and displays coaching messages
- ✅ Full API flow works end-to-end

### What Activates Later (Real TTS)
- 🔄 Voice synthesis with YOUR cloned voice
- 🔄 Actual audio playback in app
- 🔄 Speech matches coaching text

## 📊 Monitoring

### Key Logs to Watch

**Successful startup:**
```
✅ Brain Router: Using Claude
INFO: Reference audio loaded: shape=torch.Size([1, 320000])
INFO: TTS service initialized
```

**During workout:**
```
🎤 Coaching tick: 15s, phase: intense
📊 Analysis: moderate, should_speak: True, reason: push_harder
🗣️ Coach speaking: 'Push harder.'
```

**Errors to investigate:**
```
❌ Coaching cycle failed: [error message]
⚠️ No audio chunk available, retrying next tick
⚠️ Reference audio not found
```

## 🆘 Troubleshooting

### Issue: "Reference audio not found"
**Fix:** Ensure `backend/voices/coach_voice.wav` exists in repository

### Issue: "Failed to initialize TTS"
**Expected:** This is normal until Qwen3-TTS package is installed
**Status:** Backend will use mock mode

### Issue: Claude API errors
**Fix:** Check `ANTHROPIC_API_KEY` in Render environment variables

### Issue: iOS can't connect to backend
**Fix:** Verify `Config.swift` has correct backend URL

## 📝 Notes

- Backend works in **mock mode** until Qwen3-TTS is installed
- No code changes needed when switching mock → real TTS
- Reference audio is **625KB** (well within GitHub limits)
- PyTorch will install on Render (takes ~2 minutes)
- First TTS synthesis may be slower (~5 seconds) as model loads

## ✅ Deployment Complete When...

- [ ] Backend deployed to Render successfully
- [ ] Health endpoint returns 200
- [ ] iOS app connects to production backend
- [ ] Continuous workout mode works
- [ ] Coach messages display correctly
- [ ] No errors in Render logs

---

**You're ready to deploy!** 🚀
