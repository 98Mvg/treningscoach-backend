#
# brain_router.py
# Routes coaching requests to the configured AI brain
#

import os
import random
from typing import Dict, Any, Optional
import config


class BrainRouter:
    """
    Router that directs coaching requests to the active brain.

    This is the single point of contact for the iOS app/website.
    The app never knows which brain is active - it just talks to this router.

    STEP 4: Supports hybrid mode - Claude for patterns, config for speed.
    """

    def __init__(self, brain_type: Optional[str] = None, use_hybrid: Optional[bool] = None):
        """
        Initialize router with specified brain type.

        Args:
            brain_type: "claude", "openai", or "config" (if None, uses config.ACTIVE_BRAIN)
            use_hybrid: Enable hybrid mode (if None, uses config.USE_HYBRID_BRAIN)
        """
        self.brain_type = brain_type or config.ACTIVE_BRAIN
        self.use_hybrid = use_hybrid if use_hybrid is not None else getattr(config, 'USE_HYBRID_BRAIN', False)
        self.brain = None
        self.claude_brain = None  # STEP 4: Keep Claude brain for patterns
        self._initialize_brain()

        # STEP 4: Initialize Claude brain for hybrid mode if enabled
        if self.use_hybrid and self.brain_type == "config":
            self._initialize_hybrid_claude()

    def _initialize_brain(self):
        """Initialize the active brain based on configuration."""
        if self.brain_type == "claude":
            try:
                from brains.claude_brain import ClaudeBrain
                self.brain = ClaudeBrain()
                print(f"✅ Brain Router: Using Claude (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize Claude: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "openai":
            try:
                from brains.openai_brain import OpenAIBrain
                self.brain = OpenAIBrain()
                print(f"✅ Brain Router: Using OpenAI (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize OpenAI: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "config":
            hybrid_status = " (hybrid mode enabled)" if self.use_hybrid else ""
            print(f"✅ Brain Router: Using config-based messages (no AI){hybrid_status}")
            self.brain = None

        else:
            print(f"⚠️ Brain Router: Unknown brain type '{self.brain_type}', using config")
            self.brain_type = "config"
            self.brain = None

    def _initialize_hybrid_claude(self):
        """
        STEP 4: Initialize Claude brain for hybrid mode pattern detection.

        This allows config brain to handle fast responses, while Claude provides
        intelligent pattern detection and trend analysis in the background.
        """
        try:
            from brains.claude_brain import ClaudeBrain
            self.claude_brain = ClaudeBrain()
            print(f"✅ Brain Router: Hybrid mode - Claude available for patterns (model: {self.claude_brain.model})")
        except Exception as e:
            print(f"⚠️ Brain Router: Hybrid mode - Claude unavailable: {e}")
            print("   Continuing with config-only mode")
            self.claude_brain = None

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense",
        mode: str = "realtime_coach",
        language: str = "en",
        persona: str = None
    ) -> str:
        """
        Get coaching response from active brain.

        This is the main API method that the app calls.

        Args:
            breath_data: Dictionary containing breath analysis metrics
            phase: Current workout phase ("warmup", "intense", "cooldown")
            mode: Brain mode - "chat" or "realtime_coach" (default: realtime_coach)
            language: "en" or "no" for language-specific message selection
            persona: Optional persona override (e.g. "toxic_mode" for toxic message bank)

        Returns:
            String containing coaching message
        """
        # STEP 3: Route to appropriate brain mode
        if mode == "realtime_coach":
            # Use optimized real-time coach brain (fast, actionable, no explanations)
            if self.brain is not None:
                try:
                    return self.brain.get_realtime_coaching(breath_data, phase)
                except Exception as e:
                    print(f"⚠️ Brain Router: Real-time brain error: {e}, using fallback")
                    return self._get_config_response(breath_data, phase, language=language, persona=persona)
            else:
                # Config mode uses same messages for both modes
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

        elif mode == "chat":
            # Use conversational chat brain (explanatory, educational)
            if self.brain is not None:
                try:
                    return self.brain.get_coaching_response(breath_data, phase)
                except Exception as e:
                    print(f"⚠️ Brain Router: Chat brain error: {e}, using fallback")
                    return self._get_config_response(breath_data, phase, language=language, persona=persona)
            else:
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

        else:
            print(f"⚠️ Brain Router: Unknown mode '{mode}', using realtime_coach")
            return self.get_coaching_response(breath_data, phase, mode="realtime_coach", language=language, persona=persona)

    def _get_config_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense",
        language: str = "en",
        persona: str = None
    ) -> str:
        """
        Get response from config messages (no AI).
        Supports language selection (EN/NO) and persona-specific message banks.
        """
        intensity = breath_data.get("intensity", breath_data.get("intensitet", "moderate"))

        # Route to toxic mode message bank if persona is toxic_mode
        if persona == "toxic_mode":
            return self._get_toxic_response(intensity, phase, language)

        # Select message bank based on language
        if language == "no":
            messages = config.CONTINUOUS_COACH_MESSAGES_NO
        else:
            messages = config.CONTINUOUS_COACH_MESSAGES

        # Critical override
        if intensity in ("critical", "kritisk"):
            return random.choice(messages.get("critical", ["Stop! Breathe."]))

        # Phase-based responses
        if phase == "warmup":
            return random.choice(messages.get("warmup", ["Easy pace."]))

        if phase == "cooldown":
            return random.choice(messages.get("cooldown", ["Slow down."]))

        # Intense phase with intensity levels
        if phase == "intense":
            intense_msgs = messages.get("intense", {})
            # Normalize intensity key
            intensity_key = intensity if intensity in intense_msgs else "moderate"
            if intensity_key in intense_msgs:
                return random.choice(intense_msgs[intensity_key])

        return "Fortsett!" if language == "no" else "Keep going!"

    def _get_toxic_response(
        self,
        intensity: str,
        phase: str,
        language: str = "en"
    ) -> str:
        """Get response from toxic mode message bank."""
        lang_key = language if language in config.TOXIC_MODE_MESSAGES else "en"
        messages = config.TOXIC_MODE_MESSAGES[lang_key]

        # Critical override (safety first, even in toxic mode)
        if intensity in ("critical", "kritisk"):
            return random.choice(messages.get("critical", ["Stop. Breathe. Safety first."]))

        # Phase-based responses
        if phase == "warmup":
            return random.choice(messages.get("warmup", ["MOVE!"]))

        if phase == "cooldown":
            return random.choice(messages.get("cooldown", ["Fine. Rest."]))

        # Intense phase
        if phase == "intense":
            intense_msgs = messages.get("intense", {})
            intensity_key = intensity if intensity in intense_msgs else "moderate"
            if intensity_key in intense_msgs:
                return random.choice(intense_msgs[intensity_key])

        return "KEEP GOING!" if language == "en" else "FORTSETT!"

    def get_active_brain(self) -> str:
        """Get the name of the currently active brain."""
        if self.brain is not None:
            return self.brain.get_provider_name()
        return "config"

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of active brain.

        Returns:
            Dictionary with health status
        """
        status = {
            "active_brain": self.get_active_brain(),
            "healthy": True,
            "message": "OK"
        }

        if self.brain is not None:
            try:
                brain_healthy = self.brain.health_check()
                status["healthy"] = brain_healthy
                if not brain_healthy:
                    status["message"] = "Brain health check failed"
            except Exception as e:
                status["healthy"] = False
                status["message"] = str(e)

        return status

    def switch_brain(self, new_brain_type: str, preserve_hybrid: bool = True) -> bool:
        """
        STEP 4: Hot-switch to a different brain at runtime.

        Args:
            new_brain_type: "claude", "openai", or "config"
            preserve_hybrid: Keep hybrid Claude brain if switching away from it

        Returns:
            True if switch successful, False otherwise
        """
        old_brain = self.brain_type
        self.brain_type = new_brain_type

        # STEP 4: Preserve hybrid Claude if requested
        if preserve_hybrid and self.claude_brain is not None:
            old_claude = self.claude_brain
        else:
            old_claude = None

        self._initialize_brain()

        # Restore hybrid Claude if preserved
        if preserve_hybrid and old_claude is not None:
            self.claude_brain = old_claude
            print(f"   Hybrid Claude brain preserved for pattern detection")

        success = (self.brain_type == new_brain_type)
        if success:
            print(f"✅ Brain Router: Switched from {old_brain} to {new_brain_type}")
        else:
            print(f"⚠️ Brain Router: Failed to switch to {new_brain_type}, stayed on {self.brain_type}")

        return success

    # ============================================
    # STEP 4: HYBRID MODE METHODS
    # ============================================

    def detect_pattern(
        self,
        breath_history: list,
        coaching_history: list,
        phase: str
    ) -> Optional[str]:
        """
        STEP 4: Use Claude to detect patterns and trends over time.

        This is called in the background (non-blocking) to provide higher-level
        encouragement based on workout progression.

        Args:
            breath_history: List of recent breath analyses
            coaching_history: List of recent coaching messages
            phase: Current workout phase

        Returns:
            Pattern insight string or None if no pattern detected
        """
        # Only works in hybrid mode with Claude available
        if not self.use_hybrid or self.claude_brain is None:
            return None

        # Need sufficient history to detect patterns
        if len(breath_history) < 3:
            return None

        try:
            # Build context for Claude
            context = self._build_pattern_context(breath_history, coaching_history, phase)

            # Ask Claude to detect patterns (using chat mode, not realtime)
            # This is intentionally slower/deeper than realtime coaching
            pattern_prompt = f"""Analyze this workout progression and identify ONE key pattern or trend.

