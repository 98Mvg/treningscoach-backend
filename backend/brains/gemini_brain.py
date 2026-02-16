#
# gemini_brain.py
# Google Gemini brain adapter using google-generativeai SDK
#
# Docs: https://ai.google.dev/gemini-api/docs
#

import os
import random
from typing import Dict, Any, Optional, AsyncIterator, List

from .base_brain import BaseBrain
import config
from coach_personality import get_coach_prompt

try:
    import google.generativeai as genai
except Exception as e:  # pragma: no cover - import-time guard
    genai = None
    _GENAI_IMPORT_ERROR = e


class GeminiBrain(BaseBrain):
    """
    Google Gemini brain implementation using google-generativeai SDK.

    Supports both legacy coaching mode and streaming chat mode.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini brain with API key.

        Args:
            api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
            model: Model to use. Defaults to GEMINI_MODEL env var or "gemini-2.0-flash-lite".
        """
        super().__init__(api_key)
        if genai is None:
            raise ImportError(
                "google-generativeai is not installed. Install it with `pip install google-generativeai`."
            ) from _GENAI_IMPORT_ERROR

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        # Model selection: env var > parameter > default
        # flash-lite is the cheapest, fast Gemini option
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

        # Configure global API key for SDK
        genai.configure(api_key=self.api_key)
        self.genai = genai

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

        Rules:
        - Max 1 sentence (5-10 words)
        - No explanations, no theory
        - Actionable commands only
        - Spoken language optimized
        """
        intensity = self.extract_intensity(breath_data)
        language = self.extract_language(breath_data)

        # Critical situations: use config message directly (fastest, no API call)
        if intensity == "critical":
            messages = config.CONTINUOUS_COACH_MESSAGES_NO if language == "no" else config.CONTINUOUS_COACH_MESSAGES
            return random.choice(messages.get("critical", ["Stop. Breathe slow."]))

        system_prompt = self._build_realtime_system_prompt(phase, intensity, language)
        user_message = f"{intensity} breathing, {phase} phase. One action:"

        try:
            model = self._make_model(system_prompt)
            response = model.generate_content(
                user_message,
                generation_config={
                    "max_output_tokens": 20,
                    "temperature": 0.9
                }
            )

            message = (response.text or "").strip()
            if not message:
                raise ValueError("Empty Gemini response")

            # Safety: truncate to first sentence if model ignores limits
            if '.' in message:
                message = message.split('.')[0] + '.'

            return message

        except Exception as e:
            print(f"Gemini real-time API error: {e}")
            raise RuntimeError(f"Gemini realtime request failed: {e}") from e

    def _build_realtime_system_prompt(self, phase: str, intensity: str, language: str) -> str:
        """Build system prompt for REALTIME COACH mode using endurance coach personality."""
        base_prompt = get_coach_prompt(mode="realtime_coach", language=language)
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensity}"
        return base_prompt + context

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response using Gemini (CHAT MODE).
        """
        intensity = self.extract_intensity(breath_data)
        language = self.extract_language(breath_data)

        # Critical situations: config message directly
        if intensity == "critical":
            messages = config.COACH_MESSAGES_NO if language == "no" else config.COACH_MESSAGES
            return random.choice(messages.get("critical", ["Stop. Breathe slow."]))

        system_prompt = self._build_coaching_system_prompt(phase, intensity, language)
        user_message = self._build_coaching_user_message(breath_data, phase)

        try:
            model = self._make_model(system_prompt)
            response = model.generate_content(
                user_message,
                generation_config={
                    "max_output_tokens": 50,
                    "temperature": 0.8
                }
            )
            message = (response.text or "").strip()
            if not message:
                raise ValueError("Empty Gemini response")
            return message

        except Exception as e:
            print(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini chat request failed: {e}") from e

    def _build_coaching_system_prompt(self, phase: str, intensity: str, language: str) -> str:
        """Build system prompt for CHAT MODE using endurance coach personality."""
        base_prompt = get_coach_prompt(mode="chat", language=language)
        context = (
            f"\n\nCurrent context:\n- Phase: {phase.upper()}\n"
            f"- Breathing intensity: {intensity}\n\n"
            "Provide coaching in 1-2 concise sentences."
        )
        return base_prompt + context

    def _build_coaching_user_message(self, breath_data: Dict[str, Any], phase: str) -> str:
        """Build user message with breath analysis data."""
        intensity = self.extract_intensity(breath_data)
        volume = breath_data.get("volume", 0)
        tempo = breath_data.get("tempo", 0)

        return f"""Breath analysis:
- Intensity: {intensity}
- Volume: {volume}
- Tempo: {tempo} breaths/min
- Phase: {phase}

Give ONE short coaching message (max 7 words):"""

    def _get_fallback_message(self, intensity: str, phase: str, language: str = "en") -> str:
        """Get fallback message from config if API fails."""
        message_bank = config.COACH_MESSAGES_NO if language == "no" else config.COACH_MESSAGES
        if phase == "warmup":
            return random.choice(message_bank.get("warmup", ["Easy start."]))
        if phase == "cooldown":
            return random.choice(message_bank.get("cooldown", ["Slow down."]))
        intense_msgs = message_bank.get("intense", {})
        if intensity in intense_msgs and intense_msgs[intensity]:
            return random.choice(intense_msgs[intensity])
        return self.localized_keep_going(language)

    def _make_model(self, system_prompt: Optional[str] = None):
        """Create a GenerativeModel with optional system instruction."""
        if system_prompt:
            return self.genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_prompt
            )
        return self.genai.GenerativeModel(model_name=self.model)

    def _build_chat_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Flatten chat messages to a single prompt string."""
        parts = []
        if system_prompt:
            parts.append(f"System: {system_prompt}")
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            parts.append(f"{role.capitalize()}: {content}")
        parts.append("Assistant:")
        return "\n".join(parts)

    # ============================================
    # NEW: Streaming Chat Mode
    # ============================================

    def supports_streaming(self) -> bool:
        """Gemini supports streaming."""
        return True

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat response from Gemini.
        """
        prompt = self._build_chat_prompt(messages, system_prompt)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 512)

        model = self._make_model()
        try:
            response = model.generate_content(
                prompt,
                stream=True,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
            )
            for chunk in response:
                text = getattr(chunk, "text", "") or ""
                if text:
                    yield text
        except Exception as e:
            print(f"Gemini streaming error: {e}")
            # Fallback to non-streaming response
            fallback = await self.chat(messages, system_prompt=system_prompt, **kwargs)
            if fallback:
                yield fallback

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Non-streaming chat response from Gemini.
        """
        prompt = self._build_chat_prompt(messages, system_prompt)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 512)

        model = self._make_model()
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        return (response.text or "").strip()

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "gemini"
