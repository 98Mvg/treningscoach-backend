# config.py - Central configuration for easy customization

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "Treningscoach"
APP_VERSION = "1.1.0"

# ============================================
# UI CUSTOMIZATION
# ============================================
# Colors (CSS format)
COLOR_PRIMARY = "#007AFF"  # Blue
COLOR_LISTENING = "#34C759"  # Green
COLOR_SPEAKING = "#FF3B30"  # Red
COLOR_TEXT_PRIMARY = "#1d1d1f"
COLOR_TEXT_SECONDARY = "#86868b"
COLOR_BACKGROUND_START = "#ffffff"
COLOR_BACKGROUND_END = "#f5f5f7"

# Text
STATUS_TEXT_IDLE = "Ready"
STATUS_TEXT_LISTENING = "Listening"
STATUS_TEXT_SPEAKING = "Speaking"
INFO_TEXT_IDLE = "Click to start"
INFO_TEXT_LISTENING = "Analyzing your breath..."
INFO_TEXT_SPEAKING = "Coach is responding..."

# ============================================
# PHASE TIMINGS (seconds)
# ============================================
WARMUP_DURATION = 120  # First 2 minutes
INTENSE_DURATION = 900  # 2-15 minutes
# After INTENSE_DURATION = cooldown

# ============================================
# COACH MESSAGES
# ============================================
COACH_MESSAGES = {
    "kritisk": ["STOPP! Pust rolig. Du er trygg."],

    "warmup": [
        "Start rolig. Vi varmer opp.",
        "Bra. Hold denne farten.",
        "Rolig tempo. Fortsett."
    ],

    "cooldown": [
        "Ta ned farten.",
        "Pust rolig.",
        "Bra. Rolig ned."
    ],

    "intense": {
        "rolig": [
            "PUSH! Hardere!",
            "Du klarer mer!",
            "Raskere! Nå!"
        ],
        "moderat": [
            "Fortsett! Du har mer!",
            "Ikke stopp! Fortsett!",
            "Bra! Hold farten!"
        ],
        "hard": [
            "Ja! Hold ut! Ti til!",
            "Bra! Fortsett!",
            "Der ja! Fem sekunder!"
        ]
    }
}

# ============================================
# API SETTINGS
# ============================================
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

# ============================================
# ANALYSIS THRESHOLDS
# ============================================
# Adjust these to tune the breath analysis sensitivity
SILENCE_THRESHOLD = 0.01  # 1% of max amplitude
VOLUME_AMPLIFICATION = 10  # How much to amplify volume readings

# Intensity classification thresholds
INTENSITY_THRESHOLDS = {
    "rolig": {"max_volume": 20, "min_silence": 50},
    "moderat": {"max_volume": 40, "max_tempo": 20},
    "hard": {"max_volume": 70, "max_tempo": 35},
    # Above these = kritisk
}

# ============================================
# DEPLOYMENT
# ============================================
GITHUB_REPO = "https://github.com/98Mvg/treningscoach-backend"
PRODUCTION_URL = "https://treningscoach-backend.onrender.com"
