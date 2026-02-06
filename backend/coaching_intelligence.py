# coaching_intelligence.py - Intelligence layer for continuous coaching decisions
# Now with emotional progression safety guardrails

from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# SAFETY OVERRIDE RULES
# =============================================================================
# These are NON-NEGOTIABLE. No matter the persona or emotional state,
# safety always comes first.

def check_safety_override(
    breath_analysis: Dict,
    emotional_intensity: float = 0.0
) -> Tuple[bool, str]:
    """
    Check if safety override should be triggered.

    Safety overrides emotional progression. When triggered:
    - All personas drop to "supportive" mode
    - Messages become supportive, not challenging
    - Coaching frequency increases

    Args:
        breath_analysis: Current breath analysis
        emotional_intensity: Current emotional intensity (0.0-1.0)

    Returns:
        Tuple of (should_override: bool, reason: str)
    """
    intensity = breath_analysis.get("intensity", "moderate")
    signal_quality = breath_analysis.get("signal_quality")
    breath_regularity = breath_analysis.get("breath_regularity")
    respiratory_rate = breath_analysis.get("respiratory_rate")

    # Rule 1: Critical breathing - ALWAYS override
    if intensity == "critical":
        logger.warning("SAFETY OVERRIDE: critical breathing detected")
        return (True, "critical_breathing")

    # Rule 2: Hyperventilation pattern (respiratory rate > 30)
    if respiratory_rate is not None and respiratory_rate > 30:
        logger.warning(f"SAFETY OVERRIDE: hyperventilation (rate={respiratory_rate})")
        return (True, "hyperventilation")

    # Rule 3: Signal quality collapse (can't reliably assess)
    if signal_quality is not None and signal_quality < 0.15:
        logger.warning(f"SAFETY OVERRIDE: signal quality collapse ({signal_quality})")
        return (True, "signal_collapse")

    # Rule 4: Highly irregular breathing with high emotional intensity
    # (User may be panicking)
    if breath_regularity is not None and breath_regularity < 0.25:
        if emotional_intensity > 0.7:
            logger.warning(f"SAFETY OVERRIDE: panic pattern (regularity={breath_regularity}, intensity={emotional_intensity})")
            return (True, "panic_pattern")

    # Rule 5: Emotional intensity at absolute max (0.95+) for too long
    # Even if breathing seems OK, back off the pressure
    if emotional_intensity >= 0.95:
        logger.warning(f"SAFETY OVERRIDE: emotional ceiling reached ({emotional_intensity})")
        return (True, "emotional_ceiling")

    return (False, "none")


def apply_safety_to_coaching(
    message: str,
    persona: str,
    safety_reason: str,
    language: str = "en"
) -> str:
    """
    Transform a coaching message when safety override is active.

    Args:
        message: Original coaching message
        persona: The persona that generated it
        safety_reason: Why safety was triggered
        language: "en" or "no"

    Returns:
        Safety-appropriate message
    """
    # Safety messages by reason
    safety_messages = {
        "en": {
            "critical_breathing": "Let's slow down. Take a deep breath with me. In... and out.",
            "hyperventilation": "I need you to slow your breathing. In for 4... out for 6.",
            "signal_collapse": "Take a moment. Let's reset together.",
            "panic_pattern": "You're doing great. Let's just breathe together for a moment.",
            "emotional_ceiling": "Amazing effort. Let's take a recovery breath."
        },
        "no": {
            "critical_breathing": "La oss roe ned. Ta et dypt pust med meg. Inn... og ut.",
            "hyperventilation": "Jeg trenger at du senker pusten. Inn i 4... ut i 6.",
            "signal_collapse": "Ta et øyeblikk. La oss nullstille sammen.",
            "panic_pattern": "Du gjør det bra. La oss bare puste sammen et øyeblikk.",
            "emotional_ceiling": "Utrolig innsats. La oss ta et pust."
        }
    }

    # For toxic mode, explicitly drop the act
    if persona == "toxic_mode":
        prefix_en = "Alright, dropping the act for a second. "
        prefix_no = "Ok, jeg legger bort akten et øyeblikk. "
        prefix = prefix_no if language == "no" else prefix_en
        base_message = safety_messages.get(language, safety_messages["en"]).get(safety_reason, "")
        return prefix + base_message

    return safety_messages.get(language, safety_messages["en"]).get(
        safety_reason,
        "Take a breath. You're doing well." if language == "en" else "Ta et pust. Du gjør det bra."
    )


def emotional_decay_on_silence(
    emotional_intensity: float,
    seconds_silent: float
) -> float:
    """
    Apply emotional decay when coach stays silent.

    Silence = calm. The longer the coach is silent, the more
    emotional intensity should decay.

    Args:
        emotional_intensity: Current intensity (0.0-1.0)
        seconds_silent: How long coach has been silent

    Returns:
        New emotional intensity after decay
    """
    if seconds_silent <= 0:
        return emotional_intensity

    # Decay rate: 5% per 8-second tick of silence
    ticks_silent = seconds_silent / 8.0
    decay_factor = 0.95 ** ticks_silent

    new_intensity = emotional_intensity * decay_factor

    # Floor at 0.1 (never fully reset)
    return max(0.1, new_intensity)


