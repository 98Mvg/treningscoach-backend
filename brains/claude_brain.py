#
# claude_brain.py
# Claude AI brain adapter with streaming support
#

import os
import random
from typing import Dict, Any, Optional, AsyncIterator, List
from anthropic import Anthropic, AsyncAnthropic
from .base_brain import BaseBrain
import config


class ClaudeBrain(BaseBrain):
    """
    Claude AI brain implementation using Anthropic API.
    Supports both legacy coaching mode and new streaming chat mode.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude brain with API key."""
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        # Sync client for legacy coaching
        self.client = Anthropic(api_key=self.api_key)
        # Async client for streaming chat
        self.async_client = AsyncAnthropic(api_key=self.api_key)

        self.model = "claude-3-5-sonnet-20241022"

    # ============================================
    # LEGACY: Breath Coaching Mode
    # ============================================

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response using Claude.

        Uses the configured messages as guidance, but lets Claude add personality.
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # For critical situations, use config message directly
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        # Build context for Claude
        system_prompt = self._build_coaching_system_prompt(phase, intensitet)
        user_message = self._build_coaching_user_message(breath_data, phase)

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            response = message.content[0].text.strip()
            return response

        except Exception as e:
            print(f"Claude API error: {e}")
            # Fallback to config messages
            return self._get_fallback_message(intensitet, phase)

    def _build_coaching_system_prompt(self, phase: str, intensitet: str) -> str:
        """Build system prompt for Claude based on phase and intensity."""
        base_prompt = """Du er en motiverende treningscoach som gir korte, kraftige beskjeder basert på pustanalyse.

Regler:
- Maks 5-7 ord per beskjed
- Bruk store bokstaver for intensitet
- Vær direkte og motiverende
- Tilpass tone til treningsfase og pusteintensitet
"""

        if phase == "warmup":
            base_prompt += "\nFase: OPPVARMING - Vær rolig og oppmuntrende. Hjelp brukeren starte forsiktig."
        elif phase == "cooldown":
            base_prompt += "\nFase: NEDKJØLING - Vær rolig og beroligende. Hjelp brukeren roe ned."
        else:  # intense
            if intensitet == "rolig":
                base_prompt += "\nFase: HARD TRENING - Bruker puster FOR ROLIG. Push dem til å øke intensiteten!"
            elif intensitet == "moderat":
                base_prompt += "\nFase: HARD TRENING - Bruker er i moderat intensitet. Oppretthold motivasjon!"
            elif intensitet == "hard":
                base_prompt += "\nFase: HARD TRENING - Bruker går ALL IN! Bekreft og oppmuntre!"

        # Add example messages from config as style guide
        example_messages = self._get_example_messages(phase, intensitet)
        if example_messages:
            base_prompt += f"\n\nEksempler på stil:\n" + "\n".join(f"- {msg}" for msg in example_messages[:3])

        return base_prompt

    def _build_coaching_user_message(self, breath_data: Dict[str, Any], phase: str) -> str:
        """Build user message with breath analysis data."""
        intensitet = breath_data.get("intensitet", "moderat")
        volume = breath_data.get("volume", 0)
        tempo = breath_data.get("tempo", 0)

        return f"""Pustanalyse:
- Intensitet: {intensitet}
- Volum: {volume}
- Tempo: {tempo} pust/min
- Fase: {phase}

Gi EN kort coach-beskjed (maks 7 ord):"""

    def _get_example_messages(self, phase: str, intensitet: str) -> list:
        """Get example messages from config for this phase/intensity."""
        if phase == "warmup":
            return config.COACH_MESSAGES.get("warmup", [])
        elif phase == "cooldown":
            return config.COACH_MESSAGES.get("cooldown", [])
        else:  # intense
            intense_msgs = config.COACH_MESSAGES.get("intense", {})
            return intense_msgs.get(intensitet, [])

    def _get_fallback_message(self, intensitet: str, phase: str) -> str:
        """Get fallback message from config if API fails."""
        if phase == "warmup":
            return random.choice(config.COACH_MESSAGES["warmup"])
        elif phase == "cooldown":
            return random.choice(config.COACH_MESSAGES["cooldown"])
        else:
            intense_msgs = config.COACH_MESSAGES["intense"]
            if intensitet in intense_msgs:
                return random.choice(intense_msgs[intensitet])
            return "Fortsett!"

    # ============================================
    # NEW: Streaming Chat Mode
    # ============================================

    def supports_streaming(self) -> bool:
        """Claude supports streaming."""
        return True

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response from Claude token by token.

        Args:
            messages: Conversation history
            system_prompt: System prompt / persona
            **kwargs: temperature, max_tokens, etc.

        Yields:
            Response tokens as they arrive
        """
        try:
            async with self.async_client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.8),
                system=system_prompt or "",
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            print(f"Claude streaming error: {e}")
            # Fallback: yield error message
            yield f"[Error: {str(e)}]"

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
        try:
            message = await self.async_client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.8),
                system=system_prompt or "",
                messages=messages
            )
            return message.content[0].text

        except Exception as e:
            print(f"Claude chat error: {e}")
            return f"[Error: {str(e)}]"

    # ============================================
    # METADATA
    # ============================================

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "claude"

    def health_check(self) -> bool:
        """Check if Claude API is accessible."""
        try:
            # Make a minimal API call to check health
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
