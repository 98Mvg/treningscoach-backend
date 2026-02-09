#
# openai_brain.py
# OpenAI brain adapter with streaming support
#

import os
import random
from typing import Dict, Any, Optional, AsyncIterator, List
from openai import OpenAI, AsyncOpenAI
from .base_brain import BaseBrain
import config
from coach_personality import get_coach_prompt


class OpenAIBrain(BaseBrain):
    """
    OpenAI brain implementation using OpenAI API.
    Supports both legacy coaching mode and new streaming chat mode.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI brain with API key."""
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Sync client for legacy coaching
        self.client = OpenAI(api_key=self.api_key)
        # Async client for streaming chat
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # gpt-4o-mini is cheapest ($0.15/$0.60 per 1M tokens) with great quality
        self.model = "gpt-4o-mini"

    # ============================================
    # BREATH COACHING MODES
    # ============================================

    def get_realtime_coaching(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        STEP 3: Real-Time Coach Brain - Fast, actionable, no explanations.

        This is the product-defining mode for continuous workout coaching.

        Rules:
        - Max 1 sentence (5-10 words)
        - No explanations, no theory
        - Actionable commands only
        - Spoken language optimized
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # Critical situations: use config message directly (fastest)
        if intensitet == "kritisk":
            return random.choice(config.CONTINUOUS_COACH_MESSAGES["kritisk"])

        # Build ultra-minimal context for OpenAI
        language = breath_data.get("language", "en")
        system_prompt = self._build_realtime_system_prompt(phase, intensitet, language)
        user_message = f"{intensitet} breathing, {phase} phase. One action:"

        try:
            # Call OpenAI API with aggressive limits
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=20,  # Force brevity
                temperature=0.9,  # High creativity for variety
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            message = response.choices[0].message.content.strip()

            # Safety: truncate to first sentence if GPT ignores limits
            if '.' in message:
                message = message.split('.')[0] + '.'

            return message

        except Exception as e:
            print(f"OpenAI real-time API error: {e}")
            # Fallback to config messages (still fast)
            return self._get_fallback_message(intensitet, phase)

    def _build_realtime_system_prompt(self, phase: str, intensitet: str, language: str) -> str:
        """Build system prompt for REALTIME COACH mode using endurance coach personality."""

        # Use the shared endurance coach personality with realtime constraints
        base_prompt = get_coach_prompt(mode="realtime_coach", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensitet}"

        return base_prompt + context

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response using OpenAI (CHAT MODE).

        This is the conversational, explanatory mode for educational coaching.
        Uses the configured messages as guidance, but lets GPT add personality.
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # For critical situations, use config message directly
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        # Build context for OpenAI
        language = breath_data.get("language", "en")
        system_prompt = self._build_coaching_system_prompt(phase, intensitet, language)
        user_message = self._build_coaching_user_message(breath_data, phase)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=50,
                temperature=0.8,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            message = response.choices[0].message.content.strip()
            return message

        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to config messages
            return self._get_fallback_message(intensitet, phase)

    def _build_coaching_system_prompt(self, phase: str, intensitet: str, language: str) -> str:
        """Build system prompt for CHAT MODE using endurance coach personality."""

        # Use the shared endurance coach personality for conversational coaching
        base_prompt = get_coach_prompt(mode="chat", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensitet}\n\nProvide coaching in 1-2 concise sentences."

        return base_prompt + context

    def _build_coaching_user_message(self, breath_data: Dict[str, Any], phase: str) -> str:
        """Build user message with breath analysis data."""
        intensitet = breath_data.get("intensitet", "moderat")
        volume = breath_data.get("volume", 0)
        tempo = breath_data.get("tempo", 0)

        return f"""Breath analysis:
- Intensity: {intensitet}
- Volume: {volume}
- Tempo: {tempo} breaths/min
- Phase: {phase}

Give ONE short coaching message (max 7 words):"""

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
        """OpenAI supports streaming."""
        return True

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response from OpenAI token by token.

        Args:
            messages: Conversation history
            system_prompt: System prompt / persona
            **kwargs: temperature, max_tokens, etc.

        Yields:
            Response tokens as they arrive
        """
        try:
            # Prepend system message if provided
            full_messages = messages.copy()
            if system_prompt:
                full_messages.insert(0, {"role": "system", "content": system_prompt})

            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=kwargs.get("temperature", 0.8),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"OpenAI streaming error: {e}")
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
            # Prepend system message if provided
            full_messages = messages.copy()
            if system_prompt:
                full_messages.insert(0, {"role": "system", "content": system_prompt})

            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=kwargs.get("temperature", 0.8),
                max_tokens=kwargs.get("max_tokens", 2048)
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"OpenAI chat error: {e}")
            return f"[Error: {str(e)}]"

    # ============================================
    # METADATA
    # ============================================

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Make a minimal API call to check health
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
