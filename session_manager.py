#
# session_manager.py
# Manages conversation sessions and message history
#

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json

from flask import has_app_context

from breathing_timeline import BreathingTimeline


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

    def __init__(self, storage_backend="memory", app=None):
        """
        Initialize session manager.

        Args:
            storage_backend: "memory" (default) or "database"
            app: Optional Flask app used to resolve a DB engine outside request/app context
        """
        self.sessions: Dict[str, Dict] = {}
        normalized_backend = str(storage_backend or "memory").strip().lower()
        self.storage_backend = normalized_backend if normalized_backend in {"memory", "database"} else "memory"
        self.app = app
        self._database_storage_disabled_reason: Optional[str] = None
        self._database_runtime_table_verified = False

    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def _uses_database_storage(self) -> bool:
        return self.storage_backend == "database" and self._database_storage_disabled_reason is None

    @staticmethod
    def _missing_runtime_table_reason() -> str:
        return "runtime_session_states_missing"

    @staticmethod
    def _is_missing_runtime_table_error(error: Exception) -> bool:
        normalized = str(error or "").strip().lower()
        return (
            "runtime_session_states" in normalized
            and any(
                marker in normalized
                for marker in (
                    "does not exist",
                    "undefinedtable",
                    "no such table",
                    "unknown table",
                )
            )
        )

    def _disable_database_storage(self, reason: str, error: Optional[Exception] = None) -> None:
        if self._database_storage_disabled_reason is not None:
            return
        self._database_storage_disabled_reason = reason
        details = ""
        if error is not None:
            details = f" ({type(error).__name__}: {error})"
        print(
            f"⚠️ Runtime session DB storage disabled: {reason}. Falling back to in-memory session state{details}"
        )

    def _database_runtime_table_ready(self) -> bool:
        if not self._uses_database_storage():
            return False

        bind = self._database_bind()
        if bind is None:
            return False

        if self._database_runtime_table_verified:
            return True

        from sqlalchemy import inspect

        try:
            if inspect(bind).has_table("runtime_session_states"):
                self._database_runtime_table_verified = True
                return True
            self._disable_database_storage(self._missing_runtime_table_reason())
            return False
        except Exception as exc:
            if self._is_missing_runtime_table_error(exc):
                self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)
                return False
            return False

    def _database_bind(self):
        if not self._uses_database_storage():
            return None

        from database import db

        def _resolve_bind():
            try:
                return db.session.get_bind()
            except RuntimeError:
                return None

        if has_app_context():
            return _resolve_bind()

        if self.app is None:
            return None

        try:
            with self.app.app_context():
                return _resolve_bind()
        except Exception:
            return None

    @staticmethod
    def _normalize_session_id(session_id: str) -> str:
        return str(session_id or "").strip()

    def _encode_special_types(self, value: Any):
        if isinstance(value, BreathingTimeline):
            return {
                "__type__": "BreathingTimeline",
                "payload": value.to_dict(),
            }
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    def _decode_special_types(self, value: Any):
        if isinstance(value, list):
            return [self._decode_special_types(item) for item in value]
        if isinstance(value, dict):
            marker = str(value.get("__type__") or "").strip()
            if marker == "BreathingTimeline":
                return BreathingTimeline.from_dict(value.get("payload"))
            return {key: self._decode_special_types(item) for key, item in value.items()}
        return value

    def _persist_session_record(self, session_id: str, session: Dict) -> None:
        if not self._database_runtime_table_ready():
            return

        from database import RuntimeSessionState

        normalized_session_id = self._normalize_session_id(session_id)
        if not normalized_session_id:
            return

        now = self._utcnow_naive()
        payload_json = json.dumps(session, default=self._encode_special_types, ensure_ascii=True)
        user_id = str(session.get("user_id") or "").strip() or None
        values = {
            "session_id": normalized_session_id,
            "user_id": user_id,
            "payload_json": payload_json,
            "created_at": now,
            "updated_at": now,
        }
        table = RuntimeSessionState.__table__
        bind = self._database_bind()
        if bind is None:
            return
        dialect_name = bind.dialect.name if bind is not None else ""

        try:
            if dialect_name == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as dialect_insert
            elif dialect_name == "postgresql":
                from sqlalchemy.dialects.postgresql import insert as dialect_insert
            else:
                raise RuntimeError("dialect_fallback")

            stmt = dialect_insert(table).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["session_id"],
                set_={
                    "user_id": user_id,
                    "payload_json": payload_json,
                    "updated_at": now,
                },
            )
            with bind.begin() as connection:
                connection.execute(stmt)
            return
        except Exception as exc:
            if self._is_missing_runtime_table_error(exc):
                self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)
                return
            pass

        try:
            with bind.begin() as connection:
                updated = connection.execute(
                    table.update()
                    .where(table.c.session_id == normalized_session_id)
                    .values(
                        user_id=user_id,
                        payload_json=payload_json,
                        updated_at=now,
                    )
                ).rowcount
                if not updated:
                    connection.execute(table.insert().values(**values))
        except Exception as exc:
            if self._is_missing_runtime_table_error(exc):
                self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)

    def _load_session_record(self, session_id: str) -> Optional[Dict]:
        normalized_session_id = self._normalize_session_id(session_id)
        if not normalized_session_id:
            return None

        if not self._database_runtime_table_ready():
            return self.sessions.get(normalized_session_id)

        from database import RuntimeSessionState
        from sqlalchemy import select

        table = RuntimeSessionState.__table__
        bind = self._database_bind()
        if bind is None:
            return self.sessions.get(normalized_session_id)

        try:
            with bind.connect() as connection:
                row = connection.execute(
                    select(table.c.payload_json).where(table.c.session_id == normalized_session_id)
                ).first()
        except Exception as exc:
            if self._is_missing_runtime_table_error(exc):
                self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)
            return self.sessions.get(normalized_session_id)
        if row is None:
            self.sessions.pop(normalized_session_id, None)
            return None

        try:
            payload = json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            self.sessions.pop(normalized_session_id, None)
            return None

        session = self._decode_special_types(payload)
        if not isinstance(session, dict):
            self.sessions.pop(normalized_session_id, None)
            return None
        self.sessions[normalized_session_id] = session
        return session

    def save_session(self, session_id: str, session: Dict) -> None:
        normalized_session_id = self._normalize_session_id(session_id)
        if not normalized_session_id:
            return
        self.sessions[normalized_session_id] = session
        self._persist_session_record(normalized_session_id, session)

    def save_workout_state(self, session_id: str, workout_state: Optional[Dict]) -> None:
        session = self.get_session(session_id)
        if session is None:
            return
        if workout_state is None:
            session.pop("workout_state", None)
        else:
            session["workout_state"] = workout_state
        session["updated_at"] = datetime.now().isoformat()
        self.save_session(session_id, session)

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

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "persona": persona,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.save_session(session_id, session)

        print(f"✅ Created session: {session_id} (persona: {persona})")
        return session_id

    def get_session(self, session_id: str, *, refresh: bool = False) -> Optional[Dict]:
        """Get session data."""
        normalized_session_id = self._normalize_session_id(session_id)
        if not normalized_session_id:
            return None
        if self._uses_database_storage() and (refresh or normalized_session_id not in self.sessions):
            return self._load_session_record(normalized_session_id)
        return self.sessions.get(normalized_session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return self.get_session(session_id, refresh=self._uses_database_storage()) is not None

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
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        session.setdefault("messages", []).append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session["updated_at"] = datetime.now().isoformat()
        self.save_session(session_id, session)

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
        session = self.get_session(session_id, refresh=self._uses_database_storage())
        if session is None:
            return []

        messages = session.get("messages", [])

        if limit:
            messages = messages[-limit:]

        # Return in format AI expects
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def get_persona(self, session_id: str) -> str:
        """Get session persona."""
        session = self.get_session(session_id, refresh=self._uses_database_storage())
        if session is None:
            return "personal_trainer"  # Default
        return session.get("persona", "personal_trainer")

    def set_persona(self, session_id: str, persona: str):
        """Change session persona."""
        session = self.get_session(session_id)
        if session is not None:
            session["persona"] = persona
            session["updated_at"] = datetime.now().isoformat()
            self.save_session(session_id, session)

    def delete_session(self, session_id: str):
        """Delete session and all messages."""
        normalized_session_id = self._normalize_session_id(session_id)
        if not normalized_session_id:
            return
        self.sessions.pop(normalized_session_id, None)
        if self._database_runtime_table_ready():
            from database import RuntimeSessionState

            table = RuntimeSessionState.__table__
            bind = self._database_bind()
            if bind is None:
                print(f"🗑️  Deleted session: {normalized_session_id}")
                return
            try:
                with bind.begin() as connection:
                    connection.execute(
                        table.delete().where(table.c.session_id == normalized_session_id)
                    )
            except Exception as exc:
                if self._is_missing_runtime_table_error(exc):
                    self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)
        print(f"🗑️  Deleted session: {normalized_session_id}")

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all sessions.

        Args:
            user_id: Filter by user_id (optional)

        Returns:
            List of session summaries
        """
        if not self._database_runtime_table_ready():
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

        from database import RuntimeSessionState
        from sqlalchemy import select

        table = RuntimeSessionState.__table__
        stmt = select(table.c.session_id)
        if user_id:
            stmt = stmt.where(table.c.user_id == user_id)

        bind = self._database_bind()
        if bind is None:
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
        try:
            with bind.connect() as connection:
                session_ids = [row[0] for row in connection.execute(stmt)]
        except Exception as exc:
            if self._is_missing_runtime_table_error(exc):
                self._disable_database_storage(self._missing_runtime_table_reason(), error=exc)
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

        sessions = []
        for session_id in session_ids:
            session = self.get_session(session_id, refresh=True)
            if session is None:
                continue
            sessions.append({
                "session_id": session_id,
                "user_id": session.get("user_id"),
                "persona": session.get("persona", "personal_trainer"),
                "message_count": len(session.get("messages", [])),
                "created_at": session.get("created_at"),
                "updated_at": session.get("updated_at"),
            })
        return sessions

    def clear_messages(self, session_id: str):
        """Clear all messages from session but keep session."""
        session = self.get_session(session_id)
        if session is not None:
            session["messages"] = []
            session["updated_at"] = datetime.now().isoformat()
            self.save_session(session_id, session)

    def export_session(self, session_id: str) -> str:
        """Export session as JSON."""
        session = self.get_session(session_id, refresh=self._uses_database_storage())
        if session is None:
            return "{}"
        return json.dumps(session, default=self._encode_special_types, indent=2)

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
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        session["workout_state"] = {
            "current_phase": phase,
            "breath_history": [],
            "coaching_history": [],
            "last_coaching_time": None,
            "last_pattern_time": None,  # STEP 4: Track when last pattern insight was given
            "elapsed_seconds": 0,
            "workout_start": datetime.now().isoformat(),
            "training_level": training_level,
            # Emotional progression state
            "emotional_state": EmotionalState().to_dict(),
            # Latency-aware response strategy state (per session)
            "latency_strategy": {
                "pending_rich_followup": False,
                "last_fast_fallback_elapsed": -10_000,
                "last_rich_followup_elapsed": -10_000,
                "last_latency_provider": None,
            },
        }
        session["updated_at"] = datetime.now().isoformat()
        self.save_session(session_id, session)

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
        session = self.get_session(session_id)
        if session is None:
            return

        # Initialize if not exists
        if "workout_state" not in session:
            self.init_workout_state(session_id)
            session = self.get_session(session_id)
            if session is None:
                return

        workout_state = session["workout_state"]

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

        session["updated_at"] = datetime.now().isoformat()
        self.save_session(session_id, session)

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
        session = self.get_session(session_id)
        if session is None:
            return
        workout_state = session.get("workout_state", {})

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
        session = self.get_session(session_id, refresh=self._uses_database_storage())
        if session is None:
            return None

        return session.get("workout_state")

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
