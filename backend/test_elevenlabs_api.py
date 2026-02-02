import requests
import time

print("🧪 Testing ElevenLabs Integration via API")
print("=" * 50)

# Test continuous coaching endpoint
data = {
    'session_id': f'test_elevenlabs_{int(time.time())}',
    'phase': 'warmup',
    'last_coaching': '',
    'elapsed_seconds': '5'
}

with open('backend/voices/coach_voice.wav', 'rb') as f:
    files = {'audio': ('test.wav', f, 'audio/wav')}
    
    print("Sending request to backend...")
    start = time.time()
    response = requests.post(
        "http://localhost:10000/coach/continuous",
        files=files,
        data=data,
        timeout=30
    )
    elapsed = time.time() - start
    
    print(f"Response time: {elapsed:.1f}s")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nShould speak: {result['should_speak']}")
        print(f"Text: {result['text']}")
        print(f"Audio URL: {result.get('audio_url', 'None')}")
        
        if result.get('audio_url'):
            print("\n🔊 Downloading and playing...")
            voice_url = "http://localhost:10000" + result['audio_url']
            audio = requests.get(voice_url)
            with open('/tmp/elevenlabs_test.mp3', 'wb') as af:
                af.write(audio.content)
            print(f"Saved: {len(audio.content)} bytes")
            
            import os
            os.system("afplay /tmp/elevenlabs_test.mp3")
            print("✅ Played! Did you hear the calm, authoritative coach?")
    else:
        print(f"Error: {response.text}")

