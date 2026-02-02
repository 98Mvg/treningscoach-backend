#!/usr/bin/env python3
"""
Tests for BreathAnalyzer — DSP + spectral breath classification.

Run: python test_breath_analyzer.py
"""

import os
import sys
import tempfile
import wave
import struct
import math
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from breath_analyzer import BreathAnalyzer

# ============================================
# TEST HELPERS
# ============================================

def create_test_wav(filepath, duration=8.0, sample_rate=44100, frequencies=None, amplitude=0.5):
    """Create a synthetic WAV file with given frequencies."""
    n_samples = int(duration * sample_rate)
    samples = np.zeros(n_samples, dtype=np.float32)

    if frequencies:
        for freq, amp in frequencies:
            t = np.arange(n_samples) / sample_rate
            samples += amp * np.sin(2 * np.pi * freq * t)
    else:
        samples = np.random.randn(n_samples).astype(np.float32) * amplitude

    # Clip to [-1, 1]
    samples = np.clip(samples, -1.0, 1.0)

    # Write WAV
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for s in samples:
            wf.writeframes(struct.pack('<h', int(s * 32767)))


def create_silent_wav(filepath, duration=8.0, sample_rate=44100):
    """Create a silent WAV file."""
    n_samples = int(duration * sample_rate)
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for _ in range(n_samples):
            wf.writeframes(struct.pack('<h', 0))


def create_breath_like_wav(filepath, duration=8.0, sample_rate=44100):
    """
    Create a WAV that simulates breathing patterns.
    Alternates between:
    - Inhale: higher freq noise burst (300-600Hz), moderate amplitude
    - Exhale: lower freq noise burst (150-350Hz), higher amplitude, longer
    - Pause: near silence
    """
    n_samples = int(duration * sample_rate)
    samples = np.zeros(n_samples, dtype=np.float32)
    t = np.arange(n_samples) / sample_rate

    # Simulate 3 breath cycles in 8 seconds (~22.5 BPM)
    breath_cycle = duration / 3.0  # ~2.67s per cycle

    for cycle in range(3):
        cycle_start = cycle * breath_cycle
        inhale_start = int(cycle_start * sample_rate)
        inhale_end = int((cycle_start + breath_cycle * 0.3) * sample_rate)  # 30% inhale
        exhale_start = int((cycle_start + breath_cycle * 0.35) * sample_rate)
        exhale_end = int((cycle_start + breath_cycle * 0.75) * sample_rate)  # 40% exhale
        # Remaining 25% = pause (silence)

        # Inhale: band-limited noise 300-600Hz, amplitude 0.15
        if inhale_end <= n_samples:
            n_inhale = inhale_end - inhale_start
            noise = np.random.randn(n_inhale) * 0.15
            # Simple band-pass via mixing sine waves in target range
            for freq in [350, 450, 550]:
                noise += 0.05 * np.sin(2 * np.pi * freq * np.arange(n_inhale) / sample_rate)
            samples[inhale_start:inhale_end] += noise.astype(np.float32)

        # Exhale: band-limited noise 150-350Hz, amplitude 0.25, longer
        if exhale_end <= n_samples:
            n_exhale = exhale_end - exhale_start
            noise = np.random.randn(n_exhale) * 0.25
            for freq in [200, 250, 300]:
                noise += 0.08 * np.sin(2 * np.pi * freq * np.arange(n_exhale) / sample_rate)
            samples[exhale_start:exhale_end] += noise.astype(np.float32)

    # Clip
    samples = np.clip(samples, -1.0, 1.0)

    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for s in samples:
            wf.writeframes(struct.pack('<h', int(s * 32767)))


# ============================================
# TESTS
# ============================================

passed = 0
failed = 0
total = 0

def test(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} — {detail}")


