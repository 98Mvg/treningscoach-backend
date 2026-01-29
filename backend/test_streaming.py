#!/usr/bin/env python3
"""
Test script for streaming chat system.
Demonstrates real-time token-by-token streaming.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:5001"


def create_session(user_id, persona="fitness_coach"):
    """Create a new chat session."""
    print(f"\n🎯 Creating session for {user_id} with {persona} persona...")

    response = requests.post(
        f"{BASE_URL}/chat/start",
        json={"user_id": user_id, "persona": persona}
    )

    data = response.json()
    session_id = data["session_id"]

    print(f"✅ Session created: {session_id}")
    print(f"📝 Description: {data['persona_description']}")

    return session_id


def stream_message(session_id, message):
    """Send message and stream response."""
    print(f"\n💬 You: {message}")
    print(f"🤖 Coach: ", end="", flush=True)

    response = requests.post(
        f"{BASE_URL}/chat/stream",
        json={"session_id": session_id, "message": message},
        stream=True
    )

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data = json.loads(line_str[6:])

                if 'token' in data:
                    # Print token and flush to show streaming effect
                    print(data['token'], end="", flush=True)
                    time.sleep(0.05)  # Slight delay to visualize streaming

                if data.get('done'):
                    print()  # New line after complete response
                    break


def test_conversation():
    """Run a test conversation."""
    print("=" * 60)
    print("🏋️  STREAMING CHAT TEST")
    print("=" * 60)

    # Create session
    session_id = create_session("demo_user", "fitness_coach")

    # Test conversation
    messages = [
        "Hey! Ready to train?",
        "What should I do for warm up?",
        "I'm feeling tired today",
        "Let's do this!"
    ]

    for msg in messages:
        stream_message(session_id, msg)
        time.sleep(1)

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)


def test_personas():
    """Test different personas."""
    print("\n" + "=" * 60)
    print("🎭 TESTING DIFFERENT PERSONAS")
    print("=" * 60)

    personas = [
        ("fitness_coach", "I need motivation!"),
        ("calm_coach", "Help me relax"),
        ("drill_sergeant", "I want to quit")
    ]

    for persona, message in personas:
        session_id = create_session("demo_user", persona)
        stream_message(session_id, message)
        time.sleep(1)


if __name__ == "__main__":
    try:
        # Run tests
        test_conversation()
        test_personas()

        print("\n✨ All tests passed!")

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
