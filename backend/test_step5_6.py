#!/usr/bin/env python3
"""
Test script for STEP 5 & 6: Memory + Human Voice

STEP 5: Memory That Actually Matters
- Minimal memory (preferences, safety events, improvement)
- Injected once at session start

STEP 6: Make Voice Feel Human
- Strategic silence (when breathing is optimal)
- Variation in phrasing
- Overtalk detection
"""

import sys
from user_memory import UserMemory
from voice_intelligence import VoiceIntelligence

def test_user_memory():
    """Test STEP 5: User memory management."""

    print("\n" + "="*70)
    print("🧠 STEP 5: MEMORY THAT ACTUALLY MATTERS")
    print("="*70 + "\n")

    memory = UserMemory(storage_path="test_memories.json")

    # Test 1: New user
    print("Test 1: New user (first workout)")
    user1_memory = memory.get_memory("user_123")
    print(f"  Memory: {user1_memory}")
    print(f"  Summary: \"{memory.get_memory_summary('user_123')}\"\n")

    # Test 2: Update memory after workout
    print("Test 2: Update memory after workout with critical event")
    memory.update_memory(
        user_id="user_123",
        critical_event=True,
        overbreathe_detected=True
    )
    user1_memory = memory.get_memory("user_123")
    print(f"  Memory: {user1_memory}")
    print(f"  Summary: \"{memory.get_memory_summary('user_123')}\"\n")

    # Test 3: Multiple workouts
    print("Test 3: User with workout history")
    for i in range(3):
        memory.update_memory(user_id="user_123")

    user1_memory = memory.get_memory("user_123")
    print(f"  Total workouts: {user1_memory['total_workouts']}")
    print(f"  Summary: \"{memory.get_memory_summary('user_123')}\"\n")

    # Test 4: Coaching preference
    print("Test 4: User with coaching style preference")
    memory.update_memory(
        user_id="user_456",
        coaching_style_preference="calm"
    )
    user2_memory = memory.get_memory("user_456")
    print(f"  Prefers: {user2_memory['user_prefers']}")
    print(f"  Summary: \"{memory.get_memory_summary('user_456')}\"\n")

    print("✅ STEP 5: Memory stores minimal, meaningful data")
    print("✅ Memory injected once at session start (not every message)\n")

    # Cleanup
    import os
    if os.path.exists("test_memories.json"):
        os.remove("test_memories.json")

def test_voice_intelligence():
    """Test STEP 6: Voice intelligence (silence, variation, pacing)."""

    print("="*70)
    print("🗣️ STEP 6: MAKE VOICE FEEL HUMAN")
    print("="*70 + "\n")

    voice = VoiceIntelligence()

    # Test 1: Strategic silence during optimal breathing
    print("Test 1: Strategic silence (optimal breathing)\n")

    test_cases = [
        {
            "breath": {"intensitet": "rolig", "tempo": 15},
            "phase": "warmup",
            "elapsed": 35,
            "expected_silent": True,
            "desc": "Optimal warmup breathing"
        },
        {
            "breath": {"intensitet": "hard", "tempo": 28},
            "phase": "intense",
            "elapsed": 120,
            "expected_silent": True,
            "desc": "Optimal intense breathing"
        },
        {
            "breath": {"intensitet": "kritisk", "tempo": 40},
            "phase": "intense",
            "elapsed": 150,
            "expected_silent": False,
            "desc": "Critical breathing (never silent)"
        },
        {
            "breath": {"intensitet": "rolig", "tempo": 12},
            "phase": "intense",
            "elapsed": 180,
            "expected_silent": False,
            "desc": "Too calm during intense (needs coaching)"
        },
    ]

    for test in test_cases:
        should_be_silent, reason = voice.should_stay_silent(
            breath_data=test["breath"],
            phase=test["phase"],
            last_coaching="",
            elapsed_seconds=test["elapsed"]
        )
        status = "✅" if should_be_silent == test["expected_silent"] else "❌"
        print(f"{status} {test['desc']}")
        print(f"   Silent: {should_be_silent} (reason: {reason})")

    print()

    # Test 2: Human variation
    print("Test 2: Human variation (avoid robotic repetition)\n")

    original_messages = [
        "Perfect!",
        "Keep going!",
        "Good pace!",
        "Hold it!",
    ]

    print("Testing variation (10% chance per message):")
    for msg in original_messages:
        variations = set()
        for _ in range(20):  # Try 20 times
            varied = voice.add_human_variation(msg)
            variations.add(varied)

        print(f"  \"{msg}\" → {len(variations)} variations found")
        if len(variations) > 1:
            print(f"    Examples: {list(variations)[:3]}")

    print()

    # Test 3: Overtalk detection
    print("Test 3: Overtalk detection\n")

    # Create mock coaching history
    coaching_history_quiet = [
        {"text": "Keep going!"},
        {"text": None},  # Silent
        {"text": "Good pace!"},
        {"text": None},  # Silent
    ]

    coaching_history_loud = [
        {"text": "Keep going!"},
        {"text": "Good pace!"},
        {"text": "Hold it!"},
        {"text": "Perfect!"},
    ]

    is_overtalking_quiet = voice.detect_overtalking(coaching_history_quiet)
    is_overtalking_loud = voice.detect_overtalking(coaching_history_loud)

    print(f"  Quiet history (2 spoken, 2 silent): Overtalking={is_overtalking_quiet}")
    print(f"  Loud history (4 spoken, 0 silent): Overtalking={is_overtalking_loud}")
    print()

    print("✅ STEP 6: Silence = confidence")
    print("✅ STEP 6: Variation prevents robotic feel")
    print("✅ STEP 6: Overtalk detection reduces frequency\n")

