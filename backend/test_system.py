#!/usr/bin/env python3
"""
System Test - Verify Treningscoach Backend
Tests the full workflow: audio analysis + coaching
"""

import wave
import struct
import requests
import json

def create_test_audio(filename="test_breath.wav", duration=2.0):
    """Create a simple test audio file (simulated breathing)"""
    sample_rate = 44100
    num_samples = int(duration * sample_rate)

    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Create simple breathing pattern (sine wave)
        import math
        for i in range(num_samples):
            # Low frequency breathing sound (0.5 Hz = 30 breaths/min)
            value = int(8000 * math.sin(2 * math.pi * 0.5 * i / sample_rate))
            wav_file.writeframes(struct.pack('<h', value))

    print(f"✅ Created test audio: {filename}")
    return filename

def test_health():
    """Test 1: Health endpoint"""
    print("\n=== Test 1: Health Check ===")
    response = requests.get("http://localhost:10000/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Server is healthy")
        print(f"   Version: {data.get('version')}")
        print(f"   Status: {data.get('status')}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

    return True

def test_analyze():
    """Test 2: Analyze endpoint"""
    print("\n=== Test 2: Breath Analysis ===")

    # Create test audio
    audio_file = create_test_audio()

    # Send to analyze endpoint
    with open(audio_file, 'rb') as f:
        response = requests.post(
            "http://localhost:10000/analyze",
            files={'audio': f}
        )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Analysis successful")
        print(f"   Intensity: {data.get('intensity')}")
        print(f"   Volume: {data.get('volume')}")
        print(f"   Tempo: {data.get('tempo')}")
        print(f"   Silence: {data.get('silence')}%")
    else:
        print(f"❌ Analysis failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True

def test_coach():
    """Test 3: Coach endpoint (full workflow)"""
    print("\n=== Test 3: Coach Response ===")

    # Create test audio
    audio_file = create_test_audio()

    # Send to coach endpoint
    with open(audio_file, 'rb') as f:
        response = requests.post(
            "http://localhost:10000/coach",
            files={'audio': f},
            data={'phase': 'intense'}
        )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Coaching successful")
        print(f"   Coach says: '{data.get('text')}'")
        print(f"   Intensity: {data['breath_analysis'].get('intensity')}")
        print(f"   Audio URL: {data.get('audio_url')}")
        print(f"   Phase: {data.get('phase')}")
    else:
        print(f"❌ Coaching failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True

def test_brain_health():
    """Test 4: Brain Router health"""
    print("\n=== Test 4: Brain Router Health ===")

    response = requests.get("http://localhost:10000/brain/health")

    if response.status_code in [200, 503]:
        data = response.json()
        print(f"✅ Brain router responded")
        print(f"   Active brain: {data.get('active_brain')}")
        print(f"   Healthy: {data.get('healthy')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"❌ Brain health check failed: {response.status_code}")
        return False

    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("🏋️  TRENINGSCOACH SYSTEM TEST")
    print("=" * 50)

    tests = [
        ("Health Check", test_health),
        ("Breath Analysis", test_analyze),
        ("Coach Response", test_coach),
        ("Brain Health", test_brain_health)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
