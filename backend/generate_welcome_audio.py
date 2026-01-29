#!/usr/bin/env python3
"""
Generate welcome message audio files for TreningsCoach.

This pre-generates all welcome messages so they're ready instantly
when the user starts a workout (no generation delay).
"""

import os
from dotenv import load_dotenv
from elevenlabs_tts import ElevenLabsTTS
import config
import hashlib

# Load environment variables
load_dotenv()

def get_cache_filename(text):
    """Generate consistent cache filename from text"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return f"cached_{text_hash}.wav"

def main():
    # Initialize ElevenLabs
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        print("❌ Error: ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID not set in .env")
        return

    tts = ElevenLabsTTS(api_key=api_key, voice_id=voice_id)

    # Create cache directory
    cache_dir = os.path.join(os.path.dirname(__file__), 'output', 'cache')
    os.makedirs(cache_dir, exist_ok=True)

    print(f"🎙️ Generating welcome audio files...")
    print(f"📁 Output directory: {cache_dir}\n")

    # Collect all unique welcome messages
    all_messages = []
    for category, messages in config.WELCOME_MESSAGES.items():
        for msg in messages:
            if msg not in all_messages:
                all_messages.append(msg)

    total = len(all_messages)
    generated = 0
    skipped = 0
    errors = 0

    # Generate audio for each message
    for i, message in enumerate(all_messages, 1):
        cache_filename = get_cache_filename(message)
        output_path = os.path.join(cache_dir, cache_filename)

        # Skip if already exists
        if os.path.exists(output_path):
            print(f"[{i}/{total}] ⏭️  Skipped (exists): '{message[:50]}...'")
            skipped += 1
            continue

        try:
            print(f"[{i}/{total}] 🔊 Generating: '{message}'")
            tts.generate_audio(message, output_path)
            print(f"         ✅ Saved: {cache_filename}")
            generated += 1

        except Exception as e:
            print(f"         ❌ Error: {e}")
            errors += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 Welcome audio generation complete!")
    print(f"{'='*60}")
    print(f"✅ Generated: {generated}")
    print(f"⏭️  Skipped: {skipped}")
    if errors > 0:
        print(f"❌ Errors: {errors}")
    print(f"📊 Total messages: {total}")
    print(f"📁 Location: {cache_dir}")
    print(f"{'='*60}\n")

    # List generated files
    cache_files = [f for f in os.listdir(cache_dir) if f.startswith('cached_') and f.endswith('.wav')]
    print(f"💾 Total cached files: {len(cache_files)}")

    if generated > 0:
        print(f"\n🚀 Welcome messages are now ready for instant playback!")
        print(f"   Test: curl http://localhost:10000/welcome")

if __name__ == "__main__":
    main()
