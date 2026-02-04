"""
Strategic Brain - High-level coaching intelligence layer

This module provides Claude-powered strategic coaching decisions that sit above
the tactical coaching intelligence. It's called occasionally (not every breath)
to provide higher-level insights, session reflection, and adaptive guidance.

Architecture:
    Coaching Intelligence (tactical) → Strategic Brain (strategic) → Messages
    
Frequency: 
    - Every 2-3 minutes during workout
    - At session start/end
    - When patterns indicate need for strategic shift
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class StrategicBrain:
    """
    Claude-powered strategic coaching layer.
    Provides high-level guidance and session insights.

    Cost optimization:
    - Uses Haiku by default (10x cheaper)
    - Haiku escalates to Sonnet when needed
    - Caches identical contexts
    - Hard token limits
    """

    def __init__(self):
        """Initialize Strategic Brain with Claude API"""
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        # Cache for strategic guidance (avoid redundant calls)
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
                logger.info("✅ Strategic Brain initialized with Claude")
            except Exception as e:
                logger.warning(f"⚠️ Strategic Brain failed to initialize: {e}")
                self.client = None
        else:
            logger.warning("⚠️ Strategic Brain disabled (no ANTHROPIC_API_KEY)")
    
    def is_available(self) -> bool:
        """Check if Strategic Brain is available"""
        return self.client is not None
    
    def should_provide_insight(
        self,
        elapsed_seconds: int,
        last_strategic_time: Optional[int] = None,
        phase: str = "warmup"
    ) -> bool:
        """
        Determine if it's time for strategic insight.
        
        Args:
            elapsed_seconds: Time since workout start
            last_strategic_time: Last time strategic insight was given
            phase: Current workout phase
            
        Returns:
            True if strategic insight should be provided
        """
        if not self.is_available():
            return False
        
        # First insight at 2 minutes
        if elapsed_seconds >= 120 and (last_strategic_time is None or last_strategic_time == 0):
            return True
        
        # Subsequent insights every 3 minutes
        if last_strategic_time is not None:
            time_since_last = elapsed_seconds - last_strategic_time
            if time_since_last >= 180:  # 3 minutes
                return True
        
        return False
    
    def get_strategic_insight(
        self,
        breath_history: List[Dict],
        coaching_history: List[str],
        phase: str,
        elapsed_seconds: int,
        session_context: Optional[Dict] = None,
        language: str = "en"
    ) -> Optional[Dict]:
        """
        Generate strategic coaching insight based on session context.

        This is the main entry point for strategic decisions.
        Returns GUIDANCE, not raw speech - the system decides what to say.

        Cost optimizations:
        - Checks cache first (80% hit rate potential)
        - Uses Haiku by default (10x cheaper)
        - Haiku escalates to Sonnet when needed
        - Hard token limit (60 max)

        Args:
            breath_history: Recent breath analyses
            coaching_history: Recent coaching messages
            phase: Current workout phase
            elapsed_seconds: Time since workout start
            session_context: Additional session data

        Returns:
            Strategic guidance dict with: strategy, tone, message_goal, suggested_phrase
            Or None if not needed
        """
        if not self.is_available():
            return None

        try:
            # Build context summary
            context_key = self._build_cache_key(
                breath_history=breath_history,
                phase=phase,
                elapsed_seconds=elapsed_seconds
            )

            # Check cache first (avoid redundant API calls)
            if context_key in self._cache:
                self._cache_hits += 1
                logger.info(f"💾 Cache hit! (hits: {self._cache_hits}, misses: {self._cache_misses})")
                return self._cache[context_key]

            self._cache_misses += 1

            # Prepare context for Claude
            prompt = self._build_strategic_prompt(
                breath_history=breath_history,
                coaching_history=coaching_history,
                phase=phase,
                elapsed_seconds=elapsed_seconds,
                session_context=session_context
            )

            # Try Haiku first (10x cheaper)
            logger.info("🧠 Requesting strategic guidance from Haiku...")

            haiku_response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=60,  # Hard limit for cost control
                temperature=0.7,
                system=self._get_system_prompt(language=language),
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = haiku_response.content[0].text.strip()

            # Check if Haiku wants to escalate
            if "ESCALATE" in response_text:
                logger.info("⬆️ Haiku escalating to Sonnet...")

                sonnet_response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=60,  # Hard limit
                    temperature=0.7,
                    system=self._get_system_prompt(language=language),
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                response_text = sonnet_response.content[0].text.strip()

            # Parse Claude's response into structured guidance
            guidance = self._parse_strategic_response(response_text)
            logger.info(f"✅ Strategic guidance: {guidance}")

            # Cache the result
            self._cache[context_key] = guidance

            # Limit cache size (keep last 20 entries)
            if len(self._cache) > 20:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            return guidance

        except Exception as e:
            logger.error(f"Strategic Brain error: {e}")
            return None

    def _parse_strategic_response(self, response: str) -> Dict:
        """
        Parse Claude's response into structured guidance.

        Claude returns guidance like:
        "Strategy: reduce_overload | Tone: calm_firm | Goal: restore_rhythm | Phrase: Control the exhale."

        Returns dict with: strategy, tone, message_goal, suggested_phrase
        """
        try:
            # Try to parse structured format first
            parts = response.split("|")
            if len(parts) >= 4:
                guidance = {}
                for part in parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        key = key.strip().lower().replace(" ", "_")
                        value = value.strip()

                        # Map keys to expected format
                        if "strategy" in key:
                            guidance["strategy"] = value
                        elif "tone" in key:
                            guidance["tone"] = value
                        elif "goal" in key or "message" in key:
                            guidance["message_goal"] = value
                        elif "phrase" in key or "suggestion" in key:
                            guidance["suggested_phrase"] = value

                return guidance
        except:
            pass

        # Fallback: treat entire response as suggested phrase
        return {
            "strategy": "tactical_adjustment",
            "tone": "calm_firm",
            "message_goal": "guidance",
            "suggested_phrase": response
        }
    
    def _get_system_prompt(self, language: str = "en") -> str:
        """
        System prompt defining Strategic Brain's role and style.
        Supports language selection for Norwegian coaching phrases.
        """
        base = """You are a coaching intelligence module.
