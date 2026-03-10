<p align="center">
  <img src="TreningsCoach/TreningsCoach/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png" width="120" alt="Coachi Logo">
</p>

<h1 align="center">Coachi</h1>

<p align="center">
  <strong>AI-Powered Real-Time Workout Coach</strong><br>
  Voice-guided training with breath analysis, adaptive personas, and multilingual support
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue" alt="Version 3.0.0">
  <img src="https://img.shields.io/badge/platform-iOS%2017%2B-black" alt="iOS 17+">
  <img src="https://img.shields.io/badge/backend-Flask%20on%20Render-green" alt="Flask on Render">
  <img src="https://img.shields.io/badge/TTS-ElevenLabs-purple" alt="ElevenLabs TTS">
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20NO%20%7C%20DA-orange" alt="EN | NO | DA">
</p>

---

## Codebase Guide

- Primary architecture guide: [CODEBASE_GUIDE.md](/Users/mariusgaarder/Documents/treningscoach/CODEBASE_GUIDE.md)
- Regenerate after architecture/runtime changes:

```bash
python3 scripts/generate_codebase_guide.py
pytest -q tests_phaseb/test_codebase_guide_sync.py
```

## 📁 Project Structure

```
treningscoach/
├── main.py                        # Production Flask app (Render deploys from root)
├── config.py                      # Central config: thresholds, messages, brain settings
├── brain_router.py                # AI provider routing with priority fallback
├── breath_analyzer.py             # Librosa DSP for breath metrics
├── elevenlabs_tts.py              # ElevenLabs TTS (eleven_flash_v2_5)
├── locale_config.py               # Language/voice/locale single source of truth
├── persona_manager.py             # Coach personas + emotional progression
├── coaching_engine.py             # Text validation, anti-repetition, template anchors
├── breathing_timeline.py          # 5-phase breathing guidance (prep→cooldown)
├── coaching_intelligence.py       # Pattern detection + strategic insights
├── brains/                        # AI provider adapters
│   ├── base_brain.py              # Abstract base class
│   ├── grok_brain.py              # xAI Grok (default — cheapest)
│   ├── gemini_brain.py            # Google Gemini
│   ├── openai_brain.py            # OpenAI GPT
│   └── claude_brain.py            # Anthropic Claude
│
├── backend/                       # Legacy tooling/docs; runtime source of truth is ROOT
│   ├── main.py                    # Compatibility shim -> imports root main.py
│   └── ...
│
├── TreningsCoach/                 # iOS app (SwiftUI)
│   └── TreningsCoach/
│       ├── App/                   # Entry point, root navigation
│       ├── Views/                 # All SwiftUI views
│       ├── ViewModels/            # Workout + app state management
│       ├── Services/              # Audio, API, wake word, auth
│       ├── Theme/                 # CoachiTheme "Midnight Ember" design system
│       ├── Localization/          # L10n.swift (EN + NO bilingual strings)
│       └── Models/                # Data models
│
├── Procfile                       # Gunicorn config for Render
└── requirements.txt               # Python dependencies
```

Production and local Flask runtime source of truth is `/Users/mariusgaarder/Documents/treningscoach/main.py`.

## 🎯 System Overview

Coachi is a real-time AI workout coach that listens to your breathing, analyzes effort intensity, and delivers voice-guided coaching — adapting tone, language, and personality to your workout phase.

### Architecture

```
iOS App (SwiftUI)
  ↓ HTTP POST /coach/continuous (6-10s audio chunks)
Backend (Flask on Render)
  ↓ breath_analyzer.py → breath metrics (librosa DSP)
  ↓ brain_router.py → picks AI brain (grok → gemini → openai → claude → config)
  ↓ persona_manager.py → emotional mode + persona
  ↓ coaching_engine.py → validates + anchors coaching text
  ↓ elevenlabs_tts.py → text-to-speech (eleven_flash_v2_5)
  ↑ Returns audio URL to iOS
iOS App plays coaching audio
```

**Key design**: The iOS app never knows which AI provider is active. The Brain Router abstracts all provider selection, fallback, and timeout handling.

### Talk Safety Policy

- `/coach/talk` strict safety categories, refusal banks, and rotation behavior are documented in:
  `/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-05-talk-safety-rules-integration.md`

### Final Launch Gate (Watch)

- Final pre-live watch hardware gate checklist (what is already prepared vs. what must pass on real devices):
  `/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-05-final-step-before-live-launch-watch-gate.md`

### Brain Priority Chain

```
grok (provider timeout via `BRAIN_TIMEOUTS_JSON`, default 6.0s) → gemini → openai → claude → config (static messages)
```