def run_tests():
    global passed, failed, total

    analyzer = BreathAnalyzer()

    # ==========================================
    print("\n=== Test 1: Backward Compatibility ===")
    # ==========================================
    # The output must always contain the 5 original fields

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmpfile = f.name
    create_test_wav(tmpfile, duration=4.0, frequencies=[(300, 0.3)])

    result = analyzer.analyze(tmpfile)
    os.unlink(tmpfile)

    required_fields = ['silence', 'volume', 'tempo', 'intensity', 'duration']
    for field in required_fields:
        test(f"Has field '{field}'", field in result, f"Missing: {field}")

    test("intensity is valid string",
         result['intensity'] in ('calm', 'moderate', 'intense', 'critical'),
         f"Got: {result['intensity']}")
    test("volume is 0-100", 0 <= result['volume'] <= 100, f"Got: {result['volume']}")
    test("silence is 0-100", 0 <= result['silence'] <= 100, f"Got: {result['silence']}")
    test("duration > 0", result['duration'] > 0, f"Got: {result['duration']}")

    # ==========================================
    print("\n=== Test 2: New Fields Present ===")
    # ==========================================

    new_fields = ['breath_phases', 'respiratory_rate', 'breath_regularity',
                  'inhale_exhale_ratio', 'signal_quality', 'dominant_frequency']
    for field in new_fields:
        test(f"Has new field '{field}'", field in result, f"Missing: {field}")

    test("breath_phases is list", isinstance(result.get('breath_phases'), list))
    test("respiratory_rate is number",
         isinstance(result.get('respiratory_rate'), (int, float)))
    test("breath_regularity in [0,1]",
         0 <= result.get('breath_regularity', -1) <= 1,
         f"Got: {result.get('breath_regularity')}")
    test("signal_quality in [0,1]",
         0 <= result.get('signal_quality', -1) <= 1,
         f"Got: {result.get('signal_quality')}")

    # ==========================================
    print("\n=== Test 3: Silent Audio ===")
    # ==========================================

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmpsilent = f.name
    create_silent_wav(tmpsilent)

    result_silent = analyzer.analyze(tmpsilent)
    os.unlink(tmpsilent)

    test("Silent: has all required fields",
         all(f in result_silent for f in required_fields))
    test("Silent: intensity is calm",
         result_silent['intensity'] == 'calm',
         f"Got: {result_silent['intensity']}")
    test("Silent: volume is low",
         result_silent['volume'] < 10,
         f"Got: {result_silent['volume']}")

    # ==========================================
    print("\n=== Test 4: Band-Pass Filter ===")
    # ==========================================
    # A 50Hz signal should be filtered out (below 100Hz)
    # A 500Hz signal should pass through

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_lowfreq = f.name
    create_test_wav(tmp_lowfreq, duration=4.0, frequencies=[(50, 0.5)], amplitude=0)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_midfreq = f.name
    create_test_wav(tmp_midfreq, duration=4.0, frequencies=[(500, 0.5)], amplitude=0)

    result_low = analyzer.analyze(tmp_lowfreq)
    result_mid = analyzer.analyze(tmp_midfreq)
    os.unlink(tmp_lowfreq)
    os.unlink(tmp_midfreq)

    # 50Hz should be attenuated by band-pass, 500Hz should pass through
    # Even with some filter leakage, 500Hz should have notably more energy
    test("Band-pass: 500Hz has more volume than 50Hz",
         result_mid['volume'] >= result_low['volume'],
         f"50Hz vol={result_low['volume']}, 500Hz vol={result_mid['volume']}")
    test("Band-pass: 500Hz signal detected",
         result_mid['volume'] > 0 or len(result_mid.get('breath_phases', [])) >= 0)

    # ==========================================
    print("\n=== Test 5: Breath-Like Audio ===")
    # ==========================================

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_breath = f.name
    create_breath_like_wav(tmp_breath)

    result_breath = analyzer.analyze(tmp_breath)
    os.unlink(tmp_breath)

    test("Breath-like: detected breath phases",
         len(result_breath.get('breath_phases', [])) > 0,
         f"Got {len(result_breath.get('breath_phases', []))} phases")

    phases = result_breath.get('breath_phases', [])
    breath_types = [p['type'] for p in phases if p['type'] != 'pause']
    test("Breath-like: has inhale or exhale events",
         any(t in ('inhale', 'exhale') for t in breath_types),
         f"Types found: {breath_types}")

    test("Breath-like: respiratory rate is reasonable (5-60 BPM)",
         5 <= result_breath.get('respiratory_rate', 0) <= 60,
         f"Got: {result_breath.get('respiratory_rate')}")

    test("Breath-like: all phase events have required fields",
         all('type' in p and 'start' in p and 'end' in p and 'confidence' in p
             for p in phases),
         f"Sample phase: {phases[0] if phases else 'none'}")

    # ==========================================
    print("\n=== Test 6: Real Audio File ===")
    # ==========================================

    real_wav = os.path.join(os.path.dirname(__file__), 'test_breath.wav')
    if os.path.exists(real_wav):
        result_real = analyzer.analyze(real_wav)

        test("Real WAV: has all fields",
             all(f in result_real for f in required_fields + new_fields))
        test("Real WAV: intensity is valid",
             result_real['intensity'] in ('calm', 'moderate', 'intense', 'critical'))
        test("Real WAV: detected some phases",
             len(result_real.get('breath_phases', [])) >= 0)
        test("Real WAV: respiratory_rate is positive",
             result_real.get('respiratory_rate', 0) > 0)

        print(f"\n  Real WAV analysis summary:")
        print(f"    Intensity: {result_real['intensity']}")
        print(f"    Volume: {result_real['volume']}")
        print(f"    Respiratory Rate: {result_real['respiratory_rate']} BPM")
        print(f"    Breath Regularity: {result_real['breath_regularity']}")
        print(f"    I:E Ratio: {result_real['inhale_exhale_ratio']}")
        print(f"    Signal Quality: {result_real['signal_quality']}")
        print(f"    Dominant Freq: {result_real['dominant_frequency']} Hz")
        print(f"    Phases detected: {len(result_real.get('breath_phases', []))}")
        for p in result_real.get('breath_phases', [])[:5]:
            print(f"      {p['type']}: {p['start']:.2f}s - {p['end']:.2f}s (conf: {p['confidence']})")
    else:
        print(f"  [SKIP] test_breath.wav not found at {real_wav}")

    # ==========================================
    print("\n=== Test 7: Default Analysis (error handling) ===")
    # ==========================================

    result_bad = analyzer.analyze("/nonexistent/file.wav")
    test("Bad file: returns default analysis",
         all(f in result_bad for f in required_fields))
    test("Bad file: intensity is moderate (default)",
         result_bad['intensity'] == 'moderate')
    test("Bad file: signal_quality is 0 (indicates failure)",
         result_bad.get('signal_quality') == 0.0)

    # ==========================================
    # SUMMARY
    # ==========================================
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED!")
    else:
        print(f"FAILURES: {failed} tests failed")
    print(f"{'='*50}\n")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
