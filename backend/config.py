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
# WELCOME MESSAGES (Gym Companion - Martin Sundby Style)
# ============================================
# Spoken once at workout start (before first breath)
# Purpose: Acknowledge start, set expectations, establish rhythm
# Tone: Calm, authoritative, friendly
WELCOME_MESSAGES = {
    "standard": [
        "Welcome. Let's start slow. Find your rhythm.",
        "Good. Breathe in, and out. Settle your shoulders.",
        "Steady now. Don't rush. Warmup first, intensity later.",
        "Easy does it. Focus on breathing, not speed.",
        "Alright, lungs and legs. Let's get them talking."
    ],

    "beginner_friendly": [
        "Hi there. Let's start easy and find your rhythm.",
        "Ready to move? Let's warm up gently.",
        "Time to begin. Focus on your breathing and ease into it.",
        "Hello. Start slow and steady. We'll build from here.",
        "You made it. Let's start easy and feel your body wake up."
    ],

    "breath_aware": [
        "Find your breath. Relax your shoulders. Warmup begins.",
        "Focus on calm breathing. Let's ease into the session.",
        "Listen to your body, breathe steadily, and start gently.",
        "Check your rhythm. Warmup is on, take it easy."
    ]
}

# ============================================
# COACH MESSAGES (English for live conversations)
# ============================================
COACH_MESSAGES = {
    "critical": ["STOP! Breathe slowly. You're safe."],

    "warmup": [
        "Welcome. Let's start slow. Find your rhythm.",
        "Good. Breathe in, and out. Settle your shoulders.",
        "Steady now. Don't rush. Warmup first, intensity later.",
        "Easy does it. Focus on breathing, not speed."
    ],

    "cooldown": [
        "Well done. Let the breath settle. You earned it.",
        "Relax. Slow it down. Shoulder and chest relaxed.",
        "Good session. Keep calm and controlled.",
        "Steady breathing. That's how we finish strong.",
        "Nice work. You controlled your effort well."
    ],

    "intense": {
        "calm": [
            "Maintain control. Pace yourself. Don't overdo it.",
            "Good. Keep that rhythm. Slightly faster, not frantic.",
            "PUSH! Harder!",
            "You got more!"
        ],
        "moderate": [
            "Good. Keep that rhythm. Slightly faster, not frantic.",
            "Steady arms, steady breath. That's it.",
            "Keep going! Don't stop!",
            "Good! Hold the pace!"
        ],
        "intense": [
            "Breathing quickened. Slow down a touch.",
            "Maintain control. Pace yourself. Don't overdo it.",
            "One more interval like this and you're done. Focus.",
            "YES! Hold on! Ten more!"
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
    "calm": {"max_volume": 20, "min_silence": 50},
    "moderate": {"max_volume": 40, "max_tempo": 20},
    "intense": {"max_volume": 70, "max_tempo": 35},
    # Above these = critical
}

# ============================================
# BRAIN ROUTER CONFIGURATION
# ============================================
# Choose which AI brain to use: "claude", "openai", "config"
# - "claude": Uses Claude AI (requires ANTHROPIC_API_KEY)
# - "openai": Uses OpenAI GPT (requires OPENAI_API_KEY)
# - "config": Uses simple config-based messages (no AI, no API key needed)
ACTIVE_BRAIN = "config"  # Default to config (no API needed)

# STEP 4: Hybrid Brain Strategy
# Use Claude for pattern detection, config for speed
USE_HYBRID_BRAIN = True  # Enable intelligent fallback
HYBRID_CLAUDE_FOR_PATTERNS = True  # Use Claude to detect trends over time
HYBRID_CONFIG_FOR_SPEED = True  # Use config for fast, immediate cues

# ============================================
# CONTINUOUS COACHING SETTINGS
# ============================================
CONTINUOUS_COACHING_ENABLED = True
DEFAULT_COACHING_INTERVAL = 8  # seconds between coaching ticks
MIN_COACHING_INTERVAL = 6      # fastest interval
MAX_COACHING_INTERVAL = 15     # slowest interval
MIN_TIME_BETWEEN_COACHING = 20  # minimum seconds between spoken messages (prevent over-coaching)

# STEP 2: Intensity-driven message bank with personality
# Message characteristics:
#   critical → FIRM, SAFETY-FIRST: 1-3 words, urgent tone
#   calm → REASSURING, CALM: 3-5 words, gentle encouragement
#   moderate → GUIDING, ENCOURAGING: 2-4 words, supportive
#   intense → ASSERTIVE, FOCUSED: 2-3 words, direct motivation
CONTINUOUS_COACH_MESSAGES = {
    # CRITICAL - Firm, safety-first (1-3 words, URGENT)
    "critical": [
        "STOP!",
        "Breathe slow!",
        "Easy now!",
        "Slow down!",
        "Too hard!"
    ],

    # WARMUP - Reassuring, calm (3-5 words)
    "warmup": [
        "Easy pace, nice start.",
        "Steady, good warmup.",
        "Gentle, keep warming up.",
        "Nice and easy.",
        "Perfect warmup pace."
    ],

    # COOLDOWN - Reassuring, calm (3-5 words)
    "cooldown": [
        "Bring it down, easy now.",
        "Slow breaths, good cooldown.",
        "Ease off, nice work.",
        "Almost done, slow it.",
        "Perfect, keep slowing down."
    ],

    # INTENSE PHASE - Personality by intensity level
    "intense": {
        # CALM during intense - Reassuring but encouraging (3-5 words)
        "calm": [
            "You can push harder!",
            "More effort, you got this!",
            "Speed up a bit!",
            "Give me more power!",
            "Let's pick up the pace!"
        ],

        # MODERATE during intense - Guiding, encouraging (2-4 words)
        "moderate": [
            "Keep going, good pace!",
            "Stay with it!",
            "Nice rhythm, maintain!",
            "You got this!",
            "Good work, keep steady!"
        ],

        # INTENSE during intense - Assertive, focused (2-3 words)
        "intense": [
            "Perfect! Hold it!",
            "Yes! Strong!",
            "Keep this!",
            "Excellent work!",
            "Ten more seconds!"
        ]
    }
}

# ============================================
# DEPLOYMENT
# ============================================
GITHUB_REPO = "https://github.com/98Mvg/treningscoach-backend"
PRODUCTION_URL = "https://treningscoach-backend.onrender.com"
