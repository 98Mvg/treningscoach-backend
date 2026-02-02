import requests
import uuid

print("🧪 Testing first breath welcome message...")

# Create a NEW session ID to trigger welcome
session_id = f"test_session_{uuid.uuid4().hex[:8]}"
print(f"New session: {session_id}")

data = {
    'session_id': session_id,
    'phase': 'warmup',
    'last_coaching': '',
    'elapsed_seconds': '5'  # Just started
}

with open('backend/voices/coach_voice.wav', 'rb') as f:
    files = {'audio': ('test.wav', f, 'audio/wav')}
    
    print("Sending first breath...")
    response = requests.post(
        "http://localhost:10000/coach/continuous",
        files=files,
        data=data,
        timeout=30
    )
    
    result = response.json()
    print(f"\n✅ Response:")
    print(f"  Should speak: {result['should_speak']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Text: {result['text']}")
    print(f"  Audio URL: {result.get('audio_url', 'None')}")
    
    if result.get('audio_url'):
        print("\n🔊 Downloading and playing...")
        voice_url = "http://localhost:10000" + result['audio_url']
        audio = requests.get(voice_url)
        with open('/tmp/welcome.wav', 'wb') as af:
            af.write(audio.content)
        print(f"  Saved: {len(audio.content)} bytes")
        
        import os
        os.system("afplay /tmp/welcome.wav")
        print("  ✅ Played!")
    else:
        print("\n⚠️ No audio generated")

