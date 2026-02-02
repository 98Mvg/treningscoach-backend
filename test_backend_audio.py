import requests
import time

print("🧪 Testing backend audio generation...")
print()

# Test 1: Health check
print("1️⃣ Testing health endpoint...")
response = requests.get("http://localhost:10000/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
print()

# Test 2: Continuous coaching endpoint (simpler than full coach)
print("2️⃣ Testing continuous coaching with cached phrase...")
print("   Using phrase: 'Perfect!' (should be cached)")

# Create minimal test data
data = {
    'session_id': 'test123',
    'phase': 'warmup',
    'last_coaching': '',
    'elapsed_seconds': '10'
}

# Use a dummy audio file
with open('backend/voices/coach_voice.wav', 'rb') as f:
    files = {'audio': ('test.wav', f, 'audio/wav')}
    
    print("   Sending request...")
    start = time.time()
    response = requests.post(
        "http://localhost:10000/coach/continuous",
        files=files,
        data=data,
        timeout=30
    )
    elapsed = time.time() - start
    
    print(f"   Status: {response.status_code}")
    print(f"   Time: {elapsed:.1f}s")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {result}")
        
        if 'voice_url' in result:
            print()
            print(f"3️⃣ Testing voice download...")
            voice_url = "http://localhost:10000" + result['voice_url']
            print(f"   URL: {voice_url}")
            
            audio_response = requests.get(voice_url)
            print(f"   Status: {audio_response.status_code}")
            print(f"   Size: {len(audio_response.content)} bytes")
            
            # Save and try to play
            with open('/tmp/test_voice.wav', 'wb') as af:
                af.write(audio_response.content)
            print(f"   Saved to: /tmp/test_voice.wav")
            print()
            print("▶️  Playing audio...")
            import os
            os.system("afplay /tmp/test_voice.wav")
    else:
        print(f"   Error: {response.text}")