If all AI brains fail, `config.py` has static coaching message banks in all languages — the app never goes silent.

### Coaching Timeline

```
PREP (safety + countdown) → WARMUP (4-4 breathing) → INTENSE (power) → RECOVERY (4-6) → COOLDOWN (4-7)
```

Active at all times. Each phase has breathing patterns, cue intervals, and bilingual message banks.

## 📋 Features

### Backend (Python/Flask)

- **30 non-static API routes** — coaching, chat, web funnel, auth, and observability
- **Multi-brain AI routing** — Grok, Gemini, OpenAI, Claude with priority fallback + timeout
- **Real-time breath analysis** — librosa DSP: volume, tempo, respiratory rate, intensity
- **ElevenLabs TTS** — `eleven_flash_v2_5` model, per-persona voices, Norwegian Bokmål support
- **2 coach personas** — Personal Trainer (calm discipline) + Toxic Mode (drill sergeant humor)
- **Emotional progression** — supportive → pressing → intense → peak (per persona)
- **Coaching text validation** — length, forbidden phrases, language check, tone match
- **5-phase breathing timeline** — prep, warmup, intense, recovery, cooldown
- **Safety interrupts** — "can't breathe", "dizzy", "slow down" → immediate safety response
- **Brain observability** — per-brain call stats, latency tracking, cooldown management
- **3 languages** — English, Norwegian (Bokmål), Danish

### iOS App (Swift/SwiftUI)

- **"Midnight Ember" design system** — CoachiTheme with dark gradients and ember accents
- **Animated coaching orb** — idle/listening/speaking states with fluid animations
- **Continuous audio recording** — 6-10s chunks sent to backend in real-time
- **Workout state machine** — idle → active ↔ paused → complete
- **Onboarding flow** — Welcome → Language → Features → Setup
- **Bilingual UI** — L10n.swift with EN + NO strings
- **Persona selection** — choose coach personality before workout
- **Wake word support** — talk to coach mid-workout
- **Workout history** — save and review completed sessions

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| Framework | Flask 3.0 |
| Audio Analysis | librosa + numpy |
| AI Providers | Grok (xAI), Gemini, OpenAI, Claude |
| Text-to-Speech | ElevenLabs (`eleven_flash_v2_5`) |
| Hosting | Render (auto-deploy from GitHub) |
| Process Manager | Gunicorn (2 workers, 120s timeout) |

### iOS
| Component | Technology |
|-----------|-----------|
| Language | Swift 5.9 |
| Framework | SwiftUI |
| Audio | AVFoundation |
| Min iOS | 17.0+ |
| Architecture | MVVM |
| Design System | CoachiTheme ("Midnight Ember") |

## 🚀 Quick Start

### Backend

```bash
# Install dependencies
pip3 install -r requirements.txt

# Set required env vars
export ELEVENLABS_API_KEY="your_key"
export ELEVENLABS_VOICE_ID="your_english_voice_id"
export XAI_API_KEY="your_grok_key"

# Run locally
PORT=5001 python3 main.py
```

### iOS

```bash
open TreningsCoach/TreningsCoach.xcodeproj
# Press Cmd+R in Xcode to build and run
```

### iOS Signing Notes (Personal Team-safe)

- `APPLE_SIGN_IN_ENABLED` is `0` by default in
  `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Info.plist`.
- Apple Sign-In UI is feature-flagged off in this mode.
- Entitlements source of truth is
  `/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/TreningsCoach.entitlements`.
- Strict signing is enforced in project settings (`CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION = NO`).

### Verify

```bash
# Health check
curl http://localhost:5001/health

# Test welcome
curl "http://localhost:5001/welcome?language=en&persona=personal_trainer"

# Check brain status
curl http://localhost:5001/brain/health
```

### Web Variant Compare (Claude vs Codex)

```bash
# Set root page variant (default: codex)
export WEB_UI_VARIANT=claude   # or codex

# Start backend
PORT=5001 python3 main.py
```

- `GET /?variant=claude` → Force Claude page for this request
- `GET /?variant=codex` → Force Codex page for this request
- `GET /preview/claude` → Direct Claude preview
- `GET /preview/codex` → Direct Codex preview
- `GET /preview` → Side-by-side A/B compare page

## 🌐 Production

- **Backend API:** https://treningscoach-backend.onrender.com
- **Health Check:** https://treningscoach-backend.onrender.com/health
- **Brain Status:** https://treningscoach-backend.onrender.com/brain/health

## ☁️ Cloudflare Worker Edge Proxy

Cloudflare deploy source of truth is now versioned in git:

- `/Users/mariusgaarder/Documents/treningscoach/wrangler.toml`
- `/Users/mariusgaarder/Documents/treningscoach/cloudflare/worker.js`
- `/Users/mariusgaarder/Documents/treningscoach/package.json`
- guide: [/Users/mariusgaarder/Documents/treningscoach/docs/CLOUDFLARE_DEPLOY_SOURCE_OF_TRUTH.md](/Users/mariusgaarder/Documents/treningscoach/docs/CLOUDFLARE_DEPLOY_SOURCE_OF_TRUTH.md)

## 📊 API Endpoints

### Main App Routes (`main.py`)

| # | Method | Route | Purpose |
|---|--------|-------|---------|
| 1 | GET | `/` | Web interface (variant-resolved) |
| 2 | GET | `/preview` | Side-by-side web variant compare |
| 3 | GET | `/preview/<variant>` | Direct web variant preview |
| 4 | GET | `/health` | Health check + version |
| 5 | GET | `/tts/cache/stats` | TTS cache observability |
| 6 | GET | `/welcome` | Welcome message + TTS audio |
| 7 | POST | `/analyze` | Analyze breath audio |
| 8 | POST | `/coach/continuous` | **Main endpoint** — deterministic continuous workout coaching |
| 9 | POST | `/coach/talk` | Talk to coach (wake word/chat) |
| 10 | POST | `/coach/persona` | Switch persona mid-workout |
| 11 | GET | `/download/<path:filename>` | Download audio files |
| 12 | GET | `/brain/health` | Brain status + per-brain stats |
| 13 | POST | `/brain/switch` | Hot-swap AI brain |
| 14 | POST | `/chat/start` | Create chat session |
| 15 | POST | `/chat/stream` | Streaming chat (SSE) |
| 16 | POST | `/chat/message` | Non-streaming chat |
| 17 | GET | `/chat/sessions` | List sessions |
| 18 | DELETE | `/chat/sessions/<session_id>` | Delete session |
| 19 | GET | `/chat/personas` | List personas |
| 20 | POST | `/workouts` | Save workout record |
| 21 | GET | `/workouts` | Get workout history |
| 22 | POST | `/waitlist` | Capture waitlist email |
| 23 | POST | `/analytics/event` | Capture lightweight landing analytics |

### Auth Routes (`auth_routes.py`)

| # | Method | Route | Purpose |
|---|--------|-------|---------|
| 24 | POST | `/auth/google` | Authenticate with Google |
| 25 | POST | `/auth/facebook` | Authenticate with Facebook |
| 26 | POST | `/auth/vipps` | Authenticate with Vipps |
| 27 | POST | `/auth/refresh` | Rotate refresh token + issue new access token |
| 28 | POST | `/auth/logout` | Revoke refresh-token family |
| 29 | GET | `/auth/me` | Get current user profile |
| 30 | PUT | `/auth/me` | Update current user profile |
| 31 | DELETE | `/auth/me` | Delete current user account |

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `XAI_API_KEY` | Yes | Grok (xAI) API key — active brain |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs TTS API key |
| `ELEVENLABS_VOICE_ID` | Yes | Default English voice ID |
| `ELEVENLABS_VOICE_ID_NO` | Recommended | Norwegian voice ID (fallback: nhvaqgRyAq6BmFs3WcdX) |
| `ANTHROPIC_API_KEY` | If using Claude | Claude API key |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `GEMINI_API_KEY` | If using Gemini | Gemini API key |
| `JWT_ACCESS_TOKEN_MAX_DAYS` | Recommended | Access token TTL (default: 7 days) |
| `JWT_REFRESH_TOKEN_MAX_DAYS` | Recommended | Refresh token TTL (default: 7 days) |
| `CORS_ALLOWED_ORIGINS` | Recommended | Comma-separated strict CORS allow-list |
| `AUDIO_SIGNATURE_BYPASS_FOR_TESTS` | Test only | Allows synthetic test audio without real file signatures |

## 📝 Version History

### v3.0.0 — Coachi (2026-02)
- Complete UI redesign: "Midnight Ember" design system
- Multi-brain AI routing with priority fallback
- ElevenLabs TTS with `eleven_flash_v2_5` (Norwegian Bokmål support)
- 2 coach personas with emotional progression
- 5-phase breathing timeline (prep → cooldown)
- Coaching text validation + anti-repetition
- Brain observability (per-brain stats, latency tracking)
- 3 language support (EN, NO, DA)
- Onboarding flow, workout history

### v1.1.0 (2026-01)
- Initial audio analysis + coaching
- Basic Flask backend
- Single AI provider

## 📄 License

This project is private and proprietary.

---

**Made by [Marius Gaarder](https://github.com/98Mvg)**