You must be concise.
You must not explain your reasoning.
Do not repeat the input.
Do not add commentary.
Respond with only the requested output format.
Use short sentences.
No filler.

Task: Generate strategic coaching guidance.

If this task requires deeper reasoning than you can provide, return: ESCALATE

Otherwise, output format:
Strategy: [reduce_overload|maintain_pace|push_intensity|restore_rhythm]
Tone: [calm_firm|authoritative|encouraging|warning]
Goal: [slow_down|stabilize|maintain|intensity_check]
Phrase: [optional - max 15 words]

Constraints:
- Max 40 words total
- No questions
- No metaphors
- Calm, authoritative tone
- Return only the requested format
"""
        if language == "no":
            base += "\nIMPORTANT: The Phrase MUST be in Norwegian (Bokmal). Short, direct coaching."
        return base
    
    def _build_cache_key(
        self,
        breath_history: List[Dict],
        phase: str,
        elapsed_seconds: int
    ) -> str:
        """
        Build cache key from session state.

        Same state = same guidance = cache hit = $0.

        Key factors:
        - Phase
        - Breath trend (stable/erratic/variable)
        - Intensity pattern
        """
        if not breath_history:
            return f"{phase}_calm"

        recent_breaths = breath_history[-5:]
        intensities = [b.get("intensity", "moderate") for b in recent_breaths]

        # Classify breath trend
        if len(set(intensities)) <= 2:
            trend = "stable"
        elif len(set(intensities)) >= 4:
            trend = "erratic"
        else:
            trend = "variable"

        # Most common intensity
        intensity = max(set(intensities), key=intensities.count)

        return f"{phase}_{trend}_{intensity}"

    def _build_strategic_prompt(
        self,
        breath_history: List[Dict],
        coaching_history: List[str],
        phase: str,
        elapsed_seconds: int,
        session_context: Optional[Dict] = None
    ) -> str:
        """
        Build the prompt for Claude with session context.

        AGGREGATES ONLY. No raw data. No breath-by-breath samples.
        """
        # Calculate session statistics
        minutes = elapsed_seconds // 60

        # Breath pattern summary (AGGREGATED, not raw)
        if breath_history:
            recent_breaths = breath_history[-10:]
            avg_tempo = sum(b.get("tempo", 60) for b in recent_breaths) / len(recent_breaths)
            intensities = [b.get("intensity", "moderate") for b in recent_breaths]

            # Calculate struggle duration
            struggle_count = 0
            for b in reversed(recent_breaths):
                intensity = b.get("intensity", "moderate")
                if (phase == "warmup" and intensity == "intense") or \
                   (phase == "intense" and intensity == "calm"):
                    struggle_count += 1
                else:
                    break
            duration_struggling = struggle_count * 8
        else:
            avg_tempo = 60
            intensities = ["moderate"]
            duration_struggling = 0

        # Determine breath trend
        if len(set(intensities[-5:])) <= 2:
            breath_trend = "stable"
        elif len(set(intensities[-5:])) >= 4:
            breath_trend = "erratic"
        else:
            breath_trend = "variable"

        # Last coaching (max 2 messages)
        recent_coaching = coaching_history[-2:] if coaching_history else []

        # Ultra-concise prompt
        prompt = f"""Phase: {phase}