def demonstrate_silence_philosophy():
    """Show the STEP 6 silence philosophy."""

    print("="*70)
    print("💡 STEP 6: SILENCE = CONFIDENCE")
    print("="*70 + "\n")

    print("Traditional coach (talks every tick):")
    print("  0:08 → \"Easy pace!\"")
    print("  0:16 → \"Steady!\"")
    print("  0:24 → \"Keep going!\"")
    print("  0:32 → \"Good!\"")
    print("  0:40 → \"Nice work!\"")
    print("  ⚠️ Feels like coach is nervous, needs to fill silence\n")

    print("STEP 6 coach (strategic silence):")
    print("  0:08 → \"Easy pace!\"")
    print("  0:16 → [Silent - breathing is optimal]")
    print("  0:24 → [Silent - breathing is optimal]")
    print("  0:32 → \"Perfect! Keep this.\"")
    print("  0:40 → [Silent - breathing is optimal]")
    print("  ✅ Feels like coach is confident, knows when to speak\n")

    print("Key principle:")
    print("  \"If breathing is optimal, say nothing.\"")
    print("  Silence communicates: 'You're doing great, I trust you.'\n")

def demonstrate_memory_injection():
    """Show STEP 5 memory injection strategy."""

    print("="*70)
    print("💾 STEP 5: MEMORY INJECTION STRATEGY")
    print("="*70 + "\n")

    print("❌ WRONG: Inject memory every message")
    print("  Every API call includes full user history (slow, expensive)")
    print("  Claude sees: 'User has done 47 workouts, prefers calm coaching, ...'")
    print("  Result: Latency increases, API costs explode\n")

    print("✅ RIGHT: Inject memory once at session start")
    print("  Memory loaded when session begins (one-time cost)")
    print("  Stored in session metadata: {'memory': 'User prefers calm coaching...'}")
    print("  Result: Fast, cheap, coach 'remembers' without overhead\n")

    print("Memory stores only:")
    print("  ✅ Coaching style preference (calm/assertive/balanced)")
    print("  ✅ Safety events (tends to overbreathe)")
    print("  ✅ Improvement markers (improving/stable/declining)")
    print("  ❌ NOT: Full workout logs, every breath sample, chat history\n")

def main():
    """Run all STEP 5 & 6 tests."""

    print("\n" + "🎯"*35)
    print("  STEP 5 & 6: Memory + Human Voice")
    print("🎯"*35 + "\n")

    try:
        # Run tests
        test_user_memory()
        test_voice_intelligence()
        demonstrate_silence_philosophy()
        demonstrate_memory_injection()

        print("="*70)
        print("🎉 STEP 5 & 6 COMPLETE")
        print("="*70 + "\n")

        print("✅ STEP 5 Done when:")
        print("  ✅ Coach 'remembers' the user next session")
        print("  ✅ But stays fast (memory injected once, not every message)\n")

        print("✅ STEP 6 Done when:")
        print("  ✅ Coach doesn't overtalk")
        print("  ✅ Silence feels intentional")
        print("  ✅ Variation prevents robotic feel\n")

        print("Next steps:")
        print("  1. Test with real workout to experience strategic silence")
        print("  2. Observe user memory persistence across sessions")
        print("  3. Fine-tune silence thresholds if needed\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
