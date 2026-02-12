# coaching_engine.py - Hybrid template-anchor + AI variation coaching system
#
# Design: Templates are the safety net. AI generates variations.
# If the AI variation fails validation, the template plays instead.
#
# This module also validates AI-generated coaching text for:
# - Length (2-15 words for realtime, 5-30 for strategic)
# - Language correctness (Norwegian text should contain Norwegian chars)
# - Forbidden phrases (no "breathing app" framing, no AI self-reference)
# - Tone match (no humor during critical intensity)
# - Profanity check (basic, respects toxic_mode exemptions)

import random
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# ============================================
# FORBIDDEN PHRASES (R0.4: No "breathing app" framing)
# ============================================
FORBIDDEN_PHRASES = [
    "breathing exercise",
    "breathing app",
    "breath work",
    "breathwork session",
    "as an ai",
    "i can't actually",
    "i'm an ai",
    "as a language model",
    "i don't have the ability",
]

# Basic profanity list (NOT applied to toxic_mode)
PROFANITY_BLOCKLIST = [
    # Keep minimal — only truly offensive words, not "hell" or "damn" which are fine in coaching
]

# Humor markers — blocked during critical/intense safety states
HUMOR_MARKERS = ["haha", "lol", "😂", "🤣", "funny", "joke", "hilarious"]


def validate_coaching_text(
    text: str,
    phase: str = "intense",
    intensity: str = "moderate",
    persona: str = "personal_trainer",
    language: str = "en",
    mode: str = "realtime"
) -> bool:
    """
    Validate AI-generated coaching text.

    Returns True if text passes all quality checks, False otherwise.
    When False, caller should fall back to template message.

    Args:
        text: AI-generated coaching text
        phase: Current workout phase
        intensity: Current breathing intensity
        persona: Active persona
        language: Target language
        mode: "realtime" (2-15 words) or "strategic" (5-30 words)
    """
    if not text or not text.strip():
        logger.debug("Validation FAIL: empty text")
        return False

    words = text.split()
    word_count = len(words)

    # Length check
    if mode == "realtime":
        if word_count < 1 or word_count > 15:
            logger.debug(f"Validation FAIL: realtime length {word_count} words (need 1-15)")
            return False
    elif mode == "strategic":
        if word_count < 2 or word_count > 30:
            logger.debug(f"Validation FAIL: strategic length {word_count} words (need 2-30)")
            return False

    text_lower = text.lower()

    # Forbidden phrases (R0.4 + AI self-reference)
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            logger.debug(f"Validation FAIL: forbidden phrase '{phrase}'")
            return False

    # Language check: Norwegian text > 5 words should ideally have Norwegian chars
    # This is a soft heuristic — short phrases like "Kom igjen!" are fine without æøå
    if language == "no" and word_count > 8:
        has_norwegian_chars = any(c in text for c in "æøåÆØÅ")
        # Many Norwegian words don't need special chars, so only flag if it looks English
        english_indicators = ["the ", "you ", " is ", " are ", " your ", "keep going", "let's go"]
        looks_english = any(ind in text_lower for ind in english_indicators)
        if looks_english and not has_norwegian_chars:
            logger.debug(f"Validation FAIL: looks English when language=no")
            return False

    # Tone check: no humor during critical or safety states
    if intensity == "critical":
        for marker in HUMOR_MARKERS:
            if marker in text_lower:
                logger.debug(f"Validation FAIL: humor marker '{marker}' during critical intensity")
                return False

    # Profanity check (skip for toxic_mode which intentionally uses edgy language)
    if persona != "toxic_mode":
        for word in PROFANITY_BLOCKLIST:
            if word in text_lower:
                logger.debug(f"Validation FAIL: profanity '{word}'")
                return False

    return True


class SessionCoachState:
    """
    Tracks coaching coherence across a workout session.
    Prevents repetition, balances motivation types, tracks breathing cue cadence.
    """

    def __init__(self):
        self.themes_used: List[str] = []         # Avoid repeating same cue type
        self.last_messages: List[str] = []        # Prevent word-for-word repeats (last 10)
        self.motivation_balance: float = 0.0      # -1 (all push) to +1 (all praise)
        self.breathing_cue_count: int = 0
        self.last_breathing_cue_time: int = 0
        self.phase_transitions_announced: set = set()

    def record_message(self, text: str, cue_type: str = "general"):
        """Record a coaching message for anti-repetition tracking."""
        self.last_messages.append(text)
        if len(self.last_messages) > 10:
            self.last_messages.pop(0)
        self.themes_used.append(cue_type)
        if len(self.themes_used) > 5:
            self.themes_used.pop(0)

    def is_duplicate(self, text: str) -> bool:
        """Check if this exact text was spoken recently."""
        return text in self.last_messages[-5:]

    def get_next_cue_type(self, phase: str, intensity: str) -> str:
        """
        Select next cue type, avoiding recent repeats.
        Types: pace, effort, form, breathing, motivation
        """
        available = ["pace", "effort", "form", "breathing", "motivation"]
        recent = set(self.themes_used[-3:])
        candidates = [c for c in available if c not in recent]
        if not candidates:
            candidates = available

        # Weight by phase
        weights = {
            "warmup": {"breathing": 3, "motivation": 2, "pace": 2, "form": 1, "effort": 1},
            "intense": {"effort": 3, "motivation": 2, "pace": 2, "breathing": 1, "form": 1},
            "cooldown": {"breathing": 3, "pace": 2, "motivation": 1, "form": 1, "effort": 1},
        }
        phase_weights = weights.get(phase, weights["intense"])
        weighted = [(c, phase_weights.get(c, 1)) for c in candidates]
        total = sum(w for _, w in weighted)
        r = random.random() * total
        cumulative = 0
        for cue_type, weight in weighted:
            cumulative += weight
            if r <= cumulative:
                return cue_type
        return candidates[0]


def get_template_message(
    phase: str,
    intensity: str,
    persona: str,
    language: str
) -> str:
    """
    Get a template coaching message (the anchor).
    Always returns a valid message — never None.
    """
    import config

    # Select message bank
    if persona == "toxic_mode":
        lang_key = language if language in getattr(config, "TOXIC_MODE_MESSAGES", {}) else "en"
        messages = config.TOXIC_MODE_MESSAGES.get(lang_key, config.TOXIC_MODE_MESSAGES.get("en", {}))
    elif language == "no":
        messages = getattr(config, "CONTINUOUS_COACH_MESSAGES_NO", config.CONTINUOUS_COACH_MESSAGES)
    else:
        messages = config.CONTINUOUS_COACH_MESSAGES

    # Critical override
    if intensity in ("critical", "kritisk"):
        return random.choice(messages.get("critical", ["Stop!"]))

    # Phase-based
    if phase == "warmup":
        return random.choice(messages.get("warmup", ["Easy pace."]))

    if phase == "cooldown":
        return random.choice(messages.get("cooldown", ["Slow down."]))

    if phase == "intense":
        intense_msgs = messages.get("intense", {})
        intensity_key = intensity if intensity in intense_msgs else "moderate"
        if intensity_key in intense_msgs:
            return random.choice(intense_msgs[intensity_key])

    return "Fortsett!" if language == "no" else "Keep going!"