def should_coach_speak(
    current_analysis: Dict,
    last_analysis: Optional[Dict],
    coaching_history: List[Dict],
    phase: str,
    training_level: str = "intermediate"
) -> Tuple[bool, str]:
    """
    Determines whether the coach should speak based on breath analysis and context.

    Args:
        current_analysis: Current breath analysis dict with intensity, tempo, volume, etc.
        last_analysis: Previous breath analysis (None if first tick)
        coaching_history: List of recent coaching outputs with timestamps
        phase: Current workout phase ("warmup", "intense", "cooldown")

    Returns:
        Tuple of (should_speak: bool, reason: str)
    """

    intensity = current_analysis.get("intensity", "moderate")
    tempo = current_analysis.get("tempo", 0)
    volume = current_analysis.get("volume", 0)

    # NEW: Advanced breath metrics (from BreathAnalyzer, optional)
    breath_regularity = current_analysis.get("breath_regularity")
    inhale_exhale_ratio = current_analysis.get("inhale_exhale_ratio")
    signal_quality = current_analysis.get("signal_quality")
    respiratory_rate = current_analysis.get("respiratory_rate")

    # Rule 0: Skip coaching if audio quality is too poor to be reliable
    if signal_quality is not None and signal_quality < 0.2:
        logger.info("Coach silent: signal_quality too low (%.2f)", signal_quality)
        return (False, "low_signal_quality")

    # Rule 1: Always speak for critical breathing (safety override)
    if intensity == "critical":
        logger.info("Coach speaking: critical_breathing detected")
        return (True, "critical_breathing")

    # Rule 1b: Irregular breathing warrants coaching guidance
    if breath_regularity is not None and breath_regularity < 0.4:
        logger.info("Coach speaking: irregular_breathing (regularity=%.2f)", breath_regularity)
        return (True, "irregular_breathing")

    # Rule 1c: Inhale nearly as long as exhale — suggest longer exhales
    if inhale_exhale_ratio is not None and inhale_exhale_ratio > 0.9:
        logger.info("Coach speaking: short_exhale (I:E ratio=%.2f)", inhale_exhale_ratio)
        return (True, "short_exhale")

    # Rule 2: First tick of workout - always welcome
    if last_analysis is None:
        logger.info("Coach speaking: first_tick")
        return (True, "first_tick")

    # Rule 3: Check for significant changes
    last_intensity = last_analysis.get("intensity", "moderate")
    last_tempo = last_analysis.get("tempo", 0)

    intensity_changed = intensity != last_intensity
    tempo_delta = abs(tempo - last_tempo)
    tempo_changed = tempo_delta > 5  # More than 5 breaths/min change

    # Rule 4: Phase-aware periodic speaking (adjusted by training level)
    # Warmup: coach talks more (every 30s) — tips, encouragement, preparation
    # Intense: coach stays quiet, breath-focused (every 90s) — minimal distraction
    # Cooldown: moderate (every 45s) — recovery guidance
    periodic_intervals = {
        "warmup": 30,     # More talkative during warmup
        "intense": 90,    # Minimal during workout — focus on breath
        "cooldown": 45    # Moderate during cooldown
    }
    periodic_interval = periodic_intervals.get(phase, 60)

    # Training level adjusts coaching frequency
    # Beginners need more guidance (1.5x), advanced need less (0.7x)
    try:
        import config
        level_config = config.TRAINING_LEVEL_CONFIG.get(training_level, {})
        frequency_multiplier = level_config.get("coaching_frequency_multiplier", 1.0)
        # Lower multiplier = less frequent = longer interval
        periodic_interval = int(periodic_interval / frequency_multiplier)
    except (ImportError, AttributeError):
        pass  # Use default if config not available

    if not intensity_changed and not tempo_changed:
        if coaching_history and len(coaching_history) > 0:
            last_coaching = coaching_history[-1]
            last_coaching_time = last_coaching.get("timestamp")
            if last_coaching_time:
                if isinstance(last_coaching_time, str):
                    try:
                        last_coaching_time = datetime.fromisoformat(last_coaching_time)
                    except:
                        last_coaching_time = None
                if isinstance(last_coaching_time, datetime):
                    elapsed_since_last = (datetime.now() - last_coaching_time).total_seconds()
                    if elapsed_since_last >= periodic_interval:
                        reason = f"periodic_{phase}" if phase == "warmup" else "periodic_encouragement"
                        logger.info(f"Coach speaking: {reason} ({elapsed_since_last:.0f}s since last, interval={periodic_interval}s)")
                        return (True, reason)
            logger.debug(f"Coach silent: no_change (intensity={intensity}, tempo={tempo}, phase={phase})")
            return (False, "no_change")
        else:
            # No coaching history at all — speak
            logger.info("Coach speaking: no_history (first coaching after welcome)")
            return (True, "no_history")

    # Rule 5: During intense phase, push if breathing is too calm
    if phase == "intense" and intensity == "calm":
        logger.info("Coach speaking: push_harder (calm during intense)")
        return (True, "push_harder")

    # Rule 6: During cooldown, remind to slow down if still breathing intense
    if phase == "cooldown" and intensity == "intense":
        logger.info("Coach speaking: slow_down (intense during cooldown)")
        return (True, "slow_down")

    # Rule 7: Avoid over-coaching (don't speak more than once per 20 seconds)
    if coaching_history and len(coaching_history) > 0:
        last_coaching = coaching_history[-1]
        last_coaching_time = last_coaching.get("timestamp")

        if last_coaching_time:
            if isinstance(last_coaching_time, str):
                try:
                    last_coaching_time = datetime.fromisoformat(last_coaching_time)
                except:
                    pass

            if isinstance(last_coaching_time, datetime):
                elapsed = (datetime.now() - last_coaching_time).total_seconds()
                if elapsed < 20:
                    logger.debug(f"Coach silent: too_frequent (last spoke {elapsed}s ago)")
                    return (False, "too_frequent")

    # Rule 8: Speak for any significant intensity or tempo change
    if intensity_changed or tempo_changed:
        logger.info(f"Coach speaking: change detected (intensity: {last_intensity}→{intensity}, tempo Δ{tempo_delta})")
        return (True, "intensity_change")

    # Default: stay silent
    return (False, "no_trigger")


