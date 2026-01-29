# 🎉 Deployment Complete!

## Your Backend URLs

**Production URL:** https://treningscoach-backend.onrender.com
**GitHub Repository:** https://github.com/98Mvg/treningscoach-backend
**Local Development:** http://localhost:5001

---

## API Endpoints

### GET /
**Purpose:** Home page - verify backend is running
```bash
curl https://treningscoach-backend.onrender.com/
```

### GET /health
**Purpose:** Health check
```bash
curl https://treningscoach-backend.onrender.com/health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T..."
}
```

### POST /analyze
**Purpose:** Analyze audio and return breath data
```bash
curl -X POST \
  -F "audio=@/path/to/audio.wav" \
  https://treningscoach-backend.onrender.com/analyze
```
**Response:**
```json
{
  "stillhet": 50.0,
  "volum": 30.0,
  "tempo": 15.0,
  "intensitet": "moderat",
  "varighet": 2.0
}
```

### POST /coach
**Purpose:** Analyze audio and get coach response with voice URL
```bash
curl -X POST \
  -F "audio=@/path/to/audio.wav" \
  -F "phase=intense" \
  https://treningscoach-backend.onrender.com/coach
```
**Parameters:**
- `audio`: WAV file
- `phase`: "warmup", "intense", or "cooldown"

**Response:**
```json
{
  "text": "PUSH! Hardere!",
  "breath_analysis": {
    "stillhet": 50.0,
    "volum": 30.0,
    "tempo": 15.0,
    "intensitet": "moderat",
    "varighet": 2.0
  },
  "audio_url": "/download/coach_1234567890.123.mp3"
}
```

### GET /download/<filename>
**Purpose:** Download generated voice file
```bash
curl https://treningscoach-backend.onrender.com/download/coach_1234567890.123.mp3 -o output.mp3
```

---

## iOS App Integration

Use this in your Swift code:

```swift
let backendURL = "https://treningscoach-backend.onrender.com"

// Example: Send audio to coach endpoint
func sendAudioToCoach(audioData: Data, phase: String) {
    let url = URL(string: "\(backendURL)/coach")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"

    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

    var body = Data()

    // Add audio file
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"recording.wav\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
    body.append(audioData)
    body.append("\r\n".data(using: .utf8)!)

    // Add phase parameter
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"phase\"\r\n\r\n".data(using: .utf8)!)
    body.append(phase.data(using: .utf8)!)
    body.append("\r\n".data(using: .utf8)!)

    body.append("--\(boundary)--\r\n".data(using: .utf8)!)

    request.httpBody = body

    URLSession.shared.dataTask(with: request) { data, response, error in
        guard let data = data else { return }

        let json = try? JSONDecoder().decode(CoachResponse.self, from: data)
        // Handle response
    }.resume()
}

struct CoachResponse: Codable {
    let text: String
    let breath_analysis: BreathAnalysis
    let audio_url: String
}

struct BreathAnalysis: Codable {
    let stillhet: Double
    let volum: Double
    let tempo: Double
    let intensitet: String
    let varighet: Double
}
```

---

## Updating Your Backend

When you make changes to the code:

```bash
# Navigate to project directory
cd /Users/mariusgaarder/Documents/TreningsCoach-Backend

# Make your changes to main.py or other files
# Then commit and push:

git add .
git commit -m "Description of changes"
git push

# Render will automatically redeploy! 🎉
```

---

## Important Notes

### Free Tier Behavior
- Backend sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- Subsequent requests are fast
- 750 hours/month free (plenty for testing)

### Local Development
To run locally:
```bash
cd /Users/mariusgaarder/Documents/TreningsCoach-Backend
PORT=5001 python3 main.py
```
Access at: http://localhost:5001

### File Structure
```
TreningsCoach-Backend/
├── main.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── Procfile            # Render deployment config
├── README.md           # Project documentation
├── DEPLOYMENT.md       # This file
└── .gitignore          # Git ignore rules
```

---

## Next Steps

1. ✅ Backend deployed and tested
2. 🔜 Build iOS app to send audio
3. 🔜 Integrate PersonaPlex for voice generation
4. 🔜 Test end-to-end flow

---

## Troubleshooting

**Backend not responding?**
- Check Render dashboard for logs
- Verify backend is not sleeping (first request may be slow)

**Getting 400 errors?**
- Verify audio file is valid WAV format
- Check that form-data is correctly formatted

**Need faster response times?**
- Consider upgrading to Render Starter ($7/month)
- Backend won't sleep and will be always-on

---

**Deployment Date:** 2026-01-27
**Status:** ✅ Live and Working
