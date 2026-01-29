# 🏋️ Treningscoach - Complete Project

AI-powered workout coaching system with ChatGPT-like voice UI and real-time breath analysis.

## 📁 Project Structure

```
treningscoach/
├── backend/                    # Flask API for audio analysis
│   ├── config.py              # 🎨 Easy customization (colors, messages, timings)
│   ├── main.py                # Main application
│   ├── requirements.txt
│   ├── Procfile
│   ├── runtime.txt
│   ├── README.md
│   └── DEPLOYMENT.md
│
├── TreningsCoach/             # iOS SwiftUI application
│   ├── TreningsCoach/
│   │   ├── Config.swift       # 🎨 Easy customization (iOS settings)
│   │   ├── TreningsCoachApp.swift
│   │   ├── Views/
│   │   │   ├── ContentView.swift
│   │   │   └── VoiceOrbView.swift  # Main voice orb component
│   │   ├── ViewModels/
│   │   │   └── WorkoutViewModel.swift
│   │   ├── Services/
│   │   │   ├── AudioRecordingManager.swift
│   │   │   └── BackendAPIService.swift
│   │   └── Models/
│   │       └── Models.swift
│   └── TreningsCoach.xcodeproj
│
├── CUSTOMIZATION.md          # 🎨 Complete customization guide
└── README.md                 # This file
```

## 🎨 Customization Made Easy

**All customization in two files:**
- `backend/config.py` - Backend settings, messages, colors
- `TreningsCoach/TreningsCoach/Config.swift` - iOS settings

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for the complete guide!

## 🎯 System Overview

### How It Works

1. **iOS App records breathing** during workout
2. **Audio sent to Flask backend** for analysis
3. **Python analyzes** volume, tempo, silence patterns
4. **AI coach generates** motivational feedback
5. **Voice response** played back to user

### Architecture

```
┌─────────────┐
│  iOS App    │
│  (SwiftUI)  │
└──────┬──────┘
       │ Audio (WAV)
       ↓
┌─────────────┐
│   Backend   │
│  (Flask)    │
└──────┬──────┘
       │ Analysis
       ↓
┌─────────────┐
│   Coach     │
│   Logic     │
└──────┬──────┘
       │ Voice
       ↓
┌─────────────┐
│  iOS App    │
│  (Playback) │
└─────────────┘
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip3 install -r requirements.txt
PORT=5001 python3 main.py
```

Backend runs at: `http://localhost:5001`

### iOS App Setup

```bash
cd ios-app
open TreningsCoach.xcodeproj
```

Then press `Cmd + R` in Xcode to build and run.

## 🌐 Production URLs

- **Backend API:** https://treningscoach-backend.onrender.com
- **GitHub:** https://github.com/98Mvg/treningscoach-backend

## 📋 Features

### Backend (Python/Flask)
- ✅ Audio file processing (WAV/MP3/M4A)
- ✅ Breath pattern analysis
- ✅ Intensity classification (rolig, moderat, hard, kritisk)
- ✅ Dynamic coaching responses
- ✅ Voice generation (placeholder for PersonaPlex)
- ✅ RESTful API with CORS support
- ✅ Comprehensive logging
- ✅ Error handling and validation

### iOS App (Swift/SwiftUI)
- ✅ Real-time audio recording
- ✅ Microphone permission handling
- ✅ Workout phase selection (warmup/intense/cooldown)
- ✅ Beautiful animated UI
- ✅ Breath metrics visualization
- ✅ Voice playback
- ✅ Error handling

## 🛠️ Tech Stack

### Backend
- **Language:** Python 3.11
- **Framework:** Flask 3.0
- **Audio:** wave (built-in)
- **Hosting:** Render
- **CI/CD:** GitHub → Render auto-deploy

### iOS
- **Language:** Swift 5.9
- **Framework:** SwiftUI
- **Audio:** AVFoundation
- **Min iOS:** 17.0+
- **Architecture:** MVVM

