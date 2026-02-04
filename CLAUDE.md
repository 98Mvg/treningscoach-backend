# Treningscoach - Claude Quick Reference Guide

## Project Overview
AI workout coaching app with real-time voice feedback.
- **iOS App**: SwiftUI in `/TreningsCoach/`
- **Backend**: Flask/Python deployed to Render

---

## CRITICAL: Render Deployment Architecture

### File Structure (IMPORTANT!)
```
treningscoach/           <- ROOT (Render deploys from HERE)
├── main.py              <- MAIN BACKEND FILE (Render uses this!)
├── requirements.txt     <- DEPENDENCIES (must be complete!)
├── Procfile             <- "web: gunicorn main:app"
├── *.py                 <- All Python modules must be in ROOT
├── brains/              <- Brain modules
├── backend/             <- DEVELOPMENT copy (NOT used by Render)
│   └── main.py          <- Dev version (sync to root when changing)
└── TreningsCoach/       <- iOS App (Xcode project)
```

### Render Deployment Rules
1. **Render uses ROOT directory**, not `backend/`
2. **Procfile** in root says `gunicorn main:app` - runs `main.py` from root
3. **All Python files** must be copied from `backend/` to root for deployment
4. **requirements.txt** in root must have ALL dependencies
5. **Auto-deploy** is enabled - pushes to `main` branch trigger deploys

### When Backend Code Changes:
```bash
# 1. Make changes in backend/
# 2. Copy to root:
cp backend/*.py .
cp backend/requirements.txt .

# 3. Commit and push:
git add *.py requirements.txt
git commit -m "Sync backend to root for Render"
git push
```

### Check Deployment Status:
```bash
# Health check (shows version + endpoints)
curl https://treningscoach-backend.onrender.com/health

# Test specific endpoint
curl https://treningscoach-backend.onrender.com/welcome?language=en
```

### If Deploy Fails:
1. Check Render dashboard for error logs
2. Common issues:
   - Missing module → copy from `backend/` to root
   - Missing dependency → add to `requirements.txt`
   - Import error → check module exists in root

---

## iOS App Structure

### Key Files:
- `TreningsCoachApp.swift` - Entry point, onboarding flow
- `WorkoutViewModel.swift` - Main workout logic
- `ContinuousRecordingManager.swift` - Audio recording
- `BackendAPIService.swift` - API calls to backend
- `Config.swift` - Backend URL, timings

### Common iOS Issues:

#### Error -10875 (Audio Session)
**Cause**: Conflicting audio session categories
**Fix**: Deactivate session before changing category:
```swift
try? audioSession.setActive(false)
try audioSession.setCategory(.playAndRecord, ...)
try audioSession.setActive(true)
```

#### Onboarding Not Showing
**Cause**: `has_completed_onboarding` is true in UserDefaults
**Fix**: Delete app or reset UserDefaults

---

## Backend API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check + version |
| `/welcome` | GET | Welcome message + audio |
| `/coach` | POST | Main coaching (audio in, voice out) |
| `/coach/continuous` | POST | Continuous workout coaching |
| `/download/<file>` | GET | Download generated audio |

---

## Quick Commands

### Check Backend Health:
```bash
curl https://treningscoach-backend.onrender.com/health
```

### Test Welcome Endpoint:
```bash
curl "https://treningscoach-backend.onrender.com/welcome?language=en"
```

### Sync Backend to Root:
```bash
cp backend/*.py . && cp backend/requirements.txt .
git add *.py requirements.txt && git commit -m "Sync" && git push
```

### Check Git Status:
```bash
git status
git log --oneline -5
```

---

## Environment Variables (Render Dashboard)
- `ANTHROPIC_API_KEY` - Claude API key
- `ELEVENLABS_API_KEY` - ElevenLabs TTS key
- `ELEVENLABS_VOICE_ID` - Voice ID for English
- `ELEVENLABS_VOICE_ID_NO` - Voice ID for Norwegian

---

## Troubleshooting Checklist

### Backend Not Updating After Push:
1. Check Render dashboard - is deploy in progress?
2. Check if deploy failed - read error logs
3. Verify `main.py` in ROOT has changes (not just `backend/main.py`)
4. Verify `requirements.txt` in ROOT has all dependencies

### iOS App Crashes on Workout Start:
1. Check Xcode console for error code
2. Error -10875 = audio session conflict (see fix above)
3. Check microphone permissions in Info.plist

### No Welcome Voice:
1. Check `/welcome` endpoint exists: `curl .../health`
2. Check backend logs for TTS errors
3. Verify ELEVENLABS_API_KEY is set in Render
