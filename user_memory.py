# user_memory.py
# STEP 5: Memory That Actually Matters
# Minimal, meaningful memory injection

from typing import Dict, Optional
import json
import os
from datetime import datetime

class UserMemory:
    """
    STEP 5: Stores minimal, meaningful user preferences and patterns.

    NOT a full history log. Only stores:
    - Preferred coaching style
    - Safety events (critical breathing patterns)
    - Improvement markers (progression over time)

    Memory is injected ONCE at session start, not every message (keeps it fast).
    """

    def __init__(self, storage_path: str = "user_memories.json"):
        """
        Initialize user memory manager.

        Args:
            storage_path: Path to JSON file storing memories
        """
        self.storage_path = storage_path
        self.memories: Dict[str, Dict] = {}
        self._load_memories()

    def _load_memories(self):
        """Load memories from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.memories = json.load(f)
                print(f"✅ Loaded {len(self.memories)} user memories")
            except Exception as e:
                print(f"⚠️ Failed to load memories: {e}")
                self.memories = {}
        else:
            self.memories = {}

    def _save_memories(self):
        """Save memories to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.memories, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save memories: {e}")

    def get_memory(self, user_id: str) -> Dict:
        """
        Get memory for a user.

        Returns minimal, meaningful context:
        {
            "user_prefers": "calm coaching" | "assertive coaching" | "balanced",
            "tends_to_overbreathe": true | false,
            "last_critical_event": "2024-01-28" | "none",
            "improvement_trend": "improving" | "stable" | "declining" | "new_user",
            "total_workouts": 5,
            "last_workout": "2024-01-28T10:00:00"
        }

        Args:
            user_id: User identifier

        Returns:
            Memory dict (empty if new user)
        """
        if user_id not in self.memories:
            # New user - return defaults
            return {
                "user_prefers": "balanced",
                "tends_to_overbreathe": False,
                "last_critical_event": "none",
                "improvement_trend": "new_user",
                "total_workouts": 0,
                "last_workout": None
            }

        return self.memories[user_id]

    def update_memory(
        self,
        user_id: str,
        coaching_style_preference: Optional[str] = None,
        critical_event: Optional[bool] = None,
        overbreathe_detected: Optional[bool] = None,
        improvement_marker: Optional[str] = None
    ):
        """
        Update user memory with new observations.

        STEP 5: Only update meaningful patterns, not every data point.

        Args:
            user_id: User identifier
            coaching_style_preference: "calm" | "assertive" | "balanced"
            critical_event: True if kritisk breathing occurred
            overbreathe_detected: True if user tends to overbreathe
            improvement_marker: "improving" | "stable" | "declining"
        """
        if user_id not in self.memories:
            self.memories[user_id] = {
                "user_prefers": "balanced",
                "tends_to_overbreathe": False,
                "last_critical_event": "none",
                "improvement_trend": "new_user",
                "total_workouts": 0,
                "last_workout": None,
                "created_at": datetime.now().isoformat()
            }

        memory = self.memories[user_id]

        # Update coaching style preference
        if coaching_style_preference:
            memory["user_prefers"] = coaching_style_preference

        # Update safety events
        if critical_event:
            memory["last_critical_event"] = datetime.now().strftime("%Y-%m-%d")

        # Update breathing pattern
        if overbreathe_detected is not None:
            memory["tends_to_overbreathe"] = overbreathe_detected

        # Update improvement trend
        if improvement_marker:
            memory["improvement_trend"] = improvement_marker

        # Update workout count
        memory["total_workouts"] += 1
        memory["last_workout"] = datetime.now().isoformat()
        memory["updated_at"] = datetime.now().isoformat()

        self._save_memories()

    def get_memory_summary(self, user_id: str) -> str:
        """
        STEP 5: Get human-readable memory summary for Claude.

        This is injected ONCE at session start, not every message.

        Args:
            user_id: User identifier

        Returns:
            Short memory context string (2-3 sentences)
        """
        memory = self.get_memory(user_id)

        parts = []

        # Coaching style preference
        if memory["user_prefers"] != "balanced":
            parts.append(f"User prefers {memory['user_prefers']} coaching style.")

        # Safety patterns
        if memory["tends_to_overbreathe"]:
            parts.append("User tends to overbreathe - watch for kritisk breathing.")

        # Improvement trend
        if memory["improvement_trend"] != "new_user":
            parts.append(f"Trend: {memory['improvement_trend']}.")

        # Workout count
        if memory["total_workouts"] > 0:
            parts.append(f"Workout #{memory['total_workouts'] + 1}.")

        if not parts:
            return "New user - first workout."

        return " ".join(parts)

    def detect_coaching_preference(
        self,
        session_id: str,
        coaching_history: list
    ) -> Optional[str]:
        """
        STEP 5: Detect user's preferred coaching style from their responses.

        Looks for patterns like:
        - User responds better to calm coaching (fewer kritisk events)
        - User needs assertive coaching (rolig during intense phase)

        Args:
            session_id: Session identifier
            coaching_history: Recent coaching messages

        Returns:
            "calm" | "assertive" | "balanced" | None (if unclear)
        """
        # This is a placeholder for future ML/pattern detection
        # For now, return None (use balanced)
        return None

    def mark_safety_event(self, user_id: str):
        """
        STEP 5: Mark that a critical breathing event occurred.

        Args:
            user_id: User identifier
        """
        self.update_memory(
            user_id=user_id,
            critical_event=True
        )

    def mark_improvement(self, user_id: str, trend: str):
        """
        STEP 5: Mark improvement trend after workout.

        Args:
            user_id: User identifier
            trend: "improving" | "stable" | "declining"
        """
        self.update_memory(
            user_id=user_id,
            improvement_marker=trend
        )