def calculate_next_interval(
    phase: str,
    intensity: str,
    coaching_frequency: int = 0
) -> int:
    """
    Calculates the optimal wait time before next coaching tick.

    INTENSITY-DRIVEN FREQUENCY (STEP 2):
    - critical: 5s (URGENT - safety-first, check frequently)
    - intense: 6s (FOCUSED - assertive, frequent feedback)
    - moderate: 8s (GUIDING - balanced, encouraging)
    - calm: 12s (REASSURING - calm, give space)

    Args:
        phase: Current workout phase
        intensity: Current breathing intensity
        coaching_frequency: How many times coached in last minute (for throttling)

    Returns:
        Wait time in seconds (5-15)
    """

    # Intensity-driven intervals (CRITICAL: shorter, CALM: longer)
    intensity_intervals = {
        "critical": 5,    # URGENT - check every 5 seconds for safety
        "intense": 6,     # FOCUSED - frequent feedback
        "moderate": 8,    # GUIDING - balanced pacing
        "calm": 12        # REASSURING - give space, don't over-coach
    }

    base_interval = intensity_intervals.get(intensity, 8)

    # Phase adjustments (subtle modifiers)
    phase_modifiers = {
        "warmup": -1,    # Faster during warmup — coach talks more, gives tips
        "intense": 0,    # No change during intense (let intensity drive, breath focus)
        "cooldown": 3    # Slower during cooldown
    }

    modifier = phase_modifiers.get(phase, 0)

    # Critical breathing overrides phase modifiers (always fast)
    if intensity == "critical":
        return 5  # Safety-first, ignore phase

    # Apply phase modifier
    adjusted_interval = base_interval + modifier

    # Throttle if coaching too frequently
    if coaching_frequency > 3:  # More than 3 times in last minute
        adjusted_interval = min(15, adjusted_interval + 3)

    # Clamp to safe range
    return max(5, min(15, adjusted_interval))


def get_coaching_context_summary(
    breath_history: List[Dict],
    coaching_history: List[Dict],
    max_history: int = 5
) -> str:
    """
    Creates a brief context summary for AI brains to use in coaching.

    Args:
        breath_history: Recent breath analyses
        coaching_history: Recent coaching outputs
        max_history: Maximum number of items to include

    Returns:
        Human-readable context string
    """

    context_parts = []

    # Recent breath trend
    if len(breath_history) >= 2:
        recent = breath_history[-max_history:]
        intensities = [b.get("intensity", "unknown") for b in recent]
        trend = " → ".join(intensities[-3:])  # Last 3
        context_parts.append(f"Breath trend: {trend}")

    # Recent coaching
    if coaching_history:
        last_coaching = coaching_history[-1]
        last_text = last_coaching.get("text", "")
        if last_text:
            context_parts.append(f"Last said: '{last_text}'")

    # Workout progression
    if breath_history:
        first_intensity = breath_history[0].get("intensity", "unknown")
        current_intensity = breath_history[-1].get("intensity", "unknown")
        if first_intensity != current_intensity:
            context_parts.append(f"Progressed from {first_intensity} to {current_intensity}")

    return " | ".join(context_parts) if context_parts else "Starting workout"
