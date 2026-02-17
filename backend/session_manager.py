#
# session_manager.py
# Manages conversation sessions and message history
#

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json


@dataclass
class EmotionalState:
    """
    Tracks emotional progression throughout a workout session.

    This is the key to persona drift - the same persona behaves differently
    at emotional_intensity 0.2 vs 0.8.

    Signals flow: Breath → Struggle → Emotional Intensity → Persona Expression
    """
    intensity: float = 0.2  # 0.0-1.0, starts low (escalation must be earned)
    trend: str = "stable"   # rising | stable | falling
    time_in_struggle: float = 0.0  # seconds struggling in current phase
    consecutive_struggles: int = 0  # consecutive ticks of struggle
    last_update: str = ""  # ISO timestamp

    # Escalation tuning
    ESCALATION_RATE: float = 0.05  # per struggle tick
    DECAY_RATE: float = 0.02  # per optimal tick
    SILENCE_DECAY: float = 0.95  # multiplier when coach is silent

    def update(
        self,
        is_struggling: bool,
        coach_was_silent: bool,
        training_level: str = "intermediate",
        near_phase_end: bool = False
    ) -> None:
        """
        Update emotional state based on current breath analysis.

        Args:
            is_struggling: True if breathing doesn't match phase target
            coach_was_silent: True if coach didn't speak this tick
            training_level: beginner/intermediate/advanced
            near_phase_end: True if within 30s of phase transition
        """
        self.last_update = datetime.now().isoformat()

        # Training level guardrails:
        # - beginner: slightly slower escalation (safety margin)
        # - intermediate/advanced: same escalation profile (consistent personality)
        level_multiplier = {
            "beginner": 0.85,
            "intermediate": 1.0,
            "advanced": 1.0
        }.get(training_level, 1.0)

        # Near phase end = faster escalation (urgency)
        if near_phase_end:
            level_multiplier *= 1.2

        old_intensity = self.intensity

        if is_struggling:
            self.consecutive_struggles += 1
            self.time_in_struggle += 8.0  # Assume 8s ticks

            # Escalate intensity
            escalation = self.ESCALATION_RATE * level_multiplier

            # Compound escalation for prolonged struggle
            if self.consecutive_struggles > 3:
                escalation *= 1.5
            if self.consecutive_struggles > 6:
                escalation *= 2.0

            self.intensity = min(1.0, self.intensity + escalation)
        else:
            # Reset struggle tracking
            self.consecutive_struggles = 0
            self.time_in_struggle = max(0, self.time_in_struggle - 8.0)

            # Decay intensity (recovery)
            self.intensity = max(0.1, self.intensity - self.DECAY_RATE)

        # Silence accelerates decay (calm begets calm)
        if coach_was_silent:
            self.intensity *= self.SILENCE_DECAY
            self.intensity = max(0.1, self.intensity)

        # Update trend
        delta = self.intensity - old_intensity
        if delta > 0.02:
            self.trend = "rising"
        elif delta < -0.02:
            self.trend = "falling"
        else:
            self.trend = "stable"

    def get_persona_mode(self) -> str:
        """
        Map emotional intensity to persona mode.

        This is the bridge between internal state and external expression.
        """
        if self.intensity < 0.3:
            return "supportive"
        elif self.intensity < 0.5:
            return "pressing"
        elif self.intensity < 0.75:
            return "intense"
        else:
            return "peak"

    def should_safety_override(self) -> bool:
        """
        Check if intensity is high enough to warrant safety check.

        At very high emotional intensity, all personas should soften
        to avoid pushing someone into actual distress.
        """
        return self.intensity >= 0.95

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalState":
        """Create from dictionary."""
        if not data:
            return cls()
        # Filter out class constants
        valid_fields = {"intensity", "trend", "time_in_struggle",
                       "consecutive_struggles", "last_update"}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class SessionManager:
    """
    Manages conversation sessions and memory.

    Responsibilities:
    - Create/delete sessions
    - Store message history
    - Apply personas
    - Manage context windows
    """

    def __init__(self, storage_backend="memory"):
        """
        Initialize session manager.

        Args:
            storage_backend: "memory" (default), "redis", or "postgres"
        """
        # For MVP: in-memory storage
        # For production: Use Redis or PostgreSQL
        self.sessions: Dict[str, Dict] = {}
        self.storage_backend = storage_backend

    def create_session(
        self,
        user_id: str,
        persona: str = "personal_trainer",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new conversation session.

        Args:
            user_id: User identifier
            persona: Persona to use (personal_trainer, toxic_mode)
            metadata: Optional session metadata

        Returns:
            session_id: Unique session identifier
        """
        timestamp = int(datetime.now().timestamp())
        session_id = f"session_{user_id}_{timestamp}"

        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "persona": persona,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        print(f"✅ Created session: {session_id} (persona: {persona})")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        return self.sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.sessions

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """
        Add message to session history.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.sessions[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history in AI format.

        Args:
            session_id: Session identifier
            limit: Max number of messages (from end)

        Returns:
            List of messages: [{"role": "user", "content": "..."}, ...]
        """
        if session_id not in self.sessions:
            return []

        messages = self.sessions[session_id]["messages"]

        if limit:
            messages = messages[-limit:]

        # Return in format AI expects
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def get_persona(self, session_id: str) -> str:
        """Get session persona."""
        if session_id not in self.sessions:
            return "personal_trainer"  # Default
        return self.sessions[session_id].get("persona", "personal_trainer")

    def set_persona(self, session_id: str, persona: str):
        """Change session persona."""
        if session_id in self.sessions:
            self.sessions[session_id]["persona"] = persona
            self.sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def delete_session(self, session_id: str):
        """Delete session and all messages."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"🗑️  Deleted session: {session_id}")

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all sessions.

        Args:
            user_id: Filter by user_id (optional)

        Returns:
            List of session summaries
        """
        sessions = []
        for session_id, session in self.sessions.items():
            if user_id and session["user_id"] != user_id:
                continue

            sessions.append({
                "session_id": session_id,
                "user_id": session["user_id"],
                "persona": session["persona"],
                "message_count": len(session["messages"]),
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            })

        return sessions

    def clear_messages(self, session_id: str):
        """Clear all messages from session but keep session."""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"] = []
            self.sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def export_session(self, session_id: str) -> str:
        """Export session as JSON."""
        if session_id not in self.sessions:
            return "{}"
        return json.dumps(self.sessions[session_id], indent=2)

    # ============================================
    # CONTINUOUS COACHING STATE MANAGEMENT
    # ============================================

    def init_workout_state(self, session_id: str, phase: str = "warmup", training_level: str = "intermediate"):
        """
        Initialize workout state tracking for continuous coaching.

        Args:
            session_id: Session identifier
            phase: Starting phase ("warmup", "intense", "cooldown")
            training_level: User's training level for emotional escalation tuning
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.sessions[session_id]["workout_state"] = {
            "current_phase": phase,
            "breath_history": [],
            "coaching_history": [],
            "last_coaching_time": None,
            "last_pattern_time": None,  # STEP 4: Track when last pattern insight was given
            "elapsed_seconds": 0,
            "workout_start": datetime.now().isoformat(),
            "training_level": training_level,
            # Emotional progression state
            "emotional_state": EmotionalState().to_dict()
        }

    def update_workout_state(
        self,
        session_id: str,
        breath_analysis: Optional[Dict] = None,
        coaching_output: Optional[str] = None,
        phase: Optional[str] = None,
        elapsed_seconds: Optional[int] = None
    ):
        """
        Update workout state with latest breath analysis and coaching.

        Args:
            session_id: Session identifier
            breath_analysis: Latest breath metrics
            coaching_output: Latest coaching message (if spoken)
            phase: Updated workout phase
            elapsed_seconds: Total workout time
        """
        if session_id not in self.sessions:
            return

        # Initialize if not exists
        if "workout_state" not in self.sessions[session_id]:
            self.init_workout_state(session_id)

        workout_state = self.sessions[session_id]["workout_state"]

        # Update breath history
        if breath_analysis:
            workout_state["breath_history"].append({
                "timestamp": datetime.now().isoformat(),
                "intensity": breath_analysis.get("intensity", "unknown"),
                "intensity_score": breath_analysis.get("intensity_score"),
                "intensity_confidence": breath_analysis.get("intensity_confidence"),
                "tempo": breath_analysis.get("tempo", 0),
                "respiratory_rate": breath_analysis.get("respiratory_rate"),
                "volume": breath_analysis.get("volume", 0),
                "silence": breath_analysis.get("silence", 0),
                "breath_regularity": breath_analysis.get("breath_regularity"),
                "inhale_exhale_ratio": breath_analysis.get("inhale_exhale_ratio"),
                "signal_quality": breath_analysis.get("signal_quality"),
                "dominant_frequency": breath_analysis.get("dominant_frequency"),
                "interval_state": breath_analysis.get("interval_state"),
                "interval_zone": breath_analysis.get("interval_zone")
            })

            # Keep only last 10 breath analyses
            if len(workout_state["breath_history"]) > 10:
                workout_state["breath_history"] = workout_state["breath_history"][-10:]

        # Update coaching history
        if coaching_output:
            workout_state["coaching_history"].append({
                "timestamp": datetime.now().isoformat(),
                "text": coaching_output
            })
            workout_state["last_coaching_time"] = datetime.now().isoformat()

            # Keep only last 10 coaching messages
            if len(workout_state["coaching_history"]) > 10:
                workout_state["coaching_history"] = workout_state["coaching_history"][-10:]

        # Update phase
        if phase:
            workout_state["current_phase"] = phase

        # Update elapsed time
        if elapsed_seconds is not None:
            workout_state["elapsed_seconds"] = elapsed_seconds

        # Update emotional state based on breath analysis
        if breath_analysis:
            self._update_emotional_state(session_id, breath_analysis, coaching_output is None)

        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def _update_emotional_state(
        self,
        session_id: str,
        breath_analysis: Dict,
        coach_was_silent: bool
    ):
        """
        Update emotional state based on breath analysis.

        Determines if user is struggling based on phase-intensity mismatch.
        """
        workout_state = self.sessions[session_id].get("workout_state", {})

        # Get or create emotional state
        emotional_data = workout_state.get("emotional_state", {})
        emotional_state = EmotionalState.from_dict(emotional_data)

        # Determine if struggling (phase-intensity mismatch)
        current_phase = workout_state.get("current_phase", "warmup")
        intensity = breath_analysis.get("intensity", "moderate")

        is_struggling = self._is_struggling(current_phase, intensity)

        # Check if near phase end (last 30 seconds of phase)
        elapsed = workout_state.get("elapsed_seconds", 0)
        near_phase_end = self._is_near_phase_end(current_phase, elapsed)

        # Get training level
        training_level = workout_state.get("training_level", "intermediate")

        # Update emotional state
        emotional_state.update(
            is_struggling=is_struggling,
            coach_was_silent=coach_was_silent,
            training_level=training_level,
            near_phase_end=near_phase_end
        )

        # Persist updated state
        workout_state["emotional_state"] = emotional_state.to_dict()

    def _is_struggling(self, phase: str, intensity: str) -> bool:
        """
        Determine if user is struggling based on phase-intensity mismatch.

        Struggling means breathing doesn't match what the phase requires:
        - Warmup: should be calm/moderate, struggling if intense/critical
        - Intense: should be intense, struggling if calm (not pushing)
        - Cooldown: should be calm, struggling if still intense
        """
        if phase == "warmup":
            return intensity in ["intense", "critical"]
        elif phase == "intense":
            return intensity == "calm"  # Not pushing hard enough
        elif phase == "cooldown":
            return intensity in ["intense", "critical"]  # Not recovering
        return False

    def _is_near_phase_end(self, phase: str, elapsed_seconds: int) -> bool:
        """Check if we're in the last 30 seconds of a phase."""
        # Phase durations (approximate)
        phase_ends = {
            "warmup": 120,    # 2 minutes
            "intense": 900,   # 15 minutes
            "cooldown": 1200  # 20 minutes total
        }
        phase_end = phase_ends.get(phase, 900)
        return (phase_end - elapsed_seconds) <= 30 and (phase_end - elapsed_seconds) > 0

    def get_workout_state(self, session_id: str) -> Optional[Dict]:
        """
        Get current workout state for continuous coaching context.

        Returns:
            Workout state dict or None if not found
        """
        if session_id not in self.sessions:
            return None

        return self.sessions[session_id].get("workout_state")

    def get_coaching_context(self, session_id: str) -> Dict:
        """
        Get coaching context for intelligence decisions.

        Returns:
            Dict with breath_history, coaching_history, and metadata
        """
        workout_state = self.get_workout_state(session_id)

        if not workout_state:
            return {
                "breath_history": [],
                "coaching_history": [],
                "last_coaching_time": None,
                "phase": "warmup",
                "elapsed_seconds": 0
            }

        return {
            "breath_history": workout_state.get("breath_history", []),
            "coaching_history": workout_state.get("coaching_history", []),
            "last_coaching_time": workout_state.get("last_coaching_time"),
            "phase": workout_state.get("current_phase", "warmup"),
            "elapsed_seconds": workout_state.get("elapsed_seconds", 0)
        }

    def get_last_breath_analysis(self, session_id: str) -> Optional[Dict]:
        """Get the most recent breath analysis from workout state."""
        workout_state = self.get_workout_state(session_id)

        if not workout_state or not workout_state.get("breath_history"):
            return None

        return workout_state["breath_history"][-1]

    def get_emotional_state(self, session_id: str) -> EmotionalState:
        """
        Get current emotional state for a session.

        Returns:
            EmotionalState object (default if not found)
        """
        workout_state = self.get_workout_state(session_id)

        if not workout_state:
            return EmotionalState()

        emotional_data = workout_state.get("emotional_state", {})
        return EmotionalState.from_dict(emotional_data)

    def get_persona_mode(self, session_id: str) -> str:
        """
        Get the current persona mode based on emotional state.

        Returns:
            One of: "supportive", "pressing", "intense", "peak"
        """
        emotional_state = self.get_emotional_state(session_id)
        return emotional_state.get_persona_mode()

    def get_coaching_context_with_emotion(self, session_id: str) -> Dict:
        """
        Get full coaching context including emotional state.

        This is the primary method for coaching intelligence to use.

        Returns:
            Dict with breath_history, coaching_history, emotional state, and metadata
        """
        base_context = self.get_coaching_context(session_id)
        emotional_state = self.get_emotional_state(session_id)

        return {
            **base_context,
            "emotional_intensity": emotional_state.intensity,
            "emotional_trend": emotional_state.trend,
            "persona_mode": emotional_state.get_persona_mode(),
            "time_in_struggle": emotional_state.time_in_struggle,
            "safety_override": emotional_state.should_safety_override()
        }
