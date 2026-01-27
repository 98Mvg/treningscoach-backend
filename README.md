# 🏋️ Treningscoach Backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Deployed on Render](https://img.shields.io/badge/Deployed-Render-46E3B7.svg)](https://render.com/)

Backend for iOS voice-coaching app that analyzes breathing patterns and provides real-time coaching feedback.

## 🚀 Live URL

Production: **https://treningscoach-backend.onrender.com**

## ✨ Features

- 🎤 **Audio Analysis** - Analyzes breathing patterns from audio recordings
- 🏃 **Intensity Detection** - Classifies workout intensity (rolig, moderat, hard, kritisk)
- 💬 **Coach Feedback** - Provides motivational coaching responses
- 🔊 **Voice Generation** - Mock voice output (ready for PersonaPlex integration)
- 🌐 **CORS Enabled** - Ready for iOS app integration
- 📊 **Logging** - Comprehensive logging for monitoring and debugging

## 📋 API Endpoints

### `GET /`
Home page with API documentation

**Response:** HTML page

---

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "timestamp": "2026-01-27T...",
  "endpoints": {
    "analyze": "/analyze",
    "coach": "/coach",
    "download": "/download/<filename>"
  }
}
```

---

### `POST /analyze`
Analyze audio recording and return breathing data

**Parameters:**
- `audio` (file) - Audio file (WAV/MP3/M4A, max 10MB)

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

**Example:**
```bash
curl -X POST \
  -F "audio=@recording.wav" \
  https://treningscoach-backend.onrender.com/analyze
```

---

### `POST /coach`
Get coaching feedback based on audio analysis

**Parameters:**
- `audio` (file) - Audio file (WAV/MP3/M4A, max 10MB)
- `phase` (string) - Workout phase: `warmup`, `intense`, or `cooldown` (default: `intense`)

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
  "audio_url": "/download/coach_1234567890.123.mp3",
  "phase": "intense"
}
```

**Example:**
```bash
curl -X POST \
  -F "audio=@recording.wav" \
  -F "phase=intense" \
  https://treningscoach-backend.onrender.com/coach
```

---

### `GET /download/<filename>`
Download generated voice file

**Response:** Audio file (MP3)

**Example:**
```bash
curl https://treningscoach-backend.onrender.com/download/coach_1234567890.123.mp3 -o output.mp3
```

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/98Mvg/treningscoach-backend.git
cd treningscoach-backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
# Development mode (port 5001 to avoid AirPlay conflict on macOS)
PORT=5001 python main.py

# Or with debug mode disabled
PORT=5001 DEBUG=false python main.py
```

4. Access the API:
```
http://localhost:5001
```

---

## 📦 Deployment

### Render (Recommended)

1. Push code to GitHub
2. Connect Render to your GitHub repository
3. Configure build settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app`
   - **Environment:** Python 3
4. Deploy!

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `5000` |
| `DEBUG` | Enable debug mode | `False` |

---

## 🏗️ Project Structure

```
treningscoach-backend/
├── main.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── Procfile            # Render deployment config
├── runtime.txt         # Python version specification
├── README.md           # This file
├── DEPLOYMENT.md       # Deployment guide and iOS integration
├── .gitignore          # Git ignore rules
├── uploads/            # Temporary audio uploads (gitignored)
└── outputs/            # Generated voice files (gitignored)
```

---

## 🔧 Configuration

### File Size Limits
- Maximum upload size: 10MB

### Supported Audio Formats
- WAV
- MP3
- M4A

### Workout Phases
- `warmup` - Gentle coaching for warm-up
- `intense` - Motivational coaching for intense workout
- `cooldown` - Calming coaching for cool-down

### Intensity Levels
- `rolig` - Calm breathing
- `moderat` - Moderate intensity
- `hard` - High intensity
- `kritisk` - Critical (safety message triggered)

---

## 📱 iOS Integration

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete iOS integration guide with Swift code examples.

**Quick Start:**
```swift
let backendURL = "https://treningscoach-backend.onrender.com"
```

---

## 🔄 Updating the Backend

```bash
# Make changes to code
git add .
git commit -m "Description of changes"
git push

# Render will automatically redeploy
```

---

## 📊 Monitoring

View logs on Render dashboard:
1. Go to your Render service
2. Click "Logs" tab
3. Monitor real-time activity

---

## 🐛 Troubleshooting

**Backend sleeping?**
- Free tier sleeps after 15 minutes of inactivity
- First request may take 30-60 seconds to wake up

**Getting 400 errors?**
- Verify audio file is valid format (WAV/MP3/M4A)
- Check file size is under 10MB
- Ensure form-data is correctly formatted

**CORS issues?**
- CORS is enabled for all origins
- Verify request headers are correct

---

## 📝 Version History

### v1.1.0 (2026-01-27)
- Added CORS support for iOS integration
- Improved error handling and logging
- Added file size validation
- Enhanced security (directory traversal prevention)
- Better HTML home page
- Comprehensive API documentation

### v1.0.0 (2026-01-27)
- Initial release
- Basic audio analysis
- Coach response generation
- Mock voice output

---

## 🔮 Roadmap

- [ ] Integrate PersonaPlex API for real voice generation
- [ ] Add authentication/API keys
- [ ] Implement rate limiting
- [ ] Add webhook support for async processing
- [ ] Create analytics dashboard
- [ ] Support for multiple languages

---

## 📄 License

This project is private and proprietary.

---

## 👤 Author

**Marius Gaarder**
- GitHub: [@98Mvg](https://github.com/98Mvg)

---

## 🆘 Support

For issues and questions:
1. Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide
2. Review Render logs for errors
3. Test endpoints with curl examples above

---

**Made with ❤️ for iOS Treningscoach App**
