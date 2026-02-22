"""Chat + brain control routes extracted from main runtime path."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from flask import Blueprint, Response, jsonify, request, stream_with_context


def create_chat_blueprint(
    *,
    brain_router: Any,
    session_manager: Any,
    persona_manager: Any,
    logger: Any,
) -> Blueprint:
    """Create blueprint for brain control and chat endpoints."""
    chat_bp = Blueprint("chat_routes", __name__)

    @chat_bp.route("/brain/health", methods=["GET"])
    def brain_health():
        """
        Check health of active brain.

        Returns brain status and health information.
        """
        try:
            health = brain_router.health_check()
            logger.info("Brain health check: %s", health)
            return jsonify(health), 200 if health["healthy"] else 503

        except Exception as e:
            logger.error(f"Error checking brain health: {e}", exc_info=True)
            return (
                jsonify(
                    {
                        "active_brain": "unknown",
                        "healthy": False,
                        "message": str(e),
                    }
                ),
                500,
            )

    @chat_bp.route("/brain/switch", methods=["POST"])
    def switch_brain():
        """
        Switch to a different brain at runtime.

        Request body:
        {
            "brain": "claude" | "openai" | "config"
        }

        Returns success status and new active brain.
        """
        try:
            data = request.get_json()
            if not data or "brain" not in data:
                return jsonify({"error": "Missing 'brain' parameter"}), 400

            new_brain = data["brain"]
            valid_brains = ["priority", "claude", "openai", "grok", "gemini", "config"]

            if new_brain not in valid_brains:
                return (
                    jsonify(
                        {
                            "error": f"Invalid brain. Must be one of: {', '.join(valid_brains)}"
                        }
                    ),
                    400,
                )

            success = brain_router.switch_brain(new_brain)

            if success:
                return (
                    jsonify(
                        {
                            "success": True,
                            "active_brain": brain_router.get_active_brain(),
                            "message": f"Switched to {new_brain}",
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "active_brain": brain_router.get_active_brain(),
                            "message": f"Failed to switch to {new_brain}, stayed on current brain",
                        }
                    ),
                    500,
                )

        except Exception as e:
            logger.error(f"Error switching brain: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

    @chat_bp.route("/chat/start", methods=["POST"])
    def chat_start():
        """
        Create new conversation session.

        Request body:
        {
            "user_id": "user123",
            "persona": "fitness_coach"  (optional)
        }

        Returns:
        {
            "session_id": "session_...",
            "persona": "fitness_coach",
            "available_personas": [...]
        }
        """
        try:
            data = request.get_json()
            user_id = data.get("user_id", "anonymous")
            persona = data.get("persona", "personal_trainer")

            # Validate persona
            if not persona_manager.validate_persona(persona):
                return (
                    jsonify(
                        {"error": f"Invalid persona. Available: {persona_manager.list_personas()}"}
                    ),
                    400,
                )

            # Create session
            session_id = session_manager.create_session(user_id, persona)

            logger.info("Created chat session: %s", session_id)

            return (
                jsonify(
                    {
                        "session_id": session_id,
                        "persona": persona,
                        "persona_description": persona_manager.get_persona_description(persona),
                        "available_personas": persona_manager.list_personas(),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            return jsonify({"error": "Failed to create session"}), 500

    @chat_bp.route("/chat/stream", methods=["POST"])
    def chat_stream():
        """
        Streaming chat endpoint (SSE).

        Request body:
        {
            "session_id": "session_...",
            "message": "How are you?"
        }

        Response: Server-Sent Events (SSE) stream
        data: {"token": "Great! "}
        data: {"token": "Ready "}
        data: {"token": "to train?"}
        data: {"done": true}
        """
        try:
            data = request.get_json()
            session_id = data.get("session_id")
            user_message = data.get("message")

            if not session_id or not user_message:
                return jsonify({"error": "Missing session_id or message"}), 400

            if not session_manager.session_exists(session_id):
                return jsonify({"error": "Session not found"}), 404

            # Add user message to history
            session_manager.add_message(session_id, "user", user_message)

            # Get conversation history
            messages = session_manager.get_messages(session_id)

            # Get persona system prompt
            persona = session_manager.get_persona(session_id)
            system_prompt = persona_manager.get_system_prompt(persona)

            logger.info("Streaming chat: session=%s, persona=%s", session_id, persona)

            def generate():
                """SSE generator function."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                full_response = ""

                try:

                    async def stream_tokens():
                        nonlocal full_response
                        # Get streaming brain
                        if brain_router.brain and brain_router.brain.supports_streaming():
                            async for token in brain_router.brain.stream_chat(
                                messages=messages, system_prompt=system_prompt
                            ):
                                full_response += token
                                yield f"data: {json.dumps({'token': token})}\n\n"
                        else:
                            # Fallback for non-streaming brains
                            response = brain_router.get_coaching_response(
                                {"intensity": "moderate", "volume": 50, "tempo": 20},
                                "intense",
                            )
                            full_response = response
                            yield f"data: {json.dumps({'token': response})}\n\n"

                    # Run async generator
                    async_gen = stream_tokens()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break

                    # Send done signal
                    yield f"data: {json.dumps({'done': True})}\n\n"

                    # Save assistant response
                    session_manager.add_message(session_id, "assistant", full_response)
                    logger.info("Stream complete: %s chars", len(full_response))

                except Exception as e:
                    logger.error(f"Streaming error: {e}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    loop.close()

            return Response(
                stream_with_context(generate()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                },
            )

        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            return jsonify({"error": "Streaming failed"}), 500

    @chat_bp.route("/chat/message", methods=["POST"])
    def chat_message():
        """
        Non-streaming chat endpoint (fallback).

        Request body:
        {
            "session_id": "session_...",
            "message": "How are you?"
        }

        Returns:
        {
            "message": "Great! Ready to train?",
            "session_id": "session_...",
            "persona": "fitness_coach"
        }
        """
        try:
            data = request.get_json()
            session_id = data.get("session_id")
            user_message = data.get("message")

            if not session_id or not user_message:
                return jsonify({"error": "Missing session_id or message"}), 400

            if not session_manager.session_exists(session_id):
                return jsonify({"error": "Session not found"}), 404

            # Add user message
            session_manager.add_message(session_id, "user", user_message)

            # Get history and persona
            messages = session_manager.get_messages(session_id)
            persona = session_manager.get_persona(session_id)
            system_prompt = persona_manager.get_system_prompt(persona)

            # Get response
            if brain_router.brain:
                loop = asyncio.new_event_loop()
                response = loop.run_until_complete(brain_router.brain.chat(messages, system_prompt))
                loop.close()
            else:
                # Fallback to config brain
                response = brain_router.get_coaching_response(
                    {"intensity": "moderate", "volume": 50, "tempo": 20}, "intense"
                )

            # Save assistant response
            session_manager.add_message(session_id, "assistant", response)

            logger.info("Chat message: session=%s, response_len=%s", session_id, len(response))

            return (
                jsonify(
                    {"message": response, "session_id": session_id, "persona": persona}
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error in chat message: {e}", exc_info=True)
            return jsonify({"error": "Chat failed"}), 500

    @chat_bp.route("/chat/sessions", methods=["GET"])
    def list_sessions():
        """
        List all sessions.

        Query params:
        - user_id: Filter by user (optional)

        Returns:
        {
            "sessions": [...]
        }
        """
        try:
            user_id = request.args.get("user_id")
            sessions = session_manager.list_sessions(user_id)

            return jsonify({"sessions": sessions}), 200

        except Exception as e:
            logger.error(f"Error listing sessions: {e}", exc_info=True)
            return jsonify({"error": "Failed to list sessions"}), 500

    @chat_bp.route("/chat/sessions/<session_id>", methods=["DELETE"])
    def delete_session(session_id):
        """Delete a session."""
        try:
            session_manager.delete_session(session_id)
            return jsonify({"success": True, "session_id": session_id}), 200

        except Exception as e:
            logger.error(f"Error deleting session: {e}", exc_info=True)
            return jsonify({"error": "Failed to delete session"}), 500

    @chat_bp.route("/chat/personas", methods=["GET"])
    def list_personas():
        """
        List all available personas.

        Returns:
        {
            "personas": [
                {"id": "fitness_coach", "description": "..."},
                ...
            ]
        }
        """
        try:
            personas = []
            for persona_id in persona_manager.list_personas():
                personas.append(
                    {
                        "id": persona_id,
                        "description": persona_manager.get_persona_description(persona_id),
                    }
                )

            return jsonify({"personas": personas}), 200

        except Exception as e:
            logger.error(f"Error listing personas: {e}", exc_info=True)
            return jsonify({"error": "Failed to list personas"}), 500

    return chat_bp

