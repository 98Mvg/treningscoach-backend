# Audio Debugging Guide

## Problem: No sound on website or iOS

## ✅ Backend Status (Checked - Working)
- Backend is running on port 10000
- ElevenLabs is initialized
- Audio files are being generated
- Download endpoint works (tested)

## 🔍 Debug Steps

### 1. Test Audio Directly in Browser

**Test if backend is generating audio:**
```
http://127.0.0.1:10000/download/cache/cached_002b211d29dd26cc245c1dbae3448465.wav
```

Open this URL in Safari/Chrome:
- ✅ If you hear audio → Backend is working
- ❌ If no audio → Backend issue (unlikely, files exist)

### 2. Check iOS App Audio Playback

The issue is likely in the iOS app's audio player. Let me check the audio service:

**Common iOS Audio Issues:**

1. **AVAudioSession not configured**
   - Need to set audio session category
   - Need to activate audio session

2. **Volume is muted**
   - Check device volume
   - Check silent mode switch

3. **Audio URL not being fetched**
   - Check network requests in Xcode console
   - Look for 404 or connection errors

4. **AVPlayer not playing**
   - Player might not be retained
   - Playback might fail silently

---

## Quick Fixes

### Fix 1: Test Backend Audio Directly

Open in your browser:
```
http://127.0.0.1:10000/download/cache/cached_002b211d29dd26cc245c1dbae3448465.wav
```

If you hear audio → Backend works, iOS app issue
If no audio → Backend audio generation issue

### Fix 2: Check iOS Audio Service

Look for this in your iOS app code:
- `AVAudioSession.sharedInstance().setCategory(.playback)`
- `AVAudioSession.sharedInstance().setActive(true)`
- `AVPlayer` initialization and playback

### Fix 3: Check iOS Network Requests

In Xcode console, look for:
```
Request: GET /continuous_coach
Response: {"audio_url": "/download/cache/..."}
```

Then look for:
```
Request: GET /download/cache/...
Status: 200
```

If 404 → URL path issue
If no request → App not fetching audio

### Fix 4: Verify iOS Device Settings

1. **Check volume**: Side buttons, Control Center
2. **Check silent mode**: Physical switch on iPhone
3. **Check app permissions**: Settings → TreningsCoach → Allow audio

---

## Backend Audio Test Commands

### Generate Fresh Audio
```bash
# Test ElevenLabs generation
curl -X POST http://127.0.0.1:10000/coach \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good pace. Stay focused.",
    "phase": "intense"
  }'
```

Expected response:
```json
{
  "audio_url": "/download/cache/cached_XXXXX.wav",
  "text": "Good pace. Stay focused."
}
```

### Download and Play the Audio
```bash
# Download the audio file
curl -O http://127.0.0.1:10000/download/cache/cached_002b211d29dd26cc245c1dbae3448465.wav

# Play it (macOS)
afplay cached_002b211d29dd26cc245c1dbae3448465.wav
```

If you hear it → Backend is 100% working

---

## iOS App Audio Service Check

Look at your `AudioService.swift` or wherever audio playback happens.

**Required for iOS audio playback:**

```swift
import AVFoundation

class AudioService {
    private var player: AVPlayer?

    init() {
        // Configure audio session
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            print("Failed to setup audio session: \\(error)")
        }
    }

    func playAudio(from urlString: String) {
        guard let url = URL(string: urlString) else {
            print("Invalid audio URL: \\(urlString)")
            return
        }

        // Create player
        player = AVPlayer(url: url)

        // Observe when playback finishes
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(playerDidFinishPlaying),
            name: .AVPlayerItemDidPlayToEndTime,
            object: player?.currentItem
        )

        // Play
        player?.play()
        print("▶️ Playing audio from: \\(urlString)")
    }

    @objc func playerDidFinishPlaying() {
        print("✅ Audio finished playing")
    }
}
```

**Key points:**
1. `setCategory(.playback)` - Allow audio even when silent switch is on
2. `setActive(true)` - Activate the audio session
3. Keep `player` reference - Don't let it get deallocated

---

## Common Mistakes

### ❌ Mistake 1: Player gets deallocated
```swift
func playAudio(url: String) {
    let player = AVPlayer(url: URL(string: url)!)
    player.play()
    // Player is deallocated immediately - no sound!
}
```

### ✅ Fix: Keep player as property
```swift
class AudioService {
    private var player: AVPlayer?  // Property, not local variable

    func playAudio(url: String) {
        player = AVPlayer(url: URL(string: url)!)
        player?.play()
    }
}
```

### ❌ Mistake 2: No audio session setup
```swift
// Missing:
try AVAudioSession.sharedInstance().setCategory(.playback)
try AVAudioSession.sharedInstance().setActive(true)
```

### ❌ Mistake 3: Wrong URL format
```swift
// Backend returns: "/download/cache/file.wav"
// Need to prepend base URL:
let fullURL = "http://127.0.0.1:10000/download/cache/file.wav"
```

---

## Debug Checklist

### Backend (Already Verified ✅)
- [x] Backend running on port 10000
- [x] ElevenLabs initialized
- [x] Audio files exist in output/cache/
- [x] Download endpoint returns 200

### iOS App (Need to Check)
- [ ] App connects to backend at localhost:10000
- [ ] App receives audio_url in response
- [ ] App fetches audio from download endpoint
- [ ] AVAudioSession is configured
- [ ] AVPlayer is retained (not deallocated)
- [ ] Device volume is up
- [ ] Silent mode is off

### Quick iOS Test
1. Build and run app
2. Start workout
3. Watch Xcode console for:
   - "Request: /continuous_coach" ✅
   - "Response: audio_url = /download/..." ✅
   - "Playing audio from: http://..." ✅
   - "Audio finished playing" ✅

If you see all 4 → Audio should work
If missing → That's where the problem is

---

## Next Steps

### 1. Test Backend Audio (30 seconds)
```bash
# Download and play a cached file
curl -O http://127.0.0.1:10000/download/cache/cached_002b211d29dd26cc245c1dbae3448465.wav
afplay cached_002b211d29dd26cc245c1dbae3448465.wav
```

If you hear it → Backend is perfect ✅

### 2. Test in Browser (10 seconds)
Open: `http://127.0.0.1:10000/download/cache/cached_002b211d29dd26cc245c1dbae3448465.wav`

If you hear it → Backend is perfect ✅

### 3. Check iOS App Code
Look for:
- AVAudioSession setup
- AVPlayer initialization
- Audio URL construction
- Console logs for playback

### 4. Common iOS Fix
Add this to your audio service init:
```swift
do {
    try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
    try AVAudioSession.sharedInstance().setActive(true)
} catch {
    print("Audio session error: \\(error)")
}
```

---

## Most Likely Issue

**90% chance it's one of these:**

1. **AVAudioSession not configured** → Add `.setCategory(.playback)`
2. **Silent mode ON** → Flip switch on side of iPhone
3. **AVPlayer deallocated** → Make it a class property
4. **Wrong URL** → Need full URL: `http://127.0.0.1:10000/download/...`

**Test backend first (30 sec) to confirm it's working, then focus on iOS app.**

---

## Get Help

If still not working, share:
1. Result of browser test (does audio play?)
2. iOS Xcode console logs (when starting workout)
3. Any error messages

Backend is working ✅ - Focus on iOS audio playback.
