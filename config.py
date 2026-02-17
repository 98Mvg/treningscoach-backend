# config.py - Central configuration for Coachi AI Coach
# Voice/locale config lives in locale_config.py (single source of truth)

import json
import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_csv_list(name: str, default: list) -> list:
    raw = os.getenv(name)
    if not raw:
        return default
    values = [item.strip() for item in raw.split(",")]
    values = [item for item in values if item]
    return values or default


def _env_json_dict(name: str, default: dict) -> dict:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        return default
    except json.JSONDecodeError:
        return default

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "Coachi"
APP_VERSION = "3.0.0"

# ============================================
# LANGUAGE SETTINGS
# ============================================
SUPPORTED_LANGUAGES = ["en", "no", "da"]
DEFAULT_LANGUAGE = "en"

# ============================================
# VOICE CONFIGURATION (per language)
# ============================================
VOICE_CONFIG = {
    "en": {
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID_EN", os.getenv("ELEVENLABS_VOICE_ID", "")),
        "name": "English Coach"
    },
    "no": {
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID_NO", "nhvaqgRyAq6BmFs3WcdX"),
        "name": "Norwegian Coach"
    },
    "da": {
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID_DA", ""),
        "name": "Danish Coach"
    }
}

# ============================================
# TTS SETTINGS
# ============================================
# Local Qwen3-TTS is disabled (too slow on CPU). Use ElevenLabs instead.
ENABLE_QWEN_TTS = False

# ============================================
# BREATH ANALYSIS SETTINGS
# ============================================
# Downsample to reduce CPU and improve stability
BREATH_ANALYSIS_SAMPLE_RATE = 16000
# Minimum upload size (bytes) to treat as valid audio
BREATH_MIN_AUDIO_BYTES = 8000
# Smoothing for breath metrics (EMA over recent history)
BREATH_SMOOTHING_ALPHA = 0.5
BREATH_SMOOTHING_WINDOW = 4
# Maximum silence before forcing a coach cue (seconds)
# 30s ensures coach doesn't disappear — users expect active coaching
MAX_SILENCE_SECONDS = 30
EARLY_WORKOUT_GRACE_SECONDS = 30  # Force coaching output during early workout
# Minimum signal quality required to force a cue after max silence
# Set to 0.0 so the override ALWAYS fires — phone mics are noisy during workouts
# and we never want the coach to go permanently silent
MIN_SIGNAL_QUALITY_TO_FORCE = 0.0

# Persona-specific voices
# Maps to iOS CoachPersonality enum values
# voice_ids: Dict of language -> voice_id (use language default if not set)
# stability: 0.0-1.0 (higher = more consistent delivery)
# style: 0.0-1.0 (higher = more expressive/dramatic)
PERSONA_VOICE_CONFIG = {
    "personal_trainer": {
        "voice_ids": {
            "en": os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN", "1DHhvmhXw9p08Sc79vuJ"),
            "no": os.getenv("ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO", "nhvaqgRyAq6BmFs3WcdX"),
        },
        "name": "Personal Trainer",
        "stability": 0.6,
        "style": 0.0
    },
    "toxic_mode": {
        "voice_ids": {
            "en": os.getenv("ELEVENLABS_VOICE_ID_TOXIC_EN", "YxsfIjmqZRHBp5erMzLg"),
            "no": os.getenv("ELEVENLABS_VOICE_ID_TOXIC_NO", "nhvaqgRyAq6BmFs3WcdX"),
        },
        "name": "Toxic Mode",
        "stability": 0.25,
        "style": 0.9
    }
}

