# voice_intelligence.py
# STEP 6: Make Voice Feel Human
# Silence, variation, and natural pacing

from typing import Optional, Tuple
import random

class VoiceIntelligence:
    """
    STEP 6: Makes coach voice feel human through:
    - Strategic silence (when things are optimal, say nothing)
    - Variation in phrasing (avoid robotic repetition)
    - Natural pacing (short pauses between sentences)

    Key principle: Silence = confidence
    """

    def __init__(self):
        """Initialize voice intelligence."""
        self.last_messages = []  # Track recent messages to avoid repetition
        self.silence_count = 0  # Track consecutive silent ticks

    def should_stay_silent(
        self,
        breath_data: dict,
        phase: str,
        last_coaching: str,
        elapsed_seconds: int
    ) -> Tuple[bool, str]:
        """
        STEP 6: Decide if coach should stay silent (optimal breathing).

        "If breathing is optimal, say nothing."
        Silence = confidence.

        Args:
            breath_data: Current breath analysis
            phase: Current phase
            last_coaching: Last message spoken
            elapsed_seconds: Workout duration

        Returns:
            (should_be_silent: bool, reason: str)
        """
        intensitet = breath_data.get("intensity", "moderate")
        tempo = breath_data.get("tempo", 0)

        # NEVER silent for critical breathing
        if intensitet == "critical":
            return (False, "safety_override")

        # Don't be silent at the very start (greet user)
        if elapsed_seconds < 10:
            return (False, "greeting")

        # STEP 6: Silence when breathing is optimal for the phase
        if phase == "warmup" and intensitet in ["calm", "moderate"]:
            # Optimal warmup breathing - silence is golden
            if self.silence_count < 2:  # Allow some silence
                self.silence_count += 1
                return (True, "optimal_warmup")

        elif phase == "intense" and intensitet == "intense":
            # Optimal intense breathing - let them focus
            if self.silence_count < 1:  # Brief silence during optimal performance
                self.silence_count += 1
                return (True, "optimal_intense")

        elif phase == "cooldown" and intensitet == "calm":
            # Optimal cooldown breathing - peaceful silence
            if self.silence_count < 3:  # Longer silence during recovery
                self.silence_count += 1
                return (True, "optimal_cooldown")

        # Reset silence count if not silent
        self.silence_count = 0
        return (False, "needs_coaching")

    def add_human_variation(self, message: str) -> str:
        """
        STEP 6: Add subtle variation to avoid robotic repetition.

        Examples:
        - "Perfect!" → "Perfect!" | "Nice!" | "Yes!"
        - "Keep going!" → "Keep going!" | "Keep it up!" | "Stay with it!"

        Args:
            message: Original message

        Returns:
            Message with subtle variation (90% same, 10% varied)
        """
        # Most of the time, keep original message
        if random.random() < 0.9:
            return message

        # 10% of the time, add subtle variation
        variations = {
            "Perfect!": ["Perfect!", "Nice!", "Yes!", "Excellent!"],
            "Keep going!": ["Keep going!", "Keep it up!", "Stay with it!", "You got this!"],
            "Good pace!": ["Good pace!", "Nice rhythm!", "Solid work!", "Well done!"],
            "Hold it!": ["Hold it!", "Hold this!", "Keep this!", "Maintain!"],
        }

        # Check if message matches any variation pattern
        for base, options in variations.items():
            if base in message:
                return random.choice(options)

        return message

    def add_natural_pacing(self, message: str) -> dict:
        """
        STEP 6: Add natural pacing metadata for TTS.

        Returns metadata about how the message should be spoken:
        - pause_before: Short pause before speaking (ms)
        - pause_after: Short pause after speaking (ms)
        - emphasis: Words to emphasize

        Args:
            message: Message to speak

        Returns:
            Dict with pacing metadata
        """
        pacing = {
            "pause_before": 0,
            "pause_after": 0,
            "emphasis": []
        }

        # Short pause before critical safety messages
        if "STOP" in message or "critical" in message.lower():
            pacing["pause_before"] = 100  # 100ms pause for attention
            pacing["emphasis"] = ["STOP", "slow", "breathe"]

        # Brief pause before encouragement
        if "Perfect" in message or "Yes" in message:
            pacing["pause_before"] = 50  # 50ms pause for impact
            pacing["emphasis"] = ["Perfect", "Yes", "Strong"]

        # Slight pause after commands
        if "!" in message:
            pacing["pause_after"] = 200  # 200ms pause after commands

        return pacing

    def detect_overtalking(self, coaching_history: list) -> bool:
        """
        STEP 6: Detect if coach is talking too much.

        If coach spoke for last 3+ consecutive ticks, force silence.

        Args:
            coaching_history: Recent coaching messages

        Returns:
            True if coach is overtalking
        """
        if len(coaching_history) < 3:
            return False

        # Check if last 3 messages were all spoken (not None)
        last_three = coaching_history[-3:]
        all_spoke = all(msg.get("text") for msg in last_three if msg)

        return all_spoke

    def should_reduce_frequency(
        self,
        breath_data: dict,
        coaching_history: list
    ) -> bool:
        """
        STEP 6: Decide if coaching frequency should be reduced.

        Used to adjust wait_seconds dynamically based on overtalking detection.

        Args:
            breath_data: Current breath analysis
            coaching_history: Recent coaching messages

        Returns:
            True if should increase wait time
        """
        # If overtalking, increase wait time
        if self.detect_overtalking(coaching_history):
            return True

        # If breathing is stable (moderate), less coaching needed
        if breath_data.get("intensity") == "moderate":
            # Check if intensity has been stable
            if len(coaching_history) >= 3:
                recent_intensities = [
                    h.get("breath_analysis", {}).get("intensity")
                    for h in coaching_history[-3:]
                    if h and "breath_analysis" in h
                ]
                if all(i == "moderate" for i in recent_intensities if i):
                    return True

        return False

    def get_silence_message(self) -> str:
        """
        STEP 6: Return a "meta-message" explaining silence (for debugging).

        This is NOT spoken to the user - it's for backend logs.

        Returns:
            Explanation of why coach is silent
        """
        return "[Silent - breathing is optimal]"
