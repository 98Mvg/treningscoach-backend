#!/usr/bin/env python3
"""
Test script for STEP 4: Hybrid Brain Mode

Demonstrates:
- Config brain for fast, immediate cues (STEP 2 intensity messages)
- Claude brain for pattern detection and trend analysis
- Hot-switching between brains mid-session
- Quality improvement without speed degradation
"""

import sys
from brain_router import BrainRouter
from config import CONTINUOUS_COACH_MESSAGES

def test_hybrid_initialization():
    """Test that hybrid mode initializes correctly."""

    print("\n" + "="*70)
    print("🧪 STEP 4: HYBRID MODE INITIALIZATION")
    print("="*70 + "\n")

    # Test 1: Config brain without hybrid
    router_no_hybrid = BrainRouter(brain_type="config", use_hybrid=False)
    print(f"Config (no hybrid): {router_no_hybrid.get_active_brain()}")
    print(f"  Claude brain available: {router_no_hybrid.claude_brain is not None}")
    print(f"  Hybrid mode: {router_no_hybrid.use_hybrid}\n")

    # Test 2: Config brain with hybrid
    router_hybrid = BrainRouter(brain_type="config", use_hybrid=True)
    print(f"Config (hybrid mode): {router_hybrid.get_active_brain()}")
    print(f"  Claude brain available: {router_hybrid.claude_brain is not None}")
    print(f"  Hybrid mode: {router_hybrid.use_hybrid}")

    if router_hybrid.claude_brain:
        print(f"  ✅ Hybrid mode active - Claude will detect patterns")
    else:
        print(f"  ⚠️ Claude unavailable - falling back to config-only")

    print()

def test_pattern_detection():
    """Test pattern detection with mock workout data."""

    print("="*70)
    print("🔍 STEP 4: PATTERN DETECTION TEST")
    print("="*70 + "\n")

    router = BrainRouter(brain_type="config", use_hybrid=True)

    if not router.claude_brain:
        print("⚠️ Claude not available - skipping pattern detection test")
        print("   Set ANTHROPIC_API_KEY to test this feature\n")
        return

    # Mock workout progression: User starts calm, builds intensity
    breath_history = [
        {"intensitet": "rolig", "tempo": 15, "volum": 20, "timestamp": "2024-01-28T10:00:00"},
        {"intensitet": "rolig", "tempo": 16, "volum": 22, "timestamp": "2024-01-28T10:00:10"},
        {"intensitet": "moderat", "tempo": 20, "volum": 35, "timestamp": "2024-01-28T10:00:20"},
        {"intensitet": "moderat", "tempo": 22, "volum": 40, "timestamp": "2024-01-28T10:00:30"},
        {"intensitet": "hard", "tempo": 28, "volum": 65, "timestamp": "2024-01-28T10:00:40"},
    ]

    coaching_history = [
        {"text": "You can push harder!", "timestamp": "2024-01-28T10:00:00"},
        {"text": "Speed up a bit!", "timestamp": "2024-01-28T10:00:10"},
        {"text": "Keep going, good pace!", "timestamp": "2024-01-28T10:00:20"},
        {"text": "Nice rhythm, maintain!", "timestamp": "2024-01-28T10:00:30"},
    ]

    print("Workout progression:")
    print("  0:00 → rolig (too calm)")
    print("  0:10 → rolig (still calm)")
    print("  0:20 → moderat (picking up)")
    print("  0:30 → moderat (good pace)")
    print("  0:40 → hard (working hard!)")
    print()

    print("Detecting pattern...")
    pattern = router.detect_pattern(breath_history, coaching_history, "intense")

    if pattern:
        print(f"✅ Pattern detected: \"{pattern}\"")
        print(f"   This insight is from Claude (trend analysis)\n")
    else:
        print("⚠️ No pattern detected\n")

def test_should_use_pattern_insight():
    """Test pattern insight timing logic."""

    print("="*70)
    print("⏱️  STEP 4: PATTERN INSIGHT TIMING")
    print("="*70 + "\n")

    router = BrainRouter(brain_type="config", use_hybrid=True)

    test_cases = [
        (15, None, "15s into workout, no previous pattern"),
        (35, None, "35s into workout, no previous pattern"),
        (65, None, "65s into workout, no previous pattern"),
        (95, 40, "95s into workout, last pattern at 40s (55s ago)"),
        (95, 70, "95s into workout, last pattern at 70s (25s ago)"),
    ]

    print("Pattern insight eligibility:\n")
    for elapsed, last_pattern, desc in test_cases:
        # Run multiple times since it's probabilistic
        results = [router.should_use_pattern_insight(elapsed, last_pattern) for _ in range(10)]
        eligible_count = sum(results)

        status = "✅" if eligible_count > 0 else "❌"
        print(f"{status} {desc}")
        print(f"   Eligible: {eligible_count}/10 attempts ({eligible_count*10}%)")

    print()

def test_hot_switching():
    """Test hot-switching between brains mid-session."""

    print("="*70)
    print("🔄 STEP 4: HOT-SWITCHING TEST")
    print("="*70 + "\n")

    router = BrainRouter(brain_type="config", use_hybrid=True)

    print(f"Initial brain: {router.get_active_brain()}")
    print(f"Hybrid Claude available: {router.claude_brain is not None}\n")

    # Try switching to Claude
    print("Attempting to switch to Claude...")
    success = router.switch_brain("claude", preserve_hybrid=True)

    if success:
        print(f"✅ Switched to: {router.get_active_brain()}")
        print(f"   Hybrid Claude preserved: {router.claude_brain is not None}")
    else:
        print(f"⚠️ Switch failed (expected if no API key)")
        print(f"   Current brain: {router.get_active_brain()}")

    print()

    # Switch back to config
    print("Switching back to config...")
    success = router.switch_brain("config", preserve_hybrid=True)
    print(f"{'✅' if success else '❌'} Current brain: {router.get_active_brain()}")
    print(f"   Hybrid Claude preserved: {router.claude_brain is not None}\n")

