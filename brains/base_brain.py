#
# base_brain.py
# Abstract base class for all AI brains
#

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseBrain(ABC):
    """
    Abstract base class for AI brain implementations.

    All brain adapters (Claude, OpenAI, Nvidia, etc.) must implement this interface.
    This allows the Brain Router to swap between providers without changing the API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the brain with optional API key.

        Args:
            api_key: API key for the provider (if None, will try to load from environment)
        """
        self.api_key = api_key

    @abstractmethod
    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response based on breath analysis data.

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
