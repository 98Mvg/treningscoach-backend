# coaching_intelligence.py - Intelligence layer for continuous coaching decisions

from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def should_coach_speak(
    current_analysis: Dict,
    last_analysis: Optional[Dict],
    coaching_history: List[Dict],
    phase: str
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

    # Rule 1: Always speak for critical breathing (safety override)
    if intensity == "critical":
        logger.info("Coach speaking: critical_breathing detected")
        return (True, "critical_breathing")

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

    # Rule 4: Phase-aware periodic speaking
    # Warmup: coach talks more (every 30s) — tips, encouragement, preparation
    # Intense: coach stays quiet, breath-focused (every 90s) — minimal distraction
    # Cooldown: moderate (every 45s) — recovery guidance
    periodic_intervals = {
        "warmup": 30,     # More talkative during warmup
        "intense": 90,    # Minimal during workout — focus on breath
        "cooldown": 45    # Moderate during cooldown
    }
    periodic_interval = periodic_intervals.get(phase, 60)

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
