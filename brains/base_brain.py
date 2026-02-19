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

    @staticmethod
    def normalize_persona(persona: Optional[str]) -> str:
        """Normalize persona identifier to known runtime personas."""
        value = (persona or "personal_trainer").strip().lower()
        if value not in {"personal_trainer", "toxic_mode"}:
            return "personal_trainer"
        return value

    def extract_language(self, breath_data: Dict[str, Any]) -> str:
        """Read language from breath payload with safe normalization."""
        return self.normalize_language(breath_data.get("language"))

    def extract_intensity(self, breath_data: Dict[str, Any]) -> str:
        """Read intensity from both new and legacy payload keys."""
        raw = breath_data.get("intensity", breath_data.get("intensitet"))
        return self.normalize_intensity(raw)

    def build_persona_directives(
        self,
        breath_data: Dict[str, Any],
        language: str,
        mode: str = "realtime_coach",
    ) -> str:
        """
        Build compact persona directives so model outputs stay in-character.

        Covers role, character, humor style, and safety boundaries.
        """
        lang = self.normalize_language(language)
        persona = self.normalize_persona(breath_data.get("persona"))
        realtime = mode == "realtime_coach"
        emotional_mode = (breath_data.get("persona_mode") or "").strip().lower()
        emotional_trend = (breath_data.get("emotional_trend") or "").strip().lower()
        emotional_intensity = breath_data.get("emotional_intensity")
        safety_override = bool(breath_data.get("safety_override"))

        if emotional_mode not in {"supportive", "pressing", "intense", "peak"}:
            emotional_mode = self._infer_emotional_mode(emotional_intensity)

        if lang == "no":
            if persona == "toxic_mode":
                lines = [
                    "Persona/rolle: toxic_mode (hard drillsersjant).",
                    "Karakter: konfronterende, energisk, mørk humor.",
                    "Humor: sarkasme og lett roasting, aldri personangrep.",
                    "Sikkerhet: slipp akten umiddelbart ved kritisk pust.",
                ]
                if realtime:
                    lines.append("Stil nå: korte, slagkraftige kommandoer, moderat CAPS.")
            else:
                lines = [
                    "Persona/rolle: personal_trainer (rolig elitecoach).",
                    "Karakter: disiplinert, konstruktiv, jordnær.",
                    "Humor: lett og sjelden, aldri sarkasme.",
                    "Sikkerhet: prioriter kontroll og trygg progresjon.",
                    "Metode: prosess-først (møt opp, gjennomfør, restituer, gjenta).",
                    "Stilregel: bruk eksempler som referanse, ikke fast manus.",
                    "Stilregel: lag av og til nye korte formuleringer, uten å gjenta samme cue på rad.",
                ]
                if realtime:
                    lines.append("Stil nå: korte, tydelige og handlingsrettede cues (typisk 2-8 ord, maks én setning).")

            if safety_override:
                lines.append("Emosjonell segment: SAFETY override aktiv, bruk støttende modus nå.")
            elif emotional_mode:
                lines.append(f"Emosjonell segment: modus={emotional_mode}.")

            if emotional_trend in {"rising", "falling", "stable"}:
                trend_map = {"rising": "stigende", "falling": "fallende", "stable": "stabil"}
                lines.append(f"Trend: {trend_map.get(emotional_trend, emotional_trend)}.")
        else:
            if persona == "toxic_mode":
                lines = [
                    "Persona role: toxic_mode drill-sergeant coach.",
                    "Character: confrontational, high-energy, darkly humorous.",
                    "Humor: sarcasm/playful roasting, never personal attacks.",
                    "Safety: drop the act immediately on critical breathing.",
                ]
                if realtime:
                    lines.append("Style now: short punchy commands, occasional ALL CAPS.")
            else:
                lines = [
                    "Persona role: personal_trainer elite endurance coach.",
                    "Character: calm, disciplined, constructive, grounded.",
                    "Humor: light and rare, never sarcastic.",
                    "Safety: prioritize control and sustainable effort.",
                    "Method: process-first coaching (show up, execute, recover, repeat).",
                    "Style rule: treat examples as references, not fixed scripts.",
                    "Style rule: occasionally generate fresh short phrasing; avoid repeating identical cues back-to-back.",
                ]
                if realtime:
                    lines.append("Style now: short direct actionable cues (typically 2-8 words, max one sentence).")

            if safety_override:
                lines.append("Emotional segment: SAFETY override active, force supportive mode now.")
            elif emotional_mode:
                lines.append(f"Emotional segment: mode={emotional_mode}.")

            if emotional_trend in {"rising", "falling", "stable"}:
                lines.append(f"Trend: {emotional_trend}.")

            if isinstance(emotional_intensity, (int, float)):
                lines.append(f"Emotional intensity: {float(emotional_intensity):.2f}.")

        return "\n\nPersona directives:\n- " + "\n- ".join(lines)

    @staticmethod
    def _infer_emotional_mode(emotional_intensity: Any) -> str:
        """Infer persona mode from emotional intensity if explicit mode is missing."""
        try:
            value = float(emotional_intensity)
        except (TypeError, ValueError):
            return "supportive"

        if value < 0.3:
            return "supportive"
        if value < 0.5:
            return "pressing"
        if value < 0.75:
            return "intense"
        return "peak"

    @staticmethod
    def localized_keep_going(language: str) -> str:
        """Language-safe default fallback cue."""
        return "Fortsett!" if language == "no" else "Keep going!"

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
        Optional provider hook for zone-event phrasing.

        Default behavior is a no-op so deterministic event text remains intact
        when the provider does not support rewrite mode.
        """
        _ = (language, persona, coaching_style, event_type)
        return (base_text or "").strip()

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