# ============================================
# TRAINING LEVEL CONFIGURATION
# ============================================
TRAINING_LEVEL_CONFIG = {
    "beginner": {
        "coaching_frequency_multiplier": 1.5,   # Talk more often
        "intensity_threshold_offset": -10,       # Lower threshold to trigger "intense"
        "tone": "supportive",
        "max_push_intensity": "moderate",        # Never push beginners to extreme
        "prompt_modifier": "Speak to a beginner. Be encouraging and patient. Explain what to do. Never assume fitness knowledge. Use simple language."
    },
    "intermediate": {
        "coaching_frequency_multiplier": 1.0,
        "intensity_threshold_offset": 0,
        "tone": "balanced",
        "max_push_intensity": "intense",
        "prompt_modifier": "Speak to an experienced exerciser. Be direct and motivating. Challenge appropriately."
    },
    "advanced": {
        "coaching_frequency_multiplier": 0.7,    # Talk less (they know what they're doing)
        "intensity_threshold_offset": 10,
        "tone": "direct",
        "max_push_intensity": "critical",
        "prompt_modifier": "Speak to an elite athlete. Be minimal. Only speak when it matters. Push hard."
    }
}

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
        "Good to see you. Let's start with some easy movement and build from there.",
        "Ready when you are. Take a breath, settle in, and we'll ease into it.",
        "Nice timing. Let's warm up properly and set the tone for a good session.",
        "Let's get moving. Controlled pace to start, then we'll find your rhythm.",
        "Welcome back. Focus on how your body feels and we'll build from there.",
        "Alright, let's begin. Smooth and steady, no rush.",
        "Good call showing up. Start easy, the intensity will come naturally."
    ],

    "beginner_friendly": [
        "Great that you're here. We'll start slow and keep it simple.",
        "Welcome. Just focus on breathing and moving at your own pace.",
        "Let's begin easy. No pressure, just getting your body warmed up.",
        "Nice to have you. Take it one step at a time, I'll guide you through.",
        "You're here, that's the hardest part. Now let's ease into it together."
    ],

    "breath_aware": [
        "Take a moment. Deep breath in, slow breath out. Now let's begin.",
        "Start by finding your breath. Shoulders down, chest open, easy pace.",
        "Let's connect with your breathing first. Everything else follows from there.",
        "Settle your breath, relax your body. We'll build the intensity gradually."
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
# Choose which AI brain to use: "claude", "openai", "grok", "gemini", "config"
# - "claude": Uses Claude AI (requires ANTHROPIC_API_KEY)
# - "openai": Uses OpenAI GPT (requires OPENAI_API_KEY)
# - "grok":   Uses xAI Grok (requires XAI_API_KEY, OpenAI-compatible API)
# - "gemini": Uses Google Gemini (requires GEMINI_API_KEY)
# - "config": Uses simple config-based messages (no AI, no API key needed)
ACTIVE_BRAIN = os.getenv("ACTIVE_BRAIN", "grok").strip().lower() or "grok"

# Priority routing (try brains in order with timeout + fallback)
USE_PRIORITY_ROUTING = _env_bool("USE_PRIORITY_ROUTING", True)
# Default: Grok first, then immediate config fallback (no Gemini/OpenAI/Claude calls).
BRAIN_PRIORITY = _env_csv_list("BRAIN_PRIORITY", ["grok", "config"])
BRAIN_TIMEOUT = _env_float("BRAIN_TIMEOUT", 1.2)  # global default timeout (seconds) for brains without overrides
# Per-brain timeout overrides. Grok typically needs ~4-5s in production.
BRAIN_TIMEOUTS = _env_json_dict("BRAIN_TIMEOUTS_JSON", {"grok": 6.0})
# Optional per-mode overrides (realtime_coach/chat). Falls back to BRAIN_TIMEOUTS/BRAIN_TIMEOUT.
BRAIN_MODE_TIMEOUTS = _env_json_dict("BRAIN_MODE_TIMEOUTS_JSON", {})
USAGE_LIMIT = _env_float("USAGE_LIMIT", 0.9)  # skip brain if usage >= this (optional BRAIN_USAGE map)
BRAIN_COOLDOWN_SECONDS = _env_float("BRAIN_COOLDOWN_SECONDS", 60)
BRAIN_TIMEOUT_COOLDOWN_SECONDS = _env_float("BRAIN_TIMEOUT_COOLDOWN_SECONDS", 30)
BRAIN_INIT_RETRY_SECONDS = _env_float("BRAIN_INIT_RETRY_SECONDS", 5)  # Short cooldown for init failures (API key missing, import error)
BRAIN_QUOTA_COOLDOWN_SECONDS = _env_float("BRAIN_QUOTA_COOLDOWN_SECONDS", 300)  # Longer cooldown for provider quota failures
BRAIN_SLOW_THRESHOLD = _env_float("BRAIN_SLOW_THRESHOLD", 3.0)  # seconds avg latency before skipping (must be > BRAIN_TIMEOUT)
# Per-brain slow-threshold overrides. Grok should not be marked slow at 4-5s.
BRAIN_SLOW_THRESHOLDS = _env_json_dict("BRAIN_SLOW_THRESHOLDS_JSON", {"grok": 6.5})
BRAIN_LATENCY_DECAY_FACTOR = _env_float("BRAIN_LATENCY_DECAY_FACTOR", 0.9)  # Decay old avg_latency toward recent readings
BRAIN_RECENT_CUE_WINDOW = _env_int("BRAIN_RECENT_CUE_WINDOW", 4)  # Anti-repetition memory per session
# Latency-aware response strategy:
# - If expected brain latency is high, return fast config fallback cue immediately.
# - Force one richer AI follow-up cue on the next tick.
LATENCY_FAST_FALLBACK_ENABLED = _env_bool("LATENCY_FAST_FALLBACK_ENABLED", True)
LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS = _env_float("LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", 2.8)
LATENCY_FAST_FALLBACK_MIN_CALLS = _env_int("LATENCY_FAST_FALLBACK_MIN_CALLS", 2)
LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS = _env_float("LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS", 20.0)
# Optional live usage map (0.0-1.0). Example: {"grok": 0.92}
BRAIN_USAGE = _env_json_dict("BRAIN_USAGE_JSON", {})

# STEP 4: Hybrid Brain Strategy
# Use Claude for pattern detection, config for speed
USE_HYBRID_BRAIN = _env_bool("USE_HYBRID_BRAIN", False)  # Disabled by default: pattern insights not wanted during workouts
HYBRID_CLAUDE_FOR_PATTERNS = _env_bool("HYBRID_CLAUDE_FOR_PATTERNS", False)
HYBRID_CONFIG_FOR_SPEED = _env_bool("HYBRID_CONFIG_FOR_SPEED", True)
USE_STRATEGIC_BRAIN = _env_bool("USE_STRATEGIC_BRAIN", False)

# ============================================
# CONTINUOUS COACHING SETTINGS
# ============================================
CONTINUOUS_COACHING_ENABLED = True
DEFAULT_COACHING_INTERVAL = 8  # seconds between coaching ticks
MIN_COACHING_INTERVAL = 6      # fastest interval
MAX_COACHING_INTERVAL = 15     # slowest interval
MIN_TIME_BETWEEN_COACHING = 20  # minimum seconds between spoken messages (prevent over-coaching)

# ============================================
# WORKOUT MODES (BACKEND-ONLY FOR NOW)
# ============================================
SUPPORTED_WORKOUT_MODES = ["standard", "interval"]
DEFAULT_WORKOUT_MODE = "standard"

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
# NORWEGIAN WELCOME MESSAGES
# ============================================
WELCOME_MESSAGES_NO = {
    "standard": [
        "Fint at du er her. Vi starter rolig og bygger derfra.",
        "Klar når du er. Ta et pust, finn roen, så setter vi i gang.",
        "Bra timing. La oss varme opp ordentlig og legge grunnlaget.",
        "La oss komme i gang. Kontrollert tempo til å begynne med.",
        "Velkommen tilbake. Kjenn på kroppen så bygger vi derfra.",
        "Ok, la oss begynne. Rolig og jevnt, uten stress.",
        "Bra at du dukket opp. Start rolig, intensiteten kommer naturlig."
    ],
    "beginner_friendly": [
        "Fint at du er her. Vi starter sakte og holder det enkelt.",
        "Velkommen. Bare fokuser på pusten og beveg deg i ditt tempo.",
        "La oss starte rolig. Ingen press, bare få kroppen varm.",
        "Godt å ha deg her. Ett steg om gangen, jeg guider deg.",
        "Du er her, det er det vanskeligste. Nå tar vi det rolig sammen."
    ],
    "breath_aware": [
        "Ta et øyeblikk. Dyp innpust, rolig utpust. Nå begynner vi.",
        "Start med å finne pusten. Skuldrene ned, brystet åpent, rolig tempo.",
        "La oss koble på pusten først. Alt annet følger derfra.",
        "Finn roen i pusten, slapp av kroppen. Vi bygger intensiteten gradvis."
    ]
}

# ============================================
# NORWEGIAN COACH MESSAGES
# ============================================
COACH_MESSAGES_NO = {
    "critical": ["STOPP! Pust sakte. Du er trygg."],

    "warmup": [
        "Velkommen. La oss starte rolig. Finn rytmen din.",
        "Bra. Pust inn, og ut. Slapp av skuldrene.",
        "Rolig nå. Ikke stress. Oppvarming først.",
        "Ta det med ro. Fokuser på pusten."
    ],

    "cooldown": [
        "Bra jobbet. La pusten roe seg. Du fortjener det.",
        "Slapp av. Senk tempoet. Skuldre og bryst avslappet.",
        "God økt. Hold deg rolig og kontrollert.",
        "Jevn pust. Slik avslutter vi sterkt.",
        "Bra jobbet. Du kontrollerte innsatsen godt."
    ],

    "intense": {
        "calm": [
            "Behold kontrollen. Hold tempoet. Ikke overdrive.",
            "Bra. Hold rytmen. Litt raskere, ikke hektisk.",
            "PUSH! Hardere!",
            "Du har mer!"
        ],
        "moderate": [
            "Bra. Hold rytmen. Litt raskere, ikke hektisk.",
            "Sterke armer, stø pust. Der ja.",
            "Fortsett! Ikke stopp!",
            "Bra! Hold tempoet!"
        ],
        "intense": [
            "Pusten øker. Senk litt.",
            "Behold kontrollen. Hold tempoet.",
            "En runde til slik, så er du ferdig. Fokus.",
            "JA! Hold ut! Ti til!"
        ]
    }
}

# ============================================
# NORWEGIAN CONTINUOUS COACH MESSAGES
# ============================================
CONTINUOUS_COACH_MESSAGES_NO = {
    "critical": [
        "STOPP!",
        "Pust rolig!",
        "Ta det rolig!",
        "Senk farten!",
        "For hardt!"
    ],

    "warmup": [
        "Rolig tempo, fin start.",
        "Jevnt, god oppvarming.",
        "Rolig, fortsett oppvarmingen.",
        "Fint og rolig.",
        "Perfekt oppvarmingstempo."
    ],

    "cooldown": [
        "Senk tempoet, ta det rolig nå.",
        "Rolige pust, god nedkjøling.",
        "Slipp av, bra jobbet.",
        "Nesten ferdig, senk farten.",
        "Perfekt, fortsett å roe ned."
    ],

    "intense": {
        "calm": [
            "Du kan presse hardere!",
            "Mer innsats, du klarer dette!",
            "Øk tempoet litt!",
            "Mer trykk nå!",
            "La oss øke farten!"
        ],
        "moderate": [
            "Fortsett, godt tempo!",
            "Hold deg i det!",
            "Fin rytme, behold!",
            "Du klarer dette!",
            "Bra jobbet, hold jevnt!"
        ],
        "intense": [
            "Perfekt! Hold det!",
            "Ja! Sterkt!",
            "Behold dette!",
            "Utmerket jobbet!",
            "Ti sekunder til!"
        ]
    }
}

# ============================================
# TOXIC MODE MESSAGES (EN + NO)
# ============================================
TOXIC_MODE_MESSAGES = {
    "en": {
        "warmup": [
            "Warming up?! We're WASTING TIME!",
            "Move FASTER or go home!",
            "My GRANDMOTHER warms up faster!",
            "This is PATHETIC! Let's GO!",
            "You call this a warmup? I call it a NAP!"
        ],
        "intense": {
            "calm": [
                "PATHETIC! My grandma pushes harder!",
                "Are you even TRYING?! MOVE!",
                "I've seen SNAILS with more intensity!",
                "Is that ALL you got?! EMBARRASSING!",
                "WAKE UP! This isn't a spa day!"
            ],
            "moderate": [
                "Barely acceptable. Give me MORE!",
                "You can do better than THAT!",
                "I'm NOT impressed yet. HARDER!",
                "Keep going or I'll double it!",
                "That's it?! Push HARDER!"
            ],
            "intense": [
                "FINALLY! Was that so hard?!",
                "NOW we're talking! Don't you DARE slow down!",
                "THERE it is! About TIME!",
                "YES! That's what I want! MORE!",
                "Not bad. But I want BETTER!"
            ]
        },
        "cooldown": [
            "Done already?! Fine. You EARNED this break.",
            "Okay, okay. You survived. Barely.",
            "Not the worst I've seen. Rest up.",
            "Acceptable performance. BARELY acceptable.",
            "Alright, breathe. You'll need it for next time."
        ],
        "critical": [
            "Alright, real talk. Breathe. Safety first.",
            "Okay, stop. I'm tough, not stupid. Rest.",
            "Hey. Real break. Breathe slow. I mean it."
        ]
    },
    "no": {
        "warmup": [
            "Oppvarming?! Vi KASTER BORT TID!",
            "Beveg deg RASKERE eller gå hjem!",
            "BESTEMORA mi varmer opp raskere!",
            "Dette er PATETISK! La oss KJØRE!",
            "Kaller du dette oppvarming? Jeg kaller det en LITEN BLUND!"
        ],
        "intense": {
            "calm": [
                "PATETISK! Bestemora mi pusher hardere!",
                "PRØVER du i det hele tatt?! BEVEG DEG!",
                "Jeg har sett SNEGLER med mer intensitet!",
                "Er det ALT du har?! PINLIG!",
                "VÅKN OPP! Dette er ikke en spa-dag!"
            ],
            "moderate": [
                "Så vidt godkjent. Gi meg MER!",
                "Du kan bedre enn DET!",
                "Jeg er IKKE imponert ennå. HARDERE!",
                "Fortsett ellers dobler jeg det!",
                "Er det alt?! Push HARDERE!"
            ],
            "intense": [
                "ENDELIG! Var det så vanskelig?!",
                "NÅ snakker vi! Ikke VÅG å senke farten!",
                "DER er det! På TIDE!",
                "JA! Det er det jeg vil ha! MER!",
                "Ikke verst. Men jeg vil ha BEDRE!"
            ]
        },
        "cooldown": [
            "Ferdig allerede?! Greit. Du FORTJENTE denne pausen.",
            "Ok, ok. Du overlevde. Så vidt.",
            "Ikke det verste jeg har sett. Hvil deg.",
            "Godkjent prestasjon. Så vidt godkjent.",
            "Greit, pust. Du trenger det til neste gang."
        ],
        "critical": [
            "Ok, alvor nå. Pust. Sikkerhet først.",
            "Ok, stopp. Jeg er toff, ikke dum. Hvil.",
            "Hei. Ordentlig pause. Pust rolig. Jeg mener det."
        ]
    }
}

# ============================================
# DEPLOYMENT
# ============================================
GITHUB_REPO = "https://github.com/98Mvg/treningscoach-backend"
PRODUCTION_URL = "https://treningscoach-backend.onrender.com"
