# voice_intelligence.py
# STEP 6: Make Voice Feel Human
# Silence, variation, natural pacing, and emotional voice modulation

from typing import Optional, Tuple, Dict
import random


# =============================================================================
# VOICE PACING PROFILES
# =============================================================================
# Different personas at different emotional intensities get different voice settings.
# These affect TTS parameters like speed, stability, and pauses.

VOICE_PACING_PROFILES = {
    # Personal Trainer: Calm and measured, slightly more direct at peak
    "personal_trainer": {
        "supportive": {"speed": 1.0, "stability": 0.6, "pause_multiplier": 1.0},
        "pressing":   {"speed": 1.0, "stability": 0.55, "pause_multiplier": 0.95},
        "intense":    {"speed": 1.02, "stability": 0.5, "pause_multiplier": 0.9},
        "peak":       {"speed": 1.05, "stability": 0.45, "pause_multiplier": 0.8},
    },
    # Toxic Mode: Gets increasingly unhinged (faster, more variable)
    "toxic_mode": {
        "supportive": {"speed": 1.0, "stability": 0.5, "pause_multiplier": 1.0},
        "pressing":   {"speed": 1.05, "stability": 0.4, "pause_multiplier": 0.85},
        "intense":    {"speed": 1.1, "stability": 0.35, "pause_multiplier": 0.7},
        "peak":       {"speed": 1.15, "stability": 0.3, "pause_multiplier": 0.5},
    },
}

# Default pacing for unknown personas
DEFAULT_PACING = {"speed": 1.0, "stability": 0.5, "pause_multiplier": 1.0}


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
        STEP 6: Decide if coach should stay silent.

        Key principle: Coach is the user's MOTIVATOR. Silence should be rare,
        not the default. Users expect an active, engaging coach — not a silent one.

        Only stay silent when:
        - Breathing is HIGHLY regular AND optimal for the current phase
        - Even then, only for 1 tick max before coaching again

        Never stay silent for noisy audio — coach should still motivate
        even when breath analysis is unreliable.

        Args:
            breath_data: Current breath analysis
            phase: Current phase
            last_coaching: Last message spoken
            elapsed_seconds: Workout duration

        Returns:
            (should_be_silent: bool, reason: str)
        """
        intensitet = breath_data.get("intensity", "moderate")
        signal_quality = breath_data.get("signal_quality")
        breath_regularity = breath_data.get("breath_regularity")

        # NEVER silent for critical breathing
        if intensitet == "critical":
            self.silence_count = 0
            return (False, "safety_override")

        # Always coach at the start (first 30 seconds = warmup tips, motivation)
        if elapsed_seconds < 30:
            self.silence_count = 0
            return (False, "early_workout")

        # Noisy audio: still coach! Coach should motivate regardless of signal.
        # Breath data may be unreliable but coach messages (pace, encouragement) still help.
        # Only note it for logging, don't suppress coaching.
        if signal_quality is not None and signal_quality < 0.1:
            # Very poor signal — skip ONE tick, then coach anyway
            if self.silence_count < 1:
                self.silence_count += 1
                return (True, "very_noisy_audio")

        # Stay silent ONLY if breathing is highly regular AND matches phase target
        # Even then, max 1 consecutive silent tick
        if breath_regularity is not None and breath_regularity > 0.9:
            if ((phase == "intense" and intensitet == "intense") or
                (phase == "cooldown" and intensitet == "calm")):
                if self.silence_count < 1:
                    self.silence_count += 1
                    return (True, "peak_performance")

        # Reset silence count — coach speaks
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

    def get_voice_pacing(
        self,
        persona: str,
        emotional_mode: str,
        message: str = ""
    ) -> Dict:
        """
        Get voice pacing settings based on persona and emotional mode.

        This enables emotional progression in the VOICE itself:
        - Calm Coach gets slower under stress
        - Drill Sergeant gets faster and sharper
        - Toxic Mode becomes increasingly unhinged

        Args:
            persona: The persona identifier
            emotional_mode: "supportive", "pressing", "intense", or "peak"
            message: The message being spoken (for additional adjustments)

        Returns:
            Dict with voice settings:
            - speed: TTS speed multiplier (0.7-1.15)
            - stability: ElevenLabs stability parameter (0.3-0.8)
            - pause_multiplier: Multiplier for pause durations
            - pause_before: ms pause before speaking
            - pause_after: ms pause after speaking
        """
        # Get base pacing for persona + mode
        persona_profiles = VOICE_PACING_PROFILES.get(persona, {})
        base_pacing = persona_profiles.get(emotional_mode, DEFAULT_PACING).copy()

        # Get message-based pacing adjustments
        message_pacing = self.add_natural_pacing(message)

        # Apply pause multiplier to message pacing
        pause_multiplier = base_pacing.get("pause_multiplier", 1.0)
        adjusted_pause_before = int(message_pacing["pause_before"] * pause_multiplier)
        adjusted_pause_after = int(message_pacing["pause_after"] * pause_multiplier)

        return {
            "speed": base_pacing.get("speed", 1.0),
            "stability": base_pacing.get("stability", 0.5),
            "pause_multiplier": pause_multiplier,
            "pause_before": adjusted_pause_before,
            "pause_after": adjusted_pause_after,
            "emphasis": message_pacing.get("emphasis", [])
        }

    def get_elevenlabs_voice_settings(
        self,
        persona: str,
        emotional_mode: str
    ) -> Dict:
        """
        Get ElevenLabs-specific voice settings for emotional progression.

        These can be passed directly to the ElevenLabs API.

        Args:
            persona: The persona identifier
            emotional_mode: "supportive", "pressing", "intense", or "peak"

        Returns:
            Dict with ElevenLabs VoiceSettings parameters
        """
        pacing = self.get_voice_pacing(persona, emotional_mode)

        return {
            "stability": pacing["stability"],
            "similarity_boost": 0.75,  # Keep voice consistent
            "style": 0.0,  # Neutral style
            "use_speaker_boost": True
        }
