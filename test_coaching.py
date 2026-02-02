import requests

print("🧪 Testing voice coaching...")

# Send same audio multiple times to trigger coaching
data = {
    'session_id': 'test456',
    'phase': 'intense',  # Intense phase = more likely to coach
    'last_coaching': '',
    'elapsed_seconds': '300'  # 5 minutes in
}

with open('backend/voices/coach_voice.wav', 'rb') as f:
    files = {'audio': ('test.wav', f, 'audio/wav')}
    
    print("Sending request (intense phase)...")
    response = requests.post(
        "http://localhost:10000/coach/continuous",
        files=files,
        data=data,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Should speak: {result['should_speak']}")
    print(f"Text: {result['text']}")
    print(f"Audio URL: {result['audio_url']}")
    
    if result['audio_url']:
        print("\n✅ Got voice URL! Downloading and playing...")
        voice_url = "http://localhost:10000" + result['audio_url']
        audio = requests.get(voice_url)
        with open('/tmp/coach_test.wav', 'wb') as af:
            af.write(audio.content)
        print(f"Saved to: /tmp/coach_test.wav ({len(audio.content)} bytes)")
        
        import os
        print("\n🔊 Playing...")
        os.system("afplay /tmp/coach_test.wav")
        print("✅ Done!")
    else:
        print(f"\n⚠️ No audio - reason: {result['reason']}")

