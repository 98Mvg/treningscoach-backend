#
# base_brain.py
# Abstract base class for all AI brains
#

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator, List


class BaseBrain(ABC):
    """
    Abstract base class for AI brain implementations.

    All brain adapters (Claude, OpenAI, Nvidia, etc.) must implement this interface.
    This allows the Brain Router to swap between providers without changing the API.

    Supports both:
    1. Legacy coaching mode (breath analysis)
    2. New streaming chat mode (conversational AI)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the brain with optional API key.

        Args:
            api_key: API key for the provider (if None, will try to load from environment)
        """
        self.api_key = api_key

    @staticmethod
    def normalize_language(language: Optional[str]) -> str:
        """Normalize locale-like values to supported language codes."""
        value = (language or "en").strip().lower()
        if value.startswith(("nb", "nn", "no")):
            return "no"
        if value.startswith("da"):
            return "da"
        if value.startswith("en"):
            return "en"
        return "en"

    @staticmethod
    def normalize_intensity(raw_intensity: Optional[str]) -> str:
        """Normalize legacy/localized intensity values to canonical EN keys."""
        value = (raw_intensity or "moderate").strip().lower()
        mapping = {
            "critical": "critical",
            "kritisk": "critical",
            "intense": "intense",
            "hard": "intense",
            "hoy": "intense",
            "høy": "intense",
            "moderate": "moderate",
            "moderat": "moderate",
            "calm": "calm",
            "rolig": "calm",
            "easy": "calm",
        }
        return mapping.get(value, "moderate")

    def extract_language(self, breath_data: Dict[str, Any]) -> str:
        """Read language from breath payload with safe normalization."""
        return self.normalize_language(breath_data.get("language"))

    def extract_intensity(self, breath_data: Dict[str, Any]) -> str:
        """Read intensity from both new and legacy payload keys."""
        raw = breath_data.get("intensity", breath_data.get("intensitet"))
        return self.normalize_intensity(raw)

    @staticmethod
    def localized_keep_going(language: str) -> str:
        """Language-safe default fallback cue."""
        return "Fortsett!" if language == "no" else "Keep going!"

    # ============================================
    # BREATH COACHING MODES
    # ============================================

    @abstractmethod
    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response based on breath analysis data (CHAT MODE).

        This is the conversational, explanatory mode for educational coaching.

        Args:
            breath_data: Dictionary containing breath analysis metrics
                - intensitet: "rolig", "moderat", "hard", "kritisk"
                - volume: breath volume metric
                - tempo: breaths per minute
                - silence_percentage: percentage of silence in recording
            phase: Current workout phase ("warmup", "intense", "cooldown")

        Returns:
            String containing coaching message
        """
        pass

    @abstractmethod
    def get_realtime_coaching(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate real-time coaching cue (REALTIME_COACH MODE).

        STEP 3: This is the product-defining real-time coach brain.

        Rules:
        - Max 1 sentence per response
        - No explanations
        - No theory
        - Actionable only
        - Spoken language optimized

        Args:
            breath_data: Dictionary containing breath analysis metrics
            phase: Current workout phase

        Returns:
            Short, actionable coaching cue (1 sentence max)
        """
        pass

    # ============================================
    # NEW: Streaming Chat Mode
    # ============================================

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Does this brain support token-by-token streaming?

        Returns:
            True if streaming is supported, False otherwise
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response token by token.

        Args:
            messages: Conversation history in format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            system_prompt: System prompt / persona to apply
            **kwargs: Model-specific parameters (temperature, max_tokens, etc.)

        Yields:
            Response tokens as they arrive from the AI

        Example:
            async for token in brain.stream_chat(messages, system_prompt="You are a coach"):
                print(token, end="", flush=True)
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Non-streaming chat (fallback).

        Args:
            messages: Conversation history
            system_prompt: System prompt / persona
            **kwargs: Model parameters

        Returns:
            Complete response string
        """
        pass

    # ============================================
    # METADATA
    # ============================================

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this brain provider.

        Returns:
            String identifier (e.g., "claude", "openai", "nvidia")
        """
        pass

    def health_check(self) -> bool:
        """
        Check if the brain is healthy and can make requests.

        Returns:
            True if healthy, False otherwise
        """
        return True
