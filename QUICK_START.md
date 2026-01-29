# ⚡ Quick Start Guide

Get Treningscoach running in 5 minutes!

## 🎯 What You Get

- **Minimal ChatGPT-like voice UI** (no clutter, just focus)
- **Auto-phase detection** (warm-up → intense → cool-down)
- **Real-time breath analysis** with motivational coaching
- **Easy customization** via config files

---

## 🚀 Step 1: Start Backend (30 seconds)

```bash
cd backend
pip3 install -r requirements.txt
PORT=5001 python3 main.py
```

✅ Backend running at http://localhost:5001

---

## 📱 Step 2: Run iOS App (2 minutes)

```bash
cd TreningsCoach
open TreningsCoach.xcodeproj
```

In Xcode:
1. Select a device/simulator
2. Press `Cmd + R`

✅ App launches with minimal voice UI

---

## 🎨 Step 3: Customize (Optional, 2 minutes)

### Change Colors

Edit `backend/config.py`:
```python
COLOR_PRIMARY = "#FF0000"  # Change to red!
```

Edit `TreningsCoach/TreningsCoach/Config.swift`:
```swift
static let idle = Color.red
```

### Change Messages

Edit `backend/config.py`:
```python
COACH_MESSAGES = {
    "intense": {
        "rolig": ["GO FASTER!", "PUSH IT!"]
    }
}
```

**See [CUSTOMIZATION.md](CUSTOMIZATION.md) for complete guide!**

---

## 🌐 Production Deployment

### Backend

```bash
cd backend
git add .
git commit -m "Update"
git push
```

Render auto-deploys in 2-3 minutes!

### iOS

Build in Xcode and deploy via TestFlight/App Store

---

## 📖 File Structure

**Only touch these for customization:**
```
backend/config.py                    # Backend settings
TreningsCoach/TreningsCoach/Config.swift  # iOS settings
```

**Everything else is implementation (don't need to touch):**
```
backend/main.py                      # Flask app
TreningsCoach/TreningsCoach/Views/   # SwiftUI views
TreningsCoach/TreningsCoach/Services/  # API & audio
```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check if port 5000 is in use
PORT=5001 python3 main.py
```

### iOS build fails
1. Clean: `Cmd + Shift + K`
2. Build: `Cmd + B`
3. Check Config.swift is added to project

### Can't connect to backend
In `Config.swift`, change:
```swift
static let backendURL = localURL  // For local testing
```

---

## 🎉 You're Ready!

- Test the voice orb (tap to record breath)
- See auto-phase detection in action
- Customize colors/messages to your style
- Deploy to production when ready

**Happy coaching! 💪**
