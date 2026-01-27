#
# openai_brain.py
# OpenAI brain adapter
#

import os
import random
from typing import Dict, Any, Optional
from openai import OpenAI
from .base_brain import BaseBrain
import config


class OpenAIBrain(BaseBrain):
    """
    OpenAI brain implementation using OpenAI API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI brain with API key."""
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense"
    ) -> str:
        """
        Generate coaching response using OpenAI.

        Uses the configured messages as guidance, but lets GPT add personality.
        """
        intensitet = breath_data.get("intensitet", "moderat")

        # For critical situations, use config message directly
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        # Build context for OpenAI
        system_prompt = self._build_system_prompt(phase, intensitet)
        user_message = self._build_user_message(breath_data, phase)

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

    def _build_system_prompt(self, phase: str, intensitet: str) -> str:
        """Build system prompt for OpenAI based on phase and intensity."""
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

    def _build_user_message(self, breath_data: Dict[str, Any], phase: str) -> str:
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
