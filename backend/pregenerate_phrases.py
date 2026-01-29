#!/usr/bin/env python3
"""
Pre-generate common coaching phrases to cache
Run this once, then use cached audio files for instant playback
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tts_service import synthesize_speech, initialize_tts
import time

# Common coaching phrases by intensity (Norwegian + English)
PHRASES = {
    "calm": [
        "God rytme.",
        "Fortsett sånn.",
        "Perfekt.",
        "Bra jobbet.",
        "Good pace.",
        "Keep going.",
        "Perfect.",
        "Well done."
    ],
    "moderate": [
        "Øk tempoet.",
        "Push litt hardere.",
        "God innsats.",
        "Fortsett!",
        "Increase pace.",
        "Push harder.",
        "Good effort.",
        "Continue!"
    ],
    "intense": [
        "Push!",
        "Fortsett!",
        "Yes!",
        "Ti til!",
        "Gi alt!",
        "Ja!",
        "Ten more!",
        "Give it all!",
        "Keep pushing!"
    ],
    "critical": [
        "Stopp.",
        "Pust rolig.",
        "Ta en pause.",
        "Senk tempoet.",
        "Stop.",
        "Breathe slowly.",
        "Take a break.",
        "Slow down."
    ]
}

def main():
    print("🎙️  Pre-generating coaching phrases...")
    print("⚠️  This will take ~2 hours on CPU for all phrases")
    print("    (32 phrases × ~4 minutes each)")
    print("")
    print("💡 Tip: Let this run overnight or during lunch")
    print("    Once done, all phrases will be INSTANT!")
    print("")

    # Initialize TTS first
    print("Initializing TTS model...")
    initialize_tts()
    print("✅ TTS ready!")
    print("")

    total = sum(len(phrases) for phrases in PHRASES.values())
    count = 0

    start_time = time.time()

    for intensity, phrases in PHRASES.items():
        print(f"\n{intensity.upper()}:")
        for phrase in phrases:
            count += 1
            print(f"  [{count}/{total}] Generating: '{phrase}'...")

            phrase_start = time.time()
            audio_path = synthesize_speech(phrase)
            phrase_time = time.time() - phrase_start

            print(f"      ✅ {audio_path} ({phrase_time:.1f}s)")

    total_time = time.time() - start_time
    print(f"\n🎉 Done! Generated {total} phrases in {total_time/60:.1f} minutes")
    print(f"   Average: {total_time/total:.1f}s per phrase")

if __name__ == "__main__":
    main()