## 📊 API Endpoints

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "timestamp": "2026-01-27T..."
}
```

### POST /analyze
Analyze audio only

**Request:**
- `audio`: Audio file (WAV/MP3/M4A)

**Response:**
```json
{
  "stillhet": 50.0,
  "volum": 30.0,
  "tempo": 15.0,
  "intensitet": "moderat",
  "varighet": 2.0
}
```

### POST /coach
Get coaching feedback

**Request:**
- `audio`: Audio file
- `phase`: "warmup", "intense", or "cooldown"

**Response:**
```json
{
  "text": "PUSH! Hardere!",
  "breath_analysis": {...},
  "audio_url": "/download/coach_xxx.mp3",
  "phase": "intense"
}
```

## 🎨 Key Features Explained

### Breath Analysis
The backend analyzes:
- **Stillhet** - Amount of silence (0-100%)
- **Volum** - Breathing volume (0-100)
- **Tempo** - Breaths per minute
- **Intensitet** - Overall classification

### Intensity Levels
- **Rolig** 😌 - Calm breathing
- **Moderat** 💪 - Moderate intensity
- **Hard** 🔥 - High intensity
- **Kritisk** ⚠️ - Safety warning triggered

### Coaching Logic
- **Warmup:** Gentle encouragement
- **Intense:** Motivational pushing
- **Cooldown:** Calming guidance

## 🔧 Development

### Backend Development

```bash
cd backend

# Install dependencies
pip3 install -r requirements.txt

# Run locally
PORT=5001 DEBUG=true python3 main.py

# Test endpoints
curl http://localhost:5001/health
```

### iOS Development

```bash
cd ios-app

# Open in Xcode
open TreningsCoach.xcodeproj

# Or use command line
xcodebuild -scheme TreningsCoach
```

## 📦 Deployment

### Backend (Render)

1. Push to GitHub
```bash
cd backend
git add .
git commit -m "Update backend"
git push
```

2. Render auto-deploys (2-3 minutes)

### iOS (TestFlight/App Store)

1. Archive in Xcode
2. Upload to App Store Connect
3. Submit for TestFlight or review

## 🐛 Troubleshooting

### Backend Issues

**Port 5000 in use (macOS):**
```bash
PORT=5001 python3 main.py
```

**Backend sleeping (Render free tier):**
- First request takes 30-60 seconds
- Consider upgrading to paid tier

**CORS errors:**
- Already enabled in v1.1.0
- Check request headers

### iOS Issues

**Microphone permission denied:**
- Go to Settings → Privacy → Microphone
- Enable for Treningscoach

**Recording fails:**
- Check no other app is using microphone
- Try restarting app

**Backend timeout:**
- Wait for backend to wake up
- Check internet connection

## 📝 Version History

### Backend v1.1.0 (2026-01-27)
- Added CORS support
- Improved error handling
- File size validation
- Security enhancements
- Better logging

### iOS v1.0.0 (2026-01-27)
- Initial release
- Audio recording
- Backend integration
- UI animations
- Voice playback

## 🔮 Roadmap

### Short Term
- [ ] Integrate PersonaPlex for real TTS
- [ ] Add workout history
- [ ] Progress analytics
- [ ] Better error messages

### Long Term
- [ ] Apple Watch support
- [ ] HealthKit integration
- [ ] Social features
- [ ] Custom workout programs
- [ ] Multi-language support

## 📄 Documentation

- [Backend README](backend/README.md) - Complete API documentation
- [Backend Deployment Guide](backend/DEPLOYMENT.md) - iOS integration details
- [iOS README](ios-app/README.md) - iOS app documentation

## 💰 Costs

**Current:**
- Backend: $0/month (Render Free)
- iOS: Free (Development)

**Production:**
- Backend: $7/month (Render Starter)
- iOS: $99/year (Apple Developer)

## 🙏 Acknowledgments

- Flask for the backend framework
- SwiftUI for iOS development
- Render for hosting
- OpenAI/Claude for development assistance

## 📧 Contact

**Marius Gaarder**
- GitHub: [@98Mvg](https://github.com/98Mvg)

## 📄 License

This project is private and proprietary.

---

**Made with ❤️ for Better Workouts**
