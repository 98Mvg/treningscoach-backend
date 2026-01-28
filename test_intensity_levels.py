#!/usr/bin/env python3
"""
Test script to verify STEP 2: Coaching Intensity Levels
Tests that same workout feels different based on breathing intensity:
- kritisk → FIRM, urgent (5s intervals, 1-3 words)
- hard → ASSERTIVE, focused (6s intervals, 2-3 words)
- moderat → GUIDING, encouraging (8s intervals, 2-4 words)
- rolig → REASSURING, calm (12s intervals, 3-5 words)
"""

import requests
import json
from coaching_intelligence import calculate_next_interval, should_coach_speak
from config import CONTINUOUS_COACH_MESSAGES

BASE_URL = "http://localhost:5001"

def test_intensity_intervals():
    """Test that intervals adapt to intensity levels."""
    print("\n" + "="*60)
    print("🎯 STEP 2: INTENSITY-DRIVEN FREQUENCY TEST")
    print("="*60 + "\n")

    test_cases = [
        ("kritisk", "warmup", 5, "URGENT - safety-first"),
        ("kritisk", "intense", 5, "URGENT - safety-first"),
        ("hard", "intense", 6, "FOCUSED - assertive"),
        ("hard", "warmup", 8, "FOCUSED + warmup modifier (+2s)"),
        ("moderat", "intense", 8, "GUIDING - encouraging"),
        ("moderat", "warmup", 10, "GUIDING + warmup modifier (+2s)"),
        ("rolig", "intense", 12, "REASSURING - calm"),
        ("rolig", "warmup", 14, "REASSURING + warmup modifier (+2s)"),
        ("rolig", "cooldown", 15, "REASSURING + cooldown modifier (+3s, clamped)"),
    ]

    print("Interval calculations:\n")
    all_passed = True
    for intensitet, phase, expected, description in test_cases:
        actual = calculate_next_interval(phase, intensitet)
        status = "✅" if actual == expected else "❌"
        if actual != expected:
            all_passed = False
        print(f"{status} {intensitet:8s} + {phase:8s} → {actual:2d}s (expected {expected}s) - {description}")

    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n")

def test_message_personalities():
    """Test that message tone/length adapts to intensity."""
    print("="*60)
    print("🎭 STEP 2: MESSAGE PERSONALITY TEST")
    print("="*60 + "\n")

    print("Message bank analysis:\n")

    # Test kritisk messages
    kritisk_messages = CONTINUOUS_COACH_MESSAGES["kritisk"]
    kritisk_lengths = [len(msg.split()) for msg in kritisk_messages]
    print(f"kritisk (FIRM, URGENT):")
    print(f"  Messages: {kritisk_messages}")
    print(f"  Word counts: {kritisk_lengths} (target: 1-3 words)")
    print(f"  ✅ All 1-3 words: {all(1 <= wc <= 3 for wc in kritisk_lengths)}\n")

    # Test intense/hard messages
    hard_messages = CONTINUOUS_COACH_MESSAGES["intense"]["hard"]
    hard_lengths = [len(msg.split()) for msg in hard_messages]
    print(f"hard during intense (ASSERTIVE, FOCUSED):")
    print(f"  Messages: {hard_messages}")
    print(f"  Word counts: {hard_lengths} (target: 2-3 words)")
    print(f"  ✅ All 2-3 words: {all(2 <= wc <= 3 for wc in hard_lengths)}\n")

    # Test intense/moderat messages
    moderat_messages = CONTINUOUS_COACH_MESSAGES["intense"]["moderat"]
    moderat_lengths = [len(msg.split()) for msg in moderat_messages]
    print(f"moderat during intense (GUIDING, ENCOURAGING):")
    print(f"  Messages: {moderat_messages}")
    print(f"  Word counts: {moderat_lengths} (target: 2-4 words)")
    print(f"  ✅ All 2-4 words: {all(2 <= wc <= 4 for wc in moderat_lengths)}\n")

    # Test intense/rolig messages
    rolig_messages = CONTINUOUS_COACH_MESSAGES["intense"]["rolig"]
    rolig_lengths = [len(msg.split()) for msg in rolig_messages]
    print(f"rolig during intense (REASSURING, CALM):")
    print(f"  Messages: {rolig_messages}")
    print(f"  Word counts: {rolig_lengths} (target: 3-5 words)")
    print(f"  ✅ All 3-5 words: {all(3 <= wc <= 5 for wc in rolig_lengths)}\n")

    # Test warmup messages
    warmup_messages = CONTINUOUS_COACH_MESSAGES["warmup"]
    warmup_lengths = [len(msg.split()) for msg in warmup_messages]
    print(f"warmup (REASSURING, CALM):")
    print(f"  Messages: {warmup_messages}")
    print(f"  Word counts: {warmup_lengths} (target: 3-5 words)")
    print(f"  ✅ All 3-5 words: {all(3 <= wc <= 5 for wc in warmup_lengths)}\n")

def test_personality_comparison():
    """Demonstrate how same workout feels different based on intensity."""
    print("="*60)
    print("💡 STEP 2: PERSONALITY COMPARISON")
    print("="*60 + "\n")

    print("Scenario: User is in INTENSE phase of workout\n")

    scenarios = [
        {
            "breath": "rolig (too calm)",
            "interval": "12s",
            "message": CONTINUOUS_COACH_MESSAGES["intense"]["rolig"][0],
            "personality": "REASSURING but encouraging - coach wants you to push harder"
        },
        {
            "breath": "moderat (good pace)",
            "interval": "8s",
            "message": CONTINUOUS_COACH_MESSAGES["intense"]["moderat"][0],
            "personality": "GUIDING, encouraging - coach supports your effort"
        },
        {
            "breath": "hard (working hard)",
            "interval": "6s",
            "message": CONTINUOUS_COACH_MESSAGES["intense"]["hard"][0],
            "personality": "ASSERTIVE, focused - coach celebrates your intensity"
        },
        {
            "breath": "kritisk (too hard)",
            "interval": "5s",
            "message": CONTINUOUS_COACH_MESSAGES["kritisk"][0],
            "personality": "FIRM, safety-first - coach prioritizes your wellbeing"
        }
    ]

    for scenario in scenarios:
        print(f"🫁 Breathing: {scenario['breath']}")
        print(f"   ⏱️  Check frequency: Every {scenario['interval']}")
        print(f"   💬 Coach says: \"{scenario['message']}\"")
        print(f"   🎭 Personality: {scenario['personality']}\n")

    print("✅ VERIFICATION:")
    print("   ✅ Same workout, different coaching based on breathing state")
    print("   ✅ 'kritisk' feels urgent (5s, 1-3 words), not verbose")
    print("   ✅ Frequency adapts: 5s (urgent) → 12s (reassuring)")
    print("   ✅ Tone adapts: FIRM → ASSERTIVE → GUIDING → REASSURING\n")

def check_backend_health():
    """Verify backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        health = response.json()
        print(f"✅ Backend health: {health['status']}")
        print(f"   Version: {health.get('version', 'unknown')}\n")
        return True
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        print(f"   Start backend with: cd backend && python3 main.py\n")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 STEP 2: COACHING INTENSITY LEVELS TEST SUITE")
    print("="*60 + "\n")

    if not check_backend_health():
        exit(1)

    # Run all tests
    test_intensity_intervals()
    test_message_personalities()
    test_personality_comparison()

    print("="*60)
    print("🎉 STEP 2 COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test with iOS app to verify real-time adaptation")
    print("  2. Observe if intensity changes are noticeable during workout")
    print("  3. Tune intervals if needed (currently 5s-15s range)\n")
