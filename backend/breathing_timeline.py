# breathing_timeline.py - Structured breathing guidance throughout entire workout
#
# The breathing architecture is ACTIVE AT ALL TIMES — from warmup prep through cooldown.
# Each phase has a breathing pattern, cue interval, and message bank.
#
# Phases (in order):
#   prep     → Before workout starts. Motivate, prep, safety words, countdown.
#   warmup   → Establish rhythm. 4-4 pattern (4s in, 4s out).
#   intense  → Power breathing. Short sharp breaths matched to effort.
#   recovery → Extended exhale. 4-6 pattern (4s in, 6s out).
#   cooldown → Deep recovery. 4-7 pattern. Return to rest.
#
# The coach uses templates as anchors. AI variation is optional.
# If AI output fails validation, the template plays.

import random
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


# ============================================
# BREATHING TIMELINE DEFINITION
# ============================================
BREATHING_TIMELINE = {
    "prep": {
        "pattern": "natural",
        "cue_interval": 20,  # Every 20 seconds during prep
        "messages_en": [
            "Alright, let's get ready.",
            "Drink some water if you need to.",
            "Stretch out anything that feels tight.",
            "We start in a moment. Take a deep breath.",
            "Remember: if you need to stop at any point, just stop. Listen to your body.",
            "Shake it out. Loosen up.",
        ],
        "messages_no": [
            "Greit, la oss gjore oss klare.",
            "Drikk litt vann om du trenger.",
            "Toey ut det som kjenns stramt.",
            "Vi starter snart. Ta et dypt pust.",
            "Husk: om du trenger aa stoppe, bare stopp. Lytt til kroppen.",
            "Rist det ut. Slapp av.",
        ],
        "countdown_en": [
            "Starting in {seconds} seconds.",
            "{seconds} seconds. Ready?",
            "Here we go in {seconds}.",
        ],
        "countdown_no": [
            "Starter om {seconds} sekunder.",
            "{seconds} sekunder. Klar?",
            "Her kjorer vi om {seconds}.",
        ],
        "safety_en": "If anything feels wrong during the workout, stop immediately. Your safety comes first.",
        "safety_no": "Hvis noe foeles feil under oekten, stopp med en gang. Din sikkerhet kommer foerst.",
    },

    "warmup": {
        "pattern": "4-4",  # 4s inhale, 4s exhale (calm, establishing rhythm)
        "cue_interval": 45,  # Cue every 45 seconds
        "messages_en": [
            "Find your rhythm. Steady breaths.",
            "Easy breathing. Let it flow.",
            "Shoulders down, chest open.",
            "Nice and controlled. Build slowly.",
            "Breathe through the nose if you can.",
        ],
        "messages_no": [
            "Finn rytmen. Jevne pust.",
            "Rolig pust. La det flyte.",
            "Skuldrene ned, brystet aapent.",
            "Fint og kontrollert. Bygg sakte.",
            "Pust gjennom nesen om du kan.",
        ],
    },

    "intense": {
        "pattern": "power",  # Short sharp breaths matched to effort
        "cue_interval": 90,  # Less frequent — don't interrupt peak effort
        "messages_en": [
            "Breathe through it.",
            "Strong exhale. Power.",
            "Don't hold your breath.",
            "Exhale on the effort.",
            "Keep breathing. Stay with it.",
        ],
        "messages_no": [
            "Pust gjennom det.",
            "Sterk utpust. Kraft.",
            "Ikke hold pusten.",
            "Pust ut paa innsatsen.",
            "Fortsett aa puste. Hold deg i det.",
        ],
    },

    "recovery": {
        "pattern": "4-6",  # 4s inhale, 6s exhale (extended exhale for recovery)
        "cue_interval": 30,  # More frequent — guide the recovery
        "messages_en": [
            "Slow it down. In four... out six.",
            "Long exhale. Let the tension go.",
            "Recovery breath. Nice and slow.",
            "Breathe deep. You earned this.",
            "Slow nose breathing. Good.",
        ],
        "messages_no": [
            "Senk tempoet. Inn fire... ut seks.",
            "Lang utpust. Slipp spenningen.",
            "Hvilepust. Fint og rolig.",
            "Pust dypt. Du fortjente dette.",
            "Rolig nesepust. Bra.",
        ],
    },

    "cooldown": {
        "pattern": "4-7",  # Deep recovery breathing
        "cue_interval": 60,
        "messages_en": [
            "Deep breath in... slow breath out.",
            "You earned this. Breathe deep.",
            "Let your breathing return to normal.",
            "Relax everything. Just breathe.",
            "Great session. Wind it down.",
        ],
        "messages_no": [
            "Dypt inn... sakte ut.",
            "Du fortjente dette. Pust dypt.",
            "La pusten komme tilbake til normalt.",
            "Slapp av alt. Bare pust.",
            "Bra oekt. Ro det ned.",
        ],
    },
}


