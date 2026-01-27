#
# session_manager.py
# Manages conversation sessions and message history
#

from typing import Dict, List, Optional
from datetime import datetime
import json


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
        persona: str = "fitness_coach",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new conversation session.

        Args:
            user_id: User identifier
            persona: Persona to use (fitness_coach, calm_coach, etc.)
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
            return "fitness_coach"  # Default
        return self.sessions[session_id].get("persona", "fitness_coach")

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