Min: {minutes}
Trend: {breath_trend}
Tempo: {avg_tempo:.0f}
Struggling: {duration_struggling}s
Last coaching: {', '.join(recent_coaching) if recent_coaching else 'None'}

Provide guidance."""

        return prompt
    
    def session_summary(
        self,
        breath_history: List[Dict],
        coaching_history: List[str],
        total_time: int,
        phase: str
    ) -> Optional[str]:
        """
        Generate end-of-session summary.

        Called when workout ends for reflection.

        Args:
            breath_history: Full workout breath data
            coaching_history: All coaching given
            total_time: Total workout duration
            phase: Final phase

        Returns:
            Summary message or None
        """
        if not self.is_available():
            return None

        try:
            minutes = total_time // 60

            prompt = f"""Duration: {minutes}m
Phase: {phase}
Interventions: {len([c for c in coaching_history if c])}

Closing statement. Max 12 words."""

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Haiku for summaries
                max_tokens=30,  # Hard limit
                temperature=0.7,
                system="You are a coaching intelligence module. Be concise. No explanations. Calm, authoritative tone. Max 12 words.",
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()

        except Exception as e:
            logger.error(f"Session summary error: {e}")
            return None
    
    def calibrate_motivation(
        self,
        breath_history: List[Dict],
        phase: str
    ) -> str:
        """
        Determine current motivation level needed.
        
        Returns: "calm", "moderate", or "intense"
        """
        if not breath_history:
            return "calm"
        
        recent = breath_history[-5:]
        intensities = [b.get("intensity", "moderate") for b in recent]
        
        # If mostly calm/moderate in intense phase → need push
        if phase == "intense" and intensities.count("calm") > 2:
            return "intense"
        
        # If mostly intense in warmup → need calm
        if phase == "warmup" and intensities.count("intense") > 2:
            return "calm"
        
        return "moderate"


# Singleton instance
_strategic_brain = None

def get_strategic_brain() -> StrategicBrain:
    """Get or create Strategic Brain singleton"""
    global _strategic_brain
    if _strategic_brain is None:
        _strategic_brain = StrategicBrain()
    return _strategic_brain


if __name__ == "__main__":
    # Test Strategic Brain
    brain = StrategicBrain()
    
    if brain.is_available():
        print("✅ Strategic Brain is available")
        
        # Test insight generation
        test_breath = [
            {"tempo": 65, "intensity": "moderate"},
            {"tempo": 68, "intensity": "moderate"},
            {"tempo": 72, "intensity": "intense"},
        ]
        
        insight = brain.get_strategic_insight(
            breath_history=test_breath,
            coaching_history=["Push harder", "Good pace"],
            phase="intense",
            elapsed_seconds=180
        )
        
        if insight:
            print(f"Strategic insight: {insight}")
    else:
        print("⚠️ Strategic Brain not available (set ANTHROPIC_API_KEY)")