# ============================================
# INTERRUPTION HANDLING
# ============================================
# When user expresses distress, the coach responds with safety + guidance
BREATHING_INTERRUPTS = {
    "cant_breathe": {
        "triggers_en": ["can't breathe", "hard to breathe", "can not breathe", "struggling to breathe"],
        "triggers_no": ["kan ikke puste", "vanskelig aa puste", "sliter med pusten", "faar ikke pust"],
        "response_en": "That's okay. Slow way down. Breathe through your nose.",
        "response_no": "Det er greit. Senk farten. Pust gjennom nesen.",
        "action": "force_recovery",
    },
    "slow_down": {
        "triggers_en": ["slow down", "too fast", "too much", "too hard"],
        "triggers_no": ["saktere", "for fort", "for mye", "for hardt"],
        "response_en": "Slowing down. Match my count. In... two... three...",
        "response_no": "Vi senker tempoet. Foelg tellingen. Inn... to... tre...",
        "action": "extend_pattern",
    },
    "dizzy": {
        "triggers_en": ["dizzy", "lightheaded", "seeing stars", "about to faint"],
        "triggers_no": ["svimmel", "yr", "ser stjerner"],
        "response_en": "Stop moving. Sit down if you need to. Slow nose breathing.",
        "response_no": "Stopp. Sett deg ned om du trenger. Rolig nesepust.",
        "action": "force_safety_pause",
    },
}


class BreathingTimeline:
    """
    Manages breathing cues throughout a workout session.
    Active at ALL times — from prep through cooldown.
    """

    def __init__(self):
        self.last_cue_time: int = 0
        self.cues_given: int = 0
        self.current_phase: str = "prep"
        self.prep_safety_given: bool = False
        self.prep_start_time: int = 0

    def get_breathing_cue(
        self,
        phase: str,
        elapsed_seconds: int,
        language: str = "en",
        time_until_start: Optional[int] = None,
    ) -> Optional[str]:
        """
        Get the next breathing cue if it's time for one.

        Args:
            phase: Current workout phase (prep/warmup/intense/recovery/cooldown)
            elapsed_seconds: Seconds since workout start (or prep start)
            language: "en" or "no"
            time_until_start: Seconds until workout starts (prep phase only)

        Returns:
            Coaching message string, or None if not time yet
        """
        self.current_phase = phase
        timeline = BREATHING_TIMELINE.get(phase)
        if not timeline:
            return None

        # Check interval
        time_since_last = elapsed_seconds - self.last_cue_time
        if time_since_last < timeline["cue_interval"]:
            return None

        self.last_cue_time = elapsed_seconds
        self.cues_given += 1

        # Prep phase: special handling for countdown + safety
        if phase == "prep":
            return self._get_prep_cue(elapsed_seconds, language, time_until_start)

        # Normal phase: pick from message bank
        msg_key = f"messages_{language}" if f"messages_{language}" in timeline else "messages_en"
        messages = timeline.get(msg_key, timeline.get("messages_en", []))
        if messages:
            return random.choice(messages)

        return None

    def _get_prep_cue(
        self,
        elapsed_seconds: int,
        language: str,
        time_until_start: Optional[int] = None,
    ) -> str:
        """Generate prep phase cues: motivation, safety, countdown."""
        timeline = BREATHING_TIMELINE["prep"]

        # First cue: always safety
        if not self.prep_safety_given:
            self.prep_safety_given = True
            safety_key = f"safety_{language}" if f"safety_{language}" in timeline else "safety_en"
            return timeline.get(safety_key, timeline["safety_en"])

        # If we have countdown info
        if time_until_start is not None and time_until_start <= 30:
            countdown_key = f"countdown_{language}" if f"countdown_{language}" in timeline else "countdown_en"
            countdowns = timeline.get(countdown_key, timeline["countdown_en"])
            return random.choice(countdowns).format(seconds=time_until_start)

        # General prep motivation
        msg_key = f"messages_{language}" if f"messages_{language}" in timeline else "messages_en"
        messages = timeline.get(msg_key, timeline["messages_en"])
        return random.choice(messages)

    def check_interruption(self, user_message: str, language: str = "en") -> Optional[Dict]:
        """
        Check if user message indicates breathing distress.

        Args:
            user_message: What the user said (from wake word / talk endpoint)
            language: "en" or "no"

        Returns:
            Dict with response + action, or None if no interrupt detected
        """
        message_lower = user_message.lower()

        for interrupt_type, data in BREATHING_INTERRUPTS.items():
            # Check triggers for the user's language
            triggers_key = f"triggers_{language}" if f"triggers_{language}" in data else "triggers_en"
            triggers = data.get(triggers_key, data.get("triggers_en", []))

            for trigger in triggers:
                if trigger in message_lower:
                    response_key = f"response_{language}" if f"response_{language}" in data else "response_en"
                    return {
                        "type": interrupt_type,
                        "response": data.get(response_key, data["response_en"]),
                        "action": data["action"],
                    }

        return None

    def get_phase_info(self, phase: str) -> Dict:
        """Get breathing pattern info for the current phase."""
        timeline = BREATHING_TIMELINE.get(phase, BREATHING_TIMELINE["intense"])
        return {
            "pattern": timeline["pattern"],
            "cue_interval": timeline["cue_interval"],
        }

    def reset(self):
        """Reset for a new session."""
        self.last_cue_time = 0
        self.cues_given = 0
        self.current_phase = "prep"
        self.prep_safety_given = False
        self.prep_start_time = 0
