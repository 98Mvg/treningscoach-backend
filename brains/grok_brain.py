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
import re
from typing import Dict, Any, Optional, AsyncIterator, List
from openai import OpenAI, AsyncOpenAI
from .base_brain import BaseBrain
import config
from persona_manager import get_coach_prompt


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

        # Keep HTTP client timeouts slightly below router timeouts to avoid
        # timed-out work continuing in background threads.
        self.request_timeout = self._timeout_for_mode("realtime_coach")

        # Sync client for legacy coaching (OpenAI SDK with xAI base URL)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.XAI_BASE_URL,
            max_retries=0,
            timeout=self.request_timeout,
        )
        # Async client for streaming chat
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.XAI_BASE_URL,
            max_retries=0,
            timeout=self.request_timeout,
        )

    def _timeout_for_mode(self, mode: str) -> float:
        """Resolve provider HTTP timeout for this mode."""
        mode_timeouts = getattr(config, "BRAIN_MODE_TIMEOUTS", {}) or {}
        if isinstance(mode_timeouts, dict):
            per_mode = mode_timeouts.get(mode, {})
            if isinstance(per_mode, dict):
                if "grok" in per_mode:
                    return max(1.0, float(per_mode["grok"]))
                if "default" in per_mode:
                    return max(1.0, float(per_mode["default"]))

        explicit = getattr(config, "GROK_CLIENT_TIMEOUT_SECONDS", None)
        if explicit is not None:
            return max(1.0, float(explicit))

        per_brain = getattr(config, "BRAIN_TIMEOUTS", {}) or {}
        base = float(per_brain.get("grok", getattr(config, "BRAIN_TIMEOUT", 6.0)))
        margin = float(getattr(config, "BRAIN_CLIENT_TIMEOUT_MARGIN_SECONDS", 0.25))
        return max(1.0, base - margin)

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
        intensity = self.extract_intensity(breath_data)
        language = self.extract_language(breath_data)

        # Critical situations: use config message directly (fastest, no API call)
        if intensity == "critical":
            messages = config.CONTINUOUS_COACH_MESSAGES_NO if language == "no" else config.CONTINUOUS_COACH_MESSAGES
            return random.choice(messages.get("critical", ["Stop. Breathe slow."]))

        # Build ultra-minimal context for Grok
        user_name = breath_data.get("user_name", "")
        recent_cues = breath_data.get("recent_coach_cues") or []
        coaching_reason = breath_data.get("coaching_reason")
        persona = breath_data.get("persona")
        training_level = breath_data.get("training_level")
        persona_mode = breath_data.get("persona_mode")
        emotional_trend = breath_data.get("emotional_trend")
        emotional_intensity = breath_data.get("emotional_intensity")
        safety_override = breath_data.get("safety_override")
        system_prompt = self._build_realtime_system_prompt(
            phase,
            intensity,
            language,
            persona=persona,
            training_level=training_level,
            persona_mode=persona_mode,
            emotional_trend=emotional_trend,
            emotional_intensity=emotional_intensity,
            safety_override=safety_override,
            user_name=user_name,
            recent_cues=recent_cues,
            coaching_reason=coaching_reason,
        )
        user_message = f"{intensity} breathing, {phase} phase. One action:"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=20,  # Force brevity
                temperature=0.9,  # High creativity for variety
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                timeout=self._timeout_for_mode("realtime_coach"),
            )

            message = response.choices[0].message.content.strip()

            # Safety: truncate to first sentence if model ignores limits
            if '.' in message:
                message = message.split('.')[0] + '.'

            return message

        except Exception as e:
            print(f"Grok real-time API error: {e}")
            raise RuntimeError(f"Grok realtime request failed: {e}") from e

    def _build_realtime_system_prompt(
        self,
        phase: str,
        intensity: str,
        language: str,
        persona: Optional[str] = None,
        training_level: Optional[str] = None,
        persona_mode: Optional[str] = None,
        emotional_trend: Optional[str] = None,
        emotional_intensity: Optional[float] = None,
        safety_override: bool = False,
        user_name: str = "",
        recent_cues: Optional[list] = None,
        coaching_reason: Optional[str] = None,
    ) -> str:
        """Build system prompt for REALTIME COACH mode using endurance coach personality."""

        # Use the shared endurance coach personality with realtime constraints
        base_prompt = get_coach_prompt(mode="realtime_coach", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensity}"
        context += "\n- Response format: 2-5 words, one actionable cue."
        context += self.build_persona_directives(
            {
                "persona": persona,
                "training_level": training_level,
                "persona_mode": persona_mode,
                "emotional_trend": emotional_trend,
                "emotional_intensity": emotional_intensity,
                "safety_override": safety_override,
            },
            language=language,
            mode="realtime_coach",
        )
        context += self._get_realtime_persona_rules(persona, training_level)

        if coaching_reason:
            context += f"\n- Decision reason: {coaching_reason}"

        cleaned_recent = [str(c).strip() for c in (recent_cues or []) if str(c).strip()]
        if cleaned_recent:
            context += "\n- Avoid repeating these recent cues verbatim:"
            for cue in cleaned_recent[-4:]:
                context += f"\n  - {cue}"
            context += "\n- Use different wording from recent cues."

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
        intensity = self.extract_intensity(breath_data)
        language = self.extract_language(breath_data)

        # Critical situations: config message directly
        if intensity == "critical":
            messages = config.COACH_MESSAGES_NO if language == "no" else config.COACH_MESSAGES
            return random.choice(messages.get("critical", ["Stop. Breathe slow."]))

        user_name = breath_data.get("user_name", "")
        persona = breath_data.get("persona")
        training_level = breath_data.get("training_level")
        persona_mode = breath_data.get("persona_mode")
        emotional_trend = breath_data.get("emotional_trend")
        emotional_intensity = breath_data.get("emotional_intensity")
        safety_override = breath_data.get("safety_override")
        system_prompt = self._build_coaching_system_prompt(
            phase,
            intensity,
            language,
            user_name=user_name,
            persona=persona,
            training_level=training_level,
            persona_mode=persona_mode,
            emotional_trend=emotional_trend,
            emotional_intensity=emotional_intensity,
            safety_override=safety_override,
        )
        user_message = self._build_coaching_user_message(breath_data, phase)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=50,
                temperature=0.8,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                timeout=self._timeout_for_mode("chat"),
            )

            message = response.choices[0].message.content.strip()
            return message

        except Exception as e:
            print(f"Grok API error: {e}")
            raise RuntimeError(f"Grok chat request failed: {e}") from e

    def _build_coaching_system_prompt(
        self,
        phase: str,
        intensity: str,
        language: str,
        user_name: str = "",
        persona: Optional[str] = None,
        training_level: Optional[str] = None,
        persona_mode: Optional[str] = None,
        emotional_trend: Optional[str] = None,
        emotional_intensity: Optional[float] = None,
        safety_override: bool = False,
    ) -> str:
        """Build system prompt for CHAT MODE using endurance coach personality."""

        # Use the shared endurance coach personality for conversational coaching
        base_prompt = get_coach_prompt(mode="chat", language=language)

        # Add current context
        context = f"\n\nCurrent context:\n- Phase: {phase.upper()}\n- Breathing intensity: {intensity}\n\nProvide coaching in 1-2 concise sentences."
        context += self.build_persona_directives(
            {
                "persona": persona,
                "training_level": training_level,
                "persona_mode": persona_mode,
                "emotional_trend": emotional_trend,
                "emotional_intensity": emotional_intensity,
                "safety_override": safety_override,
            },
            language=language,
            mode="chat",
        )
        context += self._get_chat_persona_rules(persona, training_level)

        # Norwegian character instruction
        if language == "no":
            context += "\nIMPORTANT: Use proper Norwegian characters: æ, ø, å (NOT ae, oe, aa). Example: 'Kjør på!' not 'Kjoer paa!'"

        # Personalize with user name — RARE usage
        if user_name:
            context += f"\nAthlete's name: {user_name}. Use their name at MOST once or twice total — never on consecutive messages. Most messages should NOT include the name."

        return base_prompt + context

    def _normalize_persona(self, persona: Optional[str]) -> str:
        value = (persona or "personal_trainer").strip().lower()
        if value not in {"personal_trainer", "toxic_mode"}:
            return "personal_trainer"
        return value

    def _get_realtime_persona_rules(self, persona: Optional[str], training_level: Optional[str]) -> str:
        persona_key = self._normalize_persona(persona)

        if persona_key == "toxic_mode":
            rules = (
                "\n- Persona mode: toxic_mode."
                "\n- Voice style: aggressive drill-sergeant with dark humor."
                "\n- Use sharp commands, occasional CAPS, and confrontational energy."
                "\n- Keep it playful-mocking, never personal or unsafe."
                "\n- Do not repeat the exact same cue on consecutive speaking ticks."
            )
        else:
            rules = (
                "\n- Persona mode: personal_trainer."
                "\n- Voice style: calm and disciplined elite coach."
                "\n- Use direct, constructive cues with steady confidence."
                "\n- No sarcasm and no shouting."
                "\n- Do not repeat the exact same cue on consecutive speaking ticks."
            )

        return rules

    def _get_chat_persona_rules(self, persona: Optional[str], training_level: Optional[str]) -> str:
        persona_key = self._normalize_persona(persona)

        if persona_key == "toxic_mode":
            rules = (
                "\n- Persona mode: toxic_mode."
                "\n- Tone: intense, confrontational, and darkly humorous."
                "\n- Keep responses short and energetic, but never unsafe."
            )
        else:
            rules = (
                "\n- Persona mode: personal_trainer."
                "\n- Tone: calm, structured, and performance-focused."
                "\n- Be honest and constructive without hype."
            )

        return rules

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

    def _get_example_messages(self, phase: str, intensity: str, language: str = "en") -> list:
        """Get example messages from config for this phase/intensity."""
        message_bank = config.COACH_MESSAGES_NO if language == "no" else config.COACH_MESSAGES
        if phase == "warmup":
            return message_bank.get("warmup", [])
        elif phase == "cooldown":
            return message_bank.get("cooldown", [])
        else:  # intense
            intense_msgs = message_bank.get("intense", {})
            return intense_msgs.get(intensity, [])

    def _get_fallback_message(self, intensity: str, phase: str, language: str = "en") -> str:
        """Get fallback message from config if API fails."""
        message_bank = config.COACH_MESSAGES_NO if language == "no" else config.COACH_MESSAGES
        if phase == "warmup":
            return random.choice(message_bank.get("warmup", ["Easy start."]))
        elif phase == "cooldown":
            return random.choice(message_bank.get("cooldown", ["Slow down."]))
        else:
            intense_msgs = message_bank.get("intense", {})
            if intensity in intense_msgs and intense_msgs[intensity]:
                return random.choice(intense_msgs[intensity])
            return self.localized_keep_going(language)

    def rewrite_zone_event_text(
        self,
        base_text: str,
        *,
        language: str = "en",
        persona: Optional[str] = None,
        coaching_style: str = "normal",
        event_type: Optional[str] = None,
    ) -> str:
        """
        Rephrase deterministic zone-event text without changing intent or action.

        This is used only by the Phase 4 phrasing layer; event decisions are
        still made by the deterministic zone event motor.
        """
        seed = (base_text or "").strip()
        if not seed:
            return seed

        lang = self.normalize_language(language)
        persona_key = self.normalize_persona(persona)
        style = (coaching_style or "normal").strip().lower()
        if style not in {"minimal", "normal", "motivational"}:
            style = "normal"

        max_words = max(6, int(getattr(config, "ZONE_EVENT_LLM_REWRITE_MAX_WORDS", 16)))
        max_chars = max(60, int(getattr(config, "ZONE_EVENT_LLM_REWRITE_MAX_CHARS", 120)))

        if lang == "no":
            system_prompt = (
                "Du omskriver en løpecoach-setning på norsk. "
                "Behold NØYAKTIG samme handling og mening. "
                "Ikke legg til nye instruksjoner, tall eller soner. "
                "Maks én kort setning."
            )
            user_prompt = (
                f"Event: {event_type or 'zone_event'}\n"
                f"Persona: {persona_key}\n"
                f"Style: {style}\n"
                f"Original: {seed}\n"
                "Omskriv med samme betydning:"
            )
        else:
            system_prompt = (
                "You rewrite running-coach cues in English. "
                "Keep the EXACT same action and meaning. "
                "Do not add new instructions, numbers, or zones. "
                "Output one short sentence only."
            )
            user_prompt = (
                f"Event: {event_type or 'zone_event'}\n"
                f"Persona: {persona_key}\n"
                f"Style: {style}\n"
                f"Original: {seed}\n"
                "Rewrite with identical meaning:"
            )

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=48,
            temperature=0.35,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=self._timeout_for_mode("realtime_coach"),
        )

        rewritten = (response.choices[0].message.content or "").strip()
        if not rewritten:
            return seed

        rewritten = re.sub(r"\s+", " ", rewritten).strip()
        sentence_split = re.split(r"(?<=[.!?])\s+", rewritten)
        rewritten = sentence_split[0].strip() if sentence_split else rewritten

        if len(rewritten) > max_chars:
            rewritten = rewritten[:max_chars].rstrip(" ,;:-")

        words = rewritten.split()
        if len(words) > max_words:
            rewritten = " ".join(words[:max_words]).rstrip(" ,;:-")
            if not rewritten.endswith((".", "!", "?")):
                rewritten += "."

        # Guard against empty/degenerate output after trimming.
        if len(rewritten) < 4:
            return seed
        return rewritten

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
                stream=True,
                timeout=kwargs.get("timeout", self._timeout_for_mode("chat")),
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
                max_tokens=kwargs.get("max_tokens", 2048),
                timeout=kwargs.get("timeout", self._timeout_for_mode("chat")),
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
                messages=[{"role": "user", "content": "test"}],
                timeout=min(2.5, self._timeout_for_mode("chat")),
            )
            return True
        except Exception:
            return False
