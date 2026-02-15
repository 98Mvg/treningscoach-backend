#
# grok_brain.py
# xAI Grok brain adapter using OpenAI-compatible API
#
# Grok API is fully compatible with the OpenAI SDK.
# Base URL: https://api.x.ai/v1
# Models: grok-3, grok-4
# Docs: https://docs.x.ai/docs
#

import os
import random
from typing import Dict, Any, Optional, AsyncIterator, List
from openai import OpenAI, AsyncOpenAI
from .base_brain import BaseBrain
import config
from coach_personality import get_coach_prompt


class GrokBrain(BaseBrain):
    """
    xAI Grok brain implementation using OpenAI-compatible API.

    Grok's API is fully compatible with the OpenAI SDK, so we use the same
    openai Python package with a different base_url pointing to api.x.ai.

    Supports both legacy coaching mode and streaming chat mode.
    """

    # xAI API base URL (OpenAI-compatible)
    XAI_BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Grok brain with xAI API key.

        Args:
            api_key: xAI API key (starts with "xai-"). Falls back to XAI_API_KEY env var.
            model: Model to use. Defaults to XAI_MODEL env var or "grok-3-mini".
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not found in environment")

        # Model selection: env var > parameter > default
        # grok-3-mini is cheapest ($0.30/$0.50 per 1M tokens) and outperforms grok-3
        self.model = model or os.getenv("XAI_MODEL", "grok-3-mini")

        # Sync client for legacy coaching (OpenAI SDK with xAI base URL)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.XAI_BASE_URL
        )
        # Async client for streaming chat
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.XAI_BASE_URL
        )

    # ============================================
    # BREATH COACHING MODES
    # ============================================

    def get_realtime_coaching(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Real-Time Coach Brain - Fast, actionable, no explanations.

        Uses Grok for creative, punchy coaching cues.

        Rules:
        - Max 1 sentence (5-10 words)
        - No explanations, no theory
        - Actionable commands only
        - Spoken language optimized
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # Critical situations: use config message directly (fastest, no API call)
        if intensitet == "kritisk":
            return random.choice(config.CONTINUOUS_COACH_MESSAGES["kritisk"])

        # Build ultra-minimal context for Grok
        language = breath_data.get("language", "en")
        user_name = breath_data.get("user_name", "")
        system_prompt = self._build_realtime_system_prompt(phase, intensitet, language, user_name=user_name)
        user_message = f"{intensitet} breathing, {phase} phase. One action:"

        try:
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

            # Safety: truncate to first sentence if model ignores limits
            if '.' in message:
                message = message.split('.')[0] + '.'

            return message

        except Exception as e:
            print(f"Grok real-time API error: {e}")
            # Fallback to config messages (still fast)
            return self._get_fallback_message(intensitet, phase)

    def _build_realtime_system_prompt(self, phase: str, intensitet: str, language: str, user_name: str = "") -> str:
        """Build system prompt for REALTIME COACH mode using endurance coach personality."""

        # Use the shared endurance coach personality with realtime constraints
        base_prompt = get_coach_prompt(mode="realtime_coach", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensitet}"

        # Norwegian character instruction
        if language == "no":
            context += "\n- IMPORTANT: Use proper Norwegian characters: æ, ø, å (NOT ae, oe, aa). Example: 'Kjør på!' not 'Kjoer paa!'"

        # Personalize with user name — RARE usage (max 1-2 times per workout)
        if user_name:
            context += f"\n- Athlete's name: {user_name}. Use their name at MOST once or twice during the entire workout — never on back-to-back messages. Most messages should NOT include the name."

        return base_prompt + context

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response using Grok (CHAT MODE).

        Conversational, explanatory mode for educational coaching.
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # Critical situations: config message directly
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        language = breath_data.get("language", "en")
        user_name = breath_data.get("user_name", "")
        system_prompt = self._build_coaching_system_prompt(phase, intensitet, language, user_name=user_name)
        user_message = self._build_coaching_user_message(breath_data, phase)

        try:
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
            print(f"Grok API error: {e}")
            return self._get_fallback_message(intensitet, phase)

    def _build_coaching_system_prompt(self, phase: str, intensitet: str, language: str, user_name: str = "") -> str:
        """Build system prompt for CHAT MODE using endurance coach personality."""

        # Use the shared endurance coach personality for conversational coaching
        base_prompt = get_coach_prompt(mode="chat", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensitet}\n\nProvide coaching in 1-2 concise sentences."

        # Norwegian character instruction
        if language == "no":
            context += "\nIMPORTANT: Use proper Norwegian characters: æ, ø, å (NOT ae, oe, aa). Example: 'Kjør på!' not 'Kjoer paa!'"

        # Personalize with user name — RARE usage
        if user_name:
            context += f"\nAthlete's name: {user_name}. Use their name at MOST once or twice total — never on consecutive messages. Most messages should NOT include the name."

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
            return "Keep going!"

    # ============================================
    # STREAMING CHAT MODE
    # ============================================

    def supports_streaming(self) -> bool:
        """Grok supports streaming via OpenAI-compatible API."""
        return True

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response from Grok token by token.

        Args:
            messages: Conversation history
            system_prompt: System prompt / persona
            **kwargs: temperature, max_tokens, etc.

        Yields:
            Response tokens as they arrive
        """
        try:
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
            print(f"Grok streaming error: {e}")
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
            print(f"Grok chat error: {e}")
            return f"[Error: {str(e)}]"

    # ============================================
    # METADATA
    # ============================================

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "grok"

    def health_check(self) -> bool:
        """Check if xAI Grok API is accessible."""
        try:
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
