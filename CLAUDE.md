# Treningscoach — Claude Code Behavior Spec

You are working inside an existing, production codebase. Your job is to improve and extend it WITHOUT breaking working behavior, WITHOUT moving files across directories, and WITHOUT inventing endpoints.

This is a low-latency AI Coach app ("Coachi", v3.0) with "Midnight Ember" design system. Uses physiological signals (breath analysis) to guide users through workouts with real-time voice feedback. The backend Brain Router abstracts multiple AI providers. The iOS app never knows which provider is active.

---

## 0) Non-Negotiable Rules

**R0.1 — Do not start from scratch.** Assume the system works today. Make improvements incrementally. Always read files before editing.

**R0.2 — Never invent routes, files, or behavior.** If you don't see it in the repo, search the code first.

**R0.3 — Low latency comes first.** Any change that increases latency must be justified and optional behind a flag in `config.py`.

**R0.4 — No "breathing app" framing in user-facing copy.** Breath analysis is a backend sensing function. UI/coach language frames this as an AI coach experience.

**R0.5 — Two languages always.** Every user-facing string needs both English (`en`) and Norwegian (`no`).

**R0.6 — Config is king.** Tunable values live in `config.py`. Don't hardcode magic numbers elsewhere.

**R0.7 — Keep coaching messages short.** 2-5 words for real-time cues, max 15 words for pattern insights.

---

## 1) Architecture (How It All Fits Together)

```
iOS App (SwiftUI)
  ↓ HTTP POST /coach/continuous (audio bytes)
Backend (Flask on Render)
  ↓ breath_analyzer.py → breath metrics (librosa DSP)
  ↓ brain_router.py → picks AI brain
  ↓ brains/*.py → generates coaching text
  ↓ elevenlabs_tts.py → text-to-speech audio
  ↑ Returns audio file URL to iOS
iOS App plays audio through speaker
```

**Active brain:** Grok (xAI) — cheapest + fastest.
**Fallback chain:** grok → gemini → openai → claude → config (static messages).
**TTS:** ElevenLabs cloud only. Qwen TTS disabled (too slow on CPU).
**Personas:** `personal_trainer` (supportive) and `toxic_mode` (drill sergeant), each with own voice settings + message banks.

### Architecture Decisions (Why Things Are This Way)

- **Brain Router abstraction**: App calls ONE backend API. Backend chooses the AI provider. Enables hot-swapping, A/B testing, fallback — UI stays stable.
- **Adapter pattern**: Each provider inherits from `BaseBrain`. Adding a provider is additive; router logic stays simple.
- **Grok as default**: Cheapest API, fast response times, good enough quality for real-time coaching.
- **Priority routing with timeout**: 1.2s timeout per brain. On failure, automatically tries next in chain. App never goes silent.
- **ElevenLabs over local TTS**: Qwen3-TTS was too slow on Render's CPU.
- **Librosa pre-warming**: First import takes ~10s. Pre-imported on startup to avoid timeout on first request.
- **Config fallback messages**: If ALL AI brains fail, `config.py` has static message banks in both languages.
- **Hybrid mode**: Config handles fast real-time cues. Claude runs in background for pattern detection over longer time windows.
- **Memory is minimal by design**: Inject only at session start. Store only coaching style, safety flags, improvement markers, last session config. Never inject full memory every message.
- **Safety overrides always win**: Critical breathing patterns override humor, pushiness, and long responses. Trigger concise, authoritative coaching.

---

## 2) CRITICAL: The Root vs Backend Sync Problem

Render deploys from **ROOT**, not `backend/`. This has caused broken deploys before.

```
treningscoach/              ← Render deploys THIS directory
├── main.py                 ← PRODUCTION (what Render runs via Procfile)
├── requirements.txt        ← PRODUCTION dependencies
├── Procfile                ← "web: gunicorn main:app --timeout 120 --workers 2"
├── config.py, brain_router.py, etc.  ← All .py modules in root
├── brains/                 ← Brain adapters (also in root)
├── backend/                ← DEVELOPMENT copy (NOT deployed)
│   ├── main.py             ← Edit here first
│   ├── brains/             ← Edit here first
│   └── requirements.txt    ← Edit here first
└── TreningsCoach/          ← iOS app (Xcode project)
```

### When you change backend code, ALWAYS:

```bash
# 1. Make changes in backend/ (the development copy)
# 2. Sync ALL Python files to root:
cp backend/*.py .
cp -r backend/brains/*.py brains/
cp backend/requirements.txt .
# 3. Commit BOTH locations:
git add backend/ *.py brains/ requirements.txt
git commit -m "Description of change"
git push
```

**If you forget to sync → deploy uses old code → nothing changes in production.**

### Before committing, verify sync:
```bash
diff backend/main.py main.py          # Must show no differences
diff backend/config.py config.py      # Must show no differences
diff backend/requirements.txt requirements.txt
```

### If you detect root/backend divergence:
1. Report the specific files that differ
2. Propose a safe sync (copy backend/ → root)
3. Do NOT delete anything without explicit instruction

Note: Root has 3 test files NOT in backend/ (test_backend_audio.py, test_coaching.py, test_first_breath.py). This is expected.

### CRITICAL: Xcode project.pbxproj is NOT in git

`TreningsCoach/TreningsCoach.xcodeproj/project.pbxproj` is NOT tracked by git (it's in `.gitignore`).
- Adding/deleting Swift files requires manual pbxproj edits (PBXBuildFile, PBXFileReference, PBXGroup, PBXSourcesBuildPhase)
- The `.xcodeproj` lives in the main repo only, NOT in git worktrees
- Xcode builds from the main repo checkout — worktree branch changes must be merged to the branch checked out in main repo before they appear in Xcode builds

---

## 3) Operating Mode: Problem-Driven Playbook

### When you encounter missing context:
- Search the codebase for the relevant file/function/route
- Quote exact filenames and line references
- Only then propose changes

### When asked to add a new AI provider:
1. Add a new adapter under `backend/brains/` conforming to `BaseBrain` interface
2. Add it to the router mapping in `brain_router.py`
3. Add health checks + timeout handling
4. Add env var for API key
5. Update config.py BRAIN_PRIORITY list
6. Sync to root

### When asked to change routing/switching:
- Keep the iOS app unaware of provider selection
- Implement switching in Brain Router via config + runtime `/brain/switch` API
- Maintain fallback order and timeouts (currently 1.2s per brain)
- Use usage/quota-aware selection if metrics exist (`config.BRAIN_USAGE`)

### When encountering latency issues:
- Prefer short prompts and template responses
- Memory injection only at session start
- Use strict timeouts per provider (config.BRAIN_TIMEOUT = 1.2s)
- Stream responses where supported
- Maintain fast fallback chain

### When encountering "stateful" features (memory, last session):
- Keep memory minimal: coaching style, safety flags, improvement markers, last session config
- Store in a single durable place and load once per session
- Do NOT inject full memory every message

### When encountering endpoint drift:
- Update the endpoint table in section 4 immediately
- If code and docs disagree, update docs to match code OR propose a safe refactor
- Never remove or rename endpoints without migration plan

---

## 4) All Backend Endpoints (19 routes in main.py)

### 1. GET `/` (line 276)
**Purpose:** Web interface
**Response:** HTML (templates/index.html)
**Auth:** None

### 2. GET `/health` (line 281)
**Purpose:** Health check + version + active brain
**Response:** `{status, version, timestamp, endpoints}`
**Auth:** None

### 3. GET `/welcome` (line 296)
**Purpose:** Welcome message + TTS audio at workout start
**Request params:** `?experience=beginner|intermediate|advanced&language=en|no&persona=personal_trainer|toxic_mode`
**Response:** `{text, audio_url, category}`
**Auth:** None

### 4. POST `/analyze` (line 347)
**Purpose:** Analyze breath audio only (no coaching)
**Request:** multipart/form-data — `audio` file (wav/mp3/m4a, max 10MB)
**Response:** `{intensity, volume, tempo, respiratory_rate, breath_regularity, signal_quality, ...}`
**Auth:** None

### 5. POST `/coach` (line 396)
**Purpose:** Single-shot coaching (audio in → voice out)
**Request:** multipart/form-data — `audio` file, `phase` (warmup|intense|cooldown), `mode` (chat|realtime_coach), `persona`
**Response:** `{text, breath_analysis, audio_url, phase}`
**Auth:** None

### 6. POST `/coach/continuous` (line 476) — MAIN ENDPOINT
**Purpose:** Continuous workout coaching — rapid coaching cycles
**Request:** multipart/form-data — `audio` (6-10s chunk), `session_id` (required), `phase`, `last_coaching`, `elapsed_seconds`, `language`, `training_level`, `persona`, `workout_mode`
**Response:** `{text, should_speak, breath_analysis, audio_url, wait_seconds, phase, workout_mode, reason}`
**Auth:** None

### 7. POST `/coach/talk` (line 1425)
**Purpose:** Talk to coach — casual chat or mid-workout wake word speech
**Request:** JSON — `{message (required), session_id, context (workout|chat), phase, intensity, persona, language}`
**Response:** `{text, audio_url, personality}`
**Auth:** None

### 8. POST `/coach/persona` (line 1277)
**Purpose:** Switch coach persona mid-workout
**Request:** JSON — `{session_id, persona}`
**Response:** `{success, persona, description}`
**Auth:** None

### 9. GET `/download/<file>` (line 900)
**Purpose:** Download generated audio files
**Response:** Audio file (audio/wav or audio/mpeg)
**Auth:** None. Path traversal blocked (`..` rejected).

### 10. GET `/brain/health` (line 925)
**Purpose:** Check active AI brain status
**Response:** `{active_brain, healthy, message}`
**Auth:** None

### 11. POST `/brain/switch` (line 945)
**Purpose:** Hot-swap AI brain at runtime
**Request:** JSON — `{brain: "priority"|"claude"|"openai"|"grok"|"gemini"|"config"}`
**Response:** `{success, active_brain, message}`
**Auth:** None

### 12. POST `/chat/start` (line 993)
**Purpose:** Create new conversation session
**Request:** JSON — `{user_id, persona (optional)}`
**Response:** `{session_id, persona, persona_description, available_personas}`
**Auth:** None

### 13. POST `/chat/stream` (line 1039)
**Purpose:** Streaming chat (SSE)
**Request:** JSON — `{session_id, message}`
**Response:** SSE stream — `data: {token: "..."}` ... `data: {done: true}`
**Auth:** None. Session must exist (404 if not).

### 14. POST `/chat/message` (line 1143)
**Purpose:** Non-streaming chat (fallback)
**Request:** JSON — `{session_id, message}`
**Response:** `{message, session_id, persona}`
**Auth:** None. Session must exist (404 if not).

### 15. GET `/chat/sessions` (line 1210)
**Purpose:** List sessions
**Request params:** `?user_id=...` (optional filter)
**Response:** `{sessions: [...]}`
**Auth:** None

### 16. DELETE `/chat/sessions/<id>` (line 1234)
**Purpose:** Delete a session
**Response:** `{success, session_id}`
**Auth:** None

### 17. GET `/chat/personas` (line 1246)
**Purpose:** List available personas
**Response:** `{personas: [{id, description}, ...]}`
**Auth:** None

### 18. POST `/workouts` (line 1324)
**Purpose:** Save completed workout record
**Request:** JSON — `{duration_seconds, final_phase, avg_intensity, persona_used, language}`
**Response:** `{workout: {...}}` (201)
**Auth:** Optional Bearer JWT → extracts user_id. Falls back to "anonymous".

### 19. GET `/workouts` (line 1378)
**Purpose:** Get workout history
**Request params:** `?limit=20`
**Response:** `{workouts: [...]}`
**Auth:** Optional Bearer JWT → filters by user_id. Without auth, returns all.

---

**Verification rule:** After any route change, confirm count = 19 (or update). Each route above includes its line number in main.py for quick lookup.

---

## 5) iOS App Key Files

| File | What it does | When to edit |
|------|-------------|--------------|
| `AppTheme.swift` | CoachiTheme design system — colors, gradients, view modifiers | Changing colors, fonts, card styles |
| `AppViewModel.swift` | App-level state: onboarding, language, user profile | Onboarding flow, app-wide state |
| `RootView.swift` | Root navigation: onboarding vs MainTabView | App entry flow changes |
| `Config.swift` | Backend URL, phase timings, version | Changing backend URL or timing |
| `WorkoutViewModel.swift` | Main workout logic + state machine | Workout flow changes |
| `ContinuousRecordingManager.swift` | Real-time audio capture | Audio recording issues |
| `BackendAPIService.swift` | All HTTP calls to backend | API changes |
| `TreningsCoachApp.swift` | Entry point, injects AppViewModel + AuthManager | App startup changes |
| `CoachOrbView.swift` | Animated coaching orb (idle/listening/speaking) | UI animation changes |
| `AudioPipelineDiagnostics.swift` | Debug overlay for audio pipeline | Debugging audio |
| `L10n.swift` | All bilingual strings (en/no) | Adding user-facing text |

### iOS Design Rules
- Workout screen must be immersive. No settings UI during workout.
- User picks voice/persona/language BEFORE workout.
- During workout: minimal controls only.

---

## 6) Solving Common Problems

### "Backend deployed but nothing changed"
1. Did you sync? `diff backend/main.py main.py`
2. Did you push to `main` branch? Auto-deploy only triggers on `main`.
3. Check Render dashboard for deploy status/errors.
4. Verify: `curl https://treningscoach-backend.onrender.com/health`

### "New dependency not found on Render"
1. Add to `backend/requirements.txt`
2. Sync: `cp backend/requirements.txt .` (root is what Render installs)
3. Push.

### "iOS Error -10875 (Audio Session)"
Audio session category conflict. Fix pattern:
```swift
try? audioSession.setActive(false)
try audioSession.setCategory(.playAndRecord, options: [.defaultToSpeaker, .allowBluetooth])
try audioSession.setActive(true)
```

### "Onboarding not showing / stuck"
`has_completed_onboarding` is true in UserDefaults. Delete the app or reset:
```swift
UserDefaults.standard.removeObject(forKey: "has_completed_onboarding")
```

### "No voice/audio in coaching response"
1. Check `ELEVENLABS_API_KEY` is set in Render env vars
2. Check voice IDs: `ELEVENLABS_VOICE_ID` (English), `ELEVENLABS_VOICE_ID_NO` (Norwegian)
3. Check backend logs for TTS errors
4. Test: `curl "https://treningscoach-backend.onrender.com/welcome?language=en"`

### "Brain/AI not responding"
1. Check active brain: `curl https://treningscoach-backend.onrender.com/brain/health`
2. Check API key for that brain is set in Render env vars
3. Priority routing tries: grok → gemini → openai → claude → config (static)
4. Switch brain: `curl -X POST .../brain/switch -H "Content-Type: application/json" -d '{"brain":"claude"}'`

### "Breath analysis timing out / first request slow"
Librosa is pre-warmed on startup. Render free tier cold-starts take 30-60s. Procfile has `--timeout 120` to handle this.

---

## 7) Environment Variables (Render Dashboard)

| Variable | Required | Used by |
|----------|----------|---------|
| `XAI_API_KEY` | Yes (active brain) | brains/grok_brain.py |
| `ELEVENLABS_API_KEY` | Yes (TTS) | elevenlabs_tts.py |
| `ELEVENLABS_VOICE_ID` | Yes (English voice) | config.py |
| `ELEVENLABS_VOICE_ID_NO` | Yes (Norwegian voice) | config.py |
| `ANTHROPIC_API_KEY` | If using Claude brain | brains/claude_brain.py |
| `OPENAI_API_KEY` | If using OpenAI brain | brains/openai_brain.py |
| `GEMINI_API_KEY` | If using Gemini brain | brains/gemini_brain.py |

---

## 8) Quick Verification Commands

```bash
# Health check
curl https://treningscoach-backend.onrender.com/health

# Test welcome audio
curl "https://treningscoach-backend.onrender.com/welcome?language=en"

# Check active brain
curl https://treningscoach-backend.onrender.com/brain/health

# Sync backend to root
cp backend/*.py . && cp -r backend/brains/*.py brains/ && cp backend/requirements.txt .

# Verify sync
diff backend/main.py main.py && echo "SYNCED" || echo "OUT OF SYNC!"
```

---

## 9) Output Expectations (How You Respond)

When you propose changes:
- Start with what exists (files/paths/line numbers)
- Explain why the change is needed
- Provide minimal diff approach
- Include "how to verify" steps (curl examples, tests)

When you touch routes:
- Update the endpoint table in section 4 immediately
- Provide curl commands for each modified/added route

When you touch provider routing:
- State the routing order and timeouts
- Provide failure behavior examples

---

## 10) Guardrails for Coach Personality

- Humor allowed only when user is calm/performing well. No humor in intense/critical states.
- Keep coaching lines short (often < 10 words in realtime mode).
- Use the user's name in the FIRST welcome message of a session (if known).
- Safety overrides always win over personality/humor.
- Breath analysis is a sensor signal — never expose DSP internals to the user.
