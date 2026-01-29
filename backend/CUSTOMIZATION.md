# 🎨 Customization Guide

Easy guide to customize Treningscoach without touching complex code.

## 📁 Where to Make Changes

All customization happens in **config files** - no need to dig through code!

### Backend: `backend/config.py`
### iOS: `TreningsCoach/TreningsCoach/Config.swift`

---

## 🎨 Change Colors

### Backend (Web UI)

Edit `backend/config.py`:

```python
# Change the orb colors
COLOR_PRIMARY = "#007AFF"      # Idle (blue)
COLOR_LISTENING = "#34C759"    # Listening (green)
COLOR_SPEAKING = "#FF3B30"     # Speaking (red)

# Change text colors
COLOR_TEXT_PRIMARY = "#1d1d1f"     # Main text
COLOR_TEXT_SECONDARY = "#86868b"   # Subtitle text

# Change background
COLOR_BACKGROUND_START = "#ffffff"  # Top
COLOR_BACKGROUND_END = "#f5f5f7"    # Bottom
```

### iOS App

Edit `TreningsCoach/TreningsCoach/Config.swift`:

```swift
// Find Colors struct and modify:
static let idle = Color.blue        // Change orb colors
static let listening = Color.green
static let speaking = Color.red
```

---

## 💬 Change Coach Messages

Edit `backend/config.py`:

```python
COACH_MESSAGES = {
    "kritisk": ["STOPP! Pust rolig."],  # Emergency

    "warmup": [
        "Start rolig.",
        "Bra. Hold farten.",
        # Add more warmup messages
    ],

    "cooldown": [
        "Ta ned farten.",
        # Add more cooldown messages
    ],

    "intense": {
        "rolig": ["PUSH! Hardere!"],      # When breathing is calm
        "moderat": ["Fortsett!"],         # Moderate intensity
        "hard": ["Ja! Hold ut!"]          # High intensity
    }
}
```

**Tip:** Add multiple messages - one is randomly picked each time!

---

## ⏱️ Change Phase Timings

How long each workout phase lasts:

### Backend

Edit `backend/config.py`:

```python
WARMUP_DURATION = 120   # 2 minutes warmup
INTENSE_DURATION = 900  # 15 minutes hard training
# After this = cooldown
```

### iOS App

Edit `TreningsCoach/TreningsCoach/Config.swift`:

```swift
static let warmupDuration: TimeInterval = 120   // 2 minutes
static let intenseDuration: TimeInterval = 900  // 15 minutes
```

**Must match on both backend and iOS!**

---

## 📝 Change UI Text

### Backend

Edit `backend/config.py`:

```python
# Status texts (top of screen)
STATUS_TEXT_IDLE = "Ready"
STATUS_TEXT_LISTENING = "Listening"
STATUS_TEXT_SPEAKING = "Speaking"

# Info texts (below orb)
INFO_TEXT_IDLE = "Click to start"
INFO_TEXT_LISTENING = "Analyzing..."
INFO_TEXT_SPEAKING = "Coach responding..."
```

### iOS App

Edit `TreningsCoach/TreningsCoach/Config.swift`:

```swift
struct Text {
    static let phaseWarmup = "Warm-up"
    static let phaseIntense = "Hard Coach"
    static let phaseCooldown = "Cool-down"
}
```

---

## 🎭 Change Animation Speed

Edit `TreningsCoach/TreningsCoach/Config.swift`:

```swift
struct Animation {
    static let pulseDuration: Double = 1.5  // Slower = higher number
    static let waveDuration: Double = 0.8   // Faster wave
}
```

---

## 🔧 Change Breath Analysis Sensitivity

Edit `backend/config.py`:

```python
# Make analysis more/less sensitive
SILENCE_THRESHOLD = 0.01        # Lower = detects quieter sounds
VOLUME_AMPLIFICATION = 10       # Higher = more sensitive

# Adjust intensity thresholds
INTENSITY_THRESHOLDS = {
    "rolig": {"max_volume": 20, "min_silence": 50},
    "moderat": {"max_volume": 40, "max_tempo": 20},
    "hard": {"max_volume": 70, "max_tempo": 35},
}
```

---

## 🌐 Change Backend URL

### For Local Testing

Edit `TreningsCoach/TreningsCoach/Config.swift`:

```swift
// Change this line:
static let backendURL = localURL  // Use local instead of production
```

### For Production

```swift
static let backendURL = productionURL  // Back to production
```

---

## 📦 After Making Changes

### Backend Changes

```bash
cd backend
git add config.py
git commit -m "Update configuration"
git push
```

Render will auto-deploy in 2-3 minutes!

### iOS Changes

1. Open Xcode
2. Press `Cmd + B` to build
3. Press `Cmd + R` to run

---

## 🎯 Quick Customization Examples

### Example 1: Make Coach More Aggressive

```python
# backend/config.py
COACH_MESSAGES = {
    "intense": {
        "rolig": [
            "RASKERE! PUSH!",
            "HVA ER DETTE?! MER!",
            "INGEN PAUSE! KOM IGJEN!"
        ],
        "moderat": [
            "HARDERE!",
            "FORTSETT! IKKE STOPP!",
            "TI SEKUNDER TIL!"
        ],
        "hard": [
            "JA! DER! FORTSETT!",
            "PERFEKT! HOLD DET!",
            "FEM TIL! KOM IGJEN!"
        ]
    }
}
```

### Example 2: Change to Purple Theme

```python
# backend/config.py
COLOR_PRIMARY = "#8E44AD"       # Purple
COLOR_LISTENING = "#9B59B6"     # Light purple
COLOR_SPEAKING = "#6C3483"      # Dark purple
```

```swift
// Config.swift
static let idle = Color.purple
static let listening = Color(red: 0.61, green: 0.35, blue: 0.71)
static let speaking = Color(red: 0.42, green: 0.20, blue: 0.51)
```

### Example 3: Shorter Workouts

```python
# backend/config.py
WARMUP_DURATION = 60    # 1 minute warmup
INTENSE_DURATION = 300  // 5 minutes intense
```

```swift
// Config.swift
static let warmupDuration: TimeInterval = 60   // 1 minute
static let intenseDuration: TimeInterval = 300 // 5 minutes
```

---

## 🧠 Change AI Brain

Switch between different AI providers for coaching messages.

Edit `backend/config.py`:

```python
# Choose which AI brain to use
ACTIVE_BRAIN = "config"  # Options: "config", "claude", "openai"
```

### Brain Options

- **config** - Uses messages from config.py (no AI, no API key needed) - DEFAULT
- **claude** - Claude AI by Anthropic (requires ANTHROPIC_API_KEY)
- **openai** - GPT by OpenAI (requires OPENAI_API_KEY)

### Setup AI Brains

For Claude:
```bash
export ANTHROPIC_API_KEY="your-key-here"
pip install anthropic
```

For OpenAI:
```bash
export OPENAI_API_KEY="your-key-here"
pip install openai
```

**See [backend/brains/README.md](backend/brains/README.md) for complete brain setup guide!**

---

## 💡 Tips

- **Start small**: Change one thing at a time
- **Test locally** before deploying to production
- **Keep backups** of config files when experimenting
- **Colors**: Use hex codes from tools like [Coolors.co](https://coolors.co)
- **Messages**: Short and punchy works best (max 5-7 words)
- **AI Brains**: Start with "config" brain (free), then upgrade to Claude/OpenAI for dynamic responses

---

## 🆘 Need Help?

If something breaks:

1. Check you didn't introduce typos
2. Restart the app/server
3. Revert to original config values
4. Check console for error messages

---

**Happy customizing! 🎉**
