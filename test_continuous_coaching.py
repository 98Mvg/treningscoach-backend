#!/usr/bin/env python3
"""
Test script for continuous coaching endpoint.
Tests back-to-back calls with same session_id to verify:
- Coaching history is respected
- should_speak=false suppresses output correctly
- wait_seconds varies based on context
"""

import requests
import time
import os

# Configuration
BASE_URL = "http://localhost:5001"
TEST_AUDIO = "test_breath.wav"
SESSION_ID = "session_test_continuous_123"

def create_test_audio():
    """Create a simple test WAV file for testing."""
    import wave
    import struct
    import math

    # Create a simple sine wave (simulated breathing sound)
    sample_rate = 44100
    duration = 2.0  # 2 seconds
    frequency = 440  # A4 note

    num_samples = int(sample_rate * duration)

    with wave.open(TEST_AUDIO, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(num_samples):
            # Generate sine wave with amplitude modulation (simulates breathing)
            t = i / sample_rate
            amplitude = 0.5 * (1 + math.sin(2 * math.pi * 0.5 * t))  # Slow modulation
            sample = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * t))
            wav_file.writeframes(struct.pack('<h', sample))

    print(f"✅ Created test audio: {TEST_AUDIO}")

def test_continuous_coaching():
    """Test continuous coaching with multiple sequential calls."""

    print("\n" + "="*60)
    print("🧪 CONTINUOUS COACHING TEST")
    print("="*60 + "\n")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        health = response.json()
        print(f"✅ Backend health: {health['status']}")
        print(f"   Version: {health.get('version', 'unknown')}\n")
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        print("   Start backend with: cd backend && python3 main.py")
        return

    # Create test audio if it doesn't exist
    if not os.path.exists(TEST_AUDIO):
        create_test_audio()

    # Test scenario: 5 consecutive coaching ticks
    test_cases = [
        {
            "phase": "warmup",
            "elapsed_seconds": 30,
            "last_coaching": "",
            "description": "First tick - warmup phase, no history"
        },
        {
            "phase": "warmup",
            "elapsed_seconds": 40,
            "last_coaching": "Easy pace.",
            "description": "Second tick - 10s later, same phase"
        },
        {
            "phase": "intense",
            "elapsed_seconds": 130,
            "last_coaching": "Steady.",
            "description": "Third tick - transitioned to intense"
        },
        {
            "phase": "intense",
            "elapsed_seconds": 140,
            "last_coaching": "PUSH! Harder!",
            "description": "Fourth tick - 10s later in intense (should likely be silent)"
        },
        {
            "phase": "intense",
            "elapsed_seconds": 160,
            "last_coaching": "PUSH! Harder!",
            "description": "Fifth tick - 20s later in intense (may speak again)"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"📊 Test {i}/5: {test_case['description']}")
        print(f"   Phase: {test_case['phase']}, Elapsed: {test_case['elapsed_seconds']}s")

        try:
            with open(TEST_AUDIO, 'rb') as audio_file:
                files = {'audio': ('test.wav', audio_file, 'audio/wav')}
                data = {
                    'session_id': SESSION_ID,
                    'phase': test_case['phase'],
                    'last_coaching': test_case['last_coaching'],
                    'elapsed_seconds': test_case['elapsed_seconds']
                }

                start_time = time.time()
                response = requests.post(
                    f"{BASE_URL}/coach/continuous",
                    files=files,
                    data=data,
                    timeout=30
                )
                elapsed_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    result = response.json()
                    results.append(result)

                    print(f"   ✅ Response ({elapsed_ms}ms):")
                    print(f"      Intensity: {result['breath_analysis']['intensitet']}")
                    print(f"      Should speak: {result['should_speak']}")
                    print(f"      Message: \"{result['text']}\"")
                    print(f"      Reason: {result.get('reason', 'none')}")
                    print(f"      Next interval: {result['wait_seconds']}s")

                    if result['should_speak']:
                        print(f"      🗣️ Coach will speak!")
                    else:
                        print(f"      🤐 Coach stays silent")
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    print(f"      {response.text}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        print()

        # Small delay between requests
        if i < len(test_cases):
            time.sleep(0.5)

    # Summary
    print("="*60)
    print("📈 TEST SUMMARY")
    print("="*60 + "\n")

    if results:
        spoke_count = sum(1 for r in results if r['should_speak'])
        silent_count = len(results) - spoke_count

        print(f"Total ticks: {len(results)}")
        print(f"Coach spoke: {spoke_count} times")
        print(f"Coach silent: {silent_count} times")
        print(f"Silence rate: {silent_count/len(results)*100:.1f}%")

        print("\n📊 Decisions breakdown:")
        for i, result in enumerate(results, 1):
            status = "🗣️ SPOKE" if result['should_speak'] else "🤐 SILENT"
            print(f"  {i}. {status} - {result.get('reason', 'no reason')} - \"{result['text']}\"")

        print("\n⏱️ Wait intervals:")
        intervals = [r['wait_seconds'] for r in results]
        print(f"  Range: {min(intervals):.0f}s - {max(intervals):.0f}s")
        print(f"  Average: {sum(intervals)/len(intervals):.1f}s")

        # Verify key behaviors
        print("\n✅ VERIFICATION:")

        # Check if first tick speaks (should welcome)
        if results[0]['should_speak']:
            print("  ✅ First tick speaks (welcome)")
        else:
            print("  ⚠️ First tick silent (expected to speak)")

        # Check if any ticks were suppressed
        if silent_count > 0:
            print(f"  ✅ Coaching intelligence active (suppressed {silent_count} ticks)")
        else:
            print("  ⚠️ All ticks spoke (intelligence may not be working)")

        # Check if intervals vary
        if len(set(intervals)) > 1:
            print(f"  ✅ Dynamic intervals (varied from {min(intervals):.0f}s to {max(intervals):.0f}s)")
        else:
            print("  ⚠️ Static intervals (all same)")
    else:
        print("❌ No successful responses")

    # Cleanup
    if os.path.exists(TEST_AUDIO):
        os.remove(TEST_AUDIO)
        print(f"\n🧹 Cleaned up {TEST_AUDIO}")

if __name__ == "__main__":
    test_continuous_coaching()
