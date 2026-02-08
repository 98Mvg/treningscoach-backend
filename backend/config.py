# config.py - Central configuration for easy customization

import os

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "Treningscoach"
APP_VERSION = "2.0.0"

# ============================================
# LANGUAGE SETTINGS
# ============================================
SUPPORTED_LANGUAGES = ["en", "no"]
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
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID_NO", os.getenv("ELEVENLABS_VOICE_ID", "")),
        "name": "Norwegian Coach"
    }
}

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
# NORWEGIAN WELCOME MESSAGES
# ============================================
WELCOME_MESSAGES_NO = {
    "standard": [
        "Fint at du er her. Vi starter rolig og bygger derfra.",
        "Klar naar du er. Ta et pust, finn roen, saa setter vi i gang.",
        "Bra timing. La oss varme opp ordentlig og legge grunnlaget.",
        "La oss komme i gang. Kontrollert tempo til aa begynne med.",
        "Velkommen tilbake. Kjenn paa kroppen saa bygger vi derfra.",
        "Okei, la oss begynne. Rolig og jevnt, ingen hastverk.",
        "Bra at du dukket opp. Start rolig, intensiteten kommer naturlig."
    ],
    "beginner_friendly": [
        "Fint at du er her. Vi starter sakte og holder det enkelt.",
        "Velkommen. Bare fokuser paa pusten og beveg deg i ditt tempo.",
        "La oss starte rolig. Ingen press, bare faa kroppen varm.",
        "Godt aa ha deg her. Ett steg om gangen, jeg guider deg.",
        "Du er her, det er det vanskeligste. Naa tar vi det rolig sammen."
    ],
    "breath_aware": [
        "Ta et oyeblikk. Dyp innpust, rolig utpust. Naa begynner vi.",
        "Start med aa finne pusten. Skuldrene ned, brystet aapent, rolig tempo.",
        "La oss koble paa pusten foerst. Alt annet foelger derfra.",
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
        "Rolig naa. Ikke stress. Oppvarming foerst.",
        "Ta det med ro. Fokuser paa pusten."
    ],

    "cooldown": [
        "Bra jobbet. La pusten roe seg. Du fortjener det.",
        "Slapp av. Senk tempoet. Skuldre og bryst avslappet.",
        "God oekt. Hold deg rolig og kontrollert.",
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
            "Stoe armer, stoe pust. Der ja.",
            "Fortsett! Ikke stopp!",
            "Bra! Hold tempoet!"
        ],
        "intense": [
            "Pusten oeker. Senk litt.",
            "Behold kontrollen. Hold tempoet.",
            "En runde til slik, saa er du ferdig. Fokus.",
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
        "Forsiktig, fortsett aa varme opp.",
        "Fint og rolig.",
        "Perfekt oppvarmingstempo."
    ],

    "cooldown": [
        "Senk tempoet, ta det rolig naa.",
        "Rolige pust, god nedkjoeling.",
        "Slipp av, bra jobbet.",
        "Nesten ferdig, senk farten.",
        "Perfekt, fortsett aa roe ned."
    ],

    "intense": {
        "calm": [
            "Du kan pushe hardere!",
            "Mer innsats, du klarer dette!",
            "Oek tempoet litt!",
            "Gi meg mer kraft!",
            "La oss oeke farten!"
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
            "Beveg deg RASKERE eller gaa hjem!",
            "BESTEMORA mi varmer opp raskere!",
            "Dette er PATETISK! La oss KJORE!",
            "Kaller du dette oppvarming? Jeg kaller det en LITEN BLUND!"
        ],
        "intense": {
            "calm": [
                "PATETISK! Bestemora mi pusher hardere!",
                "PROVER du i det hele tatt?! BEVEG DEG!",
                "Jeg har sett SNEGLER med mer intensitet!",
                "Er det ALT du har?! PINLIG!",
                "VAAKN OPP! Dette er ikke en spa-dag!"
            ],
            "moderate": [
                "Saa vidt godkjent. Gi meg MER!",
                "Du kan bedre enn DET!",
                "Jeg er IKKE imponert ennaa. HARDERE!",
                "Fortsett ellers dobler jeg det!",
                "Er det alt?! Push HARDERE!"
            ],
            "intense": [
                "ENDELIG! Var det saa vanskelig?!",
                "NAA snakker vi! Ikke VAAG aa senke farten!",
                "DER er det! Paa TIDE!",
                "JA! Det er det jeg vil ha! MER!",
                "Ikke verst. Men jeg vil ha BEDRE!"
            ]
        },
        "cooldown": [
            "Ferdig allerede?! Greit. Du FORTJENTE denne pausen.",
            "Ok, ok. Du overlevde. Saa vidt.",
            "Ikke det verste jeg har sett. Hvil deg.",
            "Godkjent prestasjon. Saa vidt godkjent.",
            "Greit, pust. Du trenger det til neste gang."
        ],
        "critical": [
            "Ok, alvor naa. Pust. Sikkerhet foerst.",
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
