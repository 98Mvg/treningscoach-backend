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
    """

    def __init__(self, brain_type: Optional[str] = None):
        """
        Initialize router with specified brain type.

        Args:
            brain_type: "claude", "openai", or "config" (if None, uses config.ACTIVE_BRAIN)
        """
        self.brain_type = brain_type or config.ACTIVE_BRAIN
        self.brain = None
        self._initialize_brain()

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
            print("✅ Brain Router: Using config-based messages (no AI)")
            self.brain = None

        else:
            print(f"⚠️ Brain Router: Unknown brain type '{self.brain_type}', using config")
            self.brain_type = "config"
            self.brain = None

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Get coaching response from active brain.

        This is the main API method that the app calls.

        Args:
            breath_data: Dictionary containing breath analysis metrics
            phase: Current workout phase ("warmup", "intense", "cooldown")

        Returns:
            String containing coaching message
        """
        # If we have an AI brain, use it
        if self.brain is not None:
            try:
                return self.brain.get_coaching_response(breath_data, phase)
            except Exception as e:
                print(f"⚠️ Brain Router: Brain error: {e}, using fallback")
                return self._get_config_response(breath_data, phase)

        # Otherwise use config-based messages
        return self._get_config_response(breath_data, phase)

    def _get_config_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Get response from config messages (no AI).

        This is the original logic - simple and fast.
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # Critical override
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        # Phase-based responses
        if phase == "warmup":
            return random.choice(config.COACH_MESSAGES["warmup"])

        if phase == "cooldown":
            return random.choice(config.COACH_MESSAGES["cooldown"])

        # Intense phase with intensity levels
        if phase == "intense":
            intense_msgs = config.COACH_MESSAGES["intense"]
            if intensitet in intense_msgs:
                return random.choice(intense_msgs[intensitet])

        return "Fortsett!"

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

    def switch_brain(self, new_brain_type: str) -> bool:
        """
        Switch to a different brain at runtime.

        Args:
            new_brain_type: "claude", "openai", or "config"

        Returns:
            True if switch successful, False otherwise
        """
        old_brain = self.brain_type
        self.brain_type = new_brain_type
        self._initialize_brain()

        success = (self.brain_type == new_brain_type)
        if success:
            print(f"✅ Brain Router: Switched from {old_brain} to {new_brain_type}")
        else:
            print(f"⚠️ Brain Router: Failed to switch to {new_brain_type}, stayed on {self.brain_type}")

        return success