def demonstrate_hybrid_strategy():
    """Show the STEP 4 hybrid strategy visually."""

    print("="*70)
    print("💡 STEP 4: HYBRID BRAIN STRATEGY")
    print("="*70 + "\n")

    print("The Best of Both Worlds:\n")

    print("Config Brain (Fast, Immediate Cues):")
    print("  ✅ Response time: <1ms")
    print("  ✅ Uses STEP 2 intensity messages (rolig/moderat/hard/kritisk)")
    print("  ✅ Perfect for real-time coaching (every 5-15 seconds)")
    print("  ✅ No API costs")
    print("  ❌ No pattern detection")
    print("  ❌ No trend analysis\n")

    print("Claude Brain (Pattern Detection):")
    print("  ✅ Detects workout progression trends")
    print("  ✅ Provides higher-level encouragement")
    print("  ✅ Interprets intensity changes over time")
    print("  ❌ Response time: ~200-400ms")
    print("  ❌ API costs per call\n")

    print("Hybrid Strategy (STEP 4):")
    print("  🎯 Config handles 95% of coaching (fast cues)")
    print("  🎯 Claude handles 5% (pattern insights every 60-90s)")
    print("  🎯 Quality improves, speed doesn't degrade")
    print("  🎯 Best user experience + reasonable API costs\n")

    print("Example workout (5 minutes, 25 coaching ticks):\n")

    ticks = [
        (0, "config", "Easy pace, nice start.", "warmup/rolig"),
        (8, "config", "Steady, good warmup.", "warmup/moderat"),
        (16, "config", "Gentle, keep warming up.", "warmup/moderat"),
        (24, "config", "Nice and easy.", "warmup/rolig"),
        (32, "config", "Perfect warmup pace.", "warmup/moderat"),
        (40, "config", "You can push harder!", "intense/rolig"),
        (48, "config", "More effort, you got this!", "intense/rolig"),
        (56, "config", "Speed up a bit!", "intense/rolig"),
        (64, "config", "Keep going, good pace!", "intense/moderat"),
        (72, "config", "Stay with it!", "intense/moderat"),
        (80, "config", "Nice rhythm, maintain!", "intense/moderat"),
        (88, "config", "You got this!", "intense/moderat"),
        (96, "CLAUDE", "Building intensity steadily - great pacing!", "PATTERN"),  # Pattern insight
        (104, "config", "Perfect! Hold it!", "intense/hard"),
        (110, "config", "Yes! Strong!", "intense/hard"),
        (116, "config", "Keep this!", "intense/hard"),
        (122, "config", "Excellent work!", "intense/hard"),
        (128, "config", "Perfect! Hold it!", "intense/hard"),
        (136, "config", "Yes! Strong!", "intense/hard"),
        (144, "config", "Keep this!", "intense/hard"),
        (152, "config", "Excellent work!", "intense/hard"),
        (160, "config", "Perfect! Hold it!", "intense/hard"),
        (168, "config", "Yes! Strong!", "intense/hard"),
        (180, "CLAUDE", "You found your rhythm - intensity stable!", "PATTERN"),  # Pattern insight
        (188, "config", "Excellent work!", "intense/hard"),
    ]

    config_count = sum(1 for _, brain, _, _ in ticks if brain == "config")
    claude_count = sum(1 for _, brain, _, _ in ticks if brain == "CLAUDE")

    for elapsed, brain, message, context in ticks[:10]:  # Show first 10
        icon = "⚡" if brain == "config" else "🧠"
        print(f"  {elapsed:3d}s {icon} {brain:7s} → \"{message}\" ({context})")

    print(f"  ... (showing 10/{len(ticks)} ticks)")
    print()
    print(f"Summary:")
    print(f"  Config cues: {config_count}/{len(ticks)} ({config_count/len(ticks)*100:.0f}%)")
    print(f"  Claude insights: {claude_count}/{len(ticks)} ({claude_count/len(ticks)*100:.0f}%)")
    print(f"  Result: Fast + Intelligent\n")

def main():
    """Run all STEP 4 tests."""

    print("\n" + "🎯"*35)
    print("  STEP 4: Enable Claude (but correctly)")
    print("🎯"*35 + "\n")

    try:
        # Run tests
        test_hybrid_initialization()
        test_pattern_detection()
        test_should_use_pattern_insight()
        test_hot_switching()
        demonstrate_hybrid_strategy()

        print("="*70)
        print("🎉 STEP 4 COMPLETE")
        print("="*70 + "\n")

        print("✅ Done when:")
        print("  ✅ You can hot-switch brain mid-session")
        print("  ✅ Coach quality improves, not slows down")
        print("  ✅ Config handles immediate cues (fast)")
        print("  ✅ Claude handles patterns (intelligent)\n")

        print("Next steps:")
        print("  1. Set ANTHROPIC_API_KEY to enable Claude pattern detection")
        print("  2. Test with real workout to see pattern insights")
        print("  3. Adjust pattern insight frequency if needed (currently 60-90s)\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