{context}

Provide ONE short insight (max 15 words) about their progression.
Examples:
- "You're building intensity steadily - great pacing!"
- "Breathing stabilized after initial spike - you found your rhythm."
- "Intensity dropping - time to push harder?"

Your insight:"""

            message = self.claude_brain.client.messages.create(
                model=self.claude_brain.model,
                max_tokens=50,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": pattern_prompt}
                ]
            )

            insight = message.content[0].text.strip()
            return insight

        except Exception as e:
            print(f"⚠️ Pattern detection error: {e}")
            return None

    def _build_pattern_context(
        self,
        breath_history: list,
        coaching_history: list,
        phase: str
    ) -> str:
        """Build context string for pattern detection."""

        context_parts = [f"Phase: {phase}"]

        # Recent breath trend
        if len(breath_history) >= 3:
            recent = breath_history[-5:]  # Last 5 samples
            intensities = [b.get("intensitet", "?") for b in recent]
            tempos = [b.get("tempo", 0) for b in recent]

            context_parts.append(f"Intensity trend: {' → '.join(intensities)}")
            context_parts.append(f"Tempo range: {min(tempos)}-{max(tempos)} breaths/min")

        # Coaching pattern
        if coaching_history:
            last_messages = [c.get("text", "") for c in coaching_history[-3:]]
            context_parts.append(f"Recent coaching: {', '.join(last_messages)}")

        return "\n".join(context_parts)

    def should_use_pattern_insight(
        self,
        elapsed_seconds: int,
        last_pattern_time: Optional[int]
    ) -> bool:
        """
        STEP 4: Decide if it's time to inject a pattern-based insight.

        Pattern insights are sparse (every 60-90 seconds) to avoid over-coaching.

        Args:
            elapsed_seconds: Total workout time
            last_pattern_time: When last pattern insight was given

        Returns:
            True if pattern insight should be used
        """
        # Don't give pattern insights too early
        if elapsed_seconds < 30:
            return False

        # Don't give pattern insights too frequently
        if last_pattern_time is not None:
            time_since_last = elapsed_seconds - last_pattern_time
            if time_since_last < 60:  # Minimum 60 seconds between pattern insights
                return False

        # Random chance to keep it natural (not every 60 seconds on the dot)
        return random.random() < 0.3  # 30% chance when eligible
